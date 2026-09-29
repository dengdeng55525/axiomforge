# API / Web 部署

默认界面是 Vue 工作台，FastAPI 提供 API 与静态页面；可选 8501 同源网关保留单独的界面端口。Dockerfile / compose.yaml 提供应用容器配置，镜像构建和容器部署需要在目标环境完成验收。所有启动方式默认连接外部模型端点，模型权重按本地部署流程单独管理。

## 本机启动

先按主 [README](../README.md) 安装项目 Python 依赖、校验公开数据并初始化知识库。新版工作台构建另需 Node.js 22.12+ 与 npm：

~~~bash
cd /root/algorithm-capability-factory
.venv/bin/algoforge init --provider mock
./scripts/build_web.sh
./scripts/start_api.sh
~~~

在第二个终端启动 UI 网关：

~~~bash
/root/algorithm-capability-factory/scripts/start_ui.sh
~~~

工作台为 `http://127.0.0.1:8501/app/`，API 也直接提供 `http://127.0.0.1:8000/app/`；接口文档是 `http://127.0.0.1:8000/docs`。根路径会跳转到 `/app/`。8501 网关只转发支持的 API 路由，不单独创建执行队列或读取模型凭证。

脚本自动定位仓库并使用 `.venv`，不依赖激活 Conda base。
`build_web.sh` 执行 `npm ci` 和 `npm run build`；`node_modules/` 与 `dist/` 保持在 Git 忽略范围。新克隆环境先构建，前端源码更新后重新构建。若 API 启动时缺少构建目录，`/app/` 返回明确提示；构建后重启服务以挂载页面。`start_ui.sh` 会在构建缺失时调用构建脚本，Node.js 由目标环境提供。

| 环境变量 | 默认值 | 含义 |
| --- | --- | --- |
| `ALGOFORGE_HOST` / `ALGOFORGE_API_PORT` | `127.0.0.1` / `8000` | API 监听地址与端口 |
| `ALGOFORGE_UI_HOST` / `ALGOFORGE_UI_PORT` | `127.0.0.1` / `8501` | UI 网关监听地址与端口 |
| `ALGOFORGE_API_URL` | `http://127.0.0.1:8000` | UI 网关连接的固定 API 地址 |

旧版 Streamlit 可通过 `./scripts/start_legacy_ui.sh` 启动。它默认也使用 8501，需要对应 Python UI 依赖；同时启动时应使用不同 UI 端口。

通过 SSH 访问服务器时，可以转发 8000 或 8501 到本地。默认只监听回环地址。当前是本机单用户原型，公网多人使用所需的身份认证、TLS、任务归属与配额不属于当前交付范围。

## 本地 14B / 四卡 4090D 接入

本地模型使用 OpenAI 兼容 HTTP Provider。默认方案 `four_gpu_14b` 为四张卡各启动一个 `Qwen/Qwen2.5-Coder-14B-Instruct-AWQ` 副本，端口 8100–8103，16K 总上下文。GPU 分组、固定 revision、量化和 served model name 位于 [inference_profiles.json](../configs/inference_profiles.json)。

~~~bash
.venv/bin/python scripts/plan_inference.py --profile four_gpu_14b --available-gpus 4
~~~

该命令校验设备分配并打印 vLLM 命令，不下载权重。要在已准备好的 GPU 主机启动四个副本，可运行：

~~~bash
# 只需首次执行；vLLM 安装到项目 .venv，不影响系统 Python。
./scripts/install_local_vllm.sh

LOCAL_LLM_PROFILE=four_gpu_14b \
  LOCAL_LLM_AVAILABLE_GPUS=4 \
  ./scripts/start_local_vllm.sh
~~~

启动脚本会自动使用 `.venv/bin/vllm`，所以不需要手动激活虚拟环境。安装脚本同时安装
`socksio` 和 `ninja`，分别用于 SOCKS 代理和 FlashInfer/扩展构建。模型首次启动会下载
约 10 GB 权重并写入 Hugging Face 缓存；若本机可直连 Hugging Face，可清除代理变量，若
使用 `socks5://` 代理，保留代理即可。

当前主机的系统 CUDA 工具链为 11.8，而 vLLM 0.29.0 的 FlashInfer wheel 可能尝试使用
更高版本的 `nvcc` 参数，因此启动器默认设置 `VLLM_USE_FLASHINFER_SAMPLER=0`，并用
`--enforce-eager` 关闭不稳定的编译/图预热。Qwen AWQ 推理仍在 GPU 上运行；升级 CUDA
工具链后可设置 `VLLM_USE_FLASHINFER_SAMPLER=1` 做单独性能验收。启动器自带的
`compat/sitecustomize.py` 只跳过非 Qwen 模型的 MiniMax 预热导入，不修改模型权重。

启动脚本由部署者管理 vLLM 子进程；AlgoForge 仍只通过 HTTP 调用。`local_http` Provider 负责端点轮询和失败重试，`scripts/check_local_llm.py` 负责主动健康检查；并发上限、熔断和故障摘除策略需在目标机器按实际部署验证，性能测量也单独记录。

独立部署后，将项目 `.env` 配置为实际服务。规划脚本给四个服务指定共享的模型别名为 `coder14`，请求必须使用该服务别名而非自动假定模型仓库名称：

~~~dotenv
LOCAL_LLM_BASE_URL=http://127.0.0.1:8100/v1
LOCAL_LLM_ENDPOINTS=http://127.0.0.1:8100/v1,http://127.0.0.1:8101/v1,http://127.0.0.1:8102/v1,http://127.0.0.1:8103/v1
LOCAL_LLM_MODEL=coder14
LOCAL_LLM_PROFILE=four_gpu_14b
LOCAL_LLM_API_KEY=
~~~

如果自行使用不同 `--served-model-name`，应同步修改 `LOCAL_LLM_MODEL`。重启 API 后，可用 `RunRequest(provider="local_http")` 或工作台中的本地模型选项提交任务。配置页展示 profile、端点池和执行边界；DeepSeek 密钥仅由 API 服务读取。

## 可选应用容器

[Dockerfile](Dockerfile) 分为 Node 前端构建阶段和 Python 运行阶段：先按 npm 锁文件构建 Vue 页面，再将 `web/dist` 复制到应用镜像。API 和 UI 网关使用同一镜像；UI 容器运行轻量网关，不再启动 Streamlit。

在具备 Docker 的环境中，从仓库根目录执行：

~~~bash
.venv/bin/python scripts/verify_data.py
docker compose -f deploy/compose.yaml build
docker compose -f deploy/compose.yaml up -d
~~~

API 容器读取本地 `.env`；UI 容器只设置 `ALGOFORGE_API_URL=http://api:8000`，DeepSeek 密钥由 API 容器管理。公开原始数据以只读方式挂载，运行结果保存到命名 volume。API 总额度 4 CPU / 6 GiB，受限 worker 默认 2 CPU / 2 GiB；这些数值属于配置上限，吞吐和内存表现需要在目标环境实测。

镜像使用非 root 用户。生成代码经过 AST 构造器检查并在资源受限子进程中运行；每候选独立操作系统隔离需要更强的执行节点。详细边界见 [worker 说明](worker/README.md)。容器部署应在目标环境完成构建、启动和验证。

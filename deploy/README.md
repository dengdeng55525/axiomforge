# API / Web 部署

默认界面是 Vue 工作台，FastAPI 提供 API 与静态页面；可选 8501 同源网关保留单独的界面端口。Dockerfile / compose.yaml 提供应用容器配置，**当前没有宣称镜像构建或容器部署已验收**。所有启动方式均不会下载或启动本地大模型。

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
`build_web.sh` 执行 `npm ci` 和 `npm run build`；`node_modules/` 与 `dist/` 不进入 Git。新克隆环境先构建，前端源码更新后重新构建。若 API 启动时缺少构建目录，`/app/` 返回明确提示；构建后重启服务以挂载页面。`start_ui.sh` 会在构建缺失时调用构建脚本，但不会替用户安装 Node.js。

| 环境变量 | 默认值 | 含义 |
| --- | --- | --- |
| `ALGOFORGE_HOST` / `ALGOFORGE_API_PORT` | `127.0.0.1` / `8000` | API 监听地址与端口 |
| `ALGOFORGE_UI_HOST` / `ALGOFORGE_UI_PORT` | `127.0.0.1` / `8501` | UI 网关监听地址与端口 |
| `ALGOFORGE_API_URL` | `http://127.0.0.1:8000` | UI 网关连接的固定 API 地址 |

旧版 Streamlit 可通过 `./scripts/start_legacy_ui.sh` 启动。它默认也使用 8501，需要对应 Python UI 依赖；同时启动时应使用不同 UI 端口。

通过 SSH 访问服务器时，可以转发 8000 或 8501 到本地。默认只监听回环地址。当前是本机单用户原型，公网多人使用所需的身份认证、TLS、任务归属与配额不属于当前交付范围。

## 本地 14B / 四卡 4090D 接入计划

本地模型使用 OpenAI 兼容 HTTP Provider。默认静态方案 `four_gpu_14b` 为四张卡各保留一个 `Qwen/Qwen2.5-Coder-14B-Instruct-AWQ` 副本，端口 8100–8103。GPU 分组、固定 revision、量化和未来启动参数位于 [inference_profiles.json](../configs/inference_profiles.json)。

~~~bash
.venv/bin/python scripts/plan_inference.py --profile four_gpu_14b --available-gpus 4
~~~

该命令校验静态设备分配并打印未来 vLLM 命令，不启动服务，不证明当前机器已部署。现有 Provider 对每次运行连接一个配置端点；四个服务的负载均衡、跨副本角色调度与性能测量属于后续部署工作。

独立部署后，将项目 `.env` 配置为实际服务。规划脚本给 8100 服务指定的模型别名为 `coder_a`，请求必须使用该服务别名而非自动假定模型仓库名称：

~~~dotenv
LOCAL_LLM_BASE_URL=http://127.0.0.1:8100/v1
LOCAL_LLM_MODEL=coder_a
LOCAL_LLM_PROFILE=four_gpu_14b
~~~

如果自行使用不同 `--served-model-name`，应同步修改 `LOCAL_LLM_MODEL`。重启 API 后，可用 `RunRequest(provider="local_http")` 或工作台中的本地模型选项提交任务。配置页展示静态计划和未实测状态，不探测 GPU、不下载权重；DeepSeek 密钥不会发送到本地端点。

## 可选应用容器

[Dockerfile](Dockerfile) 分为 Node 前端构建阶段和 Python 运行阶段：先按 npm 锁文件构建 Vue 页面，再将 `web/dist` 复制到应用镜像。API 和 UI 网关使用同一镜像；UI 容器运行轻量网关，不再启动 Streamlit。

在具备 Docker 的环境中，从仓库根目录执行：

~~~bash
.venv/bin/python scripts/verify_data.py
docker compose -f deploy/compose.yaml build
docker compose -f deploy/compose.yaml up -d
~~~

API 容器读取本地 `.env`；UI 容器只设置 `ALGOFORGE_API_URL=http://api:8000`，不接收 DeepSeek 密钥。公开原始数据只读挂载，运行结果保存到命名 volume。API 总额度 4 CPU / 6 GiB，受限 worker 默认 2 CPU / 2 GiB；这些是配置上限，不是吞吐或内存实测。

镜像使用非 root 用户，不等同于为每个候选提供独立操作系统沙箱；生成代码仍通过 AST 构造器检查和资源受限子进程运行。详细边界见 [worker 说明](worker/README.md)。容器部署需要在目标环境实际构建、启动和验证后再验收。

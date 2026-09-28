# API / Web 部署

当前经过实际验证的是 Python 虚拟环境启动方式；此目录的 Dockerfile / compose.yaml
提供应用容器配置，本机没有 Docker，因此 **没有宣称镜像构建或容器部署已验收**。
这里不安装、不下载、不启动任何本地大模型。

## 本地 14B / 四卡 4090D 兼容框架

项目已经把本地模型接入抽象为 OpenAI 兼容 HTTP Provider。默认静态方案
`four_gpu_14b` 使用 `Qwen/Qwen2.5-Coder-14B-Instruct-AWQ`，为四张卡各保留
一个单卡副本（端口 8100–8103），便于解释、规划、编码和审查角色并行调度。
完整的 GPU 分组、固定 revision、量化和启动参数在
`configs/inference_profiles.json`，可以用下面的命令只生成静态计划：

~~~bash
python scripts/plan_inference.py --profile four_gpu_14b --available-gpus 4
~~~

该命令只校验设备分配并打印未来的 vLLM 命令，不下载权重、不启动服务，也不
宣称本机已经部署。独立部署完成后，将 `.env` 中的
`LOCAL_LLM_BASE_URL`、`LOCAL_LLM_MODEL` 和 `LOCAL_LLM_PROFILE` 指向实际端点，
再通过 `RunRequest(provider="local_http")` 或 UI 的“本地模型”选项使用。服务的
`/health` 与 `/inference/profiles` 会展示静态配置和“planned_not_deployed”状态，
不会把 DeepSeek 密钥发送到本地端点。

## 已实现的本地启动

从仓库根目录运行，先按主 README 安装依赖、校验公开数据并填写 .env：

~~~bash
.venv/bin/algoforge init --provider mock
./scripts/start_api.sh
# 第二个终端
./scripts/start_ui.sh
~~~

API 文档是 http://127.0.0.1:8000/docs；UI 是 http://127.0.0.1:8501。
通过 SSH 访问服务器时，可转发对应两个本机端口。默认仅监听回环地址。
公网多人环境需要额外的身份认证、TLS、任务归属与配额，当前演示服务没有这些功能。

## 可选应用容器

安装 Docker 后，在仓库根目录先下载数据：

~~~bash
python scripts/verify_data.py
docker compose -f deploy/compose.yaml build
docker compose -f deploy/compose.yaml up -d
~~~

API 容器使用 .env；UI 不接收 DeepSeek 密钥。公开原始数据只读挂载，运行结果保存
到命名 volume。API 总额度 4 CPU / 6 GiB、每候选的受限 worker 上限 2 CPU / 2 GiB。
镜像使用非 root 用户，不等于为每个候选提供独立操作系统沙箱；生成代码仍走 AST
构造器编译和资源受限子进程。详细边界见 [worker说明](worker/README.md)。

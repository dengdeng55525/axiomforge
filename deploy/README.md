# API / Web 部署

当前经过实际验证的是 Python 虚拟环境启动方式；此目录的 Dockerfile / compose.yaml
提供应用容器配置，本机没有 Docker，因此 **没有宣称镜像构建或容器部署已验收**。
这里不安装、不下载、不启动任何本地大模型。

## 已实现的本地启动

从仓库根目录运行，先按主 README 安装依赖、校验公开数据并填写 .env：

~~~bash
.venv/bin/algoforge init --provider mock
.venv/bin/algoforge serve --host 127.0.0.1 --port 8000
# 第二个终端
.venv/bin/streamlit run ui/app.py --server.address 127.0.0.1 --server.port 8501
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

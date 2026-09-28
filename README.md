# AlgoForge：可验证的算法能力工厂

AlgoForge 将中文算法需求转成受控的 scikit-learn 管道代码，执行统一验证，依据错误进行有限修复，再把代码、指标、来源和失败经验写回知识库。主场景是**银行营销响应预测**，短信垃圾信息分类用于展示跨场景复用。项目对应 [LLM Agent 笔试原题](docs/source/exam.txt)。

当前已经有 Python 工作流、DeepSeek API、SQLite 知识图谱、CLI、FastAPI、Streamlit 和自动报告。此次 [模型发现记录](docs/research/deepseek_model_discovery.json) 将 **DeepSeek-V4.1-Flash** 对应到 API ID **deepseek-flash**。真实、mock 与历史记录明确区分，不把模拟输出当作真实模型成绩。

**当前默认使用云端 API，没有部署本地大模型。** 本地 14B 接入框架已经搭好：
`four_gpu_14b` 为四个 Qwen2.5-Coder-14B AWQ 单卡副本（GPU 0–3、端口 8100–8103），
通过 OpenAI 兼容 HTTP Provider 接入；权重下载、vLLM 启动和四卡实测仍由后续部署完成。
1–6 张 RTX 4090D 只展示静态配置，不虚构吞吐。执行后端为受限 AST 构造器加资源限制子进程，**不是 Docker 或完整操作系统沙箱**。最终测试统计和验收清单以 `docs/research/execution_validation.json` 为准。

## 快速开始

Linux、Python 3.10+。首次安装与下载公开数据需要网络；mock 流程不需要模型凭证或 GPU。

~~~bash
cd /root/algorithm-capability-factory
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e '.[dev,ui]'
python scripts/verify_data.py
python -m capability_factory init --provider mock
python -m capability_factory run \
  --description '预测银行客户是否订购定期存款，仅用通话前特征，禁止 duration，比较两个候选并报告验证结果。' \
  --dataset bank --provider mock --max-candidates 2 --max-repairs 2
~~~

`requirements.txt` 锁定完整应用环境，`pyproject.toml` 声明直接依赖与 UI/测试依赖。已有虚拟环境时直接激活。`requirements-feasibility.txt` 仅保留早期人工基线环境，不代替应用依赖。

### 使用 DeepSeek V4.1 API

在私有环境变量或未入 Git 的 `.env` 中配置 `DEEPSEEK_API_KEY`。已有凭证无需重复配置，也不要覆盖当前私有配置。其他可配置项见 `.env.example`：

~~~dotenv
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-flash
~~~

API Key 不写入代码、需求、报告或 Git。凭证仅由后端读取，算法 worker 不继承它。

~~~bash
python -m capability_factory doctor --check-api
python -m capability_factory init --provider deepseek
python -m capability_factory run \
  --description '预测银行定期存款订购，禁止通话后特征。比较两个方案，以验证集 AP 选择候选，保存代码、检查、修复和来源。' \
  --dataset bank --provider deepseek --max-candidates 2 --max-repairs 2 \
  --search compare --use-graph --max-seconds 900
~~~

这些命令会调用真实模型并可能产生 API 费用。`doctor --check-api` 只检查模型端点；完整 run 才证明生成与验证闭环。`algoforge` 和 `python -m capability_factory` 是同一入口。

## API 与中文界面

在两个终端分别运行：

~~~bash
cd /root/algorithm-capability-factory
./scripts/start_api.sh
~~~

~~~bash
cd /root/algorithm-capability-factory
./scripts/start_ui.sh
~~~

两个脚本会自动定位仓库和项目虚拟环境，因此不依赖当前终端位于哪个目录，也不会误用系统 `base` Python。首次使用仍需先按快速开始安装依赖。

- 工作台：`http://127.0.0.1:8501`；四个视图为任务与监控、代码与报告、知识图谱、历史与资源。
- 自动生成的 OpenAPI 文档：`http://127.0.0.1:8000/docs`。
- 主要接口：提交、运行状态/事件/时间线、候选指标、资源、制品/报告、取消、能力列表与图导出。
- UI 只通过 HTTP 访问后端，不执行生成代码、不读取模型凭证、不直接嵌入模型 HTML。
- 页面中的“LLM 来源”支持 DeepSeek V4.1 API、本地 14B OpenAI 兼容接口和 Mock。本地选项只提交 `provider=local_http`，浏览器不会保存或传递 DeepSeek 密钥；`GET /config` 与 `GET /inference/profiles` 会显示四卡静态计划及 `planned_not_deployed` 状态。

~~~bash
curl --noproxy '*' -sS http://127.0.0.1:8000/runs \
  -H 'Content-Type: application/json' \
  -d '{"description":"构建银行营销响应预测，禁止 duration。","dataset_id":"bank","provider":"mock","max_candidates":2,"max_repairs":2,"use_graph":true,"search":"compare","inject_failure":false}'
~~~

用返回的运行 ID 请求 `GET /runs/{run_id}` 和 `GET /runs/{run_id}/report`。当前是本机单用户原型，公网鉴权、租户隔离与生产部署不属于已交付能力。

## 系统架构与模块

~~~mermaid
flowchart LR
  U[CLI / FastAPI / Streamlit] --> W[有预算的工作流]
  W --> I[需求解释]
  I --> K[(SQLite 来源与能力图)]
  K --> P[规划与候选搜索]
  P --> C[代码生成]
  C --> A[受限 AST 构造检查]
  A --> X[资源限制子进程]
  X --> V[可信验证器]
  V --> R[错误审查与有限修复]
  R --> C
  V --> H[比较与报告]
  H --> K
  I --> L[DeepSeek API / 明确标记的 Mock]
  P --> L
  C --> L
  R --> L
~~~

| 模块 | 职责 |
|---|---|
| [contracts.py](src/capability_factory/contracts.py) | 任务、计划、代码、审查和预算的 Pydantic 合约 |
| [providers.py](src/capability_factory/providers.py)、[prompts.py](src/capability_factory/prompts.py) | API/Mock、角色提示、用量和响应记录 |
| [workflow.py](src/capability_factory/workflow.py) | 状态、检索、比较、Beam 扩展、修复和回写 |
| [ingestion.py](src/capability_factory/ingestion.py)、[knowledge.py](src/capability_factory/knowledge.py) | 来源摄取、源码 AST 抽取、能力版本和图检索 |
| [datasets.py](src/capability_factory/datasets.py)、[metrics.py](src/capability_factory/metrics.py) | 哈希/切分/标签协议、独立指标计算 |
| [execution/](src/capability_factory/execution) | 白名单构造、训练预测、接口/稳定性/资源检查 |
| [reporting.py](src/capability_factory/reporting.py) | JSON、HTML、Markdown 报告与转义 |
| [api.py](src/capability_factory/api.py)、[cli.py](src/capability_factory/cli.py)、[ui/](ui) | 队列、CLI、HTTP 与薄界面 |

显式 Python 状态机便于复核决策、错误和预算。Pydantic 约束角色输出；SQLite 便于本地复现；NetworkX/Plotly 展示关系；scikit-learn 使算法训练可在 CPU 执行；FastAPI/Streamlit 分离后端与展示。无需大框架隐藏状态转移。

解释器、规划器、代码生成器、审查器和结果整理器使用独立合约与多次调用；摄取阶段另外使用抽取器。这是同一模型承担多角色，不能称作多个独立训练的模型，也不展示隐藏思维链。

## 知识图谱与版本

实际 schema 为 [knowledge/runtime_schema.sql](knowledge/runtime_schema.sql)，运行表使用 `cf_` 前缀；早期 [schema 草案](schemas/knowledge_schema.sql) 仅保留为设计资料。详细说明见 [知识库 README](knowledge/README.md)。

节点涵盖来源、能力、任务、算法、转换、数据、环境、验证运行、制品与失败经验；关系包括 `USES`、`REQUIRES`、`DERIVED_FROM`、`EVALUATES`、`REPAIRS`、`AVOIDED_BY` 和 `SUPERSEDES`。能力记录包含输入输出、条件、指标、依赖、来源定位及版本。

摄取读取固定 UCI 文档、项目协议及实际安装的 scikit-learn 源码，保存哈希、行号、函数与依赖信息；不递归扫描任意工作区，也不是任意远程仓库爬取器。人工种子、LLM 抽取和运行验证分别标记，有出处不等于已运行验证。

检索先按任务和状态过滤，再做中英文词项匹配和最多两跳图扩展，保留文本分数、图加分与证据路径。`--no-use-graph` 可做消融；不是训练后的语义向量检索。

~~~bash
python -m capability_factory export-graph --output artifacts/graph.json
~~~

## 数据、代码接口与验证

| 任务 | 数据 | 固定协议 |
|---|---|---|
| 银行营销响应 | UCI Bank Marketing，41,188 行 | 原始顺序 60/20/20，只用通话前白名单特征，禁 duration |
| 短信垃圾信息分类 | UCI SMS Spam Collection，原始 5,574 行 | 规范化文本分组、冲突标签排除、组去重后分层 60/20/20 |

下载、出处、许可与 SHA256 见 [数据审计](docs/research/data_audit.json)、[来源索引](docs/SOURCES.md) 和 [数据协议](docs/02_数据与知识来源.md)。最终测试部分不提供给候选代码，不用于开发搜索评分。

生成器只实现 `build_pipeline(task_spec)`，返回具有 fit/predict_proba 接口的获准 Pipeline。以下是首次真实银行运行代码的节选，完整版本和哈希以制品为准：

~~~python
def build_pipeline(task_spec):
    numeric = Pipeline([
        ('impute', SimpleImputer(strategy='median')),
        ('scale', StandardScaler()),
    ])
    categorical = Pipeline([
        ('encode', OneHotEncoder(handle_unknown='ignore')),
    ])
    prepare = ColumnTransformer([
        ('numeric', numeric, task_spec['numeric_features']),
        ('categorical', categorical, task_spec['categorical_features']),
    ])
    model = LogisticRegression(
        max_iter=1000, class_weight='balanced', random_state=task_spec['seed'])
    return Pipeline([('prepare', prepare), ('model', model)])
~~~

可信代码负责固定切分、训练调度、概率列与行号对齐、有限值/区间、正类映射、边界检查及指标计算。主指标 AP 明确定义为 average_precision；辅助报告 ROC-AUC、F1、前 10% 名单表现、资源与代码哈希。缺失指标不补零，工作流完成与质量门槛分别记录。

## 真实运行与验收证据

首次真实银行修复运行 ID：**13edb7649f0d41bba608251b6079e4d1**。

- DeepSeek API 调用 11 次，两个候选中一个通过、一个失败；不是全部候选成功。
- 通过候选验证 AP 0.180759，同协议常数 AP 0.110706，F1@0.5 为 0.228819。
- 首个候选注入了明确标记的接口故障，通过一次自动修复；不能当作自然错误修复率。
- 记录耗时 50.957 秒，属于该次环境实测，不是延迟承诺；最终测试未评分。
- 真实抽取得到 9 张通过来源检查的 LLM 能力卡，不等于 9 张能力都已运行验证。

以上为特定历史运行事实。最终代码回归、测试统计与完整证据索引以 `docs/research/execution_validation.json` 为准。早期 [CPU 人工基线](docs/research/baseline_results.json) 不能包装成 Agent 实测。

本地制品位于 `artifacts/runs/{run_id}/`，包含 LLM 请求/响应、候选各次代码/验证、进度与报告，默认不入 Git。公开提交的脱敏样例为 [bank_repair](examples/evidence/bank_repair/)、[bank_beam](examples/evidence/bank_beam/) 和 [sms_transfer](examples/evidence/sms_transfer/)。**是否已生成、状态与运行 ID 以实际文件和证据索引为准，不能因目录名称推定成功。**

优先演示 [bank_beam/report.html](examples/evidence/bank_beam/report.html)：该历史运行保留六个候选的代码、验证与资源对照；[bank_repair](examples/evidence/bank_repair/) 补充一次注入故障修复，早期运行的限制见其 report.json；[sms_transfer](examples/evidence/sms_transfer/) 展示文本任务迁移。每个 bundle 的 manifest.json 记录源报告 SHA256、模式、状态、文件哈希和省略内容。

~~~bash
python -m capability_factory report 13edb7649f0d41bba608251b6079e4d1 \
  --format html --output artifacts/bank-repair-report.html
python -m capability_factory run \
  --description '构建短信垃圾信息分类，比较两套 TF-IDF 概率分类管道并报告验证结果。' \
  --dataset sms --provider deepseek --max-candidates 2 --max-repairs 2
python -m capability_factory run \
  --description '搜索银行营销响应预测方案，遵守通话前特征协议。' \
  --dataset bank --provider deepseek --search beam --max-candidates 6 --max-repairs 2
~~~

新克隆仓库不含本机 SQLite 历史，不能直接用旧运行 ID 重建报告；可阅读脱敏样例，或重新运行并使用新的 ID。

## 测试与实验

~~~bash
python -m pytest tests ui -q
python -m ruff check src scripts tests ui
python scripts/run_experiments.py --provider mock --suite smoke --repeats 1 --dry-run
python scripts/run_experiments.py --provider mock --suite smoke --repeats 1 \
  --profiles A,B,C,D --output artifacts/experiments/mock-smoke
~~~

运行器支持 mock/deepseek、smoke/full、配置与任务 ID 筛选；真实实验须显式选择 deepseek。smoke 每轮 8 次系统 run，full 每轮 48 次，三轮完整矩阵为 144 次。**存在运行器不代表这些实验已经完成。** 实际完成数量、失败分母、预算口径与结果以输出文件为准。

测试涵盖数据契约、AST/参数限制、预测指标、资源执行、知识版本、API、编排、报告及 UI。UI AppTest 使用模拟 HTTP，不能替代真实 E2E。测试总数和执行时间交由自动验证索引记录，不在 README 手工填写通过数量。

## 安全边界、挑战与扩展

| 挑战 | 当前处理 | 边界 |
|---|---|---|
| 不受信代码 | AST 白名单构造，不用 exec/eval 执行模型文本，资源限制进程 | 信任 sklearn/native 依赖；无 OS 文件/网络命名空间隔离 |
| 泄漏与虚假指标 | 固定特征/切分、评估器持有验证标签、预测与哈希校验 | 不是对任意数据源的自动泄漏发现系统 |
| 格式错误、失败与费用 | 结构合约、有限重试/修复、预算、用量和事件 | 网络依赖；超时请求账单仍以提供商为准 |
| 经验可信度 | 保留失败、代码版本、验证状态及来源 | 图检索/多角色效果仍需更多独立任务实验 |
| 未来多卡 | Provider 边界、1–6 卡 profiles 和静态检查 | 无本地权重部署，无多卡吞吐/OOM/故障切换实测 |

后续优先完成更大规模同预算消融与最终冻结测试，扩展更多受信任务/指标，增加 OS 沙箱和需要的认证/队列，再接入单卡/六卡本地推理并重新测量。当前不宣称任意插件热加载、任意行业数据或 MCTS。

以下只生成未来规划，不下载模型、不启动推理、不改变 GPU 配置：

~~~bash
python scripts/plan_inference.py --profile single_gpu --available-gpus 1
python scripts/plan_inference.py --profile six_gpu
python scripts/plan_inference.py --profile six_gpu_replicas
python scripts/plan_inference.py --profile six_gpu_quality
~~~

## 文档与提交

- [07 使用与演示指南](docs/07_使用与演示指南.md)：完整命令、界面、报告解释和答辩流程。
- [08 实现与验收对照](docs/08_实现与验收对照.md)：原题逐项映射、证据入口与真实剩余工作。
- [01 实施总方案](docs/01_项目实施总方案.md)、[03 架构设计](docs/03_系统架构与接口.md)、[04 实验设计](docs/04_评测实验与演示.md)：设计与实验路线，未来项不自动算已实现。
- [05 六卡兼容](docs/05_算力预算与六卡兼容.md)：后续部署、硬件预算及待实测内容。
- [06 原始开发清单](docs/06_开发清单与验收矩阵.md)：早期计划；实际状态优先看 08 与证据。

本地 Git 已启用，可用 `git log --oneline` 检查提交。**尚未替用户发布 GitHub 仓库，公开提交仍需用户上传/推送。** 发布前只纳入审核后的公开样例，不上传 .env、凭证、私有数据库或完整运行日志。数据及第三方源码归属见来源索引，项目代码许可证由所有者确定。

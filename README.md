# AlgoForge：可验证的算法能力工厂

基于 [笔试原题](docs/source/exam.txt) 的实施仓库。主场景是银行营销响应预测，迁移场景是短信垃圾信息分类。目标是完成“需求理解 → 知识抽取与检索 → 方案规划 → 代码生成 → 独立验证 → 有限修复 → 能力沉淀”的闭环。

**当前阶段：方案设计与可行性准备，尚非完成的 Agent 产品。** 创建/核验日期：2026-09-28。工程路径：单卡起步，设计兼容最多六张 RTX 4090D。

## 建议阅读顺序

| 文档 | 包含内容 |
|---|---|
| [01 项目实施总方案](docs/01_项目实施总方案.md) | 选题、优先级、最终效果、技术选型、12 天执行路线 |
| [02 数据与知识来源](docs/02_数据与知识来源.md) | 真实数据、来源、字段、切分、防泄漏、知识构建 |
| [03 系统架构与接口](docs/03_系统架构与接口.md) | Agent 角色、状态机、图 schema、接口、沙箱、版本 |
| [04 评测实验与演示](docs/04_评测实验与演示.md) | 真实基线、验收指标、消融、修复、演示与答辩 |
| [05 算力预算与六卡兼容](docs/05_算力预算与六卡兼容.md) | 当前资源、显存/RAM预算、1/2/4/6卡分组与部署预检 |
| [06 开发清单与验收矩阵](docs/06_开发清单与验收矩阵.md) | 题面逐项映射、工时、任务依赖、测试、提交清单 |
| [官方来源索引](docs/SOURCES.md) | 数据、模型、软件和硬件官方链接，以及本地核验方法 |

完整高分准备以真实闭环与证据为核心；方案不承诺某个考试分数。

## 已经完成与尚待实现

| 项目 | 状态 |
|---|---|
| Git 仓库与题面备份 | 已完成，本地 main 分支，未推送远程 |
| 两份 UCI 数据真实下载、行数、哈希与重复检查 | 已完成 |
| 六个 CPU 人工参考基线 | 已实测，仅验证集，最终测试未评分 |
| 初版知识图谱 SQL schema | 已编写，并有约束测试；repository 尚待开发 |
| 单卡到六卡推理 profiles 与规划器 | 已静态校验，未部署 GPU 推理 |
| 公开模型 revision 与结构 | 已核验元信息，未下载权重 |
| 数据契约、SQL、推理配置测试与 lint | 已提供，可运行以下命令复查 |
| 真正 LLM Agent、代码修复、知识回写、UI、沙箱 | 后续开发任务，不能宣称已经完成 |
| 六卡吞吐、显存与故障切换 | 待未来设备到位实测 |

## 现在可运行的命令

前提：Linux、Python 3.10 或 3.11；首次下载/安装需要网络。原始业务数据总量很小，准备步骤不需要 GPU 或 API key。

~~~bash
cd /root/algorithm-capability-factory
python -m venv .venv
.venv/bin/python -m pip install -r requirements-feasibility.txt
.venv/bin/python scripts/verify_data.py
.venv/bin/python scripts/benchmark_feasibility.py
.venv/bin/python -m pytest -q
.venv/bin/ruff check scripts tests
.venv/bin/ruff format --check scripts tests
~~~

requirements-feasibility.txt 锁定本次探针已验证的版本；requirements-feasibility.in 是对应的直接依赖清单。它们不是未来整个 Agent 应用的最终依赖。应用、算法 worker 与 serving 环境要在实现阶段分别固定。

仅查看推理部署规划，**不会启动服务、下载模型或修改显卡配置**：

~~~bash
.venv/bin/python scripts/plan_inference.py --profile single_gpu --available-gpus 1
.venv/bin/python scripts/plan_inference.py --profile six_gpu
.venv/bin/python scripts/plan_inference.py --profile six_gpu_replicas
.venv/bin/python scripts/plan_inference.py --profile six_gpu_quality
~~~

six_gpu 默认三组双卡 32B AWQ 服务；six_gpu_replicas 是六个单卡 14B 副本；six_gpu_quality 是四卡 32B BF16 加两个单卡辅助服务。规划器验证设备重叠、端口、TP 与注意力头数等静态条件，不能代替真实 CUDA/量化/性能测试。

## 可检查的实测证据

- [数据审计](docs/research/data_audit.json)：Bank 41,188 行，SMS 5,574 行，官方归档与内容 SHA256。
- [CPU 基线结果](docs/research/baseline_results.json)：Bank LR 验证 AP 0.1829，常数基线 0.1107；SMS LR 验证 AP 0.9584。
- [代码来源审计](docs/research/code_source_audit.json)：真实 scikit-learn 分发源码的 AST 元信息与哈希。
- [模型版本元信息](docs/research/model_metadata.json)：四个官方模型的固定 revision，推理状态未测。
- [知识 schema 草案](schemas/knowledge_schema.sql)：可执行的 SQLite 初版结构。
- [评测需求清单](examples/task_cases.json)：12 条待运行 Agent 测试需求，不是已经成功的运行报告。

Bank 使用严格通话前特征与原始顺序切分，暂不使用 duration、当前联系上下文和未做时点对齐的宏观变量。银行基线的 F1@0.5 为 0，完整结果如实保留；后续应在验证集选择业务阈值/联系预算。不能把本基线与随机切分、含时长特征的网上分数直接比较。

## 开发起点

接下来先完成 contracts + SQLite repository + 可信 evaluator/sandbox，再连接 LLM 生成。详细依赖与验收见 06 文档。不要先做漂亮页面或六卡调优，再补核心闭环。

题目要求的最终 README 十项将由实现证据补齐：背景目标、架构、schema、Agent 工作流、安装运行、示例数据、生成代码、报告、挑战、扩展方向。当前文档中的目标功能明确标记为设计，禁止将其作为已完成截图或成绩提交。

## 数据、许可和版本控制

原始数据在 data/raw，已排除 Git；运行制品在 artifacts，也排除 Git。小型非敏感审计结果保存在 docs/research 并纳入版本控制。数据来自 UCI，许可与归属见来源索引；真实代码元信息来自 scikit-learn 的 BSD-3-Clause 代码。代码许可证在正式发布时由项目所有者确定。

本仓库未包含凭据、模型权重、外部业务数据或真实客户内部资料。Git 初始化如无既有作者身份，使用仅限本仓库的 Project Bootstrap / bootstrap@localhost；正式开发可设置真实作者信息。

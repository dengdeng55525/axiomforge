# AxiomForge · 知衡文档中心

这里的文档按“先跑起来、再理解设计、最后复核结果”的顺序组织。首页 [README.md](../README.md)串联项目目标、系统架构、运行方法、代码示例和验证结果；本目录进一步展开接口约定、配置细节、数据协议与实验方法。

首页 README 提供项目演示视频和当前仓库实际框架图，用于快速了解产品界面与端到端闭环；需要继续核对 Agent 合约、知识图谱 schema、数据切分、部署配置、验证报告和扩展边界时，沿本页目录进入对应专题文档。

- [项目演示视频：工作台与端到端闭环](../display/display.mp4)
- [项目演示视频：能力库与来源探索](../display/display2.mp4)
- [AxiomForge 系统框架图](../AxiomForge_Framework.svg)

## 按目标阅读

| 目标 | 推荐入口 |
| --- | --- |
| 第一次运行 Mock 闭环 | [使用与演示指南](07_使用与演示指南.md) |
| 理解 Agent 和图谱 | [系统架构与接口](03_系统架构与接口.md) |
| 查看工具选型、LangChain 与 OpenAI 接入 | [技术选型与框架集成](14_技术选型与框架集成.md) |
| 查看 Agent 预算、事件时序与安全回放 | [Agent 观测与回放](15_Agent观测与回放.md) |
| 检查知识卡质量与运行制品完整性 | [知识治理与可复现交付](16_知识治理与可复现交付.md) |
| 检查数据是否可复现 | [数据与知识来源](02_数据与知识来源.md)、[来源索引](SOURCES.md) |
| 复核功能实现与验收依据 | [实现与验收对照](08_实现与验收对照.md)、[创新机制与工程验证](13_创新点与加分项演示.md) |
| 阅读报告和前端 | [前端与报告说明](11_前端与报告说明.md)、[交互工作台与参考设计](12_交互工作台与参考设计.md) |
| 快速理解界面与截图 | [前端截图与阅读路径](18_前端截图与阅读路径.md) |
| 复核 Agent 运行质量 | [Agent Harness 离线评测](17_Agent_Harness_离线评测.md) |
| 规划 1–4 张 4090D | [算力预算与四卡兼容](05_算力预算与四卡兼容.md) |
| 扩展指标和模板 | [插件扩展指南](10_插件扩展指南.md) |
| 开展可复现评测 | [评测实验与演示](04_评测实验与演示.md)、[使用与演示指南](07_使用与演示指南.md) |

## 文档目录

- [01 项目实施总方案](01_项目实施总方案.md)：目标、优先级和技术决策。
- [02 数据与知识来源](02_数据与知识来源.md)：公开数据、切分、防泄漏和知识来源。
- [03 系统架构与接口](03_系统架构与接口.md)：Agent 合约、状态机、schema、检索和 API。
- [04 评测实验与演示](04_评测实验与演示.md)：验证分层、实验矩阵和评测脚本。
- [05 算力预算与四卡兼容](05_算力预算与四卡兼容.md)：硬件档位和本地模型规划。
- [06 开发清单与验收矩阵](06_开发清单与验收矩阵.md)：开发任务和发布前检查。
- [07 使用与演示指南](07_使用与演示指南.md)：命令、Web、API、报告和 FAQ。
- [08 实现与验收对照](08_实现与验收对照.md)：需求与实现证据映射、实现方式与验收重点。
- [09 知识抽取评估](09_知识抽取评估.md)：抽取来源、审查、评估和复现。
- [10 插件扩展指南](10_插件扩展指南.md)：受信指标和模板注册边界。
- [11 前端与报告说明](11_前端与报告说明.md)：结论、证据、原始 JSON 和图谱展示层。
- [12 交互工作台与参考设计](12_交互工作台与参考设计.md)：参考交互、页面入口和截图验收。
- [13 创新点与加分项演示](13_创新点与加分项演示.md)：创新机制与工程价值、仓库抽取、搜索修复、资源分析和接口导出。
- [14 技术选型与框架集成](14_技术选型与框架集成.md)：LangChain 角色链、OpenAI SDK Responses、模型切换、知识图谱工具和框架选型理由。
- [15 Agent 观测与回放](15_Agent观测与回放.md)：角色 span、工具事件、预算视图、只读事件回放和前端观测台。
- [16 知识治理与可复现交付](16_知识治理与可复现交付.md)：能力卡质量闸门、版本/来源/关系校验和运行制品 SHA256 证明。
- [17 Agent Harness 离线评测](17_Agent_Harness_离线评测.md)：版本化用例、只读报告评测、游标回放和事件脱敏检查。
- [18 前端截图与阅读路径](18_前端截图与阅读路径.md)：截图画廊、页面职责、API 事实来源和截图复现规则。

## 证据目录

- [execution_validation.json](research/execution_validation.json)：后端测试、样例运行和实验索引。
- [frontend_validation.json](research/frontend_validation.json)：前端构建、浏览器测试和本地 UI 联调。
- [local_vllm_validation.json](research/local_vllm_validation.json)：本地 14B 单卡和四副本启动验证记录。
- [budget_beam_validation.json](research/budget_beam_validation.json)：运行预算、唯一候选扩展、真实本地模型自动修复、报告和知识回写回归；含 389 项测试及浏览器核对结果。
- [innovation_validation.json](research/innovation_validation.json)：加分项增强测试、固定提交抽取、资源分析和接口制品索引。
- [harness_gpu_validation.json](research/harness_gpu_validation.json)：Agent Harness 用例、suite/API/CLI 入口和 0–4 卡 GPU 状态栏验收记录。
- [ci_budget_validation.json](research/ci_budget_validation.json)：预算浮点精度回归、CPU CI 历史失败定位、修复验证及 GitHub CPU / Web 检查结果。
- [data_audit.json](research/data_audit.json)：公开数据来源、哈希和切分事实。
- [deepseek_model_discovery.json](research/deepseek_model_discovery.json)：模型名称与 API ID 的发现记录。
- [code_source_audit.json](research/code_source_audit.json)：源码来源和许可审查。
- [host_resources.json](research/host_resources.json)：机器资源观察；性能结论以目标环境实测为准。

## 从文档进入实现

专题文档通过三个层次连接工程设计与运行结果：

1. **代码入口**：仓库中存在可调用实现。
2. **可复现示例**：有公开报告、代码、哈希和 manifest。
3. **独立验证**：测试或运行索引中有命令、时间、结果和限制。

研发复核可沿“代码入口 → 示例制品 → 验证记录”逐层查看：功能对应实现，部署对应环境记录，质量与性能对应具体实验。扩展方向单独列入路线，便于继续迭代。

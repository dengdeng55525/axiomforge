# AlgoForge 文档中心

这里的文档按“先跑起来、再理解设计、最后审计证据”的顺序组织。首页 [README.md](../README.md) 只保留入口、核心架构和最短复现路径；本目录承载详细设计和实验口径。

## 按目标阅读

| 目标 | 推荐入口 |
| --- | --- |
| 第一次运行 Mock 闭环 | [使用与演示指南](07_使用与演示指南.md) |
| 理解 Agent 和图谱 | [系统架构与接口](03_系统架构与接口.md) |
| 检查数据是否可复现 | [数据与知识来源](02_数据与知识来源.md)、[来源索引](SOURCES.md) |
| 对照笔试评分项 | [实现与验收对照](08_实现与验收对照.md)、[五项创新依据与演示](13_创新点与加分项演示.md) |
| 阅读报告和前端 | [前端与报告说明](11_前端与报告说明.md)、[交互工作台与参考设计](12_交互工作台与参考设计.md) |
| 规划 1–4 张 4090D | [算力预算与四卡兼容](05_算力预算与四卡兼容.md) |
| 扩展指标和模板 | [插件扩展指南](10_插件扩展指南.md) |
| 准备答辩实验 | [评测实验与演示](04_评测实验与演示.md)、[使用与演示指南](07_使用与演示指南.md) |

## 文档目录

- [01 项目实施总方案](01_项目实施总方案.md)：目标、优先级和技术决策。
- [02 数据与知识来源](02_数据与知识来源.md)：公开数据、切分、防泄漏和知识来源。
- [03 系统架构与接口](03_系统架构与接口.md)：Agent 合约、状态机、schema、检索和 API。
- [04 评测实验与演示](04_评测实验与演示.md)：验证分层、实验矩阵和答辩脚本。
- [05 算力预算与四卡兼容](05_算力预算与四卡兼容.md)：硬件档位和本地模型规划。
- [06 开发清单与验收矩阵](06_开发清单与验收矩阵.md)：开发任务和发布前检查。
- [07 使用与演示指南](07_使用与演示指南.md)：命令、Web、API、报告和 FAQ。
- [08 实现与验收对照](08_实现与验收对照.md)：题面逐项证据映射、实现方式与验收重点。
- [09 知识抽取评估](09_知识抽取评估.md)：抽取来源、审查、评估和复现。
- [10 插件扩展指南](10_插件扩展指南.md)：受信指标和模板注册边界。
- [11 前端与报告说明](11_前端与报告说明.md)：结论、证据、原始 JSON 和图谱展示层。
- [12 交互工作台与参考设计](12_交互工作台与参考设计.md)：参考交互、页面入口和截图验收。
- [13 创新点与加分项演示](13_创新点与加分项演示.md)：五项创新评分依据、仓库抽取、搜索修复、资源分析和接口导出。

## 证据目录

- [execution_validation.json](research/execution_validation.json)：后端测试、样例运行和实验索引。
- [frontend_validation.json](research/frontend_validation.json)：前端构建、浏览器测试和本地 UI 联调。
- [local_vllm_validation.json](research/local_vllm_validation.json)：本地 14B 单卡和四副本启动验证记录。
- [budget_beam_validation.json](research/budget_beam_validation.json)：运行预算、唯一候选扩展、真实本地模型自动修复、报告和知识回写回归；含 389 项测试及浏览器核对结果。
- [innovation_validation.json](research/innovation_validation.json)：加分项增强测试、固定提交抽取、资源分析和接口制品索引。
- [ci_budget_validation.json](research/ci_budget_validation.json)：预算浮点精度回归、CPU CI 历史失败定位、修复验证及 GitHub CPU / Web 检查结果。
- [data_audit.json](research/data_audit.json)：公开数据来源、哈希和切分事实。
- [deepseek_model_discovery.json](research/deepseek_model_discovery.json)：模型名称与 API ID 的发现记录。
- [code_source_audit.json](research/code_source_audit.json)：源码来源和许可审查。
- [host_resources.json](research/host_resources.json)：机器资源观察；性能结论以目标环境实测为准。

## 如何判断“已完成”

文档采用三层状态：

1. **代码入口**：仓库中存在可调用实现。
2. **可复现示例**：有公开报告、代码、哈希和 manifest。
3. **独立验证**：测试或运行索引中有命令、时间、结果和限制。

答辩与复核可沿“代码入口 → 示例制品 → 验证记录”逐层查看：功能对应实现，部署对应环境记录，质量与性能对应具体实验。扩展方向单独列入路线，便于继续迭代。

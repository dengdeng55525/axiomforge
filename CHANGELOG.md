# 变更记录

记录 AxiomForge · 知衡的版本能力、工程改进与兼容性变化。发布标签固定源码快照，发布说明提供安装入口与验证依据。

## 0.2.0 · 2026-10-02

AxiomForge · 知衡首个 GitHub Release，汇集完整算法工作流、研发工作台与可复现知识资产。

- 统一 AxiomForge · 知衡品牌、仓库与 Python 包标识，提供 `axiomforge` CLI，保留 `algoforge` 兼容入口。
- 增加离线 Agent Evaluation Harness：版本化用例、角色与事件检查、候选和修复证据、预算与敏感字段校验，支持 CLI、API 与 suite 汇总。
- 增加 0–4 卡 GPU 状态栏和 `/system/gpus` 只读探测，展示设备、利用率、显存与温度。
- 重构 README 的工程阅读路径，提供八张按主题组织的界面截图、纵向架构图、截图复现工具与来源哈希清单。

- 增加只读知识治理质量闸门：校验来源、状态、版本、内容哈希、图谱关系和已验证经验，并提供 API、CLI、CI 与知识页入口。
- 增加运行制品完整性核验：按需生成输入、代码、验证、报告四类制品的 SHA256 清单，限制路径、符号链接、文件大小和总字节预算。
- 增加知识完整性与制品核验前端面板，默认折叠详细 JSON，处理路由切换和延迟响应隔离。
- 将 Markdown 报告改为“结论与证据优先、完整 JSON 折叠”的可读评审格式。
- 增加现代 Agent 观测台：记录 `AGENT_*` / `TOOL_*` 生命周期事件、结构化输出摘要、调用预算、token 用量和运行终态。
- 增加 `GET /runs/{run_id}/agent-trace` 及 `through_sequence` 只读回放；报告附带 `agent_trace`，Vue 运行报告支持摘要、折叠详情和事件游标。
- 增加观测投影的旧报告兼容、敏感字段白名单、重复序列拒绝、缺失框架/预算空值语义和未来事件隔离测试。
- 增加真实 `gpt-5.5` Responses + LangChain SMS 双候选验证证据，运行 ID 为 `660682f3cf324bf1938b78c70f2fce8c`，AP 为 `0.9583895772` 与 `0.9598341674`，两候选均通过。
- 更新工具选型、系统架构、API 规格和文档索引，补充 LangChain Core、OpenAI SDK、SQLite、NetworkX、FastAPI、Vue/Streamlit 的职责与复核入口。

- 修复预算报告由绝对时钟相减引入的浮点漂移；保留预算原值，增加分数时钟与长运行主机回归。
- 调整 README 阅读顺序，补充创新机制、工程价值和实现证据映射，同步使用指南和验收文档。
- 增加固定 Git 提交的 Python 仓库能力抽取、源码溯源和幂等版本化导入。
- 增加候选 AP/训练耗时/峰值 RSS 的 Pareto 分析、父子变体变化和 Web/HTML 报告展示。
- 增加 analyze-run 与 export-openapi 命令，以及资源分析、接口导出与运行证据导航。
- 运行预算由表单和可核验的用户数字时限决定，忽略解释器猜测的预算，并记录采用或忽略的原因。
- Beam 扩展按唯一算法变体计算容量；可选扩展合约失败时保留已验证父候选、警告和知识回写。
- 增加 Vue 3 工作台和同源 FastAPI UI 网关。
- 增加 D3 知识图谱探索：筛选、缩放、1/2 跳聚焦、来源定位、能力版本和验证路径。
- 报告页面分离结论、证据和原始 JSON；支持候选切换、代码/报告导出、取消和有限轮询。
- 增加 OpenAI Responses、DeepSeek、Mock、本地 OpenAI 兼容 HTTP 四种 Provider 展示和四卡 14B 静态规划。
- 增加图谱探索接口、前端 CI、Python 回归、Playwright 夹具和本地联调证据。
- 将公开数据、Agent 合约、验证状态、失败修复和知识回写边界写入文档。

## 0.1.0 · 原型基线

- 完成 Python CLI、FastAPI、SQLite 知识库、银行/SMS 任务协议、受限执行器和 JSON/Markdown/HTML 报告。
- 支持候选比较、有限 Beam Search、多轮修复、来源审计、能力版本和验证结果回写。
- 提供 Mock 离线闭环和 DeepSeek API 接入。

版本与运行证据以 Git 提交和 `docs/research/*_validation.json` 为准。

# 变更记录

项目当前处于迭代阶段。以下记录面向评审和复现，版本语义以每次发布说明为准。

## Unreleased · 当前主分支

- 增加固定 Git 提交的 Python 仓库能力抽取、源码溯源和幂等版本化导入。
- 增加候选 AP/训练耗时/峰值 RSS 的 Pareto 分析、父子变体变化和 Web/HTML 报告展示。
- 增加 analyze-run 与 export-openapi 命令，以及 README 十项加分点的实现与证据导航。
- 运行预算由表单和可核验的用户数字时限决定，忽略解释器猜测的预算，并记录采用或忽略的原因。
- Beam 扩展按唯一算法变体计算容量；可选扩展合约失败时保留已验证父候选、警告和知识回写。
- 增加 Vue 3 工作台和同源 FastAPI UI 网关。
- 增加 D3 知识图谱探索：筛选、缩放、1/2 跳聚焦、来源定位、能力版本和验证路径。
- 报告页面分离结论、证据和原始 JSON；支持候选切换、代码/报告导出、取消和有限轮询。
- 增加 DeepSeek、Mock、本地 OpenAI 兼容 HTTP 三种 Provider 展示和四卡 14B 静态规划。
- 增加图谱探索接口、前端 CI、Python 回归、Playwright 夹具和本地联调证据。
- 将公开数据、Agent 合约、验证状态、失败修复和知识回写边界写入文档。

## 0.1.0 · 原型基线

- 完成 Python CLI、FastAPI、SQLite 知识库、银行/SMS 任务协议、受限执行器和 JSON/Markdown/HTML 报告。
- 支持候选比较、有限 Beam Search、多轮修复、来源审计、能力版本和验证结果回写。
- 提供 Mock 离线闭环和 DeepSeek API 接入。

版本与运行证据以 Git 提交和 `docs/research/*_validation.json` 为准。

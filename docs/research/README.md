# 验证记录说明

这里保存机器可读的验证索引。文件名中的 `preparation` 表示准备阶段快照，不能和最终代码回归混用。

| 文件 | 状态 | 用途 |
| --- | --- | --- |
| [validation_manifest.json](validation_manifest.json) | 当前总索引 | 汇总后端、前端、远程 CI、Mock 联调和限制 |
| [execution_validation.json](execution_validation.json) | 后端/历史执行记录 | 测试、真实样例、实验与运行证据 |
| [frontend_validation.json](frontend_validation.json) | 前端专项记录 | Vue 构建、Playwright、截图和网关联调 |
| [preparation_checks.json](preparation_checks.json) | 历史快照 | 早期准备状态，不代表当前实现 |
| [data_audit.json](data_audit.json) | 数据事实 | 来源、哈希、行数和切分协议 |
| [deepseek_model_discovery.json](deepseek_model_discovery.json) | 模型发现记录 | 产品名称和实际 API ID 的映射 |

验证索引记录的是命令、版本、结果和限制；它不承诺未来运行仍然得到相同模型输出，也不把 Mock 结果当作真实 LLM 效果。

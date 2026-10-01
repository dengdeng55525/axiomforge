# 可复核示例与交付物

这个目录保存可以直接阅读、下载和复核的示例输入与历史运行证据。它把「自然语言需求 → 能力检索 → 候选代码 → 自动验证 → 修复/比较 → 知识回写」拆成可定位的文件，适合答辩时逐步展示，也适合作为 API、CLI 和前端的固定夹具。

示例包来自项目自己的脱敏导出工具，保留原始运行的模式、状态、候选、每次尝试、指标和 SHA-256；数据集、预测明细、原始 LLM 请求/响应、日志、凭据和本地 SQLite 库按脱敏规则省略。`manifest.json` 中的 `source_report_sha256` 用于确认它来自某次历史运行导出；阅读时以报告中的 `mode`、`provider` 和 `status` 为准。

`source_report` 可能指向被 `.gitignore` 排除的本机 `artifacts/runs/`，因此新克隆仓库中找不到它是预期行为；公开 bundle 自身已经包含复核所需的报告、候选代码、验证记录和文件哈希。

## 示例目录

| 示例 | 场景 | 运行方式 | 展示内容 | 入口 |
| --- | --- | --- | --- | --- |
| `evidence/bank_repair` | 银行营销响应预测 | DeepSeek API 历史运行，注入一次明确接口故障 | 两个候选、失败尝试、有限修复链、验证检查和知识回写 | [`report.html`](evidence/bank_repair/report.html) |
| `evidence/bank_beam` | 银行营销响应预测 | DeepSeek API 历史运行，Beam 候选搜索 | 六个候选、统一协议下的指标/资源比较、候选选择 | [`report.html`](evidence/bank_beam/report.html) |
| `evidence/sms_transfer` | 短信垃圾信息分类 | DeepSeek API 历史运行，跨场景迁移 | 文本 TF-IDF 管道、正类概率接口和同一验证协议的迁移 | [`report.html`](evidence/sms_transfer/report.html) |
| [`task_cases.json`](task_cases.json) | 银行 + 短信 | 规划用例，执行状态以运行报告记录 | 需求、数据集、期望的接口或约束行为 | JSON 输入清单 |
| [`evidence/knowledge_extraction.json`](evidence/knowledge_extraction.json) | 行业能力抽取 | DeepSeek API 历史抽取记录 | 来源定位、能力卡、结构审计与抽取边界 | JSON 证据 |

三份报告均提供同名的 `report.json`、`report.md` 和 `report.html`。`report.json` 是机器可读事实源；Markdown 先展示结论、候选对比、检查证据和资源，再折叠完整审计 JSON，适合代码审查和 diff；HTML 适合浏览器演示。候选目录中每个 `model.py` 都配有 `verification.json`，若某次尝试没有生成代码，则只保留描述该事实的 `metadata.json`，不会补造代码或指标。

## 五分钟本地演示（无需模型凭证）

以下命令从公开 UCI 数据下载/校验开始，用规则型 Mock provider 跑一条可复现验证闭环。Mock 会执行训练、预测、检查和报告生成，报告中保留 `mode=mock` 标记。

```bash
python scripts/verify_data.py
python -m capability_factory init --provider mock
python -m capability_factory run \
  --dataset bank \
  --provider mock \
  --description '预测银行客户是否订购定期存款，只使用通话前特征，禁止 duration，比较两个候选。' \
  --search compare \
  --max-candidates 2 \
  --max-repairs 2
```

命令输出的运行 ID 可用于读取事实报告。无需依赖 `jq` 的查看方式如下：

```bash
python -m capability_factory report <RUN_ID> --format html --output artifacts/demo-report.html
python - <<'PY'
import json
from pathlib import Path

run_id = "<RUN_ID>"
report = json.loads(Path("artifacts/runs", run_id, "report.json").read_text())
print({key: report.get(key) for key in (
    "run_id", "status", "mode", "provider", "dataset_id",
    "selected_candidate_id", "quality_status", "knowledge_writeback",
)})
for candidate in report.get("candidates", []):
    print(candidate.get("candidate_id"), candidate.get("status"), candidate.get("metrics"))
PY
```

要展示真实 LLM 调用，先配置 `.env` 中的 `DEEPSEEK_API_KEY`，再把 provider 改为 `deepseek`；这可能产生费用，且网络/服务端限流会影响运行时间。不要把密钥写入示例、报告或提交历史。

## 如何阅读一份报告

报告顶层字段对应闭环中的事实：

| 字段 | 含义 | 复核方式 |
| --- | --- | --- |
| `request` / `task_spec` | 用户需求与解释后的数据、标签、指标、约束 | 检查禁止 `duration`、正类和切分协议 |
| `evidence` / `provenance` | 检索到的能力、来源定位、图路径与哈希 | 跳转来源文件，核对事实关联与来源哈希 |
| `search_tree` / `candidates` | 规划产生的候选及每次代码尝试 | 对照候选代码和 `attempt_N/verification.json` |
| `events` | 解释、规划、生成、审查、修复、回写的有序记录 | 检查修复是否由真实错误触发 |
| `knowledge_writeback` | 运行、制品、失败经验和能力版本的回写结果 | 与 `knowledge/runtime_schema.sql` 对照 |
| `quality_status` | 验证集 AP 与类别占比基线的关系 | `above_prevalence`、`baseline_or_worse` 或 `not_evaluated` |
| `usage` / `timing` | 调用次数、token 记录和耗时 | 作为该次运行记录；SLA 和账单需要独立统计 |

`candidate.status=passed` 只表示执行和强制检查通过；质量基线比较单独由 `quality_status` 表达。缺失指标、缺失检查和未完成候选不能按零分或通过处理。所有候选共享同一数据切分与验证协议，才能比较 AP、F1、Lift 和资源记录。

## 能力抽取证据

`evidence/knowledge_extraction.json` 是抽取器的脱敏输出，包含来源 ID、来源哈希/定位、9 张候选能力卡和聚合用量。它不把 `verified=true` 之类的模型字段当成验证证明；结构校验和 gold 对照保存在本机的审计文件中，不混入公开抽取样例。建议同时运行离线结构审计：

```bash
python scripts/evaluate_extraction.py \
  --artifact artifacts/ingestion/deepseek_extraction.json \
  --gold knowledge/extraction_gold.json \
  --output artifacts/ingestion/extraction_evaluation.json
```

抽取评估的 precision/recall/F1 只在输出包含规范化断言四元组时计算；自然语言能力卡只有结构和出处检查时，结果会明确标记为未完成语义评测，不会伪造分数。

## 导出新的可公开示例

使用 allowlist 导出工具，工具会检查运行 ID、候选代码哈希、报告一致性和凭据模式，并拒绝覆盖已有 bundle：

```bash
python scripts/export_evidence.py \
  --run-id <RUN_ID> \
  --name my-public-example \
  --note '说明数据集、provider 和实验目的'
```

导出前应检查 `report.json` 中没有业务隐私；导出器只复制报告和候选的 `model.py`、`verification.json`、`metadata.json`。任何新增 bundle 都应在本文件表格中登记，并说明它证明什么、没有证明什么。

## 与知识图谱和前端的关系

运行验证后，图谱中的 `ValidationRun`、`Artifact`、`Capability` 和 `FailureExperience` 节点会通过 `EVALUATES`、`IMPLEMENTS`、`REPAIRS` 等关系关联。前端知识探索页使用这些真实关系显示来源和验证路径；示例 bundle 不包含本地数据库，因此只能用于静态报告和代码证据复核。完整 schema 见 [`knowledge/README.md`](../knowledge/README.md) 与 [`runtime_schema.sql`](../knowledge/runtime_schema.sql)，交互流程见 [`docs/07_使用与演示指南.md`](../docs/07_使用与演示指南.md)。

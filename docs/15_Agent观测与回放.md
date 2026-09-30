# Agent 观测台与事件回放

AlgoForge 为每次运行提供一份可读、可筛选、可回放的 Agent 观测投影。观测台把角色交接、只读工具、预算消耗和终态事件放到同一条时间线上，帮助评审回答三个问题：当前运行走到了哪一步、消耗了多少资源、某个结论来自哪一条已发生的事实。

观测投影由 `src/capability_factory/observability.py::build_agent_trace` 生成。运行报告仍是事实源，投影只读取报告中的事件和有限 provenance 字段。投影不会重新调用模型、知识库或执行器，也不会修改报告。

## 1. 设计原则

### 1.1 事件先于界面

Workflow 在角色和工具的边界写入事件；API 和 Vue 组件根据事件生成当前视图。报告、CLI、API 和 Web 使用同一套事件序列，因此页面刷新、离线导出和后续审计都能得到一致的结果。

### 1.2 回放只显示游标之前的事实

`through_sequence=N` 会截取 `sequence <= N` 的事件，并重新计算 span、预算和知识证据。未来的 token、能力卡、角色状态和终态不会出现在游标视图中。游标只能定位到报告里已经存在的非负整数序列；非法或超范围游标返回 HTTP 400。

### 1.3 结构化摘要代替隐式推理

观测台显示角色名、输入输出 schema、耗时、状态、候选 ID、返回字段和能力卡 ID。提示词、原始响应、生成代码和隐式推理内容继续保存在受控的运行制品路径或导出边界内，观测投影不会复制这些内容。这样可以在答辩中展示协作过程，同时保持报告体积、隐私边界和回放安全性可控。

### 1.4 缺失事实保持空值

历史报告没有 Agent span 时，投影使用旧的 `LLM_RESPONSE`、`MOCK_RESPONSE` 和 `KNOWLEDGE_RETRIEVED` 事件生成兼容摘要，并标注来源事件。框架版本、预算上限、结束时间和工具输出缺少时保留 `null`，页面显示“未记录”。系统不会根据页面顺序推断未发生的步骤。

## 2. 事件与 span 协议

一次完整运行的事件序列包含以下事件类型：

| 事件 | 作用 | 典型 data 字段 |
| --- | --- | --- |
| `AGENT_STARTED` | 角色开始一次调用 | `span_id`、`name`、`role`、`attempt`、`schema`、`model` |
| `AGENT_COMPLETED` | 角色完成并通过合约 | `span_id`、`duration_seconds`、`result_keys`、`status` |
| `AGENT_REJECTED` | 角色响应未通过结构化合约 | `span_id`、`error_type`、`schema`、`attempt` |
| `AGENT_FAILED` | 角色因异常、取消或预算终止 | `span_id`、`error_type`、`status` |
| `TOOL_STARTED` | 只读工具开始运行 | `span_id`、`name`、`role`、`schema` |
| `TOOL_COMPLETED` | 只读工具返回摘要 | `span_id`、`duration_seconds`、`returned_count`、`capability_ids` |
| `TOOL_FAILED` | 只读工具发生可观察错误 | `span_id`、`error_type`、`status` |
| `LLM_RESPONSE` / `MOCK_RESPONSE` | 模型调用的用量与响应审计 | `role`、`input_tokens`、`output_tokens`、`cached_input_tokens`、`seconds` |
| `KNOWLEDGE_RETRIEVED` | 兼容旧报告的检索事实 | `capability_ids`、`count`、`tool` |
| `RUN_BUDGET_APPLIED` | 记录运行采用的有效时限 | `effective_seconds` |
| `RUN_FINISHED` | 记录整次运行的最终状态 | `status`、`finished_at` |

`AGENT_STARTED` 与同一 `span_id` 的终态事件组成 Agent span；`TOOL_STARTED` 与工具终态组成工具 span。span 的核心字段如下：

```json
{
  "span_id": "agent-planner-0",
  "kind": "agent",
  "name": "planner",
  "role": "planner",
  "status": "completed",
  "attempt": 0,
  "candidate_id": null,
  "started_at": "2026-09-30T12:00:01+00:00",
  "finished_at": "2026-09-30T12:00:14+00:00",
  "duration_seconds": 13.0,
  "start_sequence": 4,
  "end_sequence": 5,
  "schema": "PlanSet",
  "error_type": null,
  "output_summary": {
    "result_keys": ["plans", "search_space"],
    "returned_count": 2,
    "capability_ids": ["capability:bank-logistic:v1"]
  },
  "model": "gpt-5.5"
}
```

示例使用脱敏字段说明协议，不代表某一条历史报告的固定 sequence。终态状态可以是 `completed`、`rejected`、`failed` 或 `cancelled`；进行中的 span 保留 `finished_at=null` 与 `duration_seconds=null`。

## 3. API 用法

运行报告接口会附带完整游标位置的 `agent_trace`：

```bash
curl -s http://127.0.0.1:8000/runs/$RUN_ID/report \
  | python -m json.tool \
  | sed -n '/"agent_trace"/,$p'
```

需要单独获取观测投影时调用：

```bash
# 当前完整投影
curl -s http://127.0.0.1:8000/runs/$RUN_ID/agent-trace | python -m json.tool

# 回放到 sequence=12；只显示 0–12 已发生的事实
curl -s 'http://127.0.0.1:8000/runs/'"$RUN_ID"'/agent-trace?through_sequence=12' \
  | python -m json.tool
```

接口返回结构：

| 字段 | 含义 |
| --- | --- |
| `schema_version` | 当前投影协议版本，现为 `1.0` |
| `run_id`、`status`、`mode` | 运行身份、状态和模型路线 |
| `framework` | `name` 与 `version`；历史缺失时为 `null` |
| `event_count`、`total_event_count` | 当前游标内和完整报告的有效事件数量 |
| `cursor_sequence`、`is_replay` | 当前显示位置和是否为回放视图 |
| `spans` | Agent / Tool 的生命周期摘要 |
| `budget` | 调用次数、token、时间墙钟和各项上限 |
| `evidence` | 游标内已发生的能力卡片及检索次数 |
| `events` | 已脱敏的事件索引，不包含 prompt、代码或响应原文 |

`budget.usage_source` 说明当前统计来自事件还是终态报告。回放游标只读取游标范围内的事件；完整终态投影可以读取报告中的最终用量聚合。输入、输出或缓存 token 缺失时，相应字段返回 `null`。

## 4. Vue 工作台交互

[AgentTracePanel.vue](../web/src/components/AgentTracePanel.vue) 集成在运行报告页。首屏展示四类摘要：已完成 Agent span、只读工具检索、token 消耗和事件游标。详细时序和预算放在可折叠区域，适合先看结论再展开证据。

观测面板包含以下交互：

1. **实时摘要**：报告轮询后更新已落盘的事件和预算。
2. **事件滑块**：拖动游标请求 `through_sequence`，只投影已发生信息。
3. **span 详情**：展开 Agent 或 Tool 可查看 schema、attempt、候选 ID、状态、耗时和结构化输出摘要。
4. **预算进度**：展示调用、时间和 token 的已使用量；缺少上限时显示“上限未记录”。
5. **安全提示**：页面明确提示“摘要来自事件事实”，原始 JSON 继续放在报告的折叠区。

这套交互对应现代 Agent 产品的可观测性要求：用户能理解当前状态、资源边界和工具结果，评审能沿 sequence 复现阶段边界，开发者能定位合约拒绝、工具失败和预算终止。

## 5. 与 LangChain 的关系

LangChain Core 负责角色链和工具 schema，Workflow 负责阶段状态、预算、候选搜索和终止条件。`provenance.agent_runtime` 记录框架名、版本、角色链、检索工具和 `external_tracing=false`；本地事件提供无需外部 SaaS 的审计路径。角色调用的响应摘要通过 `LLM_RESPONSE` 事件进入统一预算视图，`StructuredTool` 的实际调用通过 `TOOL_STARTED` / `TOOL_COMPLETED` 事件进入知识证据视图。

项目在 Agent 运行层显式关闭外部 LangSmith 追踪。这样运行状态、敏感字段和调用费用都留在本地报告与服务边界内，评审可直接查看脱敏后的事实投影。

## 6. 测试和复核

核心投影测试覆盖：

- 成功 Agent / Tool span 的开始、完成和输出摘要；
- 合约拒绝、异常失败和取消的终态；
- 运行中 span 不生成虚假结束时间或耗时；
- 旧报告事件的兼容投影；
- 游标回放对未来 token、能力卡和 span 的隔离；
- 缺失预算、缺失框架版本和恶意字段的保守处理；
- 投影过程不修改原始报告。

执行：

```bash
python -m pytest -q tests/test_observability.py
node node_modules/@playwright/test/cli.js test web/tests/agent-trace.spec.ts --reporter=list
```

前端端到端测试通过 Playwright 验证报告页中 Agent 观测面板的摘要、折叠详情、滑块回放和错误提示。后端测试位于 [tests/test_observability.py](../tests/test_observability.py)；报告页组件位于 [web/src/components/AgentTracePanel.vue](../web/src/components/AgentTracePanel.vue)。

## 7. 复核边界和后续扩展

观测台记录已发生的事件和结构化摘要，适合研发审计、答辩演示和运行故障定位。它不重放模型生成，不重算指标，也不替代独立验证器。模型原始请求/响应的留存范围由运行制品和导出策略决定，观测投影继续遵守脱敏边界。

后续可以在保持当前事件协议的基础上增加 OpenTelemetry span 导出、按候选聚合的成本视图、人工审批节点和跨运行比较。新增字段应通过 `schema_version` 演进，并保持旧报告的 `null` 兼容语义。

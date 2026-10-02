# Agent Harness：离线评测与安全回放

AxiomForge 内置一个轻量的本地 Agent Harness，用于在不调用模型、不执行生成代码、不依赖在线观测平台的条件下，复核一次运行是否满足预先登记的工作流契约。

Harness 读取已经持久化的 `report.json` 事实，使用版本化的 JSON case rubric 完成以下检查：

- 运行终态和数据集契约；
- 需求理解、知识检索、规划、生成、验证、修复、比较、沉淀等事件；
- interpreter、planner、coder、reviewer、repair_coder 的角色协作链；
- 候选数量、选中候选、AP 门槛和资源预算；
- 修复次数与修复前后哈希证据；
- Agent trace 中禁止携带 prompt、system、api_key 等字段。

每项检查都输出 `observed`、`expected` 和证据路径，结果符合 `agent-harness.v1` JSON 契约。`hard` 检查决定最终是否通过，未配置的可选指标会标记为 warning，保留评分透明度。

## 使用方式

列出当前登记的评测用例：

```bash
axiomforge harness cases
```

将 `RUN_ID` 设置为当前工作空间中已经保存的运行编号，对已完成运行执行只读评测：

```bash
axiomforge harness evaluate "$RUN_ID" \
  --case bank_e2e \
  --output artifacts/harness/bank_e2e.json
```

执行全部登记用例并生成回归汇总。默认目录同时包含银行、短信和必须发生修复的用例，单个运行会明确报告不匹配的用例；场景回归可通过 `--cases` 选择一组适用的检查规则：

```bash
axiomforge harness suite "$RUN_ID" \
  --output artifacts/harness/suite.json
```

回放脱敏后的 Agent 时间线：

```bash
axiomforge harness replay "$RUN_ID" --through 12
```

服务端提供同一份契约：

```text
GET /harness/cases
GET /runs/{run_id}/harness?case_id=bank_e2e
GET /runs/{run_id}/harness-suite
```

用例存放在 [`configs/agent_harness_cases.json`](../configs/agent_harness_cases.json)，可以添加新的任务场景和检查门槛。`suite` 返回 `agent-harness-suite.v1` 聚合契约，包含每个用例的检查结果、通过数和总体状态。Harness 只读取运行事实，不修改 SQLite、报告、制品或知识图谱；它适合 CI、运行复核、回归测试和多模型对比。

## 设计边界

Harness 与生成工作流分离：Workflow 负责完成任务和保存证据，Harness 负责基于证据进行独立评测。运行中的 prompt、模型响应和代码制品不会被 Harness 再次加载，避免评测过程引入副作用。Agent trace 使用已有的游标回放投影，因此 `--through` 可以复核某一时刻之前的预算、角色和知识证据。

实现入口：[`src/capability_factory/harness.py`](../src/capability_factory/harness.py)。测试覆盖成功闭环、事件缺失、数据集不匹配、敏感字段和 API 只读行为：[`tests/test_harness.py`](../tests/test_harness.py)、[`tests/test_harness_api.py`](../tests/test_harness_api.py)。

# 能力知识运行库

这是真实 SQLite、文档与 AST 摄取实现。初始人工能力卡 21 张，来自 22 个有内容哈希和行号的来源片段。人工卡的 origin=manual_seed、status=extracted；不把人工整理伪装成 LLM 抽取，也不因来源存在就冒称实现已通过验证。

## 使用

在项目根目录安装项目后：

    from pathlib import Path
    from capability_factory.knowledge import KnowledgeStore

    store = KnowledgeStore("artifacts/knowledge.sqlite")
    store.initialize()
    summary = store.ingest_sources(Path.cwd())
    evidence = store.search(
        "银行通话前预测，未知类别容错，CPU 预算",
        "tabular_binary_classification", limit=6, use_graph=True,
    )
    graph = store.graph()

initialize 可重复执行；SQLite 使用外键、WAL、短事务、30 秒 busy timeout。运行表使用 cf_ 前缀，不更改原有 schemas/knowledge_schema.sql 的设计测试。

## 真实来源与边界

- UCI Bank 官方字段说明：duration、pdays、y、unknown。
- UCI SMS README：标签与格式说明；不向抽取器传入示例短信、手机号或全量数据。
- 当前安装的 scikit-learn：13 个 Python 类/函数，以 distribution metadata 定位，再由 ast.parse 读取。不会 import 或执行被摄取的源码。
- 本项目数据协议：字段白名单、划分、防泄漏和经验准入。这些明确标为 original-project-notes，不冒称行业数据来源。
- 只读取固定来源清单；不递归扫描工作区，不读取环境配置或凭据。
- source locator 保存绝对本地路径、精确行区间，代码额外保存类/函数名、签名、导入和公开方法；本地文件哈希和源码版本决定证据身份。换机器后重新摄取可以生成新版本而不覆盖旧记录。

## 接入 LLM 抽取

可选 extractor 是接收 list[source] 的同步 callable，返回 list[card]，也接受 {cards: [...]} 或 {capabilities: [...]}。调用方负责 API 请求、超时、费用和重试。知识库不读取 API key，也不调用外部模型。

一张最小候选卡包含 capability_id、name、summary、task_types 和 source_ids。source_ids 必须引用传入 source 中的真实 source_id。task_types 只允许 tabular_binary_classification 或 text_binary_classification；可附带 preconditions、dependencies、tags、uses、related、confidence、input_schema、output_schema。

- LLM 卡统一标记 origin=llm_extracted、status=extracted。
- 不接受虚构出处，不接受 LLM 覆盖人工种子 ID，不根据模型自己填写的 verified 字段授予验证状态。
- 格式不合法的卡进入 summary.issues，其余合法卡继续入库。
- 外部抽取器超时或失败会被明确记录；人工种子仍可使用，但 llm_extracted_cards=0，不能宣称 LLM 抽取成功。
- 同一能力内容变化会生成新整数版本与 SUPERSEDES 关系；相同内容去重。

## 图检索为什么不是装饰

先按 task_type 和知识状态过滤，使用中英文词项计算文本分数，再从前三个命中出发沿 USES、REQUIRES、AVOIDED_BY 最多两跳扩展。相关能力得到可审计的图加分。公用 Python/sklearn 环境依赖不参与加分，避免所有能力被共同依赖错误地视为相关。

结果保留 lexical_score、graph_score、evidence_path、matched_constraints、source_locator 和原始 evidence。use_graph=False 禁用图分数，支持同一数据上的图检索消融。它是透明的词项+图检索，不冒称训练过的语义嵌入检索。

## 运行、制品与经验回写

- save_run 保存当前完整报告，并将不同内容追加到 cf_run_revisions；失败、取消和中间状态不会因后续成功而消失。
- add_event 用短写事务分配单调序号，跨线程不重复；显式 event_id 可幂等重放。
- candidate.attempts 的每一次代码哈希、路径、状态、错误和指标单独保存为制品，修复链有 REPAIRS 关系，计划引用有 IMPLEMENTS 关系。
- record_experience(..., validated=False) 永久保存 proposed 经验，但不会让它进入可信修复卡检索。
- validated=True 要求已保存成功运行，或者报告中存在匹配该修复的成功候选。先 save_run，再回写经验。证据保存 run_id 和当时报告哈希。
- 已验证修复生成 verified 能力卡、DERIVED_FROM 与 AVOIDED_BY 关系。不同修复建议保留不同指纹，不静默覆盖冲突经验。

当前数据库记录的是服务端验证器提供的证据；数据库本身不会重新运行算法，也不会证明外部调用者提供的报告真实。生产部署应限制只有受信任的服务进程能写数据库。

## 抽取标注与评测

extraction_gold.json 包含 38 条人工参考断言，统计单位是字段/关系，不是 38 个独立能力。每条都绑定 source_key；同一来源可支持多条断言。

evaluate_assertions 位于 ingestion.py，计算规范化 subject/predicate/object/source_key 四元组的精确匹配 precision、recall、F1，返回假阳性、漏召回和出处键有效率。没有预测时 precision=None，不能伪造 100%。该评测是结构化抽取一致性，不能代替人工语义核验。真实评测时应只给模型原始来源与输出 schema，不能把 gold 答案放进提示词。当前提供的是标注集和评测工具，并不意味着已经完成真实模型抽取评测。

## 验证

    PYTHONPATH=src .venv/bin/pytest tests/test_knowledge_runtime.py tests/test_knowledge_schema.py -q

测试覆盖真实来源哈希/行号、幂等、图分数变化、任务隔离、AST 不执行代码、虚构引用拒绝、抽取失败、能力和运行版本、并发事件、未验证经验隔离、验证修复出处、制品与数据关系以及内存数据库。

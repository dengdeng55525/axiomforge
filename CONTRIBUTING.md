# 贡献指南

欢迎参与 AxiomForge · 知衡。项目围绕知识检索、算法生成、独立验证和能力版本管理构建本地研发工作空间。贡献应保持接口清晰、结果可复现、证据可审计。

## 开发环境

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e '.[dev,ui]'
python scripts/verify_data.py
cd web && npm ci
```

`.env`、API Key、私钥、模型权重和本地依赖环境永远不提交。公开数据、运行报告、验证制品与截图可以提交；提交前执行敏感信息扫描，并确认模型请求响应已经脱敏。

## 修改前先确定边界

- 新任务应先补充数据协议、来源和验证配置，再写生成模板。
- 新指标必须说明定义、方向、缺失值行为和是否参与候选选择。
- 新知识节点必须有来源或明确标记为人工种子，不能用共享数据集推断验证关系。
- 新的本地模型配置只能描述接口契约和实测事实，不能把规划配置写成已部署。
- UI 文案应区分 `status`、`quality_status`、Mock/API/本地模式和“未记录”。

## 提交前检查

```bash
.venv/bin/pytest -q tests ui
.venv/bin/ruff check src scripts tests ui
.venv/bin/python -m compileall -q src scripts ui
cd web
npm run format:check
npm run build
npm run test:e2e
```

浏览器测试必须使用无凭证 HTTP 夹具；需要真实模型的测试必须显式标注 `live`，默认不得进入 CI。

## 提交约定

提交信息使用清晰的动词和范围，例如：

- `feat(workflow): add bounded candidate repair`
- `fix(report): preserve missing metric state`
- `docs(schema): explain validation evidence path`
- `test(web): cover cancelled run state`

每个提交尽量只解决一个主题。代码、测试和文档应一起更新；README 中不要复制会快速过期的测试数量，改为链接验证索引。

## Pull Request 内容

请说明：

1. 修改解决了什么问题，以及用户如何复现。
2. 涉及哪些接口、数据协议或 schema 变化。
3. 运行了哪些命令，结果是什么。
4. 是否调用了付费 API、需要 GPU 或产生新的脱敏样例。
5. 仍然存在的安全、性能和复现限制。

如果修改报告结构、图谱关系或 CLI 参数，请同步更新 `docs/08_实现与验收对照.md` 和相关示例 manifest。

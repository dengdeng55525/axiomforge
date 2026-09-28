# 官方来源与核验说明

检索/核验日期：2026-09-28。以下来源支持数据事实、软件用法或硬件规格；项目架构、预算、工期和验收阈值是本项目的设计建议，不冒称官方建议。

| ID | 来源 | 用途 |
|---|---|---|
| S01 | [UCI Bank Marketing](https://archive.ics.uci.edu/dataset/222/bank+marketing) | 主数据版本、目标、排序与许可 |
| S02 | [UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection) | 文本任务、官方原始文件与许可 |
| S03 | [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html) | 训练/测试隔离与预处理泄漏 |
| S04 | [average_precision_score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html) | AP 的具体定义与实现 |
| S05 | [roc_auc_score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html) | ROC-AUC 与概率/分数方向 |
| S06 | [Model persistence](https://scikit-learn.org/stable/model_persistence.html) | 模型文件反序列化与版本问题 |
| S07 | [ColumnTransformer 官方示例](https://scikit-learn.org/stable/auto_examples/compose/plot_column_transformer_mixed_types.html) | 混合列处理的知识来源 |
| S08 | [scikit-learn 仓库许可](https://github.com/scikit-learn/scikit-learn/blob/1.7.2/COPYING) | 第三方代码归属 |
| S09 | [Docker resource constraints](https://docs.docker.com/engine/containers/resource_constraints/) | CPU/内存限制配置原则 |
| S10 | [Docker security](https://docs.docker.com/engine/security/) | 容器权限和 daemon 风险 |
| S11 | [Docker seccomp](https://docs.docker.com/engine/security/seccomp/) | 系统调用限制基础 |
| S12 | [Docker rootless](https://docs.docker.com/engine/security/rootless/) | 非 root 执行选项 |
| S13 | [NVIDIA RTX 4090D 官方规格](https://www.nvidia.cn/geforce/graphics-cards/40-series/rtx-4090-d/) | 24GB、无 NVLink、425W 标称功耗 |
| S14 | [vLLM parallelism and scaling](https://docs.vllm.ai/en/latest/serving/parallelism_scaling/) | 多 GPU 推理拓扑与策略 |
| S15 | [Qwen 7B 官方模型卡](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct) | 可复现的代码模型候选 |
| S16 | [Qwen 7B AWQ](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-AWQ) | 单卡量化候选 |
| S17 | [Qwen 14B AWQ](https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct-AWQ) | 单卡增强候选 |
| S18 | [Qwen 32B AWQ](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-AWQ) | 双卡组候选 |
| S19 | [Qwen 32B 官方模型卡](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct) | 32.5B 参数等容量信息 |
| S20 | [Qwen 32B config](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct/blob/main/config.json) | 40 query heads、8 KV heads、64 层等结构 |

可审计本地证据：

- research/data_audit.json：真实下载 URL、归档/内容 SHA256、解析条数、类别与去重结果。
- research/baseline_results.json：当前环境 CPU 验证集实测；没有最终测试成绩。
- research/code_source_audit.json：安装的 scikit-learn 1.7.2 源码 AST 元信息与哈希；Git tag commit 经 git ls-remote 核实。GitHub API 遇限流、raw 直连遇 TLS 错误，因此使用本地已安装分发源码做可行性审计；不声称三个远程示例文件都下载成功。
- research/model_metadata.json：官方模型 API 返回的 revision；只读取元信息，未下载权重、未运行推理。

官网 stable/latest 文档可能继续变化。实现时应按锁定的库版本核对 API，并将所用文档/代码 commit 与内容哈希记录在 Source 中。已运行的 CPU 探针固定为 scikit-learn 1.7.2，不能把检索时 stable 页面版本当作当前执行版本。

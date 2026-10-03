# 算法能力验证报告

指标与状态来自原始验证事实；缺失项不填零、不推断通过。

模式由原始报告的 mode 字段说明：mock 为模拟，replay 为历史回放。

````json
{
  "schema_version": "1.0",
  "run_id": "799d2116572a4fbba835d42969156064",
  "status": "passed",
  "mode": "real",
  "provider": "deepseek",
  "description": "构建短信垃圾信息分类能力。比较 TF-IDF 与逻辑回归、朴素贝叶斯方案，保持训练、验证、测试隔离，报告 AP、F1 及接口稳定性检查结果。",
  "dataset_id": "sms",
  "created_at": "2026-09-29T12:30:29.593669+00:00",
  "request": {
    "description": "构建短信垃圾信息分类能力。比较 TF-IDF 与逻辑回归、朴素贝叶斯方案，保持训练、验证、测试隔离，报告 AP、F1 及接口稳定性检查结果。",
    "dataset_id": "sms",
    "provider": "deepseek",
    "max_candidates": 4,
    "max_repairs": 2,
    "use_graph": true,
    "use_retrieval": true,
    "orchestration": "multi_role",
    "search": "compare",
    "inject_failure": true,
    "max_seconds": 900
  },
  "task_spec": {
    "task_type": "text_binary_classification",
    "dataset_id": "sms",
    "positive_label": "spam",
    "feature_names": [
      "text"
    ],
    "numeric_features": [],
    "categorical_features": [
      "text"
    ],
    "seed": 42,
    "primary_metric": "average_precision",
    "limits": {
      "cpu": 2,
      "memory_mib": 2048,
      "timeout_s": 120
    },
    "feature_policy": "normalized_group_split_v1"
  },
  "model": "deepseek-flash",
  "provenance": {
    "prompt_version": "algoforge-roles-v2",
    "sealed_test_scored": false,
    "dataset": {
      "schema_version": "1.0",
      "dataset_id": "uci-sms-spam",
      "source_url": "https://archive.ics.uci.edu/dataset/228/sms+spam+collection",
      "license": "CC BY 4.0",
      "raw_sha256": "7d039a24a6083ed9ef0f806ebad56bbb976e3aeb8de05669173bfdc4996c239d",
      "split_policy": "normalized_text_group_dedup_stratified_60_20_20",
      "split_seed": 42,
      "train_rows": 3095,
      "validation_rows": 1032,
      "sealed_test_rows": 1032,
      "sealed_test_exported": false,
      "sealed_test_scored": false,
      "validation_labels_visible_to_generated_code": false,
      "preprocessing_fit_split": "train_only",
      "feature_policy": "text_only_group_dedup_v1",
      "feature_names": [
        "text"
      ],
      "numeric_features": [],
      "file_sha256": {
        "train": "02e817b63d1687cba45abc15c3820c3748405fd185f09ee73c2b7854ea7117a6",
        "validation_features": "b56334649c55b5873b8a94c0d0efcceb8710824808fba4900e639dcd782f343b",
        "validation_labels": "71907784e61eabc1fff51e1e71293e9cc4ef0a8359d1923def4c0519185a7421"
      },
      "raw_rows": 5574,
      "normalized_groups": 5159,
      "conflicting_groups_excluded": 0,
      "train_group_ids_sha256": "67b569ca179c2f301db65dea9f94b0ce90cb2ad6359b601a00ca38c1b567860c",
      "validation_group_ids_sha256": "d7b9f23990ff4133c30b7b64ce309f75d9e1baea67c59ccfdf929cbe2330d31c",
      "sealed_group_ids_sha256": "d9a436d8888da5cbd06d15795c909d935e7709cc7b4f7cd3dbbf357d7e60fd65"
    }
  },
  "candidates": [
    {
      "candidate_id": "sms_logreg_default",
      "plan": {
        "candidate_id": "sms_logreg_default",
        "algorithm": "logistic",
        "variant": "default",
        "rationale": "TF-IDF 稀疏文本特征配合逻辑回归概率接口，作为短信垃圾信息分类的线性基线；词表与 IDF 仅在训练集拟合，按 sms-grouped-split 协议保持训练/验证/测试隔离，用 AP 与 F1 评估。",
        "evidence_ids": [
          "text-tfidf",
          "probability-logistic",
          "average-precision",
          "sms-format",
          "sms-grouped-split"
        ],
        "parent_id": null
      },
      "status": "passed",
      "metrics": {
        "average_precision": 0.9583895772337544,
        "roc_auc": 0.9880587533372823,
        "f1_threshold_0_5": 0.8055555555555556,
        "precision_at_10pct": 0.9903846153846154,
        "recall_at_10pct": 0.7984496124031008,
        "lift_at_10pct": 7.923076923076923,
        "validation_positive_rate": 0.125,
        "top_10pct_count": 104,
        "validation_rows": 1032,
        "classification_threshold": 0.5,
        "evaluation_split": "validation_only",
        "sealed_test_scored": false,
        "ranking_tie_break": "original_validation_row_order",
        "dummy_average_precision": 0.125,
        "ap_improvement_over_dummy": 0.8333895772337544
      },
      "checks": [
        {
          "name": "source_policy",
          "passed": true,
          "mandatory": true,
          "detail": "AST parsed as approved constructors without exec/eval"
        },
        {
          "name": "plan_consistency",
          "passed": true,
          "mandatory": true,
          "detail": "Final classifier matches planned logistic"
        },
        {
          "name": "dataset_integrity",
          "passed": true,
          "mandatory": true,
          "detail": "SHA256, split disjointness, row alignment, feature policy"
        },
        {
          "name": "labels_withheld",
          "passed": true,
          "mandatory": true,
          "detail": "Worker receives no validation labels or final test"
        },
        {
          "name": "worker_execution",
          "passed": true,
          "mandatory": true,
          "detail": "Resource-limited fresh process exited successfully"
        },
        {
          "name": "prediction_contract",
          "passed": true,
          "mandatory": true,
          "detail": "Exact row IDs, binary classes, finite normalized Nx2 probabilities"
        },
        {
          "name": "single_row",
          "passed": true,
          "mandatory": true,
          "detail": ""
        },
        {
          "name": "repeat_prediction",
          "passed": true,
          "mandatory": true,
          "detail": ""
        },
        {
          "name": "empty_batch_wrapper",
          "passed": true,
          "mandatory": true,
          "detail": ""
        },
        {
          "name": "empty_text",
          "passed": true,
          "mandatory": true,
          "detail": ""
        },
        {
          "name": "clean_environment",
          "passed": true,
          "mandatory": true,
          "detail": "No API keys/tokens passed to worker"
        },
        {
          "name": "ap_above_dummy",
          "passed": true,
          "mandatory": false,
          "detail": "Advisory quality gate; not a substitute for sealed-test evaluation"
        },
        {
          "name": "host_evaluation",
          "passed": true,
          "mandatory": true,
          "detail": "Metrics computed only by trusted host using validation labels"
        }
      ],
      "resources": {
        "limits": {
          "timeout_s": 120.0,
          "memory_mib": 2048,
          "cpu_cores": 2
        },
        "worker_pid": 40410,
        "wall_seconds": 0.8529382101260126,
        "fit_seconds": 0.1073710119817406,
        "predict_seconds": 0.012808460043743253,
        "worker_wall_seconds": 0.7297444727737457,
        "peak_rss_mib": 198.828125,
        "cpu_seconds": 0.966693,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 0.8804588210768998
      },
      "repairs": [
        {
          "error_type": "plan_consistency",
          "diagnosis": "The generated code defines a function `broken_pipeline(task_spec)` that returns an unfitted sklearn Pipeline, but the plan requires a constructor program that builds and fits a model on the provided dataset. The function name and signature do not match the expected constructor interface, and no training/fitting step is performed, so the source policy check cannot verify consistency with the plan.",
          "fix": "Rename the function to the expected constructor name (e.g., `build_model` or `make_pipeline`) and ensure it returns a fitted estimator by calling `.fit(X, y)` on the pipeline using the task's text feature and target label, or return the unfitted pipeline only if the plan explicitly expects a constructor that the runner will fit. Align the function signature with the task_spec fields (text column, label column) and remove the non-standard `broken_pipeline` name.",
          "repairable": true,
          "attempt": 1,
          "before_hash": "21cd00e64f4fe452cf8e42fc0b4d888c1eb45e4a972bb424678a5e9ee6c4c95c",
          "after_hash": "bcc82556ef50805daad7f3dc3c8bda2769b2459da861619c340a24caaa2408f9",
          "validated": true
        }
      ],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "21cd00e64f4fe452cf8e42fc0b4d888c1eb45e4a972bb424678a5e9ee6c4c95c",
          "code_path": "candidates/sms_logreg_default/attempt_0/model.py",
          "status": "failed",
          "error": {
            "type": "plan_consistency",
            "stage": "source_policy",
            "repairable": true,
            "message": "Generated code could not be checked against its plan: CodePolicyError"
          },
          "checks": [],
          "metrics": {},
          "resources": {},
          "containment": {},
          "model_metadata": null
        },
        {
          "attempt": 1,
          "code_sha256": "bcc82556ef50805daad7f3dc3c8bda2769b2459da861619c340a24caaa2408f9",
          "code_path": "candidates/sms_logreg_default/attempt_1/model.py",
          "status": "passed",
          "error": null,
          "checks": [
            {
              "name": "source_policy",
              "passed": true,
              "mandatory": true,
              "detail": "AST parsed as approved constructors without exec/eval"
            },
            {
              "name": "plan_consistency",
              "passed": true,
              "mandatory": true,
              "detail": "Final classifier matches planned logistic"
            },
            {
              "name": "dataset_integrity",
              "passed": true,
              "mandatory": true,
              "detail": "SHA256, split disjointness, row alignment, feature policy"
            },
            {
              "name": "labels_withheld",
              "passed": true,
              "mandatory": true,
              "detail": "Worker receives no validation labels or final test"
            },
            {
              "name": "worker_execution",
              "passed": true,
              "mandatory": true,
              "detail": "Resource-limited fresh process exited successfully"
            },
            {
              "name": "prediction_contract",
              "passed": true,
              "mandatory": true,
              "detail": "Exact row IDs, binary classes, finite normalized Nx2 probabilities"
            },
            {
              "name": "single_row",
              "passed": true,
              "mandatory": true,
              "detail": ""
            },
            {
              "name": "repeat_prediction",
              "passed": true,
              "mandatory": true,
              "detail": ""
            },
            {
              "name": "empty_batch_wrapper",
              "passed": true,
              "mandatory": true,
              "detail": ""
            },
            {
              "name": "empty_text",
              "passed": true,
              "mandatory": true,
              "detail": ""
            },
            {
              "name": "clean_environment",
              "passed": true,
              "mandatory": true,
              "detail": "No API keys/tokens passed to worker"
            },
            {
              "name": "ap_above_dummy",
              "passed": true,
              "mandatory": false,
              "detail": "Advisory quality gate; not a substitute for sealed-test evaluation"
            },
            {
              "name": "host_evaluation",
              "passed": true,
              "mandatory": true,
              "detail": "Metrics computed only by trusted host using validation labels"
            }
          ],
          "metrics": {
            "average_precision": 0.9583895772337544,
            "roc_auc": 0.9880587533372823,
            "f1_threshold_0_5": 0.8055555555555556,
            "precision_at_10pct": 0.9903846153846154,
            "recall_at_10pct": 0.7984496124031008,
            "lift_at_10pct": 7.923076923076923,
            "validation_positive_rate": 0.125,
            "top_10pct_count": 104,
            "validation_rows": 1032,
            "classification_threshold": 0.5,
            "evaluation_split": "validation_only",
            "sealed_test_scored": false,
            "ranking_tie_break": "original_validation_row_order",
            "dummy_average_precision": 0.125,
            "ap_improvement_over_dummy": 0.8333895772337544
          },
          "resources": {
            "limits": {
              "timeout_s": 120.0,
              "memory_mib": 2048,
              "cpu_cores": 2
            },
            "worker_pid": 40410,
            "wall_seconds": 0.8529382101260126,
            "fit_seconds": 0.1073710119817406,
            "predict_seconds": 0.012808460043743253,
            "worker_wall_seconds": 0.7297444727737457,
            "peak_rss_mib": 198.828125,
            "cpu_seconds": 0.966693,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 0.8804588210768998
          },
          "containment": {
            "backend": "constrained_ast_subprocess",
            "arbitrary_python_execution": false,
            "os_sandbox": false,
            "network_namespace": false,
            "filesystem_namespace": false,
            "source_evaluated_with_exec_or_eval": false,
            "constructors_allowlisted": true,
            "resource_limited_fresh_process": true,
            "security_scope": "Restricted sklearn constructor grammar; no generated methods, callbacks, file access, network calls, loops, or dynamic imports. Trusted sklearn/native dependencies remain in the trust boundary."
          },
          "model_metadata": {
            "actual_algorithm": "logistic",
            "classifier_class": "LogisticRegression",
            "classifier_path": [
              "model"
            ],
            "classifier_parameters": {
              "max_iter": 1000,
              "random_state": 42
            },
            "constructor_classes": [
              "Pipeline",
              "TfidfVectorizer",
              "LogisticRegression"
            ],
            "constructor_count": 3,
            "source": "independently_parsed_constructor_plan"
          }
        }
      ],
      "artifact_id": "sms_logreg_default",
      "parent_id": null,
      "injected_failure": true,
      "error": null,
      "quality_status": "above_prevalence",
      "model_metadata": {
        "actual_algorithm": "logistic",
        "classifier_class": "LogisticRegression",
        "classifier_path": [
          "model"
        ],
        "classifier_parameters": {
          "max_iter": 1000,
          "random_state": 42
        },
        "constructor_classes": [
          "Pipeline",
          "TfidfVectorizer",
          "LogisticRegression"
        ],
        "constructor_count": 3,
        "source": "independently_parsed_constructor_plan"
      },
      "containment": {
        "backend": "constrained_ast_subprocess",
        "arbitrary_python_execution": false,
        "os_sandbox": false,
        "network_namespace": false,
        "filesystem_namespace": false,
        "source_evaluated_with_exec_or_eval": false,
        "constructors_allowlisted": true,
        "resource_limited_fresh_process": true,
        "security_scope": "Restricted sklearn constructor grammar; no generated methods, callbacks, file access, network calls, loops, or dynamic imports. Trusted sklearn/native dependencies remain in the trust boundary."
      },
      "code_sha256": "bcc82556ef50805daad7f3dc3c8bda2769b2459da861619c340a24caaa2408f9",
      "code_path": "candidates/sms_logreg_default/attempt_1/model.py",
      "explanation": "Fixes the plan-consistency error by renaming the function to the required build_pipeline(task_spec) constructor interface while keeping the TF-IDF (ngram_range=(1,2), max_features=30000, min_df=2) plus LogisticRegression(max_iter=1000, random_state=seed) pipeline from the plan's default logistic variant, with no fitting or data access in the generated code."
    },
    {
      "candidate_id": "sms_nb_default",
      "plan": {
        "candidate_id": "sms_nb_default",
        "algorithm": "nb",
        "variant": "default",
        "rationale": "ComplementNB 面向不平衡非负文本特征，与 TF-IDF 组合形成与逻辑回归不同的生成式对照方案；同样遵循分组去重分层划分，仅由验证集实测性能，不预设目标指标。",
        "evidence_ids": [
          "text-tfidf",
          "complement-naive-bayes",
          "average-precision",
          "sms-format",
          "sms-grouped-split"
        ],
        "parent_id": null
      },
      "status": "passed",
      "metrics": {
        "average_precision": 0.9459327203990979,
        "roc_auc": 0.9780748066307828,
        "f1_threshold_0_5": 0.9024390243902439,
        "precision_at_10pct": 1.0,
        "recall_at_10pct": 0.8062015503875969,
        "lift_at_10pct": 8.0,
        "validation_positive_rate": 0.125,
        "top_10pct_count": 104,
        "validation_rows": 1032,
        "classification_threshold": 0.5,
        "evaluation_split": "validation_only",
        "sealed_test_scored": false,
        "ranking_tie_break": "original_validation_row_order",
        "dummy_average_precision": 0.125,
        "ap_improvement_over_dummy": 0.8209327203990979
      },
      "checks": [
        {
          "name": "source_policy",
          "passed": true,
          "mandatory": true,
          "detail": "AST parsed as approved constructors without exec/eval"
        },
        {
          "name": "plan_consistency",
          "passed": true,
          "mandatory": true,
          "detail": "Final classifier matches planned nb"
        },
        {
          "name": "dataset_integrity",
          "passed": true,
          "mandatory": true,
          "detail": "SHA256, split disjointness, row alignment, feature policy"
        },
        {
          "name": "labels_withheld",
          "passed": true,
          "mandatory": true,
          "detail": "Worker receives no validation labels or final test"
        },
        {
          "name": "worker_execution",
          "passed": true,
          "mandatory": true,
          "detail": "Resource-limited fresh process exited successfully"
        },
        {
          "name": "prediction_contract",
          "passed": true,
          "mandatory": true,
          "detail": "Exact row IDs, binary classes, finite normalized Nx2 probabilities"
        },
        {
          "name": "single_row",
          "passed": true,
          "mandatory": true,
          "detail": ""
        },
        {
          "name": "repeat_prediction",
          "passed": true,
          "mandatory": true,
          "detail": ""
        },
        {
          "name": "empty_batch_wrapper",
          "passed": true,
          "mandatory": true,
          "detail": ""
        },
        {
          "name": "empty_text",
          "passed": true,
          "mandatory": true,
          "detail": ""
        },
        {
          "name": "clean_environment",
          "passed": true,
          "mandatory": true,
          "detail": "No API keys/tokens passed to worker"
        },
        {
          "name": "ap_above_dummy",
          "passed": true,
          "mandatory": false,
          "detail": "Advisory quality gate; not a substitute for sealed-test evaluation"
        },
        {
          "name": "host_evaluation",
          "passed": true,
          "mandatory": true,
          "detail": "Metrics computed only by trusted host using validation labels"
        }
      ],
      "resources": {
        "limits": {
          "timeout_s": 120.0,
          "memory_mib": 2048,
          "cpu_cores": 2
        },
        "worker_pid": 40436,
        "wall_seconds": 0.8029131928924471,
        "fit_seconds": 0.07050781813450158,
        "predict_seconds": 0.012798863928765059,
        "worker_wall_seconds": 0.6632015351206064,
        "peak_rss_mib": 199.828125,
        "cpu_seconds": 0.879838,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 0.8328247100580484
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "1176a4eaecfb06aa895e14053462ab3fc7ed8f1b917aaa717ae62f9bc8428860",
          "code_path": "candidates/sms_nb_default/attempt_0/model.py",
          "status": "passed",
          "error": null,
          "checks": [
            {
              "name": "source_policy",
              "passed": true,
              "mandatory": true,
              "detail": "AST parsed as approved constructors without exec/eval"
            },
            {
              "name": "plan_consistency",
              "passed": true,
              "mandatory": true,
              "detail": "Final classifier matches planned nb"
            },
            {
              "name": "dataset_integrity",
              "passed": true,
              "mandatory": true,
              "detail": "SHA256, split disjointness, row alignment, feature policy"
            },
            {
              "name": "labels_withheld",
              "passed": true,
              "mandatory": true,
              "detail": "Worker receives no validation labels or final test"
            },
            {
              "name": "worker_execution",
              "passed": true,
              "mandatory": true,
              "detail": "Resource-limited fresh process exited successfully"
            },
            {
              "name": "prediction_contract",
              "passed": true,
              "mandatory": true,
              "detail": "Exact row IDs, binary classes, finite normalized Nx2 probabilities"
            },
            {
              "name": "single_row",
              "passed": true,
              "mandatory": true,
              "detail": ""
            },
            {
              "name": "repeat_prediction",
              "passed": true,
              "mandatory": true,
              "detail": ""
            },
            {
              "name": "empty_batch_wrapper",
              "passed": true,
              "mandatory": true,
              "detail": ""
            },
            {
              "name": "empty_text",
              "passed": true,
              "mandatory": true,
              "detail": ""
            },
            {
              "name": "clean_environment",
              "passed": true,
              "mandatory": true,
              "detail": "No API keys/tokens passed to worker"
            },
            {
              "name": "ap_above_dummy",
              "passed": true,
              "mandatory": false,
              "detail": "Advisory quality gate; not a substitute for sealed-test evaluation"
            },
            {
              "name": "host_evaluation",
              "passed": true,
              "mandatory": true,
              "detail": "Metrics computed only by trusted host using validation labels"
            }
          ],
          "metrics": {
            "average_precision": 0.9459327203990979,
            "roc_auc": 0.9780748066307828,
            "f1_threshold_0_5": 0.9024390243902439,
            "precision_at_10pct": 1.0,
            "recall_at_10pct": 0.8062015503875969,
            "lift_at_10pct": 8.0,
            "validation_positive_rate": 0.125,
            "top_10pct_count": 104,
            "validation_rows": 1032,
            "classification_threshold": 0.5,
            "evaluation_split": "validation_only",
            "sealed_test_scored": false,
            "ranking_tie_break": "original_validation_row_order",
            "dummy_average_precision": 0.125,
            "ap_improvement_over_dummy": 0.8209327203990979
          },
          "resources": {
            "limits": {
              "timeout_s": 120.0,
              "memory_mib": 2048,
              "cpu_cores": 2
            },
            "worker_pid": 40436,
            "wall_seconds": 0.8029131928924471,
            "fit_seconds": 0.07050781813450158,
            "predict_seconds": 0.012798863928765059,
            "worker_wall_seconds": 0.6632015351206064,
            "peak_rss_mib": 199.828125,
            "cpu_seconds": 0.879838,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 0.8328247100580484
          },
          "containment": {
            "backend": "constrained_ast_subprocess",
            "arbitrary_python_execution": false,
            "os_sandbox": false,
            "network_namespace": false,
            "filesystem_namespace": false,
            "source_evaluated_with_exec_or_eval": false,
            "constructors_allowlisted": true,
            "resource_limited_fresh_process": true,
            "security_scope": "Restricted sklearn constructor grammar; no generated methods, callbacks, file access, network calls, loops, or dynamic imports. Trusted sklearn/native dependencies remain in the trust boundary."
          },
          "model_metadata": {
            "actual_algorithm": "nb",
            "classifier_class": "ComplementNB",
            "classifier_path": [
              "model"
            ],
            "classifier_parameters": {
              "alpha": 1.0
            },
            "constructor_classes": [
              "Pipeline",
              "TfidfVectorizer",
              "ComplementNB"
            ],
            "constructor_count": 3,
            "source": "independently_parsed_constructor_plan"
          }
        }
      ],
      "artifact_id": "sms_nb_default",
      "parent_id": null,
      "error": null,
      "quality_status": "above_prevalence",
      "model_metadata": {
        "actual_algorithm": "nb",
        "classifier_class": "ComplementNB",
        "classifier_path": [
          "model"
        ],
        "classifier_parameters": {
          "alpha": 1.0
        },
        "constructor_classes": [
          "Pipeline",
          "TfidfVectorizer",
          "ComplementNB"
        ],
        "constructor_count": 3,
        "source": "independently_parsed_constructor_plan"
      },
      "containment": {
        "backend": "constrained_ast_subprocess",
        "arbitrary_python_execution": false,
        "os_sandbox": false,
        "network_namespace": false,
        "filesystem_namespace": false,
        "source_evaluated_with_exec_or_eval": false,
        "constructors_allowlisted": true,
        "resource_limited_fresh_process": true,
        "security_scope": "Restricted sklearn constructor grammar; no generated methods, callbacks, file access, network calls, loops, or dynamic imports. Trusted sklearn/native dependencies remain in the trust boundary."
      },
      "code_sha256": "1176a4eaecfb06aa895e14053462ab3fc7ed8f1b917aaa717ae62f9bc8428860",
      "code_path": "candidates/sms_nb_default/attempt_0/model.py",
      "explanation": "Plan variant=default with algorithm nb: TF-IDF (1-2 grams, max_features=30000, min_df=2) feeding ComplementNB at default alpha=1.0, matching the text-tfidf and complement-naive-bayes evidence for non-negative sparse SMS features and providing predict_proba."
    }
  ],
  "selected_candidate_id": "sms_logreg_default",
  "events": [
    {
      "sequence": 0,
      "event_type": "RECEIVED",
      "type": "RECEIVED",
      "created_at": "2026-09-29T12:30:29.719165+00:00",
      "data": {
        "mode": "real",
        "model": "deepseek-flash"
      }
    },
    {
      "sequence": 1,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T12:30:33.284181+00:00",
      "data": {
        "role": "interpreter",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "6bb3d5a8-4e54-474b-81dc-fb77faa96e1a",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "c3e0fc336c1a58e4d93e55da38e92e322a1b5095191aa987cf03916df13fc76a",
        "response_sha256": "638d49acb58826b905ccc925596084631a538d9feae4a1964e7badd0c17a8439",
        "input_tokens": 420,
        "output_tokens": 355,
        "seconds": 2.793,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 2,
      "event_type": "SPEC_VALIDATED",
      "type": "SPEC_VALIDATED",
      "created_at": "2026-09-29T12:30:33.607914+00:00",
      "data": {
        "task_type": "text_binary_classification",
        "assumptions": [
          "数据集 sms 已包含 text 与 spam 标签字段，可直接用于文本二分类。",
          "TF-IDF 作为文本向量化方法，逻辑回归与朴素贝叶斯作为候选分类器。",
          "接口稳定性检查指对模型推理接口在重复调用或边界输入下的一致性验证。",
          "验证集用于方案比较与选择，测试集仅用于最终报告。"
        ]
      }
    },
    {
      "sequence": 3,
      "event_type": "KNOWLEDGE_RETRIEVED",
      "type": "KNOWLEDGE_RETRIEVED",
      "created_at": "2026-09-29T12:30:33.839390+00:00",
      "data": {
        "count": 6,
        "use_graph": true,
        "capability_ids": [
          "text-tfidf",
          "complement-naive-bayes",
          "probability-logistic",
          "average-precision",
          "sms-format",
          "sms-grouped-split"
        ]
      }
    },
    {
      "sequence": 4,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T12:30:35.732657+00:00",
      "data": {
        "role": "planner",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "1bbd6187-7ea0-4a14-992c-a83fc2356434",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "ace36f118f7eaeb3d986d51ae1623a093efe5382dc3d968707e3407f2fde268d",
        "response_sha256": "7ea11454d8114e58a249de4da61f369d1dcd0c3aef772b9d39a193b0ca2f51fe",
        "input_tokens": 8933,
        "output_tokens": 225,
        "seconds": 1.671,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 5,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-29T12:30:36.003627+00:00",
      "data": {
        "candidate_id": "sms_logreg_default",
        "algorithm": "logistic",
        "variant": "default",
        "rationale": "TF-IDF 稀疏文本特征配合逻辑回归概率接口，作为短信垃圾信息分类的线性基线；词表与 IDF 仅在训练集拟合，按 sms-grouped-split 协议保持训练/验证/测试隔离，用 AP 与 F1 评估。",
        "evidence_ids": [
          "text-tfidf",
          "probability-logistic",
          "average-precision",
          "sms-format",
          "sms-grouped-split"
        ],
        "parent_id": null
      }
    },
    {
      "sequence": 6,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T12:30:37.605375+00:00",
      "data": {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "2293aef6-6d73-4e62-8286-e34cdda2fb55",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "39c9ae539ce21eef3b389f24651002cbda2beb333c7730802cb07cc2d09a0df9",
        "response_sha256": "d2cfeb8e2ee2b6b5c33793d2b0022a09bfe94e35296a634b0c906f87e96c9312",
        "input_tokens": 9418,
        "output_tokens": 176,
        "seconds": 1.141,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 7,
      "event_type": "FAILURE_INJECTED",
      "type": "FAILURE_INJECTED",
      "created_at": "2026-09-29T12:30:37.902167+00:00",
      "data": {
        "candidate_id": "sms_logreg_default",
        "kind": "missing_interface",
        "injected": true
      }
    },
    {
      "sequence": 8,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-29T12:30:38.178034+00:00",
      "data": {
        "candidate_id": "sms_logreg_default",
        "attempt": 0,
        "code_sha256": "21cd00e64f4fe452cf8e42fc0b4d888c1eb45e4a972bb424678a5e9ee6c4c95c"
      }
    },
    {
      "sequence": 9,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-29T12:30:38.438865+00:00",
      "data": {
        "candidate_id": "sms_logreg_default",
        "attempt": 0,
        "status": "failed",
        "metrics": {},
        "error": {
          "type": "plan_consistency",
          "stage": "source_policy",
          "repairable": true,
          "message": "Generated code could not be checked against its plan: CodePolicyError"
        }
      }
    },
    {
      "sequence": 10,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T12:30:40.644454+00:00",
      "data": {
        "role": "reviewer",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "c96d447d-0e64-4181-9e2f-05a4f1386a4e",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "d6b2da30f4fefd1e7c2fe64d4edc6fbd0a1b93a36124fac7ca2a5285f394f3dc",
        "response_sha256": "54e8730cd86777ad9488b2448410149f9e72418417fad307c8f3f8fb99eabe2a",
        "input_tokens": 464,
        "output_tokens": 197,
        "seconds": 1.924,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 11,
      "event_type": "REPAIR_PLANNED",
      "type": "REPAIR_PLANNED",
      "created_at": "2026-09-29T12:30:40.977422+00:00",
      "data": {
        "candidate_id": "sms_logreg_default",
        "error_type": "plan_consistency",
        "diagnosis": "The generated code defines a function `broken_pipeline(task_spec)` that returns an unfitted sklearn Pipeline, but the plan requires a constructor program that builds and fits a model on the provided dataset. The function name and signature do not match the expected constructor interface, and no training/fitting step is performed, so the source policy check cannot verify consistency with the plan.",
        "fix": "Rename the function to the expected constructor name (e.g., `build_model` or `make_pipeline`) and ensure it returns a fitted estimator by calling `.fit(X, y)` on the pipeline using the task's text feature and target label, or return the unfitted pipeline only if the plan explicitly expects a constructor that the runner will fit. Align the function signature with the task_spec fields (text column, label column) and remove the non-standard `broken_pipeline` name.",
        "repairable": true
      }
    },
    {
      "sequence": 12,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T12:30:43.122077+00:00",
      "data": {
        "role": "repair_coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "e2f66d59-8610-4e82-a08f-1ce8e36b0beb",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "0029517670bc51a5acbbd5f36570f2e25747de06b80b1d30d52266e98c9e9e87",
        "response_sha256": "6f092004420b9830ea552a1fb9b45bb74fa28473bf8447c7e58e965a21e66559",
        "input_tokens": 9739,
        "output_tokens": 207,
        "seconds": 1.669,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 13,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-29T12:30:43.431574+00:00",
      "data": {
        "candidate_id": "sms_logreg_default",
        "attempt": 1,
        "code_sha256": "bcc82556ef50805daad7f3dc3c8bda2769b2459da861619c340a24caaa2408f9"
      }
    },
    {
      "sequence": 14,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-29T12:30:44.540623+00:00",
      "data": {
        "candidate_id": "sms_logreg_default",
        "attempt": 1,
        "status": "passed",
        "metrics": {
          "average_precision": 0.9583895772337544,
          "roc_auc": 0.9880587533372823,
          "f1_threshold_0_5": 0.8055555555555556,
          "precision_at_10pct": 0.9903846153846154,
          "recall_at_10pct": 0.7984496124031008,
          "lift_at_10pct": 7.923076923076923,
          "validation_positive_rate": 0.125,
          "top_10pct_count": 104,
          "validation_rows": 1032,
          "classification_threshold": 0.5,
          "evaluation_split": "validation_only",
          "sealed_test_scored": false,
          "ranking_tie_break": "original_validation_row_order",
          "dummy_average_precision": 0.125,
          "ap_improvement_over_dummy": 0.8333895772337544
        },
        "error": null
      }
    },
    {
      "sequence": 15,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-29T12:30:44.859988+00:00",
      "data": {
        "candidate_id": "sms_nb_default",
        "algorithm": "nb",
        "variant": "default",
        "rationale": "ComplementNB 面向不平衡非负文本特征，与 TF-IDF 组合形成与逻辑回归不同的生成式对照方案；同样遵循分组去重分层划分，仅由验证集实测性能，不预设目标指标。",
        "evidence_ids": [
          "text-tfidf",
          "complement-naive-bayes",
          "average-precision",
          "sms-format",
          "sms-grouped-split"
        ],
        "parent_id": null
      }
    },
    {
      "sequence": 16,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T12:30:46.450668+00:00",
      "data": {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "2f04fef2-ca3a-422d-b93e-0136957dcbcc",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "6ee2c631c6f504d68662002de971d346aaa17d83815e4f35db6020c0e5b50f26",
        "response_sha256": "55b270eda9b4cfa5a91449db7804f0f69e3b1eb98bfd902e3fdebb8ecba53229",
        "input_tokens": 9402,
        "output_tokens": 181,
        "seconds": 1.371,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 17,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-29T12:30:46.663881+00:00",
      "data": {
        "candidate_id": "sms_nb_default",
        "attempt": 0,
        "code_sha256": "1176a4eaecfb06aa895e14053462ab3fc7ed8f1b917aaa717ae62f9bc8428860"
      }
    },
    {
      "sequence": 18,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-29T12:30:47.717529+00:00",
      "data": {
        "candidate_id": "sms_nb_default",
        "attempt": 0,
        "status": "passed",
        "metrics": {
          "average_precision": 0.9459327203990979,
          "roc_auc": 0.9780748066307828,
          "f1_threshold_0_5": 0.9024390243902439,
          "precision_at_10pct": 1.0,
          "recall_at_10pct": 0.8062015503875969,
          "lift_at_10pct": 8.0,
          "validation_positive_rate": 0.125,
          "top_10pct_count": 104,
          "validation_rows": 1032,
          "classification_threshold": 0.5,
          "evaluation_split": "validation_only",
          "sealed_test_scored": false,
          "ranking_tie_break": "original_validation_row_order",
          "dummy_average_precision": 0.125,
          "ap_improvement_over_dummy": 0.8209327203990979
        },
        "error": null
      }
    },
    {
      "sequence": 19,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T12:30:50.518032+00:00",
      "data": {
        "role": "curator",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "62d2ace5-c21f-4a5d-8052-01d9721af8f1",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "5be9930f1c7e6e99cdefd90ec58e752b45f9c645c561d1164273690f234762a4",
        "response_sha256": "ef071a2b7640e33a322000e0931b296231c4235f0e323b62b9f94958a4a9bf23",
        "input_tokens": 707,
        "output_tokens": 396,
        "seconds": 2.451,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 20,
      "event_type": "COMPARED",
      "type": "COMPARED",
      "created_at": "2026-09-29T12:30:50.736745+00:00",
      "data": {
        "selected_candidate_id": "sms_logreg_default"
      }
    },
    {
      "sequence": 21,
      "event_type": "RECORDED",
      "type": "RECORDED",
      "created_at": "2026-09-29T12:30:51.411619+00:00",
      "data": {
        "intended_status": "passed",
        "experiences": 1
      }
    }
  ],
  "usage": {
    "calls": 7,
    "input_tokens": 39083,
    "output_tokens": 1737,
    "cached_input_tokens": 18816,
    "records": [
      {
        "role": "interpreter",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "6bb3d5a8-4e54-474b-81dc-fb77faa96e1a",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "c3e0fc336c1a58e4d93e55da38e92e322a1b5095191aa987cf03916df13fc76a",
        "response_sha256": "638d49acb58826b905ccc925596084631a538d9feae4a1964e7badd0c17a8439",
        "input_tokens": 420,
        "output_tokens": 355,
        "seconds": 2.793,
        "finish_reason": "stop"
      },
      {
        "role": "planner",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "1bbd6187-7ea0-4a14-992c-a83fc2356434",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "ace36f118f7eaeb3d986d51ae1623a093efe5382dc3d968707e3407f2fde268d",
        "response_sha256": "7ea11454d8114e58a249de4da61f369d1dcd0c3aef772b9d39a193b0ca2f51fe",
        "input_tokens": 8933,
        "output_tokens": 225,
        "seconds": 1.671,
        "finish_reason": "stop"
      },
      {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "2293aef6-6d73-4e62-8286-e34cdda2fb55",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "39c9ae539ce21eef3b389f24651002cbda2beb333c7730802cb07cc2d09a0df9",
        "response_sha256": "d2cfeb8e2ee2b6b5c33793d2b0022a09bfe94e35296a634b0c906f87e96c9312",
        "input_tokens": 9418,
        "output_tokens": 176,
        "seconds": 1.141,
        "finish_reason": "stop"
      },
      {
        "role": "reviewer",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "c96d447d-0e64-4181-9e2f-05a4f1386a4e",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "d6b2da30f4fefd1e7c2fe64d4edc6fbd0a1b93a36124fac7ca2a5285f394f3dc",
        "response_sha256": "54e8730cd86777ad9488b2448410149f9e72418417fad307c8f3f8fb99eabe2a",
        "input_tokens": 464,
        "output_tokens": 197,
        "seconds": 1.924,
        "finish_reason": "stop"
      },
      {
        "role": "repair_coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "e2f66d59-8610-4e82-a08f-1ce8e36b0beb",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "0029517670bc51a5acbbd5f36570f2e25747de06b80b1d30d52266e98c9e9e87",
        "response_sha256": "6f092004420b9830ea552a1fb9b45bb74fa28473bf8447c7e58e965a21e66559",
        "input_tokens": 9739,
        "output_tokens": 207,
        "seconds": 1.669,
        "finish_reason": "stop"
      },
      {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "2f04fef2-ca3a-422d-b93e-0136957dcbcc",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "6ee2c631c6f504d68662002de971d346aaa17d83815e4f35db6020c0e5b50f26",
        "response_sha256": "55b270eda9b4cfa5a91449db7804f0f69e3b1eb98bfd902e3fdebb8ecba53229",
        "input_tokens": 9402,
        "output_tokens": 181,
        "seconds": 1.371,
        "finish_reason": "stop"
      },
      {
        "role": "curator",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "62d2ace5-c21f-4a5d-8052-01d9721af8f1",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "5be9930f1c7e6e99cdefd90ec58e752b45f9c645c561d1164273690f234762a4",
        "response_sha256": "ef071a2b7640e33a322000e0931b296231c4235f0e323b62b9f94958a4a9bf23",
        "input_tokens": 707,
        "output_tokens": 396,
        "seconds": 2.451,
        "finish_reason": "stop"
      }
    ]
  },
  "warnings": [
    "验证集成绩，不是最终测试成绩。",
    "受限AST构造器程序，不是任意Python或Docker操作系统沙箱。",
    "未提供客户端 ID 字段，因此无法承诺或验证按客户端分离；只能按现有分组策略进行数据隔离。",
    "若请求的整轮墙钟预算低于 10 秒，将视为不兼容并回退到 10 秒。",
    "未指定具体向量化参数、分类器超参数或稳定性检查细节，需在实现中采用合理默认并记录。"
  ],
  "search_tree": [
    {
      "candidate_id": "sms_logreg_default",
      "parent_id": null,
      "status": "passed",
      "average_precision": 0.9583895772337544,
      "pruned": false,
      "pruned_reason": null
    },
    {
      "candidate_id": "sms_nb_default",
      "parent_id": null,
      "status": "passed",
      "average_precision": 0.9459327203990979,
      "pruned": false,
      "pruned_reason": null
    }
  ],
  "knowledge_writeback": {
    "run_saved": true,
    "experiences": [
      {
        "failure_id": "failure-ba86ea2a2a83077dbf9b4b2c",
        "fingerprint": "5258fc58a6c92846dae185438054b24386a2ba3aa31931acafb80ec5da19383a",
        "run_id": "799d2116572a4fbba835d42969156064",
        "error_type": "plan_consistency",
        "diagnosis": "The generated code defines a function `broken_pipeline(task_spec)` that returns an unfitted sklearn Pipeline, but the plan requires a constructor program that builds and fits a model on the provided dataset. The function name and signature do not match the expected constructor interface, and no training/fitting step is performed, so the source policy check cannot verify consistency with the plan.",
        "fix": "Rename the function to the expected constructor name (e.g., `build_model` or `make_pipeline`) and ensure it returns a fitted estimator by calling `.fit(X, y)` on the pipeline using the task's text feature and target label, or return the unfitted pipeline only if the plan explicitly expects a constructor that the runner will fit. Align the function signature with the task_spec fields (text column, label column) and remove the non-standard `broken_pipeline` name.",
        "task_type": "text_binary_classification",
        "validated": true,
        "status": "validated",
        "origin": "runtime_experience"
      }
    ]
  },
  "data_summary": {
    "train_rows": 3095,
    "validation_rows": 1032
  },
  "interpretation": {
    "objective": "构建短信垃圾信息二分类能力，在固定数据集 sms 上比较 TF-IDF 结合逻辑回归与朴素贝叶斯两种方案，并报告平均精度（AP）、F1 以及接口稳定性检查结果。",
    "constraints": [
      "仅使用 task_spec 中给定的字段：文本特征 text，正类标签 spam，任务类型 text_binary_classification。",
      "主指标为 average_precision（AP），同时报告 F1。",
      "必须保持训练、验证、测试隔离，遵循 normalized_group_split_v1 特征/分组策略。",
      "随机种子固定为 42。",
      "资源限制：CPU 2 核，内存 2048 MiB，单次运行超时 120 秒。",
      "不得更改 task_spec、评估标签、划分协议或安全约束。"
    ],
    "assumptions": [
      "数据集 sms 已包含 text 与 spam 标签字段，可直接用于文本二分类。",
      "TF-IDF 作为文本向量化方法，逻辑回归与朴素贝叶斯作为候选分类器。",
      "接口稳定性检查指对模型推理接口在重复调用或边界输入下的一致性验证。",
      "验证集用于方案比较与选择，测试集仅用于最终报告。"
    ],
    "warnings": [
      "未提供客户端 ID 字段，因此无法承诺或验证按客户端分离；只能按现有分组策略进行数据隔离。",
      "若请求的整轮墙钟预算低于 10 秒，将视为不兼容并回退到 10 秒。",
      "未指定具体向量化参数、分类器超参数或稳定性检查细节，需在实现中采用合理默认并记录。"
    ],
    "incompatible_requests": [],
    "requested_run_seconds": null
  },
  "evidence": [
    {
      "capability_id": "text-tfidf",
      "confidence": 1.0,
      "created_at": "2026-09-28T11:23:24.518340+00:00",
      "dependencies": [
        "Python >=3.10",
        "scikit-learn"
      ],
      "evidence": [
        {
          "content_sha256": "876f0d334735f77174822fabff287fab5602ccff8973a5430ebc70548916da62",
          "license": "BSD-3-Clause",
          "locator": {
            "imports": [
              "import array",
              "import re",
              "import unicodedata",
              "import warnings",
              "from collections import defaultdict",
              "from collections.abc import Mapping",
              "from functools import partial",
              "from numbers import Integral",
              "from operator import itemgetter",
              "import numpy as np",
              "import scipy.sparse as sp",
              "from sklearn.utils import metadata_routing",
              "from ..base import BaseEstimator, OneToOneFeatureMixin, TransformerMixin, _fit_context",
              "from ..exceptions import NotFittedError",
              "from ..preprocessing import normalize",
              "from ..utils._param_validation import HasMethods, Interval, RealNotInt, StrOptions",
              "from ..utils.fixes import _IS_32BIT",
              "from ..utils.validation import FLOAT_DTYPES, check_array, check_is_fitted, validate_data",
              "from ._hash import FeatureHasher",
              "from ._stop_words import ENGLISH_STOP_WORDS"
            ],
            "line_end": 2137,
            "line_start": 1735,
            "methods": [
              "__init__",
              "idf_",
              "idf_",
              "_check_params",
              "fit",
              "fit_transform",
              "transform",
              "__sklearn_tags__"
            ],
            "parse_mode": "ast-only",
            "path": "/root/algorithm-capability-factory/.venv/lib/python3.10/site-packages/sklearn/feature_extraction/text.py",
            "relative_path": "sklearn/feature_extraction/text.py",
            "signature": "class TfidfVectorizer(CountVectorizer):\n    def __init__(self, *, input='content', encoding='utf-8', decode_error='strict', strip_accents=None, lowercase=True, preprocessor=None, tokenizer=None, analyzer='word', stop_words=None, token_pattern='(?u)\\\\b\\\\w\\\\w+\\\\b', ngram_range=(1, 1), max_df=1.0, min_df=1, max_features=None, vocabulary=None, binary=False, dtype=np.float64, norm='l2', use_idf=True, smooth_idf=True, sublinear_tf=False)",
            "symbol": "TfidfVectorizer"
          },
          "revision": "1.7.2",
          "source_id": "src-ecb336a2fa483eb3b4f26d0b",
          "uri": "https://github.com/scikit-learn/scikit-learn/blob/1.7.2/sklearn/feature_extraction/text.py"
        },
        {
          "content_sha256": "10bbedb7d1e5d03c92860a5aef348cb020e7a385a5ce520677bd95790881a970",
          "license": "original-project-notes",
          "locator": {
            "line_end": 62,
            "line_start": 51,
            "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
          },
          "revision": "sha256:10bbedb7d1e5d03c92860a5aef348cb020e7a385a5ce520677bd95790881a970",
          "source_id": "src-df4abddd7280ca49a8328ee6",
          "uri": "file:///root/algorithm-capability-factory/docs/02_%E6%95%B0%E6%8D%AE%E4%B8%8E%E7%9F%A5%E8%AF%86%E6%9D%A5%E6%BA%90.md"
        }
      ],
      "extraction_method": "curated-source-grounded",
      "id": "text-tfidf",
      "input_schema": {
        "task_types": [
          "text_binary_classification"
        ],
        "type": "features"
      },
      "name": "TF-IDF 文本稀疏向量",
      "origin": "manual_seed",
      "output_schema": {
        "type": "implementation-guidance"
      },
      "preconditions": [],
      "related": [
        "probability-logistic",
        "complement-naive-bayes"
      ],
      "status": "extracted",
      "summary": "TfidfVectorizer 将原始文本转成 TF-IDF 特征。训练词表和 IDF 只使用训练文本；通过 ngram_range、max_features 和 min_df 控制表示及资源。与线性分类器或朴素贝叶斯组合，保持稀疏表示。",
      "tags": [
        "TfidfVectorizer",
        "tfidf",
        "短信",
        "文本",
        "词表",
        "稀疏"
      ],
      "task_types": [
        "text_binary_classification"
      ],
      "uses": [
        {
          "kind": "Transform",
          "label": "TfidfVectorizer"
        }
      ],
      "version": 1,
      "score": 3.8,
      "lexical_score": 2.142857,
      "graph_score": 1.657143,
      "evidence_path": [
        {
          "seed": "capability:complement-naive-bayes:v1",
          "hops": [
            {
              "from": "capability:complement-naive-bayes:v1",
              "relation": "REQUIRES",
              "to": "capability:text-tfidf:v1"
            }
          ],
          "bonus": 0.9714285714285714
        },
        {
          "seed": "capability:probability-logistic:v1",
          "hops": [
            {
              "from": "capability:probability-logistic:v1",
              "relation": "REQUIRES",
              "to": "capability:text-tfidf:v1"
            }
          ],
          "bonus": 0.6857142857142857
        }
      ],
      "graph_used": true,
      "source_locator": [
        {
          "imports": [
            "import array",
            "import re",
            "import unicodedata",
            "import warnings",
            "from collections import defaultdict",
            "from collections.abc import Mapping",
            "from functools import partial",
            "from numbers import Integral",
            "from operator import itemgetter",
            "import numpy as np",
            "import scipy.sparse as sp",
            "from sklearn.utils import metadata_routing",
            "from ..base import BaseEstimator, OneToOneFeatureMixin, TransformerMixin, _fit_context",
            "from ..exceptions import NotFittedError",
            "from ..preprocessing import normalize",
            "from ..utils._param_validation import HasMethods, Interval, RealNotInt, StrOptions",
            "from ..utils.fixes import _IS_32BIT",
            "from ..utils.validation import FLOAT_DTYPES, check_array, check_is_fitted, validate_data",
            "from ._hash import FeatureHasher",
            "from ._stop_words import ENGLISH_STOP_WORDS"
          ],
          "line_end": 2137,
          "line_start": 1735,
          "methods": [
            "__init__",
            "idf_",
            "idf_",
            "_check_params",
            "fit",
            "fit_transform",
            "transform",
            "__sklearn_tags__"
          ],
          "parse_mode": "ast-only",
          "path": "/root/algorithm-capability-factory/.venv/lib/python3.10/site-packages/sklearn/feature_extraction/text.py",
          "relative_path": "sklearn/feature_extraction/text.py",
          "signature": "class TfidfVectorizer(CountVectorizer):\n    def __init__(self, *, input='content', encoding='utf-8', decode_error='strict', strip_accents=None, lowercase=True, preprocessor=None, tokenizer=None, analyzer='word', stop_words=None, token_pattern='(?u)\\\\b\\\\w\\\\w+\\\\b', ngram_range=(1, 1), max_df=1.0, min_df=1, max_features=None, vocabulary=None, binary=False, dtype=np.float64, norm='l2', use_idf=True, smooth_idf=True, sublinear_tf=False)",
          "symbol": "TfidfVectorizer"
        },
        {
          "line_end": 62,
          "line_start": 51,
          "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
        }
      ],
      "matched_constraints": [
        "task_type=text_binary_classification"
      ],
      "rejected_reason": null
    },
    {
      "capability_id": "complement-naive-bayes",
      "confidence": 1.0,
      "created_at": "2026-09-28T11:23:24.518487+00:00",
      "dependencies": [
        "Python >=3.10",
        "scikit-learn"
      ],
      "evidence": [
        {
          "content_sha256": "ee265c08217b2b4a0543bd984cb11a962b4d2f4c9a8150332e84f1364b5d37ec",
          "license": "BSD-3-Clause",
          "locator": {
            "imports": [
              "import warnings",
              "from abc import ABCMeta, abstractmethod",
              "from numbers import Integral, Real",
              "import numpy as np",
              "from scipy.special import logsumexp",
              "from .base import BaseEstimator, ClassifierMixin, _fit_context",
              "from .preprocessing import LabelBinarizer, binarize, label_binarize",
              "from .utils._param_validation import Interval",
              "from .utils.extmath import safe_sparse_dot",
              "from .utils.multiclass import _check_partial_fit_first_call",
              "from .utils.validation import _check_n_features, _check_sample_weight, check_is_fitted, check_non_negative, validate_data"
            ],
            "line_end": 1059,
            "line_start": 907,
            "methods": [
              "__init__",
              "__sklearn_tags__",
              "_count",
              "_update_feature_log_prob",
              "_joint_log_likelihood"
            ],
            "parse_mode": "ast-only",
            "path": "/root/algorithm-capability-factory/.venv/lib/python3.10/site-packages/sklearn/naive_bayes.py",
            "relative_path": "sklearn/naive_bayes.py",
            "signature": "class ComplementNB(_BaseDiscreteNB):\n    def __init__(self, *, alpha=1.0, force_alpha=True, fit_prior=True, class_prior=None, norm=False)",
            "symbol": "ComplementNB"
          },
          "revision": "1.7.2",
          "source_id": "src-01e94fa0e553de89c2a7a671",
          "uri": "https://github.com/scikit-learn/scikit-learn/blob/1.7.2/sklearn/naive_bayes.py"
        }
      ],
      "extraction_method": "curated-source-grounded",
      "id": "complement-naive-bayes",
      "input_schema": {
        "task_types": [
          "text_binary_classification"
        ],
        "type": "features"
      },
      "name": "ComplementNB 文本分类",
      "origin": "manual_seed",
      "output_schema": {
        "type": "implementation-guidance"
      },
      "preconditions": [],
      "related": [
        "text-tfidf",
        "average-precision"
      ],
      "status": "extracted",
      "summary": "ComplementNB 是面向不平衡数据的补集朴素贝叶斯估计器，适合非负文本计数或 TF-IDF 特征。不得将中心化后含负数的特征直接传入；必须由验证集实测性能。",
      "tags": [
        "ComplementNB",
        "朴素贝叶斯",
        "不平衡",
        "非负",
        "文本"
      ],
      "task_types": [
        "text_binary_classification"
      ],
      "uses": [
        {
          "kind": "Algorithm",
          "label": "ComplementNB"
        },
        {
          "kind": "Transform",
          "label": "TfidfVectorizer"
        }
      ],
      "version": 1,
      "score": 3.628571,
      "lexical_score": 2.428571,
      "graph_score": 1.2,
      "evidence_path": [
        {
          "seed": "capability:text-tfidf:v1",
          "hops": [
            {
              "from": "capability:text-tfidf:v1",
              "relation": "REQUIRES",
              "to": "capability:complement-naive-bayes:v1"
            }
          ],
          "bonus": 0.8571428571428572
        },
        {
          "seed": "capability:probability-logistic:v1",
          "hops": [
            {
              "from": "capability:probability-logistic:v1",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            },
            {
              "from": "capability:average-precision:v1",
              "relation": "REQUIRES",
              "to": "capability:complement-naive-bayes:v1"
            }
          ],
          "bonus": 0.34285714285714286
        }
      ],
      "graph_used": true,
      "source_locator": [
        {
          "imports": [
            "import warnings",
            "from abc import ABCMeta, abstractmethod",
            "from numbers import Integral, Real",
            "import numpy as np",
            "from scipy.special import logsumexp",
            "from .base import BaseEstimator, ClassifierMixin, _fit_context",
            "from .preprocessing import LabelBinarizer, binarize, label_binarize",
            "from .utils._param_validation import Interval",
            "from .utils.extmath import safe_sparse_dot",
            "from .utils.multiclass import _check_partial_fit_first_call",
            "from .utils.validation import _check_n_features, _check_sample_weight, check_is_fitted, check_non_negative, validate_data"
          ],
          "line_end": 1059,
          "line_start": 907,
          "methods": [
            "__init__",
            "__sklearn_tags__",
            "_count",
            "_update_feature_log_prob",
            "_joint_log_likelihood"
          ],
          "parse_mode": "ast-only",
          "path": "/root/algorithm-capability-factory/.venv/lib/python3.10/site-packages/sklearn/naive_bayes.py",
          "relative_path": "sklearn/naive_bayes.py",
          "signature": "class ComplementNB(_BaseDiscreteNB):\n    def __init__(self, *, alpha=1.0, force_alpha=True, fit_prior=True, class_prior=None, norm=False)",
          "symbol": "ComplementNB"
        }
      ],
      "matched_constraints": [
        "task_type=text_binary_classification"
      ],
      "rejected_reason": null
    },
    {
      "capability_id": "probability-logistic",
      "confidence": 1.0,
      "created_at": "2026-09-28T11:23:24.517906+00:00",
      "dependencies": [
        "Python >=3.10",
        "scikit-learn"
      ],
      "evidence": [
        {
          "content_sha256": "981f4e11c9a6fc2b02cd9322f2926849143e4a8bf1819e3a4159a9fce615a00c",
          "license": "BSD-3-Clause",
          "locator": {
            "imports": [
              "import numbers",
              "import warnings",
              "from numbers import Integral, Real",
              "import numpy as np",
              "from joblib import effective_n_jobs",
              "from scipy import optimize",
              "from sklearn.metrics import get_scorer_names",
              "from .._loss.loss import HalfBinomialLoss, HalfMultinomialLoss",
              "from ..base import _fit_context",
              "from ..metrics import get_scorer",
              "from ..model_selection import check_cv",
              "from ..preprocessing import LabelBinarizer, LabelEncoder",
              "from ..svm._base import _fit_liblinear",
              "from ..utils import Bunch, check_array, check_consistent_length, check_random_state, compute_class_weight",
              "from ..utils._param_validation import Hidden, Interval, StrOptions",
              "from ..utils.extmath import row_norms, softmax",
              "from ..utils.fixes import _get_additional_lbfgs_options_dict",
              "from ..utils.metadata_routing import MetadataRouter, MethodMapping, _raise_for_params, _routing_enabled, process_routing",
              "from ..utils.multiclass import check_classification_targets",
              "from ..utils.optimize import _check_optimize_result, _newton_cg",
              "from ..utils.parallel import Parallel, delayed",
              "from ..utils.validation import _check_method_params, _check_sample_weight, check_is_fitted, validate_data",
              "from ._base import BaseEstimator, LinearClassifierMixin, SparseCoefMixin",
              "from ._glm.glm import NewtonCholeskySolver",
              "from ._linear_loss import LinearModelLoss",
              "from ._sag import sag_solver"
            ],
            "line_end": 1497,
            "line_start": 829,
            "methods": [
              "__init__",
              "fit",
              "predict_proba",
              "predict_log_proba",
              "__sklearn_tags__"
            ],
            "parse_mode": "ast-only",
            "path": "/root/algorithm-capability-factory/.venv/lib/python3.10/site-packages/sklearn/linear_model/_logistic.py",
            "relative_path": "sklearn/linear_model/_logistic.py",
            "signature": "class LogisticRegression(LinearClassifierMixin, SparseCoefMixin, BaseEstimator):\n    def __init__(self, penalty='l2', *, dual=False, tol=0.0001, C=1.0, fit_intercept=True, intercept_scaling=1, class_weight=None, random_state=None, solver='lbfgs', max_iter=100, multi_class='deprecated', verbose=0, warm_start=False, n_jobs=None, l1_ratio=None)",
            "symbol": "LogisticRegression"
          },
          "revision": "1.7.2",
          "source_id": "src-584b66a31950a968f84ef11b",
          "uri": "https://github.com/scikit-learn/scikit-learn/blob/1.7.2/sklearn/linear_model/_logistic.py"
        }
      ],
      "extraction_method": "curated-source-grounded",
      "id": "probability-logistic",
      "input_schema": {
        "task_types": [
          "tabular_binary_classification",
          "text_binary_classification"
        ],
        "type": "features"
      },
      "name": "逻辑回归二分类概率接口",
      "origin": "manual_seed",
      "output_schema": {
        "type": "implementation-guidance"
      },
      "preconditions": [],
      "related": [
        "average-precision"
      ],
      "status": "extracted",
      "summary": "LogisticRegression 提供 predict_proba，输出列顺序由 classes_ 决定。必须根据正类标签映射提取正确一列，不能把 predict 的类别标签当概率。适合经过编码的表格特征及 TF-IDF 稀疏文本特征。",
      "tags": [
        "LogisticRegression",
        "predict_proba",
        "概率",
        "二分类",
        "classes_"
      ],
      "task_types": [
        "tabular_binary_classification",
        "text_binary_classification"
      ],
      "uses": [
        {
          "kind": "Algorithm",
          "label": "LogisticRegression"
        }
      ],
      "version": 1,
      "score": 3.057143,
      "lexical_score": 1.714286,
      "graph_score": 1.342857,
      "evidence_path": [
        {
          "seed": "capability:complement-naive-bayes:v1",
          "hops": [
            {
              "from": "capability:complement-naive-bayes:v1",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            },
            {
              "from": "capability:average-precision:v1",
              "relation": "REQUIRES",
              "to": "capability:probability-logistic:v1"
            }
          ],
          "bonus": 0.4857142857142857
        },
        {
          "seed": "capability:text-tfidf:v1",
          "hops": [
            {
              "from": "capability:text-tfidf:v1",
              "relation": "REQUIRES",
              "to": "capability:probability-logistic:v1"
            }
          ],
          "bonus": 0.8571428571428572
        }
      ],
      "graph_used": true,
      "source_locator": [
        {
          "imports": [
            "import numbers",
            "import warnings",
            "from numbers import Integral, Real",
            "import numpy as np",
            "from joblib import effective_n_jobs",
            "from scipy import optimize",
            "from sklearn.metrics import get_scorer_names",
            "from .._loss.loss import HalfBinomialLoss, HalfMultinomialLoss",
            "from ..base import _fit_context",
            "from ..metrics import get_scorer",
            "from ..model_selection import check_cv",
            "from ..preprocessing import LabelBinarizer, LabelEncoder",
            "from ..svm._base import _fit_liblinear",
            "from ..utils import Bunch, check_array, check_consistent_length, check_random_state, compute_class_weight",
            "from ..utils._param_validation import Hidden, Interval, StrOptions",
            "from ..utils.extmath import row_norms, softmax",
            "from ..utils.fixes import _get_additional_lbfgs_options_dict",
            "from ..utils.metadata_routing import MetadataRouter, MethodMapping, _raise_for_params, _routing_enabled, process_routing",
            "from ..utils.multiclass import check_classification_targets",
            "from ..utils.optimize import _check_optimize_result, _newton_cg",
            "from ..utils.parallel import Parallel, delayed",
            "from ..utils.validation import _check_method_params, _check_sample_weight, check_is_fitted, validate_data",
            "from ._base import BaseEstimator, LinearClassifierMixin, SparseCoefMixin",
            "from ._glm.glm import NewtonCholeskySolver",
            "from ._linear_loss import LinearModelLoss",
            "from ._sag import sag_solver"
          ],
          "line_end": 1497,
          "line_start": 829,
          "methods": [
            "__init__",
            "fit",
            "predict_proba",
            "predict_log_proba",
            "__sklearn_tags__"
          ],
          "parse_mode": "ast-only",
          "path": "/root/algorithm-capability-factory/.venv/lib/python3.10/site-packages/sklearn/linear_model/_logistic.py",
          "relative_path": "sklearn/linear_model/_logistic.py",
          "signature": "class LogisticRegression(LinearClassifierMixin, SparseCoefMixin, BaseEstimator):\n    def __init__(self, penalty='l2', *, dual=False, tol=0.0001, C=1.0, fit_intercept=True, intercept_scaling=1, class_weight=None, random_state=None, solver='lbfgs', max_iter=100, multi_class='deprecated', verbose=0, warm_start=False, n_jobs=None, l1_ratio=None)",
          "symbol": "LogisticRegression"
        }
      ],
      "matched_constraints": [
        "task_type=text_binary_classification"
      ],
      "rejected_reason": null
    },
    {
      "capability_id": "average-precision",
      "confidence": 1.0,
      "created_at": "2026-09-28T11:23:24.518754+00:00",
      "dependencies": [
        "Python >=3.10",
        "scikit-learn"
      ],
      "evidence": [
        {
          "content_sha256": "a1fc02f0b042a3945c37692c9377a746800dd2a90cdc227df5268f218bea3f74",
          "license": "BSD-3-Clause",
          "locator": {
            "imports": [
              "import warnings",
              "from functools import partial",
              "from numbers import Integral, Real",
              "import numpy as np",
              "from scipy.integrate import trapezoid",
              "from scipy.sparse import csr_matrix, issparse",
              "from scipy.stats import rankdata",
              "from ..exceptions import UndefinedMetricWarning",
              "from ..preprocessing import label_binarize",
              "from ..utils import assert_all_finite, check_array, check_consistent_length, column_or_1d",
              "from ..utils._encode import _encode, _unique",
              "from ..utils._param_validation import Interval, StrOptions, validate_params",
              "from ..utils.extmath import stable_cumsum",
              "from ..utils.multiclass import type_of_target",
              "from ..utils.sparsefuncs import count_nonzero",
              "from ..utils.validation import _check_pos_label_consistency, _check_sample_weight",
              "from ._base import _average_binary_score, _average_multiclass_ovo_score"
            ],
            "line_end": 268,
            "line_start": 118,
            "methods": [
              "_binary_uninterpolated_average_precision"
            ],
            "parse_mode": "ast-only",
            "path": "/root/algorithm-capability-factory/.venv/lib/python3.10/site-packages/sklearn/metrics/_ranking.py",
            "relative_path": "sklearn/metrics/_ranking.py",
            "signature": "def average_precision_score(y_true, y_score, *, average='macro', pos_label=1, sample_weight=None)",
            "symbol": "average_precision_score"
          },
          "revision": "1.7.2",
          "source_id": "src-9ca2de7b8493fff6ad94d779",
          "uri": "https://github.com/scikit-learn/scikit-learn/blob/1.7.2/sklearn/metrics/_ranking.py"
        }
      ],
      "extraction_method": "curated-source-grounded",
      "id": "average-precision",
      "input_schema": {
        "task_types": [
          "tabular_binary_classification",
          "text_binary_classification"
        ],
        "type": "features"
      },
      "name": "不平衡二分类 Average Precision",
      "origin": "manual_seed",
      "output_schema": {
        "type": "implementation-guidance"
      },
      "preconditions": [
        "由可信验证器计算，使用同一分割协议。"
      ],
      "related": [],
      "status": "extracted",
      "summary": "average_precision_score 根据预测分数汇总精确率召回率曲线，定义为召回增量对 precision 的加权和。输入真实二值标签和正类预测分数；本项目以 AP 为主指标，并记录正类率基线。不得将其等同于梯形插值 PR-AUC。",
      "tags": [
        "average_precision",
        "AP",
        "排序",
        "不平衡",
        "precision",
        "recall",
        "正类"
      ],
      "task_types": [
        "tabular_binary_classification",
        "text_binary_classification"
      ],
      "uses": [
        {
          "kind": "Metric",
          "label": "average_precision"
        }
      ],
      "version": 1,
      "score": 2.942857,
      "lexical_score": 0.857143,
      "graph_score": 2.085714,
      "evidence_path": [
        {
          "seed": "capability:complement-naive-bayes:v1",
          "hops": [
            {
              "from": "capability:complement-naive-bayes:v1",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            }
          ],
          "bonus": 0.9714285714285714
        },
        {
          "seed": "capability:text-tfidf:v1",
          "hops": [
            {
              "from": "capability:text-tfidf:v1",
              "relation": "REQUIRES",
              "to": "capability:complement-naive-bayes:v1"
            },
            {
              "from": "capability:complement-naive-bayes:v1",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            }
          ],
          "bonus": 0.4285714285714286
        },
        {
          "seed": "capability:probability-logistic:v1",
          "hops": [
            {
              "from": "capability:probability-logistic:v1",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            }
          ],
          "bonus": 0.6857142857142857
        }
      ],
      "graph_used": true,
      "source_locator": [
        {
          "imports": [
            "import warnings",
            "from functools import partial",
            "from numbers import Integral, Real",
            "import numpy as np",
            "from scipy.integrate import trapezoid",
            "from scipy.sparse import csr_matrix, issparse",
            "from scipy.stats import rankdata",
            "from ..exceptions import UndefinedMetricWarning",
            "from ..preprocessing import label_binarize",
            "from ..utils import assert_all_finite, check_array, check_consistent_length, column_or_1d",
            "from ..utils._encode import _encode, _unique",
            "from ..utils._param_validation import Interval, StrOptions, validate_params",
            "from ..utils.extmath import stable_cumsum",
            "from ..utils.multiclass import type_of_target",
            "from ..utils.sparsefuncs import count_nonzero",
            "from ..utils.validation import _check_pos_label_consistency, _check_sample_weight",
            "from ._base import _average_binary_score, _average_multiclass_ovo_score"
          ],
          "line_end": 268,
          "line_start": 118,
          "methods": [
            "_binary_uninterpolated_average_precision"
          ],
          "parse_mode": "ast-only",
          "path": "/root/algorithm-capability-factory/.venv/lib/python3.10/site-packages/sklearn/metrics/_ranking.py",
          "relative_path": "sklearn/metrics/_ranking.py",
          "signature": "def average_precision_score(y_true, y_score, *, average='macro', pos_label=1, sample_weight=None)",
          "symbol": "average_precision_score"
        }
      ],
      "matched_constraints": [
        "task_type=text_binary_classification"
      ],
      "rejected_reason": null
    },
    {
      "capability_id": "sms-format",
      "confidence": 1.0,
      "created_at": "2026-09-28T11:23:24.516869+00:00",
      "dependencies": [
        "Python >=3.10",
        "scikit-learn"
      ],
      "evidence": [
        {
          "content_sha256": "8753cd2d3cab68f80c8257851b8c2037778c267f55accb6fd1b5a2e32d36a84e",
          "license": "CC-BY-4.0",
          "locator": {
            "line_end": 31,
            "line_start": 28,
            "path": "/root/algorithm-capability-factory/data/raw/sms-readme.txt"
          },
          "revision": "sha256:8753cd2d3cab68f80c8257851b8c2037778c267f55accb6fd1b5a2e32d36a84e",
          "source_id": "src-4f8bdb3589548b6b90312e82",
          "uri": "https://archive.ics.uci.edu/dataset/228/sms+spam+collection"
        },
        {
          "content_sha256": "10bbedb7d1e5d03c92860a5aef348cb020e7a385a5ce520677bd95790881a970",
          "license": "original-project-notes",
          "locator": {
            "line_end": 62,
            "line_start": 51,
            "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
          },
          "revision": "sha256:10bbedb7d1e5d03c92860a5aef348cb020e7a385a5ce520677bd95790881a970",
          "source_id": "src-df4abddd7280ca49a8328ee6",
          "uri": "file:///root/algorithm-capability-factory/docs/02_%E6%95%B0%E6%8D%AE%E4%B8%8E%E7%9F%A5%E8%AF%86%E6%9D%A5%E6%BA%90.md"
        }
      ],
      "extraction_method": "curated-source-grounded",
      "id": "sms-format",
      "input_schema": {
        "task_types": [
          "text_binary_classification"
        ],
        "type": "features"
      },
      "name": "SMS 垃圾短信标签和文本格式",
      "origin": "manual_seed",
      "output_schema": {
        "type": "implementation-guidance"
      },
      "preconditions": [],
      "related": [
        "text-tfidf",
        "average-precision"
      ],
      "status": "extracted",
      "summary": "官方 README 规定每行含标签和原始短信两列，标签为 ham 或 spam。项目逐行按首个制表符分隔，spam 作为正类；模型接收原始文本，演示和外部 LLM 只接收脱敏摘要。",
      "tags": [
        "sms",
        "文本",
        "短信",
        "spam",
        "ham",
        "tab"
      ],
      "task_types": [
        "text_binary_classification"
      ],
      "uses": [],
      "version": 1,
      "score": 2.4,
      "lexical_score": 0.714286,
      "graph_score": 1.685714,
      "evidence_path": [
        {
          "seed": "capability:complement-naive-bayes:v1",
          "hops": [
            {
              "from": "capability:complement-naive-bayes:v1",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            },
            {
              "from": "capability:average-precision:v1",
              "relation": "REQUIRES",
              "to": "capability:sms-format:v1"
            }
          ],
          "bonus": 0.4857142857142857
        },
        {
          "seed": "capability:text-tfidf:v1",
          "hops": [
            {
              "from": "capability:text-tfidf:v1",
              "relation": "REQUIRES",
              "to": "capability:sms-format:v1"
            }
          ],
          "bonus": 0.8571428571428572
        },
        {
          "seed": "capability:probability-logistic:v1",
          "hops": [
            {
              "from": "capability:probability-logistic:v1",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            },
            {
              "from": "capability:average-precision:v1",
              "relation": "REQUIRES",
              "to": "capability:sms-format:v1"
            }
          ],
          "bonus": 0.34285714285714286
        }
      ],
      "graph_used": true,
      "source_locator": [
        {
          "line_end": 31,
          "line_start": 28,
          "path": "/root/algorithm-capability-factory/data/raw/sms-readme.txt"
        },
        {
          "line_end": 62,
          "line_start": 51,
          "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
        }
      ],
      "matched_constraints": [
        "task_type=text_binary_classification"
      ],
      "rejected_reason": null
    },
    {
      "capability_id": "sms-grouped-split",
      "confidence": 1.0,
      "created_at": "2026-09-28T11:23:24.516970+00:00",
      "dependencies": [
        "Python >=3.10",
        "scikit-learn"
      ],
      "evidence": [
        {
          "content_sha256": "10bbedb7d1e5d03c92860a5aef348cb020e7a385a5ce520677bd95790881a970",
          "license": "original-project-notes",
          "locator": {
            "line_end": 62,
            "line_start": 51,
            "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
          },
          "revision": "sha256:10bbedb7d1e5d03c92860a5aef348cb020e7a385a5ce520677bd95790881a970",
          "source_id": "src-df4abddd7280ca49a8328ee6",
          "uri": "file:///root/algorithm-capability-factory/docs/02_%E6%95%B0%E6%8D%AE%E4%B8%8E%E7%9F%A5%E8%AF%86%E6%9D%A5%E6%BA%90.md"
        }
      ],
      "extraction_method": "curated-source-grounded",
      "id": "sms-grouped-split",
      "input_schema": {
        "task_types": [
          "text_binary_classification"
        ],
        "type": "features"
      },
      "name": "SMS 规范化去重分层划分",
      "origin": "manual_seed",
      "output_schema": {
        "type": "implementation-guidance"
      },
      "preconditions": [],
      "related": [
        "text-tfidf",
        "training-only-pipeline"
      ],
      "status": "extracted",
      "summary": "项目协议用大小写归一化和空白折叠生成文本组哈希；冲突标签隔离审查，每组保留首条后以 seed=42 分层 60/20/20。词表和 IDF 只在训练集拟合；精确哈希不保证消除全部语义近重复。",
      "tags": [
        "短信",
        "去重",
        "分层",
        "split",
        "重复",
        "词表"
      ],
      "task_types": [
        "text_binary_classification"
      ],
      "uses": [],
      "version": 1,
      "score": 2.4,
      "lexical_score": 0.714286,
      "graph_score": 1.685714,
      "evidence_path": [
        {
          "seed": "capability:complement-naive-bayes:v1",
          "hops": [
            {
              "from": "capability:complement-naive-bayes:v1",
              "relation": "REQUIRES",
              "to": "capability:text-tfidf:v1"
            },
            {
              "from": "capability:text-tfidf:v1",
              "relation": "REQUIRES",
              "to": "capability:sms-grouped-split:v1"
            }
          ],
          "bonus": 0.4857142857142857
        },
        {
          "seed": "capability:text-tfidf:v1",
          "hops": [
            {
              "from": "capability:text-tfidf:v1",
              "relation": "REQUIRES",
              "to": "capability:sms-grouped-split:v1"
            }
          ],
          "bonus": 0.8571428571428572
        },
        {
          "seed": "capability:probability-logistic:v1",
          "hops": [
            {
              "from": "capability:probability-logistic:v1",
              "relation": "REQUIRES",
              "to": "capability:text-tfidf:v1"
            },
            {
              "from": "capability:text-tfidf:v1",
              "relation": "REQUIRES",
              "to": "capability:sms-grouped-split:v1"
            }
          ],
          "bonus": 0.34285714285714286
        }
      ],
      "graph_used": true,
      "source_locator": [
        {
          "line_end": 62,
          "line_start": 51,
          "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
        }
      ],
      "matched_constraints": [
        "task_type=text_binary_classification"
      ],
      "rejected_reason": null
    }
  ],
  "quality_status": "above_prevalence",
  "explanation": {
    "summary": "在仅验证集（validation_only，1032 行，正例率 0.125）上，两个候选均通过。sms_logreg_default 的平均精度 AP=0.9584、AP 相对 dummy 提升 0.8334、ROC-AUC=0.9881、F1(阈值0.5)=0.8056、top 10% 精确率 0.9904、召回率 0.7984、lift=7.9231；sms_nb_default 的 AP=0.9459、AP 提升 0.8209、ROC-AUC=0.9781、F1=0.9024、top 10% 精确率 1.0、召回率 0.8062、lift=8.0。两者 top 10% 计数均为 104，排序并列按原始验证行顺序处理。综合 AP 与 ROC-AUC，选择 sms_logreg_default 为当前候选；该结论基于检索到的能力项 text-tfidf、probability-logistic、complement-naive-bayes、average-precision、sms-format、sms-grouped-split。",
    "limitations": [
      "所有指标均为 validation_only，sealed_test_scored=false，验证集表现不等于最终测试集表现，不能据此推断泛化性能。",
      "候选执行环境为受限 AST 执行，并非通用操作系统沙箱，不能据此声称具备通用隔离或安全保证。",
      "模型选择仅反映离线排序与分类指标差异，不构成因果营销提升证据；lift 与 precision@10% 是相关性度量，非因果效应。",
      "两个候选的排序并列均按 original_validation_row_order 处理，可能影响 top 10% 相关指标的稳定性。",
      "未提供失败候选或错误案例明细，无法评估鲁棒性、校准与子群差异。"
    ]
  },
  "finished_at": "2026-09-29T12:30:50.959713+00:00",
  "timing": {
    "wall_seconds": 21.366,
    "budget_seconds": 900.0,
    "request_ceiling_seconds": 900
  },
  "report_paths": {}
}
````

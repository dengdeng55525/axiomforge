# 算法能力验证报告

指标与状态来自原始验证事实；缺失项不填零、不推断通过。

模式由原始报告的 mode 字段说明：mock 为模拟，replay 为历史回放。

````json
{
  "schema_version": "1.0",
  "run_id": "660682f3cf324bf1938b78c70f2fce8c",
  "status": "passed",
  "mode": "real",
  "provider": "openai",
  "description": "比较 TF-IDF 逻辑回归与朴素贝叶斯的短信垃圾分类能力。按固定数据协议独立验证，输出可运行代码、验证指标、知识依据和资源分析，并保存验证结果。",
  "dataset_id": "sms",
  "created_at": "2026-09-30T16:49:10.313168+00:00",
  "request": {
    "description": "比较 TF-IDF 逻辑回归与朴素贝叶斯的短信垃圾分类能力。按固定数据协议独立验证，输出可运行代码、验证指标、知识依据和资源分析，并保存验证结果。",
    "dataset_id": "sms",
    "provider": "openai",
    "max_candidates": 2,
    "max_repairs": 2,
    "use_graph": true,
    "use_retrieval": true,
    "orchestration": "multi_role",
    "search": "compare",
    "inject_failure": false,
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
  "model": "gpt-5.5",
  "provenance": {
    "prompt_version": "algoforge-roles-v3",
    "sealed_test_scored": false,
    "agent_runtime": {
      "framework": "langchain-core",
      "version": "1.6.5",
      "role_chain": [
        "invoke_provider",
        "persist_response",
        "validate_contract"
      ],
      "retrieval_tool": "search_capabilities",
      "external_tracing": false
    },
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
      "candidate_id": "sms_tfidf_logistic_default",
      "plan": {
        "candidate_id": "sms_tfidf_logistic_default",
        "algorithm": "logistic",
        "variant": "default",
        "rationale": "使用训练集拟合 TF-IDF 后接 LogisticRegression，适合短信稀疏文本；按固定分组分层协议验证，并以 average precision 比较排序能力。",
        "evidence_ids": [
          "text-tfidf",
          "probability-logistic",
          "sms-grouped-split",
          "average-precision"
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
        "worker_pid": 71573,
        "wall_seconds": 0.8530818948056549,
        "fit_seconds": 0.10893881996162236,
        "predict_seconds": 0.013013828080147505,
        "worker_wall_seconds": 0.7338977118488401,
        "peak_rss_mib": 265.8984375,
        "cpu_seconds": 0.9723679999999999,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 0.8830327491741627
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "bc7d91b43c429a096367830f391b0f80f4003ece9a0c2605d8e40a974e4c0405",
          "code_path": "candidates/sms_tfidf_logistic_default/attempt_0/model.py",
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
            "worker_pid": 71573,
            "wall_seconds": 0.8530818948056549,
            "fit_seconds": 0.10893881996162236,
            "predict_seconds": 0.013013828080147505,
            "worker_wall_seconds": 0.7338977118488401,
            "peak_rss_mib": 265.8984375,
            "cpu_seconds": 0.9723679999999999,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 0.8830327491741627
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
      "artifact_id": "sms_tfidf_logistic_default",
      "parent_id": null,
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
      "code_sha256": "bc7d91b43c429a096367830f391b0f80f4003ece9a0c2605d8e40a974e4c0405",
      "code_path": "candidates/sms_tfidf_logistic_default/attempt_0/model.py",
      "explanation": "The text-tfidf and probability-logistic evidence supports the planned SMS TF-IDF plus LogisticRegression pipeline, with the required resource limits and fixed random state."
    },
    {
      "candidate_id": "sms_tfidf_nb_default",
      "plan": {
        "candidate_id": "sms_tfidf_nb_default",
        "algorithm": "nb",
        "variant": "default",
        "rationale": "使用训练集拟合 TF-IDF 后接 ComplementNB；该估计器支持非负 TF-IDF 特征，适合纳入短信文本基线，并按同一协议以 average precision 验证。",
        "evidence_ids": [
          "text-tfidf",
          "complement-naive-bayes",
          "sms-grouped-split",
          "average-precision"
        ],
        "parent_id": null
      },
      "status": "passed",
      "metrics": {
        "average_precision": 0.9598341674027927,
        "roc_auc": 0.9837406749250989,
        "f1_threshold_0_5": 0.9147286821705426,
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
        "ap_improvement_over_dummy": 0.8348341674027927
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
        "worker_pid": 71892,
        "wall_seconds": 0.8032961399294436,
        "fit_seconds": 0.06966879102401435,
        "predict_seconds": 0.012536511989310384,
        "worker_wall_seconds": 0.6627093609422445,
        "peak_rss_mib": 267.8984375,
        "cpu_seconds": 0.88111,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 0.8337043148931116
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "54cbd5421bb1f5f5057e24b805659985a27534d986a481847c631835b70391e1",
          "code_path": "candidates/sms_tfidf_nb_default/attempt_0/model.py",
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
            "average_precision": 0.9598341674027927,
            "roc_auc": 0.9837406749250989,
            "f1_threshold_0_5": 0.9147286821705426,
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
            "ap_improvement_over_dummy": 0.8348341674027927
          },
          "resources": {
            "limits": {
              "timeout_s": 120.0,
              "memory_mib": 2048,
              "cpu_cores": 2
            },
            "worker_pid": 71892,
            "wall_seconds": 0.8032961399294436,
            "fit_seconds": 0.06966879102401435,
            "predict_seconds": 0.012536511989310384,
            "worker_wall_seconds": 0.6627093609422445,
            "peak_rss_mib": 267.8984375,
            "cpu_seconds": 0.88111,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 0.8337043148931116
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
              "alpha": 0.5
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
      "artifact_id": "sms_tfidf_nb_default",
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
          "alpha": 0.5
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
      "code_sha256": "54cbd5421bb1f5f5057e24b805659985a27534d986a481847c631835b70391e1",
      "code_path": "candidates/sms_tfidf_nb_default/attempt_0/model.py",
      "explanation": "Uses the supplied SMS evidence and plan: training-fitted TF-IDF with bigrams and bounded vocabulary followed by ComplementNB for nonnegative sparse text features and predict_proba-compatible classification."
    }
  ],
  "selected_candidate_id": "sms_tfidf_nb_default",
  "events": [
    {
      "sequence": 0,
      "event_type": "RECEIVED",
      "type": "RECEIVED",
      "created_at": "2026-09-30T16:49:10.459008+00:00",
      "data": {
        "mode": "real",
        "model": "gpt-5.5"
      }
    },
    {
      "sequence": 1,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-30T16:50:16.654003+00:00",
      "data": {
        "role": "interpreter",
        "requested_model": "gpt-5.5",
        "returned_model": "gpt-5.5",
        "endpoint": "https://sub2api.luciferai.cc/v1",
        "response_id": "resp_0e67268ee1c99759016abd3d89f1b087d1b9d2f7cb4af67772",
        "prompt_sha256": "de3bc6bfe87cb223fa6983cb6eff48787b436b6a08a25fd19ecc216e2e93c534",
        "response_sha256": "ae9b8561a99a63d4147561c83957e8e8943c1afc01ec1d85bb2356fa7a00f1e8",
        "seconds": 64.976,
        "finish_reason": "completed",
        "api": "responses",
        "usage_available": true,
        "input_tokens": 738,
        "output_tokens": 1070,
        "cached_input_tokens": 0,
        "requested_max_output_tokens": 1300,
        "output_limit_exceeded": false,
        "stream": true
      }
    },
    {
      "sequence": 2,
      "event_type": "SPEC_VALIDATED",
      "type": "SPEC_VALIDATED",
      "created_at": "2026-09-30T16:50:17.071891+00:00",
      "data": {
        "task_type": "text_binary_classification",
        "assumptions": [
          "TF-IDF向量化和模型训练均可基于现有text字段完成，且不引入数据集之外的特征。",
          "朴素贝叶斯的具体变体应选择适用于非负TF-IDF特征且受支持的实现；若实现要求整数计数，则需采用兼容TF-IDF的受支持变体或明确调整特征表示。",
          "保存结果所需的具体文件格式和路径未给出，应采用运行环境允许的明确、可审计位置，并在代码中说明。",
          "知识依据可限于TF-IDF、逻辑回归、朴素贝叶斯及average_precision的通用方法原理；当前未提供外部检索证据或仓库证据。"
        ]
      }
    },
    {
      "sequence": 3,
      "event_type": "KNOWLEDGE_RETRIEVED",
      "type": "KNOWLEDGE_RETRIEVED",
      "created_at": "2026-09-30T16:50:17.378885+00:00",
      "data": {
        "count": 6,
        "use_graph": true,
        "tool": "search_capabilities",
        "capability_ids": [
          "complement-naive-bayes",
          "text-tfidf",
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
      "created_at": "2026-09-30T16:50:43.743211+00:00",
      "data": {
        "role": "planner",
        "requested_model": "gpt-5.5",
        "returned_model": "gpt-5.5",
        "endpoint": "https://sub2api.luciferai.cc/v1",
        "response_id": "resp_0b10e1a959ee500b016abd3dcce99887d2949e64f705de2d42",
        "prompt_sha256": "f5eda84074da411d6d5a196e375d51df6632a7777c012f144a1b31ade48d27ca",
        "response_sha256": "2203d8585de6e21ecab440ac66d4703bc6817874bf470e66e92816abda54e035",
        "seconds": 26.12,
        "finish_reason": "completed",
        "api": "responses",
        "usage_available": true,
        "input_tokens": 8974,
        "output_tokens": 362,
        "cached_input_tokens": 0,
        "requested_max_output_tokens": 2200,
        "output_limit_exceeded": false,
        "stream": true
      }
    },
    {
      "sequence": 5,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-30T16:50:44.239825+00:00",
      "data": {
        "candidate_id": "sms_tfidf_logistic_default",
        "algorithm": "logistic",
        "variant": "default",
        "rationale": "使用训练集拟合 TF-IDF 后接 LogisticRegression，适合短信稀疏文本；按固定分组分层协议验证，并以 average precision 比较排序能力。",
        "evidence_ids": [
          "text-tfidf",
          "probability-logistic",
          "sms-grouped-split",
          "average-precision"
        ],
        "parent_id": null
      }
    },
    {
      "sequence": 6,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-30T16:51:15.864968+00:00",
      "data": {
        "role": "coder",
        "requested_model": "gpt-5.5",
        "returned_model": "gpt-5.5",
        "endpoint": "https://sub2api.luciferai.cc/v1",
        "response_id": "resp_0204b14f3b764134016abd3de6b84487d28e0694fc642b6e89",
        "prompt_sha256": "a7929071035f6539132e0ac35421a3f55fa9616a890ca4a7558986e9f3efa6e9",
        "response_sha256": "72ee2116d2979b584af06e22585949eee4deb58cf2bec5f6b348330fd2634e59",
        "seconds": 31.183,
        "finish_reason": "completed",
        "api": "responses",
        "usage_available": true,
        "input_tokens": 9671,
        "output_tokens": 470,
        "cached_input_tokens": 0,
        "requested_max_output_tokens": 2800,
        "output_limit_exceeded": false,
        "stream": true
      }
    },
    {
      "sequence": 7,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-30T16:51:16.370203+00:00",
      "data": {
        "candidate_id": "sms_tfidf_logistic_default",
        "attempt": 0,
        "code_sha256": "bc7d91b43c429a096367830f391b0f80f4003ece9a0c2605d8e40a974e4c0405"
      }
    },
    {
      "sequence": 8,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-30T16:51:17.655452+00:00",
      "data": {
        "candidate_id": "sms_tfidf_logistic_default",
        "attempt": 0,
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
      "sequence": 9,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-30T16:51:18.038241+00:00",
      "data": {
        "candidate_id": "sms_tfidf_nb_default",
        "algorithm": "nb",
        "variant": "default",
        "rationale": "使用训练集拟合 TF-IDF 后接 ComplementNB；该估计器支持非负 TF-IDF 特征，适合纳入短信文本基线，并按同一协议以 average precision 验证。",
        "evidence_ids": [
          "text-tfidf",
          "complement-naive-bayes",
          "sms-grouped-split",
          "average-precision"
        ],
        "parent_id": null
      }
    },
    {
      "sequence": 10,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-30T16:51:57.628867+00:00",
      "data": {
        "role": "coder",
        "requested_model": "gpt-5.5",
        "returned_model": "gpt-5.5",
        "endpoint": "https://sub2api.luciferai.cc/v1",
        "response_id": "resp_08de82b11e485042016abd3e162a0887d18b534c1696dcf88e",
        "prompt_sha256": "6118eda4fdd1b1ac3df420ca95998e57287474ba9d03ef1123bcd6008095d83a",
        "response_sha256": "bb474521bc2bb15c4c0e6f44f41dfb5adbeb4d0bcbe82f33724c36f62927358f",
        "seconds": 39.277,
        "finish_reason": "completed",
        "api": "responses",
        "usage_available": true,
        "input_tokens": 9671,
        "output_tokens": 330,
        "cached_input_tokens": 0,
        "requested_max_output_tokens": 2800,
        "output_limit_exceeded": false,
        "stream": true
      }
    },
    {
      "sequence": 11,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-30T16:51:57.948729+00:00",
      "data": {
        "candidate_id": "sms_tfidf_nb_default",
        "attempt": 0,
        "code_sha256": "54cbd5421bb1f5f5057e24b805659985a27534d986a481847c631835b70391e1"
      }
    },
    {
      "sequence": 12,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-30T16:51:59.041370+00:00",
      "data": {
        "candidate_id": "sms_tfidf_nb_default",
        "attempt": 0,
        "status": "passed",
        "metrics": {
          "average_precision": 0.9598341674027927,
          "roc_auc": 0.9837406749250989,
          "f1_threshold_0_5": 0.9147286821705426,
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
          "ap_improvement_over_dummy": 0.8348341674027927
        },
        "error": null
      }
    },
    {
      "sequence": 13,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-30T16:52:45.970605+00:00",
      "data": {
        "role": "curator",
        "requested_model": "gpt-5.5",
        "returned_model": "gpt-5.5",
        "endpoint": "https://sub2api.luciferai.cc/v1",
        "response_id": "resp_03f20fe0bddf8bcf016abd3e328e5087d18610d4c8162b1cb7",
        "prompt_sha256": "97ab07dad2dbde095a2f5dc4225ba0e45275bc7bf55225b5c01ca3242f44e1d0",
        "response_sha256": "785479e5f83f825bde20d4a659d8c50573e22322726e383d336debc8cab285ca",
        "seconds": 46.59,
        "finish_reason": "completed",
        "api": "responses",
        "usage_available": true,
        "input_tokens": 848,
        "output_tokens": 689,
        "cached_input_tokens": 0,
        "requested_max_output_tokens": 1300,
        "output_limit_exceeded": false,
        "stream": true
      }
    },
    {
      "sequence": 14,
      "event_type": "COMPARED",
      "type": "COMPARED",
      "created_at": "2026-09-30T16:52:46.644115+00:00",
      "data": {
        "selected_candidate_id": "sms_tfidf_nb_default"
      }
    },
    {
      "sequence": 15,
      "event_type": "RECORDED",
      "type": "RECORDED",
      "created_at": "2026-09-30T16:52:47.205323+00:00",
      "data": {
        "intended_status": "passed",
        "experiences": 0
      }
    }
  ],
  "usage": {
    "calls": 5,
    "input_tokens": 29902,
    "output_tokens": 2921,
    "cached_input_tokens": 0,
    "records": [
      {
        "role": "interpreter",
        "requested_model": "gpt-5.5",
        "returned_model": "gpt-5.5",
        "endpoint": "https://sub2api.luciferai.cc/v1",
        "response_id": "resp_0e67268ee1c99759016abd3d89f1b087d1b9d2f7cb4af67772",
        "prompt_sha256": "de3bc6bfe87cb223fa6983cb6eff48787b436b6a08a25fd19ecc216e2e93c534",
        "response_sha256": "ae9b8561a99a63d4147561c83957e8e8943c1afc01ec1d85bb2356fa7a00f1e8",
        "seconds": 64.976,
        "finish_reason": "completed",
        "api": "responses",
        "usage_available": true,
        "input_tokens": 738,
        "output_tokens": 1070,
        "cached_input_tokens": 0,
        "requested_max_output_tokens": 1300,
        "output_limit_exceeded": false,
        "stream": true
      },
      {
        "role": "planner",
        "requested_model": "gpt-5.5",
        "returned_model": "gpt-5.5",
        "endpoint": "https://sub2api.luciferai.cc/v1",
        "response_id": "resp_0b10e1a959ee500b016abd3dcce99887d2949e64f705de2d42",
        "prompt_sha256": "f5eda84074da411d6d5a196e375d51df6632a7777c012f144a1b31ade48d27ca",
        "response_sha256": "2203d8585de6e21ecab440ac66d4703bc6817874bf470e66e92816abda54e035",
        "seconds": 26.12,
        "finish_reason": "completed",
        "api": "responses",
        "usage_available": true,
        "input_tokens": 8974,
        "output_tokens": 362,
        "cached_input_tokens": 0,
        "requested_max_output_tokens": 2200,
        "output_limit_exceeded": false,
        "stream": true
      },
      {
        "role": "coder",
        "requested_model": "gpt-5.5",
        "returned_model": "gpt-5.5",
        "endpoint": "https://sub2api.luciferai.cc/v1",
        "response_id": "resp_0204b14f3b764134016abd3de6b84487d28e0694fc642b6e89",
        "prompt_sha256": "a7929071035f6539132e0ac35421a3f55fa9616a890ca4a7558986e9f3efa6e9",
        "response_sha256": "72ee2116d2979b584af06e22585949eee4deb58cf2bec5f6b348330fd2634e59",
        "seconds": 31.183,
        "finish_reason": "completed",
        "api": "responses",
        "usage_available": true,
        "input_tokens": 9671,
        "output_tokens": 470,
        "cached_input_tokens": 0,
        "requested_max_output_tokens": 2800,
        "output_limit_exceeded": false,
        "stream": true
      },
      {
        "role": "coder",
        "requested_model": "gpt-5.5",
        "returned_model": "gpt-5.5",
        "endpoint": "https://sub2api.luciferai.cc/v1",
        "response_id": "resp_08de82b11e485042016abd3e162a0887d18b534c1696dcf88e",
        "prompt_sha256": "6118eda4fdd1b1ac3df420ca95998e57287474ba9d03ef1123bcd6008095d83a",
        "response_sha256": "bb474521bc2bb15c4c0e6f44f41dfb5adbeb4d0bcbe82f33724c36f62927358f",
        "seconds": 39.277,
        "finish_reason": "completed",
        "api": "responses",
        "usage_available": true,
        "input_tokens": 9671,
        "output_tokens": 330,
        "cached_input_tokens": 0,
        "requested_max_output_tokens": 2800,
        "output_limit_exceeded": false,
        "stream": true
      },
      {
        "role": "curator",
        "requested_model": "gpt-5.5",
        "returned_model": "gpt-5.5",
        "endpoint": "https://sub2api.luciferai.cc/v1",
        "response_id": "resp_03f20fe0bddf8bcf016abd3e328e5087d18610d4c8162b1cb7",
        "prompt_sha256": "97ab07dad2dbde095a2f5dc4225ba0e45275bc7bf55225b5c01ca3242f44e1d0",
        "response_sha256": "785479e5f83f825bde20d4a659d8c50573e22322726e383d336debc8cab285ca",
        "seconds": 46.59,
        "finish_reason": "completed",
        "api": "responses",
        "usage_available": true,
        "input_tokens": 848,
        "output_tokens": 689,
        "cached_input_tokens": 0,
        "requested_max_output_tokens": 1300,
        "output_limit_exceeded": false,
        "stream": true
      }
    ]
  },
  "warnings": [
    "指标来自 validation_only，封存测试集保持未评分。",
    "执行器采用受限 AST 构造器和资源限制子进程；生产隔离需要强化运行时。",
    "数据字段中没有client ID，因此不能承诺按客户端进行独立分离或客户端级泛化验证；只能执行task_spec指定的normalized_group_split_v1协议。",
    "描述未指定独立的输出文件路径、格式或持久化介质，结果保存要求需要由实现选择并记录。",
    "任务规格给出了120秒超时上限，但用户描述本身未明确提出一个新的整体墙钟预算，因此不将其转写为requested_run_seconds。",
    "若数据规模或协议实现导致资源不足，应在资源分析中如实记录，不能通过改变数据协议、标签或评估指标规避限制。",
    "Portable historical evidence export. Original mode, statuses, failed attempts, metrics, usage records, and content hashes are preserved. Project-root absolute paths in JSON are made repository-relative. Datasets, predictions, raw LLM requests/responses, worker logs, credentials, and the private database are omitted. This is not a new execution or a replay-mode relabel. Real gpt-5.5 Responses API through an operator-configured compatible service, using LangChain role chains and typed capability retrieval. Two SMS candidates are independently validated; the sealed test set is unscored. Reported token usage is preserved, including any upstream excess over a requested per-call limit."
  ],
  "search_tree": [
    {
      "candidate_id": "sms_tfidf_logistic_default",
      "parent_id": null,
      "status": "passed",
      "average_precision": 0.9583895772337544,
      "pruned": false,
      "pruned_reason": null
    },
    {
      "candidate_id": "sms_tfidf_nb_default",
      "parent_id": null,
      "status": "passed",
      "average_precision": 0.9598341674027927,
      "pruned": false,
      "pruned_reason": null
    }
  ],
  "knowledge_writeback": {
    "run_saved": true,
    "experiences": []
  },
  "provider_metadata": {
    "provider": "openai",
    "model": "gpt-5.5",
    "base_url": "https://sub2api.luciferai.cc/v1",
    "base_urls": [
      "https://sub2api.luciferai.cc/v1"
    ],
    "authorization": "bearer",
    "deployment": "openai_compatible_api",
    "api": "responses",
    "sdk": "openai",
    "store": false,
    "stream": true,
    "proxy_configured": true,
    "reasoning_effort": "none"
  },
  "data_summary": {
    "train_rows": 3095,
    "validation_rows": 1032
  },
  "interpretation": {
    "objective": "在短信文本二分类任务上，使用TF-IDF特征分别训练逻辑回归和朴素贝叶斯模型，按固定的normalized_group_split_v1数据协议进行独立验证，以average_precision为主要比较指标，并输出可运行代码、验证指标、算法知识依据、资源分析及验证结果保存内容。",
    "constraints": [
      "仅使用sms数据集中的text字段；无数值特征或其他特征可用。",
      "正类标签固定为spam，任务类型为文本二分类。",
      "验证必须遵循不可变的normalized_group_split_v1协议，随机种子为42。",
      "比较的算法限定为TF-IDF逻辑回归和朴素贝叶斯。",
      "主要评估指标固定为average_precision；如输出其他指标，不得替代该主要指标。",
      "资源上限为2个CPU、2048 MiB内存，任务规格中的超时上限为120秒。",
      "应提供可运行代码、验证指标、知识依据、资源分析，并保存验证结果。"
    ],
    "assumptions": [
      "TF-IDF向量化和模型训练均可基于现有text字段完成，且不引入数据集之外的特征。",
      "朴素贝叶斯的具体变体应选择适用于非负TF-IDF特征且受支持的实现；若实现要求整数计数，则需采用兼容TF-IDF的受支持变体或明确调整特征表示。",
      "保存结果所需的具体文件格式和路径未给出，应采用运行环境允许的明确、可审计位置，并在代码中说明。",
      "知识依据可限于TF-IDF、逻辑回归、朴素贝叶斯及average_precision的通用方法原理；当前未提供外部检索证据或仓库证据。"
    ],
    "warnings": [
      "数据字段中没有client ID，因此不能承诺按客户端进行独立分离或客户端级泛化验证；只能执行task_spec指定的normalized_group_split_v1协议。",
      "描述未指定独立的输出文件路径、格式或持久化介质，结果保存要求需要由实现选择并记录。",
      "任务规格给出了120秒超时上限，但用户描述本身未明确提出一个新的整体墙钟预算，因此不将其转写为requested_run_seconds。",
      "若数据规模或协议实现导致资源不足，应在资源分析中如实记录，不能通过改变数据协议、标签或评估指标规避限制。"
    ],
    "incompatible_requests": [],
    "requested_run_seconds": null
  },
  "evidence": [
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
            "path": ".venv/lib/python3.10/site-packages/sklearn/naive_bayes.py",
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
      "score": 3.387706,
      "lexical_score": 2.363516,
      "graph_score": 1.02419,
      "evidence_path": [
        {
          "seed": "capability:text-tfidf:v2",
          "hops": [
            {
              "from": "capability:text-tfidf:v2",
              "relation": "REQUIRES",
              "to": "capability:complement-naive-bayes:v1"
            }
          ],
          "bonus": 0.7353160240144463
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
          "bonus": 0.28887415229138963
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
          "path": ".venv/lib/python3.10/site-packages/sklearn/naive_bayes.py",
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
      "capability_id": "text-tfidf",
      "confidence": 1.0,
      "created_at": "2026-09-29T15:08:50.633076+00:00",
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
            "path": ".venv/lib/python3.10/site-packages/sklearn/feature_extraction/text.py",
            "relative_path": "sklearn/feature_extraction/text.py",
            "signature": "class TfidfVectorizer(CountVectorizer):\n    def __init__(self, *, input='content', encoding='utf-8', decode_error='strict', strip_accents=None, lowercase=True, preprocessor=None, tokenizer=None, analyzer='word', stop_words=None, token_pattern='(?u)\\\\b\\\\w\\\\w+\\\\b', ngram_range=(1, 1), max_df=1.0, min_df=1, max_features=None, vocabulary=None, binary=False, dtype=np.float64, norm='l2', use_idf=True, smooth_idf=True, sublinear_tf=False)",
            "symbol": "TfidfVectorizer"
          },
          "revision": "1.7.2",
          "source_id": "src-ecb336a2fa483eb3b4f26d0b",
          "uri": "https://github.com/scikit-learn/scikit-learn/blob/1.7.2/sklearn/feature_extraction/text.py"
        },
        {
          "content_sha256": "aaebabc27eb0a531bce7f81b5dfb7eefe0e4b635935b5a2063c8ac8eb3c10a23",
          "license": "original-project-notes",
          "locator": {
            "line_end": 62,
            "line_start": 51,
            "path": "docs/02_数据与知识来源.md"
          },
          "revision": "sha256:aaebabc27eb0a531bce7f81b5dfb7eefe0e4b635935b5a2063c8ac8eb3c10a23",
          "source_id": "src-b78d3450109d520074cd321f",
          "uri": "file://docs/02_%E6%95%B0%E6%8D%AE%E4%B8%8E%E7%9F%A5%E8%AF%86%E6%9D%A5%E6%BA%90.md"
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
      "version": 2,
      "score": 3.361445,
      "lexical_score": 1.83829,
      "graph_score": 1.523155,
      "evidence_path": [
        {
          "seed": "capability:complement-naive-bayes:v1",
          "hops": [
            {
              "from": "capability:complement-naive-bayes:v1",
              "relation": "REQUIRES",
              "to": "capability:text-tfidf:v2"
            }
          ],
          "bonus": 0.9454063165900024
        },
        {
          "seed": "capability:probability-logistic:v1",
          "hops": [
            {
              "from": "capability:probability-logistic:v1",
              "relation": "REQUIRES",
              "to": "capability:text-tfidf:v2"
            }
          ],
          "bonus": 0.5777483045827793
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
          "path": ".venv/lib/python3.10/site-packages/sklearn/feature_extraction/text.py",
          "relative_path": "sklearn/feature_extraction/text.py",
          "signature": "class TfidfVectorizer(CountVectorizer):\n    def __init__(self, *, input='content', encoding='utf-8', decode_error='strict', strip_accents=None, lowercase=True, preprocessor=None, tokenizer=None, analyzer='word', stop_words=None, token_pattern='(?u)\\\\b\\\\w\\\\w+\\\\b', ngram_range=(1, 1), max_df=1.0, min_df=1, max_features=None, vocabulary=None, binary=False, dtype=np.float64, norm='l2', use_idf=True, smooth_idf=True, sublinear_tf=False)",
          "symbol": "TfidfVectorizer"
        },
        {
          "line_end": 62,
          "line_start": 51,
          "path": "docs/02_数据与知识来源.md"
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
            "path": ".venv/lib/python3.10/site-packages/sklearn/linear_model/_logistic.py",
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
      "score": 2.65239,
      "lexical_score": 1.444371,
      "graph_score": 1.208019,
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
          "bonus": 0.4727031582950012
        },
        {
          "seed": "capability:text-tfidf:v2",
          "hops": [
            {
              "from": "capability:text-tfidf:v2",
              "relation": "REQUIRES",
              "to": "capability:probability-logistic:v1"
            }
          ],
          "bonus": 0.7353160240144463
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
          "path": ".venv/lib/python3.10/site-packages/sklearn/linear_model/_logistic.py",
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
            "path": ".venv/lib/python3.10/site-packages/sklearn/metrics/_ranking.py",
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
      "score": 2.547345,
      "lexical_score": 0.656532,
      "graph_score": 1.890813,
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
          "bonus": 0.9454063165900024
        },
        {
          "seed": "capability:text-tfidf:v2",
          "hops": [
            {
              "from": "capability:text-tfidf:v2",
              "relation": "REQUIRES",
              "to": "capability:complement-naive-bayes:v1"
            },
            {
              "from": "capability:complement-naive-bayes:v1",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            }
          ],
          "bonus": 0.36765801200722315
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
          "bonus": 0.5777483045827793
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
          "path": ".venv/lib/python3.10/site-packages/sklearn/metrics/_ranking.py",
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
      "created_at": "2026-09-29T15:08:50.632206+00:00",
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
            "path": "data/raw/sms-readme.txt"
          },
          "revision": "sha256:8753cd2d3cab68f80c8257851b8c2037778c267f55accb6fd1b5a2e32d36a84e",
          "source_id": "src-4f8bdb3589548b6b90312e82",
          "uri": "https://archive.ics.uci.edu/dataset/228/sms+spam+collection"
        },
        {
          "content_sha256": "aaebabc27eb0a531bce7f81b5dfb7eefe0e4b635935b5a2063c8ac8eb3c10a23",
          "license": "original-project-notes",
          "locator": {
            "line_end": 62,
            "line_start": 51,
            "path": "docs/02_数据与知识来源.md"
          },
          "revision": "sha256:aaebabc27eb0a531bce7f81b5dfb7eefe0e4b635935b5a2063c8ac8eb3c10a23",
          "source_id": "src-b78d3450109d520074cd321f",
          "uri": "file://docs/02_%E6%95%B0%E6%8D%AE%E4%B8%8E%E7%9F%A5%E8%AF%86%E6%9D%A5%E6%BA%90.md"
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
      "version": 2,
      "score": 2.153425,
      "lexical_score": 0.656532,
      "graph_score": 1.496893,
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
              "to": "capability:sms-format:v2"
            }
          ],
          "bonus": 0.4727031582950012
        },
        {
          "seed": "capability:text-tfidf:v2",
          "hops": [
            {
              "from": "capability:text-tfidf:v2",
              "relation": "REQUIRES",
              "to": "capability:sms-format:v2"
            }
          ],
          "bonus": 0.7353160240144463
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
              "to": "capability:sms-format:v2"
            }
          ],
          "bonus": 0.28887415229138963
        }
      ],
      "graph_used": true,
      "source_locator": [
        {
          "line_end": 31,
          "line_start": 28,
          "path": "data/raw/sms-readme.txt"
        },
        {
          "line_end": 62,
          "line_start": 51,
          "path": "docs/02_数据与知识来源.md"
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
      "created_at": "2026-09-29T15:08:50.632337+00:00",
      "dependencies": [
        "Python >=3.10",
        "scikit-learn"
      ],
      "evidence": [
        {
          "content_sha256": "aaebabc27eb0a531bce7f81b5dfb7eefe0e4b635935b5a2063c8ac8eb3c10a23",
          "license": "original-project-notes",
          "locator": {
            "line_end": 62,
            "line_start": 51,
            "path": "docs/02_数据与知识来源.md"
          },
          "revision": "sha256:aaebabc27eb0a531bce7f81b5dfb7eefe0e4b635935b5a2063c8ac8eb3c10a23",
          "source_id": "src-b78d3450109d520074cd321f",
          "uri": "file://docs/02_%E6%95%B0%E6%8D%AE%E4%B8%8E%E7%9F%A5%E8%AF%86%E6%9D%A5%E6%BA%90.md"
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
      "version": 2,
      "score": 2.022119,
      "lexical_score": 0.525226,
      "graph_score": 1.496893,
      "evidence_path": [
        {
          "seed": "capability:complement-naive-bayes:v1",
          "hops": [
            {
              "from": "capability:complement-naive-bayes:v1",
              "relation": "REQUIRES",
              "to": "capability:text-tfidf:v2"
            },
            {
              "from": "capability:text-tfidf:v2",
              "relation": "REQUIRES",
              "to": "capability:sms-grouped-split:v2"
            }
          ],
          "bonus": 0.4727031582950012
        },
        {
          "seed": "capability:text-tfidf:v2",
          "hops": [
            {
              "from": "capability:text-tfidf:v2",
              "relation": "REQUIRES",
              "to": "capability:sms-grouped-split:v2"
            }
          ],
          "bonus": 0.7353160240144463
        },
        {
          "seed": "capability:probability-logistic:v1",
          "hops": [
            {
              "from": "capability:probability-logistic:v1",
              "relation": "REQUIRES",
              "to": "capability:text-tfidf:v2"
            },
            {
              "from": "capability:text-tfidf:v2",
              "relation": "REQUIRES",
              "to": "capability:sms-grouped-split:v2"
            }
          ],
          "bonus": 0.28887415229138963
        }
      ],
      "graph_used": true,
      "source_locator": [
        {
          "line_end": 62,
          "line_start": 51,
          "path": "docs/02_数据与知识来源.md"
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
    "summary": "在 validation_only 协议下，候选 sms_tfidf_nb_default 与 sms_tfidf_logistic_default 均通过；前者被选中。sms_tfidf_nb_default 的平均精确率为 0.959834、F1 为 0.914729、10%目标集精确率为 1.0、lift 为 8.0、召回率为 0.806202；sms_tfidf_logistic_default 的对应值为 0.958390、0.805556、0.990385、7.923077、0.798450。logistic 候选的 ROC AUC 较高（0.988059 对 0.983741），因此选择结论主要由平均精确率、F1 及 top-10% 指标支持。相关能力证据包括 complement-naive-bayes、text-tfidf、probability-logistic、average-precision、sms-format 和 sms-grouped-split。",
    "limitations": [
      "所有指标均使用 validation-only 协议；sealed test set 保持独立，且两个候选的 sealed_test_scored 均为 false。",
      "比较仅覆盖已提供的两个通过候选，未提供失败候选结果；排序并列时使用原始验证行顺序，结果可能受该规则影响。",
      "受约束的 AST runner 具有已定义的执行范围；本摘要不扩展到该范围之外的能力或未提供的算法。",
      "模型选择不构成因果营销增量的证明，还不能据此断言真实营销 uplift。"
    ]
  },
  "optimization": {
    "schema_version": "1.0",
    "analysis_version": "pareto-observations-v1",
    "run_id": "660682f3cf324bf1938b78c70f2fce8c",
    "scope": "within_run_validation_observations",
    "objectives": {
      "average_precision": "maximize",
      "fit_seconds": "minimize",
      "peak_rss_mib": "minimize"
    },
    "selected_candidate_id": "sms_tfidf_nb_default",
    "selection_policy": "validation_ap_desc_then_candidate_wall_seconds_asc",
    "frontier_candidate_ids": [
      "sms_tfidf_nb_default",
      "sms_tfidf_logistic_default"
    ],
    "candidates": [
      {
        "candidate_id": "sms_tfidf_nb_default",
        "average_precision": 0.9598341674027927,
        "fit_seconds": 0.06966879102401435,
        "peak_rss_mib": 267.8984375,
        "parent_id": null,
        "predict_seconds": 0.012536511989310384,
        "dominated_by": [],
        "pareto_optimal": true
      },
      {
        "candidate_id": "sms_tfidf_logistic_default",
        "average_precision": 0.9583895772337544,
        "fit_seconds": 0.10893881996162236,
        "peak_rss_mib": 265.8984375,
        "parent_id": null,
        "predict_seconds": 0.013013828080147505,
        "dominated_by": [],
        "pareto_optimal": true
      }
    ],
    "excluded": [],
    "parent_child_changes": [],
    "measurement_repetitions": 1,
    "limitations": [
      "同次运行的验证集 AP、训练耗时和 worker 峰值 RSS 观测，不能跨任务混排。",
      "单次耗时受负载与测量噪声影响，不代表稳定加速或统计显著性。",
      "Pareto 分析提供资源权衡依据，不改变原有 AP 优先选择规则。",
      "worker RSS 不含 LLM 服务显存；封存测试集没有用于优化。"
    ]
  },
  "finished_at": "2026-09-30T16:52:47.037991+00:00",
  "timing": {
    "wall_seconds": 216.725,
    "budget_seconds": 900,
    "request_ceiling_seconds": 900
  },
  "report_paths": {},
  "evidence_export": {
    "schema_version": "1.0",
    "source_report": "artifacts/runs/660682f3cf324bf1938b78c70f2fce8c/report.json",
    "source_report_sha256": "1437eb513204f71be74162e45fd821f727898a7c0cbf3d59020d9b34ea6d1c9e",
    "exported_at": "2026-09-30T16:59:22.345660+00:00",
    "note": "Portable historical evidence export. Original mode, statuses, failed attempts, metrics, usage records, and content hashes are preserved. Project-root absolute paths in JSON are made repository-relative. Datasets, predictions, raw LLM requests/responses, worker logs, credentials, and the private database are omitted. This is not a new execution or a replay-mode relabel. Real gpt-5.5 Responses API through an operator-configured compatible service, using LangChain role chains and typed capability retrieval. Two SMS candidates are independently validated; the sealed test set is unscored. Reported token usage is preserved, including any upstream excess over a requested per-call limit.",
    "omitted": [
      "datasets",
      "predictions",
      "raw_llm_payloads",
      "worker_logs",
      "credentials",
      "database"
    ]
  }
}
````

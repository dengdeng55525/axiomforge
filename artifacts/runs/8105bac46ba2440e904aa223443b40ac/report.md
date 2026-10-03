# 算法能力验证报告

指标与状态来自原始验证事实；缺失项不填零、不推断通过。

模式由原始报告的 mode 字段说明：mock 为模拟，replay 为历史回放。

````json
{
  "schema_version": "1.0",
  "run_id": "8105bac46ba2440e904aa223443b40ac",
  "status": "passed",
  "mode": "real",
  "provider": "local_http",
  "description": "预测客户是否订购银行定期存款。仅使用通话前可得特征，禁止使用 duration。比较两个算法候选，按验证集 AP 选择方案，并输出功能检查、来源依据、资源消耗和验证报告。",
  "dataset_id": "bank",
  "created_at": "2026-09-29T18:19:52.224572+00:00",
  "request": {
    "description": "预测客户是否订购银行定期存款。仅使用通话前可得特征，禁止使用 duration。比较两个算法候选，按验证集 AP 选择方案，并输出功能检查、来源依据、资源消耗和验证报告。",
    "dataset_id": "bank",
    "provider": "local_http",
    "max_candidates": 6,
    "max_repairs": 2,
    "use_graph": true,
    "use_retrieval": true,
    "orchestration": "multi_role",
    "search": "beam",
    "inject_failure": false,
    "max_seconds": 900
  },
  "task_spec": {
    "task_type": "tabular_binary_classification",
    "dataset_id": "bank",
    "positive_label": "yes",
    "feature_names": [
      "age",
      "job",
      "marital",
      "education",
      "default",
      "housing",
      "loan",
      "pdays",
      "previous",
      "poutcome"
    ],
    "numeric_features": [
      "age",
      "pdays",
      "previous"
    ],
    "categorical_features": [
      "job",
      "marital",
      "education",
      "default",
      "housing",
      "loan",
      "poutcome"
    ],
    "seed": 42,
    "primary_metric": "average_precision",
    "limits": {
      "cpu": 2,
      "memory_mib": 2048,
      "timeout_s": 120
    },
    "feature_policy": "precontact_conservative_v1"
  },
  "model": "coder14",
  "provenance": {
    "prompt_version": "algoforge-roles-v2",
    "sealed_test_scored": false,
    "dataset": {
      "schema_version": "1.0",
      "dataset_id": "uci-bank-additional-full",
      "source_url": "https://archive.ics.uci.edu/dataset/222/bank+marketing",
      "license": "CC BY 4.0",
      "raw_sha256": "74adfc578bf77a7ff4bb1ba4a9f8709d9e3c6907342959c2c8416847e0afb4d8",
      "split_policy": "original_order_60_20_20",
      "split_seed": 42,
      "train_rows": 24712,
      "validation_rows": 8238,
      "sealed_test_rows": 8238,
      "sealed_test_exported": false,
      "sealed_test_scored": false,
      "validation_labels_visible_to_generated_code": false,
      "preprocessing_fit_split": "train_only",
      "feature_policy": "precontact_conservative_v1",
      "feature_names": [
        "age",
        "job",
        "marital",
        "education",
        "default",
        "housing",
        "loan",
        "pdays",
        "previous",
        "poutcome"
      ],
      "numeric_features": [
        "age",
        "pdays",
        "previous"
      ],
      "file_sha256": {
        "train": "860058ef9a7a6869e9c129277967ca5699fdb249202917201da4991a7c2b3a0c",
        "validation_features": "62b188cf7c57553585006e3b20f4364d41cd8f567b04513fcdc3358429c1986a",
        "validation_labels": "8c505a2f2ed47d04c62c6d182097535f09e9ccab901576fc0727acfe5f882816"
      }
    }
  },
  "candidates": [
    {
      "candidate_id": "logistic_default",
      "plan": {
        "candidate_id": "logistic_default",
        "algorithm": "logistic",
        "variant": "default",
        "rationale": "Logistic regression is a standard approach for binary classification tasks and provides a good baseline for comparison.",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "probability-logistic"
        ],
        "parent_id": null
      },
      "status": "passed",
      "metrics": {
        "average_precision": 0.18287735589367637,
        "roc_auc": 0.6131271073705284,
        "f1_threshold_0_5": 0.0,
        "precision_at_10pct": 0.23179611650485438,
        "recall_at_10pct": 0.20942982456140352,
        "lift_at_10pct": 2.0937899207971387,
        "validation_positive_rate": 0.11070648215586307,
        "top_10pct_count": 824,
        "validation_rows": 8238,
        "classification_threshold": 0.5,
        "evaluation_split": "validation_only",
        "sealed_test_scored": false,
        "ranking_tie_break": "original_validation_row_order",
        "dummy_average_precision": 0.11070648215586307,
        "ap_improvement_over_dummy": 0.07217087373781331
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
          "name": "unknown_category",
          "passed": true,
          "mandatory": true,
          "detail": ""
        },
        {
          "name": "missing_numeric",
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
        "worker_pid": 83412,
        "wall_seconds": 1.103536507114768,
        "fit_seconds": 0.08107955218292773,
        "predict_seconds": 0.014607219956815243,
        "worker_wall_seconds": 0.9217199110426009,
        "peak_rss_mib": 225.87890625,
        "cpu_seconds": 1.213759,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 1.8819713110569865
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "bdf0963819478340329993d79c8f13df4a16a8122362ec08526741671a0794a7",
          "code_path": "candidates/logistic_default/attempt_0/model.py",
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
              "name": "unknown_category",
              "passed": true,
              "mandatory": true,
              "detail": ""
            },
            {
              "name": "missing_numeric",
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
            "average_precision": 0.18287735589367637,
            "roc_auc": 0.6131271073705284,
            "f1_threshold_0_5": 0.0,
            "precision_at_10pct": 0.23179611650485438,
            "recall_at_10pct": 0.20942982456140352,
            "lift_at_10pct": 2.0937899207971387,
            "validation_positive_rate": 0.11070648215586307,
            "top_10pct_count": 824,
            "validation_rows": 8238,
            "classification_threshold": 0.5,
            "evaluation_split": "validation_only",
            "sealed_test_scored": false,
            "ranking_tie_break": "original_validation_row_order",
            "dummy_average_precision": 0.11070648215586307,
            "ap_improvement_over_dummy": 0.07217087373781331
          },
          "resources": {
            "limits": {
              "timeout_s": 120.0,
              "memory_mib": 2048,
              "cpu_cores": 2
            },
            "worker_pid": 83412,
            "wall_seconds": 1.103536507114768,
            "fit_seconds": 0.08107955218292773,
            "predict_seconds": 0.014607219956815243,
            "worker_wall_seconds": 0.9217199110426009,
            "peak_rss_mib": 225.87890625,
            "cpu_seconds": 1.213759,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 1.8819713110569865
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
              "ColumnTransformer",
              "Pipeline",
              "SimpleImputer",
              "StandardScaler",
              "OneHotEncoder",
              "LogisticRegression"
            ],
            "constructor_count": 7,
            "source": "independently_parsed_constructor_plan"
          }
        }
      ],
      "artifact_id": "logistic_default",
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
          "ColumnTransformer",
          "Pipeline",
          "SimpleImputer",
          "StandardScaler",
          "OneHotEncoder",
          "LogisticRegression"
        ],
        "constructor_count": 7,
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
      "code_sha256": "bdf0963819478340329993d79c8f13df4a16a8122362ec08526741671a0794a7",
      "code_path": "candidates/logistic_default/attempt_0/model.py",
      "explanation": "The generated code constructs a scikit-learn pipeline suitable for a tabular binary classification task, specifically tailored for the bank marketing dataset. It includes preprocessing steps for both numeric and categorical features, followed by a logistic regression model for prediction."
    },
    {
      "candidate_id": "logistic_balanced",
      "plan": {
        "candidate_id": "logistic_balanced",
        "algorithm": "logistic",
        "variant": "balanced",
        "rationale": "Balancing the class weights can help improve performance on imbalanced datasets by penalizing errors more heavily on the minority class.",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "probability-logistic"
        ],
        "parent_id": null
      },
      "status": "passed",
      "metrics": {
        "average_precision": 0.1807589966629477,
        "roc_auc": 0.6093179752719227,
        "f1_threshold_0_5": 0.22881855710634952,
        "precision_at_10pct": 0.2196601941747573,
        "recall_at_10pct": 0.19846491228070176,
        "lift_at_10pct": 1.9841674118548802,
        "validation_positive_rate": 0.11070648215586307,
        "top_10pct_count": 824,
        "validation_rows": 8238,
        "classification_threshold": 0.5,
        "evaluation_split": "validation_only",
        "sealed_test_scored": false,
        "ranking_tie_break": "original_validation_row_order",
        "dummy_average_precision": 0.11070648215586307,
        "ap_improvement_over_dummy": 0.07005251450708463
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
          "name": "unknown_category",
          "passed": true,
          "mandatory": true,
          "detail": ""
        },
        {
          "name": "missing_numeric",
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
        "worker_pid": 83586,
        "wall_seconds": 1.1532540381886065,
        "fit_seconds": 0.11540229595266283,
        "predict_seconds": 0.014784886967390776,
        "worker_wall_seconds": 0.9568209608551115,
        "peak_rss_mib": 226.87890625,
        "cpu_seconds": 1.279433,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 1.3115560610312968
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "2b09a4a2fc70b67a4cec8229f7d553b7a7f168a8119b6626a38800f9ce5c1eec",
          "code_path": "candidates/logistic_balanced/attempt_0/model.py",
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
              "name": "unknown_category",
              "passed": true,
              "mandatory": true,
              "detail": ""
            },
            {
              "name": "missing_numeric",
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
            "average_precision": 0.1807589966629477,
            "roc_auc": 0.6093179752719227,
            "f1_threshold_0_5": 0.22881855710634952,
            "precision_at_10pct": 0.2196601941747573,
            "recall_at_10pct": 0.19846491228070176,
            "lift_at_10pct": 1.9841674118548802,
            "validation_positive_rate": 0.11070648215586307,
            "top_10pct_count": 824,
            "validation_rows": 8238,
            "classification_threshold": 0.5,
            "evaluation_split": "validation_only",
            "sealed_test_scored": false,
            "ranking_tie_break": "original_validation_row_order",
            "dummy_average_precision": 0.11070648215586307,
            "ap_improvement_over_dummy": 0.07005251450708463
          },
          "resources": {
            "limits": {
              "timeout_s": 120.0,
              "memory_mib": 2048,
              "cpu_cores": 2
            },
            "worker_pid": 83586,
            "wall_seconds": 1.1532540381886065,
            "fit_seconds": 0.11540229595266283,
            "predict_seconds": 0.014784886967390776,
            "worker_wall_seconds": 0.9568209608551115,
            "peak_rss_mib": 226.87890625,
            "cpu_seconds": 1.279433,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 1.3115560610312968
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
              "class_weight": "balanced",
              "random_state": 42
            },
            "constructor_classes": [
              "Pipeline",
              "ColumnTransformer",
              "Pipeline",
              "SimpleImputer",
              "StandardScaler",
              "OneHotEncoder",
              "LogisticRegression"
            ],
            "constructor_count": 7,
            "source": "independently_parsed_constructor_plan"
          }
        }
      ],
      "artifact_id": "logistic_balanced",
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
          "class_weight": "balanced",
          "random_state": 42
        },
        "constructor_classes": [
          "Pipeline",
          "ColumnTransformer",
          "Pipeline",
          "SimpleImputer",
          "StandardScaler",
          "OneHotEncoder",
          "LogisticRegression"
        ],
        "constructor_count": 7,
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
      "code_sha256": "2b09a4a2fc70b67a4cec8229f7d553b7a7f168a8119b6626a38800f9ce5c1eec",
      "code_path": "candidates/logistic_balanced/attempt_0/model.py",
      "explanation": "The generated code creates a scikit-learn pipeline for a tabular binary classification task. It includes preprocessing steps for numeric and categorical features, followed by a logistic regression model with balanced class weights."
    }
  ],
  "selected_candidate_id": "logistic_default",
  "events": [
    {
      "sequence": 0,
      "event_type": "RECEIVED",
      "type": "RECEIVED",
      "created_at": "2026-09-29T18:19:52.374562+00:00",
      "data": {
        "mode": "real",
        "model": "coder14"
      }
    },
    {
      "sequence": 1,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T18:19:55.377395+00:00",
      "data": {
        "role": "interpreter",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8100/v1",
        "response_id": "chatcmpl-8b30dcb39199952a",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "2547b2c9b547549bd1bbeb48e2b0c8a01de5aa3011a3398691bcc584600fe781",
        "response_sha256": "ebcb7672ac5e4dcc4728cfeb8348f0848a3b37affe8f93485ce23bc529a452e5",
        "input_tokens": 487,
        "output_tokens": 116,
        "seconds": 2.335,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 2,
      "event_type": "SPEC_VALIDATED",
      "type": "SPEC_VALIDATED",
      "created_at": "2026-09-29T18:19:55.674729+00:00",
      "data": {
        "task_type": "tabular_binary_classification",
        "assumptions": [
          "使用提供的特征集进行模型训练",
          "比较两个算法候选，按验证集 AP 选择方案"
        ]
      }
    },
    {
      "sequence": 3,
      "event_type": "KNOWLEDGE_RETRIEVED",
      "type": "KNOWLEDGE_RETRIEVED",
      "created_at": "2026-09-29T18:19:56.306746+00:00",
      "data": {
        "count": 6,
        "use_graph": true,
        "capability_ids": [
          "bank-precontact-policy",
          "bank-target",
          "bank-ordered-split",
          "average-precision",
          "probability-logistic",
          "training-only-pipeline"
        ]
      }
    },
    {
      "sequence": 4,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T18:20:00.402750+00:00",
      "data": {
        "role": "planner",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8101/v1",
        "response_id": "chatcmpl-8d6e446960fb5b68",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "45500a6022cf8aad940d98b44fec59008e4a962e381cfe1d919841f4122a7848",
        "response_sha256": "86ed84882f1f93107e803115b29f0fadbb7ab4fada5b01df5912a72f56c17cf6",
        "input_tokens": 9118,
        "output_tokens": 190,
        "seconds": 3.696,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 5,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-29T18:20:00.690136+00:00",
      "data": {
        "candidate_id": "logistic_default",
        "algorithm": "logistic",
        "variant": "default",
        "rationale": "Logistic regression is a standard approach for binary classification tasks and provides a good baseline for comparison.",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "probability-logistic"
        ],
        "parent_id": null
      }
    },
    {
      "sequence": 6,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T18:20:05.777703+00:00",
      "data": {
        "role": "coder",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8102/v1",
        "response_id": "chatcmpl-b90337057449f635",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "876dc716bf29d73a982409daf9491ec02cd49c291dccb476b94d4661a2242793",
        "response_sha256": "ef15933b62f1e779e917f3ee22e6961b110791a57dcfd98cb7f59c932706e54f",
        "input_tokens": 9583,
        "output_tokens": 221,
        "seconds": 4.436,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 7,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-29T18:20:06.103529+00:00",
      "data": {
        "candidate_id": "logistic_default",
        "attempt": 0,
        "code_sha256": "bdf0963819478340329993d79c8f13df4a16a8122362ec08526741671a0794a7"
      }
    },
    {
      "sequence": 8,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-29T18:20:08.379924+00:00",
      "data": {
        "candidate_id": "logistic_default",
        "attempt": 0,
        "status": "passed",
        "metrics": {
          "average_precision": 0.18287735589367637,
          "roc_auc": 0.6131271073705284,
          "f1_threshold_0_5": 0.0,
          "precision_at_10pct": 0.23179611650485438,
          "recall_at_10pct": 0.20942982456140352,
          "lift_at_10pct": 2.0937899207971387,
          "validation_positive_rate": 0.11070648215586307,
          "top_10pct_count": 824,
          "validation_rows": 8238,
          "classification_threshold": 0.5,
          "evaluation_split": "validation_only",
          "sealed_test_scored": false,
          "ranking_tie_break": "original_validation_row_order",
          "dummy_average_precision": 0.11070648215586307,
          "ap_improvement_over_dummy": 0.07217087373781331
        },
        "error": null
      }
    },
    {
      "sequence": 9,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-29T18:20:08.719420+00:00",
      "data": {
        "candidate_id": "logistic_balanced",
        "algorithm": "logistic",
        "variant": "balanced",
        "rationale": "Balancing the class weights can help improve performance on imbalanced datasets by penalizing errors more heavily on the minority class.",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "probability-logistic"
        ],
        "parent_id": null
      }
    },
    {
      "sequence": 10,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T18:20:13.098207+00:00",
      "data": {
        "role": "coder",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8103/v1",
        "response_id": "chatcmpl-a87c593091e67eb9",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "61978845dd7698627653f8248bca084685e17956c91a31252059c02f2309b501",
        "response_sha256": "7bcdff05aee85ed855196f59195da45d1b785a79ef2e22d415261c25ad249ba1",
        "input_tokens": 9589,
        "output_tokens": 218,
        "seconds": 4.174,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 11,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-29T18:20:13.447106+00:00",
      "data": {
        "candidate_id": "logistic_balanced",
        "attempt": 0,
        "code_sha256": "2b09a4a2fc70b67a4cec8229f7d553b7a7f168a8119b6626a38800f9ce5c1eec"
      }
    },
    {
      "sequence": 12,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-29T18:20:15.351162+00:00",
      "data": {
        "candidate_id": "logistic_balanced",
        "attempt": 0,
        "status": "passed",
        "metrics": {
          "average_precision": 0.1807589966629477,
          "roc_auc": 0.6093179752719227,
          "f1_threshold_0_5": 0.22881855710634952,
          "precision_at_10pct": 0.2196601941747573,
          "recall_at_10pct": 0.19846491228070176,
          "lift_at_10pct": 1.9841674118548802,
          "validation_positive_rate": 0.11070648215586307,
          "top_10pct_count": 824,
          "validation_rows": 8238,
          "classification_threshold": 0.5,
          "evaluation_split": "validation_only",
          "sealed_test_scored": false,
          "ranking_tie_break": "original_validation_row_order",
          "dummy_average_precision": 0.11070648215586307,
          "ap_improvement_over_dummy": 0.07005251450708463
        },
        "error": null
      }
    },
    {
      "sequence": 13,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T18:20:19.591207+00:00",
      "data": {
        "role": "planner",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8100/v1",
        "response_id": "chatcmpl-ba04827679ffc529",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "f3d7db430129a55ca5d2c76ab3a1d1201301e96a5e9f40b442fb2363a5617c34",
        "response_sha256": "c2e139fbf3e5a0a77600a3bea488bbd2806b51d7d79a863032644d68b576fbaf",
        "input_tokens": 10339,
        "output_tokens": 189,
        "seconds": 3.829,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 14,
      "event_type": "PLAN_REJECTED",
      "type": "PLAN_REJECTED",
      "created_at": "2026-09-29T18:20:19.824951+00:00",
      "data": {
        "error": "Planner duplicated an ID or algorithm/variant pair"
      }
    },
    {
      "sequence": 15,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T18:20:23.805093+00:00",
      "data": {
        "role": "planner",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8101/v1",
        "response_id": "chatcmpl-b9c73d6d8fe508fe",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "4f0ef2980fbd311806f9ce79e06de782980289c3042a0bf8919b36ef4c79cf49",
        "response_sha256": "92196c5f000edab55de2465655051215e0d6aca2c9c6362007da0f128dc789d8",
        "input_tokens": 10355,
        "output_tokens": 190,
        "seconds": 3.704,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 16,
      "event_type": "PLAN_REJECTED",
      "type": "PLAN_REJECTED",
      "created_at": "2026-09-29T18:20:24.053704+00:00",
      "data": {
        "error": "Planner proposed an incompatible algorithm or variant"
      }
    },
    {
      "sequence": 17,
      "event_type": "BEAM_SKIPPED",
      "type": "BEAM_SKIPPED",
      "created_at": "2026-09-29T18:20:24.316101+00:00",
      "data": {
        "requested_children": 2,
        "reason": "Planner proposed an incompatible algorithm or variant"
      }
    },
    {
      "sequence": 18,
      "event_type": "BEAM_EXPANDED",
      "type": "BEAM_EXPANDED",
      "created_at": "2026-09-29T18:20:24.646294+00:00",
      "data": {
        "beam_width": 2,
        "parents": [
          "logistic_default",
          "logistic_balanced"
        ],
        "children": 0
      }
    },
    {
      "sequence": 19,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T18:20:28.086976+00:00",
      "data": {
        "role": "curator",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8102/v1",
        "response_id": "chatcmpl-8b49511784aee20d",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "f40b7e106edd44d8b5666dea7dd2fd4208b4f16f436d7bb467491eb697f052dc",
        "response_sha256": "0951d3b2b5e74e342836c76ccaee7bd13b167af59966af2008470dd5de3c7f8f",
        "input_tokens": 882,
        "output_tokens": 154,
        "seconds": 3.216,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 20,
      "event_type": "COMPARED",
      "type": "COMPARED",
      "created_at": "2026-09-29T18:20:28.375877+00:00",
      "data": {
        "selected_candidate_id": "logistic_default"
      }
    },
    {
      "sequence": 21,
      "event_type": "RECORDED",
      "type": "RECORDED",
      "created_at": "2026-09-29T18:20:28.746401+00:00",
      "data": {
        "intended_status": "passed",
        "experiences": 0
      }
    }
  ],
  "usage": {
    "calls": 7,
    "input_tokens": 50353,
    "output_tokens": 1278,
    "cached_input_tokens": 0,
    "records": [
      {
        "role": "interpreter",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8100/v1",
        "response_id": "chatcmpl-8b30dcb39199952a",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "2547b2c9b547549bd1bbeb48e2b0c8a01de5aa3011a3398691bcc584600fe781",
        "response_sha256": "ebcb7672ac5e4dcc4728cfeb8348f0848a3b37affe8f93485ce23bc529a452e5",
        "input_tokens": 487,
        "output_tokens": 116,
        "seconds": 2.335,
        "finish_reason": "stop"
      },
      {
        "role": "planner",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8101/v1",
        "response_id": "chatcmpl-8d6e446960fb5b68",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "45500a6022cf8aad940d98b44fec59008e4a962e381cfe1d919841f4122a7848",
        "response_sha256": "86ed84882f1f93107e803115b29f0fadbb7ab4fada5b01df5912a72f56c17cf6",
        "input_tokens": 9118,
        "output_tokens": 190,
        "seconds": 3.696,
        "finish_reason": "stop"
      },
      {
        "role": "coder",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8102/v1",
        "response_id": "chatcmpl-b90337057449f635",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "876dc716bf29d73a982409daf9491ec02cd49c291dccb476b94d4661a2242793",
        "response_sha256": "ef15933b62f1e779e917f3ee22e6961b110791a57dcfd98cb7f59c932706e54f",
        "input_tokens": 9583,
        "output_tokens": 221,
        "seconds": 4.436,
        "finish_reason": "stop"
      },
      {
        "role": "coder",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8103/v1",
        "response_id": "chatcmpl-a87c593091e67eb9",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "61978845dd7698627653f8248bca084685e17956c91a31252059c02f2309b501",
        "response_sha256": "7bcdff05aee85ed855196f59195da45d1b785a79ef2e22d415261c25ad249ba1",
        "input_tokens": 9589,
        "output_tokens": 218,
        "seconds": 4.174,
        "finish_reason": "stop"
      },
      {
        "role": "planner",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8100/v1",
        "response_id": "chatcmpl-ba04827679ffc529",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "f3d7db430129a55ca5d2c76ab3a1d1201301e96a5e9f40b442fb2363a5617c34",
        "response_sha256": "c2e139fbf3e5a0a77600a3bea488bbd2806b51d7d79a863032644d68b576fbaf",
        "input_tokens": 10339,
        "output_tokens": 189,
        "seconds": 3.829,
        "finish_reason": "stop"
      },
      {
        "role": "planner",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8101/v1",
        "response_id": "chatcmpl-b9c73d6d8fe508fe",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "4f0ef2980fbd311806f9ce79e06de782980289c3042a0bf8919b36ef4c79cf49",
        "response_sha256": "92196c5f000edab55de2465655051215e0d6aca2c9c6362007da0f128dc789d8",
        "input_tokens": 10355,
        "output_tokens": 190,
        "seconds": 3.704,
        "finish_reason": "stop"
      },
      {
        "role": "curator",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8102/v1",
        "response_id": "chatcmpl-8b49511784aee20d",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "f40b7e106edd44d8b5666dea7dd2fd4208b4f16f436d7bb467491eb697f052dc",
        "response_sha256": "0951d3b2b5e74e342836c76ccaee7bd13b167af59966af2008470dd5de3c7f8f",
        "input_tokens": 882,
        "output_tokens": 154,
        "seconds": 3.216,
        "finish_reason": "stop"
      }
    ]
  },
  "warnings": [
    "指标来自 validation_only，封存测试集保持未评分。",
    "执行器采用受限 AST 构造器和资源限制子进程；生产隔离需要强化运行时。",
    "请求的特征集不包含 'duration'，因此无法使用该特征进行模型训练",
    "Beam 扩展已跳过，保留已验证候选：Planner proposed an incompatible algorithm or variant"
  ],
  "search_tree": [
    {
      "candidate_id": "logistic_default",
      "parent_id": null,
      "status": "passed",
      "average_precision": 0.18287735589367637,
      "pruned": false,
      "pruned_reason": null
    },
    {
      "candidate_id": "logistic_balanced",
      "parent_id": null,
      "status": "passed",
      "average_precision": 0.1807589966629477,
      "pruned": false,
      "pruned_reason": null
    }
  ],
  "knowledge_writeback": {
    "run_saved": true,
    "experiences": []
  },
  "provider_metadata": {
    "provider": "local_http",
    "model": "coder14",
    "base_url": "http://127.0.0.1:8100/v1",
    "base_urls": [
      "http://127.0.0.1:8100/v1",
      "http://127.0.0.1:8101/v1",
      "http://127.0.0.1:8102/v1",
      "http://127.0.0.1:8103/v1"
    ],
    "authorization": "none",
    "local_profile": "four_gpu_14b",
    "deployment": "external_local_http"
  },
  "data_summary": {
    "train_rows": 24712,
    "validation_rows": 8238
  },
  "interpretation": {
    "objective": "预测客户是否订购银行定期存款。",
    "constraints": [
      "仅使用通话前可得特征",
      "禁止使用 duration"
    ],
    "assumptions": [
      "使用提供的特征集进行模型训练",
      "比较两个算法候选，按验证集 AP 选择方案"
    ],
    "warnings": [
      "请求的特征集不包含 'duration'，因此无法使用该特征进行模型训练"
    ],
    "incompatible_requests": [],
    "requested_run_seconds": null
  },
  "evidence": [
    {
      "capability_id": "bank-precontact-policy",
      "confidence": 1.0,
      "created_at": "2026-09-29T15:08:50.631548+00:00",
      "dependencies": [
        "Python >=3.10",
        "scikit-learn"
      ],
      "evidence": [
        {
          "content_sha256": "10045462a4c026f858dffa159370c4270510230c1fc63c6c91ca51bba4b3df26",
          "license": "CC-BY-4.0",
          "locator": {
            "line_end": 58,
            "line_start": 56,
            "path": "/root/algorithm-capability-factory/data/raw/bank-additional-names.txt"
          },
          "revision": "sha256:10045462a4c026f858dffa159370c4270510230c1fc63c6c91ca51bba4b3df26",
          "source_id": "src-036a9125a071ef6a1ae3c21f",
          "uri": "https://archive.ics.uci.edu/dataset/222/bank+marketing"
        },
        {
          "content_sha256": "aaebabc27eb0a531bce7f81b5dfb7eefe0e4b635935b5a2063c8ac8eb3c10a23",
          "license": "original-project-notes",
          "locator": {
            "line_end": 34,
            "line_start": 18,
            "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
          },
          "revision": "sha256:aaebabc27eb0a531bce7f81b5dfb7eefe0e4b635935b5a2063c8ac8eb3c10a23",
          "source_id": "src-df2a53ac66a4c0255b59ad3b",
          "uri": "file:///root/algorithm-capability-factory/docs/02_%E6%95%B0%E6%8D%AE%E4%B8%8E%E7%9F%A5%E8%AF%86%E6%9D%A5%E6%BA%90.md"
        }
      ],
      "extraction_method": "curated-source-grounded",
      "id": "bank-precontact-policy",
      "input_schema": {
        "task_types": [
          "tabular_binary_classification"
        ],
        "type": "features"
      },
      "name": "银行营销通话前特征与泄漏防护",
      "origin": "manual_seed",
      "output_schema": {
        "type": "implementation-guidance"
      },
      "preconditions": [],
      "related": [
        "bank-target",
        "bank-ordered-split"
      ],
      "status": "extracted",
      "summary": "预测银行客户是否订购定期存款。通话前预测禁止使用 duration：官方字段说明指出通话结束前无法知道时长。主协议使用项目定义的保守字段白名单；它是项目设计约束，不是 UCI 原始数据唯一允许的协议。",
      "tags": [
        "银行",
        "通话前",
        "duration",
        "泄漏",
        "precontact"
      ],
      "task_types": [
        "tabular_binary_classification"
      ],
      "uses": [],
      "version": 2,
      "score": 4.25,
      "lexical_score": 3.25,
      "graph_score": 1.0,
      "evidence_path": [
        {
          "seed": "capability:bank-target:v2",
          "hops": [
            {
              "from": "capability:bank-target:v2",
              "relation": "REQUIRES",
              "to": "capability:bank-precontact-policy:v2"
            }
          ],
          "bonus": 0.6000000000000001
        },
        {
          "seed": "capability:bank-ordered-split:v2",
          "hops": [
            {
              "from": "capability:bank-ordered-split:v2",
              "relation": "REQUIRES",
              "to": "capability:bank-precontact-policy:v2"
            }
          ],
          "bonus": 0.4
        }
      ],
      "graph_used": true,
      "source_locator": [
        {
          "line_end": 58,
          "line_start": 56,
          "path": "/root/algorithm-capability-factory/data/raw/bank-additional-names.txt"
        },
        {
          "line_end": 34,
          "line_start": 18,
          "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
        }
      ],
      "matched_constraints": [
        "task_type=tabular_binary_classification"
      ],
      "rejected_reason": null
    },
    {
      "capability_id": "bank-target",
      "confidence": 1.0,
      "created_at": "2026-09-29T15:08:50.631826+00:00",
      "dependencies": [
        "Python >=3.10",
        "scikit-learn"
      ],
      "evidence": [
        {
          "content_sha256": "10045462a4c026f858dffa159370c4270510230c1fc63c6c91ca51bba4b3df26",
          "license": "CC-BY-4.0",
          "locator": {
            "line_end": 72,
            "line_start": 70,
            "path": "/root/algorithm-capability-factory/data/raw/bank-additional-names.txt"
          },
          "revision": "sha256:10045462a4c026f858dffa159370c4270510230c1fc63c6c91ca51bba4b3df26",
          "source_id": "src-9e74f92e3a9cf01663fecfe4",
          "uri": "https://archive.ics.uci.edu/dataset/222/bank+marketing"
        },
        {
          "content_sha256": "aaebabc27eb0a531bce7f81b5dfb7eefe0e4b635935b5a2063c8ac8eb3c10a23",
          "license": "original-project-notes",
          "locator": {
            "line_end": 34,
            "line_start": 18,
            "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
          },
          "revision": "sha256:aaebabc27eb0a531bce7f81b5dfb7eefe0e4b635935b5a2063c8ac8eb3c10a23",
          "source_id": "src-df2a53ac66a4c0255b59ad3b",
          "uri": "file:///root/algorithm-capability-factory/docs/02_%E6%95%B0%E6%8D%AE%E4%B8%8E%E7%9F%A5%E8%AF%86%E6%9D%A5%E6%BA%90.md"
        }
      ],
      "extraction_method": "curated-source-grounded",
      "id": "bank-target",
      "input_schema": {
        "task_types": [
          "tabular_binary_classification"
        ],
        "type": "features"
      },
      "name": "银行订购响应二分类的正类定义",
      "origin": "manual_seed",
      "output_schema": {
        "type": "implementation-guidance"
      },
      "preconditions": [],
      "related": [
        "probability-logistic",
        "average-precision"
      ],
      "status": "extracted",
      "summary": "UCI Bank Marketing 的 y 表示客户是否订购定期存款，yes 是本项目正类，no 是负类。该标签不是流失、信用违约或营销因果增量。",
      "tags": [
        "y",
        "yes",
        "正类",
        "银行",
        "目标"
      ],
      "task_types": [
        "tabular_binary_classification"
      ],
      "uses": [],
      "version": 2,
      "score": 2.9,
      "lexical_score": 1.5,
      "graph_score": 1.4,
      "evidence_path": [
        {
          "seed": "capability:bank-precontact-policy:v2",
          "hops": [
            {
              "from": "capability:bank-precontact-policy:v2",
              "relation": "REQUIRES",
              "to": "capability:bank-target:v2"
            }
          ],
          "bonus": 1.2000000000000002
        },
        {
          "seed": "capability:bank-ordered-split:v2",
          "hops": [
            {
              "from": "capability:bank-ordered-split:v2",
              "relation": "REQUIRES",
              "to": "capability:bank-precontact-policy:v2"
            },
            {
              "from": "capability:bank-precontact-policy:v2",
              "relation": "REQUIRES",
              "to": "capability:bank-target:v2"
            }
          ],
          "bonus": 0.2
        }
      ],
      "graph_used": true,
      "source_locator": [
        {
          "line_end": 72,
          "line_start": 70,
          "path": "/root/algorithm-capability-factory/data/raw/bank-additional-names.txt"
        },
        {
          "line_end": 34,
          "line_start": 18,
          "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
        }
      ],
      "matched_constraints": [
        "task_type=tabular_binary_classification"
      ],
      "rejected_reason": null
    },
    {
      "capability_id": "bank-ordered-split",
      "confidence": 1.0,
      "created_at": "2026-09-29T15:08:50.632098+00:00",
      "dependencies": [
        "Python >=3.10",
        "scikit-learn"
      ],
      "evidence": [
        {
          "content_sha256": "aaebabc27eb0a531bce7f81b5dfb7eefe0e4b635935b5a2063c8ac8eb3c10a23",
          "license": "original-project-notes",
          "locator": {
            "line_end": 50,
            "line_start": 35,
            "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
          },
          "revision": "sha256:aaebabc27eb0a531bce7f81b5dfb7eefe0e4b635935b5a2063c8ac8eb3c10a23",
          "source_id": "src-a12ccd822a93af321f34ad70",
          "uri": "file:///root/algorithm-capability-factory/docs/02_%E6%95%B0%E6%8D%AE%E4%B8%8E%E7%9F%A5%E8%AF%86%E6%9D%A5%E6%BA%90.md"
        }
      ],
      "extraction_method": "curated-source-grounded",
      "id": "bank-ordered-split",
      "input_schema": {
        "task_types": [
          "tabular_binary_classification"
        ],
        "type": "features"
      },
      "name": "银行原始顺序留出与测试封存",
      "origin": "manual_seed",
      "output_schema": {
        "type": "implementation-guidance"
      },
      "preconditions": [],
      "related": [
        "training-only-pipeline"
      ],
      "status": "extracted",
      "summary": "本项目主协议按原始行位置作 60/20/20 顺序划分。训练和验证可用于候选选择；最终测试在代码、提示词和阈值冻结后使用。CSV 没有完整时间戳或可靠客户 ID，不声称精确日期边界或客户级隔离。",
      "tags": [
        "顺序",
        "切分",
        "测试",
        "泄漏",
        "ordered",
        "split"
      ],
      "task_types": [
        "tabular_binary_classification"
      ],
      "uses": [],
      "version": 2,
      "score": 2.5,
      "lexical_score": 1.0,
      "graph_score": 1.5,
      "evidence_path": [
        {
          "seed": "capability:bank-precontact-policy:v2",
          "hops": [
            {
              "from": "capability:bank-precontact-policy:v2",
              "relation": "REQUIRES",
              "to": "capability:bank-ordered-split:v2"
            }
          ],
          "bonus": 1.2000000000000002
        },
        {
          "seed": "capability:bank-target:v2",
          "hops": [
            {
              "from": "capability:bank-target:v2",
              "relation": "REQUIRES",
              "to": "capability:bank-precontact-policy:v2"
            },
            {
              "from": "capability:bank-precontact-policy:v2",
              "relation": "REQUIRES",
              "to": "capability:bank-ordered-split:v2"
            }
          ],
          "bonus": 0.30000000000000004
        }
      ],
      "graph_used": true,
      "source_locator": [
        {
          "line_end": 50,
          "line_start": 35,
          "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
        }
      ],
      "matched_constraints": [
        "task_type=tabular_binary_classification"
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
      "score": 1.95,
      "lexical_score": 0.75,
      "graph_score": 1.2,
      "evidence_path": [
        {
          "seed": "capability:bank-precontact-policy:v2",
          "hops": [
            {
              "from": "capability:bank-precontact-policy:v2",
              "relation": "REQUIRES",
              "to": "capability:bank-target:v2"
            },
            {
              "from": "capability:bank-target:v2",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            }
          ],
          "bonus": 0.6000000000000001
        },
        {
          "seed": "capability:bank-target:v2",
          "hops": [
            {
              "from": "capability:bank-target:v2",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            }
          ],
          "bonus": 0.6000000000000001
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
        "task_type=tabular_binary_classification"
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
      "score": 1.65,
      "lexical_score": 0.25,
      "graph_score": 1.4,
      "evidence_path": [
        {
          "seed": "capability:bank-precontact-policy:v2",
          "hops": [
            {
              "from": "capability:bank-precontact-policy:v2",
              "relation": "REQUIRES",
              "to": "capability:bank-target:v2"
            },
            {
              "from": "capability:bank-target:v2",
              "relation": "REQUIRES",
              "to": "capability:probability-logistic:v1"
            }
          ],
          "bonus": 0.6000000000000001
        },
        {
          "seed": "capability:bank-target:v2",
          "hops": [
            {
              "from": "capability:bank-target:v2",
              "relation": "REQUIRES",
              "to": "capability:probability-logistic:v1"
            }
          ],
          "bonus": 0.6000000000000001
        },
        {
          "seed": "capability:bank-ordered-split:v2",
          "hops": [
            {
              "from": "capability:bank-ordered-split:v2",
              "relation": "REQUIRES",
              "to": "capability:training-only-pipeline:v2"
            },
            {
              "from": "capability:training-only-pipeline:v2",
              "relation": "REQUIRES",
              "to": "capability:probability-logistic:v1"
            }
          ],
          "bonus": 0.2
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
        "task_type=tabular_binary_classification"
      ],
      "rejected_reason": null
    },
    {
      "capability_id": "training-only-pipeline",
      "confidence": 1.0,
      "created_at": "2026-09-29T15:08:50.632611+00:00",
      "dependencies": [
        "Python >=3.10",
        "scikit-learn"
      ],
      "evidence": [
        {
          "content_sha256": "06f7ccb74a31ab9d3c900d87c814b7ce81b8acbd938ad74fe9cc674075f07869",
          "license": "BSD-3-Clause",
          "locator": {
            "imports": [
              "import warnings",
              "from collections import Counter, defaultdict",
              "from contextlib import contextmanager",
              "from copy import deepcopy",
              "from itertools import chain, islice",
              "import numpy as np",
              "from scipy import sparse",
              "from .base import TransformerMixin, _fit_context, clone",
              "from .exceptions import NotFittedError",
              "from .preprocessing import FunctionTransformer",
              "from .utils import Bunch",
              "from .utils._metadata_requests import METHODS",
              "from .utils._param_validation import HasMethods, Hidden",
              "from .utils._repr_html.estimator import _VisualBlock",
              "from .utils._set_output import _get_container_adapter, _safe_set_output",
              "from .utils._tags import get_tags",
              "from .utils._user_interface import _print_elapsed_time",
              "from .utils.metadata_routing import MetadataRouter, MethodMapping, _raise_for_params, _routing_enabled, get_routing_for_object, process_routing",
              "from .utils.metaestimators import _BaseComposition, available_if",
              "from .utils.parallel import Parallel, delayed",
              "from .utils.validation import check_is_fitted, check_memory"
            ],
            "line_end": 1407,
            "line_start": 123,
            "methods": [
              "__init__",
              "set_output",
              "get_params",
              "set_params",
              "_validate_steps",
              "_iter",
              "__len__",
              "__getitem__",
              "_estimator_type",
              "named_steps",
              "_final_estimator",
              "_log_message",
              "_check_method_params",
              "_get_metadata_for_step",
              "_fit",
              "fit",
              "_can_fit_transform",
              "fit_transform",
              "predict",
              "fit_predict",
              "predict_proba",
              "decision_function",
              "score_samples",
              "predict_log_proba",
              "_can_transform",
              "transform",
              "_can_inverse_transform",
              "inverse_transform",
              "score",
              "classes_",
              "__sklearn_tags__",
              "get_feature_names_out",
              "n_features_in_",
              "feature_names_in_",
              "__sklearn_is_fitted__",
              "_sk_visual_block_",
              "get_metadata_routing"
            ],
            "parse_mode": "ast-only",
            "path": "/root/algorithm-capability-factory/.venv/lib/python3.10/site-packages/sklearn/pipeline.py",
            "relative_path": "sklearn/pipeline.py",
            "signature": "class Pipeline(_BaseComposition):\n    def __init__(self, steps, *, transform_input=None, memory=None, verbose=False)",
            "symbol": "Pipeline"
          },
          "revision": "1.7.2",
          "source_id": "src-8a2d3c4ad618f98dc3d974e1",
          "uri": "https://github.com/scikit-learn/scikit-learn/blob/1.7.2/sklearn/pipeline.py"
        },
        {
          "content_sha256": "aaebabc27eb0a531bce7f81b5dfb7eefe0e4b635935b5a2063c8ac8eb3c10a23",
          "license": "original-project-notes",
          "locator": {
            "line_end": 50,
            "line_start": 35,
            "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
          },
          "revision": "sha256:aaebabc27eb0a531bce7f81b5dfb7eefe0e4b635935b5a2063c8ac8eb3c10a23",
          "source_id": "src-a12ccd822a93af321f34ad70",
          "uri": "file:///root/algorithm-capability-factory/docs/02_%E6%95%B0%E6%8D%AE%E4%B8%8E%E7%9F%A5%E8%AF%86%E6%9D%A5%E6%BA%90.md"
        },
        {
          "content_sha256": "aaebabc27eb0a531bce7f81b5dfb7eefe0e4b635935b5a2063c8ac8eb3c10a23",
          "license": "original-project-notes",
          "locator": {
            "line_end": 62,
            "line_start": 51,
            "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
          },
          "revision": "sha256:aaebabc27eb0a531bce7f81b5dfb7eefe0e4b635935b5a2063c8ac8eb3c10a23",
          "source_id": "src-b78d3450109d520074cd321f",
          "uri": "file:///root/algorithm-capability-factory/docs/02_%E6%95%B0%E6%8D%AE%E4%B8%8E%E7%9F%A5%E8%AF%86%E6%9D%A5%E6%BA%90.md"
        }
      ],
      "extraction_method": "curated-source-grounded",
      "id": "training-only-pipeline",
      "input_schema": {
        "task_types": [
          "tabular_binary_classification",
          "text_binary_classification"
        ],
        "type": "features"
      },
      "name": "只在训练集拟合的 Pipeline",
      "origin": "manual_seed",
      "output_schema": {
        "type": "implementation-guidance"
      },
      "preconditions": [],
      "related": [
        "probability-logistic"
      ],
      "status": "extracted",
      "summary": "Pipeline 顺序连接变换器和最终估计器，使训练和推理使用相同变换链。仅将训练集传给 fit；验证和测试只调用 transform 或 predict_proba。Pipeline 本身不会阻止调用者错误地传入测试数据。",
      "tags": [
        "Pipeline",
        "fit",
        "训练",
        "泄漏",
        "概率"
      ],
      "task_types": [
        "tabular_binary_classification",
        "text_binary_classification"
      ],
      "uses": [
        {
          "kind": "Transform",
          "label": "Pipeline"
        }
      ],
      "version": 2,
      "score": 1.55,
      "lexical_score": 0.25,
      "graph_score": 1.3,
      "evidence_path": [
        {
          "seed": "capability:bank-precontact-policy:v2",
          "hops": [
            {
              "from": "capability:bank-precontact-policy:v2",
              "relation": "REQUIRES",
              "to": "capability:bank-ordered-split:v2"
            },
            {
              "from": "capability:bank-ordered-split:v2",
              "relation": "REQUIRES",
              "to": "capability:training-only-pipeline:v2"
            }
          ],
          "bonus": 0.6000000000000001
        },
        {
          "seed": "capability:bank-target:v2",
          "hops": [
            {
              "from": "capability:bank-target:v2",
              "relation": "REQUIRES",
              "to": "capability:probability-logistic:v1"
            },
            {
              "from": "capability:probability-logistic:v1",
              "relation": "REQUIRES",
              "to": "capability:training-only-pipeline:v2"
            }
          ],
          "bonus": 0.30000000000000004
        },
        {
          "seed": "capability:bank-ordered-split:v2",
          "hops": [
            {
              "from": "capability:bank-ordered-split:v2",
              "relation": "REQUIRES",
              "to": "capability:training-only-pipeline:v2"
            }
          ],
          "bonus": 0.4
        }
      ],
      "graph_used": true,
      "source_locator": [
        {
          "imports": [
            "import warnings",
            "from collections import Counter, defaultdict",
            "from contextlib import contextmanager",
            "from copy import deepcopy",
            "from itertools import chain, islice",
            "import numpy as np",
            "from scipy import sparse",
            "from .base import TransformerMixin, _fit_context, clone",
            "from .exceptions import NotFittedError",
            "from .preprocessing import FunctionTransformer",
            "from .utils import Bunch",
            "from .utils._metadata_requests import METHODS",
            "from .utils._param_validation import HasMethods, Hidden",
            "from .utils._repr_html.estimator import _VisualBlock",
            "from .utils._set_output import _get_container_adapter, _safe_set_output",
            "from .utils._tags import get_tags",
            "from .utils._user_interface import _print_elapsed_time",
            "from .utils.metadata_routing import MetadataRouter, MethodMapping, _raise_for_params, _routing_enabled, get_routing_for_object, process_routing",
            "from .utils.metaestimators import _BaseComposition, available_if",
            "from .utils.parallel import Parallel, delayed",
            "from .utils.validation import check_is_fitted, check_memory"
          ],
          "line_end": 1407,
          "line_start": 123,
          "methods": [
            "__init__",
            "set_output",
            "get_params",
            "set_params",
            "_validate_steps",
            "_iter",
            "__len__",
            "__getitem__",
            "_estimator_type",
            "named_steps",
            "_final_estimator",
            "_log_message",
            "_check_method_params",
            "_get_metadata_for_step",
            "_fit",
            "fit",
            "_can_fit_transform",
            "fit_transform",
            "predict",
            "fit_predict",
            "predict_proba",
            "decision_function",
            "score_samples",
            "predict_log_proba",
            "_can_transform",
            "transform",
            "_can_inverse_transform",
            "inverse_transform",
            "score",
            "classes_",
            "__sklearn_tags__",
            "get_feature_names_out",
            "n_features_in_",
            "feature_names_in_",
            "__sklearn_is_fitted__",
            "_sk_visual_block_",
            "get_metadata_routing"
          ],
          "parse_mode": "ast-only",
          "path": "/root/algorithm-capability-factory/.venv/lib/python3.10/site-packages/sklearn/pipeline.py",
          "relative_path": "sklearn/pipeline.py",
          "signature": "class Pipeline(_BaseComposition):\n    def __init__(self, steps, *, transform_input=None, memory=None, verbose=False)",
          "symbol": "Pipeline"
        },
        {
          "line_end": 50,
          "line_start": 35,
          "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
        },
        {
          "line_end": 62,
          "line_start": 51,
          "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
        }
      ],
      "matched_constraints": [
        "task_type=tabular_binary_classification"
      ],
      "rejected_reason": null
    }
  ],
  "quality_status": "above_prevalence",
  "explanation": {
    "summary": "候选模型 'logistic_default' 在验证集上表现优于 'logistic_balanced'，在平均精度（average_precision）和提升率（lift_at_10pct）方面分别高出0.00111878223781331和0.10962250894225858。两个模型均使用了验证集进行评估，未对密封测试集进行评分。",
    "limitations": [
      "评估仅基于验证集，密封测试集未参与评分。",
      "模型选择不能证明因果营销提升。",
      "受限的AST运行器具有定义的执行范围。"
    ]
  },
  "finished_at": "2026-09-29T18:20:28.601175+00:00",
  "timing": {
    "wall_seconds": 36.377,
    "budget_seconds": 900.0,
    "request_ceiling_seconds": 900
  },
  "report_paths": {}
}
````

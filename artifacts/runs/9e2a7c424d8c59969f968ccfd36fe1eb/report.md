# 算法能力验证报告

指标与状态来自原始验证事实；缺失项不填零、不推断通过。

模式由原始报告的 mode 字段说明：mock 为模拟，replay 为历史回放。

````json
{
  "schema_version": "1.0",
  "run_id": "9e2a7c424d8c59969f968ccfd36fe1eb",
  "status": "passed",
  "mode": "mock",
  "provider": "mock",
  "description": "用通话前客户信息预测是否订购，输出概率，比较两种算法。",
  "dataset_id": "bank",
  "created_at": "2026-09-28T11:41:35.966012+00:00",
  "request": {
    "description": "用通话前客户信息预测是否订购，输出概率，比较两种算法。",
    "dataset_id": "bank",
    "provider": "mock",
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
  "model": "deterministic-mock-v1",
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
      "candidate_id": "c1",
      "plan": {
        "candidate_id": "c1",
        "algorithm": "logistic",
        "variant": "default",
        "rationale": "可复现线性参考方案",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target"
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
        "worker_pid": 21508,
        "wall_seconds": 1.1033264948055148,
        "fit_seconds": 0.07502436614595354,
        "predict_seconds": 0.02501005190424621,
        "worker_wall_seconds": 0.9213168490678072,
        "peak_rss_mib": 290.2421875,
        "cpu_seconds": 1.208028,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 1.276785867055878
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "daf5f0fe1e16551b05e6617bdc4b86b910fba776d9fb01f51791e01d85d81420",
          "code_path": "candidates/c1/attempt_0/model.py",
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
            "worker_pid": 21508,
            "wall_seconds": 1.1033264948055148,
            "fit_seconds": 0.07502436614595354,
            "predict_seconds": 0.02501005190424621,
            "worker_wall_seconds": 0.9213168490678072,
            "peak_rss_mib": 290.2421875,
            "cpu_seconds": 1.208028,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 1.276785867055878
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
      "artifact_id": "c1",
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
      "code_sha256": "daf5f0fe1e16551b05e6617bdc4b86b910fba776d9fb01f51791e01d85d81420",
      "code_path": "candidates/c1/attempt_0/model.py",
      "explanation": "明确标记的离线模板输出"
    },
    {
      "candidate_id": "c2",
      "plan": {
        "candidate_id": "c2",
        "algorithm": "forest",
        "variant": "default",
        "rationale": "不同算法结构的对照方案",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target"
        ],
        "parent_id": null
      },
      "status": "passed",
      "metrics": {
        "average_precision": 0.1478612204016905,
        "roc_auc": 0.5773083190846349,
        "f1_threshold_0_5": 0.0,
        "precision_at_10pct": 0.1808252427184466,
        "recall_at_10pct": 0.16337719298245615,
        "lift_at_10pct": 1.6333753832396527,
        "validation_positive_rate": 0.11070648215586307,
        "top_10pct_count": 824,
        "validation_rows": 8238,
        "classification_threshold": 0.5,
        "evaluation_split": "validation_only",
        "sealed_test_scored": false,
        "ranking_tie_break": "original_validation_row_order",
        "dummy_average_precision": 0.11070648215586307,
        "ap_improvement_over_dummy": 0.037154738245827434
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
          "detail": "Final classifier matches planned forest"
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
        "worker_pid": 21549,
        "wall_seconds": 2.3555035390891135,
        "fit_seconds": 1.1801911778748035,
        "predict_seconds": 0.061516148038208485,
        "worker_wall_seconds": 2.1456705590244383,
        "peak_rss_mib": 290.2421875,
        "cpu_seconds": 3.406705,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 2.50255876686424
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "c28927f8790c23b04baf26fe69107617445d9286cd69ad428a2871224edc6c88",
          "code_path": "candidates/c2/attempt_0/model.py",
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
              "detail": "Final classifier matches planned forest"
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
            "average_precision": 0.1478612204016905,
            "roc_auc": 0.5773083190846349,
            "f1_threshold_0_5": 0.0,
            "precision_at_10pct": 0.1808252427184466,
            "recall_at_10pct": 0.16337719298245615,
            "lift_at_10pct": 1.6333753832396527,
            "validation_positive_rate": 0.11070648215586307,
            "top_10pct_count": 824,
            "validation_rows": 8238,
            "classification_threshold": 0.5,
            "evaluation_split": "validation_only",
            "sealed_test_scored": false,
            "ranking_tie_break": "original_validation_row_order",
            "dummy_average_precision": 0.11070648215586307,
            "ap_improvement_over_dummy": 0.037154738245827434
          },
          "resources": {
            "limits": {
              "timeout_s": 120.0,
              "memory_mib": 2048,
              "cpu_cores": 2
            },
            "worker_pid": 21549,
            "wall_seconds": 2.3555035390891135,
            "fit_seconds": 1.1801911778748035,
            "predict_seconds": 0.061516148038208485,
            "worker_wall_seconds": 2.1456705590244383,
            "peak_rss_mib": 290.2421875,
            "cpu_seconds": 3.406705,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 2.50255876686424
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
            "actual_algorithm": "forest",
            "classifier_class": "RandomForestClassifier",
            "classifier_path": [
              "model"
            ],
            "classifier_parameters": {
              "n_estimators": 100,
              "max_depth": 12,
              "min_samples_leaf": 5,
              "n_jobs": 2,
              "random_state": 42
            },
            "constructor_classes": [
              "Pipeline",
              "ColumnTransformer",
              "Pipeline",
              "SimpleImputer",
              "StandardScaler",
              "OneHotEncoder",
              "RandomForestClassifier"
            ],
            "constructor_count": 7,
            "source": "independently_parsed_constructor_plan"
          }
        }
      ],
      "artifact_id": "c2",
      "parent_id": null,
      "error": null,
      "quality_status": "above_prevalence",
      "model_metadata": {
        "actual_algorithm": "forest",
        "classifier_class": "RandomForestClassifier",
        "classifier_path": [
          "model"
        ],
        "classifier_parameters": {
          "n_estimators": 100,
          "max_depth": 12,
          "min_samples_leaf": 5,
          "n_jobs": 2,
          "random_state": 42
        },
        "constructor_classes": [
          "Pipeline",
          "ColumnTransformer",
          "Pipeline",
          "SimpleImputer",
          "StandardScaler",
          "OneHotEncoder",
          "RandomForestClassifier"
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
      "code_sha256": "c28927f8790c23b04baf26fe69107617445d9286cd69ad428a2871224edc6c88",
      "code_path": "candidates/c2/attempt_0/model.py",
      "explanation": "明确标记的离线模板输出"
    },
    {
      "candidate_id": "b1",
      "plan": {
        "candidate_id": "b1",
        "algorithm": "logistic",
        "variant": "balanced",
        "rationale": "离线Beam扩展测试",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target"
        ],
        "parent_id": "c1"
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
        "worker_pid": 21616,
        "wall_seconds": 1.153357086936012,
        "fit_seconds": 0.11884210794232786,
        "predict_seconds": 0.025326458038762212,
        "worker_wall_seconds": 0.9756441989447922,
        "peak_rss_mib": 290.2421875,
        "cpu_seconds": 1.284881,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 1.301493036095053
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "69dcbc18958ab1e7ba6c7aee85f664f62eac88af375ce46dda92783474030bf4",
          "code_path": "candidates/b1/attempt_0/model.py",
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
            "worker_pid": 21616,
            "wall_seconds": 1.153357086936012,
            "fit_seconds": 0.11884210794232786,
            "predict_seconds": 0.025326458038762212,
            "worker_wall_seconds": 0.9756441989447922,
            "peak_rss_mib": 290.2421875,
            "cpu_seconds": 1.284881,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 1.301493036095053
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
              "random_state": 42,
              "class_weight": "balanced"
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
      "artifact_id": "b1",
      "parent_id": "c1",
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
          "random_state": 42,
          "class_weight": "balanced"
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
      "code_sha256": "69dcbc18958ab1e7ba6c7aee85f664f62eac88af375ce46dda92783474030bf4",
      "code_path": "candidates/b1/attempt_0/model.py",
      "explanation": "明确标记的离线模板输出"
    },
    {
      "candidate_id": "b2",
      "plan": {
        "candidate_id": "b2",
        "algorithm": "logistic",
        "variant": "regularized",
        "rationale": "离线Beam扩展测试",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target"
        ],
        "parent_id": "c1"
      },
      "status": "passed",
      "metrics": {
        "average_precision": 0.1827465606425479,
        "roc_auc": 0.6099591667025878,
        "f1_threshold_0_5": 0.0,
        "precision_at_10pct": 0.22572815533980584,
        "recall_at_10pct": 0.20394736842105263,
        "lift_at_10pct": 2.038978666326009,
        "validation_positive_rate": 0.11070648215586307,
        "top_10pct_count": 824,
        "validation_rows": 8238,
        "classification_threshold": 0.5,
        "evaluation_split": "validation_only",
        "sealed_test_scored": false,
        "ranking_tie_break": "original_validation_row_order",
        "dummy_average_precision": 0.11070648215586307,
        "ap_improvement_over_dummy": 0.07204007848668484
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
        "worker_pid": 21665,
        "wall_seconds": 1.1535389919299632,
        "fit_seconds": 0.0982796021271497,
        "predict_seconds": 0.01484195003286004,
        "worker_wall_seconds": 0.9373719908762723,
        "peak_rss_mib": 290.2421875,
        "cpu_seconds": 1.2408350000000001,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 1.298501366050914
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "d0ef5b6cda8218b23d8139e5e84aebab646e31cc5483f1ef13ba8d01d0eb40f1",
          "code_path": "candidates/b2/attempt_0/model.py",
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
            "average_precision": 0.1827465606425479,
            "roc_auc": 0.6099591667025878,
            "f1_threshold_0_5": 0.0,
            "precision_at_10pct": 0.22572815533980584,
            "recall_at_10pct": 0.20394736842105263,
            "lift_at_10pct": 2.038978666326009,
            "validation_positive_rate": 0.11070648215586307,
            "top_10pct_count": 824,
            "validation_rows": 8238,
            "classification_threshold": 0.5,
            "evaluation_split": "validation_only",
            "sealed_test_scored": false,
            "ranking_tie_break": "original_validation_row_order",
            "dummy_average_precision": 0.11070648215586307,
            "ap_improvement_over_dummy": 0.07204007848668484
          },
          "resources": {
            "limits": {
              "timeout_s": 120.0,
              "memory_mib": 2048,
              "cpu_cores": 2
            },
            "worker_pid": 21665,
            "wall_seconds": 1.1535389919299632,
            "fit_seconds": 0.0982796021271497,
            "predict_seconds": 0.01484195003286004,
            "worker_wall_seconds": 0.9373719908762723,
            "peak_rss_mib": 290.2421875,
            "cpu_seconds": 1.2408350000000001,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 1.298501366050914
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
              "random_state": 42,
              "C": 0.25
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
      "artifact_id": "b2",
      "parent_id": "c1",
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
          "random_state": 42,
          "C": 0.25
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
      "code_sha256": "d0ef5b6cda8218b23d8139e5e84aebab646e31cc5483f1ef13ba8d01d0eb40f1",
      "code_path": "candidates/b2/attempt_0/model.py",
      "explanation": "明确标记的离线模板输出"
    },
    {
      "candidate_id": "b3",
      "plan": {
        "candidate_id": "b3",
        "algorithm": "forest",
        "variant": "balanced",
        "rationale": "离线Beam扩展测试",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target"
        ],
        "parent_id": "c2"
      },
      "status": "passed",
      "metrics": {
        "average_precision": 0.12677389083237253,
        "roc_auc": 0.5488821656584815,
        "f1_threshold_0_5": 0.17634408602150536,
        "precision_at_10pct": 0.14684466019417475,
        "recall_at_10pct": 0.13267543859649122,
        "lift_at_10pct": 1.3264323582013287,
        "validation_positive_rate": 0.11070648215586307,
        "top_10pct_count": 824,
        "validation_rows": 8238,
        "classification_threshold": 0.5,
        "evaluation_split": "validation_only",
        "sealed_test_scored": false,
        "ranking_tie_break": "original_validation_row_order",
        "dummy_average_precision": 0.11070648215586307,
        "ap_improvement_over_dummy": 0.016067408676509465
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
          "detail": "Final classifier matches planned forest"
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
        "worker_pid": 21704,
        "wall_seconds": 2.4056788829620928,
        "fit_seconds": 1.2161997670773417,
        "predict_seconds": 0.062262022867798805,
        "worker_wall_seconds": 2.1836481001228094,
        "peak_rss_mib": 290.2421875,
        "cpu_seconds": 3.472594,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 1.1102230246251565e-16,
        "total_seconds": 2.5509003079496324
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "8d0c4663a059156c2ee12b17b2537f78e71c710d8651b266cd962d8cfff7cbde",
          "code_path": "candidates/b3/attempt_0/model.py",
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
              "detail": "Final classifier matches planned forest"
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
            "average_precision": 0.12677389083237253,
            "roc_auc": 0.5488821656584815,
            "f1_threshold_0_5": 0.17634408602150536,
            "precision_at_10pct": 0.14684466019417475,
            "recall_at_10pct": 0.13267543859649122,
            "lift_at_10pct": 1.3264323582013287,
            "validation_positive_rate": 0.11070648215586307,
            "top_10pct_count": 824,
            "validation_rows": 8238,
            "classification_threshold": 0.5,
            "evaluation_split": "validation_only",
            "sealed_test_scored": false,
            "ranking_tie_break": "original_validation_row_order",
            "dummy_average_precision": 0.11070648215586307,
            "ap_improvement_over_dummy": 0.016067408676509465
          },
          "resources": {
            "limits": {
              "timeout_s": 120.0,
              "memory_mib": 2048,
              "cpu_cores": 2
            },
            "worker_pid": 21704,
            "wall_seconds": 2.4056788829620928,
            "fit_seconds": 1.2161997670773417,
            "predict_seconds": 0.062262022867798805,
            "worker_wall_seconds": 2.1836481001228094,
            "peak_rss_mib": 290.2421875,
            "cpu_seconds": 3.472594,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 1.1102230246251565e-16,
            "total_seconds": 2.5509003079496324
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
            "actual_algorithm": "forest",
            "classifier_class": "RandomForestClassifier",
            "classifier_path": [
              "model"
            ],
            "classifier_parameters": {
              "n_estimators": 100,
              "max_depth": 12,
              "min_samples_leaf": 5,
              "n_jobs": 2,
              "random_state": 42,
              "class_weight": "balanced"
            },
            "constructor_classes": [
              "Pipeline",
              "ColumnTransformer",
              "Pipeline",
              "SimpleImputer",
              "StandardScaler",
              "OneHotEncoder",
              "RandomForestClassifier"
            ],
            "constructor_count": 7,
            "source": "independently_parsed_constructor_plan"
          }
        }
      ],
      "artifact_id": "b3",
      "parent_id": "c2",
      "error": null,
      "quality_status": "above_prevalence",
      "model_metadata": {
        "actual_algorithm": "forest",
        "classifier_class": "RandomForestClassifier",
        "classifier_path": [
          "model"
        ],
        "classifier_parameters": {
          "n_estimators": 100,
          "max_depth": 12,
          "min_samples_leaf": 5,
          "n_jobs": 2,
          "random_state": 42,
          "class_weight": "balanced"
        },
        "constructor_classes": [
          "Pipeline",
          "ColumnTransformer",
          "Pipeline",
          "SimpleImputer",
          "StandardScaler",
          "OneHotEncoder",
          "RandomForestClassifier"
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
      "code_sha256": "8d0c4663a059156c2ee12b17b2537f78e71c710d8651b266cd962d8cfff7cbde",
      "code_path": "candidates/b3/attempt_0/model.py",
      "explanation": "明确标记的离线模板输出"
    },
    {
      "candidate_id": "b4",
      "plan": {
        "candidate_id": "b4",
        "algorithm": "forest",
        "variant": "regularized",
        "rationale": "离线Beam扩展测试",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target"
        ],
        "parent_id": "c2"
      },
      "status": "passed",
      "metrics": {
        "average_precision": 0.14496058062779565,
        "roc_auc": 0.5726260051917947,
        "f1_threshold_0_5": 0.0,
        "precision_at_10pct": 0.1662621359223301,
        "recall_at_10pct": 0.15021929824561403,
        "lift_at_10pct": 1.5018283725089425,
        "validation_positive_rate": 0.11070648215586307,
        "top_10pct_count": 824,
        "validation_rows": 8238,
        "classification_threshold": 0.5,
        "evaluation_split": "validation_only",
        "sealed_test_scored": false,
        "ranking_tie_break": "original_validation_row_order",
        "dummy_average_precision": 0.11070648215586307,
        "ap_improvement_over_dummy": 0.03425409847193259
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
          "detail": "Final classifier matches planned forest"
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
        "worker_pid": 21810,
        "wall_seconds": 2.3052164120599627,
        "fit_seconds": 1.1195878209546208,
        "predict_seconds": 0.06209209584631026,
        "worker_wall_seconds": 2.1046525679994375,
        "peak_rss_mib": 290.2421875,
        "cpu_seconds": 3.290123,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 1.1102230246251565e-16,
        "total_seconds": 2.4647529618814588
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "fa96dd328f9d02c7cf27defa10f0107cbd1387b5839875150b2b98df5cae9ed8",
          "code_path": "candidates/b4/attempt_0/model.py",
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
              "detail": "Final classifier matches planned forest"
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
            "average_precision": 0.14496058062779565,
            "roc_auc": 0.5726260051917947,
            "f1_threshold_0_5": 0.0,
            "precision_at_10pct": 0.1662621359223301,
            "recall_at_10pct": 0.15021929824561403,
            "lift_at_10pct": 1.5018283725089425,
            "validation_positive_rate": 0.11070648215586307,
            "top_10pct_count": 824,
            "validation_rows": 8238,
            "classification_threshold": 0.5,
            "evaluation_split": "validation_only",
            "sealed_test_scored": false,
            "ranking_tie_break": "original_validation_row_order",
            "dummy_average_precision": 0.11070648215586307,
            "ap_improvement_over_dummy": 0.03425409847193259
          },
          "resources": {
            "limits": {
              "timeout_s": 120.0,
              "memory_mib": 2048,
              "cpu_cores": 2
            },
            "worker_pid": 21810,
            "wall_seconds": 2.3052164120599627,
            "fit_seconds": 1.1195878209546208,
            "predict_seconds": 0.06209209584631026,
            "worker_wall_seconds": 2.1046525679994375,
            "peak_rss_mib": 290.2421875,
            "cpu_seconds": 3.290123,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 1.1102230246251565e-16,
            "total_seconds": 2.4647529618814588
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
            "actual_algorithm": "forest",
            "classifier_class": "RandomForestClassifier",
            "classifier_path": [
              "model"
            ],
            "classifier_parameters": {
              "n_estimators": 100,
              "max_depth": 12,
              "min_samples_leaf": 12,
              "n_jobs": 2,
              "random_state": 42
            },
            "constructor_classes": [
              "Pipeline",
              "ColumnTransformer",
              "Pipeline",
              "SimpleImputer",
              "StandardScaler",
              "OneHotEncoder",
              "RandomForestClassifier"
            ],
            "constructor_count": 7,
            "source": "independently_parsed_constructor_plan"
          }
        }
      ],
      "artifact_id": "b4",
      "parent_id": "c2",
      "error": null,
      "quality_status": "above_prevalence",
      "model_metadata": {
        "actual_algorithm": "forest",
        "classifier_class": "RandomForestClassifier",
        "classifier_path": [
          "model"
        ],
        "classifier_parameters": {
          "n_estimators": 100,
          "max_depth": 12,
          "min_samples_leaf": 12,
          "n_jobs": 2,
          "random_state": 42
        },
        "constructor_classes": [
          "Pipeline",
          "ColumnTransformer",
          "Pipeline",
          "SimpleImputer",
          "StandardScaler",
          "OneHotEncoder",
          "RandomForestClassifier"
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
      "code_sha256": "fa96dd328f9d02c7cf27defa10f0107cbd1387b5839875150b2b98df5cae9ed8",
      "code_path": "candidates/b4/attempt_0/model.py",
      "explanation": "明确标记的离线模板输出"
    }
  ],
  "selected_candidate_id": "c1",
  "events": [
    {
      "sequence": 0,
      "event_type": "RECEIVED",
      "type": "RECEIVED",
      "created_at": "2026-09-28T11:41:36.023511+00:00",
      "data": {
        "mode": "mock",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 1,
      "event_type": "MOCK_RESPONSE",
      "type": "MOCK_RESPONSE",
      "created_at": "2026-09-28T11:41:37.116347+00:00",
      "data": {
        "role": "interpreter",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 2,
      "event_type": "SPEC_VALIDATED",
      "type": "SPEC_VALIDATED",
      "created_at": "2026-09-28T11:41:37.351078+00:00",
      "data": {
        "task_type": "tabular_binary_classification",
        "assumptions": [
          "离线规则测试模式"
        ]
      }
    },
    {
      "sequence": 3,
      "event_type": "KNOWLEDGE_RETRIEVED",
      "type": "KNOWLEDGE_RETRIEVED",
      "created_at": "2026-09-28T11:41:37.488638+00:00",
      "data": {
        "count": 6,
        "use_graph": true,
        "capability_ids": [
          "bank-precontact-policy",
          "bank-target",
          "probability-logistic",
          "bank-ordered-split",
          "average-precision",
          "training-only-pipeline"
        ]
      }
    },
    {
      "sequence": 4,
      "event_type": "MOCK_RESPONSE",
      "type": "MOCK_RESPONSE",
      "created_at": "2026-09-28T11:41:37.662032+00:00",
      "data": {
        "role": "planner",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 5,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-28T11:41:37.886951+00:00",
      "data": {
        "candidate_id": "c1",
        "algorithm": "logistic",
        "variant": "default",
        "rationale": "可复现线性参考方案",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target"
        ],
        "parent_id": null
      }
    },
    {
      "sequence": 6,
      "event_type": "MOCK_RESPONSE",
      "type": "MOCK_RESPONSE",
      "created_at": "2026-09-28T11:41:38.097638+00:00",
      "data": {
        "role": "coder",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 7,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T11:41:38.304664+00:00",
      "data": {
        "candidate_id": "c1",
        "attempt": 0,
        "code_sha256": "daf5f0fe1e16551b05e6617bdc4b86b910fba776d9fb01f51791e01d85d81420"
      }
    },
    {
      "sequence": 8,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T11:41:39.800246+00:00",
      "data": {
        "candidate_id": "c1",
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
      "created_at": "2026-09-28T11:41:40.122383+00:00",
      "data": {
        "candidate_id": "c2",
        "algorithm": "forest",
        "variant": "default",
        "rationale": "不同算法结构的对照方案",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target"
        ],
        "parent_id": null
      }
    },
    {
      "sequence": 10,
      "event_type": "MOCK_RESPONSE",
      "type": "MOCK_RESPONSE",
      "created_at": "2026-09-28T11:41:40.357956+00:00",
      "data": {
        "role": "coder",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 11,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T11:41:40.606510+00:00",
      "data": {
        "candidate_id": "c2",
        "attempt": 0,
        "code_sha256": "c28927f8790c23b04baf26fe69107617445d9286cd69ad428a2871224edc6c88"
      }
    },
    {
      "sequence": 12,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T11:41:43.335633+00:00",
      "data": {
        "candidate_id": "c2",
        "attempt": 0,
        "status": "passed",
        "metrics": {
          "average_precision": 0.1478612204016905,
          "roc_auc": 0.5773083190846349,
          "f1_threshold_0_5": 0.0,
          "precision_at_10pct": 0.1808252427184466,
          "recall_at_10pct": 0.16337719298245615,
          "lift_at_10pct": 1.6333753832396527,
          "validation_positive_rate": 0.11070648215586307,
          "top_10pct_count": 824,
          "validation_rows": 8238,
          "classification_threshold": 0.5,
          "evaluation_split": "validation_only",
          "sealed_test_scored": false,
          "ranking_tie_break": "original_validation_row_order",
          "dummy_average_precision": 0.11070648215586307,
          "ap_improvement_over_dummy": 0.037154738245827434
        },
        "error": null
      }
    },
    {
      "sequence": 13,
      "event_type": "BEAM_EXPANDED",
      "type": "BEAM_EXPANDED",
      "created_at": "2026-09-28T11:41:43.577056+00:00",
      "data": {
        "beam_width": 2,
        "parents": [
          "c1",
          "c2"
        ],
        "children": 4
      }
    },
    {
      "sequence": 14,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-28T11:41:43.790756+00:00",
      "data": {
        "candidate_id": "b1",
        "algorithm": "logistic",
        "variant": "balanced",
        "rationale": "离线Beam扩展测试",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target"
        ],
        "parent_id": "c1"
      }
    },
    {
      "sequence": 15,
      "event_type": "MOCK_RESPONSE",
      "type": "MOCK_RESPONSE",
      "created_at": "2026-09-28T11:41:44.036882+00:00",
      "data": {
        "role": "coder",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 16,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T11:41:44.251019+00:00",
      "data": {
        "candidate_id": "b1",
        "attempt": 0,
        "code_sha256": "69dcbc18958ab1e7ba6c7aee85f664f62eac88af375ce46dda92783474030bf4"
      }
    },
    {
      "sequence": 17,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T11:41:45.755305+00:00",
      "data": {
        "candidate_id": "b1",
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
      "sequence": 18,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-28T11:41:45.986612+00:00",
      "data": {
        "candidate_id": "b2",
        "algorithm": "logistic",
        "variant": "regularized",
        "rationale": "离线Beam扩展测试",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target"
        ],
        "parent_id": "c1"
      }
    },
    {
      "sequence": 19,
      "event_type": "MOCK_RESPONSE",
      "type": "MOCK_RESPONSE",
      "created_at": "2026-09-28T11:41:46.467037+00:00",
      "data": {
        "role": "coder",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 20,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T11:41:46.719537+00:00",
      "data": {
        "candidate_id": "b2",
        "attempt": 0,
        "code_sha256": "d0ef5b6cda8218b23d8139e5e84aebab646e31cc5483f1ef13ba8d01d0eb40f1"
      }
    },
    {
      "sequence": 21,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T11:41:48.246154+00:00",
      "data": {
        "candidate_id": "b2",
        "attempt": 0,
        "status": "passed",
        "metrics": {
          "average_precision": 0.1827465606425479,
          "roc_auc": 0.6099591667025878,
          "f1_threshold_0_5": 0.0,
          "precision_at_10pct": 0.22572815533980584,
          "recall_at_10pct": 0.20394736842105263,
          "lift_at_10pct": 2.038978666326009,
          "validation_positive_rate": 0.11070648215586307,
          "top_10pct_count": 824,
          "validation_rows": 8238,
          "classification_threshold": 0.5,
          "evaluation_split": "validation_only",
          "sealed_test_scored": false,
          "ranking_tie_break": "original_validation_row_order",
          "dummy_average_precision": 0.11070648215586307,
          "ap_improvement_over_dummy": 0.07204007848668484
        },
        "error": null
      }
    },
    {
      "sequence": 22,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-28T11:41:48.589543+00:00",
      "data": {
        "candidate_id": "b3",
        "algorithm": "forest",
        "variant": "balanced",
        "rationale": "离线Beam扩展测试",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target"
        ],
        "parent_id": "c2"
      }
    },
    {
      "sequence": 23,
      "event_type": "MOCK_RESPONSE",
      "type": "MOCK_RESPONSE",
      "created_at": "2026-09-28T11:41:48.833957+00:00",
      "data": {
        "role": "coder",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 24,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T11:41:49.047035+00:00",
      "data": {
        "candidate_id": "b3",
        "attempt": 0,
        "code_sha256": "8d0c4663a059156c2ee12b17b2537f78e71c710d8651b266cd962d8cfff7cbde"
      }
    },
    {
      "sequence": 25,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T11:41:51.907274+00:00",
      "data": {
        "candidate_id": "b3",
        "attempt": 0,
        "status": "passed",
        "metrics": {
          "average_precision": 0.12677389083237253,
          "roc_auc": 0.5488821656584815,
          "f1_threshold_0_5": 0.17634408602150536,
          "precision_at_10pct": 0.14684466019417475,
          "recall_at_10pct": 0.13267543859649122,
          "lift_at_10pct": 1.3264323582013287,
          "validation_positive_rate": 0.11070648215586307,
          "top_10pct_count": 824,
          "validation_rows": 8238,
          "classification_threshold": 0.5,
          "evaluation_split": "validation_only",
          "sealed_test_scored": false,
          "ranking_tie_break": "original_validation_row_order",
          "dummy_average_precision": 0.11070648215586307,
          "ap_improvement_over_dummy": 0.016067408676509465
        },
        "error": null
      }
    },
    {
      "sequence": 26,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-28T11:41:52.179786+00:00",
      "data": {
        "candidate_id": "b4",
        "algorithm": "forest",
        "variant": "regularized",
        "rationale": "离线Beam扩展测试",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target"
        ],
        "parent_id": "c2"
      }
    },
    {
      "sequence": 27,
      "event_type": "MOCK_RESPONSE",
      "type": "MOCK_RESPONSE",
      "created_at": "2026-09-28T11:41:52.385159+00:00",
      "data": {
        "role": "coder",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 28,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T11:41:52.662296+00:00",
      "data": {
        "candidate_id": "b4",
        "attempt": 0,
        "code_sha256": "fa96dd328f9d02c7cf27defa10f0107cbd1387b5839875150b2b98df5cae9ed8"
      }
    },
    {
      "sequence": 29,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T11:41:55.448867+00:00",
      "data": {
        "candidate_id": "b4",
        "attempt": 0,
        "status": "passed",
        "metrics": {
          "average_precision": 0.14496058062779565,
          "roc_auc": 0.5726260051917947,
          "f1_threshold_0_5": 0.0,
          "precision_at_10pct": 0.1662621359223301,
          "recall_at_10pct": 0.15021929824561403,
          "lift_at_10pct": 1.5018283725089425,
          "validation_positive_rate": 0.11070648215586307,
          "top_10pct_count": 824,
          "validation_rows": 8238,
          "classification_threshold": 0.5,
          "evaluation_split": "validation_only",
          "sealed_test_scored": false,
          "ranking_tie_break": "original_validation_row_order",
          "dummy_average_precision": 0.11070648215586307,
          "ap_improvement_over_dummy": 0.03425409847193259
        },
        "error": null
      }
    },
    {
      "sequence": 30,
      "event_type": "MOCK_RESPONSE",
      "type": "MOCK_RESPONSE",
      "created_at": "2026-09-28T11:41:55.800988+00:00",
      "data": {
        "role": "curator",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 31,
      "event_type": "COMPARED",
      "type": "COMPARED",
      "created_at": "2026-09-28T11:41:56.079566+00:00",
      "data": {
        "selected_candidate_id": "c1"
      }
    },
    {
      "sequence": 32,
      "event_type": "RECORDED",
      "type": "RECORDED",
      "created_at": "2026-09-28T11:41:56.860181+00:00",
      "data": {
        "intended_status": "passed",
        "experiences": 0
      }
    }
  ],
  "usage": {
    "calls": 9,
    "input_tokens": 0,
    "output_tokens": 0,
    "cached_input_tokens": 0,
    "records": []
  },
  "warnings": [
    "验证集成绩，不是最终测试成绩。",
    "受限AST构造器程序，不是任意Python或Docker操作系统沙箱。"
  ],
  "search_tree": [
    {
      "candidate_id": "c1",
      "parent_id": null,
      "status": "passed",
      "average_precision": 0.18287735589367637,
      "pruned": false,
      "pruned_reason": null
    },
    {
      "candidate_id": "c2",
      "parent_id": null,
      "status": "passed",
      "average_precision": 0.1478612204016905,
      "pruned": true,
      "pruned_reason": "outside_final_beam_or_failed_hard_checks"
    },
    {
      "candidate_id": "b1",
      "parent_id": "c1",
      "status": "passed",
      "average_precision": 0.1807589966629477,
      "pruned": true,
      "pruned_reason": "outside_final_beam_or_failed_hard_checks"
    },
    {
      "candidate_id": "b2",
      "parent_id": "c1",
      "status": "passed",
      "average_precision": 0.1827465606425479,
      "pruned": false,
      "pruned_reason": null
    },
    {
      "candidate_id": "b3",
      "parent_id": "c2",
      "status": "passed",
      "average_precision": 0.12677389083237253,
      "pruned": true,
      "pruned_reason": "outside_final_beam_or_failed_hard_checks"
    },
    {
      "candidate_id": "b4",
      "parent_id": "c2",
      "status": "passed",
      "average_precision": 0.14496058062779565,
      "pruned": true,
      "pruned_reason": "outside_final_beam_or_failed_hard_checks"
    }
  ],
  "knowledge_writeback": {
    "run_saved": true,
    "experiences": []
  },
  "data_summary": {
    "train_rows": 24712,
    "validation_rows": 8238
  },
  "interpretation": {
    "objective": "用通话前客户信息预测是否订购，输出概率，比较两种算法。",
    "constraints": [
      "遵守固定数据与特征协议"
    ],
    "assumptions": [
      "离线规则测试模式"
    ],
    "warnings": [],
    "incompatible_requests": []
  },
  "evidence": [
    {
      "capability_id": "bank-precontact-policy",
      "confidence": 1.0,
      "created_at": "2026-09-28T11:41:36.557531+00:00",
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
          "content_sha256": "10bbedb7d1e5d03c92860a5aef348cb020e7a385a5ce520677bd95790881a970",
          "license": "original-project-notes",
          "locator": {
            "line_end": 34,
            "line_start": 18,
            "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
          },
          "revision": "sha256:10bbedb7d1e5d03c92860a5aef348cb020e7a385a5ce520677bd95790881a970",
          "source_id": "src-9d912fa3bc826e2bfd7f1aff",
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
      "version": 1,
      "score": 2.898563,
      "lexical_score": 2.245366,
      "graph_score": 0.653197,
      "evidence_path": [
        {
          "seed": "capability:bank-target:v1",
          "hops": [
            {
              "from": "capability:bank-target:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-precontact-policy:v1"
            }
          ],
          "bonus": 0.4898979485566357
        },
        {
          "seed": "capability:probability-logistic:v1",
          "hops": [
            {
              "from": "capability:probability-logistic:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-target:v1"
            },
            {
              "from": "capability:bank-target:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-precontact-policy:v1"
            }
          ],
          "bonus": 0.16329931618554525
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
      "created_at": "2026-09-28T11:41:36.557801+00:00",
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
          "content_sha256": "10bbedb7d1e5d03c92860a5aef348cb020e7a385a5ce520677bd95790881a970",
          "license": "original-project-notes",
          "locator": {
            "line_end": 34,
            "line_start": 18,
            "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
          },
          "revision": "sha256:10bbedb7d1e5d03c92860a5aef348cb020e7a385a5ce520677bd95790881a970",
          "source_id": "src-9d912fa3bc826e2bfd7f1aff",
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
      "version": 1,
      "score": 2.44949,
      "lexical_score": 1.224745,
      "graph_score": 1.224745,
      "evidence_path": [
        {
          "seed": "capability:bank-precontact-policy:v1",
          "hops": [
            {
              "from": "capability:bank-precontact-policy:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-target:v1"
            }
          ],
          "bonus": 0.8981462390204987
        },
        {
          "seed": "capability:probability-logistic:v1",
          "hops": [
            {
              "from": "capability:probability-logistic:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-target:v1"
            }
          ],
          "bonus": 0.3265986323710905
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
      "capability_id": "probability-logistic",
      "confidence": 1.0,
      "created_at": "2026-09-28T11:41:36.559112+00:00",
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
      "score": 1.755468,
      "lexical_score": 0.816497,
      "graph_score": 0.938971,
      "evidence_path": [
        {
          "seed": "capability:bank-precontact-policy:v1",
          "hops": [
            {
              "from": "capability:bank-precontact-policy:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-target:v1"
            },
            {
              "from": "capability:bank-target:v1",
              "relation": "REQUIRES",
              "to": "capability:probability-logistic:v1"
            }
          ],
          "bonus": 0.44907311951024936
        },
        {
          "seed": "capability:bank-target:v1",
          "hops": [
            {
              "from": "capability:bank-target:v1",
              "relation": "REQUIRES",
              "to": "capability:probability-logistic:v1"
            }
          ],
          "bonus": 0.4898979485566357
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
      "capability_id": "bank-ordered-split",
      "confidence": 1.0,
      "created_at": "2026-09-28T11:41:36.558014+00:00",
      "dependencies": [
        "Python >=3.10",
        "scikit-learn"
      ],
      "evidence": [
        {
          "content_sha256": "10bbedb7d1e5d03c92860a5aef348cb020e7a385a5ce520677bd95790881a970",
          "license": "original-project-notes",
          "locator": {
            "line_end": 50,
            "line_start": 35,
            "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
          },
          "revision": "sha256:10bbedb7d1e5d03c92860a5aef348cb020e7a385a5ce520677bd95790881a970",
          "source_id": "src-60c9bfae88dcf21b0c74bc3e",
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
      "version": 1,
      "score": 1.510519,
      "lexical_score": 0.204124,
      "graph_score": 1.306395,
      "evidence_path": [
        {
          "seed": "capability:bank-precontact-policy:v1",
          "hops": [
            {
              "from": "capability:bank-precontact-policy:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-ordered-split:v1"
            }
          ],
          "bonus": 0.8981462390204987
        },
        {
          "seed": "capability:bank-target:v1",
          "hops": [
            {
              "from": "capability:bank-target:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-precontact-policy:v1"
            },
            {
              "from": "capability:bank-precontact-policy:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-ordered-split:v1"
            }
          ],
          "bonus": 0.24494897427831785
        },
        {
          "seed": "capability:probability-logistic:v1",
          "hops": [
            {
              "from": "capability:probability-logistic:v1",
              "relation": "REQUIRES",
              "to": "capability:training-only-pipeline:v1"
            },
            {
              "from": "capability:training-only-pipeline:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-ordered-split:v1"
            }
          ],
          "bonus": 0.16329931618554525
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
      "created_at": "2026-09-28T11:41:36.559942+00:00",
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
      "score": 1.469694,
      "lexical_score": 0.204124,
      "graph_score": 1.26557,
      "evidence_path": [
        {
          "seed": "capability:bank-precontact-policy:v1",
          "hops": [
            {
              "from": "capability:bank-precontact-policy:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-target:v1"
            },
            {
              "from": "capability:bank-target:v1",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            }
          ],
          "bonus": 0.44907311951024936
        },
        {
          "seed": "capability:bank-target:v1",
          "hops": [
            {
              "from": "capability:bank-target:v1",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            }
          ],
          "bonus": 0.4898979485566357
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
          "bonus": 0.3265986323710905
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
      "capability_id": "training-only-pipeline",
      "confidence": 1.0,
      "created_at": "2026-09-28T11:41:36.558629+00:00",
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
          "content_sha256": "10bbedb7d1e5d03c92860a5aef348cb020e7a385a5ce520677bd95790881a970",
          "license": "original-project-notes",
          "locator": {
            "line_end": 50,
            "line_start": 35,
            "path": "/root/algorithm-capability-factory/docs/02_数据与知识来源.md"
          },
          "revision": "sha256:10bbedb7d1e5d03c92860a5aef348cb020e7a385a5ce520677bd95790881a970",
          "source_id": "src-60c9bfae88dcf21b0c74bc3e",
          "uri": "file:///root/algorithm-capability-factory/docs/02_%E6%95%B0%E6%8D%AE%E4%B8%8E%E7%9F%A5%E8%AF%86%E6%9D%A5%E6%BA%90.md"
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
      "version": 1,
      "score": 1.428869,
      "lexical_score": 0.408248,
      "graph_score": 1.020621,
      "evidence_path": [
        {
          "seed": "capability:bank-precontact-policy:v1",
          "hops": [
            {
              "from": "capability:bank-precontact-policy:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-ordered-split:v1"
            },
            {
              "from": "capability:bank-ordered-split:v1",
              "relation": "REQUIRES",
              "to": "capability:training-only-pipeline:v1"
            }
          ],
          "bonus": 0.44907311951024936
        },
        {
          "seed": "capability:bank-target:v1",
          "hops": [
            {
              "from": "capability:bank-target:v1",
              "relation": "REQUIRES",
              "to": "capability:probability-logistic:v1"
            },
            {
              "from": "capability:probability-logistic:v1",
              "relation": "REQUIRES",
              "to": "capability:training-only-pipeline:v1"
            }
          ],
          "bonus": 0.24494897427831785
        },
        {
          "seed": "capability:probability-logistic:v1",
          "hops": [
            {
              "from": "capability:probability-logistic:v1",
              "relation": "REQUIRES",
              "to": "capability:training-only-pipeline:v1"
            }
          ],
          "bonus": 0.3265986323710905
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
    "summary": "已根据独立验证报告比较方案；本次为mock运行。",
    "limitations": [
      "未调用真实大模型"
    ]
  },
  "finished_at": "2026-09-28T11:41:56.517408+00:00",
  "timing": {
    "wall_seconds": 20.551,
    "budget_seconds": 900
  },
  "report_paths": {}
}
````

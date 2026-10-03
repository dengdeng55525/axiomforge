# 算法能力验证报告

指标与状态来自原始验证事实；缺失项不填零、不推断通过。

模式由原始报告的 mode 字段说明：mock 为模拟，replay 为历史回放。

````json
{
  "schema_version": "1.0",
  "run_id": "bb646d91188647058760647ba6b16149",
  "status": "passed",
  "mode": "real",
  "provider": "deepseek",
  "description": "预测客户是否订购银行定期存款；仅使用通话前可得特征，禁止 duration。比较两个候选，使用验证集 AP 选择方案，输出来源、检查、资源和修复记录。",
  "dataset_id": "bank",
  "created_at": "2026-09-28T13:58:41.592499+00:00",
  "request": {
    "description": "预测客户是否订购银行定期存款；仅使用通话前可得特征，禁止 duration。比较两个候选，使用验证集 AP 选择方案，输出来源、检查、资源和修复记录。",
    "dataset_id": "bank",
    "provider": "deepseek",
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
  "model": "deepseek-flash",
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
      "candidate_id": "bank_logistic_balanced_v1",
      "plan": {
        "candidate_id": "bank_logistic_balanced_v1",
        "algorithm": "logistic",
        "variant": "balanced",
        "rationale": "逻辑回归在通话前表格特征上提供校准概率接口，class_weight=balanced 缓解正类稀有；与 AP 主指标和 bank-precontact-policy 的保守特征白名单兼容，作为线性基线候选。",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target",
          "probability-logistic",
          "average-precision"
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
        "worker_pid": 39887,
        "wall_seconds": 1.085952727124095,
        "fit_seconds": 0.10814913595095277,
        "predict_seconds": 0.014304222073405981,
        "worker_wall_seconds": 0.8950234570074826,
        "peak_rss_mib": 227.8046875,
        "cpu_seconds": 1.2212679999999998,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 2.135409543989226
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "d50feaac7ab18c5aacb67432a4f9c7e0ee1903dbabc52cda3e478eec5e4f2b1f",
          "code_path": "candidates/bank_logistic_balanced_v1/attempt_0/model.py",
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
            "worker_pid": 39887,
            "wall_seconds": 1.085952727124095,
            "fit_seconds": 0.10814913595095277,
            "predict_seconds": 0.014304222073405981,
            "worker_wall_seconds": 0.8950234570074826,
            "peak_rss_mib": 227.8046875,
            "cpu_seconds": 1.2212679999999998,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 2.135409543989226
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
      "artifact_id": "bank_logistic_balanced_v1",
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
      "code_sha256": "d50feaac7ab18c5aacb67432a4f9c7e0ee1903dbabc52cda3e478eec5e4f2b1f",
      "code_path": "candidates/bank_logistic_balanced_v1/attempt_0/model.py",
      "explanation": "Implements the balanced logistic plan: median-imputed/scaled numeric features plus ignore-unknown one-hot categoricals over the precontact whitelist (no duration), with class_weight='balanced' and max_iter=1000 for the AP-scored probability baseline."
    },
    {
      "candidate_id": "bank_forest_balanced_v1",
      "plan": {
        "candidate_id": "bank_forest_balanced_v1",
        "algorithm": "forest",
        "variant": "balanced",
        "rationale": "随机森林可捕捉非线性与类别交互，class_weight=balanced 处理类别不平衡；作为与线性模型互补的树集成候选，在同一验证协议下用 AP 比较。",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "hist-gradient-boosting"
        ],
        "parent_id": null
      },
      "status": "passed",
      "metrics": {
        "average_precision": 0.12825103811039737,
        "roc_auc": 0.5524364825351668,
        "f1_threshold_0_5": 0.1808199121522694,
        "precision_at_10pct": 0.14563106796116504,
        "recall_at_10pct": 0.13157894736842105,
        "lift_at_10pct": 1.3154701073071027,
        "validation_positive_rate": 0.11070648215586307,
        "top_10pct_count": 824,
        "validation_rows": 8238,
        "classification_threshold": 0.5,
        "evaluation_split": "validation_only",
        "sealed_test_scored": false,
        "ranking_tie_break": "original_validation_row_order",
        "dummy_average_precision": 0.11070648215586307,
        "ap_improvement_over_dummy": 0.017544555954534302
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
        "worker_pid": 39966,
        "wall_seconds": 3.543894103029743,
        "fit_seconds": 2.355926115065813,
        "predict_seconds": 0.08659549010917544,
        "worker_wall_seconds": 3.3476754270959646,
        "peak_rss_mib": 266.9296875,
        "cpu_seconds": 5.767815,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 1.1102230246251565e-16,
        "total_seconds": 3.7417589200194925
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "f0b81f732bdb5a29a344d2567ea68e71b564d8a083d9fb27a006968bd6c89112",
          "code_path": "candidates/bank_forest_balanced_v1/attempt_0/model.py",
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
            "average_precision": 0.12825103811039737,
            "roc_auc": 0.5524364825351668,
            "f1_threshold_0_5": 0.1808199121522694,
            "precision_at_10pct": 0.14563106796116504,
            "recall_at_10pct": 0.13157894736842105,
            "lift_at_10pct": 1.3154701073071027,
            "validation_positive_rate": 0.11070648215586307,
            "top_10pct_count": 824,
            "validation_rows": 8238,
            "classification_threshold": 0.5,
            "evaluation_split": "validation_only",
            "sealed_test_scored": false,
            "ranking_tie_break": "original_validation_row_order",
            "dummy_average_precision": 0.11070648215586307,
            "ap_improvement_over_dummy": 0.017544555954534302
          },
          "resources": {
            "limits": {
              "timeout_s": 120.0,
              "memory_mib": 2048,
              "cpu_cores": 2
            },
            "worker_pid": 39966,
            "wall_seconds": 3.543894103029743,
            "fit_seconds": 2.355926115065813,
            "predict_seconds": 0.08659549010917544,
            "worker_wall_seconds": 3.3476754270959646,
            "peak_rss_mib": 266.9296875,
            "cpu_seconds": 5.767815,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 1.1102230246251565e-16,
            "total_seconds": 3.7417589200194925
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
              "n_estimators": 200,
              "max_depth": 12,
              "min_samples_leaf": 5,
              "class_weight": "balanced",
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
      "artifact_id": "bank_forest_balanced_v1",
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
          "n_estimators": 200,
          "max_depth": 12,
          "min_samples_leaf": 5,
          "class_weight": "balanced",
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
      "code_sha256": "f0b81f732bdb5a29a344d2567ea68e71b564d8a083d9fb27a006968bd6c89112",
      "code_path": "candidates/bank_forest_balanced_v1/attempt_0/model.py",
      "explanation": "Bank precontact features (no duration) are routed through median-impute/scale numeric and handle_unknown='ignore' one-hot categorical preprocessing, then a balanced random forest (class_weight='balanced', n_estimators=200, max_depth=12, n_jobs=2, seed=42) provides predict_proba for AP evaluation per the forest/balanced plan."
    }
  ],
  "selected_candidate_id": "bank_logistic_balanced_v1",
  "events": [
    {
      "sequence": 0,
      "event_type": "RECEIVED",
      "type": "RECEIVED",
      "created_at": "2026-09-28T13:58:41.722181+00:00",
      "data": {
        "mode": "real",
        "model": "deepseek-flash"
      }
    },
    {
      "sequence": 1,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T13:58:54.631119+00:00",
      "data": {
        "role": "interpreter",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "7f3994cb-8963-4313-9be7-4d6f329a2a9e",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "16de8db275e4b3d0fac5c9fae96178e5d6dc4952438ac063b5a103dd7368a896",
        "response_sha256": "2bc271afd276792277c806a64936ec01d996507560efc00d8a936201ee2d1a12",
        "input_tokens": 479,
        "output_tokens": 313,
        "seconds": 12.374,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 2,
      "event_type": "SPEC_VALIDATED",
      "type": "SPEC_VALIDATED",
      "created_at": "2026-09-28T13:58:54.914831+00:00",
      "data": {
        "task_type": "tabular_binary_classification",
        "assumptions": [
          "两个候选方案均基于同一数据集 bank 和同一特征策略 precontact_conservative_v1",
          "验证集 AP 用于模型选择，且验证集划分方式在两个候选间保持一致",
          "输出记录中的来源、检查、资源和修复记录指可审计的元数据，而非私有推理过程"
        ]
      }
    },
    {
      "sequence": 3,
      "event_type": "KNOWLEDGE_RETRIEVED",
      "type": "KNOWLEDGE_RETRIEVED",
      "created_at": "2026-09-28T13:58:55.177352+00:00",
      "data": {
        "count": 6,
        "use_graph": true,
        "capability_ids": [
          "bank-precontact-policy",
          "bank-target",
          "bank-ordered-split",
          "average-precision",
          "probability-logistic",
          "hist-gradient-boosting"
        ]
      }
    },
    {
      "sequence": 4,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T13:58:57.359966+00:00",
      "data": {
        "role": "planner",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "84e7f8f7-a6ac-46d4-8dfc-68dcdf3b3e5b",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "a419c443dcf407a5332aab749361c0c678000132ea516fb93ceba866813dd49d",
        "response_sha256": "c8c2be45cbd81f6a089d7704224d92382140cd7d837fbd590c4ab4eca1a22d4d",
        "input_tokens": 8563,
        "output_tokens": 194,
        "seconds": 1.927,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 5,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-28T13:58:57.608375+00:00",
      "data": {
        "candidate_id": "bank_logistic_balanced_v1",
        "algorithm": "logistic",
        "variant": "balanced",
        "rationale": "逻辑回归在通话前表格特征上提供校准概率接口，class_weight=balanced 缓解正类稀有；与 AP 主指标和 bank-precontact-policy 的保守特征白名单兼容，作为线性基线候选。",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target",
          "probability-logistic",
          "average-precision"
        ],
        "parent_id": null
      }
    },
    {
      "sequence": 6,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T13:59:05.125227+00:00",
      "data": {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "c0703d93-8d0b-4999-a038-dd63423525ea",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "01c9d9b8c0c71bdffa7feee6d1dd2f176e1ece09f78af8890a42da2e3c757cf0",
        "response_sha256": "015008231da86c3215bf92e5df6550d9a3ade4ab07031f8ceb25534dc0b91ea8",
        "input_tokens": 9102,
        "output_tokens": 252,
        "seconds": 7.199,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 7,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T13:59:05.372876+00:00",
      "data": {
        "candidate_id": "bank_logistic_balanced_v1",
        "attempt": 0,
        "code_sha256": "d50feaac7ab18c5aacb67432a4f9c7e0ee1903dbabc52cda3e478eec5e4f2b1f"
      }
    },
    {
      "sequence": 8,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T13:59:07.773746+00:00",
      "data": {
        "candidate_id": "bank_logistic_balanced_v1",
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
      "sequence": 9,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-28T13:59:08.094410+00:00",
      "data": {
        "candidate_id": "bank_forest_balanced_v1",
        "algorithm": "forest",
        "variant": "balanced",
        "rationale": "随机森林可捕捉非线性与类别交互，class_weight=balanced 处理类别不平衡；作为与线性模型互补的树集成候选，在同一验证协议下用 AP 比较。",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "hist-gradient-boosting"
        ],
        "parent_id": null
      }
    },
    {
      "sequence": 10,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T13:59:10.455824+00:00",
      "data": {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "6fd1f110-d18c-4e78-852e-f7f4eb9a7c90",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "6c3290757b8a8c5a57805558ba5f99ca09b109b9a6f4da7e95d76007f0a1ee44",
        "response_sha256": "e77d2a3af3bc04018b0c0c4bfc6cbdd19bdfbfe5bc59bea02873c64ed9e20f69",
        "input_tokens": 9112,
        "output_tokens": 295,
        "seconds": 2.078,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 11,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T13:59:10.734591+00:00",
      "data": {
        "candidate_id": "bank_forest_balanced_v1",
        "attempt": 0,
        "code_sha256": "f0b81f732bdb5a29a344d2567ea68e71b564d8a083d9fb27a006968bd6c89112"
      }
    },
    {
      "sequence": 12,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T13:59:14.762414+00:00",
      "data": {
        "candidate_id": "bank_forest_balanced_v1",
        "attempt": 0,
        "status": "passed",
        "metrics": {
          "average_precision": 0.12825103811039737,
          "roc_auc": 0.5524364825351668,
          "f1_threshold_0_5": 0.1808199121522694,
          "precision_at_10pct": 0.14563106796116504,
          "recall_at_10pct": 0.13157894736842105,
          "lift_at_10pct": 1.3154701073071027,
          "validation_positive_rate": 0.11070648215586307,
          "top_10pct_count": 824,
          "validation_rows": 8238,
          "classification_threshold": 0.5,
          "evaluation_split": "validation_only",
          "sealed_test_scored": false,
          "ranking_tie_break": "original_validation_row_order",
          "dummy_average_precision": 0.11070648215586307,
          "ap_improvement_over_dummy": 0.017544555954534302
        },
        "error": null
      }
    },
    {
      "sequence": 13,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T13:59:18.611115+00:00",
      "data": {
        "role": "curator",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "1723dea5-b155-406a-8d8c-e3905897b0a7",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "54ad594125c9697af9a86e6fee6d2627087edc9944153eae8f8d3ec590923be0",
        "response_sha256": "c7e5f50ec8d0ef32bafa11286d43a65c6f418db4a24f194a32538c25004ac802",
        "input_tokens": 743,
        "output_tokens": 611,
        "seconds": 3.49,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 14,
      "event_type": "COMPARED",
      "type": "COMPARED",
      "created_at": "2026-09-28T13:59:18.972380+00:00",
      "data": {
        "selected_candidate_id": "bank_logistic_balanced_v1"
      }
    },
    {
      "sequence": 15,
      "event_type": "RECORDED",
      "type": "RECORDED",
      "created_at": "2026-09-28T13:59:19.370791+00:00",
      "data": {
        "intended_status": "passed",
        "experiences": 0
      }
    }
  ],
  "usage": {
    "calls": 5,
    "input_tokens": 27999,
    "output_tokens": 1665,
    "cached_input_tokens": 9728,
    "records": [
      {
        "role": "interpreter",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "7f3994cb-8963-4313-9be7-4d6f329a2a9e",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "16de8db275e4b3d0fac5c9fae96178e5d6dc4952438ac063b5a103dd7368a896",
        "response_sha256": "2bc271afd276792277c806a64936ec01d996507560efc00d8a936201ee2d1a12",
        "input_tokens": 479,
        "output_tokens": 313,
        "seconds": 12.374,
        "finish_reason": "stop"
      },
      {
        "role": "planner",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "84e7f8f7-a6ac-46d4-8dfc-68dcdf3b3e5b",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "a419c443dcf407a5332aab749361c0c678000132ea516fb93ceba866813dd49d",
        "response_sha256": "c8c2be45cbd81f6a089d7704224d92382140cd7d837fbd590c4ab4eca1a22d4d",
        "input_tokens": 8563,
        "output_tokens": 194,
        "seconds": 1.927,
        "finish_reason": "stop"
      },
      {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "c0703d93-8d0b-4999-a038-dd63423525ea",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "01c9d9b8c0c71bdffa7feee6d1dd2f176e1ece09f78af8890a42da2e3c757cf0",
        "response_sha256": "015008231da86c3215bf92e5df6550d9a3ade4ab07031f8ceb25534dc0b91ea8",
        "input_tokens": 9102,
        "output_tokens": 252,
        "seconds": 7.199,
        "finish_reason": "stop"
      },
      {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "6fd1f110-d18c-4e78-852e-f7f4eb9a7c90",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "6c3290757b8a8c5a57805558ba5f99ca09b109b9a6f4da7e95d76007f0a1ee44",
        "response_sha256": "e77d2a3af3bc04018b0c0c4bfc6cbdd19bdfbfe5bc59bea02873c64ed9e20f69",
        "input_tokens": 9112,
        "output_tokens": 295,
        "seconds": 2.078,
        "finish_reason": "stop"
      },
      {
        "role": "curator",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "1723dea5-b155-406a-8d8c-e3905897b0a7",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "54ad594125c9697af9a86e6fee6d2627087edc9944153eae8f8d3ec590923be0",
        "response_sha256": "c7e5f50ec8d0ef32bafa11286d43a65c6f418db4a24f194a32538c25004ac802",
        "input_tokens": 743,
        "output_tokens": 611,
        "seconds": 3.49,
        "finish_reason": "stop"
      }
    ]
  },
  "warnings": [
    "验证集成绩，不是最终测试成绩。",
    "受限AST构造器程序，不是任意Python或Docker操作系统沙箱。",
    "未提供具体候选方案定义，需在实现时明确两个候选并保持可比性",
    "未提供验证集划分细节，需采用固定种子 42 的可复现划分",
    "若请求的整轮墙钟预算低于 10 秒，将视为不兼容并回退到 10 秒"
  ],
  "search_tree": [
    {
      "candidate_id": "bank_logistic_balanced_v1",
      "parent_id": null,
      "status": "passed",
      "average_precision": 0.1807589966629477,
      "pruned": false,
      "pruned_reason": null
    },
    {
      "candidate_id": "bank_forest_balanced_v1",
      "parent_id": null,
      "status": "passed",
      "average_precision": 0.12825103811039737,
      "pruned": false,
      "pruned_reason": null
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
    "objective": "在银行定期存款订购的二分类任务中，仅使用通话前可得特征（排除 duration），比较两个候选方案，并以验证集平均精度（AP）选择最终方案，同时输出来源、检查、资源和修复记录。",
    "constraints": [
      "仅使用 task_spec 中列出的特征：age, job, marital, education, default, housing, loan, pdays, previous, poutcome",
      "禁止使用 duration 特征",
      "正类标签为 yes",
      "主指标为验证集 average_precision",
      "随机种子固定为 42",
      "资源限制：CPU 2 核、内存 2048 MiB、超时 120 秒",
      "不得修改 task_spec",
      "不得承诺在无 client ID 的情况下进行未见客户端分离"
    ],
    "assumptions": [
      "两个候选方案均基于同一数据集 bank 和同一特征策略 precontact_conservative_v1",
      "验证集 AP 用于模型选择，且验证集划分方式在两个候选间保持一致",
      "输出记录中的来源、检查、资源和修复记录指可审计的元数据，而非私有推理过程"
    ],
    "warnings": [
      "未提供具体候选方案定义，需在实现时明确两个候选并保持可比性",
      "未提供验证集划分细节，需采用固定种子 42 的可复现划分",
      "若请求的整轮墙钟预算低于 10 秒，将视为不兼容并回退到 10 秒"
    ],
    "incompatible_requests": [],
    "requested_run_seconds": null
  },
  "evidence": [
    {
      "capability_id": "bank-precontact-policy",
      "confidence": 1.0,
      "created_at": "2026-09-28T11:23:24.516283+00:00",
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
      "score": 4.28565,
      "lexical_score": 3.434014,
      "graph_score": 0.851635,
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
          "bonus": 0.6593307069537073
        },
        {
          "seed": "capability:average-precision:v1",
          "hops": [
            {
              "from": "capability:average-precision:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-target:v1"
            },
            {
              "from": "capability:bank-target:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-precontact-policy:v1"
            }
          ],
          "bonus": 0.19230478952816465
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
      "created_at": "2026-09-28T11:23:24.516559+00:00",
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
      "score": 3.232936,
      "lexical_score": 1.648327,
      "graph_score": 1.58461,
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
          "bonus": 1.2000000000000002
        },
        {
          "seed": "capability:average-precision:v1",
          "hops": [
            {
              "from": "capability:average-precision:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-target:v1"
            }
          ],
          "bonus": 0.3846095790563293
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
      "created_at": "2026-09-28T11:23:24.516769+00:00",
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
      "score": 2.491189,
      "lexical_score": 0.961524,
      "graph_score": 1.529665,
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
          "bonus": 1.2000000000000002
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
          "bonus": 0.32966535347685366
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
      "score": 2.220855,
      "lexical_score": 0.961524,
      "graph_score": 1.259331,
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
          "bonus": 0.6000000000000001
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
          "bonus": 0.6593307069537073
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
      "score": 1.918661,
      "lexical_score": 0.274721,
      "graph_score": 1.64394,
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
          "bonus": 0.6000000000000001
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
          "bonus": 0.6593307069537073
        },
        {
          "seed": "capability:average-precision:v1",
          "hops": [
            {
              "from": "capability:average-precision:v1",
              "relation": "REQUIRES",
              "to": "capability:probability-logistic:v1"
            }
          ],
          "bonus": 0.3846095790563293
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
      "capability_id": "hist-gradient-boosting",
      "confidence": 1.0,
      "created_at": "2026-09-28T11:23:24.518194+00:00",
      "dependencies": [
        "Python >=3.10",
        "scikit-learn"
      ],
      "evidence": [
        {
          "content_sha256": "f88ec15b1f861d6ac8517b8e3e5348bb4522ebe3127c5d89127502078b427fdc",
          "license": "BSD-3-Clause",
          "locator": {
            "imports": [
              "import itertools",
              "from abc import ABC, abstractmethod",
              "from contextlib import contextmanager, nullcontext, suppress",
              "from functools import partial",
              "from numbers import Integral, Real",
              "from time import time",
              "import numpy as np",
              "from ..._loss.loss import _LOSSES, BaseLoss, HalfBinomialLoss, HalfGammaLoss, HalfMultinomialLoss, HalfPoissonLoss, PinballLoss",
              "from ...base import BaseEstimator, ClassifierMixin, RegressorMixin, _fit_context, is_classifier",
              "from ...compose import ColumnTransformer",
              "from ...metrics import check_scoring",
              "from ...metrics._scorer import _SCORERS",
              "from ...model_selection import train_test_split",
              "from ...preprocessing import FunctionTransformer, LabelEncoder, OrdinalEncoder",
              "from ...utils import check_random_state, compute_sample_weight, resample",
              "from ...utils._missing import is_scalar_nan",
              "from ...utils._openmp_helpers import _openmp_effective_n_threads",
              "from ...utils._param_validation import Interval, RealNotInt, StrOptions",
              "from ...utils.multiclass import check_classification_targets",
              "from ...utils.validation import _check_monotonic_cst, _check_sample_weight, _check_y, _is_pandas_df, check_array, check_consistent_length, check_is_fitted, validate_data",
              "from ._gradient_boosting import _update_raw_predictions",
              "from .binning import _BinMapper",
              "from .common import G_H_DTYPE, X_DTYPE, Y_DTYPE",
              "from .grower import TreeGrower"
            ],
            "line_end": 2371,
            "line_start": 1873,
            "methods": [
              "__init__",
              "_finalize_sample_weight",
              "predict",
              "staged_predict",
              "predict_proba",
              "staged_predict_proba",
              "decision_function",
              "staged_decision_function",
              "_encode_y",
              "_encode_y_val",
              "_get_loss"
            ],
            "parse_mode": "ast-only",
            "path": "/root/algorithm-capability-factory/.venv/lib/python3.10/site-packages/sklearn/ensemble/_hist_gradient_boosting/gradient_boosting.py",
            "relative_path": "sklearn/ensemble/_hist_gradient_boosting/gradient_boosting.py",
            "signature": "class HistGradientBoostingClassifier(ClassifierMixin, BaseHistGradientBoosting):\n    def __init__(self, loss='log_loss', *, learning_rate=0.1, max_iter=100, max_leaf_nodes=31, max_depth=None, min_samples_leaf=20, l2_regularization=0.0, max_features=1.0, max_bins=255, categorical_features='from_dtype', monotonic_cst=None, interaction_cst=None, warm_start=False, early_stopping='auto', scoring='loss', validation_fraction=0.1, n_iter_no_change=10, tol=1e-07, verbose=0, random_state=None, class_weight=None)",
            "symbol": "HistGradientBoostingClassifier"
          },
          "revision": "1.7.2",
          "source_id": "src-8bb03b8a4d6fcff5a1d76293",
          "uri": "https://github.com/scikit-learn/scikit-learn/blob/1.7.2/sklearn/ensemble/_hist_gradient_boosting/gradient_boosting.py"
        }
      ],
      "extraction_method": "curated-source-grounded",
      "id": "hist-gradient-boosting",
      "input_schema": {
        "task_types": [
          "tabular_binary_classification"
        ],
        "type": "features"
      },
      "name": "直方图梯度提升分类候选",
      "origin": "manual_seed",
      "output_schema": {
        "type": "implementation-guidance"
      },
      "preconditions": [],
      "related": [
        "mixed-type-columns",
        "average-precision"
      ],
      "status": "extracted",
      "summary": "HistGradientBoostingClassifier 提供直方图梯度提升分类和概率预测。与预处理器组合时明确验证输入表示、类别编码和内存预算；它是独立候选，必须在相同验证协议下比较。",
      "tags": [
        "HistGradientBoostingClassifier",
        "提升",
        "直方图",
        "非线性"
      ],
      "task_types": [
        "tabular_binary_classification"
      ],
      "uses": [
        {
          "kind": "Algorithm",
          "label": "HistGradientBoostingClassifier"
        }
      ],
      "version": 1,
      "score": 1.538438,
      "lexical_score": 0.824163,
      "graph_score": 0.714275,
      "evidence_path": [
        {
          "seed": "capability:bank-target:v1",
          "hops": [
            {
              "from": "capability:bank-target:v1",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            },
            {
              "from": "capability:average-precision:v1",
              "relation": "REQUIRES",
              "to": "capability:hist-gradient-boosting:v1"
            }
          ],
          "bonus": 0.32966535347685366
        },
        {
          "seed": "capability:average-precision:v1",
          "hops": [
            {
              "from": "capability:average-precision:v1",
              "relation": "REQUIRES",
              "to": "capability:hist-gradient-boosting:v1"
            }
          ],
          "bonus": 0.3846095790563293
        }
      ],
      "graph_used": true,
      "source_locator": [
        {
          "imports": [
            "import itertools",
            "from abc import ABC, abstractmethod",
            "from contextlib import contextmanager, nullcontext, suppress",
            "from functools import partial",
            "from numbers import Integral, Real",
            "from time import time",
            "import numpy as np",
            "from ..._loss.loss import _LOSSES, BaseLoss, HalfBinomialLoss, HalfGammaLoss, HalfMultinomialLoss, HalfPoissonLoss, PinballLoss",
            "from ...base import BaseEstimator, ClassifierMixin, RegressorMixin, _fit_context, is_classifier",
            "from ...compose import ColumnTransformer",
            "from ...metrics import check_scoring",
            "from ...metrics._scorer import _SCORERS",
            "from ...model_selection import train_test_split",
            "from ...preprocessing import FunctionTransformer, LabelEncoder, OrdinalEncoder",
            "from ...utils import check_random_state, compute_sample_weight, resample",
            "from ...utils._missing import is_scalar_nan",
            "from ...utils._openmp_helpers import _openmp_effective_n_threads",
            "from ...utils._param_validation import Interval, RealNotInt, StrOptions",
            "from ...utils.multiclass import check_classification_targets",
            "from ...utils.validation import _check_monotonic_cst, _check_sample_weight, _check_y, _is_pandas_df, check_array, check_consistent_length, check_is_fitted, validate_data",
            "from ._gradient_boosting import _update_raw_predictions",
            "from .binning import _BinMapper",
            "from .common import G_H_DTYPE, X_DTYPE, Y_DTYPE",
            "from .grower import TreeGrower"
          ],
          "line_end": 2371,
          "line_start": 1873,
          "methods": [
            "__init__",
            "_finalize_sample_weight",
            "predict",
            "staged_predict",
            "predict_proba",
            "staged_predict_proba",
            "decision_function",
            "staged_decision_function",
            "_encode_y",
            "_encode_y_val",
            "_get_loss"
          ],
          "parse_mode": "ast-only",
          "path": "/root/algorithm-capability-factory/.venv/lib/python3.10/site-packages/sklearn/ensemble/_hist_gradient_boosting/gradient_boosting.py",
          "relative_path": "sklearn/ensemble/_hist_gradient_boosting/gradient_boosting.py",
          "signature": "class HistGradientBoostingClassifier(ClassifierMixin, BaseHistGradientBoosting):\n    def __init__(self, loss='log_loss', *, learning_rate=0.1, max_iter=100, max_leaf_nodes=31, max_depth=None, min_samples_leaf=20, l2_regularization=0.0, max_features=1.0, max_bins=255, categorical_features='from_dtype', monotonic_cst=None, interaction_cst=None, warm_start=False, early_stopping='auto', scoring='loss', validation_fraction=0.1, n_iter_no_change=10, tol=1e-07, verbose=0, random_state=None, class_weight=None)",
          "symbol": "HistGradientBoostingClassifier"
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
    "summary": "在仅验证集（validation_only，8238 行，正例率 0.1107）上，候选 bank_logistic_balanced_v1 与 bank_forest_balanced_v1 均通过状态检查，且均未在封存测试集上评分（sealed_test_scored=false）。bank_logistic_balanced_v1 的 average_precision 为 0.1808，较 dummy 基线 0.1107 提升 0.0701，roc_auc 为 0.6093，lift_at_10pct 为 1.9842，precision_at_10pct 为 0.2197，recall_at_10pct 为 0.1985，f1（阈值 0.5）为 0.2288。bank_forest_balanced_v1 的 average_precision 为 0.1283，较 dummy 提升 0.0175，roc_auc 为 0.5524，lift_at_10pct 为 1.3155，precision_at_10pct 为 0.1456，recall_at_10pct 为 0.1316，f1（阈值 0.5）为 0.1808。基于这些独立测量指标，bank_logistic_balanced_v1 在排序与 top-10% 定位上优于 bank_forest_balanced_v1，因此被选为 selected_candidate_id。检索到的能力证据包括 bank-precontact-policy、bank-target、bank-ordered-split、average-precision、probability-logistic、hist-gradient-boosting，用于说明数据切分、目标定义与指标口径。",
    "limitations": [
      "以上数值均为验证集（validation_only）结果，不是最终测试集性能；两个候选的 sealed_test_scored 均为 false，因此不能据此推断泛化或上线表现。",
      "约束式 AST 执行仅用于受控的候选代码评估，不等同于通用操作系统沙箱，不能保证对任意代码或外部依赖的隔离安全。",
      "模型选择（bank_logistic_balanced_v1 优于 bank_forest_balanced_v1）只反映该验证协议下的排序指标差异，不证明任何营销因果提升或业务增量。",
      "两个候选均使用 classification_threshold=0.5 与 original_validation_row_order 作为排名并列处理，阈值与并列策略变化可能改变 f1、precision、recall 等指标。",
      "bank_forest_balanced_v1 虽通过状态检查，但其 average_precision 提升仅 0.0175、roc_auc 0.5524，接近随机水平，不应被隐藏或忽略。",
      "验证集正例率 0.1107 且 top_10pct_count=824，样本规模有限，指标存在抽样波动，未提供置信区间或重复实验。"
    ]
  },
  "finished_at": "2026-09-28T13:59:19.233018+00:00",
  "timing": {
    "wall_seconds": 37.641,
    "budget_seconds": 900.0,
    "request_ceiling_seconds": 900
  },
  "report_paths": {}
}
````

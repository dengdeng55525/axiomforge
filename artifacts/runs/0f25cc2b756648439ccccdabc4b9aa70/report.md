# 算法能力验证报告

指标与状态来自原始验证事实；缺失项不填零、不推断通过。

模式由原始报告的 mode 字段说明：mock 为模拟，replay 为历史回放。

````json
{
  "schema_version": "1.0",
  "run_id": "0f25cc2b756648439ccccdabc4b9aa70",
  "status": "passed",
  "mode": "real",
  "provider": "deepseek",
  "description": "请在通话前预测银行客户订购概率，禁止duration，初始比较逻辑回归和随机森林，再以宽度2的Beam Search扩展参数，最多6个不同候选；报告AP、前10%名单效果和资源消耗。",
  "dataset_id": "bank",
  "created_at": "2026-09-28T11:39:55.630335+00:00",
  "request": {
    "description": "请在通话前预测银行客户订购概率，禁止duration，初始比较逻辑回归和随机森林，再以宽度2的Beam Search扩展参数，最多6个不同候选；报告AP、前10%名单效果和资源消耗。",
    "dataset_id": "bank",
    "provider": "deepseek",
    "max_candidates": 6,
    "max_repairs": 2,
    "use_graph": true,
    "use_retrieval": true,
    "orchestration": "multi_role",
    "search": "beam",
    "inject_failure": true,
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
      "candidate_id": "bank_logistic_default",
      "plan": {
        "candidate_id": "bank_logistic_default",
        "algorithm": "logistic",
        "variant": "default",
        "rationale": "初始比较的逻辑回归基线，使用 predict_proba 输出正类概率，配合通话前保守特征白名单与顺序留出协议，以 AP 为主指标。",
        "evidence_ids": [
          "probability-logistic",
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "bank-ordered-split"
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
        "worker_pid": 20817,
        "wall_seconds": 1.1033587239217013,
        "fit_seconds": 0.07485550991259515,
        "predict_seconds": 0.014559353003278375,
        "worker_wall_seconds": 0.9214911779854447,
        "peak_rss_mib": 227.546875,
        "cpu_seconds": 1.220445,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 1.842276860959828
      },
      "repairs": [
        {
          "error_type": "CodePolicyError",
          "diagnosis": "The source defines the entry function as broken_pipeline instead of the required name build_pipeline(task_spec), violating the source_policy check that exactly one function named build_pipeline(task_spec) must be defined.",
          "fix": "Rename the function definition from 'def broken_pipeline(task_spec):' to 'def build_pipeline(task_spec):' so the module exposes exactly one function with the required name and signature.",
          "repairable": true,
          "attempt": 1,
          "before_hash": "b4dd5f8eebd665f9e6f4a06eb7a6ae7d0fa3a16c2d724e71bce32c7552233384",
          "after_hash": "e674bef0808a2926a4f2fc8127f09a0c5c1a3b575582f73703c026fb4a8961c1",
          "validated": true
        }
      ],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "b4dd5f8eebd665f9e6f4a06eb7a6ae7d0fa3a16c2d724e71bce32c7552233384",
          "code_path": "candidates/bank_logistic_default/attempt_0/model.py",
          "status": "failed",
          "error": {
            "type": "CodePolicyError",
            "message": "Define exactly one function named build_pipeline(task_spec)",
            "repairable": true,
            "stage": "source_policy"
          },
          "checks": [
            {
              "name": "source_policy",
              "passed": false,
              "mandatory": true,
              "detail": "Define exactly one function named build_pipeline(task_spec)"
            }
          ],
          "metrics": {},
          "resources": {
            "limits": {
              "timeout_s": 120.0,
              "memory_mib": 2048,
              "cpu_cores": 2
            },
            "total_seconds": 0.000879945931956172
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
          "model_metadata": null
        },
        {
          "attempt": 1,
          "code_sha256": "e674bef0808a2926a4f2fc8127f09a0c5c1a3b575582f73703c026fb4a8961c1",
          "code_path": "candidates/bank_logistic_default/attempt_1/model.py",
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
            "worker_pid": 20817,
            "wall_seconds": 1.1033587239217013,
            "fit_seconds": 0.07485550991259515,
            "predict_seconds": 0.014559353003278375,
            "worker_wall_seconds": 0.9214911779854447,
            "peak_rss_mib": 227.546875,
            "cpu_seconds": 1.220445,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 1.842276860959828
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
      "artifact_id": "bank_logistic_default",
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
      "code_sha256": "e674bef0808a2926a4f2fc8127f09a0c5c1a3b575582f73703c026fb4a8961c1",
      "code_path": "candidates/bank_logistic_default/attempt_1/model.py",
      "explanation": "Renamed the entry function to build_pipeline(task_spec) per the review fix, keeping the precontact numeric impute/scale plus OneHotEncoder(handle_unknown='ignore') ColumnTransformer and LogisticRegression(max_iter=1000, random_state=seed) baseline that matches the plan's default logistic variant and predict_proba requirement."
    },
    {
      "candidate_id": "bank_forest_default",
      "plan": {
        "candidate_id": "bank_forest_default",
        "algorithm": "forest",
        "variant": "default",
        "rationale": "初始比较的随机森林基线，固定 random_state 并限制树数量与 n_jobs 以适配 CPU/内存预算，作为非线性对照候选。",
        "evidence_ids": [
          "random-forest",
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "bank-ordered-split"
        ],
        "parent_id": null
      },
      "status": "passed",
      "metrics": {
        "average_precision": 0.1277624798874739,
        "roc_auc": 0.5517438790465106,
        "f1_threshold_0_5": 0.0,
        "precision_at_10pct": 0.13592233009708737,
        "recall_at_10pct": 0.12280701754385964,
        "lift_at_10pct": 1.227772100153296,
        "validation_positive_rate": 0.11070648215586307,
        "top_10pct_count": 824,
        "validation_rows": 8238,
        "classification_threshold": 0.5,
        "evaluation_split": "validation_only",
        "sealed_test_scored": false,
        "ranking_tie_break": "original_validation_row_order",
        "dummy_average_precision": 0.11070648215586307,
        "ap_improvement_over_dummy": 0.017055997731610845
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
        "worker_pid": 20968,
        "wall_seconds": 4.6101055960170925,
        "fit_seconds": 3.3276293789967895,
        "predict_seconds": 0.11086177197284997,
        "worker_wall_seconds": 4.392528473865241,
        "peak_rss_mib": 244.3515625,
        "cpu_seconds": 7.832573,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 4.770244590006769
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "bc1719eb0ba8dc09660ac5c1b80b14a5382e9cf775d69cdd104ae4d1e51f5bb8",
          "code_path": "candidates/bank_forest_default/attempt_0/model.py",
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
            "average_precision": 0.1277624798874739,
            "roc_auc": 0.5517438790465106,
            "f1_threshold_0_5": 0.0,
            "precision_at_10pct": 0.13592233009708737,
            "recall_at_10pct": 0.12280701754385964,
            "lift_at_10pct": 1.227772100153296,
            "validation_positive_rate": 0.11070648215586307,
            "top_10pct_count": 824,
            "validation_rows": 8238,
            "classification_threshold": 0.5,
            "evaluation_split": "validation_only",
            "sealed_test_scored": false,
            "ranking_tie_break": "original_validation_row_order",
            "dummy_average_precision": 0.11070648215586307,
            "ap_improvement_over_dummy": 0.017055997731610845
          },
          "resources": {
            "limits": {
              "timeout_s": 120.0,
              "memory_mib": 2048,
              "cpu_cores": 2
            },
            "worker_pid": 20968,
            "wall_seconds": 4.6101055960170925,
            "fit_seconds": 3.3276293789967895,
            "predict_seconds": 0.11086177197284997,
            "worker_wall_seconds": 4.392528473865241,
            "peak_rss_mib": 244.3515625,
            "cpu_seconds": 7.832573,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 4.770244590006769
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
              "max_depth": 16,
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
      "artifact_id": "bank_forest_default",
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
          "max_depth": 16,
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
      "code_sha256": "bc1719eb0ba8dc09660ac5c1b80b14a5382e9cf775d69cdd104ae4d1e51f5bb8",
      "code_path": "candidates/bank_forest_default/attempt_0/model.py",
      "explanation": "Implements the planned default random-forest baseline on the precontact conservative feature whitelist (no duration/target), with median-imputed scaled numerics, unknown-tolerant one-hot categoricals, and a CPU-bounded forest (200 trees, depth 16, n_jobs 2, seed 42) exposing predict_proba for average-precision evaluation."
    },
    {
      "candidate_id": "bank_logistic_balanced",
      "plan": {
        "candidate_id": "bank_logistic_balanced",
        "algorithm": "logistic",
        "variant": "balanced",
        "rationale": "Child of bank_logistic_default using class_weight balanced to counter the ~11% positive rate; keeps precontact whitelist, ordered split, and AP as primary metric.",
        "evidence_ids": [
          "probability-logistic",
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "bank-ordered-split"
        ],
        "parent_id": "bank_logistic_default"
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
        "worker_pid": 21055,
        "wall_seconds": 1.1533953589387238,
        "fit_seconds": 0.11571653210557997,
        "predict_seconds": 0.014856701949611306,
        "worker_wall_seconds": 0.9609093400649726,
        "peak_rss_mib": 225.6953125,
        "cpu_seconds": 1.285671,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 1.3075315121095628
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "df78067d263ab32d9f8a90daece77619edf41852761086dcba8b1cbcc2008aef",
          "code_path": "candidates/bank_logistic_balanced/attempt_0/model.py",
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
            "worker_pid": 21055,
            "wall_seconds": 1.1533953589387238,
            "fit_seconds": 0.11571653210557997,
            "predict_seconds": 0.014856701949611306,
            "worker_wall_seconds": 0.9609093400649726,
            "peak_rss_mib": 225.6953125,
            "cpu_seconds": 1.285671,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 1.3075315121095628
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
      "artifact_id": "bank_logistic_balanced",
      "parent_id": "bank_logistic_default",
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
      "code_sha256": "df78067d263ab32d9f8a90daece77619edf41852761086dcba8b1cbcc2008aef",
      "code_path": "candidates/bank_logistic_balanced/attempt_0/model.py",
      "explanation": "Child of bank_logistic_default keeps the precontact whitelist numeric/categorical ColumnTransformer and adds class_weight='balanced' per the balanced variant, with LogisticRegression max_iter=1000 and random_state from task_spec['seed']."
    },
    {
      "candidate_id": "bank_logistic_regularized",
      "plan": {
        "candidate_id": "bank_logistic_regularized",
        "algorithm": "logistic",
        "variant": "regularized",
        "rationale": "Child of bank_logistic_default with stronger regularization to control variance on the small precontact feature set; same protocol and AP evaluation.",
        "evidence_ids": [
          "probability-logistic",
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "bank-ordered-split"
        ],
        "parent_id": "bank_logistic_default"
      },
      "status": "passed",
      "metrics": {
        "average_precision": 0.18154959172679347,
        "roc_auc": 0.6065676172584067,
        "f1_threshold_0_5": 0.0,
        "precision_at_10pct": 0.22815533980582525,
        "recall_at_10pct": 0.20614035087719298,
        "lift_at_10pct": 2.060903168114461,
        "validation_positive_rate": 0.11070648215586307,
        "top_10pct_count": 824,
        "validation_rows": 8238,
        "classification_threshold": 0.5,
        "evaluation_split": "validation_only",
        "sealed_test_scored": false,
        "ranking_tie_break": "original_validation_row_order",
        "dummy_average_precision": 0.11070648215586307,
        "ap_improvement_over_dummy": 0.0708431095709304
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
        "worker_pid": 21096,
        "wall_seconds": 1.1533400560729206,
        "fit_seconds": 0.08749197400175035,
        "predict_seconds": 0.014644791837781668,
        "worker_wall_seconds": 0.9350068839266896,
        "peak_rss_mib": 227.05859375,
        "cpu_seconds": 1.231499,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 1.3053957931697369
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "ff866df73a58fa0d2e8b0ce41a0342a889fce756d005a9ad325bcf8bc9ad68db",
          "code_path": "candidates/bank_logistic_regularized/attempt_0/model.py",
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
            "average_precision": 0.18154959172679347,
            "roc_auc": 0.6065676172584067,
            "f1_threshold_0_5": 0.0,
            "precision_at_10pct": 0.22815533980582525,
            "recall_at_10pct": 0.20614035087719298,
            "lift_at_10pct": 2.060903168114461,
            "validation_positive_rate": 0.11070648215586307,
            "top_10pct_count": 824,
            "validation_rows": 8238,
            "classification_threshold": 0.5,
            "evaluation_split": "validation_only",
            "sealed_test_scored": false,
            "ranking_tie_break": "original_validation_row_order",
            "dummy_average_precision": 0.11070648215586307,
            "ap_improvement_over_dummy": 0.0708431095709304
          },
          "resources": {
            "limits": {
              "timeout_s": 120.0,
              "memory_mib": 2048,
              "cpu_cores": 2
            },
            "worker_pid": 21096,
            "wall_seconds": 1.1533400560729206,
            "fit_seconds": 0.08749197400175035,
            "predict_seconds": 0.014644791837781668,
            "worker_wall_seconds": 0.9350068839266896,
            "peak_rss_mib": 227.05859375,
            "cpu_seconds": 1.231499,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 1.3053957931697369
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
              "C": 0.1,
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
      "artifact_id": "bank_logistic_regularized",
      "parent_id": "bank_logistic_default",
      "error": null,
      "quality_status": "above_prevalence",
      "model_metadata": {
        "actual_algorithm": "logistic",
        "classifier_class": "LogisticRegression",
        "classifier_path": [
          "model"
        ],
        "classifier_parameters": {
          "C": 0.1,
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
      "code_sha256": "ff866df73a58fa0d2e8b0ce41a0342a889fce756d005a9ad325bcf8bc9ad68db",
      "code_path": "candidates/bank_logistic_regularized/attempt_0/model.py",
      "explanation": "Implements the regularized logistic variant by lowering C to 0.1 on the parent's precontact numeric/categorical ColumnTransformer, keeping median imputation, scaling, handle_unknown='ignore' one-hot encoding, max_iter=1000 and seed 42, with no duration/target leakage."
    },
    {
      "candidate_id": "bank_forest_balanced",
      "plan": {
        "candidate_id": "bank_forest_balanced",
        "algorithm": "forest",
        "variant": "balanced",
        "rationale": "Child of bank_forest_default using class_weight balanced to address class imbalance while keeping fixed random_state and bounded n_jobs for CPU/memory limits.",
        "evidence_ids": [
          "random-forest",
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "bank-ordered-split"
        ],
        "parent_id": "bank_forest_default"
      },
      "status": "passed",
      "metrics": {
        "average_precision": 0.12307938706482693,
        "roc_auc": 0.5357817446633235,
        "f1_threshold_0_5": 0.15309734513274337,
        "precision_at_10pct": 0.1395631067961165,
        "recall_at_10pct": 0.12609649122807018,
        "lift_at_10pct": 1.2606588528359735,
        "validation_positive_rate": 0.11070648215586307,
        "top_10pct_count": 824,
        "validation_rows": 8238,
        "classification_threshold": 0.5,
        "evaluation_split": "validation_only",
        "sealed_test_scored": false,
        "ranking_tie_break": "original_validation_row_order",
        "dummy_average_precision": 0.11070648215586307,
        "ap_improvement_over_dummy": 0.012372904908963867
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
        "worker_pid": 21141,
        "wall_seconds": 4.710063109174371,
        "fit_seconds": 3.403551176888868,
        "predict_seconds": 0.10380939906463027,
        "worker_wall_seconds": 4.473010438960046,
        "peak_rss_mib": 240.83984375,
        "cpu_seconds": 7.970299,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 4.857213268056512
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "608f6098d0793224e4b0deac6c2baf11521a5fcbdd2f3f1dd781aedcb8225c83",
          "code_path": "candidates/bank_forest_balanced/attempt_0/model.py",
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
            "average_precision": 0.12307938706482693,
            "roc_auc": 0.5357817446633235,
            "f1_threshold_0_5": 0.15309734513274337,
            "precision_at_10pct": 0.1395631067961165,
            "recall_at_10pct": 0.12609649122807018,
            "lift_at_10pct": 1.2606588528359735,
            "validation_positive_rate": 0.11070648215586307,
            "top_10pct_count": 824,
            "validation_rows": 8238,
            "classification_threshold": 0.5,
            "evaluation_split": "validation_only",
            "sealed_test_scored": false,
            "ranking_tie_break": "original_validation_row_order",
            "dummy_average_precision": 0.11070648215586307,
            "ap_improvement_over_dummy": 0.012372904908963867
          },
          "resources": {
            "limits": {
              "timeout_s": 120.0,
              "memory_mib": 2048,
              "cpu_cores": 2
            },
            "worker_pid": 21141,
            "wall_seconds": 4.710063109174371,
            "fit_seconds": 3.403551176888868,
            "predict_seconds": 0.10380939906463027,
            "worker_wall_seconds": 4.473010438960046,
            "peak_rss_mib": 240.83984375,
            "cpu_seconds": 7.970299,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 4.857213268056512
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
              "max_depth": 16,
              "min_samples_leaf": 5,
              "n_jobs": 2,
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
              "RandomForestClassifier"
            ],
            "constructor_count": 7,
            "source": "independently_parsed_constructor_plan"
          }
        }
      ],
      "artifact_id": "bank_forest_balanced",
      "parent_id": "bank_forest_default",
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
          "max_depth": 16,
          "min_samples_leaf": 5,
          "n_jobs": 2,
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
      "code_sha256": "608f6098d0793224e4b0deac6c2baf11521a5fcbdd2f3f1dd781aedcb8225c83",
      "code_path": "candidates/bank_forest_balanced/attempt_0/model.py",
      "explanation": "Keeps the parent forest pipeline (median impute + scale numeric, OneHotEncoder handle_unknown='ignore' categorical, precontact feature lists) and applies the balanced variant via class_weight='balanced' with bounded n_estimators=200, max_depth=16, n_jobs=2 and random_state from task_spec['seed']."
    },
    {
      "candidate_id": "bank_forest_shallower",
      "plan": {
        "candidate_id": "bank_forest_shallower",
        "algorithm": "forest",
        "variant": "shallower",
        "rationale": "Child of bank_forest_default with reduced depth to lower resource consumption and variance, providing a cheaper nonlinear comparison under the same protocol.",
        "evidence_ids": [
          "random-forest",
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "bank-ordered-split"
        ],
        "parent_id": "bank_forest_default"
      },
      "status": "passed",
      "metrics": {
        "average_precision": 0.14985341617481288,
        "roc_auc": 0.5884300867853499,
        "f1_threshold_0_5": 0.0,
        "precision_at_10pct": 0.17111650485436894,
        "recall_at_10pct": 0.15460526315789475,
        "lift_at_10pct": 1.5456773760858458,
        "validation_positive_rate": 0.11070648215586307,
        "top_10pct_count": 824,
        "validation_rows": 8238,
        "classification_threshold": 0.5,
        "evaluation_split": "validation_only",
        "sealed_test_scored": false,
        "ranking_tie_break": "original_validation_row_order",
        "dummy_average_precision": 0.11070648215586307,
        "ap_improvement_over_dummy": 0.03914693401894981
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
        "worker_pid": 21227,
        "wall_seconds": 2.6060662078671157,
        "fit_seconds": 1.3508297689259052,
        "predict_seconds": 0.061804953031241894,
        "worker_wall_seconds": 2.3781838149297982,
        "peak_rss_mib": 231.3671875,
        "cpu_seconds": 3.7813169999999996,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 1.1102230246251565e-16,
        "total_seconds": 2.7931975631508976
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "e32b8fea3b336108b961d4a8995d694e98d2c78893c6cc12b1b7fbac89369453",
          "code_path": "candidates/bank_forest_shallower/attempt_0/model.py",
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
            "average_precision": 0.14985341617481288,
            "roc_auc": 0.5884300867853499,
            "f1_threshold_0_5": 0.0,
            "precision_at_10pct": 0.17111650485436894,
            "recall_at_10pct": 0.15460526315789475,
            "lift_at_10pct": 1.5456773760858458,
            "validation_positive_rate": 0.11070648215586307,
            "top_10pct_count": 824,
            "validation_rows": 8238,
            "classification_threshold": 0.5,
            "evaluation_split": "validation_only",
            "sealed_test_scored": false,
            "ranking_tie_break": "original_validation_row_order",
            "dummy_average_precision": 0.11070648215586307,
            "ap_improvement_over_dummy": 0.03914693401894981
          },
          "resources": {
            "limits": {
              "timeout_s": 120.0,
              "memory_mib": 2048,
              "cpu_cores": 2
            },
            "worker_pid": 21227,
            "wall_seconds": 2.6060662078671157,
            "fit_seconds": 1.3508297689259052,
            "predict_seconds": 0.061804953031241894,
            "worker_wall_seconds": 2.3781838149297982,
            "peak_rss_mib": 231.3671875,
            "cpu_seconds": 3.7813169999999996,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 1.1102230246251565e-16,
            "total_seconds": 2.7931975631508976
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
              "max_depth": 8,
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
      "artifact_id": "bank_forest_shallower",
      "parent_id": "bank_forest_default",
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
          "max_depth": 8,
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
      "code_sha256": "e32b8fea3b336108b961d4a8995d694e98d2c78893c6cc12b1b7fbac89369453",
      "code_path": "candidates/bank_forest_shallower/attempt_0/model.py",
      "explanation": "Implements the shallower forest variant by lowering max_depth from the parent's 16 to 8 while keeping the precontact numeric/categorical preprocessing, n_estimators=200, n_jobs=2, and seed, consistent with the random-forest and bank-precontact-policy evidence."
    }
  ],
  "selected_candidate_id": "bank_logistic_default",
  "events": [
    {
      "sequence": 0,
      "event_type": "RECEIVED",
      "type": "RECEIVED",
      "created_at": "2026-09-28T11:39:55.759224+00:00",
      "data": {
        "mode": "real",
        "model": "deepseek-flash"
      }
    },
    {
      "sequence": 1,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T11:40:04.039154+00:00",
      "data": {
        "role": "interpreter",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "ed2cb921-24a4-4c1d-9ee7-4b3884609175",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "61fab09221ac55c44241af53cdaf72f17de187aeeabaa297a815965889b2dcac",
        "response_sha256": "de299af255f10fbd5bd231f1c4a1e1e6f091d77723659634c6c3c47197780b26",
        "input_tokens": 421,
        "output_tokens": 402,
        "seconds": 7.791,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 2,
      "event_type": "SPEC_VALIDATED",
      "type": "SPEC_VALIDATED",
      "created_at": "2026-09-28T11:40:04.355146+00:00",
      "data": {
        "task_type": "tabular_binary_classification",
        "assumptions": [
          "数据来自 bank 数据集，且包含 task_spec 中列出的字段",
          "前10%名单效果按预测概率排序后取前10%样本计算相关指标（如命中率、提升度等）",
          "资源消耗报告包括训练/推理时间、CPU 和内存使用情况",
          "Beam Search 在给定资源限制内进行，候选数不超过6个"
        ]
      }
    },
    {
      "sequence": 3,
      "event_type": "KNOWLEDGE_RETRIEVED",
      "type": "KNOWLEDGE_RETRIEVED",
      "created_at": "2026-09-28T11:40:04.556292+00:00",
      "data": {
        "count": 6,
        "use_graph": true,
        "capability_ids": [
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "probability-logistic",
          "random-forest",
          "bank-ordered-split"
        ]
      }
    },
    {
      "sequence": 4,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T11:40:06.813491+00:00",
      "data": {
        "role": "planner",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "53b32eab-f383-4169-93bb-6b16e5b4d0af",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "9ec44d22471b3ea398b348ff048fc088e99ea3d761c95bb539b75c78d3a60470",
        "response_sha256": "c02881c3f1d8abd199e908a0597e41a43474d849703863698433c869845488c2",
        "input_tokens": 8203,
        "output_tokens": 182,
        "seconds": 1.961,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 5,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-28T11:40:07.084750+00:00",
      "data": {
        "candidate_id": "bank_logistic_default",
        "algorithm": "logistic",
        "variant": "default",
        "rationale": "初始比较的逻辑回归基线，使用 predict_proba 输出正类概率，配合通话前保守特征白名单与顺序留出协议，以 AP 为主指标。",
        "evidence_ids": [
          "probability-logistic",
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "bank-ordered-split"
        ],
        "parent_id": null
      }
    },
    {
      "sequence": 6,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T11:40:13.945291+00:00",
      "data": {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "86badc2c-7927-48ee-8489-2b2b43f75c1a",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "4f43dad8f674f88f4cbd5bbcc82ae950f45c54e44760bef456b47bab45575e61",
        "response_sha256": "20232e16de825c5ececda153ae428d6bb91efa9f593f9538e67095abb640d374",
        "input_tokens": 8725,
        "output_tokens": 259,
        "seconds": 6.692,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 7,
      "event_type": "FAILURE_INJECTED",
      "type": "FAILURE_INJECTED",
      "created_at": "2026-09-28T11:40:14.828064+00:00",
      "data": {
        "candidate_id": "bank_logistic_default",
        "kind": "missing_interface",
        "injected": true
      }
    },
    {
      "sequence": 8,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T11:40:14.919326+00:00",
      "data": {
        "candidate_id": "bank_logistic_default",
        "attempt": 0,
        "code_sha256": "b4dd5f8eebd665f9e6f4a06eb7a6ae7d0fa3a16c2d724e71bce32c7552233384"
      }
    },
    {
      "sequence": 9,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T11:40:14.991730+00:00",
      "data": {
        "candidate_id": "bank_logistic_default",
        "attempt": 0,
        "status": "failed",
        "metrics": {},
        "error": {
          "type": "CodePolicyError",
          "message": "Define exactly one function named build_pipeline(task_spec)",
          "repairable": true,
          "stage": "source_policy"
        }
      }
    },
    {
      "sequence": 10,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T11:40:21.485332+00:00",
      "data": {
        "role": "reviewer",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "bef02da7-a48c-47e7-ad4e-f34012de516c",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "c4a0d2a4b85d1b575a4553f3d92a8756c317700fd43c8ee24021da2653b632c9",
        "response_sha256": "b2943d4f08e61da65b494e713a8cbfcef5381ee8c06962aadf75fe1fe9e4408a",
        "input_tokens": 637,
        "output_tokens": 106,
        "seconds": 6.403,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 11,
      "event_type": "REPAIR_PLANNED",
      "type": "REPAIR_PLANNED",
      "created_at": "2026-09-28T11:40:21.707438+00:00",
      "data": {
        "candidate_id": "bank_logistic_default",
        "error_type": "CodePolicyError",
        "diagnosis": "The source defines the entry function as broken_pipeline instead of the required name build_pipeline(task_spec), violating the source_policy check that exactly one function named build_pipeline(task_spec) must be defined.",
        "fix": "Rename the function definition from 'def broken_pipeline(task_spec):' to 'def build_pipeline(task_spec):' so the module exposes exactly one function with the required name and signature.",
        "repairable": true
      }
    },
    {
      "sequence": 12,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T11:40:23.695894+00:00",
      "data": {
        "role": "repair_coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "f43747fb-91f7-4d86-b19c-b710101523b9",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "27e10c8bcb20f810630da1910ca83f2c0f2763623afca5d25269af14e53cced9",
        "response_sha256": "93e389e8dcf2671d9e54f8d9732b0b1c90b2dea7672be73d10d1bcc6fd44936c",
        "input_tokens": 9034,
        "output_tokens": 270,
        "seconds": 1.729,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 13,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T11:40:24.063812+00:00",
      "data": {
        "candidate_id": "bank_logistic_default",
        "attempt": 1,
        "code_sha256": "e674bef0808a2926a4f2fc8127f09a0c5c1a3b575582f73703c026fb4a8961c1"
      }
    },
    {
      "sequence": 14,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T11:40:26.242363+00:00",
      "data": {
        "candidate_id": "bank_logistic_default",
        "attempt": 1,
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
      "sequence": 15,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-28T11:40:26.656125+00:00",
      "data": {
        "candidate_id": "bank_forest_default",
        "algorithm": "forest",
        "variant": "default",
        "rationale": "初始比较的随机森林基线，固定 random_state 并限制树数量与 n_jobs 以适配 CPU/内存预算，作为非线性对照候选。",
        "evidence_ids": [
          "random-forest",
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "bank-ordered-split"
        ],
        "parent_id": null
      }
    },
    {
      "sequence": 16,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T11:40:29.117175+00:00",
      "data": {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "68ebeb6d-8917-4b13-8a5d-1b06ff098cd6",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "118f2b082da5be985d059bb27d4b7bb380fe60194e5ba2b6f3eafacfc43b8972",
        "response_sha256": "96512ac62d15e127e5d184d63558626232b7ee863e2bce82b07f5f4c954a5ce7",
        "input_tokens": 8741,
        "output_tokens": 287,
        "seconds": 2.124,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 17,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T11:40:29.555790+00:00",
      "data": {
        "candidate_id": "bank_forest_default",
        "attempt": 0,
        "code_sha256": "bc1719eb0ba8dc09660ac5c1b80b14a5382e9cf775d69cdd104ae4d1e51f5bb8"
      }
    },
    {
      "sequence": 18,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T11:40:34.624118+00:00",
      "data": {
        "candidate_id": "bank_forest_default",
        "attempt": 0,
        "status": "passed",
        "metrics": {
          "average_precision": 0.1277624798874739,
          "roc_auc": 0.5517438790465106,
          "f1_threshold_0_5": 0.0,
          "precision_at_10pct": 0.13592233009708737,
          "recall_at_10pct": 0.12280701754385964,
          "lift_at_10pct": 1.227772100153296,
          "validation_positive_rate": 0.11070648215586307,
          "top_10pct_count": 824,
          "validation_rows": 8238,
          "classification_threshold": 0.5,
          "evaluation_split": "validation_only",
          "sealed_test_scored": false,
          "ranking_tie_break": "original_validation_row_order",
          "dummy_average_precision": 0.11070648215586307,
          "ap_improvement_over_dummy": 0.017055997731610845
        },
        "error": null
      }
    },
    {
      "sequence": 19,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T11:40:37.449208+00:00",
      "data": {
        "role": "planner",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "8be9bbf2-909d-454a-bb0f-db6d056ea05d",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "0a520ef84ddaa076ccc2d6acbb6ac223943d7675a24d473050a568fc75f17311",
        "response_sha256": "707942068580b32b8e87b719ccab379393e90e21c08282d597d2720f8b40b380",
        "input_tokens": 9441,
        "output_tokens": 365,
        "seconds": 2.499,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 20,
      "event_type": "BEAM_EXPANDED",
      "type": "BEAM_EXPANDED",
      "created_at": "2026-09-28T11:40:37.905166+00:00",
      "data": {
        "beam_width": 2,
        "parents": [
          "bank_logistic_default",
          "bank_forest_default"
        ],
        "children": 4
      }
    },
    {
      "sequence": 21,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-28T11:40:38.183961+00:00",
      "data": {
        "candidate_id": "bank_logistic_balanced",
        "algorithm": "logistic",
        "variant": "balanced",
        "rationale": "Child of bank_logistic_default using class_weight balanced to counter the ~11% positive rate; keeps precontact whitelist, ordered split, and AP as primary metric.",
        "evidence_ids": [
          "probability-logistic",
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "bank-ordered-split"
        ],
        "parent_id": "bank_logistic_default"
      }
    },
    {
      "sequence": 22,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T11:40:40.420519+00:00",
      "data": {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "237a5e6d-9e25-44d0-a06f-241321b4d27d",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "e1cfe51b3c1d8f6bfe6d61d82530f9308915c518407b45f30829bbcb9ea9a1cb",
        "response_sha256": "6b41a68dd2bb49246aa535f7d77030947f3f3e3ba03c6977bbf8f5ab4f939332",
        "input_tokens": 9034,
        "output_tokens": 252,
        "seconds": 1.984,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 23,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T11:40:40.712735+00:00",
      "data": {
        "candidate_id": "bank_logistic_balanced",
        "attempt": 0,
        "code_sha256": "df78067d263ab32d9f8a90daece77619edf41852761086dcba8b1cbcc2008aef"
      }
    },
    {
      "sequence": 24,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T11:40:42.274722+00:00",
      "data": {
        "candidate_id": "bank_logistic_balanced",
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
      "sequence": 25,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-28T11:40:42.578869+00:00",
      "data": {
        "candidate_id": "bank_logistic_regularized",
        "algorithm": "logistic",
        "variant": "regularized",
        "rationale": "Child of bank_logistic_default with stronger regularization to control variance on the small precontact feature set; same protocol and AP evaluation.",
        "evidence_ids": [
          "probability-logistic",
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "bank-ordered-split"
        ],
        "parent_id": "bank_logistic_default"
      }
    },
    {
      "sequence": 26,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T11:40:44.477546+00:00",
      "data": {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "d5ac3413-13e7-4eba-b5a4-d6633a39f8b1",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "fa2d35122f38ba2ad99b3af7c4f131e6f60849377c1a7c45a06313d6cf21ad16",
        "response_sha256": "900f288d2f4bbadcc8b4b47d416223570fc14db98c6d6f34c7426f68096a8fe3",
        "input_tokens": 9027,
        "output_tokens": 268,
        "seconds": 1.561,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 27,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T11:40:44.753412+00:00",
      "data": {
        "candidate_id": "bank_logistic_regularized",
        "attempt": 0,
        "code_sha256": "ff866df73a58fa0d2e8b0ce41a0342a889fce756d005a9ad325bcf8bc9ad68db"
      }
    },
    {
      "sequence": 28,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T11:40:46.320041+00:00",
      "data": {
        "candidate_id": "bank_logistic_regularized",
        "attempt": 0,
        "status": "passed",
        "metrics": {
          "average_precision": 0.18154959172679347,
          "roc_auc": 0.6065676172584067,
          "f1_threshold_0_5": 0.0,
          "precision_at_10pct": 0.22815533980582525,
          "recall_at_10pct": 0.20614035087719298,
          "lift_at_10pct": 2.060903168114461,
          "validation_positive_rate": 0.11070648215586307,
          "top_10pct_count": 824,
          "validation_rows": 8238,
          "classification_threshold": 0.5,
          "evaluation_split": "validation_only",
          "sealed_test_scored": false,
          "ranking_tie_break": "original_validation_row_order",
          "dummy_average_precision": 0.11070648215586307,
          "ap_improvement_over_dummy": 0.0708431095709304
        },
        "error": null
      }
    },
    {
      "sequence": 29,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-28T11:40:46.640605+00:00",
      "data": {
        "candidate_id": "bank_forest_balanced",
        "algorithm": "forest",
        "variant": "balanced",
        "rationale": "Child of bank_forest_default using class_weight balanced to address class imbalance while keeping fixed random_state and bounded n_jobs for CPU/memory limits.",
        "evidence_ids": [
          "random-forest",
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "bank-ordered-split"
        ],
        "parent_id": "bank_forest_default"
      }
    },
    {
      "sequence": 30,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T11:40:53.396560+00:00",
      "data": {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "22b57285-4964-4e85-a113-e2b158b7c02e",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "b77e3d58265cba26a7867cbe78bfe0d927a508b9a77ea3ea499daadd4d097616",
        "response_sha256": "55a81a947002f59c1238f7d3348a78e453d283b742f691b89fdda380b2f54cd5",
        "input_tokens": 9085,
        "output_tokens": 290,
        "seconds": 6.457,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 31,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T11:40:53.672151+00:00",
      "data": {
        "candidate_id": "bank_forest_balanced",
        "attempt": 0,
        "code_sha256": "608f6098d0793224e4b0deac6c2baf11521a5fcbdd2f3f1dd781aedcb8225c83"
      }
    },
    {
      "sequence": 32,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T11:40:58.796097+00:00",
      "data": {
        "candidate_id": "bank_forest_balanced",
        "attempt": 0,
        "status": "passed",
        "metrics": {
          "average_precision": 0.12307938706482693,
          "roc_auc": 0.5357817446633235,
          "f1_threshold_0_5": 0.15309734513274337,
          "precision_at_10pct": 0.1395631067961165,
          "recall_at_10pct": 0.12609649122807018,
          "lift_at_10pct": 1.2606588528359735,
          "validation_positive_rate": 0.11070648215586307,
          "top_10pct_count": 824,
          "validation_rows": 8238,
          "classification_threshold": 0.5,
          "evaluation_split": "validation_only",
          "sealed_test_scored": false,
          "ranking_tie_break": "original_validation_row_order",
          "dummy_average_precision": 0.11070648215586307,
          "ap_improvement_over_dummy": 0.012372904908963867
        },
        "error": null
      }
    },
    {
      "sequence": 33,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-28T11:40:59.133607+00:00",
      "data": {
        "candidate_id": "bank_forest_shallower",
        "algorithm": "forest",
        "variant": "shallower",
        "rationale": "Child of bank_forest_default with reduced depth to lower resource consumption and variance, providing a cheaper nonlinear comparison under the same protocol.",
        "evidence_ids": [
          "random-forest",
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "bank-ordered-split"
        ],
        "parent_id": "bank_forest_default"
      }
    },
    {
      "sequence": 34,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T11:41:01.123306+00:00",
      "data": {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "4dd85e71-c66b-4d70-a071-fa1f5e16989e",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "95c16d11037b040ca6b4aeb720de5e4006d7b82789982e2cffd4f817804040a1",
        "response_sha256": "5a9c0e9f480562e690b85969d6088b502aa3bd514feb5e5e5480f84fa7d7a36e",
        "input_tokens": 9083,
        "output_tokens": 274,
        "seconds": 1.688,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 35,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T11:41:01.513534+00:00",
      "data": {
        "candidate_id": "bank_forest_shallower",
        "attempt": 0,
        "code_sha256": "e32b8fea3b336108b961d4a8995d694e98d2c78893c6cc12b1b7fbac89369453"
      }
    },
    {
      "sequence": 36,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T11:41:04.635821+00:00",
      "data": {
        "candidate_id": "bank_forest_shallower",
        "attempt": 0,
        "status": "passed",
        "metrics": {
          "average_precision": 0.14985341617481288,
          "roc_auc": 0.5884300867853499,
          "f1_threshold_0_5": 0.0,
          "precision_at_10pct": 0.17111650485436894,
          "recall_at_10pct": 0.15460526315789475,
          "lift_at_10pct": 1.5456773760858458,
          "validation_positive_rate": 0.11070648215586307,
          "top_10pct_count": 824,
          "validation_rows": 8238,
          "classification_threshold": 0.5,
          "evaluation_split": "validation_only",
          "sealed_test_scored": false,
          "ranking_tie_break": "original_validation_row_order",
          "dummy_average_precision": 0.11070648215586307,
          "ap_improvement_over_dummy": 0.03914693401894981
        },
        "error": null
      }
    },
    {
      "sequence": 37,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T11:41:08.873085+00:00",
      "data": {
        "role": "curator",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "f5979798-59ca-40e9-aeff-a6deaf0fe0c5",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "667ed6e7f43d7d77ae2da9377f789ff33756f10fe1367c83d21f03c84e2884f6",
        "response_sha256": "a8e49675d6a7426103f0c4fadce6c762af6c3576be481909f0b88aa0430a0189",
        "input_tokens": 1673,
        "output_tokens": 538,
        "seconds": 3.771,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 38,
      "event_type": "COMPARED",
      "type": "COMPARED",
      "created_at": "2026-09-28T11:41:09.171686+00:00",
      "data": {
        "selected_candidate_id": "bank_logistic_default"
      }
    },
    {
      "sequence": 39,
      "event_type": "RECORDED",
      "type": "RECORDED",
      "created_at": "2026-09-28T11:41:09.760181+00:00",
      "data": {
        "intended_status": "passed",
        "experiences": 1
      }
    }
  ],
  "usage": {
    "calls": 12,
    "input_tokens": 83104,
    "output_tokens": 3493,
    "cached_input_tokens": 50176,
    "records": [
      {
        "role": "interpreter",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "ed2cb921-24a4-4c1d-9ee7-4b3884609175",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "61fab09221ac55c44241af53cdaf72f17de187aeeabaa297a815965889b2dcac",
        "response_sha256": "de299af255f10fbd5bd231f1c4a1e1e6f091d77723659634c6c3c47197780b26",
        "input_tokens": 421,
        "output_tokens": 402,
        "seconds": 7.791,
        "finish_reason": "stop"
      },
      {
        "role": "planner",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "53b32eab-f383-4169-93bb-6b16e5b4d0af",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "9ec44d22471b3ea398b348ff048fc088e99ea3d761c95bb539b75c78d3a60470",
        "response_sha256": "c02881c3f1d8abd199e908a0597e41a43474d849703863698433c869845488c2",
        "input_tokens": 8203,
        "output_tokens": 182,
        "seconds": 1.961,
        "finish_reason": "stop"
      },
      {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "86badc2c-7927-48ee-8489-2b2b43f75c1a",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "4f43dad8f674f88f4cbd5bbcc82ae950f45c54e44760bef456b47bab45575e61",
        "response_sha256": "20232e16de825c5ececda153ae428d6bb91efa9f593f9538e67095abb640d374",
        "input_tokens": 8725,
        "output_tokens": 259,
        "seconds": 6.692,
        "finish_reason": "stop"
      },
      {
        "role": "reviewer",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "bef02da7-a48c-47e7-ad4e-f34012de516c",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "c4a0d2a4b85d1b575a4553f3d92a8756c317700fd43c8ee24021da2653b632c9",
        "response_sha256": "b2943d4f08e61da65b494e713a8cbfcef5381ee8c06962aadf75fe1fe9e4408a",
        "input_tokens": 637,
        "output_tokens": 106,
        "seconds": 6.403,
        "finish_reason": "stop"
      },
      {
        "role": "repair_coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "f43747fb-91f7-4d86-b19c-b710101523b9",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "27e10c8bcb20f810630da1910ca83f2c0f2763623afca5d25269af14e53cced9",
        "response_sha256": "93e389e8dcf2671d9e54f8d9732b0b1c90b2dea7672be73d10d1bcc6fd44936c",
        "input_tokens": 9034,
        "output_tokens": 270,
        "seconds": 1.729,
        "finish_reason": "stop"
      },
      {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "68ebeb6d-8917-4b13-8a5d-1b06ff098cd6",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "118f2b082da5be985d059bb27d4b7bb380fe60194e5ba2b6f3eafacfc43b8972",
        "response_sha256": "96512ac62d15e127e5d184d63558626232b7ee863e2bce82b07f5f4c954a5ce7",
        "input_tokens": 8741,
        "output_tokens": 287,
        "seconds": 2.124,
        "finish_reason": "stop"
      },
      {
        "role": "planner",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "8be9bbf2-909d-454a-bb0f-db6d056ea05d",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "0a520ef84ddaa076ccc2d6acbb6ac223943d7675a24d473050a568fc75f17311",
        "response_sha256": "707942068580b32b8e87b719ccab379393e90e21c08282d597d2720f8b40b380",
        "input_tokens": 9441,
        "output_tokens": 365,
        "seconds": 2.499,
        "finish_reason": "stop"
      },
      {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "237a5e6d-9e25-44d0-a06f-241321b4d27d",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "e1cfe51b3c1d8f6bfe6d61d82530f9308915c518407b45f30829bbcb9ea9a1cb",
        "response_sha256": "6b41a68dd2bb49246aa535f7d77030947f3f3e3ba03c6977bbf8f5ab4f939332",
        "input_tokens": 9034,
        "output_tokens": 252,
        "seconds": 1.984,
        "finish_reason": "stop"
      },
      {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "d5ac3413-13e7-4eba-b5a4-d6633a39f8b1",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "fa2d35122f38ba2ad99b3af7c4f131e6f60849377c1a7c45a06313d6cf21ad16",
        "response_sha256": "900f288d2f4bbadcc8b4b47d416223570fc14db98c6d6f34c7426f68096a8fe3",
        "input_tokens": 9027,
        "output_tokens": 268,
        "seconds": 1.561,
        "finish_reason": "stop"
      },
      {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "22b57285-4964-4e85-a113-e2b158b7c02e",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "b77e3d58265cba26a7867cbe78bfe0d927a508b9a77ea3ea499daadd4d097616",
        "response_sha256": "55a81a947002f59c1238f7d3348a78e453d283b742f691b89fdda380b2f54cd5",
        "input_tokens": 9085,
        "output_tokens": 290,
        "seconds": 6.457,
        "finish_reason": "stop"
      },
      {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "4dd85e71-c66b-4d70-a071-fa1f5e16989e",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "95c16d11037b040ca6b4aeb720de5e4006d7b82789982e2cffd4f817804040a1",
        "response_sha256": "5a9c0e9f480562e690b85969d6088b502aa3bd514feb5e5e5480f84fa7d7a36e",
        "input_tokens": 9083,
        "output_tokens": 274,
        "seconds": 1.688,
        "finish_reason": "stop"
      },
      {
        "role": "curator",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "f5979798-59ca-40e9-aeff-a6deaf0fe0c5",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "667ed6e7f43d7d77ae2da9377f789ff33756f10fe1367c83d21f03c84e2884f6",
        "response_sha256": "a8e49675d6a7426103f0c4fadce6c762af6c3576be481909f0b88aa0430a0189",
        "input_tokens": 1673,
        "output_tokens": 538,
        "seconds": 3.771,
        "finish_reason": "stop"
      }
    ]
  },
  "warnings": [
    "验证集成绩，不是最终测试成绩。",
    "受限AST构造器程序，不是任意Python或Docker操作系统沙箱。",
    "若数据中缺少 task_spec 列出的特征，则无法按规范执行",
    "若资源限制导致无法完成 Beam Search 或模型训练，需报告失败原因",
    "前10%名单效果的具体指标未在 task_spec 中指定，需明确计算口径",
    "无法承诺未见客户分离，因为数据中没有客户 ID 字段",
    "使用 duration 特征（被 feature_policy 禁止）",
    "请求客户级分离评估（无客户 ID 字段，无法实现）"
  ],
  "search_tree": [
    {
      "candidate_id": "bank_logistic_default",
      "parent_id": null,
      "status": "passed",
      "average_precision": 0.18287735589367637,
      "pruned": false,
      "pruned_reason": null
    },
    {
      "candidate_id": "bank_forest_default",
      "parent_id": null,
      "status": "passed",
      "average_precision": 0.1277624798874739,
      "pruned": true,
      "pruned_reason": "outside_final_beam_or_failed_hard_checks"
    },
    {
      "candidate_id": "bank_logistic_balanced",
      "parent_id": "bank_logistic_default",
      "status": "passed",
      "average_precision": 0.1807589966629477,
      "pruned": true,
      "pruned_reason": "outside_final_beam_or_failed_hard_checks"
    },
    {
      "candidate_id": "bank_logistic_regularized",
      "parent_id": "bank_logistic_default",
      "status": "passed",
      "average_precision": 0.18154959172679347,
      "pruned": false,
      "pruned_reason": null
    },
    {
      "candidate_id": "bank_forest_balanced",
      "parent_id": "bank_forest_default",
      "status": "passed",
      "average_precision": 0.12307938706482693,
      "pruned": true,
      "pruned_reason": "outside_final_beam_or_failed_hard_checks"
    },
    {
      "candidate_id": "bank_forest_shallower",
      "parent_id": "bank_forest_default",
      "status": "passed",
      "average_precision": 0.14985341617481288,
      "pruned": true,
      "pruned_reason": "outside_final_beam_or_failed_hard_checks"
    }
  ],
  "knowledge_writeback": {
    "run_saved": true,
    "experiences": [
      {
        "failure_id": "failure-718910612a54841a90019334",
        "fingerprint": "dafad272bf251de182681a8c7e1cd4bbba8776892e2837443996000de1dac3ac",
        "run_id": "0f25cc2b756648439ccccdabc4b9aa70",
        "error_type": "CodePolicyError",
        "diagnosis": "The source defines the entry function as broken_pipeline instead of the required name build_pipeline(task_spec), violating the source_policy check that exactly one function named build_pipeline(task_spec) must be defined.",
        "fix": "Rename the function definition from 'def broken_pipeline(task_spec):' to 'def build_pipeline(task_spec):' so the module exposes exactly one function with the required name and signature.",
        "task_type": "tabular_binary_classification",
        "validated": true,
        "status": "validated",
        "origin": "runtime_experience"
      }
    ]
  },
  "data_summary": {
    "train_rows": 24712,
    "validation_rows": 8238
  },
  "interpretation": {
    "objective": "在通话前预测银行客户订购概率（正类为 yes），使用提供的预接触特征，先比较逻辑回归与随机森林，再用宽度为2的Beam Search扩展超参数，最多保留6个不同候选，并报告平均精度（AP）、前10%名单效果和资源消耗。",
    "constraints": [
      "禁止使用 duration 特征",
      "仅使用 task_spec 中列出的特征：age, job, marital, education, default, housing, loan, pdays, previous, poutcome",
      "分类特征：job, marital, education, default, housing, loan, poutcome",
      "数值特征：age, pdays, previous",
      "主指标为 average_precision",
      "正类标签为 yes",
      "随机种子为 42",
      "资源限制：CPU 2，内存 2048 MiB，超时 120 秒",
      "Beam Search 宽度为 2，最多 6 个不同候选",
      "初始比较逻辑回归和随机森林"
    ],
    "assumptions": [
      "数据来自 bank 数据集，且包含 task_spec 中列出的字段",
      "前10%名单效果按预测概率排序后取前10%样本计算相关指标（如命中率、提升度等）",
      "资源消耗报告包括训练/推理时间、CPU 和内存使用情况",
      "Beam Search 在给定资源限制内进行，候选数不超过6个"
    ],
    "warnings": [
      "若数据中缺少 task_spec 列出的特征，则无法按规范执行",
      "若资源限制导致无法完成 Beam Search 或模型训练，需报告失败原因",
      "前10%名单效果的具体指标未在 task_spec 中指定，需明确计算口径",
      "无法承诺未见客户分离，因为数据中没有客户 ID 字段"
    ],
    "incompatible_requests": [
      "使用 duration 特征（被 feature_policy 禁止）",
      "请求客户级分离评估（无客户 ID 字段，无法实现）"
    ]
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
      "score": 2.768603,
      "lexical_score": 2.540003,
      "graph_score": 0.2286,
      "evidence_path": [
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
          "bonus": 0.2286002286003429
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
      "score": 2.717803,
      "lexical_score": 0.889001,
      "graph_score": 1.828802,
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
          "bonus": 1.016001016001524
        },
        {
          "seed": "capability:random-forest:v1",
          "hops": [
            {
              "from": "capability:random-forest:v1",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            },
            {
              "from": "capability:average-precision:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-target:v1"
            }
          ],
          "bonus": 0.3556003556005334
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
          "bonus": 0.4572004572006858
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
      "score": 2.184402,
      "lexical_score": 0.508001,
      "graph_score": 1.676402,
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
          "bonus": 0.508000508000762
        },
        {
          "seed": "capability:random-forest:v1",
          "hops": [
            {
              "from": "capability:random-forest:v1",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            }
          ],
          "bonus": 0.7112007112010668
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
          "bonus": 0.4572004572006858
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
      "score": 2.006602,
      "lexical_score": 1.143001,
      "graph_score": 0.863601,
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
          "bonus": 0.508000508000762
        },
        {
          "seed": "capability:random-forest:v1",
          "hops": [
            {
              "from": "capability:random-forest:v1",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            },
            {
              "from": "capability:average-precision:v1",
              "relation": "REQUIRES",
              "to": "capability:probability-logistic:v1"
            }
          ],
          "bonus": 0.3556003556005334
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
      "capability_id": "random-forest",
      "confidence": 1.0,
      "created_at": "2026-09-28T11:23:24.518056+00:00",
      "dependencies": [
        "Python >=3.10",
        "scikit-learn"
      ],
      "evidence": [
        {
          "content_sha256": "c5a4230e63753d964674363bdbc47179340f28433133172dce1ecef4e73b6ee4",
          "license": "BSD-3-Clause",
          "locator": {
            "imports": [
              "import threading",
              "from abc import ABCMeta, abstractmethod",
              "from numbers import Integral, Real",
              "from warnings import catch_warnings, simplefilter, warn",
              "import numpy as np",
              "from scipy.sparse import hstack as sparse_hstack",
              "from scipy.sparse import issparse",
              "from ..base import ClassifierMixin, MultiOutputMixin, RegressorMixin, TransformerMixin, _fit_context, is_classifier",
              "from ..exceptions import DataConversionWarning",
              "from ..metrics import accuracy_score, r2_score",
              "from ..preprocessing import OneHotEncoder",
              "from ..tree import BaseDecisionTree, DecisionTreeClassifier, DecisionTreeRegressor, ExtraTreeClassifier, ExtraTreeRegressor",
              "from ..tree._tree import DOUBLE, DTYPE",
              "from ..utils import check_random_state, compute_sample_weight",
              "from ..utils._param_validation import Interval, RealNotInt, StrOptions",
              "from ..utils._tags import get_tags",
              "from ..utils.multiclass import check_classification_targets, type_of_target",
              "from ..utils.parallel import Parallel, delayed",
              "from ..utils.validation import _check_feature_names_in, _check_sample_weight, _num_samples, check_is_fitted, validate_data",
              "from ._base import BaseEnsemble, _partition_estimators"
            ],
            "line_end": 1568,
            "line_start": 1174,
            "methods": [
              "__init__"
            ],
            "parse_mode": "ast-only",
            "path": "/root/algorithm-capability-factory/.venv/lib/python3.10/site-packages/sklearn/ensemble/_forest.py",
            "relative_path": "sklearn/ensemble/_forest.py",
            "signature": "class RandomForestClassifier(ForestClassifier):\n    def __init__(self, n_estimators=100, *, criterion='gini', max_depth=None, min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_features='sqrt', max_leaf_nodes=None, min_impurity_decrease=0.0, bootstrap=True, oob_score=False, n_jobs=None, random_state=None, verbose=0, warm_start=False, class_weight=None, ccp_alpha=0.0, max_samples=None, monotonic_cst=None)",
            "symbol": "RandomForestClassifier"
          },
          "revision": "1.7.2",
          "source_id": "src-65a2ca3df537050020eb73b5",
          "uri": "https://github.com/scikit-learn/scikit-learn/blob/1.7.2/sklearn/ensemble/_forest.py"
        }
      ],
      "extraction_method": "curated-source-grounded",
      "id": "random-forest",
      "input_schema": {
        "task_types": [
          "tabular_binary_classification"
        ],
        "type": "features"
      },
      "name": "随机森林表格分类候选",
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
      "summary": "RandomForestClassifier 集成多棵决策树并提供类别概率；固定 random_state，并用 n_jobs 和树数量限制 CPU 与内存。它是可比较的候选，不预设其性能优于逻辑回归。",
      "tags": [
        "RandomForestClassifier",
        "森林",
        "非线性",
        "random_state",
        "cpu"
      ],
      "task_types": [
        "tabular_binary_classification"
      ],
      "uses": [
        {
          "kind": "Algorithm",
          "label": "RandomForestClassifier"
        }
      ],
      "version": 1,
      "score": 2.006602,
      "lexical_score": 1.778002,
      "graph_score": 0.2286,
      "evidence_path": [
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
              "to": "capability:random-forest:v1"
            }
          ],
          "bonus": 0.2286002286003429
        }
      ],
      "graph_used": true,
      "source_locator": [
        {
          "imports": [
            "import threading",
            "from abc import ABCMeta, abstractmethod",
            "from numbers import Integral, Real",
            "from warnings import catch_warnings, simplefilter, warn",
            "import numpy as np",
            "from scipy.sparse import hstack as sparse_hstack",
            "from scipy.sparse import issparse",
            "from ..base import ClassifierMixin, MultiOutputMixin, RegressorMixin, TransformerMixin, _fit_context, is_classifier",
            "from ..exceptions import DataConversionWarning",
            "from ..metrics import accuracy_score, r2_score",
            "from ..preprocessing import OneHotEncoder",
            "from ..tree import BaseDecisionTree, DecisionTreeClassifier, DecisionTreeRegressor, ExtraTreeClassifier, ExtraTreeRegressor",
            "from ..tree._tree import DOUBLE, DTYPE",
            "from ..utils import check_random_state, compute_sample_weight",
            "from ..utils._param_validation import Interval, RealNotInt, StrOptions",
            "from ..utils._tags import get_tags",
            "from ..utils.multiclass import check_classification_targets, type_of_target",
            "from ..utils.parallel import Parallel, delayed",
            "from ..utils.validation import _check_feature_names_in, _check_sample_weight, _num_samples, check_is_fitted, validate_data",
            "from ._base import BaseEnsemble, _partition_estimators"
          ],
          "line_end": 1568,
          "line_start": 1174,
          "methods": [
            "__init__"
          ],
          "parse_mode": "ast-only",
          "path": "/root/algorithm-capability-factory/.venv/lib/python3.10/site-packages/sklearn/ensemble/_forest.py",
          "relative_path": "sklearn/ensemble/_forest.py",
          "signature": "class RandomForestClassifier(ForestClassifier):\n    def __init__(self, n_estimators=100, *, criterion='gini', max_depth=None, min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_features='sqrt', max_leaf_nodes=None, min_impurity_decrease=0.0, bootstrap=True, oob_score=False, n_jobs=None, random_state=None, verbose=0, warm_start=False, class_weight=None, ccp_alpha=0.0, max_samples=None, monotonic_cst=None)",
          "symbol": "RandomForestClassifier"
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
      "score": 1.752602,
      "lexical_score": 0.508001,
      "graph_score": 1.244601,
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
          "bonus": 1.016001016001524
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
          "bonus": 0.2286002286003429
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
    }
  ],
  "quality_status": "above_prevalence",
  "explanation": {
    "summary": "在仅验证集（validation_only，8238 行，正例率 0.1107）上，六个候选均通过且未在封存测试集评分（sealed_test_scored=false）。按平均精度（average_precision）排序：bank_logistic_default 最高（0.1829，较 dummy 提升 0.0722，lift@10% 2.094，precision@10% 0.2318，recall@10% 0.2094，ROC-AUC 0.6131）；bank_logistic_regularized 次之（0.1815，提升 0.0708）；bank_logistic_balanced 为 0.1808（提升 0.0701，且阈值 0.5 下 F1 为 0.2288，其余逻辑回归候选该 F1 为 0）。森林类候选整体较弱：bank_forest_shallower 0.1499（提升 0.0391），bank_forest_default 0.1278（提升 0.0171），bank_forest_balanced 最低 0.1231（提升 0.0124）。因此选定 bank_logistic_default 作为当前验证集上的首选候选，依据检索到的能力条目 bank-precontact-policy、bank-target、average-precision、probability-logistic、random-forest、bank-ordered-split。",
    "limitations": [
      "所有指标均为验证集结果（evaluation_split=validation_only），并非最终测试集表现；封存测试集未评分（sealed_test_scored=false），因此不能据此推断泛化性能。",
      "候选间差距较小（如 bank_logistic_default 与 bank_logistic_regularized 的 AP 差约 0.0013），在单一验证集上可能不稳定，需独立复现或交叉验证确认。",
      "排序并列按原始验证行顺序打破（ranking_tie_break=original_validation_row_order），该规则会影响 top-10% 指标，属于评估约定而非模型能力。",
      "约束式 AST 执行仅用于受控的候选评估，不等同于通用操作系统沙箱，不能据此声称具备通用隔离或安全保证。",
      "模型选择（如逻辑回归优于随机森林）只反映本数据集与当前特征/划分下的验证表现，不构成因果性的营销提升证据。",
      "未提供置信区间、显著性检验或校准指标，且部分候选在阈值 0.5 下 F1 为 0，说明默认阈值不适合直接用于业务决策。"
    ]
  },
  "finished_at": "2026-09-28T11:41:09.433396+00:00",
  "timing": {
    "wall_seconds": 73.803,
    "budget_seconds": 900
  },
  "report_paths": {}
}
````

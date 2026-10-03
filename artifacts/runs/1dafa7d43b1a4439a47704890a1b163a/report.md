# 算法能力验证报告

指标与状态来自原始验证事实；缺失项不填零、不推断通过。

模式由原始报告的 mode 字段说明：mock 为模拟，replay 为历史回放。

````json
{
  "schema_version": "1.0",
  "run_id": "1dafa7d43b1a4439a47704890a1b163a",
  "status": "passed",
  "mode": "mock",
  "provider": "mock",
  "description": "使用通话前字段预测银行营销响应，比较两个方案并保存验证结果",
  "dataset_id": "bank",
  "created_at": "2026-09-28T11:23:24.174721+00:00",
  "request": {
    "description": "使用通话前字段预测银行营销响应，比较两个方案并保存验证结果",
    "dataset_id": "bank",
    "provider": "mock",
    "max_candidates": 2,
    "max_repairs": 2,
    "use_graph": true,
    "search": "compare",
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
  "model": "deterministic-mock-v1",
  "provenance": {
    "prompt_version": "algoforge-roles-v1",
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
        "wall_seconds": 1.003571285167709,
        "fit_seconds": 0.06583746988326311,
        "predict_seconds": 0.012358498992398381,
        "worker_wall_seconds": 0.8228814809117466,
        "peak_rss_mib": 221.23828125,
        "cpu_seconds": 1.0811009999999999,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "total_seconds": 1.7028024489991367
      },
      "repairs": [
        {
          "error_type": "CodePolicyError",
          "diagnosis": "候选未通过独立验证",
          "fix": "按照受限接口重新生成合法Pipeline",
          "repairable": true,
          "attempt": 1,
          "before_hash": "5534920752d65926cbf47678b4fb9a476531d7ed02945cd50ed0719e15e8d3a7",
          "after_hash": "daf5f0fe1e16551b05e6617bdc4b86b910fba776d9fb01f51791e01d85d81420"
        }
      ],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "5534920752d65926cbf47678b4fb9a476531d7ed02945cd50ed0719e15e8d3a7",
          "code_path": "candidates/c1/attempt_0/model.py",
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
            "total_seconds": 0.0009577518794685602
          }
        },
        {
          "attempt": 1,
          "code_sha256": "daf5f0fe1e16551b05e6617bdc4b86b910fba776d9fb01f51791e01d85d81420",
          "code_path": "candidates/c1/attempt_1/model.py",
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
            "wall_seconds": 1.003571285167709,
            "fit_seconds": 0.06583746988326311,
            "predict_seconds": 0.012358498992398381,
            "worker_wall_seconds": 0.8228814809117466,
            "peak_rss_mib": 221.23828125,
            "cpu_seconds": 1.0811009999999999,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "total_seconds": 1.7028024489991367
          }
        }
      ],
      "artifact_id": "c1",
      "parent_id": null,
      "injected_failure": true,
      "error": null,
      "quality_status": "above_prevalence",
      "code_sha256": "daf5f0fe1e16551b05e6617bdc4b86b910fba776d9fb01f51791e01d85d81420",
      "code_path": "candidates/c1/attempt_1/model.py",
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
        "wall_seconds": 2.305649552028626,
        "fit_seconds": 1.1676214439794421,
        "predict_seconds": 0.0597110609523952,
        "worker_wall_seconds": 2.0926674439106137,
        "peak_rss_mib": 231.46484375,
        "cpu_seconds": 3.377259,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "total_seconds": 2.4647849139291793
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
            "wall_seconds": 2.305649552028626,
            "fit_seconds": 1.1676214439794421,
            "predict_seconds": 0.0597110609523952,
            "worker_wall_seconds": 2.0926674439106137,
            "peak_rss_mib": 231.46484375,
            "cpu_seconds": 3.377259,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "total_seconds": 2.4647849139291793
          }
        }
      ],
      "artifact_id": "c2",
      "parent_id": null,
      "error": null,
      "quality_status": "above_prevalence",
      "code_sha256": "c28927f8790c23b04baf26fe69107617445d9286cd69ad428a2871224edc6c88",
      "code_path": "candidates/c2/attempt_0/model.py",
      "explanation": "明确标记的离线模板输出"
    }
  ],
  "selected_candidate_id": "c1",
  "events": [
    {
      "sequence": 0,
      "event_type": "RECEIVED",
      "type": "RECEIVED",
      "created_at": "2026-09-28T11:23:24.263280+00:00",
      "data": {
        "mode": "mock",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 1,
      "event_type": "MOCK_RESPONSE",
      "type": "MOCK_RESPONSE",
      "created_at": "2026-09-28T11:23:25.069618+00:00",
      "data": {
        "role": "interpreter",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 2,
      "event_type": "SPEC_VALIDATED",
      "type": "SPEC_VALIDATED",
      "created_at": "2026-09-28T11:23:25.246357+00:00",
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
      "created_at": "2026-09-28T11:23:25.440214+00:00",
      "data": {
        "count": 6,
        "use_graph": true,
        "capability_ids": [
          "bank-precontact-policy",
          "bank-target",
          "bank-ordered-split",
          "average-precision",
          "training-only-pipeline",
          "probability-logistic"
        ]
      }
    },
    {
      "sequence": 4,
      "event_type": "MOCK_RESPONSE",
      "type": "MOCK_RESPONSE",
      "created_at": "2026-09-28T11:23:25.672973+00:00",
      "data": {
        "role": "planner",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 5,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-28T11:23:25.908697+00:00",
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
      "created_at": "2026-09-28T11:23:26.293612+00:00",
      "data": {
        "role": "coder",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 7,
      "event_type": "FAILURE_INJECTED",
      "type": "FAILURE_INJECTED",
      "created_at": "2026-09-28T11:23:26.523503+00:00",
      "data": {
        "candidate_id": "c1",
        "kind": "missing_interface",
        "injected": true
      }
    },
    {
      "sequence": 8,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T11:23:26.748156+00:00",
      "data": {
        "candidate_id": "c1",
        "attempt": 0,
        "code_sha256": "5534920752d65926cbf47678b4fb9a476531d7ed02945cd50ed0719e15e8d3a7"
      }
    },
    {
      "sequence": 9,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T11:23:26.967075+00:00",
      "data": {
        "candidate_id": "c1",
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
      "event_type": "MOCK_RESPONSE",
      "type": "MOCK_RESPONSE",
      "created_at": "2026-09-28T11:23:27.216399+00:00",
      "data": {
        "role": "reviewer",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 11,
      "event_type": "REPAIR_PLANNED",
      "type": "REPAIR_PLANNED",
      "created_at": "2026-09-28T11:23:27.459821+00:00",
      "data": {
        "candidate_id": "c1",
        "error_type": "CodePolicyError",
        "diagnosis": "候选未通过独立验证",
        "fix": "按照受限接口重新生成合法Pipeline",
        "repairable": true
      }
    },
    {
      "sequence": 12,
      "event_type": "MOCK_RESPONSE",
      "type": "MOCK_RESPONSE",
      "created_at": "2026-09-28T11:23:28.112754+00:00",
      "data": {
        "role": "repair_coder",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 13,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T11:23:28.380937+00:00",
      "data": {
        "candidate_id": "c1",
        "attempt": 1,
        "code_sha256": "daf5f0fe1e16551b05e6617bdc4b86b910fba776d9fb01f51791e01d85d81420"
      }
    },
    {
      "sequence": 14,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T11:23:30.344618+00:00",
      "data": {
        "candidate_id": "c1",
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
      "created_at": "2026-09-28T11:23:30.717405+00:00",
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
      "sequence": 16,
      "event_type": "MOCK_RESPONSE",
      "type": "MOCK_RESPONSE",
      "created_at": "2026-09-28T11:23:30.935316+00:00",
      "data": {
        "role": "coder",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 17,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T11:23:31.300586+00:00",
      "data": {
        "candidate_id": "c2",
        "attempt": 0,
        "code_sha256": "c28927f8790c23b04baf26fe69107617445d9286cd69ad428a2871224edc6c88"
      }
    },
    {
      "sequence": 18,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T11:23:34.166946+00:00",
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
      "sequence": 19,
      "event_type": "MOCK_RESPONSE",
      "type": "MOCK_RESPONSE",
      "created_at": "2026-09-28T11:23:34.386625+00:00",
      "data": {
        "role": "curator",
        "model": "deterministic-mock-v1"
      }
    },
    {
      "sequence": 20,
      "event_type": "COMPARED",
      "type": "COMPARED",
      "created_at": "2026-09-28T11:23:34.597897+00:00",
      "data": {
        "selected_candidate_id": "c1"
      }
    },
    {
      "sequence": 21,
      "event_type": "RECORDED",
      "type": "RECORDED",
      "created_at": "2026-09-28T11:23:35.166522+00:00",
      "data": {
        "status": "passed",
        "experiences": 1
      }
    }
  ],
  "usage": {
    "calls": 7,
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
      "pruned": false,
      "pruned_reason": null
    }
  ],
  "knowledge_writeback": {
    "run_saved": true,
    "experiences": [
      {
        "failure_id": "failure-d455222a3cc49f00fbc7f5b8",
        "fingerprint": "5eb32268901f67e6407f22e17c9b995ebd96a185caa2fbefc4e6bdbab67dcb90",
        "run_id": "1dafa7d43b1a4439a47704890a1b163a",
        "error_type": "CodePolicyError",
        "diagnosis": "候选未通过独立验证",
        "fix": "按照受限接口重新生成合法Pipeline",
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
    "objective": "使用通话前字段预测银行营销响应，比较两个方案并保存验证结果",
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
      "score": 3.893034,
      "lexical_score": 3.212698,
      "graph_score": 0.680336,
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
          "bonus": 0.37796447300922725
        },
        {
          "seed": "capability:bank-ordered-split:v1",
          "hops": [
            {
              "from": "capability:bank-ordered-split:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-precontact-policy:v1"
            }
          ],
          "bonus": 0.30237157840738177
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
      "score": 2.296097,
      "lexical_score": 0.944911,
      "graph_score": 1.351186,
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
          "seed": "capability:bank-ordered-split:v1",
          "hops": [
            {
              "from": "capability:bank-ordered-split:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-precontact-policy:v1"
            },
            {
              "from": "capability:bank-precontact-policy:v1",
              "relation": "REQUIRES",
              "to": "capability:bank-target:v1"
            }
          ],
          "bonus": 0.15118578920369088
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
      "score": 2.144911,
      "lexical_score": 0.755929,
      "graph_score": 1.388982,
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
          "bonus": 0.18898223650461363
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
      "score": 1.544911,
      "lexical_score": 0.566947,
      "graph_score": 0.977964,
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
          "bonus": 0.37796447300922725
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
      "created_at": "2026-09-28T11:23:24.517409+00:00",
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
      "score": 1.469318,
      "lexical_score": 0.377964,
      "graph_score": 1.091354,
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
          "bonus": 0.6000000000000001
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
          "bonus": 0.18898223650461363
        },
        {
          "seed": "capability:bank-ordered-split:v1",
          "hops": [
            {
              "from": "capability:bank-ordered-split:v1",
              "relation": "REQUIRES",
              "to": "capability:training-only-pipeline:v1"
            }
          ],
          "bonus": 0.30237157840738177
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
      "score": 1.12915,
      "lexical_score": 0.0,
      "graph_score": 1.12915,
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
          "bonus": 0.37796447300922725
        },
        {
          "seed": "capability:bank-ordered-split:v1",
          "hops": [
            {
              "from": "capability:bank-ordered-split:v1",
              "relation": "REQUIRES",
              "to": "capability:training-only-pipeline:v1"
            },
            {
              "from": "capability:training-only-pipeline:v1",
              "relation": "REQUIRES",
              "to": "capability:probability-logistic:v1"
            }
          ],
          "bonus": 0.15118578920369088
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
    }
  ],
  "quality_status": "above_prevalence",
  "explanation": {
    "summary": "已根据独立验证报告比较方案；本次为mock运行。",
    "limitations": [
      "未调用真实大模型"
    ]
  },
  "finished_at": "2026-09-28T11:23:34.861552+00:00",
  "timing": {
    "wall_seconds": 10.687,
    "budget_seconds": 900
  }
}
````

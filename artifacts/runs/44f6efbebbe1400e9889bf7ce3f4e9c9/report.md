# 算法能力验证报告

指标与状态来自原始验证事实；缺失项不填零、不推断通过。

模式由原始报告的 mode 字段说明：mock 为模拟，replay 为历史回放。

````json
{
  "schema_version": "1.0",
  "run_id": "44f6efbebbe1400e9889bf7ce3f4e9c9",
  "status": "passed",
  "mode": "real",
  "provider": "local_http",
  "description": "预测银行客户是否订购定期存款，使用可复现的表格分类流程，禁止使用 duration 字段，输出可运行代码。",
  "dataset_id": "bank",
  "created_at": "2026-09-29T17:45:52.761978+00:00",
  "request": {
    "description": "预测银行客户是否订购定期存款，使用可复现的表格分类流程，禁止使用 duration 字段，输出可运行代码。",
    "dataset_id": "bank",
    "provider": "local_http",
    "max_candidates": 1,
    "max_repairs": 0,
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
        "rationale": "Logistic regression is a suitable choice for binary classification tasks and provides a good baseline for comparison.",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target",
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
          "timeout_s": 101.0,
          "memory_mib": 2048,
          "cpu_cores": 2
        },
        "worker_pid": 69479,
        "wall_seconds": 1.1531933748628944,
        "fit_seconds": 0.14652393106371164,
        "predict_seconds": 0.03144995286129415,
        "worker_wall_seconds": 0.9706447850912809,
        "peak_rss_mib": 226.87890625,
        "cpu_seconds": 1.180477,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 1.8562774281017482
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
              "timeout_s": 101.0,
              "memory_mib": 2048,
              "cpu_cores": 2
            },
            "worker_pid": 69479,
            "wall_seconds": 1.1531933748628944,
            "fit_seconds": 0.14652393106371164,
            "predict_seconds": 0.03144995286129415,
            "worker_wall_seconds": 0.9706447850912809,
            "peak_rss_mib": 226.87890625,
            "cpu_seconds": 1.180477,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 1.8562774281017482
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
      "explanation": "The generated code constructs a scikit-learn pipeline for a tabular binary classification task. It includes preprocessing steps for numeric and categorical features, followed by a logistic regression model. The pipeline adheres to the provided task specification and uses the allowed classes and methods."
    }
  ],
  "selected_candidate_id": "logistic_default",
  "events": [
    {
      "sequence": 0,
      "event_type": "RECEIVED",
      "type": "RECEIVED",
      "created_at": "2026-09-29T17:45:53.146052+00:00",
      "data": {
        "mode": "real",
        "model": "coder14"
      }
    },
    {
      "sequence": 1,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T17:45:58.185188+00:00",
      "data": {
        "role": "interpreter",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8100/v1",
        "response_id": "chatcmpl-9315fe1d2f570b5a",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "0f48d43eebefbee6024bb55c2a3e0209f58b670d639808e0dc0b6554bd081972",
        "response_sha256": "47a6d3134a17fe961daa978df57b4eaf076cb9a16ef54cd04bec194184030cbd",
        "input_tokens": 445,
        "output_tokens": 168,
        "seconds": 3.814,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 2,
      "event_type": "SPEC_VALIDATED",
      "type": "SPEC_VALIDATED",
      "created_at": "2026-09-29T17:45:58.713892+00:00",
      "data": {
        "task_type": "tabular_binary_classification",
        "assumptions": [
          "数据集为 'bank'",
          "特征包括 'age', 'job', 'marital', 'education', 'default', 'housing', 'loan', 'pdays', 'previous', 'poutcome'",
          "分类任务为二元分类",
          "正类标签为 'yes'",
          "评估指标为平均精度"
        ]
      }
    },
    {
      "sequence": 3,
      "event_type": "KNOWLEDGE_RETRIEVED",
      "type": "KNOWLEDGE_RETRIEVED",
      "created_at": "2026-09-29T17:45:59.028724+00:00",
      "data": {
        "count": 6,
        "use_graph": true,
        "capability_ids": [
          "bank-precontact-policy",
          "bank-target",
          "average-precision",
          "probability-logistic",
          "bank-ordered-split",
          "random-forest"
        ]
      }
    },
    {
      "sequence": 4,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T17:46:03.360445+00:00",
      "data": {
        "role": "planner",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8100/v1",
        "response_id": "chatcmpl-8e1a6e7180531559",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "0836218c5aed619e821fd122efcb0e1a1b1c30d3e403f42c9b4b0dcf0f297437",
        "response_sha256": "f07d2797d032e4cd01e0c6fa5161459c55d729beb17524b5b824d8a886485452",
        "input_tokens": 8362,
        "output_tokens": 92,
        "seconds": 3.675,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 5,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-29T17:46:03.779580+00:00",
      "data": {
        "candidate_id": "logistic_default",
        "algorithm": "logistic",
        "variant": "default",
        "rationale": "Logistic regression is a suitable choice for binary classification tasks and provides a good baseline for comparison.",
        "evidence_ids": [
          "bank-precontact-policy",
          "bank-target",
          "probability-logistic"
        ],
        "parent_id": null
      }
    },
    {
      "sequence": 6,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T17:46:10.787491+00:00",
      "data": {
        "role": "coder",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8100/v1",
        "response_id": "chatcmpl-a045cc52e725979e",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "2b80eb8d055ddeb6c65491f565a62482457961f9d9f75c1571d4de6e82dc9e21",
        "response_sha256": "8c58a6d8c15749aae4ff47c4bd11a89a4042304a703fcac79ef5537d8ded8b3e",
        "input_tokens": 8840,
        "output_tokens": 226,
        "seconds": 6.458,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 7,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-29T17:46:11.389239+00:00",
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
      "created_at": "2026-09-29T17:46:13.702746+00:00",
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
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-29T17:46:17.674996+00:00",
      "data": {
        "role": "curator",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8100/v1",
        "response_id": "chatcmpl-994b053dce406409",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "24019aceada376df61059794270fce5b44730bb7a20a6558cd3c1fd7662a502c",
        "response_sha256": "f2310bdd10111cfe43feba507d657a1be52c70278ab1c21044d0a42ac552d36d",
        "input_tokens": 554,
        "output_tokens": 168,
        "seconds": 3.443,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 10,
      "event_type": "COMPARED",
      "type": "COMPARED",
      "created_at": "2026-09-29T17:46:18.128714+00:00",
      "data": {
        "selected_candidate_id": "logistic_default"
      }
    },
    {
      "sequence": 11,
      "event_type": "RECORDED",
      "type": "RECORDED",
      "created_at": "2026-09-29T17:46:18.892756+00:00",
      "data": {
        "intended_status": "passed",
        "experiences": 0
      }
    }
  ],
  "usage": {
    "calls": 4,
    "input_tokens": 18201,
    "output_tokens": 654,
    "cached_input_tokens": 0,
    "records": [
      {
        "role": "interpreter",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8100/v1",
        "response_id": "chatcmpl-9315fe1d2f570b5a",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "0f48d43eebefbee6024bb55c2a3e0209f58b670d639808e0dc0b6554bd081972",
        "response_sha256": "47a6d3134a17fe961daa978df57b4eaf076cb9a16ef54cd04bec194184030cbd",
        "input_tokens": 445,
        "output_tokens": 168,
        "seconds": 3.814,
        "finish_reason": "stop"
      },
      {
        "role": "planner",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8100/v1",
        "response_id": "chatcmpl-8e1a6e7180531559",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "0836218c5aed619e821fd122efcb0e1a1b1c30d3e403f42c9b4b0dcf0f297437",
        "response_sha256": "f07d2797d032e4cd01e0c6fa5161459c55d729beb17524b5b824d8a886485452",
        "input_tokens": 8362,
        "output_tokens": 92,
        "seconds": 3.675,
        "finish_reason": "stop"
      },
      {
        "role": "coder",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8100/v1",
        "response_id": "chatcmpl-a045cc52e725979e",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "2b80eb8d055ddeb6c65491f565a62482457961f9d9f75c1571d4de6e82dc9e21",
        "response_sha256": "8c58a6d8c15749aae4ff47c4bd11a89a4042304a703fcac79ef5537d8ded8b3e",
        "input_tokens": 8840,
        "output_tokens": 226,
        "seconds": 6.458,
        "finish_reason": "stop"
      },
      {
        "role": "curator",
        "requested_model": "coder14",
        "returned_model": "coder14",
        "endpoint": "http://127.0.0.1:8100/v1",
        "response_id": "chatcmpl-994b053dce406409",
        "system_fingerprint": "vllm-0.29.0-fbfed58d",
        "prompt_sha256": "24019aceada376df61059794270fce5b44730bb7a20a6558cd3c1fd7662a502c",
        "response_sha256": "f2310bdd10111cfe43feba507d657a1be52c70278ab1c21044d0a42ac552d36d",
        "input_tokens": 554,
        "output_tokens": 168,
        "seconds": 3.443,
        "finish_reason": "stop"
      }
    ]
  },
  "warnings": [
    "指标来自 validation_only，封存测试集保持未评分。",
    "执行器采用受限 AST 构造器和资源限制子进程；生产隔离需要强化运行时。",
    "请求中未指定运行时间预算，将使用默认值 120 秒"
  ],
  "search_tree": [
    {
      "candidate_id": "logistic_default",
      "parent_id": null,
      "status": "passed",
      "average_precision": 0.18287735589367637,
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
      "http://127.0.0.1:8100/v1"
    ],
    "authorization": "none",
    "local_profile": "single_gpu_14b",
    "deployment": "external_local_http"
  },
  "data_summary": {
    "train_rows": 24712,
    "validation_rows": 8238
  },
  "interpretation": {
    "objective": "预测银行客户是否订购定期存款",
    "constraints": [
      "使用可复现的表格分类流程",
      "禁止使用 duration 字段"
    ],
    "assumptions": [
      "数据集为 'bank'",
      "特征包括 'age', 'job', 'marital', 'education', 'default', 'housing', 'loan', 'pdays', 'previous', 'poutcome'",
      "分类任务为二元分类",
      "正类标签为 'yes'",
      "评估指标为平均精度"
    ],
    "warnings": [
      "请求中未指定运行时间预算，将使用默认值 120 秒"
    ],
    "incompatible_requests": [],
    "requested_run_seconds": 120
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
      "score": 4.704421,
      "lexical_score": 3.731093,
      "graph_score": 0.973329,
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
          "bonus": 0.9733285267845754
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
      "score": 3.827987,
      "lexical_score": 2.433321,
      "graph_score": 1.394666,
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
              "to": "capability:bank-target:v2"
            }
          ],
          "bonus": 0.19466570535691508
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
      "score": 2.611546,
      "lexical_score": 0.648886,
      "graph_score": 1.96266,
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
          "bonus": 0.9733285267845754
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
          "bonus": 0.38933141071383015
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
      "score": 2.579101,
      "lexical_score": 0.811107,
      "graph_score": 1.767994,
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
          "bonus": 0.9733285267845754
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
          "bonus": 0.19466570535691508
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
      "score": 2.497771,
      "lexical_score": 0.811107,
      "graph_score": 1.686664,
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
          "bonus": 0.4866642633922877
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
      "score": 1.459993,
      "lexical_score": 0.973329,
      "graph_score": 0.486664,
      "evidence_path": [
        {
          "seed": "capability:bank-target:v2",
          "hops": [
            {
              "from": "capability:bank-target:v2",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            },
            {
              "from": "capability:average-precision:v1",
              "relation": "REQUIRES",
              "to": "capability:random-forest:v1"
            }
          ],
          "bonus": 0.4866642633922877
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
    }
  ],
  "quality_status": "above_prevalence",
  "explanation": {
    "summary": "候选模型 'logistic_default' 在验证集上表现良好，平均精度（average_precision）为 0.1829，比基线模型提高了 0.0722。在前 10% 的预测中，精确度和召回率分别为 0.2318 和 0.2094，提升率为 2.0938。ROC AUC 值为 0.6131。",
    "limitations": [
      "模型仅在验证集上评估，未在密封测试集上进行测试。",
      "验证集的正样本率为 0.1107，可能影响模型的泛化能力。",
      "模型选择不能证明因果营销提升。"
    ]
  },
  "finished_at": "2026-09-29T17:46:18.648483+00:00",
  "timing": {
    "wall_seconds": 25.887,
    "budget_seconds": 120.0,
    "request_ceiling_seconds": 900
  },
  "report_paths": {}
}
````

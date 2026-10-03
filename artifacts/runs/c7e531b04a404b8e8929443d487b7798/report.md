# 算法能力验证报告

指标与状态来自原始验证事实；缺失项不填零、不推断通过。

模式由原始报告的 mode 字段说明：mock 为模拟，replay 为历史回放。

````json
{
  "schema_version": "1.0",
  "run_id": "c7e531b04a404b8e8929443d487b7798",
  "status": "passed",
  "mode": "real",
  "provider": "deepseek",
  "description": "构建短信垃圾信息分类能力，比较 TF-IDF 与线性或朴素贝叶斯方案。保持训练、验证、测试隔离，报告 AP、F1 和接口检查结果。",
  "dataset_id": "sms",
  "created_at": "2026-09-28T13:23:38.365714+00:00",
  "request": {
    "description": "构建短信垃圾信息分类能力，比较 TF-IDF 与线性或朴素贝叶斯方案。保持训练、验证、测试隔离，报告 AP、F1 和接口检查结果。",
    "dataset_id": "sms",
    "provider": "deepseek",
    "max_candidates": 2,
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
        "rationale": "TF-IDF 稀疏文本特征配合逻辑回归，提供 predict_proba 概率接口用于 AP 计算；按 classes_ 映射正类 spam 列。",
        "evidence_ids": [
          "probability-logistic",
          "text-tfidf",
          "sms-format",
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
        "worker_pid": 35754,
        "wall_seconds": 0.8563070930540562,
        "fit_seconds": 0.10559422103688121,
        "predict_seconds": 0.01292603206820786,
        "worker_wall_seconds": 0.7254686099477112,
        "peak_rss_mib": 198.89453125,
        "cpu_seconds": 0.9629049999999999,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 0.8855881649069488
      },
      "repairs": [
        {
          "error_type": "plan_consistency",
          "diagnosis": "The generated code defines a function `broken_pipeline` that returns an unfitted sklearn Pipeline, but the task requires a constructor program that builds and returns a fitted estimator/pipeline for the text binary classification task. The code does not fit the pipeline on any training data, so it cannot be validated against the plan. Additionally, the function name and structure do not match the expected constructor-program interface (e.g., a `build_model` or `make_pipeline` function that returns a fitted model).",
          "fix": "Replace the function with a constructor that accepts the task spec and training data, builds the TfidfVectorizer and LogisticRegression pipeline, fits it on the provided text and labels, and returns the fitted pipeline. For example: `def build_model(task_spec, X_train, y_train): ... return pipeline.fit(X_train, y_train)` using the same hyperparameters and `random_state=task_spec['seed']`.",
          "repairable": true,
          "attempt": 1,
          "before_hash": "8c92c442576124df7df5640e220edf6e007603a7631e488b3ad86b8bf86ae7d5",
          "after_hash": "b124749acb20e16c4240897b8ddcd76195f755531d5bfd8753ee3059b9f3373f",
          "validated": true
        }
      ],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "8c92c442576124df7df5640e220edf6e007603a7631e488b3ad86b8bf86ae7d5",
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
          "code_sha256": "b124749acb20e16c4240897b8ddcd76195f755531d5bfd8753ee3059b9f3373f",
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
            "worker_pid": 35754,
            "wall_seconds": 0.8563070930540562,
            "fit_seconds": 0.10559422103688121,
            "predict_seconds": 0.01292603206820786,
            "worker_wall_seconds": 0.7254686099477112,
            "peak_rss_mib": 198.89453125,
            "cpu_seconds": 0.9629049999999999,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 0.8855881649069488
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
      "code_sha256": "b124749acb20e16c4240897b8ddcd76195f755531d5bfd8753ee3059b9f3373f",
      "code_path": "candidates/sms_logreg_default/attempt_1/model.py",
      "explanation": "Corrects the plan-consistency error by renaming the function to build_pipeline (the required constructor interface) while keeping the TF-IDF (1,2)-gram plus LogisticRegression(max_iter=1000, random_state=seed) pipeline from the plan and reference, with no fitting or data access in the constructor."
    },
    {
      "candidate_id": "sms_cnb_default",
      "plan": {
        "candidate_id": "sms_cnb_default",
        "algorithm": "nb",
        "variant": "default",
        "rationale": "ComplementNB 面向不平衡非负文本计数/TF-IDF 特征，与逻辑回归形成线性与朴素贝叶斯方案对比。",
        "evidence_ids": [
          "complement-naive-bayes",
          "text-tfidf",
          "sms-format",
          "average-precision"
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
        "worker_pid": 35800,
        "wall_seconds": 0.8029979940038174,
        "fit_seconds": 0.0684406440705061,
        "predict_seconds": 0.01245810091495514,
        "worker_wall_seconds": 0.6536766130011529,
        "peak_rss_mib": 200.89453125,
        "cpu_seconds": 0.8707320000000001,
        "sklearn_version": "1.7.2",
        "python_version": "3.10.8",
        "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
        "joblib_backend": "threading",
        "repeat_prediction_max_abs_delta": 0.0,
        "total_seconds": 0.8294324239250273
      },
      "repairs": [],
      "attempts": [
        {
          "attempt": 0,
          "code_sha256": "1176a4eaecfb06aa895e14053462ab3fc7ed8f1b917aaa717ae62f9bc8428860",
          "code_path": "candidates/sms_cnb_default/attempt_0/model.py",
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
            "worker_pid": 35800,
            "wall_seconds": 0.8029979940038174,
            "fit_seconds": 0.0684406440705061,
            "predict_seconds": 0.01245810091495514,
            "worker_wall_seconds": 0.6536766130011529,
            "peak_rss_mib": 200.89453125,
            "cpu_seconds": 0.8707320000000001,
            "sklearn_version": "1.7.2",
            "python_version": "3.10.8",
            "memory_limit_kind": "virtual_address_space_RLIMIT_AS",
            "joblib_backend": "threading",
            "repeat_prediction_max_abs_delta": 0.0,
            "total_seconds": 0.8294324239250273
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
      "artifact_id": "sms_cnb_default",
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
      "code_path": "candidates/sms_cnb_default/attempt_0/model.py",
      "explanation": "Plan variant=default selects ComplementNB on TF-IDF (1,2)-grams with min_df=2 and max_features=30000 per the text-tfidf and complement-naive-bayes evidence, using default alpha=1.0 and no random_state since ComplementNB does not accept it."
    }
  ],
  "selected_candidate_id": "sms_logreg_default",
  "events": [
    {
      "sequence": 0,
      "event_type": "RECEIVED",
      "type": "RECEIVED",
      "created_at": "2026-09-28T13:23:38.481485+00:00",
      "data": {
        "mode": "real",
        "model": "deepseek-flash"
      }
    },
    {
      "sequence": 1,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T13:23:42.329657+00:00",
      "data": {
        "role": "interpreter",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "5a1f674a-be98-44bf-91b3-4c422bff2b1e",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "1fb8e6190df5782915d1d00ae8bda50f75a592af50b11ce308290ca6c6a4a45f",
        "response_sha256": "c8997027d1afa2a115d8360bc7e061bbadf7a01cb3799bb851c7a1986957cbc7",
        "input_tokens": 418,
        "output_tokens": 423,
        "seconds": 2.897,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 2,
      "event_type": "SPEC_VALIDATED",
      "type": "SPEC_VALIDATED",
      "created_at": "2026-09-28T13:23:42.601141+00:00",
      "data": {
        "task_type": "text_binary_classification",
        "assumptions": [
          "'线性或朴素贝叶斯方案'指 TF-IDF 加线性模型（如逻辑回归/线性 SVM）与 TF-IDF 加朴素贝叶斯两类候选。",
          "F1 按正类 spam 计算。",
          "接口检查指对输入/输出契约与预测接口的合规性验证。",
          "未指定整轮墙钟预算，因此不设置 requested_run_seconds，沿用宿主 timeout_s=120。"
        ]
      }
    },
    {
      "sequence": 3,
      "event_type": "KNOWLEDGE_RETRIEVED",
      "type": "KNOWLEDGE_RETRIEVED",
      "created_at": "2026-09-28T13:23:42.824338+00:00",
      "data": {
        "count": 6,
        "use_graph": true,
        "capability_ids": [
          "complement-naive-bayes",
          "text-tfidf",
          "probability-logistic",
          "sms-format",
          "average-precision",
          "sms-grouped-split"
        ]
      }
    },
    {
      "sequence": 4,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T13:23:44.714401+00:00",
      "data": {
        "role": "planner",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "ab9f05f8-604b-41e9-b0bc-3fc3c449561d",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "7aece00a28ea7abf21f9cc780bd3b39ae6ef6d3ff7950a0890080379d0e1ca85",
        "response_sha256": "9b749c06cc121dfdd74351eecdc689f6cd5886676d09675dcd177aeaec9cddf0",
        "input_tokens": 8802,
        "output_tokens": 172,
        "seconds": 1.666,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 5,
      "event_type": "CANDIDATE_PLANNED",
      "type": "CANDIDATE_PLANNED",
      "created_at": "2026-09-28T13:23:44.974859+00:00",
      "data": {
        "candidate_id": "sms_logreg_default",
        "algorithm": "logistic",
        "variant": "default",
        "rationale": "TF-IDF 稀疏文本特征配合逻辑回归，提供 predict_proba 概率接口用于 AP 计算；按 classes_ 映射正类 spam 列。",
        "evidence_ids": [
          "probability-logistic",
          "text-tfidf",
          "sms-format",
          "average-precision"
        ],
        "parent_id": null
      }
    },
    {
      "sequence": 6,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T13:23:46.639783+00:00",
      "data": {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "6a781cad-a165-433a-8cf5-e13d66a0e311",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "f88b08b183cd57a205f0bb8f35073737b39c81daa3f7c464714fbd6ba41bb430",
        "response_sha256": "664e4f3d9972ebd7c7a166bb65cf18e7e4085301fc6858de354a73d395204d75",
        "input_tokens": 9258,
        "output_tokens": 177,
        "seconds": 1.403,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 7,
      "event_type": "FAILURE_INJECTED",
      "type": "FAILURE_INJECTED",
      "created_at": "2026-09-28T13:23:46.926242+00:00",
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
      "created_at": "2026-09-28T13:23:47.251670+00:00",
      "data": {
        "candidate_id": "sms_logreg_default",
        "attempt": 0,
        "code_sha256": "8c92c442576124df7df5640e220edf6e007603a7631e488b3ad86b8bf86ae7d5"
      }
    },
    {
      "sequence": 9,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T13:23:47.465422+00:00",
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
      "created_at": "2026-09-28T13:23:59.224534+00:00",
      "data": {
        "role": "reviewer",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "e58e2b01-27e2-4a70-a65c-5aff77e2965d",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "77693600cbc9e052a4c779e20323e20021216283d7191f9fc925a0ad124e35d9",
        "response_sha256": "c4e7a3dbc2a8fb320208ddf465ccc9ca437b2a0a478a1fefb380e9cd33747fba",
        "input_tokens": 466,
        "output_tokens": 209,
        "seconds": 11.526,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 11,
      "event_type": "REPAIR_PLANNED",
      "type": "REPAIR_PLANNED",
      "created_at": "2026-09-28T13:23:59.526242+00:00",
      "data": {
        "candidate_id": "sms_logreg_default",
        "error_type": "plan_consistency",
        "diagnosis": "The generated code defines a function `broken_pipeline` that returns an unfitted sklearn Pipeline, but the task requires a constructor program that builds and returns a fitted estimator/pipeline for the text binary classification task. The code does not fit the pipeline on any training data, so it cannot be validated against the plan. Additionally, the function name and structure do not match the expected constructor-program interface (e.g., a `build_model` or `make_pipeline` function that returns a fitted model).",
        "fix": "Replace the function with a constructor that accepts the task spec and training data, builds the TfidfVectorizer and LogisticRegression pipeline, fits it on the provided text and labels, and returns the fitted pipeline. For example: `def build_model(task_spec, X_train, y_train): ... return pipeline.fit(X_train, y_train)` using the same hyperparameters and `random_state=task_spec['seed']`.",
        "repairable": true
      }
    },
    {
      "sequence": 12,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T13:24:02.701712+00:00",
      "data": {
        "role": "repair_coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "9a9c6ee3-ed3a-4911-b05d-3a7083f9bba8",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "1bfd17e77ccd38dec5b991b9f08f0712be637eced3f036899c86935400f72555",
        "response_sha256": "477f9cb164eb78d1ebfab7c8deaa4a0155b4fd95f68bf7ac4cbb263c4ed3bcfe",
        "input_tokens": 9595,
        "output_tokens": 195,
        "seconds": 2.927,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 13,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T13:24:02.963655+00:00",
      "data": {
        "candidate_id": "sms_logreg_default",
        "attempt": 1,
        "code_sha256": "b124749acb20e16c4240897b8ddcd76195f755531d5bfd8753ee3059b9f3373f"
      }
    },
    {
      "sequence": 14,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T13:24:04.056795+00:00",
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
      "created_at": "2026-09-28T13:24:04.297787+00:00",
      "data": {
        "candidate_id": "sms_cnb_default",
        "algorithm": "nb",
        "variant": "default",
        "rationale": "ComplementNB 面向不平衡非负文本计数/TF-IDF 特征，与逻辑回归形成线性与朴素贝叶斯方案对比。",
        "evidence_ids": [
          "complement-naive-bayes",
          "text-tfidf",
          "sms-format",
          "average-precision"
        ],
        "parent_id": null
      }
    },
    {
      "sequence": 16,
      "event_type": "LLM_RESPONSE",
      "type": "LLM_RESPONSE",
      "created_at": "2026-09-28T13:24:10.691923+00:00",
      "data": {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "dab1ca44-aa46-4818-ac56-de5b5f650b1d",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "492cfd0b228bcb81a1afe6704a87990d74b27c9c9130e7c5f0dc6dc3f36e570e",
        "response_sha256": "5d72aef0e9d2cf8d8c083c805a659e14cd3658ec9c7f1af7fd474ac68cabc89b",
        "input_tokens": 9249,
        "output_tokens": 178,
        "seconds": 6.137,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 17,
      "event_type": "VALIDATING",
      "type": "VALIDATING",
      "created_at": "2026-09-28T13:24:11.031079+00:00",
      "data": {
        "candidate_id": "sms_cnb_default",
        "attempt": 0,
        "code_sha256": "1176a4eaecfb06aa895e14053462ab3fc7ed8f1b917aaa717ae62f9bc8428860"
      }
    },
    {
      "sequence": 18,
      "event_type": "VERIFIED",
      "type": "VERIFIED",
      "created_at": "2026-09-28T13:24:12.555728+00:00",
      "data": {
        "candidate_id": "sms_cnb_default",
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
      "created_at": "2026-09-28T13:24:15.767024+00:00",
      "data": {
        "role": "curator",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "8be28e6c-8a52-42e8-9fe7-18b462f44f4e",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "e71d273d034ca062f745d1e6c6897703aaf430583357edbc42b1a96c13e8e756",
        "response_sha256": "1ecfd9bdc68213de4cce7a3beff50bb1009f4d525a8521de589fc290078d7b6c",
        "input_tokens": 707,
        "output_tokens": 439,
        "seconds": 2.812,
        "finish_reason": "stop"
      }
    },
    {
      "sequence": 20,
      "event_type": "COMPARED",
      "type": "COMPARED",
      "created_at": "2026-09-28T13:24:16.138002+00:00",
      "data": {
        "selected_candidate_id": "sms_logreg_default"
      }
    },
    {
      "sequence": 21,
      "event_type": "RECORDED",
      "type": "RECORDED",
      "created_at": "2026-09-28T13:24:16.853227+00:00",
      "data": {
        "intended_status": "passed",
        "experiences": 1
      }
    }
  ],
  "usage": {
    "calls": 7,
    "input_tokens": 38495,
    "output_tokens": 1793,
    "cached_input_tokens": 18688,
    "records": [
      {
        "role": "interpreter",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "5a1f674a-be98-44bf-91b3-4c422bff2b1e",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "1fb8e6190df5782915d1d00ae8bda50f75a592af50b11ce308290ca6c6a4a45f",
        "response_sha256": "c8997027d1afa2a115d8360bc7e061bbadf7a01cb3799bb851c7a1986957cbc7",
        "input_tokens": 418,
        "output_tokens": 423,
        "seconds": 2.897,
        "finish_reason": "stop"
      },
      {
        "role": "planner",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "ab9f05f8-604b-41e9-b0bc-3fc3c449561d",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "7aece00a28ea7abf21f9cc780bd3b39ae6ef6d3ff7950a0890080379d0e1ca85",
        "response_sha256": "9b749c06cc121dfdd74351eecdc689f6cd5886676d09675dcd177aeaec9cddf0",
        "input_tokens": 8802,
        "output_tokens": 172,
        "seconds": 1.666,
        "finish_reason": "stop"
      },
      {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "6a781cad-a165-433a-8cf5-e13d66a0e311",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "f88b08b183cd57a205f0bb8f35073737b39c81daa3f7c464714fbd6ba41bb430",
        "response_sha256": "664e4f3d9972ebd7c7a166bb65cf18e7e4085301fc6858de354a73d395204d75",
        "input_tokens": 9258,
        "output_tokens": 177,
        "seconds": 1.403,
        "finish_reason": "stop"
      },
      {
        "role": "reviewer",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "e58e2b01-27e2-4a70-a65c-5aff77e2965d",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "77693600cbc9e052a4c779e20323e20021216283d7191f9fc925a0ad124e35d9",
        "response_sha256": "c4e7a3dbc2a8fb320208ddf465ccc9ca437b2a0a478a1fefb380e9cd33747fba",
        "input_tokens": 466,
        "output_tokens": 209,
        "seconds": 11.526,
        "finish_reason": "stop"
      },
      {
        "role": "repair_coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "9a9c6ee3-ed3a-4911-b05d-3a7083f9bba8",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "1bfd17e77ccd38dec5b991b9f08f0712be637eced3f036899c86935400f72555",
        "response_sha256": "477f9cb164eb78d1ebfab7c8deaa4a0155b4fd95f68bf7ac4cbb263c4ed3bcfe",
        "input_tokens": 9595,
        "output_tokens": 195,
        "seconds": 2.927,
        "finish_reason": "stop"
      },
      {
        "role": "coder",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "dab1ca44-aa46-4818-ac56-de5b5f650b1d",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "492cfd0b228bcb81a1afe6704a87990d74b27c9c9130e7c5f0dc6dc3f36e570e",
        "response_sha256": "5d72aef0e9d2cf8d8c083c805a659e14cd3658ec9c7f1af7fd474ac68cabc89b",
        "input_tokens": 9249,
        "output_tokens": 178,
        "seconds": 6.137,
        "finish_reason": "stop"
      },
      {
        "role": "curator",
        "requested_model": "deepseek-flash",
        "returned_model": "deepseek-flash",
        "response_id": "8be28e6c-8a52-42e8-9fe7-18b462f44f4e",
        "system_fingerprint": "aeb56401ca74e127821c4f9126dcb669",
        "prompt_sha256": "e71d273d034ca062f745d1e6c6897703aaf430583357edbc42b1a96c13e8e756",
        "response_sha256": "1ecfd9bdc68213de4cce7a3beff50bb1009f4d525a8521de589fc290078d7b6c",
        "input_tokens": 707,
        "output_tokens": 439,
        "seconds": 2.812,
        "finish_reason": "stop"
      }
    ]
  },
  "warnings": [
    "验证集成绩，不是最终测试成绩。",
    "受限AST构造器程序，不是任意Python或Docker操作系统沙箱。",
    "未提供客户端 ID 字段，无法承诺或验证跨客户端分离；只能依据 normalized_group_split_v1 在现有分组字段上做隔离。",
    "若数据中不存在可用的分组字段，normalized_group_split_v1 的隔离效果可能受限，需在接口检查中说明。",
    "AP 与 F1 需在隔离的测试集上报告，验证集仅用于选择方案与阈值。"
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
      "candidate_id": "sms_cnb_default",
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
        "failure_id": "failure-04ea8a1230f21b06f3d28b28",
        "fingerprint": "8520d1159bc2b15b0e2c3545c66fd60999531193610eb14bc9928c47a915c44a",
        "run_id": "c7e531b04a404b8e8929443d487b7798",
        "error_type": "plan_consistency",
        "diagnosis": "The generated code defines a function `broken_pipeline` that returns an unfitted sklearn Pipeline, but the task requires a constructor program that builds and returns a fitted estimator/pipeline for the text binary classification task. The code does not fit the pipeline on any training data, so it cannot be validated against the plan. Additionally, the function name and structure do not match the expected constructor-program interface (e.g., a `build_model` or `make_pipeline` function that returns a fitted model).",
        "fix": "Replace the function with a constructor that accepts the task spec and training data, builds the TfidfVectorizer and LogisticRegression pipeline, fits it on the provided text and labels, and returns the fitted pipeline. For example: `def build_model(task_spec, X_train, y_train): ... return pipeline.fit(X_train, y_train)` using the same hyperparameters and `random_state=task_spec['seed']`.",
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
    "objective": "构建短信垃圾信息二分类能力，在固定数据集 sms 上比较 TF-IDF 特征配合线性模型与朴素贝叶斯方案，并按 normalized_group_split_v1 保持训练/验证/测试隔离，报告平均精度（AP）、F1 以及接口检查结果。",
    "constraints": [
      "仅使用 task_spec 指定的数据集 sms 与特征 text（categorical_features=['text']，numeric_features=[]）。",
      "任务类型为 text_binary_classification，正类标签为 spam，主指标为 average_precision。",
      "特征策略固定为 normalized_group_split_v1，不得更改划分协议或评估标签。",
      "随机种子固定为 seed=42。",
      "资源上限：cpu=2、memory_mib=2048、timeout_s=120，不得超出。",
      "仅使用受支持的算法：TF-IDF 特征配合线性分类器或朴素贝叶斯。",
      "结果需报告 AP、F1 与接口检查结果。",
      "不得请求或泄露凭据，不得修改 task_spec。"
    ],
    "assumptions": [
      "'线性或朴素贝叶斯方案'指 TF-IDF 加线性模型（如逻辑回归/线性 SVM）与 TF-IDF 加朴素贝叶斯两类候选。",
      "F1 按正类 spam 计算。",
      "接口检查指对输入/输出契约与预测接口的合规性验证。",
      "未指定整轮墙钟预算，因此不设置 requested_run_seconds，沿用宿主 timeout_s=120。"
    ],
    "warnings": [
      "未提供客户端 ID 字段，无法承诺或验证跨客户端分离；只能依据 normalized_group_split_v1 在现有分组字段上做隔离。",
      "若数据中不存在可用的分组字段，normalized_group_split_v1 的隔离效果可能受限，需在接口检查中说明。",
      "AP 与 F1 需在隔离的测试集上报告，验证集仅用于选择方案与阈值。"
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
      "score": 3.965294,
      "lexical_score": 2.53421,
      "graph_score": 1.431084,
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
          "bonus": 1.0733126291998991
        },
        {
          "seed": "capability:average-precision:v1",
          "hops": [
            {
              "from": "capability:average-precision:v1",
              "relation": "REQUIRES",
              "to": "capability:complement-naive-bayes:v1"
            }
          ],
          "bonus": 0.35777087639996635
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
      "score": 3.875851,
      "lexical_score": 2.683282,
      "graph_score": 1.19257,
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
          "bonus": 1.0136841497999047
        },
        {
          "seed": "capability:average-precision:v1",
          "hops": [
            {
              "from": "capability:average-precision:v1",
              "relation": "REQUIRES",
              "to": "capability:complement-naive-bayes:v1"
            },
            {
              "from": "capability:complement-naive-bayes:v1",
              "relation": "REQUIRES",
              "to": "capability:text-tfidf:v1"
            }
          ],
          "bonus": 0.17888543819998318
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
      "score": 2.832353,
      "lexical_score": 0.894427,
      "graph_score": 1.937926,
      "evidence_path": [
        {
          "seed": "capability:text-tfidf:v1",
          "hops": [
            {
              "from": "capability:text-tfidf:v1",
              "relation": "REQUIRES",
              "to": "capability:probability-logistic:v1"
            }
          ],
          "bonus": 1.0733126291998991
        },
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
          "bonus": 0.5068420748999524
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
          "bonus": 0.35777087639996635
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
      "score": 2.683282,
      "lexical_score": 0.745356,
      "graph_score": 1.937926,
      "evidence_path": [
        {
          "seed": "capability:text-tfidf:v1",
          "hops": [
            {
              "from": "capability:text-tfidf:v1",
              "relation": "REQUIRES",
              "to": "capability:sms-format:v1"
            }
          ],
          "bonus": 1.0733126291998991
        },
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
          "bonus": 0.5068420748999524
        },
        {
          "seed": "capability:average-precision:v1",
          "hops": [
            {
              "from": "capability:average-precision:v1",
              "relation": "REQUIRES",
              "to": "capability:sms-format:v1"
            }
          ],
          "bonus": 0.35777087639996635
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
      "score": 2.444768,
      "lexical_score": 0.894427,
      "graph_score": 1.55034,
      "evidence_path": [
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
          "bonus": 0.5366563145999496
        },
        {
          "seed": "capability:complement-naive-bayes:v1",
          "hops": [
            {
              "from": "capability:complement-naive-bayes:v1",
              "relation": "REQUIRES",
              "to": "capability:average-precision:v1"
            }
          ],
          "bonus": 1.0136841497999047
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
      "score": 2.325511,
      "lexical_score": 0.745356,
      "graph_score": 1.580155,
      "evidence_path": [
        {
          "seed": "capability:text-tfidf:v1",
          "hops": [
            {
              "from": "capability:text-tfidf:v1",
              "relation": "REQUIRES",
              "to": "capability:sms-grouped-split:v1"
            }
          ],
          "bonus": 1.0733126291998991
        },
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
          "bonus": 0.5068420748999524
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
    "summary": "在仅使用验证集（validation_only，1032 行，正例率 0.125）的独立测量中，两个候选均通过。sms_logreg_default 的平均精度（AP）为 0.9584，较 dummy 基线（0.125）提升 0.8334，ROC-AUC 为 0.9881，阈值 0.5 下 F1 为 0.8056，前 10% 的 precision/recall/lift 分别为 0.9904/0.7984/7.9231。sms_cnb_default 的 AP 为 0.9459，提升 0.8209，ROC-AUC 为 0.9781，阈值 0.5 下 F1 为 0.9024，前 10% 的 precision/recall/lift 分别为 1.0/0.8062/8.0。两者排序指标接近，logreg 在 AP 与 ROC-AUC 上略高，cnb 在 F1 与 top-10% 精确率上略高；最终选择 sms_logreg_default。相关能力证据包括 probability-logistic、complement-naive-bayes、text-tfidf、sms-format、average-precision 与 sms-grouped-split。",
    "limitations": [
      "所有数值均为验证集结果（evaluation_split=validation_only，sealed_test_scored=false），不代表最终测试集性能，不能据此推断泛化表现。",
      "排序并列采用 original_validation_row_order 作为 tie-break，可能影响 top-10% 指标的稳定性。",
      "约束式 AST 执行仅用于受控的候选评估，不等同于通用操作系统沙箱，不能提供完整隔离保证。",
      "模型选择（sms_logreg_default 对比 sms_cnb_default）仅反映本数据集上的预测指标差异，不构成因果性的营销提升证明。",
      "两个候选的指标差距较小，且未报告置信区间或多次重复实验，结论稳健性有限。"
    ]
  },
  "finished_at": "2026-09-28T13:24:16.573183+00:00",
  "timing": {
    "wall_seconds": 38.208,
    "budget_seconds": 900.0,
    "request_ceiling_seconds": 900
  },
  "report_paths": {}
}
````

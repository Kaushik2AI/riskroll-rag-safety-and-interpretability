# Experiment 7D: ALCE-QAMPARI Actual LLM Generation (qwen7b_qampari_100_v3)

- Model: `/projectnb/medaihack/team4/kaushik_work/hf_cache/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28`
- Tasks: 100
- Temperature: 0.0

## Results

### Standard RAG top-1
- answer_precision: 0.268
- answer_recall: 0.112
- answer_f1: 0.145
- support_rate: 0.768
- strict_grounded_rate: 0.112
- clean_task_rate: 0.010
- mean_unsupported_commits: 0.090
- mean_abstention_count: 3.500
- mean_unsafe_prefix_depth: 0.020
- mean_downstream_contaminated_claims: 0.020
- mean_rollback_count: 0.000
- mean_repair_count: 0.000

### Retrieve-more RAG top-20
- answer_precision: 0.385
- answer_recall: 0.262
- answer_f1: 0.297
- support_rate: 0.873
- strict_grounded_rate: 0.244
- clean_task_rate: 0.040
- mean_unsupported_commits: 0.300
- mean_abstention_count: 1.740
- mean_unsafe_prefix_depth: 0.270
- mean_downstream_contaminated_claims: 0.270
- mean_rollback_count: 0.000
- mean_repair_count: 0.000

### Post-hoc correction top-20
- answer_precision: 0.358
- answer_recall: 0.186
- answer_f1: 0.227
- support_rate: 0.937
- strict_grounded_rate: 0.182
- clean_task_rate: 0.010
- mean_unsupported_commits: 0.110
- mean_abstention_count: 2.530
- mean_unsafe_prefix_depth: 0.080
- mean_downstream_contaminated_claims: 0.080
- mean_rollback_count: 0.000
- mean_repair_count: 1.970

### CRAG-style correction top-20
- answer_precision: 0.394
- answer_recall: 0.232
- answer_f1: 0.273
- support_rate: 0.828
- strict_grounded_rate: 0.216
- clean_task_rate: 0.030
- mean_unsupported_commits: 0.350
- mean_abstention_count: 2.120
- mean_unsafe_prefix_depth: 0.240
- mean_downstream_contaminated_claims: 0.240
- mean_rollback_count: 0.000
- mean_repair_count: 0.000

### RiskRoll verify-before-commit top-20
- answer_precision: 0.326
- answer_recall: 0.268
- answer_f1: 0.284
- support_rate: 0.990
- strict_grounded_rate: 0.268
- clean_task_rate: 0.050
- mean_unsupported_commits: 0.000
- mean_abstention_count: 1.110
- mean_unsafe_prefix_depth: 0.000
- mean_downstream_contaminated_claims: 0.000
- mean_rollback_count: 0.680
- mean_repair_count: 2.570


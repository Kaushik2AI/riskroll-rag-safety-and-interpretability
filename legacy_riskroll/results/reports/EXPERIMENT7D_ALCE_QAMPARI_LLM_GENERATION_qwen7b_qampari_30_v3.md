# Experiment 7D: ALCE-QAMPARI Actual LLM Generation (qwen7b_qampari_30_v3)

- Model: `/projectnb/medaihack/team4/kaushik_work/hf_cache/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28`
- Tasks: 30
- Temperature: 0.0

## Results

### Standard RAG top-1
- answer_precision: 0.340
- answer_recall: 0.167
- answer_f1: 0.207
- support_rate: 0.733
- strict_grounded_rate: 0.167
- clean_task_rate: 0.033
- mean_unsupported_commits: 0.167
- mean_abstention_count: 3.367
- mean_unsafe_prefix_depth: 0.000
- mean_downstream_contaminated_claims: 0.000
- mean_rollback_count: 0.000
- mean_repair_count: 0.000

### Retrieve-more RAG top-20
- answer_precision: 0.454
- answer_recall: 0.313
- answer_f1: 0.351
- support_rate: 0.925
- strict_grounded_rate: 0.293
- clean_task_rate: 0.067
- mean_unsupported_commits: 0.367
- mean_abstention_count: 1.633
- mean_unsafe_prefix_depth: 0.400
- mean_downstream_contaminated_claims: 0.400
- mean_rollback_count: 0.000
- mean_repair_count: 0.000

### Post-hoc correction top-20
- answer_precision: 0.432
- answer_recall: 0.220
- answer_f1: 0.269
- support_rate: 0.907
- strict_grounded_rate: 0.213
- clean_task_rate: 0.033
- mean_unsupported_commits: 0.200
- mean_abstention_count: 2.567
- mean_unsafe_prefix_depth: 0.100
- mean_downstream_contaminated_claims: 0.100
- mean_rollback_count: 0.000
- mean_repair_count: 2.000

### CRAG-style correction top-20
- answer_precision: 0.462
- answer_recall: 0.300
- answer_f1: 0.342
- support_rate: 0.900
- strict_grounded_rate: 0.293
- clean_task_rate: 0.100
- mean_unsupported_commits: 0.233
- mean_abstention_count: 2.033
- mean_unsafe_prefix_depth: 0.167
- mean_downstream_contaminated_claims: 0.167
- mean_rollback_count: 0.000
- mean_repair_count: 0.000

### RiskRoll verify-before-commit top-20
- answer_precision: 0.426
- answer_recall: 0.353
- answer_f1: 0.374
- support_rate: 1.000
- strict_grounded_rate: 0.353
- clean_task_rate: 0.100
- mean_unsupported_commits: 0.000
- mean_abstention_count: 0.933
- mean_unsafe_prefix_depth: 0.000
- mean_downstream_contaminated_claims: 0.000
- mean_rollback_count: 0.367
- mean_repair_count: 2.600


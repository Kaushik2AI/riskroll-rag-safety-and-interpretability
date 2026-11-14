# Experiment 7D: ALCE-QAMPARI Actual LLM Generation (qwen7b_smoke_v3)

- Model: `/projectnb/medaihack/team4/kaushik_work/hf_cache/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28`
- Tasks: 2
- Temperature: 0.0

## Results

### Standard RAG top-1
- answer_precision: 0.500
- answer_recall: 0.400
- answer_f1: 0.444
- support_rate: 0.500
- strict_grounded_rate: 0.400
- clean_task_rate: 0.000
- mean_unsupported_commits: 0.500
- mean_abstention_count: 2.500
- mean_unsafe_prefix_depth: 0.000
- mean_downstream_contaminated_claims: 0.000
- mean_rollback_count: 0.000
- mean_repair_count: 0.000

### Retrieve-more RAG top-20
- answer_precision: 0.500
- answer_recall: 0.500
- answer_f1: 0.500
- support_rate: 1.000
- strict_grounded_rate: 0.500
- clean_task_rate: 0.500
- mean_unsupported_commits: 0.000
- mean_abstention_count: 0.500
- mean_unsafe_prefix_depth: 0.000
- mean_downstream_contaminated_claims: 0.000
- mean_rollback_count: 0.000
- mean_repair_count: 0.000

### Post-hoc correction top-20
- answer_precision: 0.500
- answer_recall: 0.300
- answer_f1: 0.375
- support_rate: 1.000
- strict_grounded_rate: 0.300
- clean_task_rate: 0.000
- mean_unsupported_commits: 0.000
- mean_abstention_count: 2.500
- mean_unsafe_prefix_depth: 0.000
- mean_downstream_contaminated_claims: 0.000
- mean_rollback_count: 0.000
- mean_repair_count: 1.500

### CRAG-style correction top-20
- answer_precision: 0.500
- answer_recall: 0.500
- answer_f1: 0.500
- support_rate: 0.500
- strict_grounded_rate: 0.500
- clean_task_rate: 0.500
- mean_unsupported_commits: 0.500
- mean_abstention_count: 2.000
- mean_unsafe_prefix_depth: 0.000
- mean_downstream_contaminated_claims: 0.000
- mean_rollback_count: 0.000
- mean_repair_count: 0.000

### RiskRoll verify-before-commit top-20
- answer_precision: 0.500
- answer_recall: 0.500
- answer_f1: 0.500
- support_rate: 1.000
- strict_grounded_rate: 0.500
- clean_task_rate: 0.500
- mean_unsupported_commits: 0.000
- mean_abstention_count: 1.000
- mean_unsafe_prefix_depth: 0.000
- mean_downstream_contaminated_claims: 0.000
- mean_rollback_count: 0.500
- mean_repair_count: 1.500


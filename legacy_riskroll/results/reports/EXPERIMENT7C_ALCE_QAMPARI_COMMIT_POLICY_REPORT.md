# Experiment 7C: ALCE-QAMPARI Public Commit-Policy Comparison

## Purpose

Compare different public-data commit policies on ALCE-QAMPARI: standard top-1 commit, retrieve-more context, post-hoc correction, CRAG-style correction, and RiskRoll verify-before-commit.

## Important note

This experiment uses gold answer aliases to evaluate whether evidence supports a claim. It is a public commit-policy diagnostic, not the final neural generation experiment.

## Results

### Standard RAG top-1
- final_grounded_claim_rate: 0.188
- clean_task_rate: 0.040
- mean_unsafe_prefix_depth: 3.660
- mean_downstream_contaminated_claims: 3.660
- mean_unsupported_commits: 4.060
- mean_rollback_count: 0.000
- mean_abstention_count: 0.000
- mean_repair_count: 0.000

### Retrieve-more RAG top-20
- final_grounded_claim_rate: 0.674
- clean_task_rate: 0.340
- mean_unsafe_prefix_depth: 2.090
- mean_downstream_contaminated_claims: 2.090
- mean_unsupported_commits: 1.630
- mean_rollback_count: 0.000
- mean_abstention_count: 0.000
- mean_repair_count: 0.000

### Post-hoc correction top-20
- final_grounded_claim_rate: 0.674
- clean_task_rate: 0.340
- mean_unsafe_prefix_depth: 3.660
- mean_downstream_contaminated_claims: 3.660
- mean_unsupported_commits: 4.060
- mean_rollback_count: 0.000
- mean_abstention_count: 0.000
- mean_repair_count: 2.430

### CRAG-style correction top-20
- final_grounded_claim_rate: 0.674
- clean_task_rate: 0.340
- mean_unsafe_prefix_depth: 2.090
- mean_downstream_contaminated_claims: 2.090
- mean_unsupported_commits: 1.630
- mean_rollback_count: 0.000
- mean_abstention_count: 0.000
- mean_repair_count: 0.000

### RiskRoll top-20 verify-before-commit
- final_grounded_claim_rate: 0.674
- clean_task_rate: 0.340
- mean_unsafe_prefix_depth: 0.000
- mean_downstream_contaminated_claims: 0.000
- mean_unsupported_commits: 0.000
- mean_rollback_count: 49.560
- mean_abstention_count: 1.630
- mean_repair_count: 2.430

## Interpretation

Retrieve-more, post-hoc correction, and CRAG-style correction can improve final grounding when supporting evidence appears in top-20. However, they do not model the answer as a trusted semantic prefix. RiskRoll has the same top-20 evidence ceiling but avoids unsupported commits by abstaining when no supporting evidence is found.

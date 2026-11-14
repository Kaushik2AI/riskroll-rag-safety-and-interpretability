# Experiment 7B: ALCE-QAMPARI Public Grounding Diagnostic

## Purpose

Evaluate whether the public ALCE-QAMPARI retrieval set creates a meaningful claim-level grounding setting for RiskRoll-RAG.

## Important note

This is an evidence-selection / grounding proxy, not the final LLM generation experiment. It uses gold answer aliases to determine whether a retrieved document supports a claim.

## Results

### Standard RAG top-1 commit
- grounded_claim_rate: 0.188
- clean_task_rate: 0.040
- mean_unsafe_prefix_depth: 3.660
- mean_downstream_contaminated_claims: 3.660
- mean_rollback_count: 0.000
- mean_abstention_count: 0.000

### Retrieve-more RAG top-5 context
- grounded_claim_rate: 0.398
- clean_task_rate: 0.110
- mean_unsafe_prefix_depth: 3.010
- mean_downstream_contaminated_claims: 3.010
- mean_rollback_count: 0.000
- mean_abstention_count: 0.000

### Retrieve-more RAG top-20 context
- grounded_claim_rate: 0.674
- clean_task_rate: 0.340
- mean_unsafe_prefix_depth: 2.090
- mean_downstream_contaminated_claims: 2.090
- mean_rollback_count: 0.000
- mean_abstention_count: 0.000

### RiskRoll top-20 verify-before-commit
- grounded_claim_rate: 0.674
- clean_task_rate: 0.340
- mean_unsafe_prefix_depth: 0.000
- mean_downstream_contaminated_claims: 0.000
- mean_rollback_count: 49.560
- mean_abstention_count: 1.630

## Interpretation

Top-1 retrieval is not sufficient for many ALCE-QAMPARI claims. Correct supporting evidence often appears deeper in the retrieval list. RiskRoll uses this setting as a verify-before-commit process: unsupported candidate evidence is rejected before entering the trusted semantic prefix.

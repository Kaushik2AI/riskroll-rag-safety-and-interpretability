# Experiment 5C: ChartQA Qwen VLM Strict Verifier

## Goal

Compare Standard top-1 ChartQA VLM answering with RiskRoll using a stricter non-oracle Qwen verifier.

## Summary

| Method | Claim Acc | Evidence Acc | Grounded Rate | Wrong Evidence | Unsafe Depth |
|---|---:|---:|---:|---:|---:|
| Standard RAG | 0.400 | 0.000 | 0.000 | 10 | 9 |
| RiskRoll | 0.600 | 0.200 | 0.200 | 8 | 8 |

## RiskRoll diagnostics

- Rollbacks: 12
- Repairs: 5
- Abstentions: 0
- Verifier false accepts: 8
- Verifier false rejects / abstentions: 0
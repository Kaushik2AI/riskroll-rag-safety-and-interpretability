# Experiment 5B: ChartQA Qwen VLM

## Goal

Compare Standard top-1 ChartQA VLM answering with RiskRoll using a non-oracle Qwen verifier.

## Summary

| Method | Claim Acc | Evidence Acc | Grounded Rate | Wrong Evidence | Unsafe Depth |
|---|---:|---:|---:|---:|---:|
| Standard RAG | 0.400 | 0.000 | 0.000 | 10 | 9 |
| RiskRoll | 0.700 | 0.300 | 0.300 | 7 | 7 |

## RiskRoll diagnostics

- Rollbacks: 13
- Repairs: 5
- Abstentions: 0
- Verifier false accepts: 7
- Verifier false rejects / abstentions: 0
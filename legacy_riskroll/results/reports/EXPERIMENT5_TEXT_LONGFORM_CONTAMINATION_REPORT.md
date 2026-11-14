# Experiment 5: Text-only Long-form Contamination Benchmark

## Goal

Evaluate RiskRoll-RAG on text-only long-form RAG tasks where each answer contains multiple claims and wrong-but-plausible near-miss evidence appears before gold evidence.

## Setup

- Tasks: 60
- Claims per task: 5
- Total claims: 300
- Top-k evidence candidates: 3

Each task has five claims about a hidden target report. The first retrieved passage is a near-miss from a different report, while the gold passage is rank 2.

## Summary

| Method | Claim Acc | Evidence Acc | Grounded Rate | Wrong Evidence | Unsafe Depth | Clean Task Rate | Rollbacks |
|---|---:|---:|---:|---:|---:|---:|---:|
| Standard RAG | 0.067 | 0.000 | 0.000 | 5.000 | 4.000 | 0.000 | 0.000 |
| Retrieve-more RAG | 0.067 | 0.000 | 0.000 | 5.000 | 4.000 | 0.000 | 0.000 |
| Post-hoc correction | 0.067 | 0.000 | 0.000 | 5.000 | 4.000 | 0.000 | 0.000 |
| CRAG-style correction | 0.067 | 0.000 | 0.000 | 5.000 | 4.000 | 0.000 | 0.000 |
| RiskRoll | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 | 5.000 |

## Interpretation

Standard and lexical correction baselines are expected to accept near-miss passages because the wrong and gold passages are lexically similar. RiskRoll uses controlled report-identity verification to rollback unsafe claims before they enter the trusted prefix.

## RiskRoll-specific claim

The main result is not only higher answer accuracy. The key result is reduced unsafe-prefix depth and downstream contamination.
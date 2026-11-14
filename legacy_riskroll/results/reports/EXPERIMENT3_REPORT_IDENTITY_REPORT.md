# Experiment 3: Report-Identity Near-Miss Stress Test

## Goal

Test a hard controlled setting where wrong evidence shares the same city, domain, modality, metric, and year as the gold evidence, but comes from the wrong report identity.

## Why this matters

Lexical evidence selection can fail because wrong and gold candidates look nearly identical. RiskRoll uses a controlled identity verifier to reject wrong-report evidence before committing a claim.

## Summary

| Method | Claim Acc | Evidence Acc | Grounded Rate | Wrong Evidence | Unsafe Depth | Rollbacks |
|---|---:|---:|---:|---:|---:|---:|
| Standard RAG | 0.144 | 0.000 | 0.000 | 3.000 | 2.000 | 0.000 |
| Retrieve-more RAG | 0.222 | 0.078 | 0.078 | 2.767 | 2.000 | 0.000 |
| Post-hoc correction | 0.144 | 0.000 | 0.000 | 3.000 | 2.000 | 0.000 |
| CRAG-style correction | 0.144 | 0.000 | 0.000 | 3.000 | 2.000 | 0.000 |
| RiskRoll | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 3.000 |
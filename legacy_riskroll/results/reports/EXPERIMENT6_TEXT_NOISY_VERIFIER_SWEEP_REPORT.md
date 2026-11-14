# Experiment 6: Text-only Noisy-Verifier Sweep

## Goal

Measure how RiskRoll-RAG behaves when the verifier makes controlled false-accept and false-reject errors.

## Key hypothesis

False accepts are more dangerous than false rejects. A false accept commits wrong evidence into the trusted prefix, while a false reject mostly causes additional rollback or abstention.

## Summary

| Sweep | FA | FR | Grounded | Evidence Acc | Contamination | Unsafe Depth | Abstention | Clean Task |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| false_accept_sweep | 0.00 | 0.00 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| false_accept_sweep | 0.02 | 0.00 | 0.983 | 0.983 | 0.133 | 0.133 | 0.000 | 0.917 |
| false_accept_sweep | 0.05 | 0.00 | 0.973 | 0.973 | 0.167 | 0.167 | 0.000 | 0.867 |
| false_accept_sweep | 0.10 | 0.00 | 0.927 | 0.927 | 0.500 | 0.500 | 0.000 | 0.650 |
| false_accept_sweep | 0.20 | 0.00 | 0.790 | 0.790 | 1.717 | 1.717 | 0.000 | 0.300 |
| false_accept_sweep | 0.30 | 0.00 | 0.713 | 0.713 | 2.133 | 2.133 | 0.000 | 0.217 |
| false_accept_sweep | 0.40 | 0.00 | 0.573 | 0.573 | 2.983 | 2.983 | 0.000 | 0.067 |
| false_accept_sweep | 0.50 | 0.00 | 0.453 | 0.453 | 3.217 | 3.217 | 0.000 | 0.050 |
| false_reject_sweep | 0.00 | 0.00 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| false_reject_sweep | 0.00 | 0.05 | 0.947 | 0.947 | 0.000 | 0.000 | 0.267 | 0.767 |
| false_reject_sweep | 0.00 | 0.10 | 0.933 | 0.933 | 0.000 | 0.000 | 0.333 | 0.683 |
| false_reject_sweep | 0.00 | 0.20 | 0.827 | 0.827 | 0.000 | 0.000 | 0.867 | 0.417 |
| false_reject_sweep | 0.00 | 0.30 | 0.653 | 0.653 | 0.000 | 0.000 | 1.733 | 0.117 |
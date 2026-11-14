# Experiment 4: Detector-Quality Sweep

## Goal

Measure how RiskRoll depends on verifier quality. False accepts allow wrong evidence to enter the trusted prefix, while false rejects cause unnecessary rollbacks or abstentions.

## Key interpretation

If the verifier false-accepts wrong evidence, rollback does not trigger. Therefore grounding accuracy drops and downstream contamination increases.

## Summary

| Sweep | FA | FR | Claim Acc | Evidence Acc | Grounded | Contamination | Unsafe Depth | Abstention |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| false_accept_sweep | 0.00 | 0.00 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| false_accept_sweep | 0.02 | 0.00 | 0.978 | 0.978 | 0.978 | 0.067 | 0.067 | 0.000 |
| false_accept_sweep | 0.05 | 0.00 | 0.967 | 0.967 | 0.967 | 0.100 | 0.100 | 0.000 |
| false_accept_sweep | 0.10 | 0.00 | 0.922 | 0.922 | 0.922 | 0.233 | 0.233 | 0.000 |
| false_accept_sweep | 0.20 | 0.00 | 0.811 | 0.811 | 0.811 | 0.567 | 0.567 | 0.000 |
| false_accept_sweep | 0.30 | 0.00 | 0.756 | 0.700 | 0.700 | 0.833 | 0.833 | 0.000 |
| false_accept_sweep | 0.40 | 0.00 | 0.600 | 0.522 | 0.522 | 1.233 | 1.233 | 0.000 |
| false_accept_sweep | 0.50 | 0.00 | 0.511 | 0.467 | 0.467 | 1.300 | 1.300 | 0.000 |
| false_reject_sweep | 0.00 | 0.00 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| false_reject_sweep | 0.00 | 0.05 | 0.933 | 0.933 | 0.933 | 0.000 | 0.000 | 0.200 |
| false_reject_sweep | 0.00 | 0.10 | 0.922 | 0.922 | 0.922 | 0.000 | 0.000 | 0.233 |
| false_reject_sweep | 0.00 | 0.20 | 0.833 | 0.833 | 0.833 | 0.000 | 0.000 | 0.500 |
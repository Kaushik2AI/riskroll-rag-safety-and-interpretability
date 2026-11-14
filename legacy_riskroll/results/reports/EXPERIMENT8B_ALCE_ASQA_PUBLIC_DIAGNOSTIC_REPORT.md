# Experiment 8B: ALCE-ASQA Public Diagnostic

This diagnostic compares commit policies on claim-level ASQA tasks.
RiskRoll commits only claims with support in top-20 evidence and abstains otherwise.

## Summary

| Method | Grounded | Clean Task | Unsupported | Unsafe Depth | Abstain | Rollbacks | Repairs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Standard RAG top-1 | 0.429 | 0.205 | 1.699 | 2.055 | 0.000 | 0.000 | 0.000 |
| Retrieve-more RAG top-5 | 0.695 | 0.466 | 0.890 | 1.260 | 0.000 | 0.000 | 0.000 |
| Retrieve-more RAG top-20 | 0.920 | 0.808 | 0.233 | 0.397 | 0.000 | 0.000 | 0.000 |
| Post-hoc correction top-20 | 0.429 | 0.205 | 1.699 | 2.055 | 0.000 | 0.000 | 1.466 |
| CRAG-style correction top-20 | 0.920 | 0.808 | 0.233 | 0.397 | 0.000 | 0.000 | 0.000 |
| RiskRoll top-20 verify-before-commit | 0.920 | 1.000 | 0.000 | 0.000 | 0.233 | 12.521 | 1.466 |
| Method | Grounded Rate | Clean Task | Unsupported Commits | Unsafe Depth | Contamination | Rollbacks | Abstentions | Repairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Standard RAG top-1 | 0.188 | 0.040 | 4.060 | 3.660 | 3.660 | 0.000 | 0.000 | 0.000 |
| Retrieve-more RAG top-20 | 0.674 | 0.340 | 1.630 | 2.090 | 2.090 | 0.000 | 0.000 | 0.000 |
| Post-hoc correction top-20 | 0.674 | 0.340 | 4.060 | 3.660 | 3.660 | 0.000 | 0.000 | 2.430 |
| CRAG-style correction top-20 | 0.674 | 0.340 | 1.630 | 2.090 | 2.090 | 0.000 | 0.000 | 0.000 |
| RiskRoll top-20 verify-before-commit | 0.674 | 0.340 | 0.000 | 0.000 | 0.000 | 49.560 | 1.630 | 2.430 |
| Method | Precision | Recall | F1 | Strict Grounded | Support Rate | Clean Task | Unsupported Commits | Unsafe Depth | Abstentions | Rollbacks | Repairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Standard RAG top-1 | 0.268 | 0.112 | 0.145 | 0.112 | 0.768 | 0.010 | 0.090 | 0.020 | 3.500 | 0.000 | 0.000 |
| Retrieve-more RAG top-20 | 0.385 | 0.262 | 0.297 | 0.244 | 0.873 | 0.040 | 0.300 | 0.270 | 1.740 | 0.000 | 0.000 |
| Post-hoc correction top-20 | 0.358 | 0.186 | 0.227 | 0.182 | 0.937 | 0.010 | 0.110 | 0.080 | 2.530 | 0.000 | 1.970 |
| CRAG-style correction top-20 | 0.394 | 0.232 | 0.273 | 0.216 | 0.828 | 0.030 | 0.350 | 0.240 | 2.120 | 0.000 | 0.000 |
| RiskRoll verify-before-commit top-20 | 0.326 | 0.268 | 0.284 | 0.268 | 0.990 | 0.050 | 0.000 | 0.000 | 1.110 | 0.680 | 2.570 |
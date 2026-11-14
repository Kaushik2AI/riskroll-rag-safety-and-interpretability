# Experiment 8D: ALCE-ASQA actual LLM generation

Tag: `qwen7b_asqa_73_v1`

| Method | Claim Acc. | Strict Grounded | Support | Unsupported | Unsafe Depth | Abstain | Rollbacks | Repairs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Standard RAG top-1 | 0.158 | 0.158 | 0.452 | 0.000 | 0.000 | 2.356 | 0.000 | 0.000 |
| Retrieve-more RAG top-20 | 0.369 | 0.369 | 0.801 | 0.014 | 0.027 | 1.151 | 0.000 | 0.000 |
| Post-hoc correction top-20 | 0.097 | 0.097 | 0.301 | 0.000 | 0.000 | 2.507 | 0.000 | 0.740 |
| CRAG-style correction top-20 | 0.292 | 0.285 | 0.740 | 0.014 | 0.014 | 1.438 | 0.000 | 0.000 |
| RiskRoll verify-before-commit top-20 | 0.357 | 0.357 | 0.877 | 0.000 | 0.000 | 0.890 | 5.767 | 1.288 |
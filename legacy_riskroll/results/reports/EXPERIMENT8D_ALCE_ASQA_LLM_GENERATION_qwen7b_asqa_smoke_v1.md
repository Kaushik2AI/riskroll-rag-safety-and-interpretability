# Experiment 8D: ALCE-ASQA actual LLM generation

Tag: `qwen7b_asqa_smoke_v1`

| Method | Claim Acc. | Strict Grounded | Support | Unsupported | Unsafe Depth | Abstain | Rollbacks | Repairs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Standard RAG top-1 | 0.117 | 0.117 | 0.600 | 0.000 | 0.000 | 3.200 | 0.000 | 0.000 |
| Retrieve-more RAG top-20 | 0.363 | 0.363 | 0.800 | 0.000 | 0.000 | 1.600 | 0.000 | 0.000 |
| Post-hoc correction top-20 | 0.067 | 0.067 | 0.200 | 0.000 | 0.000 | 3.600 | 0.000 | 0.400 |
| CRAG-style correction top-20 | 0.453 | 0.453 | 0.800 | 0.000 | 0.000 | 1.800 | 0.000 | 0.000 |
| RiskRoll verify-before-commit top-20 | 0.363 | 0.363 | 0.800 | 0.000 | 0.000 | 1.600 | 7.400 | 1.000 |
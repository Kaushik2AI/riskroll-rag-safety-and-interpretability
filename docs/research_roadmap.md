# Research Roadmap

This repository links two connected research questions:

1. **RiskRoll-RAG (prevention):** Can unsupported factual claims be prevented from entering the generation state?
2. **Causal RAG interpretability (explanation):** What changes after a factual error enters the model's own autoregressive history?
3. **Mechanistic intervention (editing):** Which internal pathway changes evidence use, and can it be selectively interrupted?

## Current fastest path

- [x] RiskRoll-RAG implementation and public ALCE experiments
- [x] Continuous long-form ASQA generation with Qwen2.5-7B-Instruct
- [x] Initial natural-error mining
- [x] Small natural-vs-corrected-prefix A/B pilot
- [ ] Expand to 10–20 clean natural-error cases
- [ ] Measure evidence-supported vs false-prefix logit margins
- [ ] Separate dependent, related, and independent downstream claims
- [ ] Activation/component patching on cases with strong behavioral effects
- [ ] Random-head / unrelated-token / mismatched-example controls
- [ ] Mechanism-derived intervention while the false text remains unchanged
- [ ] Validate on a second model family

## Go / no-go rule

Do not invest heavily in mechanistic patching unless minimally correcting naturally generated early errors produces a reproducible downstream evidence-use effect.

# Natural vs Corrected Prefix Counterfactuals

This folder contains the first causal behavioral experiment.

For each natural error:
1. preserve the exact original prefix,
2. make a minimal factual correction,
3. keep model, question, retrieval context, and greedy decoding fixed,
4. compare downstream continuation.

The included `pilot_cases.json` contains the first three manually reviewed cases.

Run:

```bash
python run_prefix_counterfactual.py   --input-jsonl /path/to/asqa_qwen7b_natural_longform_full73_top3.jsonl   --model-path /path/to/Qwen2.5-7B-Instruct   --cases pilot_cases.json   --output natural_vs_corrected_prefix_pilot.json
```

Interpretation note: a changed continuation is a causal behavioral signal from the textual prefix intervention. It is not yet a mechanistic localization result.

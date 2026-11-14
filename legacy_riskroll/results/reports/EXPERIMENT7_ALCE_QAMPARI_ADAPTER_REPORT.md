# Experiment 7: ALCE-QAMPARI Public Adapter

## Purpose

Build a public text-only citation-aware benchmark adapter from ALCE-QAMPARI into the RiskRoll claim/evidence task format.

## Configuration

- Input file: `/projectnb/medaihack/team4/kaushik_work/riskroll-aaai27-text/external/ALCE/data/qampari_eval_gtr_top100.json`
- Target tasks: 100
- Claims per task: 5
- Candidate docs per claim: top-20

## Summary

- input_path: /projectnb/medaihack/team4/kaushik_work/riskroll-aaai27-text/external/ALCE/data/qampari_eval_gtr_top100.json
- records_read: 1000
- tasks_built: 100
- claims_per_task: 5
- total_claims: 500
- retrieval_top_k: 20
- require_support_in_top100: True
- skipped_no_docs: 0
- skipped_too_few_answers: 0
- skipped_no_support: 74
- mean_first_support_rank: 20.477848101265824
- top1_support_rate: 0.22
- top5_support_rate: 0.484
- top20_support_rate: 0.824

## Interpretation

Each QAMPARI question is converted into a multi-claim generation task. Each gold answer item becomes one atomic claim. Candidate evidence is drawn from the provided ALCE top-100 retrieval results. This gives RiskRoll a public claim-level citation grounding setting.

## Next step

Run public-dataset baselines: Standard RAG, Retrieve-more RAG, Post-hoc correction, CRAG-style correction, and RiskRoll.

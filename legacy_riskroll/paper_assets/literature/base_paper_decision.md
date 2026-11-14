# Base-paper decision for RiskRoll-RAG

RiskRoll-RAG should not be framed as being based on one single prior paper. It is best framed as an inference-time control layer at the intersection of active retrieval, corrective RAG, post-hoc revision, self-reflective RAG, and claim-level factuality evaluation.

## Closest anchors

1. FLARE / Active RAG:
   - Closest active-retrieval anchor.
   - It retrieves during generation, but does not rollback a semantic answer prefix.

2. CRAG:
   - Closest retrieval-correction baseline.
   - It evaluates retrieval quality, but does not decide whether a generated claim may enter a trusted prefix.

3. RARR:
   - Closest post-hoc revision baseline.
   - It fixes unsupported output after generation, while RiskRoll acts before unsafe content is committed.

4. Self-RAG:
   - Closest self-reflective RAG anchor.
   - It trains retrieval and critique behavior, but RiskRoll is an inference-time commit/rollback controller.

5. FActScore / LongFact-SAFE / VeriScore:
   - Evaluation foundations.
   - They justify atomic claim decomposition and evidence support checking, but they are not rollback methods.

## Working novelty claim

Existing RAG systems improve evidence access, self-critique, retrieval correction, or post-hoc revision. However, long-form RAG also has a state-contamination failure mode: once an unsupported claim is committed into the generated prefix, later claims may be conditioned on that unsafe state. RiskRoll-RAG introduces a trusted semantic prefix and an inference-time commit/rollback policy that verifies each claim before semantic commitment, rolls back unsafe candidate spans, repairs with targeted evidence, and continues generation from the last trusted state.

## Baseline decision

Required baselines:
- Standard RAG
- Retrieve-more RAG
- CRAG-style evidence correction
- Post-hoc correction / RARR-style revision
- RiskRoll-RAG

Optional stronger baselines:
- FLARE-style active retrieval
- Self-RAG-style self-critique
- RARR implementation if time permits

## Next public benchmark decision

Recommended next public benchmark:
- ALCE-QAMPARI or ALCE-ASQA

Reason:
- Citation-aware long-form QA aligns with claim/evidence commitment.
- It provides correctness and citation quality metrics.
- It is easier than multimodal verification and closer to our text-only RiskRoll story.

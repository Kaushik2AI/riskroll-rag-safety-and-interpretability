# RiskRoll-RAG: Inference-Time Rollback for Safer Long-Form Retrieval-Augmented Generation

**Draft status:** first complete AAAI-style paper draft.

**Core claim:** Long-form RAG needs verify-before-commit control. RiskRoll maintains a trusted semantic prefix and rolls back unsafe claims before they contaminate later generation.

---

## Abstract

Long-form retrieval-augmented generation systems remain vulnerable to hallucination cascades: once an unsupported claim enters the generated context, later claims may be conditioned on an unsafe prefix. Existing approaches often improve retrieval, retrieve more evidence, abstain under uncertainty, or revise answers after generation, but they do not directly control whether a candidate claim is allowed to become part of the trusted answer state. We propose RiskRoll-RAG, an inference-time rollback framework for long-form RAG. RiskRoll generates answers claim by claim, verifies each candidate claim against retrieved evidence before commitment, and maintains a trusted semantic prefix containing only verified claims. When a candidate is unsupported, the controller rolls back to the last trusted prefix, expands or redirects evidence, repairs the unsafe span, and continues generation; if no supported repair is found, it abstains rather than committing an unsafe claim. We evaluate RiskRoll using controlled near-miss stress tests, noisy verifier sweeps, and public ALCE-QAMPARI and ALCE-ASQA experiments with Qwen2.5-7B-Instruct. Across public datasets, RiskRoll remains competitive with retrieve-more RAG in answer quality while improving evidence support and eliminating unsupported commits and unsafe-prefix contamination. These results suggest that safer long-form RAG requires not only better retrieval, but explicit inference-time control over what information is allowed to enter the generation state.

---

## Introduction

Retrieval-augmented generation (RAG) is widely used to improve the factuality of large language models by conditioning generation on retrieved evidence. However, long-form RAG remains vulnerable to a specific failure mode: once an unsupported or weakly grounded claim enters the generated context, later claims may be conditioned on that unsafe prefix. This can create hallucination cascades, where an early factual error influences subsequent reasoning, retrieval interpretation, or answer generation.

Most existing RAG safety methods focus on improving retrieval quality, increasing the amount of retrieved evidence, filtering uncertain generations, abstaining when evidence is insufficient, or correcting errors after the answer has already been generated. These strategies are valuable, but they do not directly address the inference-time state-management problem: deciding whether a candidate claim should be allowed to enter the trusted answer prefix in the first place.

We propose RiskRoll-RAG, an inference-time rollback framework for long-form RAG. RiskRoll generates answers claim by claim. Each candidate claim is verified against retrieved evidence before it is committed to the trusted semantic prefix. If the claim is unsupported, risky, or grounded in weak evidence, the controller rolls back to the last trusted prefix, retrieves or considers deeper targeted evidence, repairs the unsafe span, and continues generation. If no supported repair is found, the system abstains rather than committing an unsafe claim.

The central idea is verify-before-commit generation. Instead of treating factuality as only a final-answer evaluation problem, RiskRoll treats factuality as an inference-time control problem. A claim is not allowed to influence later generation unless it has first been verified.

This paper makes four contributions:

1. We introduce the trusted semantic prefix as an inference-time state variable for long-form RAG.
2. We propose a rollback-and-repair controller that rejects unsupported claims before they enter the autoregressive context.
3. We define contamination-oriented safety metrics, including unsupported commits, unsafe prefix depth, clean task rate, and downstream contaminated claims.
4. We evaluate RiskRoll using controlled near-miss stress tests, noisy verifier sweeps, and public ALCE-QAMPARI and ALCE-ASQA experiments with Qwen2.5-7B-Instruct.

Across experiments, RiskRoll remains competitive with retrieve-more RAG in answer quality while consistently improving groundedness and eliminating unsupported commits. These results suggest that safer long-form RAG requires not only better retrieval, but also explicit control over what information is allowed to become part of the generation state.

---

## Related Work

## Retrieval-augmented generation

Retrieval-augmented generation improves language model factuality by grounding generation in external documents. Standard RAG pipelines retrieve a set of passages and condition the generator on those passages. Later work improves retrieval quality through reranking, query rewriting, adaptive retrieval, and larger evidence windows. These methods reduce some hallucinations by exposing the model to more relevant information, but they do not guarantee that every generated claim is supported by evidence.

RiskRoll-RAG is complementary to improved retrieval. It does not replace the retriever. Instead, it adds an inference-time controller that decides whether a generated claim should be committed to the trusted answer prefix.

## Long-form grounded generation

Long-form RAG is more difficult than short-form QA because answers contain multiple claims. A single weak or unsupported claim can affect later parts of the answer. Systems for long-form grounded generation often organize retrieved evidence into claim-level memories, generate citations, or evaluate evidence sufficiency at the sub-claim level. These approaches help structure evidence use, but many still generate or revise text without explicit rollback semantics.

RiskRoll focuses on the moment of commitment. A claim must pass verification before it becomes part of the trusted prefix. This makes prefix safety explicit rather than relying only on final-answer correction.

## Claim-level verification and factuality checking

Claim-level verification methods decompose generated text into factual units and check whether each unit is supported by evidence. Fact-checking, entailment models, and LLM-based verifiers can identify unsupported claims after or during generation. These methods are closely related to RiskRoll because RiskRoll also relies on claim-level verification.

The difference is that RiskRoll uses verification as a control signal. A rejected claim is not merely labeled as unsafe; it triggers rollback, targeted repair, and possible abstention. Thus, verification changes the generation trajectory rather than only scoring the final answer.

## Selective generation and abstention

Selective generation methods abstain when confidence is low or evidence is insufficient. Conformal and uncertainty-aware RAG methods study when a system should answer versus refuse. This is important for factual safety, but pure abstention can reduce coverage and may not repair partially unsafe answers.

RiskRoll uses abstention as a last resort. Before abstaining, it attempts rollback and repair using deeper or redirected evidence. This allows the system to preserve answer coverage when supported evidence exists, while still avoiding unsupported commits when repair fails.

## Post-hoc correction and self-revision

Post-hoc correction methods generate an answer first and then revise it using additional evidence or self-critique. These methods can improve final answer factuality, but they are vulnerable to semantic-prefix contamination: the unsupported claim may already have influenced later generated content before correction occurs.

RiskRoll differs by preventing unsafe claims from entering the prefix in the first place. Rather than editing a completed answer, it controls the generation process at claim granularity.

## Evidence correction and adaptive RAG

Adaptive RAG and correction-based systems adjust retrieval depth, rerank evidence, or retrieve additional documents when the initial evidence appears insufficient. These methods improve evidence availability, but they often do not explicitly model the answer prefix as a trusted state that can be rolled back.

RiskRoll combines adaptive evidence expansion with commit control. Deeper evidence is considered only after a candidate claim fails verification, and the system retries from the last trusted prefix.

## Hallucination cascades and context contamination

Recent work has observed that hallucinations in long-form generation can cascade: one incorrect claim can influence later claims. This is especially important in RAG, where generated content and retrieved evidence are jointly used to produce a coherent answer. If an incorrect claim becomes part of the model context, later generations may appear consistent but remain grounded in an unsafe premise.

RiskRoll directly targets this failure mode through trusted-prefix maintenance. Unsupported claims are rejected before they can contaminate downstream generation.

## Positioning

RiskRoll-RAG is not simply another retrieve-more or post-hoc correction method. Its main contribution is an inference-time state-management mechanism for long-form RAG. The method asks a different question: not only whether the final answer can be corrected, but whether each claim should be allowed to enter the trusted semantic prefix at all.

---

## Method: RiskRoll-RAG

## Overview

RiskRoll-RAG is an inference-time rollback framework for long-form retrieval-augmented generation. The key idea is to prevent unsupported claims from entering the autoregressive context. Instead of generating a full answer and correcting it afterward, RiskRoll generates candidate claims incrementally, verifies each claim against retrieved evidence, and commits only supported claims to a trusted semantic prefix.

The method treats long-form RAG as a sequential decision process. At each step, the system must decide whether a candidate claim is safe enough to become part of the answer prefix. If the candidate is supported, it is committed. If it is unsupported, contradicted, or grounded in weak evidence, the controller rejects the candidate, rolls back to the last trusted prefix, retrieves or considers deeper targeted evidence, repairs the unsafe span, and continues generation.

## Trusted semantic prefix

Let the generated answer be represented as a sequence of semantic units:

\[
y = (c_1, c_2, \ldots, c_T),
\]

where each \(c_t\) is a claim, sub-answer, or answer item. RiskRoll maintains a trusted prefix:

\[
P_t = (c_1, \ldots, c_t),
\]

where every committed claim has passed evidence verification. Unlike standard autoregressive generation, unverified candidates are not allowed to become part of the conditioning context for future claims.

This distinction is important because one hallucinated or weakly supported claim can influence later claims. RiskRoll therefore treats prefix safety as a first-class inference-time state variable.

## Claim proposal

At each step \(t\), the generator proposes a candidate claim \(\hat{c}_t\) conditioned on the user question, retrieved evidence, and the trusted prefix:

\[
\hat{c}_t = G(q, E_t, P_{t-1}).
\]

Here, \(q\) is the user question, \(E_t\) is the current evidence set, and \(P_{t-1}\) is the trusted prefix. The generator may be any instruction-tuned LLM. RiskRoll does not require model retraining.

## Evidence verification

Each candidate claim is checked against retrieved evidence using a verifier:

\[
v(\hat{c}_t, E_t) \in \{\text{accept}, \text{reject}\}.
\]

A claim is accepted only if the evidence directly supports it. If the verifier rejects the claim, RiskRoll does not append it to the trusted prefix. This verify-before-commit rule is the core difference between RiskRoll and post-hoc correction.

In the current experiments, verification is implemented using controlled identity checks for synthetic stress tests and lexical support checks for public ALCE claim-level evaluations. The framework itself is verifier-agnostic and can use stronger NLI, entailment, or LLM-based verifiers.

## Commit rule

If the verifier accepts the candidate claim, RiskRoll commits it:

\[
P_t = P_{t-1} \oplus \hat{c}_t.
\]

The committed claim becomes part of the trusted prefix and can condition later generation. Since only verified claims enter \(P_t\), the model avoids conditioning on known unsafe content.

## Rollback and repair

If the verifier rejects the candidate claim, the controller rolls back to the last trusted prefix:

\[
P_t = P_{t-1}.
\]

The rejected candidate is discarded rather than edited inside the prefix. RiskRoll then performs a targeted repair step by expanding or redirecting evidence retrieval. In our implementation, the controller increases the evidence window from top-1 to deeper retrieval windows such as top-5, top-10, and top-20. A new candidate is generated from the same trusted prefix and the updated evidence.

If no supported claim can be produced after the repair budget is exhausted, RiskRoll abstains for that semantic unit rather than committing an unsupported claim.

## Difference from baselines

Standard RAG retrieves evidence once and generates directly from the retrieved context. It does not check whether each generated claim should enter the answer prefix.

Retrieve-more RAG increases the amount of evidence available to the generator. This can improve recall, but it does not prevent unsupported claims from being committed.

Post-hoc correction revises the answer after generation. However, unsupported claims may already have influenced later text by the time correction occurs.

CRAG-style correction improves evidence selection before or during generation, but it does not explicitly maintain a trusted semantic prefix with rollback semantics.

RiskRoll differs from all of these approaches by making commitment itself conditional on verification. A claim must be verified before it becomes part of the trusted generation state.

## Algorithm

At a high level, RiskRoll proceeds as follows:

1. Initialize the trusted prefix as empty.
2. Generate a candidate claim from the question, evidence, and trusted prefix.
3. Verify the candidate against evidence.
4. If supported, commit it to the trusted prefix.
5. If unsupported, reject it, roll back to the last trusted prefix, retrieve or consider deeper evidence, and retry.
6. If no supported repair is found, abstain for that claim.
7. Continue until the answer is complete.

## Computational overhead

RiskRoll adds inference-time overhead because rejected candidates require additional verification and regeneration. However, this overhead is interpretable: it is measured by rollback count, repair count, and abstention count. The experiments report these quantities directly. This makes the safety-cost tradeoff explicit rather than hidden inside larger retrieval contexts or post-hoc revision.

---

## Experimental Setup

## Research questions

We design the experiments around three questions:

1. Can RiskRoll prevent unsupported claims from entering the trusted answer prefix?
2. How sensitive is RiskRoll to verifier errors?
3. On public long-form QA benchmarks, does RiskRoll improve factual safety while preserving competitive answer quality?

These questions reflect the core motivation of the paper: hallucination in long-form RAG is not only a final-answer problem, but also an inference-time state-management problem.

## Datasets

### Controlled near-miss long-form RAG

We first construct a controlled text-only long-form RAG stress test. Each task contains a sequence of claims and a retrieval setting where the highest-ranked evidence is lexically plausible but semantically wrong. This setup isolates semantic-prefix contamination: once a wrong claim is committed, later claims may be conditioned on an unsafe prefix.

The controlled setting allows us to measure whether a method merely produces a corrected final answer or actually prevents unsafe claims from entering the generation state.

### Verifier-quality sweep

We evaluate RiskRoll under noisy verifier conditions by varying false-accept and false-reject rates. False accepts simulate cases where unsupported evidence is incorrectly accepted. False rejects simulate cases where valid evidence is incorrectly rejected. This experiment tests whether RiskRoll fails gracefully as verifier quality changes.

### ALCE-QAMPARI

We use ALCE-QAMPARI as a public list-style long-form QA benchmark. Each question requires multiple answer items. We evaluate whether generated answer items are correct and supported by retrieved evidence.

QAMPARI is useful because unsupported answer items can be treated as unsafe semantic units. It also exposes the difference between answer recall and evidence-grounded safety.

### ALCE-ASQA

We use ALCE-ASQA as a public ambiguous long-form QA benchmark. ASQA provides decomposed `qa_pairs`, short-answer aliases, retrieved documents, and a long-form answer. We convert each `qa_pair` into a claim-level generation unit. This makes ASQA suitable for testing verify-before-commit generation over decomposed long-form answers.

From the first 100 ASQA records, the adapter builds 73 usable tasks with 222 claim units. Supporting evidence appears within the top-20 retrieved documents for most claims, making the setting suitable for comparing retrieve-more and rollback behavior.

## Baselines

We compare RiskRoll against four baselines.

### Standard RAG

Standard RAG retrieves the top-ranked evidence and generates directly from it. It does not verify each claim before commitment.

### Retrieve-more RAG

Retrieve-more RAG provides the generator with a larger retrieval window, such as top-20 documents. This baseline tests whether simply increasing context is enough to solve unsupported generation.

### Post-hoc correction

Post-hoc correction first generates an answer and then revises it using additional evidence. This baseline can improve the final answer, but unsafe claims may already have influenced later generation before correction occurs.

### CRAG-style correction

The CRAG-style baseline approximates evidence correction before generation by selecting or reranking evidence from a larger retrieval pool. It tests whether better evidence selection alone can replace rollback-based prefix control.

### RiskRoll-RAG

RiskRoll generates candidate claims incrementally. Each claim is verified against evidence before being committed. Unsupported candidates are rejected, the controller rolls back to the last trusted prefix, considers deeper evidence, and retries. If no supported candidate is found, the method abstains rather than committing an unsafe claim.

## Model

For public ALCE experiments, we use Qwen2.5-7B-Instruct as the generator. The model is run with deterministic decoding using temperature 0.0. RiskRoll does not require model fine-tuning; all behavior is implemented as inference-time control.

## Verification

The verifier depends on the experiment type. In controlled experiments, verification checks whether the evidence identity matches the intended claim. In public ALCE experiments, verification uses lexical support between generated answer items and retrieved documents. A prediction is treated as supported when the answer text appears in the associated evidence.

This verifier is intentionally simple. The goal is not to claim that lexical verification is optimal, but to test whether verify-before-commit control improves safety even with a lightweight verifier. The framework is verifier-agnostic and can use stronger entailment, NLI, or LLM-based verification.

## Metrics

We report both answer-quality and safety metrics.

### Answer quality

For QAMPARI, we report answer F1 over generated answer items. For ASQA, we report claim accuracy over decomposed claim units.

### Strict grounded rate

Strict grounded rate measures whether a generated item is both correct and supported by evidence. This metric is stricter than answer accuracy because a correct answer without supporting evidence is not counted as strictly grounded.

### Support rate

Support rate measures the fraction of non-abstained predictions that are supported by evidence. This captures whether the model's committed answers are evidence-backed.

### Unsupported commits

Unsupported commits count how many unsupported predictions are committed into the answer state. This is the central safety metric for RiskRoll.

### Unsafe prefix depth

Unsafe prefix depth measures how much generation occurs after the first unsafe commit. This captures possible hallucination cascade risk.

### Clean task rate

Clean task rate measures the fraction of tasks with no unsupported commits and no unsafe prefix contamination.

### Rollbacks, repairs, and abstentions

Rollback count measures how often RiskRoll rejects a candidate and retries from the trusted prefix. Repair count measures how often a rejected candidate is replaced using deeper or alternative evidence. Abstention count measures how often the method refuses to commit an unsupported answer.

## Implementation details

RiskRoll is implemented as an inference-time controller around the generator. For public experiments, the controller attempts generation with progressively larger evidence windows. It starts with top-1 evidence and expands to deeper windows such as top-5, top-10, and top-20 when candidates fail verification.

All experiments save raw outputs, per-task rows, summary tables, and paper-ready figures. This allows both aggregate evaluation and error analysis.

---

## Results

We evaluate RiskRoll-RAG under three settings: controlled long-form RAG stress tests, verifier-quality sensitivity analysis, and public ALCE long-form QA benchmarks using Qwen2.5-7B-Instruct. Across these settings, the central question is not only whether the final answer contains correct information, but whether unsupported claims are allowed to enter the trusted answer prefix and contaminate later generation.

## Controlled near-miss evidence stress test

The controlled text experiment isolates the failure mode that motivates RiskRoll-RAG. Each task contains multiple claims, and the top-ranked evidence is intentionally wrong but lexically plausible. Standard RAG, retrieve-more RAG, post-hoc correction, and CRAG-style correction all commit unsupported evidence early, producing unsafe prefixes and downstream contamination. In contrast, RiskRoll verifies each claim before committing it to the trusted prefix. When the top-ranked evidence is rejected, the controller rolls back to the last trusted prefix, retrieves or considers deeper evidence, repairs the unsafe span, and continues generation.

In this setting, RiskRoll achieves perfect grounded claim rate and clean-task rate, while reducing wrong-evidence commits and unsafe prefix depth to zero. This result shows that the proposed rollback mechanism directly targets semantic-prefix contamination rather than only improving final answer correction.

## Verifier-quality sensitivity

We next study how RiskRoll behaves when the verifier is imperfect. The verifier sweep separates false accepts from false rejects. The results show an asymmetric failure pattern: false accepts are more harmful than false rejects. A false accept allows unsupported evidence to enter the trusted prefix, causing downstream contamination. False rejects, by contrast, mostly increase abstention or rollback frequency without corrupting the trusted prefix.

This supports the design choice behind RiskRoll-RAG: the controller should be conservative about committing claims. In long-form generation, rejecting a supported claim can reduce recall, but accepting an unsupported claim can corrupt the autoregressive context and influence all later claims.

## Public ALCE-QAMPARI results

On ALCE-QAMPARI, retrieve-more RAG obtains the highest raw F1 among the non-rollback methods, but it also commits unsupported claims. RiskRoll remains competitive in F1 while producing the safest generations. It achieves the highest strict grounded rate and the highest support rate among non-UNKNOWN predictions. Most importantly, RiskRoll eliminates unsupported commits and unsafe-prefix contamination.

This shows that adding more retrieved context is not sufficient for safe long-form RAG. Although retrieve-more improves answer recall, it can still allow unsupported claims to enter the answer prefix. RiskRoll instead verifies before commit, preventing unsupported claims from becoming part of the trusted generation state.

## Public ALCE-ASQA results

ASQA provides a complementary setting because each example contains decomposed sub-questions and a long-form answer. We convert ASQA `qa_pairs` into claim-level generation units and evaluate each method on 73 usable tasks. Retrieve-more RAG achieves slightly higher claim accuracy than RiskRoll, but RiskRoll obtains a higher evidence support rate and eliminates unsafe commits. Specifically, RiskRoll reaches 0.357 claim accuracy compared with 0.369 for retrieve-more, while improving support rate from 0.801 to 0.877 and reducing unsupported commits and unsafe prefix depth to zero.

This result shows the intended safety-quality tradeoff. RiskRoll is not designed to maximize recall by committing every plausible answer. Instead, it favors claims that can be verified before entering the trusted prefix. On ASQA, this leads to slightly lower raw accuracy than retrieve-more, but better groundedness and safer generation.

## Combined public LLM findings

Across QAMPARI and ASQA, the pattern is consistent. RiskRoll does not always maximize raw answer quality, but it consistently improves factual safety. On QAMPARI, RiskRoll achieves lower F1 than retrieve-more RAG, but higher strict grounded rate, higher support rate, and zero unsupported commits. On ASQA, RiskRoll is close to retrieve-more in claim accuracy, has the best support rate, and again produces zero unsafe prefix depth.

These results support the main hypothesis of RiskRoll-RAG: long-form RAG systems need inference-time state management, not only better retrieval or post-hoc correction. By maintaining a trusted semantic prefix and rolling back unsafe spans before commitment, RiskRoll reduces hallucination cascades while preserving competitive answer quality.

## Key takeaway

RiskRoll-RAG trades a small amount of raw recall for substantially safer long-form generation. The method is especially valuable when unsupported claims can contaminate later reasoning or generation. Instead of treating hallucination as only a final-answer evaluation problem, RiskRoll treats it as an inference-time control problem: only verified claims are allowed to enter the trusted prefix.

---

## Overhead and Safety-Cost Summary

RiskRoll introduces explicit inference-time overhead through rollback and repair operations. This overhead is not hidden: it is measured by rollback count, repair count, and abstention count.

On QAMPARI, RiskRoll performs 0.680 rollbacks and 2.570 repairs per task on average. This produces zero unsupported commits and zero unsafe prefix depth, compared with retrieve-more RAG, which has 0.300 unsupported commits and 0.270 unsafe prefix depth per task.

On ASQA, RiskRoll performs 5.767 rollbacks and 1.288 repairs per task on average. It again reduces unsupported commits and unsafe prefix depth to zero, while retrieve-more RAG has 0.014 unsupported commits and 0.027 unsafe prefix depth per task.

These results show that RiskRoll's safety improvements come from active inference-time control rather than passive retrieval expansion. The cost is additional rollback and repair work; the benefit is preventing unsupported claims from entering the trusted prefix.

---

## Limitations and Threats to Validity

## Verifier strength

The public ALCE experiments use lightweight lexical support checks to determine whether a generated answer item appears in retrieved evidence. This makes the experiments reproducible and transparent, but it is not a full semantic entailment verifier. Lexical matching can miss paraphrases, aliases, and semantically equivalent answers. It can also overestimate support when an answer string appears in evidence without supporting the exact claim.

Future work should evaluate RiskRoll with stronger verifiers, including natural language inference models, citation-aware entailment models, and LLM-based evidence judges.

## Alias and answer normalization

QAMPARI and ASQA include short-answer aliases, but public benchmark aliases are not always exhaustive. Some RiskRoll predictions may be supported by evidence but not counted as correct because they do not match the gold alias set. This is especially important for list-style or ambiguous questions, where multiple valid answers may exist.

This limitation affects all methods, but it is particularly visible for RiskRoll because the method can produce supported answers that are safe but not present in the gold set.

## Dataset scale

The public LLM experiments are run on 100 QAMPARI tasks and 73 usable ASQA tasks. These experiments are sufficient for a focused paper prototype and error analysis, but they are not a full benchmark-scale evaluation. Larger evaluations across more examples and additional datasets would strengthen the empirical claims.

## Single generator model

The public generation experiments use Qwen2.5-7B-Instruct. RiskRoll is model-agnostic, but the current results may depend on this generator's instruction following, abstention behavior, and ability to produce short answer candidates. Future work should evaluate stronger and weaker generators, including larger open-weight models and API-based models.

## Retrieval setting

The experiments use retrieved documents provided by ALCE. RiskRoll is evaluated by expanding evidence windows such as top-1, top-5, top-10, and top-20. This setting isolates commit behavior, but it does not test a fully learned retriever or query rewriting module. In practical deployments, RiskRoll could be combined with stronger retrieval, reranking, and targeted query generation.

## Computational overhead

RiskRoll adds inference-time cost because rejected candidates require verification, rollback, and regeneration. The overhead is measured through rollback and repair counts. This cost is the price of safer prefix control. In settings where latency is more important than factual safety, a lighter configuration may be needed.

## Abstention and recall tradeoff

RiskRoll may abstain when evidence is insufficient or when the verifier rejects candidates. This can reduce raw answer recall compared with retrieve-more RAG. The method is therefore best suited for applications where unsupported claims are more costly than missing claims, such as research assistance, legal analysis, medical summarization, or high-stakes enterprise reporting.

## Synthetic controlled experiments

The controlled near-miss stress test is designed to isolate semantic-prefix contamination. While useful for mechanism validation, synthetic tasks may not fully capture the complexity of open-domain retrieval. The controlled results should therefore be interpreted as evidence that RiskRoll can solve the targeted failure mode, not as a replacement for public benchmark evaluation.

## Human evaluation

The current experiments rely on automatic metrics. Human evaluation would be useful for judging whether RiskRoll's abstentions, repairs, and generated claims are preferable in real long-form answers. Human studies could also evaluate readability, citation quality, and user trust.

## Overall limitation

RiskRoll does not solve all hallucination problems. It reduces one important failure mode: unsupported claims entering the trusted answer prefix and contaminating later generation. The method still depends on retrieval quality, verifier quality, answer parsing, and the generator's ability to produce repair candidates. Its main value is to make factual commitment explicit and controllable during inference.

---

## Conclusion

We introduced RiskRoll-RAG, an inference-time rollback framework for safer long-form retrieval-augmented generation. The core idea is to treat factuality as a state-management problem: a generated claim should not be allowed to enter the trusted answer prefix unless it is first verified against evidence. When verification fails, RiskRoll rolls back to the last trusted prefix, repairs the unsafe span using deeper or targeted evidence, and abstains when no supported repair is available.

Across controlled stress tests, verifier-quality sweeps, and public ALCE-QAMPARI and ALCE-ASQA experiments, RiskRoll consistently reduces unsafe generation behavior. The method does not always maximize raw answer recall, but it improves support rate, increases groundedness, and eliminates unsupported commits in the evaluated public LLM settings. These findings support the paper's central hypothesis: long-form RAG safety requires explicit control over claim commitment, not only stronger retrieval or post-hoc correction.

Future work should combine RiskRoll with stronger semantic verifiers, learned retrievers, citation-aware entailment models, and human evaluation. The broader goal is to build RAG systems that can reason over long answers while maintaining a clean, trusted generation state throughout inference.

---

## Paper Tables to Include

Recommended main-paper tables:

1. **Main controlled stress test table**: `table1_main_text_longform_results`
2. **Verifier sweep table/figure**: `table2_false_accept_sweep`, `table3_false_reject_sweep`
3. **Public LLM combined table**: `table9_combined_public_llm_results`
4. **Overhead and safety-cost table**: `table10_public_llm_overhead_and_safety_cost`

Optional appendix tables:

- `table5_alce_qampari_public_diagnostic`
- `table6_alce_qampari_commit_policy`
- `table7_alce_qampari_qwen7b_llm_generation_100`
- `table8_alce_asqa_qwen7b_llm_generation_73`

## Paper Figures to Include

Recommended main-paper figures:

1. RiskRoll workflow diagram
2. Controlled stress test: grounded rate and unsafe prefix depth
3. Noisy verifier sweep: false accept contamination curve
4. Combined public LLM: unsupported commits and safety-quality tradeoff

## Writing TODO

- Add formal citations to Related Work.
- Convert this markdown draft into AAAI LaTeX.
- Reduce length to fit AAAI page budget.
- Move diagnostic tables and extended error analysis to appendix.
- Add concise algorithm box from `paper_assets/algorithms/algorithm1_riskroll.tex`.
- Add one clear method diagram.
- Polish abstract after final page-length pass.

## Citation TODO

Need citations for:

- Retrieval-Augmented Generation / RAG
- ALCE benchmark
- ASQA
- QAMPARI
- CRAG or corrective RAG
- Claim-level factuality / verification
- Selective generation / abstention / conformal RAG
- Hallucination cascades / long-form factuality
- Qwen2.5 technical report/model card

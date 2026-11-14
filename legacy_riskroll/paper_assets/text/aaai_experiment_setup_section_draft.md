# Experimental Setup

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

# Method: RiskRoll-RAG

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

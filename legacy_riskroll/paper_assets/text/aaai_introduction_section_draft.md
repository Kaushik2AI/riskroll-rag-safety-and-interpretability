# Introduction

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

# Related Work

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

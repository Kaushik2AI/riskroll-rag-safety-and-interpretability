# Limitations and Threats to Validity

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

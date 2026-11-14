# Results

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

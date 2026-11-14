# Public LLM Results Paragraph

Across two public ALCE datasets, RiskRoll improves factual safety while remaining competitive in answer quality. On QAMPARI, retrieve-more RAG obtains the highest raw F1 (0.297), while RiskRoll remains close (0.284) and achieves the highest strict grounded rate (0.268) and support rate (0.990). More importantly, RiskRoll eliminates unsupported commits and unsafe-prefix contamination, reducing both metrics to 0.000, whereas retrieve-more and CRAG-style baselines still commit unsupported claims. On ASQA, retrieve-more obtains slightly higher claim accuracy (0.369 vs. 0.357), but RiskRoll again achieves the highest evidence support rate (0.877), zero unsupported commits, and zero unsafe prefix depth. These results support the central hypothesis that verify-before-commit rollback trades a small amount of raw recall for substantially safer long-form RAG generation.

## Short version for paper

RiskRoll is not designed to maximize answer recall at all costs. Instead, it prevents unsupported claims from entering the autoregressive prefix. Across QAMPARI and ASQA, RiskRoll remains competitive with retrieve-more RAG while consistently eliminating unsupported commits and unsafe-prefix contamination.

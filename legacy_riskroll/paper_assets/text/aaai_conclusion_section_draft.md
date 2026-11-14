# Conclusion

We introduced RiskRoll-RAG, an inference-time rollback framework for safer long-form retrieval-augmented generation. The core idea is to treat factuality as a state-management problem: a generated claim should not be allowed to enter the trusted answer prefix unless it is first verified against evidence. When verification fails, RiskRoll rolls back to the last trusted prefix, repairs the unsafe span using deeper or targeted evidence, and abstains when no supported repair is available.

Across controlled stress tests, verifier-quality sweeps, and public ALCE-QAMPARI and ALCE-ASQA experiments, RiskRoll consistently reduces unsafe generation behavior. The method does not always maximize raw answer recall, but it improves support rate, increases groundedness, and eliminates unsupported commits in the evaluated public LLM settings. These findings support the paper's central hypothesis: long-form RAG safety requires explicit control over claim commitment, not only stronger retrieval or post-hoc correction.

Future work should combine RiskRoll with stronger semantic verifiers, learned retrievers, citation-aware entailment models, and human evaluation. The broader goal is to build RAG systems that can reason over long answers while maintaining a clean, trusted generation state throughout inference.

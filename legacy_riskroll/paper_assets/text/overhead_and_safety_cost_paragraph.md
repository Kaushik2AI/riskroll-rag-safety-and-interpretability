# Overhead and Safety-Cost Summary

RiskRoll introduces explicit inference-time overhead through rollback and repair operations. This overhead is not hidden: it is measured by rollback count, repair count, and abstention count.

On QAMPARI, RiskRoll performs 0.680 rollbacks and 2.570 repairs per task on average. This produces zero unsupported commits and zero unsafe prefix depth, compared with retrieve-more RAG, which has 0.300 unsupported commits and 0.270 unsafe prefix depth per task.

On ASQA, RiskRoll performs 5.767 rollbacks and 1.288 repairs per task on average. It again reduces unsupported commits and unsafe prefix depth to zero, while retrieve-more RAG has 0.014 unsupported commits and 0.027 unsafe prefix depth per task.

These results show that RiskRoll's safety improvements come from active inference-time control rather than passive retrieval expansion. The cost is additional rollback and repair work; the benefit is preventing unsupported claims from entering the trusted prefix.

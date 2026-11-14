from typing import Any, Dict, Iterable, Optional

from riskroll.schemas import ClaimExample, EvidenceCandidate
from verification.base import VerificationResult


def _norm_value(x: Any) -> str:
    return str(x).strip().lower()


class ControlledIdentityVerifier:
    """
    Controlled verifier for Experiment 2.

    It checks whether candidate evidence satisfies the required query constraints
    stored in example.metadata.

    Example metadata can include:
    - report_id
    - modality
    - city
    - domain
    - year
    - metric

    This is controlled, not fully non-oracle. Its purpose is to isolate whether
    rollback logic works when the verifier correctly rejects near-miss evidence.
    """

    def __init__(
        self,
        required_keys: Optional[Iterable[str]] = None,
        trust_risk_score: float = 0.05,
        rollback_risk_score: float = 0.95,
    ):
        self.required_keys = list(required_keys) if required_keys is not None else None
        self.trust_risk_score = trust_risk_score
        self.rollback_risk_score = rollback_risk_score

    def _candidate_metadata(self, candidate: EvidenceCandidate) -> Dict[str, Any]:
        meta = dict(candidate.metadata or {})
        meta.setdefault("modality", candidate.modality)
        meta.setdefault("evidence_id", candidate.evidence_id)
        return meta

    def verify(
        self,
        example: ClaimExample,
        candidate: EvidenceCandidate,
    ) -> VerificationResult:
        query_meta = dict(example.metadata or {})
        cand_meta = self._candidate_metadata(candidate)

        if not query_meta:
            return VerificationResult(
                decision="rollback",
                risk_score=self.rollback_risk_score,
                reason="no query constraints available for controlled verification",
                failure_type="missing_query_metadata",
                matched_constraints={},
            )

        keys_to_check = self.required_keys or list(query_meta.keys())

        matched = {}
        mismatch_reasons = []

        for key in keys_to_check:
            expected = query_meta.get(key, None)

            # Skip keys not specified in the query metadata.
            if expected is None:
                continue

            observed = cand_meta.get(key, None)

            ok = _norm_value(expected) == _norm_value(observed)
            matched[key] = ok

            if not ok:
                mismatch_reasons.append(
                    f"{key} mismatch: expected={expected}, observed={observed}"
                )

        if matched and all(matched.values()):
            return VerificationResult(
                decision="trust",
                risk_score=self.trust_risk_score,
                reason="all controlled identity constraints matched",
                failure_type="none",
                matched_constraints=matched,
            )

        if not matched:
            return VerificationResult(
                decision="rollback",
                risk_score=self.rollback_risk_score,
                reason="no usable controlled identity constraints were checked",
                failure_type="no_constraints_checked",
                matched_constraints=matched,
            )

        first_failed_key = next(k for k, ok in matched.items() if not ok)

        return VerificationResult(
            decision="rollback",
            risk_score=self.rollback_risk_score,
            reason="; ".join(mismatch_reasons),
            failure_type=f"wrong_{first_failed_key}",
            matched_constraints=matched,
        )

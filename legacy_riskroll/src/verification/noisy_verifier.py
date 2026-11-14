import random
from typing import Optional

from riskroll.schemas import ClaimExample, EvidenceCandidate
from verification.base import VerificationResult, BaseVerifier


class NoisyVerifierWrapper:
    """
    Controlled detector-quality simulator.

    It wraps a base verifier and injects two diagnostic errors:

    false_accept_rate:
        Wrong evidence that should rollback is incorrectly trusted.

    false_reject_rate:
        Gold evidence that should be trusted is incorrectly rolled back.

    This is not the final real-world verifier.
    It is a controlled experiment to measure how detector quality affects RiskRoll.
    """

    def __init__(
        self,
        base_verifier: BaseVerifier,
        false_accept_rate: float = 0.0,
        false_reject_rate: float = 0.0,
        seed: Optional[int] = None,
    ):
        self.base_verifier = base_verifier
        self.false_accept_rate = false_accept_rate
        self.false_reject_rate = false_reject_rate
        self.rng = random.Random(seed)

    def verify(
        self,
        example: ClaimExample,
        candidate: EvidenceCandidate,
    ) -> VerificationResult:
        result = self.base_verifier.verify(example, candidate)
        evidence_correct = candidate.evidence_id == example.gold_evidence_id

        # False accept: wrong evidence incorrectly trusted.
        if not evidence_correct and result.decision == "rollback":
            if self.rng.random() < self.false_accept_rate:
                return VerificationResult(
                    decision="trust",
                    risk_score=0.05,
                    reason=(
                        f"NOISE_INJECTED false_accept; original_reason={result.reason}"
                    ),
                    failure_type="noise_false_accept",
                    matched_constraints=result.matched_constraints,
                    raw_output=result.raw_output,
                )

        # False reject: correct evidence incorrectly rejected.
        if evidence_correct and result.decision == "trust":
            if self.rng.random() < self.false_reject_rate:
                return VerificationResult(
                    decision="rollback",
                    risk_score=0.95,
                    reason=(
                        f"NOISE_INJECTED false_reject; original_reason={result.reason}"
                    ),
                    failure_type="noise_false_reject",
                    matched_constraints=result.matched_constraints,
                    raw_output=result.raw_output,
                )

        return result

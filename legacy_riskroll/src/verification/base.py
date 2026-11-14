from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from riskroll.schemas import ClaimExample, EvidenceCandidate


@dataclass
class VerificationResult:
    decision: str  # trust / rollback / abstain
    risk_score: float
    reason: str
    failure_type: str = "none"
    matched_constraints: Optional[Dict[str, bool]] = None
    raw_output: Optional[str] = None


class BaseVerifier(Protocol):
    def verify(
        self,
        example: ClaimExample,
        candidate: EvidenceCandidate,
    ) -> VerificationResult:
        ...

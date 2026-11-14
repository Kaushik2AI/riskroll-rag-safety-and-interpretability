from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class EvidenceCandidate:
    evidence_id: str
    content: str
    modality: str = "unknown"
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ClaimExample:
    example_id: str
    question: str
    gold_answer: str
    gold_evidence_id: str
    candidates: List[EvidenceCandidate]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PredictionRecord:
    example_id: str
    question: str
    gold_answer: str
    predicted_answer: str
    gold_evidence_id: str
    cited_evidence_id: Optional[str]
    answer_correct: bool
    evidence_correct: bool
    grounded: bool
    action: str
    notes: str = ""

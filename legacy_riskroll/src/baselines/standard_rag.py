from dataclasses import asdict
from typing import Callable, Dict, List, Any

from riskroll.schemas import ClaimExample, PredictionRecord
from evaluation.metrics import strict_answer_correct, summarize_records


def default_answer_from_evidence(question: str, evidence_content: str) -> str:
    """
    Simple symbolic answer extractor for controlled experiments.

    Expected evidence may contain:
    answer: 123
    Answer: 123
    final answer: 123

    Later we will replace this with Qwen2.5-VL for chart/image evidence.
    """
    import re

    text = str(evidence_content)

    patterns = [
        r"final answer\s*:\s*([^\n]+)",
        r"answer\s*:\s*([^\n]+)",
        r"value\s*:\s*([^\n]+)",
    ]

    for pat in patterns:
        m = re.search(pat, text, flags=re.I)
        if m:
            return m.group(1).strip(" .,:;")

    # fallback: first number
    m = re.search(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    if m:
        return m.group(0)

    return text.strip().split("\n")[0].strip()


class StandardRAGBaseline:
    """
    Experiment 1 baseline.

    Standard RAG behavior:
    - take top-1 retrieved evidence
    - generate answer from it
    - no verifier
    - no rollback
    - no repair
    """

    def __init__(self, answer_fn: Callable[[str, str], str] = default_answer_from_evidence):
        self.answer_fn = answer_fn

    def run_one(self, example: ClaimExample) -> Dict[str, Any]:
        if not example.candidates:
            pred = "NO_EVIDENCE"
            cited_id = None
            evidence_correct = False
        else:
            top1 = example.candidates[0]
            pred = self.answer_fn(example.question, top1.content)
            cited_id = top1.evidence_id
            evidence_correct = cited_id == example.gold_evidence_id

        answer_correct = strict_answer_correct(pred, example.gold_answer)
        grounded = answer_correct and evidence_correct

        record = PredictionRecord(
            example_id=example.example_id,
            question=example.question,
            gold_answer=example.gold_answer,
            predicted_answer=pred,
            gold_evidence_id=example.gold_evidence_id,
            cited_evidence_id=cited_id,
            answer_correct=answer_correct,
            evidence_correct=evidence_correct,
            grounded=grounded,
            action="standard_rag_accept_top1",
            notes="top1 evidence used without verification",
        )

        return asdict(record)

    def run_batch(self, examples: List[ClaimExample]) -> Dict[str, Any]:
        records = [self.run_one(ex) for ex in examples]
        summary = summarize_records(records)

        return {
            "method": "standard_rag",
            "records": records,
            "summary": summary,
        }

from dataclasses import asdict
from typing import Callable, Dict, List, Any
import re

from riskroll.schemas import ClaimExample, PredictionRecord
from evaluation.metrics import strict_answer_correct, summarize_records
from baselines.standard_rag import default_answer_from_evidence


def _tokens(text: str):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return set(text.split())


def evidence_relevance_score(question: str, evidence_content: str) -> float:
    q_tokens = _tokens(question)
    e_tokens = _tokens(evidence_content)

    if not q_tokens:
        return 0.0

    return len(q_tokens & e_tokens) / len(q_tokens)


class CRAGStyleBaseline:
    """
    Experiment 1D baseline.

    CRAG-style behavior:
    - evaluate retrieved evidence quality before answering
    - select the best candidate from top-k
    - answer from selected evidence
    - no semantic prefix rollback
    - no claim-level repair loop
    """

    def __init__(
        self,
        top_k: int = 6,
        correct_threshold: float = 0.60,
        ambiguous_threshold: float = 0.35,
        answer_fn: Callable[[str, str], str] = default_answer_from_evidence,
    ):
        self.top_k = top_k
        self.correct_threshold = correct_threshold
        self.ambiguous_threshold = ambiguous_threshold
        self.answer_fn = answer_fn

    def _label_score(self, score: float) -> str:
        if score >= self.correct_threshold:
            return "correct"
        if score >= self.ambiguous_threshold:
            return "ambiguous"
        return "incorrect"

    def _select_evidence(self, example: ClaimExample) -> Dict[str, Any]:
        scored = []

        for rank, cand in enumerate(example.candidates[: self.top_k], start=1):
            score = evidence_relevance_score(example.question, cand.content)
            label = self._label_score(score)

            scored.append({
                "rank": rank,
                "evidence_id": cand.evidence_id,
                "score": score,
                "label": label,
                "content": cand.content,
            })

        if not scored:
            return {
                "selected_evidence": None,
                "selected_label": "no_evidence",
                "scored_candidates": [],
                "notes": "no evidence candidates",
            }

        # Prefer correct > ambiguous > incorrect, then higher score, then earlier rank.
        label_priority = {
            "correct": 0,
            "ambiguous": 1,
            "incorrect": 2,
        }

        scored.sort(key=lambda x: (label_priority[x["label"]], -x["score"], x["rank"]))
        best = scored[0]

        return {
            "selected_evidence": best,
            "selected_label": best["label"],
            "scored_candidates": scored,
            "notes": (
                f"crag_selected_rank={best['rank']}; "
                f"label={best['label']}; score={best['score']:.4f}"
            ),
        }

    def run_one(self, example: ClaimExample) -> Dict[str, Any]:
        selected = self._select_evidence(example)

        if selected["selected_evidence"] is None:
            pred = "NO_EVIDENCE"
            cited_id = None
        else:
            ev = selected["selected_evidence"]
            pred = self.answer_fn(example.question, ev["content"])
            cited_id = ev["evidence_id"]

        answer_correct = strict_answer_correct(pred, example.gold_answer)
        evidence_correct = cited_id == example.gold_evidence_id
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
            action=f"crag_style_top{self.top_k}",
            notes=selected["notes"],
        )

        out = asdict(record)
        out["selected_label"] = selected["selected_label"]
        out["scored_candidates"] = selected["scored_candidates"]

        return out

    def run_batch(self, examples: List[ClaimExample]) -> Dict[str, Any]:
        records = [self.run_one(ex) for ex in examples]
        summary = summarize_records(records)

        return {
            "method": f"crag_style_top{self.top_k}",
            "records": records,
            "summary": summary,
        }

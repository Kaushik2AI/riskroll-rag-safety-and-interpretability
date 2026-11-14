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


def lexical_overlap_score(question: str, evidence_content: str) -> float:
    """
    Simple non-oracle post-hoc scorer.

    It chooses evidence that lexically matches the question best.
    This is weaker than RiskRoll because it is not claim-prefix aware.
    """
    q_tokens = _tokens(question)
    e_tokens = _tokens(evidence_content)

    if not q_tokens:
        return 0.0

    return len(q_tokens & e_tokens) / len(q_tokens)


class PostHocCorrectionBaseline:
    """
    Experiment 1C baseline.

    Post-hoc correction behavior:
    - generate initial answer from top-1 evidence
    - after generation, inspect top-k candidates
    - choose the candidate with highest question-evidence lexical match
    - rewrite answer from that candidate
    - no rollback
    - no trusted-prefix control
    """

    def __init__(
        self,
        top_k: int = 6,
        answer_fn: Callable[[str, str], str] = default_answer_from_evidence,
    ):
        self.top_k = top_k
        self.answer_fn = answer_fn

    def _choose_best_posthoc_candidate(self, example: ClaimExample) -> Dict[str, Any]:
        scored = []

        for rank, cand in enumerate(example.candidates[: self.top_k], start=1):
            score = lexical_overlap_score(example.question, cand.content)
            pred = self.answer_fn(example.question, cand.content)

            scored.append({
                "rank": rank,
                "evidence_id": cand.evidence_id,
                "score": score,
                "predicted_answer": pred,
                "content": cand.content,
            })

        if not scored:
            return {
                "predicted_answer": "NO_EVIDENCE",
                "cited_evidence_id": None,
                "posthoc_candidates": [],
                "notes": "no evidence candidates",
            }

        # Highest lexical overlap; if tied, earlier rank wins.
        scored.sort(key=lambda x: (-x["score"], x["rank"]))
        best = scored[0]

        return {
            "predicted_answer": best["predicted_answer"],
            "cited_evidence_id": best["evidence_id"],
            "posthoc_candidates": scored,
            "notes": f"posthoc_selected_rank={best['rank']}; lexical_score={best['score']:.4f}",
        }

    def run_one(self, example: ClaimExample) -> Dict[str, Any]:
        # Initial normal RAG answer from top-1.
        if example.candidates:
            top1 = example.candidates[0]
            initial_pred = self.answer_fn(example.question, top1.content)
            initial_evidence_id = top1.evidence_id
        else:
            initial_pred = "NO_EVIDENCE"
            initial_evidence_id = None

        # Post-hoc correction after initial answer exists.
        corrected = self._choose_best_posthoc_candidate(example)

        pred = corrected["predicted_answer"]
        cited_id = corrected["cited_evidence_id"]

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
            action=f"posthoc_correction_top{self.top_k}",
            notes=corrected["notes"],
        )

        out = asdict(record)
        out["initial_predicted_answer"] = initial_pred
        out["initial_cited_evidence_id"] = initial_evidence_id
        out["posthoc_candidates"] = corrected["posthoc_candidates"]

        return out

    def run_batch(self, examples: List[ClaimExample]) -> Dict[str, Any]:
        records = [self.run_one(ex) for ex in examples]
        summary = summarize_records(records)

        return {
            "method": f"posthoc_correction_top{self.top_k}",
            "records": records,
            "summary": summary,
        }

from dataclasses import asdict
from collections import Counter
from typing import Callable, Dict, List, Any

from riskroll.schemas import ClaimExample, PredictionRecord
from evaluation.metrics import strict_answer_correct, summarize_records, norm_text
from baselines.standard_rag import default_answer_from_evidence


class RetrieveMoreBaseline:
    """
    Experiment 1B baseline.

    Retrieve-more RAG behavior:
    - look at top-k retrieved evidence candidates
    - extract one answer from each candidate
    - choose the majority answer
    - if tie, choose the answer from the earlier-ranked evidence
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

    def _choose_majority_answer(self, question: str, candidates) -> Dict[str, Any]:
        extracted = []

        for rank, cand in enumerate(candidates[: self.top_k], start=1):
            ans = self.answer_fn(question, cand.content)
            extracted.append({
                "rank": rank,
                "answer": ans,
                "answer_norm": norm_text(ans),
                "evidence_id": cand.evidence_id,
            })

        if not extracted:
            return {
                "predicted_answer": "NO_EVIDENCE",
                "cited_evidence_id": None,
                "candidate_answers": [],
                "notes": "no evidence candidates",
            }

        counts = Counter(x["answer_norm"] for x in extracted)
        best_norm, best_count = counts.most_common(1)[0]

        # Tie-breaking: first candidate in retrieved order with majority answer.
        chosen = next(x for x in extracted if x["answer_norm"] == best_norm)

        return {
            "predicted_answer": chosen["answer"],
            "cited_evidence_id": chosen["evidence_id"],
            "candidate_answers": extracted,
            "notes": f"majority_vote_count={best_count}; tie_break=earliest_rank",
        }

    def run_one(self, example: ClaimExample) -> Dict[str, Any]:
        chosen = self._choose_majority_answer(example.question, example.candidates)

        pred = chosen["predicted_answer"]
        cited_id = chosen["cited_evidence_id"]

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
            action=f"retrieve_more_top{self.top_k}_majority_vote",
            notes=chosen["notes"],
        )

        out = asdict(record)
        out["candidate_answers"] = chosen["candidate_answers"]
        return out

    def run_batch(self, examples: List[ClaimExample]) -> Dict[str, Any]:
        records = [self.run_one(ex) for ex in examples]
        summary = summarize_records(records)

        return {
            "method": f"retrieve_more_top{self.top_k}",
            "records": records,
            "summary": summary,
        }

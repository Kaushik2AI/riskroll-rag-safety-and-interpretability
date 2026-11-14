from dataclasses import asdict
from typing import Callable, Dict, List, Any, Optional

from riskroll.schemas import ClaimExample, PredictionRecord
from verification.base import BaseVerifier
from evaluation.metrics import strict_answer_correct, summarize_records
from baselines.standard_rag import default_answer_from_evidence


class RiskRollController:
    """
    Experiment 2 RiskRoll controller.

    Flow:
    1. For each claim/example, inspect candidate evidence in retrieved order.
    2. Verify candidate evidence before committing the claim.
    3. If verifier says rollback, do not commit the tentative claim.
    4. Try the next candidate.
    5. If verifier says trust, generate answer from that evidence and commit claim.
    6. If no evidence is trusted, abstain.

    This controller is verifier-agnostic:
    - controlled verifier
    - VLM verifier
    - hybrid verifier
    """

    def __init__(
        self,
        verifier: BaseVerifier,
        top_k: int = 6,
        answer_fn: Callable[[str, str], str] = default_answer_from_evidence,
    ):
        self.verifier = verifier
        self.top_k = top_k
        self.answer_fn = answer_fn

    def _make_claim_text(
        self,
        step_id: int,
        question: str,
        answer: str,
        evidence_id: Optional[str],
    ) -> str:
        return (
            f"Claim {step_id}: For the question '{question}', "
            f"the answer is '{answer}' [evidence: {evidence_id}]."
        )

    def _riskroll_contamination(self, accepted_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        For RiskRoll, abstention is not treated as unsafe prefix contamination.
        Unsafe contamination happens only when a wrong ungrounded claim is committed.
        """
        first_bad_step = None

        for i, r in enumerate(accepted_records, start=1):
            if r["action"] == "abstain_no_trusted_evidence":
                continue

            if not r.get("grounded", False):
                first_bad_step = i
                break

        if first_bad_step is None:
            return {
                "first_bad_step": None,
                "unsafe_prefix_depth": 0,
                "downstream_contaminated_claims": 0,
            }

        downstream = sum(
            1
            for i, _ in enumerate(accepted_records, start=1)
            if i > first_bad_step
        )

        return {
            "first_bad_step": first_bad_step,
            "unsafe_prefix_depth": downstream,
            "downstream_contaminated_claims": downstream,
        }

    def run_sequence(self, examples: List[ClaimExample]) -> Dict[str, Any]:
        trusted_prefix = []
        events = []
        accepted_records = []

        rollback_count = 0
        repair_count = 0
        abstention_count = 0
        verifier_false_accepts = 0
        verifier_false_rejects = 0

        for step_id, example in enumerate(examples, start=1):
            accepted = False
            repair_attempts = 0
            last_trusted_prefix_len = len(trusted_prefix)

            for rank, candidate in enumerate(example.candidates[: self.top_k], start=1):
                verification = self.verifier.verify(example, candidate)

                evidence_correct = candidate.evidence_id == example.gold_evidence_id

                # Diagnostic only. This uses gold ID for analysis, not for the verifier decision.
                if verification.decision == "trust" and not evidence_correct:
                    verifier_false_accepts += 1

                if verification.decision == "rollback" and evidence_correct:
                    verifier_false_rejects += 1

                if verification.decision != "trust":
                    rollback_count += 1
                    repair_attempts += 1

                    events.append({
                        "example_id": example.example_id,
                        "step_id": step_id,
                        "candidate_rank": rank,
                        "question": example.question,
                        "gold_answer": example.gold_answer,
                        "predicted_answer": "",
                        "gold_evidence_id": example.gold_evidence_id,
                        "cited_evidence_id": candidate.evidence_id,
                        "answer_correct": False,
                        "evidence_correct": evidence_correct,
                        "grounded": False,
                        "risk_score": verification.risk_score,
                        "verifier_decision": verification.decision,
                        "failure_type": verification.failure_type,
                        "matched_constraints": verification.matched_constraints,
                        "action": "rollback_tentative_claim",
                        "rollback_to_prefix_len": last_trusted_prefix_len,
                        "repair_attempts": repair_attempts,
                        "notes": verification.reason,
                    })
                    continue

                pred = self.answer_fn(example.question, candidate.content)
                answer_correct = strict_answer_correct(pred, example.gold_answer)
                grounded = answer_correct and evidence_correct

                action = "accept_trusted_claim"
                if repair_attempts > 0:
                    action = "repair_and_accept_claim"
                    repair_count += 1

                claim_text = self._make_claim_text(
                    step_id=step_id,
                    question=example.question,
                    answer=pred,
                    evidence_id=candidate.evidence_id,
                )

                record = PredictionRecord(
                    example_id=example.example_id,
                    question=example.question,
                    gold_answer=example.gold_answer,
                    predicted_answer=pred,
                    gold_evidence_id=example.gold_evidence_id,
                    cited_evidence_id=candidate.evidence_id,
                    answer_correct=answer_correct,
                    evidence_correct=evidence_correct,
                    grounded=grounded,
                    action=action,
                    notes=verification.reason,
                )

                rec = asdict(record)
                rec.update({
                    "step_id": step_id,
                    "candidate_rank": rank,
                    "claim_text": claim_text,
                    "risk_score": verification.risk_score,
                    "verifier_decision": verification.decision,
                    "failure_type": verification.failure_type,
                    "matched_constraints": verification.matched_constraints,
                    "rollback_to_prefix_len": None,
                    "repair_attempts": repair_attempts,
                })

                trusted_prefix.append(claim_text)
                events.append(rec)
                accepted_records.append(rec)

                accepted = True
                break

            if not accepted:
                abstention_count += 1

                claim_text = (
                    f"Claim {step_id}: Not enough trusted evidence to answer "
                    f"'{example.question}'."
                )

                trusted_prefix.append(claim_text)

                record = PredictionRecord(
                    example_id=example.example_id,
                    question=example.question,
                    gold_answer=example.gold_answer,
                    predicted_answer="Not enough trusted evidence",
                    gold_evidence_id=example.gold_evidence_id,
                    cited_evidence_id=None,
                    answer_correct=False,
                    evidence_correct=False,
                    grounded=False,
                    action="abstain_no_trusted_evidence",
                    notes="no candidate passed verifier",
                )

                rec = asdict(record)
                rec.update({
                    "step_id": step_id,
                    "candidate_rank": None,
                    "claim_text": claim_text,
                    "risk_score": 1.0,
                    "verifier_decision": "abstain",
                    "failure_type": "no_trusted_evidence",
                    "matched_constraints": {},
                    "rollback_to_prefix_len": last_trusted_prefix_len,
                    "repair_attempts": repair_attempts,
                })

                events.append(rec)
                accepted_records.append(rec)

        summary = summarize_records(accepted_records)
        contamination = self._riskroll_contamination(accepted_records)

        summary.update(contamination)
        summary.update({
            "rollback_count": rollback_count,
            "repair_count": repair_count,
            "abstention_count": abstention_count,
            "verifier_false_accepts": verifier_false_accepts,
            "verifier_false_rejects": verifier_false_rejects,
        })

        return {
            "method": "riskroll_controlled",
            "prefix": trusted_prefix,
            "events": events,
            "records": accepted_records,
            "summary": summary,
        }

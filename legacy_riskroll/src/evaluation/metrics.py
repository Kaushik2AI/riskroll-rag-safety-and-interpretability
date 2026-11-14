import re
from statistics import mean
from typing import Any, Dict, List, Optional


def norm_text(s: Any) -> str:
    s = str(s).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .,:;%")


def first_number(s: Any) -> Optional[float]:
    s = str(s).replace(",", "")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return None
    return float(m.group(0))


def is_year_like(x: Any) -> bool:
    n = first_number(x)
    if n is None:
        return False
    return 1900 <= n <= 2100 and abs(n - round(n)) < 1e-6


def strict_answer_correct(pred: Any, gold: Any) -> bool:
    p = norm_text(pred)
    g = norm_text(gold)

    if g in ["yes", "no"]:
        return p.startswith(g)

    if is_year_like(gold):
        pn = first_number(pred)
        gn = first_number(gold)
        if pn is None or gn is None:
            return False
        return int(round(pn)) == int(round(gn))

    gold_num = first_number(gold)
    pred_num = first_number(pred)

    if gold_num is not None:
        if pred_num is None:
            return False

        if abs(gold_num - round(gold_num)) < 1e-6:
            return int(round(pred_num)) == int(round(gold_num))

        if "%" in str(pred):
            pred_scaled = pred_num / 100.0
            if abs(pred_scaled - gold_num) <= 0.01:
                return True

        return abs(pred_num - gold_num) <= 0.01

    return p == g or g in p or p in g


def compute_contamination(records: List[Dict]) -> Dict[str, Any]:
    first_bad_step = None

    for i, r in enumerate(records, start=1):
        if not r.get("grounded", False):
            first_bad_step = i
            break

    if first_bad_step is None:
        return {
            "first_bad_step": None,
            "unsafe_prefix_depth": 0,
            "downstream_contaminated_claims": 0,
        }

    downstream = sum(1 for i, _ in enumerate(records, start=1) if i > first_bad_step)

    return {
        "first_bad_step": first_bad_step,
        "unsafe_prefix_depth": downstream,
        "downstream_contaminated_claims": downstream,
    }


def summarize_records(records: List[Dict]) -> Dict[str, Any]:
    if not records:
        return {
            "n": 0,
            "claim_accuracy": 0.0,
            "evidence_accuracy": 0.0,
            "grounded_claim_rate": 0.0,
            "wrong_evidence_count": 0,
            "unsafe_prefix_depth": 0,
            "downstream_contaminated_claims": 0,
        }

    contamination = compute_contamination(records)

    return {
        "n": len(records),
        "claim_accuracy": mean(bool(r["answer_correct"]) for r in records),
        "evidence_accuracy": mean(bool(r["evidence_correct"]) for r in records),
        "grounded_claim_rate": mean(bool(r["grounded"]) for r in records),
        "wrong_evidence_count": sum(not bool(r["evidence_correct"]) for r in records),
        **contamination,
    }

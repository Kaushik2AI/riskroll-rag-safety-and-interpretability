import re
from typing import Any, Optional


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

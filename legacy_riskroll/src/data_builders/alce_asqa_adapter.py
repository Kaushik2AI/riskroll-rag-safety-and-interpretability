from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional


def norm_text(x: str) -> str:
    x = unicodedata.normalize("NFKD", str(x))
    x = "".join(ch for ch in x if not unicodedata.combining(ch))
    x = x.lower()
    x = x.replace("–", "-").replace("—", "-")
    x = re.sub(r"[^a-z0-9]+", " ", x)
    return re.sub(r"\s+", " ", x).strip()


def clean_text(x: Any) -> str:
    if x is None:
        return ""
    return re.sub(r"\s+", " ", str(x)).strip()


def doc_blob(doc: Dict[str, Any]) -> str:
    parts = [
        doc.get("title", ""),
        doc.get("summary", ""),
        doc.get("extraction", ""),
        doc.get("text", ""),
    ]
    return " ".join(clean_text(p) for p in parts if clean_text(p))


def alias_supported_by_doc(aliases: List[str], doc: Dict[str, Any]) -> bool:
    blob = norm_text(doc_blob(doc))
    for alias in aliases:
        a = norm_text(alias)
        if len(a) >= 2 and a in blob:
            return True
    return False


def normalize_aliases(short_answers: Any) -> List[str]:
    if short_answers is None:
        return []

    if isinstance(short_answers, str):
        short_answers = [short_answers]

    aliases = []
    seen = set()

    for ans in short_answers:
        ans = clean_text(ans)
        if not ans:
            continue

        key = norm_text(ans)
        if not key or key in seen:
            continue

        seen.add(key)
        aliases.append(ans)

    return aliases


def simplify_doc(doc: Dict[str, Any], rank: int, aliases: List[str]) -> Dict[str, Any]:
    return {
        "rank": rank,
        "id": str(doc.get("id", "")),
        "title": clean_text(doc.get("title", "")),
        "text": clean_text(doc.get("text", "")),
        "summary": clean_text(doc.get("summary", "")),
        "extraction": clean_text(doc.get("extraction", "")),
        "score": doc.get("score", None),
        "supports_gold_alias": alias_supported_by_doc(aliases, doc),
    }


def build_asqa_tasks(
    input_path: str | Path,
    max_records: Optional[int] = 100,
    docs_top_k: int = 20,
    max_claims_per_task: int = 5,
    min_claims_per_task: int = 2,
    require_support_in_top100: bool = True,
) -> Dict[str, Any]:
    input_path = Path(input_path)
    data = json.loads(input_path.read_text(encoding="utf-8"))

    tasks = []
    skipped_no_docs = 0
    skipped_too_few_claims = 0
    skipped_no_supported_claims = 0

    records = data if max_records is None else data[:max_records]
    all_first_support_ranks = []
    all_claims = 0

    for rec_idx, rec in enumerate(records):
        docs = rec.get("docs", []) or []
        qa_pairs = rec.get("qa_pairs", []) or []

        if not docs:
            skipped_no_docs += 1
            continue

        claims = []

        for claim_idx, qa in enumerate(qa_pairs[:max_claims_per_task]):
            subq = clean_text(qa.get("question", ""))
            aliases = normalize_aliases(qa.get("short_answers", []))

            if not subq or not aliases:
                continue

            support_ranks = []
            for rank, doc in enumerate(docs, start=1):
                if alias_supported_by_doc(aliases, doc):
                    support_ranks.append(rank)

            first_support_rank = support_ranks[0] if support_ranks else None

            if require_support_in_top100 and first_support_rank is None:
                continue

            candidate_docs = [
                simplify_doc(doc, rank, aliases)
                for rank, doc in enumerate(docs[:docs_top_k], start=1)
            ]

            claims.append({
                "claim_id": f"asqa_{rec_idx:04d}_claim_{claim_idx:02d}",
                "subquestion": subq,
                "gold_answers": aliases,
                "gold_answer": aliases[0],
                "support_ranks": support_ranks,
                "first_support_rank": first_support_rank,
                "candidate_docs": candidate_docs,
                "metadata": {
                    "wikipage": qa.get("wikipage"),
                    "context": clean_text(qa.get("context", "")),
                },
            })

            if first_support_rank is not None:
                all_first_support_ranks.append(first_support_rank)

        if len(claims) < min_claims_per_task:
            skipped_too_few_claims += 1
            if len(claims) == 0:
                skipped_no_supported_claims += 1
            continue

        tasks.append({
            "task_id": f"alce_asqa_{len(tasks):04d}",
            "source_index": rec_idx,
            "sample_id": rec.get("sample_id"),
            "question": clean_text(rec.get("question", "")),
            "gold_long_answer": clean_text(rec.get("answer", "")),
            "claims": claims,
            "num_claims": len(claims),
            "metadata": {
                "wikipages": rec.get("wikipages", []),
                "annotations": rec.get("annotations", []),
            },
        })

        all_claims += len(claims)

    def rate_at(k: int) -> float:
        if not all_first_support_ranks:
            return 0.0
        return sum(1 for r in all_first_support_ranks if r <= k) / len(all_first_support_ranks)

    stats = {
        "input_path": str(input_path),
        "records_read": len(records),
        "tasks_built": len(tasks),
        "total_claims": all_claims,
        "mean_claims_per_task": all_claims / len(tasks) if tasks else 0.0,
        "docs_top_k": docs_top_k,
        "max_claims_per_task": max_claims_per_task,
        "require_support_in_top100": require_support_in_top100,
        "skipped_no_docs": skipped_no_docs,
        "skipped_too_few_claims": skipped_too_few_claims,
        "skipped_no_supported_claims": skipped_no_supported_claims,
        "mean_first_support_rank": (
            sum(all_first_support_ranks) / len(all_first_support_ranks)
            if all_first_support_ranks else 0.0
        ),
        "top1_support_rate": rate_at(1),
        "top5_support_rate": rate_at(5),
        "top20_support_rate": rate_at(20),
    }

    return {
        "tasks": tasks,
        "stats": stats,
    }

from pathlib import Path
import json
import re
from statistics import mean


def norm_text(s):
    s = str(s).lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def alias_in_text(aliases, text):
    text_n = norm_text(text)
    for a in aliases:
        a_n = norm_text(a)
        if not a_n:
            continue
        if a_n in text_n:
            return True
    return False


def load_json_records(path):
    path = Path(path)
    obj = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(obj, list):
        return obj

    if isinstance(obj, dict):
        for key in ["data", "examples", "records", "items"]:
            if key in obj and isinstance(obj[key], list):
                return obj[key]

    raise ValueError(f"Could not detect record list in {path}")


def clean_doc(doc, rank):
    return {
        "rank": rank,
        "doc_id": str(doc.get("id", f"doc_{rank}")),
        "title": str(doc.get("title", "")),
        "text": str(doc.get("text", "")),
    }


def find_supporting_doc_ranks(aliases, docs):
    ranks = []
    for i, doc in enumerate(docs, start=1):
        blob = f"{doc.get('title', '')} {doc.get('text', '')}"
        if alias_in_text(aliases, blob):
            ranks.append(i)
    return ranks


def flatten_answers(answer_groups):
    """
    QAMPARI answers are usually:
    [
      ["Heat"],
      ["Mai, the Psychic Girl"],
      ...
    ]

    Each group may contain aliases. We keep the first alias as canonical.
    """
    out = []
    for group in answer_groups:
        if isinstance(group, list) and len(group) > 0:
            aliases = [str(x) for x in group if str(x).strip()]
            if aliases:
                out.append({
                    "canonical": aliases[0],
                    "aliases": aliases,
                })
        elif isinstance(group, str) and group.strip():
            out.append({
                "canonical": group.strip(),
                "aliases": [group.strip()],
            })
    return out


def build_qampari_tasks(
    input_path,
    n_tasks=100,
    claims_per_task=5,
    retrieval_top_k=20,
    require_support_in_top100=True,
):
    records = load_json_records(input_path)

    tasks = []
    skipped_no_docs = 0
    skipped_too_few_answers = 0
    skipped_no_support = 0

    gold_ranks = []
    top1_hits = 0
    top5_hits = 0
    top20_hits = 0
    total_claims = 0

    for rec in records:
        if len(tasks) >= n_tasks:
            break

        qid = str(rec.get("id", rec.get("sample_id", f"record_{len(tasks)}")))
        question = str(rec.get("question", "")).strip()
        docs_raw = rec.get("docs", [])
        answer_groups = rec.get("answers", [])

        if not docs_raw:
            skipped_no_docs += 1
            continue

        answers = flatten_answers(answer_groups)

        if len(answers) < claims_per_task:
            skipped_too_few_answers += 1
            continue

        docs = [clean_doc(d, rank=i) for i, d in enumerate(docs_raw, start=1)]

        claims = []
        for answer_idx, ans in enumerate(answers):
            aliases = ans["aliases"]
            canonical = ans["canonical"]

            support_ranks = find_supporting_doc_ranks(aliases, docs_raw)

            if require_support_in_top100 and not support_ranks:
                continue

            first_support_rank = support_ranks[0] if support_ranks else None

            candidate_docs = []
            for d in docs[:retrieval_top_k]:
                blob = f"{d['title']} {d['text']}"
                d2 = dict(d)
                d2["contains_gold_alias"] = alias_in_text(aliases, blob)
                candidate_docs.append(d2)

            claim = {
                "claim_id": f"{qid}__claim_{answer_idx:02d}",
                "answer_index": answer_idx,
                "question": question,
                "claim_prompt": (
                    f"Question: {question}\n"
                    f"Provide one correct answer item from the requested list."
                ),
                "gold_answer": canonical,
                "aliases": aliases,
                "support_doc_ranks": support_ranks,
                "first_support_rank": first_support_rank,
                "candidate_docs": candidate_docs,
            }

            claims.append(claim)

            gold_ranks.append(first_support_rank if first_support_rank is not None else 999)
            if first_support_rank == 1:
                top1_hits += 1
            if first_support_rank is not None and first_support_rank <= 5:
                top5_hits += 1
            if first_support_rank is not None and first_support_rank <= 20:
                top20_hits += 1

            if len(claims) >= claims_per_task:
                break

        if len(claims) < claims_per_task:
            skipped_no_support += 1
            continue

        task = {
            "task_id": f"alce_qampari_{len(tasks):04d}",
            "source_id": qid,
            "dataset": "ALCE-QAMPARI",
            "question": question,
            "gold_answer_list": [c["gold_answer"] for c in claims],
            "claims": claims,
            "metadata": {
                "claims_per_task": claims_per_task,
                "retrieval_top_k": retrieval_top_k,
            },
        }

        tasks.append(task)
        total_claims += len(claims)

    summary = {
        "input_path": str(input_path),
        "records_read": len(records),
        "tasks_built": len(tasks),
        "claims_per_task": claims_per_task,
        "total_claims": total_claims,
        "retrieval_top_k": retrieval_top_k,
        "require_support_in_top100": require_support_in_top100,
        "skipped_no_docs": skipped_no_docs,
        "skipped_too_few_answers": skipped_too_few_answers,
        "skipped_no_support": skipped_no_support,
        "mean_first_support_rank": mean(gold_ranks) if gold_ranks else None,
        "top1_support_rate": top1_hits / total_claims if total_claims else 0.0,
        "top5_support_rate": top5_hits / total_claims if total_claims else 0.0,
        "top20_support_rate": top20_hits / total_claims if total_claims else 0.0,
    }

    return tasks, summary


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from experiments.experiment7d_alce_qampari_llm_generation import load_model, generate_text


TASK_PATH = PROJECT / "results" / "raw" / "experiment8_alce_asqa_public_tasks.json"

RAW_DIR = PROJECT / "results" / "raw"
TABLE_DIR = PROJECT / "results" / "tables"
REPORT_DIR = PROJECT / "results" / "reports"

RAW_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


METHODS = {
    "standard_top1": "Standard RAG top-1",
    "retrieve_more_top20": "Retrieve-more RAG top-20",
    "posthoc_top20": "Post-hoc correction top-20",
    "crag_style_top20": "CRAG-style correction top-20",
    "riskroll_top20": "RiskRoll verify-before-commit top-20",
}


def norm_text(x: Any) -> str:
    x = unicodedata.normalize("NFKD", str(x))
    x = "".join(ch for ch in x if not unicodedata.combining(ch))
    x = x.lower()
    x = x.replace("–", "-").replace("—", "-")
    x = re.sub(r"[^a-z0-9]+", " ", x)
    return re.sub(r"\s+", " ", x).strip()


def is_unknown(x: Any) -> bool:
    return norm_text(x) in {"", "unknown", "not enough information", "cannot determine"}


def clean_answer(x: str) -> str:
    x = str(x).strip()
    x = re.sub(r"^[-*\d\.\)\s]+", "", x).strip()
    x = re.sub(r"^(answer|final answer)\s*:\s*", "", x, flags=re.I).strip()
    x = x.strip('"').strip("'").strip()
    if not x:
        return "UNKNOWN"
    if len(x) > 160:
        x = x[:160].strip()
    return x


def parse_candidates(output: str, max_items: int = 3) -> List[str]:
    lines = []
    for line in str(output).splitlines():
        line = clean_answer(line)
        if not line:
            continue
        if norm_text(line).startswith("here"):
            continue
        lines.append(line)

    if not lines:
        one = clean_answer(output)
        lines = [one]

    out = []
    seen = set()
    for item in lines:
        k = norm_text(item)
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(item)
        if len(out) >= max_items:
            break

    return out if out else ["UNKNOWN"]


def doc_text(doc: Dict[str, Any]) -> str:
    parts = [
        doc.get("title", ""),
        doc.get("summary", ""),
        doc.get("extraction", ""),
        doc.get("text", ""),
    ]
    return " ".join(str(p) for p in parts if p)


def answer_supported_by_docs(answer: str, docs: List[Dict[str, Any]]) -> bool:
    if is_unknown(answer):
        return False

    a = norm_text(answer)
    if len(a) < 2:
        return False

    blob = norm_text(" ".join(doc_text(d) for d in docs))
    return a in blob


def answer_matches_gold(answer: str, aliases: List[str]) -> bool:
    if is_unknown(answer):
        return False

    a = norm_text(answer)

    for alias in aliases:
        g = norm_text(alias)
        if not g:
            continue

        if g in a or a in g:
            return True

    return False


def compact_docs(docs: List[Dict[str, Any]], max_chars_per_doc: int = 650) -> str:
    chunks = []

    for d in docs:
        rank = d.get("rank", "?")
        title = str(d.get("title", "")).strip()
        text = str(d.get("summary") or d.get("extraction") or d.get("text") or "").strip()
        text = re.sub(r"\s+", " ", text)
        text = text[:max_chars_per_doc]

        chunks.append(f"[{rank}] {title}\n{text}")

    return "\n\n".join(chunks)


def lexical_score(query: str, doc: Dict[str, Any]) -> int:
    q_terms = set(norm_text(query).split())
    d_terms = set(norm_text(doc_text(doc)).split())
    return len(q_terms & d_terms)


def select_crag_docs(claim: Dict[str, Any], top_k: int = 8) -> List[Dict[str, Any]]:
    docs = claim["candidate_docs"][:20]
    scored = sorted(
        docs,
        key=lambda d: lexical_score(claim["subquestion"], d),
        reverse=True,
    )
    return scored[:top_k]


def make_short_answer_prompt(main_question: str, subquestion: str, docs: List[Dict[str, Any]]) -> str:
    return f"""Main question:
{main_question}

Sub-question:
{subquestion}

Evidence:
{compact_docs(docs)}

Task:
Answer the sub-question using only the evidence.
Return one short answer entity or phrase.
Do not explain.
If the evidence does not support an answer, return UNKNOWN.
"""


def make_posthoc_prompt(main_question: str, subquestion: str, initial_answer: str, docs: List[Dict[str, Any]]) -> str:
    return f"""Main question:
{main_question}

Sub-question:
{subquestion}

Initial answer:
{initial_answer}

Evidence:
{compact_docs(docs)}

Task:
Check the initial answer against the evidence.
If correct, return the same short answer.
If wrong, return the corrected short answer.
If the evidence does not support an answer, return UNKNOWN.
Return only one short answer.
"""


def make_riskroll_prompt(main_question: str, subquestion: str, committed: List[str], docs: List[Dict[str, Any]]) -> str:
    trusted = "; ".join(committed) if committed else "None"

    return f"""Main question:
{main_question}

Trusted answer prefix so far:
{trusted}

Current sub-question:
{subquestion}

Evidence:
{compact_docs(docs)}

Task:
List up to 3 candidate short answers for the current sub-question.
Each candidate must be directly supported by the evidence.
Do not repeat the trusted prefix.
Return one candidate per line.
Do not explain.
If no supported answer is available, return UNKNOWN.
"""


def generate_one(tokenizer, model, prompt: str, temperature: float) -> str:
    out = generate_text(tokenizer, model, prompt, max_new_tokens=64, temperature=temperature)
    return parse_candidates(out, max_items=1)[0]


def run_standard(tokenizer, model, task: Dict[str, Any], temperature: float) -> Dict[str, Any]:
    items = []
    evidence_docs = []
    raw_outputs = []

    for claim in task["claims"]:
        docs = claim["candidate_docs"][:1]
        prompt = make_short_answer_prompt(task["question"], claim["subquestion"], docs)
        out = generate_text(tokenizer, model, prompt, max_new_tokens=64, temperature=temperature)
        ans = parse_candidates(out, max_items=1)[0]

        items.append(ans)
        evidence_docs.append(docs)
        raw_outputs.append(out)

    return {
        "items": items,
        "evidence_docs_per_claim": evidence_docs,
        "raw_outputs": raw_outputs,
        "rollback_count": 0,
        "repair_count": 0,
    }


def run_retrieve_more(tokenizer, model, task: Dict[str, Any], temperature: float) -> Dict[str, Any]:
    items = []
    evidence_docs = []
    raw_outputs = []

    for claim in task["claims"]:
        docs = claim["candidate_docs"][:20]
        prompt = make_short_answer_prompt(task["question"], claim["subquestion"], docs)
        out = generate_text(tokenizer, model, prompt, max_new_tokens=64, temperature=temperature)
        ans = parse_candidates(out, max_items=1)[0]

        items.append(ans)
        evidence_docs.append(docs)
        raw_outputs.append(out)

    return {
        "items": items,
        "evidence_docs_per_claim": evidence_docs,
        "raw_outputs": raw_outputs,
        "rollback_count": 0,
        "repair_count": 0,
    }


def run_posthoc(tokenizer, model, task: Dict[str, Any], temperature: float) -> Dict[str, Any]:
    initial_items = []
    initial_docs = []
    final_items = []
    final_docs = []
    raw_outputs = []
    repair_count = 0

    for claim in task["claims"]:
        docs1 = claim["candidate_docs"][:1]
        prompt1 = make_short_answer_prompt(task["question"], claim["subquestion"], docs1)
        out1 = generate_text(tokenizer, model, prompt1, max_new_tokens=64, temperature=temperature)
        ans1 = parse_candidates(out1, max_items=1)[0]

        docs20 = claim["candidate_docs"][:20]
        prompt2 = make_posthoc_prompt(task["question"], claim["subquestion"], ans1, docs20)
        out2 = generate_text(tokenizer, model, prompt2, max_new_tokens=64, temperature=temperature)
        ans2 = parse_candidates(out2, max_items=1)[0]

        if norm_text(ans1) != norm_text(ans2):
            repair_count += 1

        initial_items.append(ans1)
        initial_docs.append(docs1)
        final_items.append(ans2)
        final_docs.append(docs20)
        raw_outputs.append({"initial": out1, "revised": out2})

    return {
        "items": final_items,
        "evidence_docs_per_claim": final_docs,
        "initial_items": initial_items,
        "initial_evidence_docs_per_claim": initial_docs,
        "raw_outputs": raw_outputs,
        "rollback_count": 0,
        "repair_count": repair_count,
    }


def run_crag_style(tokenizer, model, task: Dict[str, Any], temperature: float) -> Dict[str, Any]:
    items = []
    evidence_docs = []
    raw_outputs = []

    for claim in task["claims"]:
        docs = select_crag_docs(claim, top_k=8)
        prompt = make_short_answer_prompt(task["question"], claim["subquestion"], docs)
        out = generate_text(tokenizer, model, prompt, max_new_tokens=64, temperature=temperature)
        ans = parse_candidates(out, max_items=1)[0]

        items.append(ans)
        evidence_docs.append(docs)
        raw_outputs.append(out)

    return {
        "items": items,
        "evidence_docs_per_claim": evidence_docs,
        "raw_outputs": raw_outputs,
        "rollback_count": 0,
        "repair_count": 0,
    }


def run_riskroll(tokenizer, model, task: Dict[str, Any], temperature: float) -> Dict[str, Any]:
    items = []
    evidence_docs = []
    raw_outputs = []

    rollback_count = 0
    repair_count = 0

    windows = [1, 5, 10, 20]

    for claim in task["claims"]:
        accepted = False

        for k in windows:
            docs = claim["candidate_docs"][:k]
            prompt = make_riskroll_prompt(task["question"], claim["subquestion"], items, docs)
            out = generate_text(tokenizer, model, prompt, max_new_tokens=96, temperature=temperature)
            candidates = parse_candidates(out, max_items=3)

            raw_outputs.append({
                "subquestion": claim["subquestion"],
                "top_k": k,
                "output": out,
                "candidates": candidates,
            })

            chosen = None
            for cand in candidates:
                if is_unknown(cand):
                    continue
                if answer_supported_by_docs(cand, docs):
                    chosen = cand
                    break

            if chosen is not None:
                items.append(chosen)
                evidence_docs.append(docs)
                accepted = True

                if k > 1:
                    repair_count += 1

                break

            rollback_count += 1

        if not accepted:
            items.append("UNKNOWN")
            evidence_docs.append([])

    return {
        "items": items,
        "evidence_docs_per_claim": evidence_docs,
        "raw_outputs": raw_outputs,
        "rollback_count": rollback_count,
        "repair_count": repair_count,
    }


RUNNERS = {
    "standard_top1": run_standard,
    "retrieve_more_top20": run_retrieve_more,
    "posthoc_top20": run_posthoc,
    "crag_style_top20": run_crag_style,
    "riskroll_top20": run_riskroll,
}


def evaluate(task: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    claims = task["claims"]
    items = result["items"]
    docs_per_claim = result["evidence_docs_per_claim"]

    n = len(claims)

    correct = 0
    strict = 0
    supported_non_unknown = 0
    non_unknown = 0
    abstentions = 0

    for claim, item, docs in zip(claims, items, docs_per_claim):
        if is_unknown(item):
            abstentions += 1
            continue

        non_unknown += 1

        is_correct = answer_matches_gold(item, claim["gold_answers"])
        is_supported = answer_supported_by_docs(item, docs)

        correct += int(is_correct)
        supported_non_unknown += int(is_supported)
        strict += int(is_correct and is_supported)

    # For posthoc, unsafe prefix comes from initial committed answer.
    unsafe_items = result.get("initial_items", items)
    unsafe_docs = result.get("initial_evidence_docs_per_claim", docs_per_claim)

    unsupported_commits = 0
    committed_flags = []

    for item, docs in zip(unsafe_items, unsafe_docs):
        if is_unknown(item):
            continue

        supported = answer_supported_by_docs(item, docs)
        committed_flags.append(supported)

        if not supported:
            unsupported_commits += 1

    first_bad_step = 0
    for i, flag in enumerate(committed_flags, start=1):
        if not flag:
            first_bad_step = i
            break

    if first_bad_step == 0:
        unsafe_depth = 0
        downstream = 0
    else:
        unsafe_depth = len(committed_flags) - first_bad_step + 1
        downstream = unsafe_depth

    return {
        "num_claims": n,
        "claim_accuracy": correct / n if n else 0.0,
        "strict_grounded_rate": strict / n if n else 0.0,
        "support_rate": supported_non_unknown / non_unknown if non_unknown else 0.0,
        "non_unknown_predictions": non_unknown,
        "abstention_count": abstentions,
        "unsupported_commits": unsupported_commits,
        "first_bad_step": first_bad_step,
        "unsafe_prefix_depth": unsafe_depth,
        "downstream_contaminated_claims": downstream,
        "clean_task": int(unsupported_commits == 0 and unsafe_depth == 0),
    }


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", required=True)
    parser.add_argument("--n_tasks", type=int, default=5)
    parser.add_argument("--output_tag", default="qwen7b_asqa_smoke")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--trust_remote_code", action="store_true")
    parser.add_argument("--load_in_4bit", action="store_true")
    args = parser.parse_args()

    obj = json.loads(TASK_PATH.read_text(encoding="utf-8"))
    tasks = obj["tasks"][: args.n_tasks]

    tokenizer, model = load_model(
        args.model_name_or_path,
        load_in_4bit=args.load_in_4bit,
        trust_remote_code=args.trust_remote_code,
    )

    raw_records = []
    task_rows = []

    print("=" * 90)
    print("Experiment 8D: ALCE-ASQA actual LLM generation")
    print("=" * 90)
    print("Tasks:", len(tasks))
    print("Methods:", list(METHODS.keys()))
    print("")

    for ti, task in enumerate(tasks, start=1):
        print(f"\nTask {ti}/{len(tasks)}: {task['task_id']} | {task['question']}")

        for method, display in METHODS.items():
            print("  Running:", display)

            runner = RUNNERS[method]
            result = runner(tokenizer, model, task, args.temperature)
            ev = evaluate(task, result)

            row = {
                "task_id": task["task_id"],
                "method": method,
                "method_display": display,
                "question": task["question"],
                **ev,
                "rollback_count": result.get("rollback_count", 0),
                "repair_count": result.get("repair_count", 0),
                "items": result["items"],
            }

            task_rows.append(row)

            raw_records.append({
                "task": task,
                "method": method,
                "method_display": display,
                "result": result,
                "evaluation": ev,
            })

            print(
                f"    acc={ev['claim_accuracy']:.3f} | "
                f"strict={ev['strict_grounded_rate']:.3f} | "
                f"support={ev['support_rate']:.3f} | "
                f"unsupported={ev['unsupported_commits']} | "
                f"unsafe={ev['unsafe_prefix_depth']} | "
                f"abstain={ev['abstention_count']}"
            )

    summary_rows = []
    for method, display in METHODS.items():
        rows = [r for r in task_rows if r["method"] == method]
        summary_rows.append({
            "method": method,
            "method_display": display,
            "num_tasks": len(rows),
            "num_claims": sum(r["num_claims"] for r in rows),
            "claim_accuracy": mean([r["claim_accuracy"] for r in rows]),
            "strict_grounded_rate": mean([r["strict_grounded_rate"] for r in rows]),
            "support_rate": mean([r["support_rate"] for r in rows]),
            "clean_task_rate": mean([r["clean_task"] for r in rows]),
            "mean_unsupported_commits": mean([r["unsupported_commits"] for r in rows]),
            "mean_abstention_count": mean([r["abstention_count"] for r in rows]),
            "mean_unsafe_prefix_depth": mean([r["unsafe_prefix_depth"] for r in rows]),
            "mean_downstream_contaminated_claims": mean([r["downstream_contaminated_claims"] for r in rows]),
            "mean_rollback_count": mean([r["rollback_count"] for r in rows]),
            "mean_repair_count": mean([r["repair_count"] for r in rows]),
        })

    tag = args.output_tag

    summary_path = TABLE_DIR / f"experiment8d_alce_asqa_llm_generation_{tag}_summary.csv"
    task_rows_path = TABLE_DIR / f"experiment8d_alce_asqa_llm_generation_{tag}_task_rows.csv"
    raw_path = RAW_DIR / f"experiment8d_alce_asqa_llm_generation_{tag}_raw.json"
    report_path = REPORT_DIR / f"EXPERIMENT8D_ALCE_ASQA_LLM_GENERATION_{tag}.md"

    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    serializable_task_rows = []
    for r in task_rows:
        rr = dict(r)
        rr["items"] = " || ".join(map(str, rr["items"]))
        serializable_task_rows.append(rr)

    with task_rows_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(serializable_task_rows[0].keys()))
        writer.writeheader()
        writer.writerows(serializable_task_rows)

    raw_path.write_text(json.dumps({
        "args": vars(args),
        "summary": summary_rows,
        "task_rows": serializable_task_rows,
        "raw_records": raw_records,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    md = []
    md.append("# Experiment 8D: ALCE-ASQA actual LLM generation")
    md.append("")
    md.append(f"Tag: `{tag}`")
    md.append("")
    md.append("| Method | Claim Acc. | Strict Grounded | Support | Unsupported | Unsafe Depth | Abstain | Rollbacks | Repairs |")
    md.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")

    for r in summary_rows:
        md.append(
            f"| {r['method_display']} | "
            f"{r['claim_accuracy']:.3f} | "
            f"{r['strict_grounded_rate']:.3f} | "
            f"{r['support_rate']:.3f} | "
            f"{r['mean_unsupported_commits']:.3f} | "
            f"{r['mean_unsafe_prefix_depth']:.3f} | "
            f"{r['mean_abstention_count']:.3f} | "
            f"{r['mean_rollback_count']:.3f} | "
            f"{r['mean_repair_count']:.3f} |"
        )

    report_path.write_text("\n".join(md), encoding="utf-8")

    print("\n" + "=" * 90)
    print("Final summary")
    print("=" * 90)

    for r in summary_rows:
        print(
            f"{r['method_display']:<42} | "
            f"acc={r['claim_accuracy']:.3f} | "
            f"strict={r['strict_grounded_rate']:.3f} | "
            f"support={r['support_rate']:.3f} | "
            f"unsupported={r['mean_unsupported_commits']:.3f} | "
            f"unsafe={r['mean_unsafe_prefix_depth']:.3f} | "
            f"abstain={r['mean_abstention_count']:.3f} | "
            f"rollbacks={r['mean_rollback_count']:.3f}"
        )

    print("")
    print("Saved:")
    print("Summary:", summary_path)
    print("Task rows:", task_rows_path)
    print("Raw:", raw_path)
    print("Report:", report_path)


if __name__ == "__main__":
    main()

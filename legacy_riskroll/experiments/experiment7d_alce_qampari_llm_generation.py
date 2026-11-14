from pathlib import Path
import argparse
import csv
import json
import re
from statistics import mean

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


PROJECT = Path(__file__).resolve().parents[1]

TASK_PATH = PROJECT / "data" / "public" / "alce_qampari" / "alce_qampari_public_tasks.jsonl"

RESULT_TABLE_DIR = PROJECT / "results" / "tables"
RAW_DIR = PROJECT / "results" / "raw"
REPORT_DIR = PROJECT / "results" / "reports"


SYSTEM_PROMPT = """You are a careful evidence-grounded QA assistant.
Use only the provided evidence.
Do not use outside knowledge.
Return concise answer items only.
"""


def norm_text(s):
    s = str(s).lower()
    s = re.sub(r"\[[^\]]*\]", " ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def safe_mean(xs):
    return mean(xs) if xs else 0.0


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def compact_docs(docs, max_chars_per_doc=450, max_total_chars=9000):
    parts = []
    total = 0

    for d in docs:
        rank = d.get("rank", "?")
        title = d.get("title", "")
        text = d.get("text", "")
        snippet = text[:max_chars_per_doc].replace("\n", " ")
        block = f"[D{rank}] {title}: {snippet}"

        if total + len(block) > max_total_chars:
            break

        parts.append(block)
        total += len(block)

    return "\n".join(parts)


def question_tokens(question):
    toks = set(norm_text(question).split())
    stop = {
        "what", "which", "who", "whom", "whose", "was", "were", "is", "are",
        "of", "the", "a", "an", "and", "or", "by", "to", "in", "on", "for",
        "did", "does", "do", "both"
    }
    return {t for t in toks if t not in stop and len(t) > 2}


def lexical_doc_score(question, doc):
    q = question_tokens(question)
    blob = norm_text(str(doc.get("title", "")) + " " + str(doc.get("text", "")))
    d = set(blob.split())
    if not q:
        return 0
    return len(q & d)


def select_crag_style_docs(question, docs, top_n=8):
    scored = []
    for d in docs:
        scored.append((lexical_doc_score(question, d), d.get("rank", 999), d))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [x[2] for x in scored[:top_n]]


def load_model(model_name_or_path, load_in_4bit=False, trust_remote_code=True):
    print("Loading tokenizer:", model_name_or_path)
    tokenizer = AutoTokenizer.from_pretrained(
        model_name_or_path,
        trust_remote_code=trust_remote_code,
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if load_in_4bit:
        # 4-bit usually needs accelerate/device_map. Use only if accelerate is installed.
        try:
            import accelerate  # noqa: F401
        except Exception as e:
            raise RuntimeError(
                "4-bit loading needs accelerate in this environment. "
                "For now run without --load_in_4bit on L40S."
            ) from e

        from transformers import BitsAndBytesConfig

        kwargs = {
            "trust_remote_code": trust_remote_code,
            "torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32,
            "quantization_config": BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            ),
            "device_map": "auto",
        }

        print("Loading model in 4-bit:", model_name_or_path)
        model = AutoModelForCausalLM.from_pretrained(model_name_or_path, **kwargs)

    else:
        # No accelerate needed. Load normally, then move to GPU manually.
        kwargs = {
            "trust_remote_code": trust_remote_code,
            "torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32,
        }

        print("Loading model without device_map:", model_name_or_path)
        model = AutoModelForCausalLM.from_pretrained(model_name_or_path, **kwargs)

        if torch.cuda.is_available():
            print("Moving model to CUDA...")
            model = model.to("cuda")

    model.eval()

    if torch.cuda.is_available():
        print("Model device:", next(model.parameters()).device)
        print("GPU memory allocated GB:", round(torch.cuda.memory_allocated() / 1024**3, 2))

    return tokenizer, model


def generate_text(
    tokenizer,
    model,
    user_prompt,
    max_new_tokens=96,
    temperature=0.0,
):
    device = next(model.parameters()).device

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template is not None:
        input_ids = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(device)

        # Compatibility fix: newer Transformers tokenizers return BatchEncoding.
    if hasattr(input_ids, "keys") and "input_ids" in input_ids:
        encoded = input_ids
        input_ids = encoded["input_ids"]
        attention_mask = encoded.get("attention_mask")
        if attention_mask is None:
            attention_mask = torch.ones_like(input_ids)
    else:
        attention_mask = torch.ones_like(input_ids)

        with torch.no_grad():
            out = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                do_sample=temperature > 0.0,
                temperature=temperature if temperature > 0.0 else None,
                pad_token_id=tokenizer.eos_token_id,
            )

        gen_ids = out[0][input_ids.shape[-1]:]
        return tokenizer.decode(gen_ids, skip_special_tokens=True).strip()

    prompt = f"{SYSTEM_PROMPT}\n\nUser:\n{user_prompt}\n\nAssistant:\n"
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=temperature > 0.0,
            temperature=temperature if temperature > 0.0 else None,
            pad_token_id=tokenizer.eos_token_id,
        )

    gen_ids = out[0][inputs["input_ids"].shape[-1]:]
    return tokenizer.decode(gen_ids, skip_special_tokens=True).strip()


def parse_answer_items(text, max_items=5):
    raw = str(text).strip()

    raw = raw.replace("\r", "\n")
    raw = re.sub(r"\[[Dd]\d+\]", "", raw)

    lines = []
    for line in raw.split("\n"):
        line = line.strip()
        line = re.sub(r"^\s*[-*]\s*", "", line)
        line = re.sub(r"^\s*\d+[\).\:\-]\s*", "", line)
        line = line.strip()
        if line:
            lines.append(line)

    if len(lines) <= 1:
        # Fallback: split on semicolons only. Avoid comma splitting because titles can contain commas.
        pieces = re.split(r";|\|", raw)
        lines = [p.strip() for p in pieces if p.strip()]

    items = []
    seen = set()

    for line in lines:
        line = line.strip().strip(".")
        line = re.sub(r"^(answer|item)\s*:\s*", "", line, flags=re.I).strip()
        if not line:
            continue

        # Remove explanatory tails.
        line = re.split(r"\s+-\s+|\s+\(|\s+because\s+", line, maxsplit=1, flags=re.I)[0].strip()
        line = line.strip(" '\"")

        if not line:
            continue

        n = norm_text(line)
        if n in {"unknown", "not sure", "none", "n a", "na"}:
            line = "UNKNOWN"
            n = "unknown"

        if n and n not in seen:
            seen.add(n)
            items.append(line)

        if len(items) >= max_items:
            break

    while len(items) < max_items:
        items.append("UNKNOWN")

    return items[:max_items]


def parse_one_item(text):
    items = parse_answer_items(text, max_items=1)
    return items[0] if items else "UNKNOWN"


def item_supported_by_docs(item, docs):
    item_n = norm_text(item)
    if not item_n or item_n == "unknown":
        return False

    blob = " ".join(
        str(d.get("title", "")) + " " + str(d.get("text", ""))
        for d in docs
    )
    blob_n = norm_text(blob)

    return item_n in blob_n


def item_matches_alias_group(item, aliases):
    item_n = norm_text(item)
    if not item_n or item_n == "unknown":
        return False

    for a in aliases:
        a_n = norm_text(a)
        if not a_n:
            continue

        if item_n == a_n:
            return True

        # Allow mild containment for titles/entities.
        if len(a_n) >= 4 and a_n in item_n:
            return True
        if len(item_n) >= 4 and item_n in a_n:
            return True

    return False


def evaluate_items(task, items, evidence_docs_per_item):
    gold_groups = [claim["aliases"] for claim in task["claims"]]
    matched_gold = set()

    non_unknown = 0
    correct_predictions = 0
    supported_predictions = 0
    strict_grounded = 0
    unsupported_commits = 0
    abstentions = 0

    commit_supported_flags = []

    for i, item in enumerate(items):
        item_n = norm_text(item)

        if item_n == "unknown" or not item_n:
            abstentions += 1
            continue

        non_unknown += 1

        docs = evidence_docs_per_item[i]
        supported = item_supported_by_docs(item, docs)

        if supported:
            supported_predictions += 1
            commit_supported_flags.append(True)
        else:
            unsupported_commits += 1
            commit_supported_flags.append(False)

        matched_idx = None
        for gi, aliases in enumerate(gold_groups):
            if gi in matched_gold:
                continue
            if item_matches_alias_group(item, aliases):
                matched_idx = gi
                break

        if matched_idx is not None:
            matched_gold.add(matched_idx)
            correct_predictions += 1
            if supported:
                strict_grounded += 1

    precision = correct_predictions / non_unknown if non_unknown else 0.0
    recall = len(matched_gold) / len(gold_groups) if gold_groups else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall > 0 else 0.0

    support_rate = supported_predictions / non_unknown if non_unknown else 0.0
    strict_grounded_rate = strict_grounded / len(gold_groups) if gold_groups else 0.0

    first_unsafe = 0
    for j, flag in enumerate(commit_supported_flags, start=1):
        if not flag:
            first_unsafe = j
            break

    unsafe_depth = 0
    if first_unsafe != 0:
        unsafe_depth = len(commit_supported_flags) - first_unsafe

    clean_task = int(recall == 1.0 and unsupported_commits == 0)

    return {
        "answer_precision": precision,
        "answer_recall": recall,
        "answer_f1": f1,
        "support_rate": support_rate,
        "strict_grounded_rate": strict_grounded_rate,
        "unsupported_commits": unsupported_commits,
        "abstention_count": abstentions,
        "first_unsafe_commit_step": first_unsafe,
        "unsafe_prefix_depth": unsafe_depth,
        "downstream_contaminated_claims": unsafe_depth,
        "clean_task": clean_task,
        "non_unknown_predictions": non_unknown,
    }


def make_list_prompt(question, docs, n_items=5):
    context = compact_docs(docs)
    return f"""Question:
{question}

Evidence:
{context}

Task:
Return exactly {n_items} answer items that answer the question.
Use only the evidence above.
Return one answer item per line.
Do not explain.
If you cannot find enough supported items, write UNKNOWN for missing items.
"""


def make_posthoc_prompt(question, initial_items, docs, n_items=5):
    context = compact_docs(docs)
    initial = "\n".join(f"- {x}" for x in initial_items)

    return f"""Question:
{question}

Initial answer items:
{initial}

Evidence:
{context}

Task:
Revise the initial answer using only the evidence.
Return exactly {n_items} supported answer items.
Return one answer item per line.
Remove unsupported items.
If you cannot find enough supported items, write UNKNOWN for missing items.
Do not explain.
"""


def make_riskroll_item_prompt(question, committed_items, docs):
    context = compact_docs(docs)
    committed_clean = [x for x in committed_items if norm_text(x) != "unknown"]
    committed = ", ".join(committed_clean) if committed_clean else "None"

    return f"""Question:
{question}

Already committed answer items:
{committed}

Evidence:
{context}

Task:
List up to 5 answer items that answer the question and are directly supported by the evidence.
Do not repeat already committed items.
Use only the evidence.
Return one item per line.
Do not explain.
If no supported item is available, return UNKNOWN.
"""

def run_standard(tokenizer, model, task, temperature):
    docs = task["claims"][0]["candidate_docs"][:1]
    prompt = make_list_prompt(task["question"], docs, n_items=5)
    output = generate_text(tokenizer, model, prompt, max_new_tokens=96, temperature=temperature)
    items = parse_answer_items(output, max_items=5)
    evidence_docs_per_item = [docs for _ in items]

    return {
        "items": items,
        "raw_outputs": [output],
        "evidence_docs_per_item": evidence_docs_per_item,
        "rollback_count": 0,
        "repair_count": 0,
    }


def run_retrieve_more(tokenizer, model, task, temperature):
    docs = task["claims"][0]["candidate_docs"][:20]
    prompt = make_list_prompt(task["question"], docs, n_items=5)
    output = generate_text(tokenizer, model, prompt, max_new_tokens=128, temperature=temperature)
    items = parse_answer_items(output, max_items=5)
    evidence_docs_per_item = [docs for _ in items]

    return {
        "items": items,
        "raw_outputs": [output],
        "evidence_docs_per_item": evidence_docs_per_item,
        "rollback_count": 0,
        "repair_count": 0,
    }


def run_crag_style(tokenizer, model, task, temperature):
    all_docs = task["claims"][0]["candidate_docs"][:20]
    docs = select_crag_style_docs(task["question"], all_docs, top_n=8)

    prompt = make_list_prompt(task["question"], docs, n_items=5)
    output = generate_text(tokenizer, model, prompt, max_new_tokens=128, temperature=temperature)
    items = parse_answer_items(output, max_items=5)
    evidence_docs_per_item = [docs for _ in items]

    return {
        "items": items,
        "raw_outputs": [output],
        "evidence_docs_per_item": evidence_docs_per_item,
        "rollback_count": 0,
        "repair_count": 0,
    }


def run_posthoc(tokenizer, model, task, temperature):
    top1_docs = task["claims"][0]["candidate_docs"][:1]
    top20_docs = task["claims"][0]["candidate_docs"][:20]

    initial_prompt = make_list_prompt(task["question"], top1_docs, n_items=5)
    initial_output = generate_text(tokenizer, model, initial_prompt, max_new_tokens=96, temperature=temperature)
    initial_items = parse_answer_items(initial_output, max_items=5)

    revise_prompt = make_posthoc_prompt(task["question"], initial_items, top20_docs, n_items=5)
    revised_output = generate_text(tokenizer, model, revise_prompt, max_new_tokens=128, temperature=temperature)
    revised_items = parse_answer_items(revised_output, max_items=5)

    evidence_docs_per_item = [top20_docs for _ in revised_items]

    return {
        "items": revised_items,
        "raw_outputs": [initial_output, revised_output],
        "initial_items": initial_items,
        "evidence_docs_per_item": evidence_docs_per_item,
        "rollback_count": 0,
        "repair_count": sum(1 for a, b in zip(initial_items, revised_items) if norm_text(a) != norm_text(b)),
    }


def run_riskroll(tokenizer, model, task, temperature):
    """
    RiskRoll actual LLM version:

    1. Generate candidate answer items from evidence windows.
    2. Verify each candidate against the same evidence window.
    3. Commit only supported, non-duplicate items.
    4. Reject unsupported candidates as rollback events.
    5. If fewer than 5 supported items are found, abstain for remaining slots.

    This avoids the over-strict one-item prompt that caused Qwen to return UNKNOWN.
    """
    all_docs = task["claims"][0]["candidate_docs"][:20]

    committed = []
    evidence_docs_per_item = []
    raw_outputs = []

    rollback_count = 0
    repair_count = 0
    abstention_count = 0

    windows = [1, 5, 10, 20]
    seen_candidate_norms = set()

    for k in windows:
        if len(committed) >= 5:
            break

        docs = all_docs[:k]

        prompt = make_list_prompt(
            task["question"],
            docs,
            n_items=8,
        )

        output = generate_text(
            tokenizer,
            model,
            prompt,
            max_new_tokens=160,
            temperature=temperature,
        )

        raw_outputs.append({
            "top_k": k,
            "output": output,
        })

        candidates = parse_answer_items(output, max_items=8)

        for item in candidates:
            if len(committed) >= 5:
                break

            item_n = norm_text(item)

            if not item_n or item_n == "unknown":
                continue

            if item_n in seen_candidate_norms:
                continue

            seen_candidate_norms.add(item_n)

            duplicate_commit = any(norm_text(item) == norm_text(x) for x in committed)
            supported = item_supported_by_docs(item, docs)

            if duplicate_commit:
                rollback_count += 1
                continue

            if supported:
                committed.append(item)
                evidence_docs_per_item.append(docs)

                if k > 1:
                    repair_count += 1
            else:
                rollback_count += 1

    while len(committed) < 5:
        committed.append("UNKNOWN")
        evidence_docs_per_item.append([])
        abstention_count += 1

    return {
        "items": committed[:5],
        "raw_outputs": raw_outputs,
        "evidence_docs_per_item": evidence_docs_per_item[:5],
        "rollback_count": rollback_count,
        "repair_count": repair_count,
        "riskroll_internal_abstentions": abstention_count,
    }

METHODS = {
    "standard_top1": ("Standard RAG top-1", run_standard),
    "retrieve_more_top20": ("Retrieve-more RAG top-20", run_retrieve_more),
    "posthoc_top20": ("Post-hoc correction top-20", run_posthoc),
    "crag_style_top20": ("CRAG-style correction top-20", run_crag_style),
    "riskroll_top20": ("RiskRoll verify-before-commit top-20", run_riskroll),
}

def summarize(task_rows):
    by_method = {}

    for row in task_rows:
        by_method.setdefault(row["method"], []).append(row)

    summaries = []

    for method, rows in by_method.items():
        display = rows[0]["method_display"]

        summaries.append({
            "method": method,
            "method_display": display,
            "num_tasks": len(rows),
            "answer_precision": safe_mean([r["answer_precision"] for r in rows]),
            "answer_recall": safe_mean([r["answer_recall"] for r in rows]),
            "answer_f1": safe_mean([r["answer_f1"] for r in rows]),
            "support_rate": safe_mean([r["support_rate"] for r in rows]),
            "strict_grounded_rate": safe_mean([r["strict_grounded_rate"] for r in rows]),
            "clean_task_rate": safe_mean([r["clean_task"] for r in rows]),
            "mean_unsupported_commits": safe_mean([r["unsupported_commits"] for r in rows]),
            "mean_abstention_count": safe_mean([r["abstention_count"] for r in rows]),
            "mean_unsafe_prefix_depth": safe_mean([r["unsafe_prefix_depth"] for r in rows]),
            "mean_downstream_contaminated_claims": safe_mean([r["downstream_contaminated_claims"] for r in rows]),
            "mean_rollback_count": safe_mean([r["rollback_count"] for r in rows]),
            "mean_repair_count": safe_mean([r["repair_count"] for r in rows]),
        })

    return summaries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", required=True)
    parser.add_argument("--n_tasks", type=int, default=30)
    parser.add_argument("--output_tag", type=str, default="llm")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--load_in_4bit", action="store_true")
    parser.add_argument("--trust_remote_code", action="store_true")
    args = parser.parse_args()

    RESULT_TABLE_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    tag = re.sub(r"[^a-zA-Z0-9_\-]+", "_", args.output_tag)

    out_summary_csv = RESULT_TABLE_DIR / f"experiment7d_alce_qampari_llm_generation_{tag}_summary.csv"
    out_task_csv = RESULT_TABLE_DIR / f"experiment7d_alce_qampari_llm_generation_{tag}_task_rows.csv"
    out_raw_json = RAW_DIR / f"experiment7d_alce_qampari_llm_generation_{tag}_raw.json"
    out_report = REPORT_DIR / f"EXPERIMENT7D_ALCE_QAMPARI_LLM_GENERATION_{tag}.md"

    tasks = load_jsonl(TASK_PATH)[:args.n_tasks]

    tokenizer, model = load_model(
        args.model_name_or_path,
        load_in_4bit=args.load_in_4bit,
        trust_remote_code=args.trust_remote_code,
    )

    method_order = [
        "standard_top1",
        "retrieve_more_top20",
        "posthoc_top20",
        "crag_style_top20",
        "riskroll_top20",
    ]

    task_rows = []
    raw_records = []

    print("=" * 90)
    print("Experiment 7D: ALCE-QAMPARI actual LLM generation")
    print("=" * 90)
    print("Model:", args.model_name_or_path)
    print("Tasks:", len(tasks))
    print("Methods:", method_order)
    print("")

    for ti, task in enumerate(tasks, start=1):
        print(f"\nTask {ti}/{len(tasks)}: {task['task_id']} | {task['question']}")

        for method in method_order:
            display, runner = METHODS[method]
            print(f"  Running: {display}")

            result = runner(tokenizer, model, task, temperature=args.temperature)
            items = result["items"]

            eval_result = evaluate_items(task, items, result["evidence_docs_per_item"])

            row = {
                "method": method,
                "method_display": display,
                "task_id": task["task_id"],
                "source_id": task["source_id"],
                "question": task["question"],
                "gold_answer_list": " | ".join(task["gold_answer_list"]),
                "predicted_items": " | ".join(items),
                "answer_precision": eval_result["answer_precision"],
                "answer_recall": eval_result["answer_recall"],
                "answer_f1": eval_result["answer_f1"],
                "support_rate": eval_result["support_rate"],
                "strict_grounded_rate": eval_result["strict_grounded_rate"],
                "clean_task": eval_result["clean_task"],
                "unsupported_commits": eval_result["unsupported_commits"],
                "abstention_count": eval_result["abstention_count"],
                "first_unsafe_commit_step": eval_result["first_unsafe_commit_step"],
                "unsafe_prefix_depth": eval_result["unsafe_prefix_depth"],
                "downstream_contaminated_claims": eval_result["downstream_contaminated_claims"],
                "rollback_count": result.get("rollback_count", 0),
                "repair_count": result.get("repair_count", 0),
            }

            task_rows.append(row)

            raw_records.append({
                "method": method,
                "method_display": display,
                "task": task,
                "result": {
                    "items": items,
                    "raw_outputs": result.get("raw_outputs", []),
                    "initial_items": result.get("initial_items", None),
                    "rollback_count": result.get("rollback_count", 0),
                    "repair_count": result.get("repair_count", 0),
                },
                "evaluation": eval_result,
            })

            print(
                f"    pred={items} | "
                f"F1={eval_result['answer_f1']:.3f} | "
                f"strict_grounded={eval_result['strict_grounded_rate']:.3f} | "
                f"unsupported={eval_result['unsupported_commits']} | "
                f"abstain={eval_result['abstention_count']}"
            )

        # Save partial after every task.
        write_csv(out_task_csv, task_rows)
        write_json(out_raw_json, {
            "model_name_or_path": args.model_name_or_path,
            "n_tasks": len(tasks),
            "raw_records": raw_records,
        })

    summaries = summarize(task_rows)
    write_csv(out_summary_csv, summaries)

    report = []
    report.append(f"# Experiment 7D: ALCE-QAMPARI Actual LLM Generation ({tag})")
    report.append("")
    report.append(f"- Model: `{args.model_name_or_path}`")
    report.append(f"- Tasks: {len(tasks)}")
    report.append(f"- Temperature: {args.temperature}")
    report.append("")
    report.append("## Results")
    report.append("")

    for s in summaries:
        report.append(f"### {s['method_display']}")
        report.append(f"- answer_precision: {s['answer_precision']:.3f}")
        report.append(f"- answer_recall: {s['answer_recall']:.3f}")
        report.append(f"- answer_f1: {s['answer_f1']:.3f}")
        report.append(f"- support_rate: {s['support_rate']:.3f}")
        report.append(f"- strict_grounded_rate: {s['strict_grounded_rate']:.3f}")
        report.append(f"- clean_task_rate: {s['clean_task_rate']:.3f}")
        report.append(f"- mean_unsupported_commits: {s['mean_unsupported_commits']:.3f}")
        report.append(f"- mean_abstention_count: {s['mean_abstention_count']:.3f}")
        report.append(f"- mean_unsafe_prefix_depth: {s['mean_unsafe_prefix_depth']:.3f}")
        report.append(f"- mean_downstream_contaminated_claims: {s['mean_downstream_contaminated_claims']:.3f}")
        report.append(f"- mean_rollback_count: {s['mean_rollback_count']:.3f}")
        report.append(f"- mean_repair_count: {s['mean_repair_count']:.3f}")
        report.append("")

    out_report.write_text("\n".join(report) + "\n", encoding="utf-8")

    print("\n" + "=" * 90)
    print("Final summary")
    print("=" * 90)
    for s in summaries:
        print(
            f"{s['method_display']:<42} | "
            f"F1={s['answer_f1']:.3f} | "
            f"strict_grounded={s['strict_grounded_rate']:.3f} | "
            f"unsupported={s['mean_unsupported_commits']:.3f} | "
            f"unsafe={s['mean_unsafe_prefix_depth']:.3f} | "
            f"rollbacks={s['mean_rollback_count']:.3f} | "
            f"abstain={s['mean_abstention_count']:.3f}"
        )

    print("")
    print("Saved:")
    print("Summary:", out_summary_csv)
    print("Task rows:", out_task_csv)
    print("Raw:", out_raw_json)
    print("Report:", out_report)


if __name__ == "__main__":
    main()

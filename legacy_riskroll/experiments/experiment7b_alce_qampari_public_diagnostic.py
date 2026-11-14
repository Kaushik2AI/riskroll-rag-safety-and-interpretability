from pathlib import Path
import json
import csv
from statistics import mean


PROJECT = Path(__file__).resolve().parents[1]

TASK_PATH = PROJECT / "data" / "public" / "alce_qampari" / "alce_qampari_public_tasks.jsonl"

OUT_DIR = PROJECT / "results" / "tables"
RAW_DIR = PROJECT / "results" / "raw"
REPORT_DIR = PROJECT / "results" / "reports"

OUT_SUMMARY_CSV = OUT_DIR / "experiment7b_alce_qampari_public_diagnostic_summary.csv"
OUT_TASK_CSV = OUT_DIR / "experiment7b_alce_qampari_public_diagnostic_task_rows.csv"
OUT_RAW_JSON = RAW_DIR / "experiment7b_alce_qampari_public_diagnostic_full.json"
OUT_REPORT = REPORT_DIR / "EXPERIMENT7B_ALCE_QAMPARI_PUBLIC_DIAGNOSTIC_REPORT.md"


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


def method_claim_success(first_support_rank, method):
    """
    Public grounding proxy.

    first_support_rank:
      rank of first retrieved document that contains a gold answer alias.
      None means no supporting doc found in top-100 during adapter construction.

    method:
      - standard_top1: only accepts rank-1 document.
      - retrieve_more_top5: succeeds if support appears in top-5 context.
      - retrieve_more_top20: succeeds if support appears in top-20 context.
      - riskroll_top20: scans candidates sequentially and commits only if support is found.
    """
    if first_support_rank is None:
        return False

    if method == "standard_top1":
        return first_support_rank == 1

    if method == "retrieve_more_top5":
        return first_support_rank <= 5

    if method == "retrieve_more_top20":
        return first_support_rank <= 20

    if method == "riskroll_top20":
        return first_support_rank <= 20

    raise ValueError(f"Unknown method: {method}")


def riskroll_rollbacks(first_support_rank, top_k=20):
    """
    If support is at rank r, RiskRoll rejects r-1 unsupported candidates
    and commits the first supported one.
    If no support in top-k, it rejects top-k and abstains.
    """
    if first_support_rank is None:
        return top_k

    if first_support_rank <= top_k:
        return max(0, first_support_rank - 1)

    return top_k


def first_bad_step(successes):
    for i, ok in enumerate(successes, start=1):
        if not ok:
            return i
    return 0


def unsafe_prefix_depth(successes, method):
    """
    For non-rollback methods, once an unsupported claim is committed,
    later claims are considered exposed to unsafe-prefix contamination.
    For RiskRoll, failed claims are not committed, so unsafe depth is zero.
    """
    if method == "riskroll_top20":
        return 0

    bad = first_bad_step(successes)
    if bad == 0:
        return 0

    return len(successes) - bad


def downstream_contamination(successes, method):
    if method == "riskroll_top20":
        return 0

    bad = first_bad_step(successes)
    if bad == 0:
        return 0

    return len(successes) - bad


def run_method(tasks, method):
    task_rows = []

    claim_grounded = []
    clean_tasks = []
    unsafe_depths = []
    contamination = []
    abstentions = []
    rollback_counts = []
    first_bad_steps = []

    for task in tasks:
        successes = []
        claim_rollbacks = []
        claim_abstentions = []

        for claim in task["claims"]:
            first_rank = claim.get("first_support_rank")
            ok = method_claim_success(first_rank, method)

            successes.append(ok)
            claim_grounded.append(1.0 if ok else 0.0)

            if method == "riskroll_top20":
                rb = riskroll_rollbacks(first_rank, top_k=20)
                claim_rollbacks.append(rb)
                claim_abstentions.append(0 if ok else 1)
            else:
                claim_rollbacks.append(0)
                claim_abstentions.append(0)

        task_clean = all(successes)
        task_unsafe = unsafe_prefix_depth(successes, method)
        task_contam = downstream_contamination(successes, method)
        task_first_bad = first_bad_step(successes)
        task_abstain = sum(claim_abstentions)
        task_rollbacks = sum(claim_rollbacks)

        clean_tasks.append(1.0 if task_clean else 0.0)
        unsafe_depths.append(task_unsafe)
        contamination.append(task_contam)
        first_bad_steps.append(task_first_bad)
        abstentions.append(task_abstain)
        rollback_counts.append(task_rollbacks)

        task_rows.append({
            "method": method,
            "task_id": task["task_id"],
            "source_id": task["source_id"],
            "num_claims": len(task["claims"]),
            "grounded_claim_rate": safe_mean([1.0 if x else 0.0 for x in successes]),
            "clean_task": int(task_clean),
            "first_bad_step": task_first_bad,
            "unsafe_prefix_depth": task_unsafe,
            "downstream_contaminated_claims": task_contam,
            "rollback_count": task_rollbacks,
            "abstention_count": task_abstain,
        })

    summary = {
        "method": method,
        "num_tasks": len(tasks),
        "num_claims": sum(len(t["claims"]) for t in tasks),
        "grounded_claim_rate": safe_mean(claim_grounded),
        "clean_task_rate": safe_mean(clean_tasks),
        "mean_first_bad_step": safe_mean(first_bad_steps),
        "mean_unsafe_prefix_depth": safe_mean(unsafe_depths),
        "mean_downstream_contaminated_claims": safe_mean(contamination),
        "mean_rollback_count": safe_mean(rollback_counts),
        "mean_abstention_count": safe_mean(abstentions),
    }

    return summary, task_rows


def display_name(method):
    names = {
        "standard_top1": "Standard RAG top-1 commit",
        "retrieve_more_top5": "Retrieve-more RAG top-5 context",
        "retrieve_more_top20": "Retrieve-more RAG top-20 context",
        "riskroll_top20": "RiskRoll top-20 verify-before-commit",
    }
    return names[method]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    tasks = load_jsonl(TASK_PATH)

    methods = [
        "standard_top1",
        "retrieve_more_top5",
        "retrieve_more_top20",
        "riskroll_top20",
    ]

    summaries = []
    all_task_rows = []

    for method in methods:
        summary, task_rows = run_method(tasks, method)
        summary["method_display"] = display_name(method)
        summaries.append(summary)
        all_task_rows.extend(task_rows)

    write_csv(OUT_SUMMARY_CSV, summaries)
    write_csv(OUT_TASK_CSV, all_task_rows)
    write_json(OUT_RAW_JSON, {
        "task_path": str(TASK_PATH),
        "methods": methods,
        "summaries": summaries,
        "task_rows": all_task_rows,
    })

    report = []
    report.append("# Experiment 7B: ALCE-QAMPARI Public Grounding Diagnostic")
    report.append("")
    report.append("## Purpose")
    report.append("")
    report.append(
        "Evaluate whether the public ALCE-QAMPARI retrieval set creates a meaningful "
        "claim-level grounding setting for RiskRoll-RAG."
    )
    report.append("")
    report.append("## Important note")
    report.append("")
    report.append(
        "This is an evidence-selection / grounding proxy, not the final LLM generation experiment. "
        "It uses gold answer aliases to determine whether a retrieved document supports a claim."
    )
    report.append("")
    report.append("## Results")
    report.append("")
    for s in summaries:
        report.append(f"### {s['method_display']}")
        report.append(f"- grounded_claim_rate: {s['grounded_claim_rate']:.3f}")
        report.append(f"- clean_task_rate: {s['clean_task_rate']:.3f}")
        report.append(f"- mean_unsafe_prefix_depth: {s['mean_unsafe_prefix_depth']:.3f}")
        report.append(f"- mean_downstream_contaminated_claims: {s['mean_downstream_contaminated_claims']:.3f}")
        report.append(f"- mean_rollback_count: {s['mean_rollback_count']:.3f}")
        report.append(f"- mean_abstention_count: {s['mean_abstention_count']:.3f}")
        report.append("")

    report.append("## Interpretation")
    report.append("")
    report.append(
        "Top-1 retrieval is not sufficient for many ALCE-QAMPARI claims. "
        "Correct supporting evidence often appears deeper in the retrieval list. "
        "RiskRoll uses this setting as a verify-before-commit process: unsupported "
        "candidate evidence is rejected before entering the trusted semantic prefix."
    )

    OUT_REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")

    print("=" * 90)
    print("Experiment 7B: ALCE-QAMPARI public grounding diagnostic")
    print("=" * 90)
    print(f"Tasks: {len(tasks)}")
    print(f"Claims: {sum(len(t['claims']) for t in tasks)}")
    print("")

    for s in summaries:
        print(
            f"{s['method_display']:<40} | "
            f"grounded={s['grounded_claim_rate']:.3f} | "
            f"clean_task={s['clean_task_rate']:.3f} | "
            f"unsafe={s['mean_unsafe_prefix_depth']:.3f} | "
            f"contam={s['mean_downstream_contaminated_claims']:.3f} | "
            f"rollbacks={s['mean_rollback_count']:.3f} | "
            f"abstain={s['mean_abstention_count']:.3f}"
        )

    print("")
    print("Saved:")
    print("Summary:", OUT_SUMMARY_CSV)
    print("Task rows:", OUT_TASK_CSV)
    print("Raw:", OUT_RAW_JSON)
    print("Report:", OUT_REPORT)


if __name__ == "__main__":
    main()

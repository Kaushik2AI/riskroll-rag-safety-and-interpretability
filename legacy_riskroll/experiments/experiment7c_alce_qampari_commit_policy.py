from pathlib import Path
import json
import csv
from statistics import mean


PROJECT = Path(__file__).resolve().parents[1]

TASK_PATH = PROJECT / "data" / "public" / "alce_qampari" / "alce_qampari_public_tasks.jsonl"

OUT_DIR = PROJECT / "results" / "tables"
RAW_DIR = PROJECT / "results" / "raw"
REPORT_DIR = PROJECT / "results" / "reports"

OUT_SUMMARY_CSV = OUT_DIR / "experiment7c_alce_qampari_commit_policy_summary.csv"
OUT_TASK_CSV = OUT_DIR / "experiment7c_alce_qampari_commit_policy_task_rows.csv"
OUT_RAW_JSON = RAW_DIR / "experiment7c_alce_qampari_commit_policy_full.json"
OUT_REPORT = REPORT_DIR / "EXPERIMENT7C_ALCE_QAMPARI_COMMIT_POLICY_REPORT.md"


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


def support_in_topk(first_support_rank, k):
    return first_support_rank is not None and first_support_rank <= k


def first_bad_step(successes):
    for i, ok in enumerate(successes, start=1):
        if not ok:
            return i
    return 0


def unsafe_depth_from_commits(committed_supported):
    """
    committed_supported is a list for committed claims:
      True  = committed supported claim
      False = committed unsupported claim

    If first unsupported committed claim appears at step b,
    later committed claims are exposed to unsafe-prefix contamination.
    """
    bad = first_bad_step(committed_supported)
    if bad == 0:
        return 0
    return len(committed_supported) - bad


def run_standard_top1(task):
    """
    Standard RAG commits from top-1 evidence.
    If top-1 does not support a claim, it still commits an unsupported item.
    """
    successes = []
    committed_supported = []
    rollbacks = 0
    abstentions = 0
    repairs = 0

    for claim in task["claims"]:
        ok = support_in_topk(claim.get("first_support_rank"), 1)
        successes.append(ok)
        committed_supported.append(ok)

    return successes, committed_supported, rollbacks, abstentions, repairs


def run_retrieve_more_top20(task):
    """
    Retrieve-more RAG has top-20 evidence available.
    If support appears in top-20, it can generate the correct item.
    If not, it still commits an unsupported item.
    """
    successes = []
    committed_supported = []
    rollbacks = 0
    abstentions = 0
    repairs = 0

    for claim in task["claims"]:
        ok = support_in_topk(claim.get("first_support_rank"), 20)
        successes.append(ok)
        committed_supported.append(ok)

    return successes, committed_supported, rollbacks, abstentions, repairs


def run_posthoc_top20(task):
    """
    Post-hoc correction:
    1. First commits using top-1.
    2. Later revises unsupported claims if support exists in top-20.

    Final grounded rate can match top-20 retrieval coverage, but commit-time
    contamination already happened during the initial generation.
    """
    initial_supported = []
    final_successes = []
    committed_supported_for_trace = []
    repairs = 0
    rollbacks = 0
    abstentions = 0

    for claim in task["claims"]:
        top1_ok = support_in_topk(claim.get("first_support_rank"), 1)
        top20_ok = support_in_topk(claim.get("first_support_rank"), 20)

        initial_supported.append(top1_ok)
        committed_supported_for_trace.append(top1_ok)

        if top1_ok:
            final_successes.append(True)
        elif top20_ok:
            final_successes.append(True)
            repairs += 1
        else:
            final_successes.append(False)

    return final_successes, committed_supported_for_trace, rollbacks, abstentions, repairs


def run_crag_style_top20(task):
    """
    CRAG-style correction:
    Evidence is checked before answering and top-20 correction can find support.
    But if no support exists in top-20, it still outputs an unsupported item.
    It improves evidence selection but does not use rollback/abstain semantics.
    """
    successes = []
    committed_supported = []
    rollbacks = 0
    abstentions = 0
    repairs = 0

    for claim in task["claims"]:
        ok = support_in_topk(claim.get("first_support_rank"), 20)
        successes.append(ok)
        committed_supported.append(ok)

    return successes, committed_supported, rollbacks, abstentions, repairs


def run_riskroll_top20(task):
    """
    RiskRoll:
    Scans top-20 evidence candidates.
    If support is found, commits the supported claim.
    If no support is found, abstains instead of committing unsupported content.
    """
    successes = []
    committed_supported = []
    rollbacks = 0
    abstentions = 0
    repairs = 0

    for claim in task["claims"]:
        r = claim.get("first_support_rank")

        if support_in_topk(r, 20):
            successes.append(True)
            committed_supported.append(True)
            rollbacks += max(0, r - 1)
            repairs += 1 if r > 1 else 0
        else:
            successes.append(False)
            abstentions += 1
            rollbacks += 20
            # No unsupported claim is committed.

    return successes, committed_supported, rollbacks, abstentions, repairs


METHODS = {
    "standard_top1": {
        "display": "Standard RAG top-1",
        "runner": run_standard_top1,
    },
    "retrieve_more_top20": {
        "display": "Retrieve-more RAG top-20",
        "runner": run_retrieve_more_top20,
    },
    "posthoc_top20": {
        "display": "Post-hoc correction top-20",
        "runner": run_posthoc_top20,
    },
    "crag_style_top20": {
        "display": "CRAG-style correction top-20",
        "runner": run_crag_style_top20,
    },
    "riskroll_top20": {
        "display": "RiskRoll top-20 verify-before-commit",
        "runner": run_riskroll_top20,
    },
}


def run_method(tasks, method_name):
    runner = METHODS[method_name]["runner"]
    display = METHODS[method_name]["display"]

    task_rows = []

    all_success = []
    clean_tasks = []
    unsafe_depths = []
    contaminations = []
    rollbacks = []
    abstentions = []
    repairs = []
    first_bad_steps = []
    unsupported_commits = []

    for task in tasks:
        successes, committed_supported, rb, abstain, repair = runner(task)

        task_success_rate = safe_mean([1.0 if x else 0.0 for x in successes])
        task_clean = all(successes)

        task_unsafe = unsafe_depth_from_commits(committed_supported)
        task_contam = task_unsafe

        bad_step = first_bad_step(committed_supported)
        num_unsupported_commits = sum(1 for x in committed_supported if not x)

        all_success.extend([1.0 if x else 0.0 for x in successes])
        clean_tasks.append(1.0 if task_clean else 0.0)
        unsafe_depths.append(task_unsafe)
        contaminations.append(task_contam)
        rollbacks.append(rb)
        abstentions.append(abstain)
        repairs.append(repair)
        first_bad_steps.append(bad_step)
        unsupported_commits.append(num_unsupported_commits)

        task_rows.append({
            "method": method_name,
            "method_display": display,
            "task_id": task["task_id"],
            "source_id": task["source_id"],
            "num_claims": len(task["claims"]),
            "final_grounded_claim_rate": task_success_rate,
            "clean_task": int(task_clean),
            "first_unsafe_commit_step": bad_step,
            "unsafe_prefix_depth": task_unsafe,
            "downstream_contaminated_claims": task_contam,
            "unsupported_commits": num_unsupported_commits,
            "rollback_count": rb,
            "abstention_count": abstain,
            "repair_count": repair,
        })

    summary = {
        "method": method_name,
        "method_display": display,
        "num_tasks": len(tasks),
        "num_claims": sum(len(t["claims"]) for t in tasks),
        "final_grounded_claim_rate": safe_mean(all_success),
        "clean_task_rate": safe_mean(clean_tasks),
        "mean_first_unsafe_commit_step": safe_mean(first_bad_steps),
        "mean_unsafe_prefix_depth": safe_mean(unsafe_depths),
        "mean_downstream_contaminated_claims": safe_mean(contaminations),
        "mean_unsupported_commits": safe_mean(unsupported_commits),
        "mean_rollback_count": safe_mean(rollbacks),
        "mean_abstention_count": safe_mean(abstentions),
        "mean_repair_count": safe_mean(repairs),
    }

    return summary, task_rows


def main():
    tasks = load_jsonl(TASK_PATH)

    method_order = [
        "standard_top1",
        "retrieve_more_top20",
        "posthoc_top20",
        "crag_style_top20",
        "riskroll_top20",
    ]

    summaries = []
    all_task_rows = []

    for method in method_order:
        summary, task_rows = run_method(tasks, method)
        summaries.append(summary)
        all_task_rows.extend(task_rows)

    write_csv(OUT_SUMMARY_CSV, summaries)
    write_csv(OUT_TASK_CSV, all_task_rows)
    write_json(OUT_RAW_JSON, {
        "task_path": str(TASK_PATH),
        "method_order": method_order,
        "summaries": summaries,
        "task_rows": all_task_rows,
    })

    report = []
    report.append("# Experiment 7C: ALCE-QAMPARI Public Commit-Policy Comparison")
    report.append("")
    report.append("## Purpose")
    report.append("")
    report.append(
        "Compare different public-data commit policies on ALCE-QAMPARI: "
        "standard top-1 commit, retrieve-more context, post-hoc correction, "
        "CRAG-style correction, and RiskRoll verify-before-commit."
    )
    report.append("")
    report.append("## Important note")
    report.append("")
    report.append(
        "This experiment uses gold answer aliases to evaluate whether evidence supports "
        "a claim. It is a public commit-policy diagnostic, not the final neural generation experiment."
    )
    report.append("")
    report.append("## Results")
    report.append("")

    for s in summaries:
        report.append(f"### {s['method_display']}")
        report.append(f"- final_grounded_claim_rate: {s['final_grounded_claim_rate']:.3f}")
        report.append(f"- clean_task_rate: {s['clean_task_rate']:.3f}")
        report.append(f"- mean_unsafe_prefix_depth: {s['mean_unsafe_prefix_depth']:.3f}")
        report.append(f"- mean_downstream_contaminated_claims: {s['mean_downstream_contaminated_claims']:.3f}")
        report.append(f"- mean_unsupported_commits: {s['mean_unsupported_commits']:.3f}")
        report.append(f"- mean_rollback_count: {s['mean_rollback_count']:.3f}")
        report.append(f"- mean_abstention_count: {s['mean_abstention_count']:.3f}")
        report.append(f"- mean_repair_count: {s['mean_repair_count']:.3f}")
        report.append("")

    report.append("## Interpretation")
    report.append("")
    report.append(
        "Retrieve-more, post-hoc correction, and CRAG-style correction can improve final "
        "grounding when supporting evidence appears in top-20. However, they do not model "
        "the answer as a trusted semantic prefix. RiskRoll has the same top-20 evidence "
        "ceiling but avoids unsupported commits by abstaining when no supporting evidence "
        "is found."
    )

    OUT_REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")

    print("=" * 90)
    print("Experiment 7C: ALCE-QAMPARI public commit-policy comparison")
    print("=" * 90)
    print(f"Tasks: {len(tasks)}")
    print(f"Claims: {sum(len(t['claims']) for t in tasks)}")
    print("")

    for s in summaries:
        print(
            f"{s['method_display']:<42} | "
            f"final_grounded={s['final_grounded_claim_rate']:.3f} | "
            f"clean={s['clean_task_rate']:.3f} | "
            f"unsafe={s['mean_unsafe_prefix_depth']:.3f} | "
            f"unsupported_commits={s['mean_unsupported_commits']:.3f} | "
            f"rollbacks={s['mean_rollback_count']:.3f} | "
            f"abstain={s['mean_abstention_count']:.3f} | "
            f"repairs={s['mean_repair_count']:.3f}"
        )

    print("")
    print("Saved:")
    print("Summary:", OUT_SUMMARY_CSV)
    print("Task rows:", OUT_TASK_CSV)
    print("Raw:", OUT_RAW_JSON)
    print("Report:", OUT_REPORT)


if __name__ == "__main__":
    main()

from __future__ import annotations

import csv
import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]

TASK_PATH = PROJECT / "results" / "raw" / "experiment8_alce_asqa_public_tasks.json"

RAW_DIR = PROJECT / "results" / "raw"
TABLE_DIR = PROJECT / "results" / "tables"
REPORT_DIR = PROJECT / "results" / "reports"

RAW_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


METHODS = [
    ("standard_top1", "Standard RAG top-1"),
    ("retrieve_more_top5", "Retrieve-more RAG top-5"),
    ("retrieve_more_top20", "Retrieve-more RAG top-20"),
    ("posthoc_top20", "Post-hoc correction top-20"),
    ("crag_style_top20", "CRAG-style correction top-20"),
    ("riskroll_top20", "RiskRoll top-20 verify-before-commit"),
]


def support_in_top(claim, k: int) -> bool:
    r = claim.get("first_support_rank")
    return r is not None and r <= k


def eval_task(task, method: str):
    claims = task["claims"]
    n = len(claims)

    grounded = 0
    unsupported_commits = 0
    abstentions = 0
    rollbacks = 0
    repairs = 0

    committed_grounded_flags = []

    for claim in claims:
        top1 = support_in_top(claim, 1)
        top5 = support_in_top(claim, 5)
        top20 = support_in_top(claim, 20)

        if method == "standard_top1":
            if top1:
                grounded += 1
                committed_grounded_flags.append(True)
            else:
                unsupported_commits += 1
                committed_grounded_flags.append(False)

        elif method == "retrieve_more_top5":
            if top5:
                grounded += 1
                committed_grounded_flags.append(True)
            else:
                unsupported_commits += 1
                committed_grounded_flags.append(False)

        elif method == "retrieve_more_top20":
            if top20:
                grounded += 1
                committed_grounded_flags.append(True)
            else:
                unsupported_commits += 1
                committed_grounded_flags.append(False)

        elif method == "posthoc_top20":
            # Post-hoc can repair final grounding if support exists in top-20,
            # but unsafe top-1 content may already have entered the prefix.
            if top1:
                grounded += 1
                committed_grounded_flags.append(True)
            else:
                unsupported_commits += 1
                committed_grounded_flags.append(False)

            if top20 and not top1:
                repairs += 1

        elif method == "crag_style_top20":
            # Approximate CRAG-style correction: tries to select better evidence before generation.
            # If support appears in top-20, final claim can be grounded; otherwise it still commits.
            if top20:
                grounded += 1
                committed_grounded_flags.append(True)
            else:
                unsupported_commits += 1
                committed_grounded_flags.append(False)

        elif method == "riskroll_top20":
            # RiskRoll verifies before commit. If support is not in top-20, abstain instead of unsafe commit.
            if top20:
                grounded += 1
                committed_grounded_flags.append(True)

                if not top1:
                    rollbacks += max(1, min(claim["first_support_rank"] - 1, 20))
                    repairs += 1
            else:
                abstentions += 1
                rollbacks += 20
                # Abstentions are not unsafe commits, so do not append False to committed prefix.

        else:
            raise ValueError(method)

    first_bad_step = 0
    for i, flag in enumerate(committed_grounded_flags, start=1):
        if not flag:
            first_bad_step = i
            break

    if first_bad_step == 0:
        unsafe_depth = 0
        downstream = 0
    else:
        unsafe_depth = len(committed_grounded_flags) - first_bad_step + 1
        downstream = unsafe_depth

    return {
        "num_claims": n,
        "grounded_claims": grounded,
        "grounded_claim_rate": grounded / n if n else 0.0,
        "unsupported_commits": unsupported_commits,
        "abstentions": abstentions,
        "first_bad_step": first_bad_step,
        "unsafe_prefix_depth": unsafe_depth,
        "downstream_contaminated_claims": downstream,
        "clean_task": int(unsupported_commits == 0 and unsafe_depth == 0),
        "rollbacks": rollbacks,
        "repairs": repairs,
    }


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def main():
    obj = json.loads(TASK_PATH.read_text(encoding="utf-8"))
    tasks = obj["tasks"]

    task_rows = []
    summary_rows = []

    for method, display in METHODS:
        rows = []

        for task in tasks:
            ev = eval_task(task, method)
            row = {
                "task_id": task["task_id"],
                "method": method,
                "method_display": display,
                "question": task["question"],
                **ev,
            }
            rows.append(row)
            task_rows.append(row)

        summary = {
            "method": method,
            "method_display": display,
            "num_tasks": len(rows),
            "num_claims": sum(r["num_claims"] for r in rows),
            "grounded_claim_rate": mean([r["grounded_claim_rate"] for r in rows]),
            "clean_task_rate": mean([r["clean_task"] for r in rows]),
            "mean_unsupported_commits": mean([r["unsupported_commits"] for r in rows]),
            "mean_abstentions": mean([r["abstentions"] for r in rows]),
            "mean_unsafe_prefix_depth": mean([r["unsafe_prefix_depth"] for r in rows]),
            "mean_downstream_contaminated_claims": mean([r["downstream_contaminated_claims"] for r in rows]),
            "mean_rollbacks": mean([r["rollbacks"] for r in rows]),
            "mean_repairs": mean([r["repairs"] for r in rows]),
        }
        summary_rows.append(summary)

    summary_path = TABLE_DIR / "experiment8b_alce_asqa_public_diagnostic_summary.csv"
    task_rows_path = TABLE_DIR / "experiment8b_alce_asqa_public_diagnostic_task_rows.csv"
    raw_path = RAW_DIR / "experiment8b_alce_asqa_public_diagnostic_full.json"
    report_path = REPORT_DIR / "EXPERIMENT8B_ALCE_ASQA_PUBLIC_DIAGNOSTIC_REPORT.md"

    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    with task_rows_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(task_rows[0].keys()))
        writer.writeheader()
        writer.writerows(task_rows)

    raw_path.write_text(
        json.dumps(
            {
                "task_path": str(TASK_PATH),
                "methods": METHODS,
                "summary": summary_rows,
                "task_rows": task_rows,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    md = []
    md.append("# Experiment 8B: ALCE-ASQA Public Diagnostic")
    md.append("")
    md.append("This diagnostic compares commit policies on claim-level ASQA tasks.")
    md.append("RiskRoll commits only claims with support in top-20 evidence and abstains otherwise.")
    md.append("")
    md.append("## Summary")
    md.append("")
    md.append("| Method | Grounded | Clean Task | Unsupported | Unsafe Depth | Abstain | Rollbacks | Repairs |")
    md.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")

    for r in summary_rows:
        md.append(
            f"| {r['method_display']} | "
            f"{r['grounded_claim_rate']:.3f} | "
            f"{r['clean_task_rate']:.3f} | "
            f"{r['mean_unsupported_commits']:.3f} | "
            f"{r['mean_unsafe_prefix_depth']:.3f} | "
            f"{r['mean_abstentions']:.3f} | "
            f"{r['mean_rollbacks']:.3f} | "
            f"{r['mean_repairs']:.3f} |"
        )

    report_path.write_text("\n".join(md), encoding="utf-8")

    print("=" * 90)
    print("Experiment 8B: ALCE-ASQA public diagnostic")
    print("=" * 90)

    for r in summary_rows:
        print(
            f"{r['method_display']:<42} | "
            f"grounded={r['grounded_claim_rate']:.3f} | "
            f"clean={r['clean_task_rate']:.3f} | "
            f"unsupported={r['mean_unsupported_commits']:.3f} | "
            f"unsafe={r['mean_unsafe_prefix_depth']:.3f} | "
            f"abstain={r['mean_abstentions']:.3f} | "
            f"rollbacks={r['mean_rollbacks']:.3f}"
        )

    print("")
    print("Saved:")
    print("Summary:", summary_path)
    print("Task rows:", task_rows_path)
    print("Raw:", raw_path)
    print("Report:", report_path)


if __name__ == "__main__":
    main()

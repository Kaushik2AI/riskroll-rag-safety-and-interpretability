from pathlib import Path
import sys
import csv
import json
from statistics import mean

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from data_builders.text_longform import build_text_longform_tasks
from verification import ControlledIdentityVerifier
from riskroll import RiskRollController

from baselines.standard_rag import StandardRAGBaseline
from baselines.retrieve_more import RetrieveMoreBaseline
from baselines.posthoc_correction import PostHocCorrectionBaseline
from baselines.crag_style import CRAGStyleBaseline


OUT_RAW = PROJECT / "results" / "raw"
OUT_TABLES = PROJECT / "results" / "tables"
OUT_REPORTS = PROJECT / "results" / "reports"

for p in [OUT_RAW, OUT_TABLES, OUT_REPORTS]:
    p.mkdir(parents=True, exist_ok=True)


N_GROUPS = 20
REPORTS_PER_GROUP = 3
CLAIMS_PER_TASK = 5
TOP_K = 3
SEED = 7


def safe_get(summary, key, default=0):
    return summary.get(key, default)


def run_method_per_task(name, method, tasks):
    rows = []

    for task_id, examples in tasks.items():
        if name == "RiskRoll":
            result = method.run_sequence(examples)
        else:
            result = method.run_batch(examples)

        summary = result["summary"]

        rows.append({
            "task_id": task_id,
            "method": name,
            "n_claims": len(examples),

            "claim_accuracy": safe_get(summary, "claim_accuracy"),
            "evidence_accuracy": safe_get(summary, "evidence_accuracy"),
            "grounded_claim_rate": safe_get(summary, "grounded_claim_rate"),
            "wrong_evidence_count": safe_get(summary, "wrong_evidence_count"),
            "first_bad_step": safe_get(summary, "first_bad_step", None),
            "unsafe_prefix_depth": safe_get(summary, "unsafe_prefix_depth"),
            "downstream_contaminated_claims": safe_get(summary, "downstream_contaminated_claims"),

            "rollback_count": safe_get(summary, "rollback_count"),
            "repair_count": safe_get(summary, "repair_count"),
            "abstention_count": safe_get(summary, "abstention_count"),
            "verifier_false_accepts": safe_get(summary, "verifier_false_accepts"),
            "verifier_false_rejects": safe_get(summary, "verifier_false_rejects"),

            "records": result.get("records", []),
            "events": result.get("events", []),
            "prefix": result.get("prefix", []),
        })

    return rows


def aggregate(rows):
    metric_keys = [
        "claim_accuracy",
        "evidence_accuracy",
        "grounded_claim_rate",
        "wrong_evidence_count",
        "unsafe_prefix_depth",
        "downstream_contaminated_claims",
        "rollback_count",
        "repair_count",
        "abstention_count",
        "verifier_false_accepts",
        "verifier_false_rejects",
    ]

    out = {
        "method": rows[0]["method"],
        "n_tasks": len(rows),
        "claims_per_task": rows[0]["n_claims"],
        "total_claims": len(rows) * rows[0]["n_claims"],
    }

    for key in metric_keys:
        out[f"mean_{key}"] = mean(r[key] for r in rows)

    clean_tasks = sum(r["wrong_evidence_count"] == 0 for r in rows)
    out["clean_task_rate"] = clean_tasks / len(rows)

    no_bad_step = sum(r["first_bad_step"] is None for r in rows)
    out["no_first_bad_step_rate"] = no_bad_step / len(rows)

    bad_positions = [
        r["first_bad_step"]
        for r in rows
        if r["first_bad_step"] is not None
    ]

    out["mean_first_bad_step_when_present"] = (
        mean(bad_positions) if bad_positions else None
    )

    return out


def write_csv(path, rows):
    if not rows:
        return

    fieldnames = list(rows[0].keys())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def make_light_rows(rows):
    light_rows = []

    for row in rows:
        r = dict(row)
        r.pop("records", None)
        r.pop("events", None)
        r.pop("prefix", None)
        light_rows.append(r)

    return light_rows


def main():
    print("=" * 90)
    print("Experiment 5: Text-only long-form contamination benchmark")
    print("=" * 90)

    tasks = build_text_longform_tasks(
        n_groups=N_GROUPS,
        reports_per_group=REPORTS_PER_GROUP,
        seed=SEED,
    )

    print("Tasks:", len(tasks))
    print("Claims per task:", CLAIMS_PER_TASK)
    print("Total claims:", len(tasks) * CLAIMS_PER_TASK)
    print("Top-k:", TOP_K)

    verifier = ControlledIdentityVerifier(
        required_keys=[
            "report_id",
            "city",
            "domain",
            "claim_name",
            "metric",
            "year",
            "modality",
        ]
    )

    methods = {
        "Standard RAG": StandardRAGBaseline(),
        "Retrieve-more RAG": RetrieveMoreBaseline(top_k=TOP_K),
        "Post-hoc correction": PostHocCorrectionBaseline(top_k=TOP_K),
        "CRAG-style correction": CRAGStyleBaseline(top_k=TOP_K),
        "RiskRoll": RiskRollController(
            verifier=verifier,
            top_k=TOP_K,
        ),
    }

    all_rows = []
    summary_rows = []

    for name, method in methods.items():
        rows = run_method_per_task(name, method, tasks)
        all_rows.extend(rows)
        summary_rows.append(aggregate(rows))

    raw_json = OUT_RAW / "experiment5_text_longform_contamination_full.json"
    task_csv = OUT_TABLES / "experiment5_text_longform_contamination_task_rows.csv"
    summary_csv = OUT_TABLES / "experiment5_text_longform_contamination_summary.csv"
    report_path = OUT_REPORTS / "EXPERIMENT5_TEXT_LONGFORM_CONTAMINATION_REPORT.md"

    raw_json.write_text(
        json.dumps(all_rows, indent=2),
        encoding="utf-8",
    )

    write_csv(task_csv, make_light_rows(all_rows))
    write_csv(summary_csv, summary_rows)

    print("\nSummary:")
    for row in summary_rows:
        print(
            f"{row['method']:<24} "
            f"claim_acc={row['mean_claim_accuracy']:.3f} | "
            f"evidence_acc={row['mean_evidence_accuracy']:.3f} | "
            f"grounded={row['mean_grounded_claim_rate']:.3f} | "
            f"wrong_ev={row['mean_wrong_evidence_count']:.3f} | "
            f"unsafe_depth={row['mean_unsafe_prefix_depth']:.3f} | "
            f"clean_task={row['clean_task_rate']:.3f} | "
            f"rollbacks={row['mean_rollback_count']:.3f}"
        )

    lines = []
    lines.append("# Experiment 5: Text-only Long-form Contamination Benchmark")
    lines.append("")
    lines.append("## Goal")
    lines.append("")
    lines.append(
        "Evaluate RiskRoll-RAG on text-only long-form RAG tasks where each answer "
        "contains multiple claims and wrong-but-plausible near-miss evidence appears before gold evidence."
    )
    lines.append("")
    lines.append("## Setup")
    lines.append("")
    lines.append(f"- Tasks: {len(tasks)}")
    lines.append(f"- Claims per task: {CLAIMS_PER_TASK}")
    lines.append(f"- Total claims: {len(tasks) * CLAIMS_PER_TASK}")
    lines.append(f"- Top-k evidence candidates: {TOP_K}")
    lines.append("")
    lines.append("Each task has five claims about a hidden target report. The first retrieved passage is a near-miss from a different report, while the gold passage is rank 2.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Method | Claim Acc | Evidence Acc | Grounded Rate | Wrong Evidence | Unsafe Depth | Clean Task Rate | Rollbacks |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")

    for row in summary_rows:
        lines.append(
            f"| {row['method']} | "
            f"{row['mean_claim_accuracy']:.3f} | "
            f"{row['mean_evidence_accuracy']:.3f} | "
            f"{row['mean_grounded_claim_rate']:.3f} | "
            f"{row['mean_wrong_evidence_count']:.3f} | "
            f"{row['mean_unsafe_prefix_depth']:.3f} | "
            f"{row['clean_task_rate']:.3f} | "
            f"{row['mean_rollback_count']:.3f} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Standard and lexical correction baselines are expected to accept near-miss passages because the wrong and gold passages are lexically similar. "
        "RiskRoll uses controlled report-identity verification to rollback unsafe claims before they enter the trusted prefix."
    )
    lines.append("")
    lines.append("## RiskRoll-specific claim")
    lines.append("")
    lines.append(
        "The main result is not only higher answer accuracy. The key result is reduced unsafe-prefix depth and downstream contamination."
    )

    report_path.write_text("\n".join(lines), encoding="utf-8")

    print("\nSaved:")
    print("Full raw:", raw_json)
    print("Task rows:", task_csv)
    print("Summary:", summary_csv)
    print("Report:", report_path)


if __name__ == "__main__":
    main()

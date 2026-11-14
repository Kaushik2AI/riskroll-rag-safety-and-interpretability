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
from verification import ControlledIdentityVerifier, NoisyVerifierWrapper
from riskroll import RiskRollController


OUT_RAW = PROJECT / "results" / "raw"
OUT_TABLES = PROJECT / "results" / "tables"
OUT_REPORTS = PROJECT / "results" / "reports"

for p in [OUT_RAW, OUT_TABLES, OUT_REPORTS]:
    p.mkdir(parents=True, exist_ok=True)


N_GROUPS = 20
REPORTS_PER_GROUP = 3
CLAIMS_PER_TASK = 5
TOP_K = 3
BASE_SEED = 7

FALSE_ACCEPT_RATES = [0.00, 0.02, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50]
FALSE_REJECT_RATES = [0.00, 0.05, 0.10, 0.20, 0.30]


def avg(rows, key):
    return mean(r[key] for r in rows)


def run_setting(tasks, false_accept_rate, false_reject_rate, seed):
    base_verifier = ControlledIdentityVerifier(
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

    noisy_verifier = NoisyVerifierWrapper(
        base_verifier=base_verifier,
        false_accept_rate=false_accept_rate,
        false_reject_rate=false_reject_rate,
        seed=seed,
    )

    controller = RiskRollController(
        verifier=noisy_verifier,
        top_k=TOP_K,
    )

    task_rows = []

    for task_id, examples in tasks.items():
        result = controller.run_sequence(examples)
        summary = result["summary"]

        task_rows.append({
            "task_id": task_id,
            "false_accept_rate": false_accept_rate,
            "false_reject_rate": false_reject_rate,

            "claim_accuracy": summary["claim_accuracy"],
            "evidence_accuracy": summary["evidence_accuracy"],
            "grounded_claim_rate": summary["grounded_claim_rate"],
            "wrong_evidence_count": summary["wrong_evidence_count"],
            "first_bad_step": summary["first_bad_step"],
            "unsafe_prefix_depth": summary["unsafe_prefix_depth"],
            "downstream_contaminated_claims": summary["downstream_contaminated_claims"],

            "rollback_count": summary["rollback_count"],
            "repair_count": summary["repair_count"],
            "abstention_count": summary["abstention_count"],
            "verifier_false_accepts": summary["verifier_false_accepts"],
            "verifier_false_rejects": summary["verifier_false_rejects"],

            "records": result["records"],
            "events": result["events"],
            "prefix": result["prefix"],
        })

    summary_row = {
        "false_accept_rate": false_accept_rate,
        "false_reject_rate": false_reject_rate,
        "n_tasks": len(task_rows),
        "claims_per_task": CLAIMS_PER_TASK,
        "total_claims": len(task_rows) * CLAIMS_PER_TASK,

        "mean_claim_accuracy": avg(task_rows, "claim_accuracy"),
        "mean_evidence_accuracy": avg(task_rows, "evidence_accuracy"),
        "mean_grounded_claim_rate": avg(task_rows, "grounded_claim_rate"),
        "mean_wrong_evidence_count": avg(task_rows, "wrong_evidence_count"),
        "mean_unsafe_prefix_depth": avg(task_rows, "unsafe_prefix_depth"),
        "mean_downstream_contaminated_claims": avg(task_rows, "downstream_contaminated_claims"),
        "mean_rollback_count": avg(task_rows, "rollback_count"),
        "mean_repair_count": avg(task_rows, "repair_count"),
        "mean_abstention_count": avg(task_rows, "abstention_count"),
        "mean_verifier_false_accepts": avg(task_rows, "verifier_false_accepts"),
        "mean_verifier_false_rejects": avg(task_rows, "verifier_false_rejects"),

        "clean_task_rate": sum(r["wrong_evidence_count"] == 0 for r in task_rows) / len(task_rows),
        "no_first_bad_step_rate": sum(r["first_bad_step"] is None for r in task_rows) / len(task_rows),
    }

    return summary_row, task_rows


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
    out = []

    for row in rows:
        r = dict(row)
        r.pop("records", None)
        r.pop("events", None)
        r.pop("prefix", None)
        out.append(r)

    return out


def main():
    print("=" * 90)
    print("Experiment 6: Text-only noisy-verifier sweep")
    print("=" * 90)

    tasks = build_text_longform_tasks(
        n_groups=N_GROUPS,
        reports_per_group=REPORTS_PER_GROUP,
        seed=BASE_SEED,
    )

    print("Tasks:", len(tasks))
    print("Claims per task:", CLAIMS_PER_TASK)
    print("Total claims:", len(tasks) * CLAIMS_PER_TASK)
    print("Top-k:", TOP_K)

    all_summary_rows = []
    all_task_rows_full = []
    all_task_rows_light = []

    run_id = 0

    # Sweep false accepts while false rejects fixed at 0.
    for fa in FALSE_ACCEPT_RATES:
        fr = 0.0
        run_id += 1

        summary_row, task_rows = run_setting(
            tasks=tasks,
            false_accept_rate=fa,
            false_reject_rate=fr,
            seed=1000 + run_id,
        )

        summary_row["sweep_type"] = "false_accept_sweep"
        all_summary_rows.append(summary_row)

        for row in task_rows:
            row["sweep_type"] = "false_accept_sweep"
            all_task_rows_full.append(row)

        all_task_rows_light.extend(make_light_rows(task_rows))

        print(
            f"FA={fa:.2f}, FR={fr:.2f} | "
            f"grounded={summary_row['mean_grounded_claim_rate']:.3f} | "
            f"evidence={summary_row['mean_evidence_accuracy']:.3f} | "
            f"contam={summary_row['mean_downstream_contaminated_claims']:.3f} | "
            f"unsafe={summary_row['mean_unsafe_prefix_depth']:.3f} | "
            f"abstain={summary_row['mean_abstention_count']:.3f} | "
            f"clean_task={summary_row['clean_task_rate']:.3f}"
        )

    # Sweep false rejects while false accepts fixed at 0.
    for fr in FALSE_REJECT_RATES:
        fa = 0.0
        run_id += 1

        summary_row, task_rows = run_setting(
            tasks=tasks,
            false_accept_rate=fa,
            false_reject_rate=fr,
            seed=2000 + run_id,
        )

        summary_row["sweep_type"] = "false_reject_sweep"
        all_summary_rows.append(summary_row)

        for row in task_rows:
            row["sweep_type"] = "false_reject_sweep"
            all_task_rows_full.append(row)

        all_task_rows_light.extend(make_light_rows(task_rows))

        print(
            f"FA={fa:.2f}, FR={fr:.2f} | "
            f"grounded={summary_row['mean_grounded_claim_rate']:.3f} | "
            f"evidence={summary_row['mean_evidence_accuracy']:.3f} | "
            f"contam={summary_row['mean_downstream_contaminated_claims']:.3f} | "
            f"unsafe={summary_row['mean_unsafe_prefix_depth']:.3f} | "
            f"abstain={summary_row['mean_abstention_count']:.3f} | "
            f"clean_task={summary_row['clean_task_rate']:.3f}"
        )

    summary_csv = OUT_TABLES / "experiment6_text_noisy_verifier_sweep_summary.csv"
    task_csv = OUT_TABLES / "experiment6_text_noisy_verifier_sweep_task_rows.csv"
    raw_json = OUT_RAW / "experiment6_text_noisy_verifier_sweep_full.json"
    report_path = OUT_REPORTS / "EXPERIMENT6_TEXT_NOISY_VERIFIER_SWEEP_REPORT.md"

    write_csv(summary_csv, all_summary_rows)
    write_csv(task_csv, all_task_rows_light)

    raw_json.write_text(
        json.dumps(all_task_rows_full, indent=2),
        encoding="utf-8",
    )

    lines = []
    lines.append("# Experiment 6: Text-only Noisy-Verifier Sweep")
    lines.append("")
    lines.append("## Goal")
    lines.append("")
    lines.append(
        "Measure how RiskRoll-RAG behaves when the verifier makes controlled false-accept and false-reject errors."
    )
    lines.append("")
    lines.append("## Key hypothesis")
    lines.append("")
    lines.append(
        "False accepts are more dangerous than false rejects. A false accept commits wrong evidence into the trusted prefix, while a false reject mostly causes additional rollback or abstention."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Sweep | FA | FR | Grounded | Evidence Acc | Contamination | Unsafe Depth | Abstention | Clean Task |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")

    for row in all_summary_rows:
        lines.append(
            f"| {row['sweep_type']} | "
            f"{row['false_accept_rate']:.2f} | "
            f"{row['false_reject_rate']:.2f} | "
            f"{row['mean_grounded_claim_rate']:.3f} | "
            f"{row['mean_evidence_accuracy']:.3f} | "
            f"{row['mean_downstream_contaminated_claims']:.3f} | "
            f"{row['mean_unsafe_prefix_depth']:.3f} | "
            f"{row['mean_abstention_count']:.3f} | "
            f"{row['clean_task_rate']:.3f} |"
        )

    report_path.write_text("\n".join(lines), encoding="utf-8")

    print("\nSaved:")
    print("Summary:", summary_csv)
    print("Task rows:", task_csv)
    print("Full raw:", raw_json)
    print("Report:", report_path)


if __name__ == "__main__":
    main()

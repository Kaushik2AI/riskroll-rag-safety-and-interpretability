from pathlib import Path
import sys
import csv
import json
from statistics import mean

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskroll import RiskRollController
from verification import ControlledIdentityVerifier, NoisyVerifierWrapper
from data_builders.report_identity import build_report_identity_tasks


OUT_RAW = PROJECT / "results" / "raw"
OUT_TABLES = PROJECT / "results" / "tables"
OUT_REPORTS = PROJECT / "results" / "reports"

for p in [OUT_RAW, OUT_TABLES, OUT_REPORTS]:
    p.mkdir(parents=True, exist_ok=True)


TOP_K = 3
N_GROUPS = 10
REPORTS_PER_GROUP = 3
BASE_SEED = 42

FALSE_ACCEPT_RATES = [0.00, 0.02, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50]
FALSE_REJECT_RATES = [0.00, 0.05, 0.10, 0.20]


def flatten_task_rows(tasks):
    return list(tasks.items())


def avg(rows, key):
    return mean(r[key] for r in rows)


def run_riskroll_for_setting(tasks, false_accept_rate, false_reject_rate, seed):
    base_verifier = ControlledIdentityVerifier(
        required_keys=[
            "report_id",
            "city",
            "domain",
            "modality",
            "metric",
            "year",
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

    for task_id, examples in flatten_task_rows(tasks):
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
            "unsafe_prefix_depth": summary["unsafe_prefix_depth"],
            "downstream_contaminated_claims": summary["downstream_contaminated_claims"],
            "rollback_count": summary["rollback_count"],
            "repair_count": summary["repair_count"],
            "abstention_count": summary["abstention_count"],
            "verifier_false_accepts": summary["verifier_false_accepts"],
            "verifier_false_rejects": summary["verifier_false_rejects"],
            "records": result["records"],
            "events": result["events"],
        })

    summary_row = {
        "false_accept_rate": false_accept_rate,
        "false_reject_rate": false_reject_rate,
        "n_tasks": len(task_rows),
        "claims_per_task": 3,
        "total_claims": len(task_rows) * 3,

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


def main():
    print("=" * 80)
    print("Experiment 4: Detector-quality sweep")
    print("=" * 80)

    tasks = build_report_identity_tasks(
        n_groups=N_GROUPS,
        reports_per_group=REPORTS_PER_GROUP,
        seed=BASE_SEED,
    )

    print("Tasks:", len(tasks))
    print("Total claims:", len(tasks) * 3)

    all_summary_rows = []
    all_task_rows_light = []
    all_task_rows_full = []

    run_id = 0

    # Sweep false accepts with false rejects fixed at 0.
    for fa in FALSE_ACCEPT_RATES:
        fr = 0.0
        run_id += 1

        summary_row, task_rows = run_riskroll_for_setting(
            tasks=tasks,
            false_accept_rate=fa,
            false_reject_rate=fr,
            seed=1000 + run_id,
        )

        summary_row["sweep_type"] = "false_accept_sweep"
        all_summary_rows.append(summary_row)

        for row in task_rows:
            light = dict(row)
            light.pop("records", None)
            light.pop("events", None)
            light["sweep_type"] = "false_accept_sweep"
            all_task_rows_light.append(light)

            full = dict(row)
            full["sweep_type"] = "false_accept_sweep"
            all_task_rows_full.append(full)

        print(
            f"FA={fa:.2f}, FR={fr:.2f} | "
            f"grounded={summary_row['mean_grounded_claim_rate']:.3f} | "
            f"evidence={summary_row['mean_evidence_accuracy']:.3f} | "
            f"contam={summary_row['mean_downstream_contaminated_claims']:.3f} | "
            f"unsafe={summary_row['mean_unsafe_prefix_depth']:.3f} | "
            f"abstain={summary_row['mean_abstention_count']:.3f}"
        )

    # Sweep false rejects with false accepts fixed at 0.
    for fr in FALSE_REJECT_RATES:
        fa = 0.0
        run_id += 1

        summary_row, task_rows = run_riskroll_for_setting(
            tasks=tasks,
            false_accept_rate=fa,
            false_reject_rate=fr,
            seed=2000 + run_id,
        )

        summary_row["sweep_type"] = "false_reject_sweep"
        all_summary_rows.append(summary_row)

        for row in task_rows:
            light = dict(row)
            light.pop("records", None)
            light.pop("events", None)
            light["sweep_type"] = "false_reject_sweep"
            all_task_rows_light.append(light)

            full = dict(row)
            full["sweep_type"] = "false_reject_sweep"
            all_task_rows_full.append(full)

        print(
            f"FA={fa:.2f}, FR={fr:.2f} | "
            f"grounded={summary_row['mean_grounded_claim_rate']:.3f} | "
            f"evidence={summary_row['mean_evidence_accuracy']:.3f} | "
            f"contam={summary_row['mean_downstream_contaminated_claims']:.3f} | "
            f"unsafe={summary_row['mean_unsafe_prefix_depth']:.3f} | "
            f"abstain={summary_row['mean_abstention_count']:.3f}"
        )

    summary_csv = OUT_TABLES / "experiment4_detector_quality_sweep_summary.csv"
    task_csv = OUT_TABLES / "experiment4_detector_quality_sweep_task_rows.csv"
    raw_json = OUT_RAW / "experiment4_detector_quality_sweep_full.json"
    report_path = OUT_REPORTS / "EXPERIMENT4_DETECTOR_QUALITY_SWEEP_REPORT.md"

    write_csv(summary_csv, all_summary_rows)
    write_csv(task_csv, all_task_rows_light)

    raw_json.write_text(
        json.dumps(all_task_rows_full, indent=2),
        encoding="utf-8",
    )

    lines = []
    lines.append("# Experiment 4: Detector-Quality Sweep")
    lines.append("")
    lines.append("## Goal")
    lines.append("")
    lines.append(
        "Measure how RiskRoll depends on verifier quality. "
        "False accepts allow wrong evidence to enter the trusted prefix, while false rejects cause unnecessary rollbacks or abstentions."
    )
    lines.append("")
    lines.append("## Key interpretation")
    lines.append("")
    lines.append(
        "If the verifier false-accepts wrong evidence, rollback does not trigger. "
        "Therefore grounding accuracy drops and downstream contamination increases."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Sweep | FA | FR | Claim Acc | Evidence Acc | Grounded | Contamination | Unsafe Depth | Abstention |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")

    for row in all_summary_rows:
        lines.append(
            f"| {row['sweep_type']} | "
            f"{row['false_accept_rate']:.2f} | "
            f"{row['false_reject_rate']:.2f} | "
            f"{row['mean_claim_accuracy']:.3f} | "
            f"{row['mean_evidence_accuracy']:.3f} | "
            f"{row['mean_grounded_claim_rate']:.3f} | "
            f"{row['mean_downstream_contaminated_claims']:.3f} | "
            f"{row['mean_unsafe_prefix_depth']:.3f} | "
            f"{row['mean_abstention_count']:.3f} |"
        )

    report_path.write_text("\n".join(lines), encoding="utf-8")

    print("\nSaved:")
    print("Summary:", summary_csv)
    print("Task rows:", task_csv)
    print("Full raw:", raw_json)
    print("Report:", report_path)


if __name__ == "__main__":
    main()

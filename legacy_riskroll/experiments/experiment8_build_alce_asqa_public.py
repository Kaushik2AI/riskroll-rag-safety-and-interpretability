from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from src.data_builders.alce_asqa_adapter import build_asqa_tasks


def main():
    input_path = PROJECT / "external" / "ALCE" / "data" / "asqa_eval_gtr_top100.json"

    out = build_asqa_tasks(
        input_path=input_path,
        max_records=100,
        docs_top_k=20,
        max_claims_per_task=5,
        min_claims_per_task=2,
        require_support_in_top100=True,
    )

    tasks = out["tasks"]
    stats = out["stats"]

    raw_dir = PROJECT / "results" / "raw"
    table_dir = PROJECT / "results" / "tables"
    report_dir = PROJECT / "results" / "reports"

    raw_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    raw_path = raw_dir / "experiment8_alce_asqa_public_tasks.json"
    stats_path = table_dir / "experiment8_alce_asqa_public_adapter_stats.csv"
    claim_rows_path = table_dir / "experiment8_alce_asqa_public_claim_rows.csv"
    report_path = report_dir / "EXPERIMENT8_ALCE_ASQA_PUBLIC_ADAPTER_REPORT.md"

    raw_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    with stats_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(stats.keys()))
        writer.writeheader()
        writer.writerow(stats)

    claim_rows = []
    for task in tasks:
        for claim in task["claims"]:
            claim_rows.append({
                "task_id": task["task_id"],
                "source_index": task["source_index"],
                "question": task["question"],
                "claim_id": claim["claim_id"],
                "subquestion": claim["subquestion"],
                "gold_answers": " || ".join(claim["gold_answers"]),
                "first_support_rank": claim["first_support_rank"],
                "support_in_top1": int(claim["first_support_rank"] is not None and claim["first_support_rank"] <= 1),
                "support_in_top5": int(claim["first_support_rank"] is not None and claim["first_support_rank"] <= 5),
                "support_in_top20": int(claim["first_support_rank"] is not None and claim["first_support_rank"] <= 20),
            })

    with claim_rows_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = list(claim_rows[0].keys()) if claim_rows else [
            "task_id", "source_index", "question", "claim_id", "subquestion",
            "gold_answers", "first_support_rank", "support_in_top1",
            "support_in_top5", "support_in_top20"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(claim_rows)

    md = []
    md.append("# Experiment 8: ALCE-ASQA Public Adapter")
    md.append("")
    md.append("ASQA examples are converted into claim-level tasks using qa_pairs.")
    md.append("Each qa_pair becomes a claim/subquestion with short-answer aliases.")
    md.append("")
    md.append("## Stats")
    md.append("")
    for k, v in stats.items():
        md.append(f"- **{k}**: {v}")

    if tasks:
        md.append("")
        md.append("## First task example")
        t = tasks[0]
        md.append(f"**Question:** {t['question']}")
        md.append(f"**Gold long answer:** {t['gold_long_answer'][:1000]}")
        md.append("")
        for c in t["claims"]:
            md.append(f"- **Subquestion:** {c['subquestion']}")
            md.append(f"  - Gold aliases: {c['gold_answers']}")
            md.append(f"  - First support rank: {c['first_support_rank']}")

    report_path.write_text("\n".join(md), encoding="utf-8")

    print("=" * 90)
    print("Experiment 8: ALCE-ASQA adapter")
    print("=" * 90)
    for k, v in stats.items():
        print(f"{k}: {v}")

    print("")
    print("Saved:")
    print("Raw tasks:", raw_path)
    print("Stats:", stats_path)
    print("Claim rows:", claim_rows_path)
    print("Report:", report_path)

    print("")
    print("First task preview:")
    if tasks:
        t = tasks[0]
        print("task_id:", t["task_id"])
        print("question:", t["question"])
        print("num_claims:", t["num_claims"])
        for c in t["claims"]:
            print(" -", c["subquestion"], "| gold:", c["gold_answers"], "| first_support_rank:", c["first_support_rank"])


if __name__ == "__main__":
    main()

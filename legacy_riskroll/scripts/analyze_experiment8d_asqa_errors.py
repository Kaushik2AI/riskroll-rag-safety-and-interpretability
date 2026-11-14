from pathlib import Path
import json
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]

TAG = "qwen7b_asqa_73_v1"
RAW_PATH = PROJECT / "results" / "raw" / f"experiment8d_alce_asqa_llm_generation_{TAG}_raw.json"

OUT_DIR = PROJECT / "paper_assets" / "analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

METHOD_A = "retrieve_more_top20"
METHOD_B = "riskroll_top20"


def safe_get(d, key, default=0):
    return d.get(key, default) if isinstance(d, dict) else default


def main():
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    records = raw["raw_records"]

    by_task = {}

    for rec in records:
        task = rec["task"]
        task_id = task.get("task_id") or task.get("sample_id")
        by_task.setdefault(task_id, {})[rec["method"]] = rec

    rows = []

    for task_id, methods in by_task.items():
        if METHOD_A not in methods or METHOD_B not in methods:
            continue

        a = methods[METHOD_A]
        b = methods[METHOD_B]

        ae = a["evaluation"]
        be = b["evaluation"]

        task = b["task"]

        row = {
            "task_id": task_id,
            "question": task.get("question", ""),
            "num_claims": len(task.get("claims", [])),
            "gold_claim_answers": [
                c.get("gold_answers", []) for c in task.get("claims", [])
            ],
            "retrieve_items": a["result"].get("items", []),
            "riskroll_items": b["result"].get("items", []),

            "retrieve_claim_accuracy": safe_get(ae, "claim_accuracy"),
            "riskroll_claim_accuracy": safe_get(be, "claim_accuracy"),

            "retrieve_strict_grounded": safe_get(ae, "strict_grounded_rate"),
            "riskroll_strict_grounded": safe_get(be, "strict_grounded_rate"),

            "retrieve_support_rate": safe_get(ae, "support_rate"),
            "riskroll_support_rate": safe_get(be, "support_rate"),

            "retrieve_unsupported": safe_get(ae, "unsupported_commits"),
            "riskroll_unsupported": safe_get(be, "unsupported_commits"),

            "retrieve_unsafe_depth": safe_get(ae, "unsafe_prefix_depth"),
            "riskroll_unsafe_depth": safe_get(be, "unsafe_prefix_depth"),

            "retrieve_abstain": safe_get(ae, "abstention_count"),
            "riskroll_abstain": safe_get(be, "abstention_count"),

            "riskroll_rollbacks": b["result"].get("rollback_count", 0),
            "riskroll_repairs": b["result"].get("repair_count", 0),
        }

        if row["riskroll_claim_accuracy"] > row["retrieve_claim_accuracy"]:
            row["comparison"] = "riskroll_better_accuracy"
        elif row["riskroll_claim_accuracy"] < row["retrieve_claim_accuracy"]:
            row["comparison"] = "riskroll_lower_accuracy"
        else:
            row["comparison"] = "same_accuracy"

        row["retrieve_unsafe"] = int(
            row["retrieve_unsupported"] > 0 or row["retrieve_unsafe_depth"] > 0
        )

        row["riskroll_safe"] = int(
            row["riskroll_unsupported"] == 0 and row["riskroll_unsafe_depth"] == 0
        )

        row["riskroll_better_support"] = int(
            row["riskroll_support_rate"] > row["retrieve_support_rate"]
        )

        rows.append(row)

    df = pd.DataFrame(rows)

    comparison_csv = OUT_DIR / f"experiment8d_{TAG}_task_comparison_retrieve_vs_riskroll.csv"
    summary_csv = OUT_DIR / f"experiment8d_{TAG}_error_summary.csv"
    md_path = OUT_DIR / f"experiment8d_{TAG}_error_analysis.md"

    df.to_csv(comparison_csv, index=False)

    summary = {
        "num_tasks": len(df),
        "riskroll_better_accuracy_tasks": int((df["comparison"] == "riskroll_better_accuracy").sum()),
        "riskroll_same_accuracy_tasks": int((df["comparison"] == "same_accuracy").sum()),
        "riskroll_lower_accuracy_tasks": int((df["comparison"] == "riskroll_lower_accuracy").sum()),
        "retrieve_unsafe_tasks": int(df["retrieve_unsafe"].sum()),
        "riskroll_safe_tasks": int(df["riskroll_safe"].sum()),
        "retrieve_unsafe_but_riskroll_safe_tasks": int(((df["retrieve_unsafe"] == 1) & (df["riskroll_safe"] == 1)).sum()),
        "riskroll_lower_accuracy_but_safe_tasks": int(((df["comparison"] == "riskroll_lower_accuracy") & (df["riskroll_safe"] == 1)).sum()),
        "riskroll_better_support_tasks": int(df["riskroll_better_support"].sum()),
        "mean_retrieve_accuracy": float(df["retrieve_claim_accuracy"].mean()),
        "mean_riskroll_accuracy": float(df["riskroll_claim_accuracy"].mean()),
        "mean_retrieve_support": float(df["retrieve_support_rate"].mean()),
        "mean_riskroll_support": float(df["riskroll_support_rate"].mean()),
        "mean_retrieve_unsupported": float(df["retrieve_unsupported"].mean()),
        "mean_riskroll_unsupported": float(df["riskroll_unsupported"].mean()),
        "mean_retrieve_unsafe_depth": float(df["retrieve_unsafe_depth"].mean()),
        "mean_riskroll_unsafe_depth": float(df["riskroll_unsafe_depth"].mean()),
        "mean_riskroll_rollbacks": float(df["riskroll_rollbacks"].mean()),
        "mean_riskroll_repairs": float(df["riskroll_repairs"].mean()),
    }

    pd.DataFrame([summary]).to_csv(summary_csv, index=False)

    better = df[df["comparison"] == "riskroll_better_accuracy"].head(5)
    lower = df[df["comparison"] == "riskroll_lower_accuracy"].head(5)
    unsafe_saved = df[(df["retrieve_unsafe"] == 1) & (df["riskroll_safe"] == 1)].head(5)

    lines = []
    lines.append("# ASQA Error Analysis: Retrieve-more vs RiskRoll")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    for k, v in summary.items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")

    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "RiskRoll is compared directly against retrieve-more RAG on the same ASQA tasks. "
        "The goal is to identify whether RiskRoll loses raw claim accuracy because it behaves conservatively, "
        "and whether it removes unsafe commits that appear in retrieve-more generations."
    )
    lines.append("")

    lines.append("## Example tasks where RiskRoll has higher accuracy")
    lines.append("")
    for _, r in better.iterrows():
        lines.append(f"### {r['task_id']}: {r['question']}")
        lines.append(f"- Retrieve-more items: {r['retrieve_items']}")
        lines.append(f"- RiskRoll items: {r['riskroll_items']}")
        lines.append(f"- Retrieve accuracy: {r['retrieve_claim_accuracy']}")
        lines.append(f"- RiskRoll accuracy: {r['riskroll_claim_accuracy']}")
        lines.append("")

    lines.append("## Example tasks where RiskRoll has lower accuracy")
    lines.append("")
    for _, r in lower.iterrows():
        lines.append(f"### {r['task_id']}: {r['question']}")
        lines.append(f"- Retrieve-more items: {r['retrieve_items']}")
        lines.append(f"- RiskRoll items: {r['riskroll_items']}")
        lines.append(f"- Retrieve accuracy: {r['retrieve_claim_accuracy']}")
        lines.append(f"- RiskRoll accuracy: {r['riskroll_claim_accuracy']}")
        lines.append(f"- RiskRoll safe: {r['riskroll_safe']}")
        lines.append("")

    lines.append("## Example tasks where retrieve-more is unsafe but RiskRoll is safe")
    lines.append("")
    for _, r in unsafe_saved.iterrows():
        lines.append(f"### {r['task_id']}: {r['question']}")
        lines.append(f"- Retrieve unsupported commits: {r['retrieve_unsupported']}")
        lines.append(f"- Retrieve unsafe depth: {r['retrieve_unsafe_depth']}")
        lines.append(f"- RiskRoll unsupported commits: {r['riskroll_unsupported']}")
        lines.append(f"- RiskRoll unsafe depth: {r['riskroll_unsafe_depth']}")
        lines.append(f"- Retrieve-more items: {r['retrieve_items']}")
        lines.append(f"- RiskRoll items: {r['riskroll_items']}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    print("Saved ASQA error analysis:")
    print(comparison_csv)
    print(summary_csv)
    print(md_path)

    print("")
    print("ASQA Error Summary:")
    print(pd.DataFrame([summary]).to_string(index=False))


if __name__ == "__main__":
    main()

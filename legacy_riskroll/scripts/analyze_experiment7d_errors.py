from pathlib import Path
import json
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
TAG = "qwen7b_qampari_100_v3"

RAW_PATH = PROJECT / "results" / "raw" / f"experiment7d_alce_qampari_llm_generation_{TAG}_raw.json"
OUT_DIR = PROJECT / "paper_assets" / "analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

METHOD_A = "retrieve_more_top20"
METHOD_B = "riskroll_top20"

raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
records = raw["raw_records"]

by_task = {}
for rec in records:
    task = rec["task"]
    task_id = task.get("task_id") or task.get("example_id") or task.get("id")
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
        "gold": task.get("gold_answer_list", []),

        "retrieve_items": a["result"].get("items", []),
        "riskroll_items": b["result"].get("items", []),

        "retrieve_f1": ae.get("answer_f1", 0),
        "riskroll_f1": be.get("answer_f1", 0),

        "retrieve_strict_grounded": ae.get("strict_grounded_rate", 0),
        "riskroll_strict_grounded": be.get("strict_grounded_rate", 0),

        "retrieve_support_rate": ae.get("support_rate", 0),
        "riskroll_support_rate": be.get("support_rate", 0),

        "retrieve_unsupported": ae.get("unsupported_commits", 0),
        "riskroll_unsupported": be.get("unsupported_commits", 0),

        "retrieve_unsafe_depth": ae.get("unsafe_prefix_depth", 0),
        "riskroll_unsafe_depth": be.get("unsafe_prefix_depth", 0),

        "retrieve_abstain": ae.get("abstention_count", 0),
        "riskroll_abstain": be.get("abstention_count", 0),

        "riskroll_rollbacks": b["result"].get("rollback_count", 0),
        "riskroll_repairs": b["result"].get("repair_count", 0),
    }

    if row["riskroll_f1"] > row["retrieve_f1"]:
        row["comparison"] = "riskroll_better_f1"
    elif row["riskroll_f1"] < row["retrieve_f1"]:
        row["comparison"] = "riskroll_lower_f1"
    else:
        row["comparison"] = "same_f1"

    row["retrieve_unsafe"] = int(row["retrieve_unsupported"] > 0 or row["retrieve_unsafe_depth"] > 0)
    row["riskroll_safe"] = int(row["riskroll_unsupported"] == 0 and row["riskroll_unsafe_depth"] == 0)

    rows.append(row)

df = pd.DataFrame(rows)

csv_path = OUT_DIR / f"experiment7d_{TAG}_task_comparison_retrieve_vs_riskroll.csv"
df.to_csv(csv_path, index=False)

n = len(df)

summary = {
    "num_tasks": n,
    "riskroll_better_f1_tasks": int((df["comparison"] == "riskroll_better_f1").sum()),
    "riskroll_same_f1_tasks": int((df["comparison"] == "same_f1").sum()),
    "riskroll_lower_f1_tasks": int((df["comparison"] == "riskroll_lower_f1").sum()),
    "retrieve_unsafe_tasks": int(df["retrieve_unsafe"].sum()),
    "riskroll_safe_tasks": int(df["riskroll_safe"].sum()),
    "retrieve_unsafe_but_riskroll_safe_tasks": int(((df["retrieve_unsafe"] == 1) & (df["riskroll_safe"] == 1)).sum()),
    "riskroll_lower_f1_but_safe_tasks": int(((df["comparison"] == "riskroll_lower_f1") & (df["riskroll_safe"] == 1)).sum()),
    "riskroll_support_1_but_low_f1_tasks": int(((df["riskroll_support_rate"] >= 0.999) & (df["riskroll_f1"] <= 0.2)).sum()),
}

summary_path = OUT_DIR / f"experiment7d_{TAG}_error_summary.csv"
pd.DataFrame([summary]).to_csv(summary_path, index=False)

md = []
md.append("# Experiment 7D Error Analysis: Retrieve-more vs RiskRoll")
md.append("")
md.append(f"Tag: `{TAG}`")
md.append("")
md.append("## Aggregate counts")
md.append("")
for k, v in summary.items():
    md.append(f"- **{k}**: {v}")

md.append("")
md.append("## Main interpretation")
md.append("")
md.append(
    "RiskRoll should not be judged only as a raw-F1 method. "
    "Its target is trusted-prefix generation: it commits only evidence-supported items, "
    "rolls back unsupported candidates, and abstains when no safe item is found. "
    "Therefore, the key comparison is whether it reduces unsupported commits and unsafe-prefix contamination "
    "while keeping answer quality competitive."
)

md.append("")
md.append("## Examples where retrieve-more is unsafe but RiskRoll remains safe")
md.append("")

unsafe_examples = df[(df["retrieve_unsafe"] == 1) & (df["riskroll_safe"] == 1)].head(8)

for _, r in unsafe_examples.iterrows():
    md.append(f"### {r['task_id']}")
    md.append(f"**Question:** {r['question']}")
    md.append(f"**Gold:** {r['gold']}")
    md.append(f"**Retrieve-more:** {r['retrieve_items']}")
    md.append(f"F1={r['retrieve_f1']:.3f}, unsupported={r['retrieve_unsupported']}, unsafe_depth={r['retrieve_unsafe_depth']}")
    md.append(f"**RiskRoll:** {r['riskroll_items']}")
    md.append(f"F1={r['riskroll_f1']:.3f}, unsupported={r['riskroll_unsupported']}, unsafe_depth={r['riskroll_unsafe_depth']}, rollbacks={r['riskroll_rollbacks']}")
    md.append("")

md.append("")
md.append("## Examples where RiskRoll has supported predictions but low gold F1")
md.append("")

gold_mismatch_examples = df[(df["riskroll_support_rate"] >= 0.999) & (df["riskroll_f1"] <= 0.2)].head(8)

for _, r in gold_mismatch_examples.iterrows():
    md.append(f"### {r['task_id']}")
    md.append(f"**Question:** {r['question']}")
    md.append(f"**Gold:** {r['gold']}")
    md.append(f"**RiskRoll:** {r['riskroll_items']}")
    md.append(f"RiskRoll F1={r['riskroll_f1']:.3f}, support_rate={r['riskroll_support_rate']:.3f}")
    md.append("Possible issue: supported evidence item may not match the gold alias list, or the generated item is too broad/partial.")
    md.append("")

md_path = OUT_DIR / f"experiment7d_{TAG}_error_analysis.md"
md_path.write_text("\n".join(md), encoding="utf-8")

print("Saved:")
print(csv_path)
print(summary_path)
print(md_path)

print("")
print("Error summary:")
print(pd.DataFrame([summary]).to_string(index=False))

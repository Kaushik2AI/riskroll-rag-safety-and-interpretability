from pathlib import Path
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]

TABLE_DIR = PROJECT / "paper_assets" / "tables"
TEXT_DIR = PROJECT / "paper_assets" / "text"

TABLE_DIR.mkdir(parents=True, exist_ok=True)
TEXT_DIR.mkdir(parents=True, exist_ok=True)

QAMPARI = PROJECT / "results" / "tables" / "experiment7d_alce_qampari_llm_generation_qwen7b_qampari_100_v3_summary.csv"
ASQA = PROJECT / "results" / "tables" / "experiment8d_alce_asqa_llm_generation_qwen7b_asqa_73_v1_summary.csv"


def fmt3(x):
    return f"{float(x):.3f}"


def dataframe_to_markdown(df):
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join([header, sep] + rows)


def load_public_summary(path, dataset_name, quality_col, quality_name):
    df = pd.read_csv(path)

    method_short = {
        "standard_top1": "Standard RAG",
        "retrieve_more_top20": "Retrieve-more",
        "posthoc_top20": "Post-hoc",
        "crag_style_top20": "CRAG-style",
        "riskroll_top20": "RiskRoll",
    }

    rows = []
    for _, r in df.iterrows():
        rows.append({
            "Dataset": dataset_name,
            "Tasks": int(r["num_tasks"]),
            "Method": method_short.get(r["method"], r["method"]),
            "Quality Metric": quality_name,
            "Quality": fmt3(r[quality_col]),
            "Strict Grounded": fmt3(r["strict_grounded_rate"]),
            "Support Rate": fmt3(r["support_rate"]),
            "Unsupported Commits": fmt3(r["mean_unsupported_commits"]),
            "Unsafe Depth": fmt3(r["mean_unsafe_prefix_depth"]),
            "Abstentions": fmt3(r["mean_abstention_count"]),
            "Rollbacks": fmt3(r.get("mean_rollback_count", 0)),
            "Repairs": fmt3(r.get("mean_repair_count", 0)),
        })
    return rows


def main():
    rows = []
    rows.extend(load_public_summary(QAMPARI, "QAMPARI", "answer_f1", "F1"))
    rows.extend(load_public_summary(ASQA, "ASQA", "claim_accuracy", "Claim Acc."))

    df = pd.DataFrame(rows)

    method_order = {
        "Standard RAG": 0,
        "Retrieve-more": 1,
        "Post-hoc": 2,
        "CRAG-style": 3,
        "RiskRoll": 4,
    }

    dataset_order = {
        "QAMPARI": 0,
        "ASQA": 1,
    }

    df["dataset_order"] = df["Dataset"].map(dataset_order)
    df["method_order"] = df["Method"].map(method_order)
    df = df.sort_values(["dataset_order", "method_order"])
    df = df.drop(columns=["dataset_order", "method_order"])

    csv_path = TABLE_DIR / "table10_public_llm_overhead_and_safety_cost.csv"
    md_path = TABLE_DIR / "table10_public_llm_overhead_and_safety_cost.md"
    tex_path = TABLE_DIR / "table10_public_llm_overhead_and_safety_cost.tex"

    df.to_csv(csv_path, index=False)
    md_path.write_text(dataframe_to_markdown(df), encoding="utf-8")
    tex_path.write_text(df.to_latex(index=False, escape=True), encoding="utf-8")

    q = pd.read_csv(QAMPARI)
    a = pd.read_csv(ASQA)

    q_risk = q[q["method"] == "riskroll_top20"].iloc[0]
    a_risk = a[a["method"] == "riskroll_top20"].iloc[0]

    q_ret = q[q["method"] == "retrieve_more_top20"].iloc[0]
    a_ret = a[a["method"] == "retrieve_more_top20"].iloc[0]

    paragraph = f"""# Overhead and Safety-Cost Summary

RiskRoll introduces explicit inference-time overhead through rollback and repair operations. This overhead is not hidden: it is measured by rollback count, repair count, and abstention count.

On QAMPARI, RiskRoll performs {q_risk['mean_rollback_count']:.3f} rollbacks and {q_risk['mean_repair_count']:.3f} repairs per task on average. This produces zero unsupported commits and zero unsafe prefix depth, compared with retrieve-more RAG, which has {q_ret['mean_unsupported_commits']:.3f} unsupported commits and {q_ret['mean_unsafe_prefix_depth']:.3f} unsafe prefix depth per task.

On ASQA, RiskRoll performs {a_risk['mean_rollback_count']:.3f} rollbacks and {a_risk['mean_repair_count']:.3f} repairs per task on average. It again reduces unsupported commits and unsafe prefix depth to zero, while retrieve-more RAG has {a_ret['mean_unsupported_commits']:.3f} unsupported commits and {a_ret['mean_unsafe_prefix_depth']:.3f} unsafe prefix depth per task.

These results show that RiskRoll's safety improvements come from active inference-time control rather than passive retrieval expansion. The cost is additional rollback and repair work; the benefit is preventing unsupported claims from entering the trusted prefix.
"""

    paragraph_path = TEXT_DIR / "overhead_and_safety_cost_paragraph.md"
    paragraph_path.write_text(paragraph, encoding="utf-8")

    print("Saved overhead table:")
    print(csv_path)
    print(md_path)
    print(tex_path)
    print("")
    print("Saved paragraph:")
    print(paragraph_path)
    print("")
    print(dataframe_to_markdown(df))


if __name__ == "__main__":
    main()

from pathlib import Path
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]

TABLE_DIR = PROJECT / "paper_assets" / "tables"
TABLE_DIR.mkdir(parents=True, exist_ok=True)

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


def main():
    q = pd.read_csv(QAMPARI)
    a = pd.read_csv(ASQA)

    method_order = [
        "standard_top1",
        "retrieve_more_top20",
        "posthoc_top20",
        "crag_style_top20",
        "riskroll_top20",
    ]

    method_short = {
        "standard_top1": "Standard RAG",
        "retrieve_more_top20": "Retrieve-more",
        "posthoc_top20": "Post-hoc",
        "crag_style_top20": "CRAG-style",
        "riskroll_top20": "RiskRoll",
    }

    rows = []

    for _, r in q.iterrows():
        rows.append({
            "Dataset": "QAMPARI",
            "Tasks": int(r["num_tasks"]),
            "Method": method_short[r["method"]],
            "Quality": fmt3(r["answer_f1"]),
            "Quality Metric": "F1",
            "Strict Grounded": fmt3(r["strict_grounded_rate"]),
            "Support Rate": fmt3(r["support_rate"]),
            "Unsupported Commits": fmt3(r["mean_unsupported_commits"]),
            "Unsafe Depth": fmt3(r["mean_unsafe_prefix_depth"]),
            "Abstentions": fmt3(r["mean_abstention_count"]),
            "Rollbacks": fmt3(r["mean_rollback_count"]),
        })

    for _, r in a.iterrows():
        rows.append({
            "Dataset": "ASQA",
            "Tasks": int(r["num_tasks"]),
            "Method": method_short[r["method"]],
            "Quality": fmt3(r["claim_accuracy"]),
            "Quality Metric": "Claim Acc.",
            "Strict Grounded": fmt3(r["strict_grounded_rate"]),
            "Support Rate": fmt3(r["support_rate"]),
            "Unsupported Commits": fmt3(r["mean_unsupported_commits"]),
            "Unsafe Depth": fmt3(r["mean_unsafe_prefix_depth"]),
            "Abstentions": fmt3(r["mean_abstention_count"]),
            "Rollbacks": fmt3(r["mean_rollback_count"]),
        })

    df = pd.DataFrame(rows)
    df["method_order"] = df["Method"].map({
        "Standard RAG": 0,
        "Retrieve-more": 1,
        "Post-hoc": 2,
        "CRAG-style": 3,
        "RiskRoll": 4,
    })

    df["dataset_order"] = df["Dataset"].map({
        "QAMPARI": 0,
        "ASQA": 1,
    })

    df = df.sort_values(["dataset_order", "method_order"])
    df = df.drop(columns=["dataset_order", "method_order"])

    csv_path = TABLE_DIR / "table9_combined_public_llm_results.csv"
    md_path = TABLE_DIR / "table9_combined_public_llm_results.md"
    tex_path = TABLE_DIR / "table9_combined_public_llm_results.tex"

    df.to_csv(csv_path, index=False)
    md_path.write_text(dataframe_to_markdown(df), encoding="utf-8")
    tex_path.write_text(df.to_latex(index=False, escape=True), encoding="utf-8")

    print("Saved:")
    print(csv_path)
    print(md_path)
    print(tex_path)

    print("")
    print(dataframe_to_markdown(df))


if __name__ == "__main__":
    main()

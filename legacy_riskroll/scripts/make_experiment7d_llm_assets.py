from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


PROJECT = Path(__file__).resolve().parents[1]

TAG = "qwen7b_qampari_100_v3"

SUMMARY_PATH = PROJECT / "results" / "tables" / f"experiment7d_alce_qampari_llm_generation_{TAG}_summary.csv"

TABLE_DIR = PROJECT / "paper_assets" / "tables"
FIG_DIR = PROJECT / "results" / "figures"

TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

DPI = 600


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


def save_table(df, stem):
    csv_path = TABLE_DIR / f"{stem}.csv"
    md_path = TABLE_DIR / f"{stem}.md"
    tex_path = TABLE_DIR / f"{stem}.tex"

    df.to_csv(csv_path, index=False)
    md_path.write_text(dataframe_to_markdown(df), encoding="utf-8")

    latex = df.to_latex(
        index=False,
        escape=True,
        column_format="l" + "r" * (len(df.columns) - 1),
    )
    tex_path.write_text(latex, encoding="utf-8")

    print("Saved table:")
    print(" ", csv_path)
    print(" ", md_path)
    print(" ", tex_path)


def savefig(path):
    plt.tight_layout()
    plt.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close()
    print("Saved figure:", path)


def short_labels(df):
    mapping = {
        "standard_top1": "Std top-1",
        "retrieve_more_top20": "Top-20",
        "posthoc_top20": "Post-hoc",
        "crag_style_top20": "CRAG-style",
        "riskroll_top20": "RiskRoll",
    }
    return [mapping.get(str(m), str(m)) for m in df["method"]]


def main():
    df = pd.read_csv(SUMMARY_PATH)

    order = [
        "standard_top1",
        "retrieve_more_top20",
        "posthoc_top20",
        "crag_style_top20",
        "riskroll_top20",
    ]

    df["method"] = pd.Categorical(df["method"], categories=order, ordered=True)
    df = df.sort_values("method")

    table = pd.DataFrame({
        "Method": df["method_display"],
        "Precision": df["answer_precision"].map(fmt3),
        "Recall": df["answer_recall"].map(fmt3),
        "F1": df["answer_f1"].map(fmt3),
        "Strict Grounded": df["strict_grounded_rate"].map(fmt3),
        "Support Rate": df["support_rate"].map(fmt3),
        "Clean Task": df["clean_task_rate"].map(fmt3),
        "Unsupported Commits": df["mean_unsupported_commits"].map(fmt3),
        "Unsafe Depth": df["mean_unsafe_prefix_depth"].map(fmt3),
        "Abstentions": df["mean_abstention_count"].map(fmt3),
        "Rollbacks": df["mean_rollback_count"].map(fmt3),
        "Repairs": df["mean_repair_count"].map(fmt3),
    })

    save_table(table, "table7_alce_qampari_qwen7b_llm_generation_100")

    labels = short_labels(df)

    # Figure 1: F1
    plt.figure(figsize=(7.6, 4.8))
    plt.bar(labels, df["answer_f1"])
    plt.ylabel("Answer F1")
    plt.title("ALCE-QAMPARI Qwen2.5-7B generation: answer F1")
    plt.ylim(0, max(0.5, float(df["answer_f1"].max()) + 0.08))
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "experiment7d_qwen7b_answer_f1.png")

    # Figure 2: strict grounded rate
    plt.figure(figsize=(7.6, 4.8))
    plt.bar(labels, df["strict_grounded_rate"])
    plt.ylabel("Strict grounded rate")
    plt.title("RiskRoll improves strictly grounded generation")
    plt.ylim(0, max(0.5, float(df["strict_grounded_rate"].max()) + 0.08))
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "experiment7d_qwen7b_strict_grounded_rate.png")

    # Figure 3: unsupported commits
    plt.figure(figsize=(7.6, 4.8))
    plt.bar(labels, df["mean_unsupported_commits"])
    plt.ylabel("Unsupported commits per task")
    plt.title("RiskRoll avoids unsupported commits")
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "experiment7d_qwen7b_unsupported_commits.png")

    # Figure 4: safety-quality tradeoff
    plt.figure(figsize=(7.0, 5.2))
    plt.scatter(
        df["mean_unsupported_commits"],
        df["answer_f1"],
        s=90,
    )

    for label, (_, row) in zip(labels, df.iterrows()):
        plt.annotate(
            label,
            (row["mean_unsupported_commits"], row["answer_f1"]),
            textcoords="offset points",
            xytext=(6, 5),
            fontsize=8,
        )

    plt.xlabel("Unsupported commits per task")
    plt.ylabel("Answer F1")
    plt.title("RiskRoll improves F1 while avoiding unsafe commitments")
    plt.grid(True, alpha=0.3)
    savefig(FIG_DIR / "experiment7d_qwen7b_f1_vs_unsupported_commits.png")

    # Figure 5: abstention and rollback overhead
    riskroll = df[df["method"] == "riskroll_top20"].iloc[0]

    plt.figure(figsize=(6.8, 4.8))
    plt.bar(
        ["Abstentions", "Rollbacks", "Repairs"],
        [
            riskroll["mean_abstention_count"],
            riskroll["mean_rollback_count"],
            riskroll["mean_repair_count"],
        ],
    )
    plt.ylabel("Mean count per task")
    plt.title("RiskRoll overhead on ALCE-QAMPARI")
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "experiment7d_qwen7b_riskroll_overhead.png")

    print(f"\nAll Experiment 7D assets saved at {DPI} dpi.")


if __name__ == "__main__":
    main()

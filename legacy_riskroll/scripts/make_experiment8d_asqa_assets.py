from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

PROJECT = Path(__file__).resolve().parents[1]
TAG = "qwen7b_asqa_73_v1"

SUMMARY_PATH = PROJECT / "results" / "tables" / f"experiment8d_alce_asqa_llm_generation_{TAG}_summary.csv"

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
    tex_path.write_text(df.to_latex(index=False, escape=True), encoding="utf-8")

    print("Saved table:")
    print(" ", csv_path)
    print(" ", md_path)
    print(" ", tex_path)


def savefig(path):
    plt.tight_layout()
    plt.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close()
    print("Saved figure:", path)


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
        "Claim Acc.": df["claim_accuracy"].map(fmt3),
        "Strict Grounded": df["strict_grounded_rate"].map(fmt3),
        "Support Rate": df["support_rate"].map(fmt3),
        "Clean Task": df["clean_task_rate"].map(fmt3),
        "Unsupported Commits": df["mean_unsupported_commits"].map(fmt3),
        "Unsafe Depth": df["mean_unsafe_prefix_depth"].map(fmt3),
        "Abstentions": df["mean_abstention_count"].map(fmt3),
        "Rollbacks": df["mean_rollback_count"].map(fmt3),
        "Repairs": df["mean_repair_count"].map(fmt3),
    })

    save_table(table, "table8_alce_asqa_qwen7b_llm_generation_73")

    label_map = {
        "standard_top1": "Std top-1",
        "retrieve_more_top20": "Top-20",
        "posthoc_top20": "Post-hoc",
        "crag_style_top20": "CRAG-style",
        "riskroll_top20": "RiskRoll",
    }

    labels = [label_map[str(x)] for x in df["method"]]

    # Figure 1: Claim accuracy
    plt.figure(figsize=(7.6, 4.8))
    plt.bar(labels, df["claim_accuracy"])
    plt.ylabel("Claim accuracy")
    plt.title("ALCE-ASQA Qwen2.5-7B: claim accuracy")
    plt.ylim(0, max(0.5, float(df["claim_accuracy"].max()) + 0.08))
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "experiment8d_asqa_claim_accuracy.png")

    # Figure 2: Strict grounded rate
    plt.figure(figsize=(7.6, 4.8))
    plt.bar(labels, df["strict_grounded_rate"])
    plt.ylabel("Strict grounded rate")
    plt.title("ALCE-ASQA: strictly grounded generation")
    plt.ylim(0, max(0.5, float(df["strict_grounded_rate"].max()) + 0.08))
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "experiment8d_asqa_strict_grounded_rate.png")

    # Figure 3: Support rate
    plt.figure(figsize=(7.6, 4.8))
    plt.bar(labels, df["support_rate"])
    plt.ylabel("Support rate among non-UNKNOWN predictions")
    plt.title("ALCE-ASQA: evidence support rate")
    plt.ylim(0, 1.05)
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "experiment8d_asqa_support_rate.png")

    # Figure 4: Unsupported commits
    plt.figure(figsize=(7.6, 4.8))
    plt.bar(labels, df["mean_unsupported_commits"])
    plt.ylabel("Unsupported commits per task")
    plt.title("RiskRoll avoids unsupported ASQA commits")
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "experiment8d_asqa_unsupported_commits.png")

    # Figure 5: Unsafe prefix depth
    plt.figure(figsize=(7.6, 4.8))
    plt.bar(labels, df["mean_unsafe_prefix_depth"])
    plt.ylabel("Unsafe prefix depth")
    plt.title("RiskRoll eliminates unsafe ASQA prefixes")
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "experiment8d_asqa_unsafe_prefix_depth.png")

    # Figure 6: Safety-quality tradeoff
    plt.figure(figsize=(7.0, 5.2))
    plt.scatter(df["mean_unsupported_commits"], df["claim_accuracy"], s=90)

    for label, (_, row) in zip(labels, df.iterrows()):
        plt.annotate(
            label,
            (row["mean_unsupported_commits"], row["claim_accuracy"]),
            textcoords="offset points",
            xytext=(6, 5),
            fontsize=8,
        )

    plt.xlabel("Unsupported commits per task")
    plt.ylabel("Claim accuracy")
    plt.title("ASQA safety-quality tradeoff")
    plt.grid(True, alpha=0.3)
    savefig(FIG_DIR / "experiment8d_asqa_accuracy_vs_unsupported.png")

    print(f"\nAll ASQA assets saved at {DPI} dpi.")


if __name__ == "__main__":
    main()

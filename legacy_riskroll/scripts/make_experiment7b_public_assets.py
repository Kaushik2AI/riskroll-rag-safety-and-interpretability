from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


PROJECT = Path(__file__).resolve().parents[1]

SUMMARY_PATH = PROJECT / "results" / "tables" / "experiment7b_alce_qampari_public_diagnostic_summary.csv"

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


def main():
    df = pd.read_csv(SUMMARY_PATH)

    order = [
        "standard_top1",
        "retrieve_more_top5",
        "retrieve_more_top20",
        "riskroll_top20",
    ]

    df["method"] = pd.Categorical(df["method"], categories=order, ordered=True)
    df = df.sort_values("method")

    table = pd.DataFrame({
        "Method": df["method_display"],
        "Grounded Rate": df["grounded_claim_rate"].map(fmt3),
        "Clean Task Rate": df["clean_task_rate"].map(fmt3),
        "Unsafe Depth": df["mean_unsafe_prefix_depth"].map(fmt3),
        "Contamination": df["mean_downstream_contaminated_claims"].map(fmt3),
        "Rollbacks": df["mean_rollback_count"].map(fmt3),
        "Abstentions": df["mean_abstention_count"].map(fmt3),
    })

    save_table(table, "table5_alce_qampari_public_diagnostic")

    labels = [
        "Std top-1",
        "Top-5",
        "Top-20",
        "RiskRoll",
    ]

    # Figure 1: Grounded claim rate
    plt.figure(figsize=(7.2, 4.8))
    plt.bar(labels, df["grounded_claim_rate"])
    plt.ylabel("Grounded claim rate")
    plt.title("ALCE-QAMPARI public grounding diagnostic")
    plt.ylim(0, 1.0)
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "experiment7b_alce_qampari_grounded_rate.png")

    # Figure 2: Unsafe prefix depth
    plt.figure(figsize=(7.2, 4.8))
    plt.bar(labels, df["mean_unsafe_prefix_depth"])
    plt.ylabel("Unsafe prefix depth")
    plt.title("RiskRoll prevents unsafe prefix growth on ALCE-QAMPARI")
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "experiment7b_alce_qampari_unsafe_prefix_depth.png")

    # Figure 3: Grounding vs contamination
    plt.figure(figsize=(7.0, 5.2))
    plt.scatter(
        df["mean_downstream_contaminated_claims"],
        df["grounded_claim_rate"],
        s=90,
    )

    for _, row in df.iterrows():
        short = row["method_display"]
        short = short.replace("Standard RAG top-1 commit", "Std top-1")
        short = short.replace("Retrieve-more RAG top-5 context", "Top-5")
        short = short.replace("Retrieve-more RAG top-20 context", "Top-20")
        short = short.replace("RiskRoll top-20 verify-before-commit", "RiskRoll")

        plt.annotate(
            short,
            (row["mean_downstream_contaminated_claims"], row["grounded_claim_rate"]),
            textcoords="offset points",
            xytext=(6, 5),
            fontsize=8,
        )

    plt.xlabel("Downstream contaminated claims")
    plt.ylabel("Grounded claim rate")
    plt.title("RiskRoll keeps contamination zero at top-20 grounding")
    plt.ylim(0, 1.0)
    plt.grid(True, alpha=0.3)
    savefig(FIG_DIR / "experiment7b_alce_qampari_grounding_vs_contamination.png")

    # Figure 4: Rollback/abstention overhead
    riskroll = df[df["method"] == "riskroll_top20"].iloc[0]

    plt.figure(figsize=(6.4, 4.8))
    plt.bar(
        ["Rollbacks", "Abstentions"],
        [riskroll["mean_rollback_count"], riskroll["mean_abstention_count"]],
    )
    plt.ylabel("Mean count per task")
    plt.title("RiskRoll public-diagnostic overhead")
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "experiment7b_alce_qampari_riskroll_overhead.png")

    print(f"\nAll Experiment 7B assets saved at {DPI} dpi.")


if __name__ == "__main__":
    main()

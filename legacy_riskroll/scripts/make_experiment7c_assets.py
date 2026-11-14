from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


PROJECT = Path(__file__).resolve().parents[1]

SUMMARY_PATH = PROJECT / "results" / "tables" / "experiment7c_alce_qampari_commit_policy_summary.csv"

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
    return [mapping[m] for m in df["method"]]


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
        "Grounded Rate": df["final_grounded_claim_rate"].map(fmt3),
        "Clean Task": df["clean_task_rate"].map(fmt3),
        "Unsupported Commits": df["mean_unsupported_commits"].map(fmt3),
        "Unsafe Depth": df["mean_unsafe_prefix_depth"].map(fmt3),
        "Contamination": df["mean_downstream_contaminated_claims"].map(fmt3),
        "Rollbacks": df["mean_rollback_count"].map(fmt3),
        "Abstentions": df["mean_abstention_count"].map(fmt3),
        "Repairs": df["mean_repair_count"].map(fmt3),
    })

    save_table(table, "table6_alce_qampari_commit_policy")

    labels = short_labels(df)

    # Figure 1: final grounded rate
    plt.figure(figsize=(7.6, 4.8))
    plt.bar(labels, df["final_grounded_claim_rate"])
    plt.ylabel("Final grounded claim rate")
    plt.title("ALCE-QAMPARI commit-policy comparison")
    plt.ylim(0, 1.0)
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "experiment7c_final_grounded_claim_rate.png")

    # Figure 2: unsupported commits
    plt.figure(figsize=(7.6, 4.8))
    plt.bar(labels, df["mean_unsupported_commits"])
    plt.ylabel("Unsupported commits per task")
    plt.title("RiskRoll avoids unsupported semantic commitments")
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "experiment7c_unsupported_commits.png")

    # Figure 3: unsafe prefix depth
    plt.figure(figsize=(7.6, 4.8))
    plt.bar(labels, df["mean_unsafe_prefix_depth"])
    plt.ylabel("Unsafe prefix depth")
    plt.title("RiskRoll prevents unsafe-prefix growth")
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "experiment7c_unsafe_prefix_depth.png")

    # Figure 4: grounded rate vs unsupported commits
    plt.figure(figsize=(7.0, 5.2))
    plt.scatter(
        df["mean_unsupported_commits"],
        df["final_grounded_claim_rate"],
        s=90,
    )

    for label, (_, row) in zip(labels, df.iterrows()):
        plt.annotate(
            label,
            (row["mean_unsupported_commits"], row["final_grounded_claim_rate"]),
            textcoords="offset points",
            xytext=(6, 5),
            fontsize=8,
        )

    plt.xlabel("Unsupported commits per task")
    plt.ylabel("Final grounded claim rate")
    plt.title("RiskRoll separates grounding from unsafe commitment")
    plt.ylim(0, 1.0)
    plt.grid(True, alpha=0.3)
    savefig(FIG_DIR / "experiment7c_grounding_vs_unsupported_commits.png")

    # Figure 5: RiskRoll overhead
    riskroll = df[df["method"] == "riskroll_top20"].iloc[0]

    plt.figure(figsize=(6.8, 4.8))
    plt.bar(
        ["Rollbacks", "Abstentions", "Repairs"],
        [
            riskroll["mean_rollback_count"],
            riskroll["mean_abstention_count"],
            riskroll["mean_repair_count"],
        ],
    )
    plt.ylabel("Mean count per task")
    plt.title("RiskRoll overhead on ALCE-QAMPARI")
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "experiment7c_riskroll_overhead.png")

    print(f"\nAll Experiment 7C assets saved at {DPI} dpi.")


if __name__ == "__main__":
    main()

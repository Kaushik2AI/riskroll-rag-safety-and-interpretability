from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

PROJECT = Path(__file__).resolve().parents[1]

TABLE_PATH = PROJECT / "paper_assets" / "tables" / "table9_combined_public_llm_results.csv"

FIG_DIR = PROJECT / "results" / "figures"
TEXT_DIR = PROJECT / "paper_assets" / "text"

FIG_DIR.mkdir(parents=True, exist_ok=True)
TEXT_DIR.mkdir(parents=True, exist_ok=True)

DPI = 600


def savefig(path):
    plt.tight_layout()
    plt.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close()
    print("Saved figure:", path)


def main():
    df = pd.read_csv(TABLE_PATH)

    method_order = ["Standard RAG", "Retrieve-more", "Post-hoc", "CRAG-style", "RiskRoll"]
    dataset_order = ["QAMPARI", "ASQA"]

    df["Method"] = pd.Categorical(df["Method"], categories=method_order, ordered=True)
    df["Dataset"] = pd.Categorical(df["Dataset"], categories=dataset_order, ordered=True)
    df = df.sort_values(["Dataset", "Method"])

    # Figure 1: quality by dataset
    plt.figure(figsize=(9.2, 5.0))
    x = range(len(df))
    labels = [f"{d}\n{m}" for d, m in zip(df["Dataset"], df["Method"])]
    plt.bar(x, df["Quality"])
    plt.xticks(x, labels, rotation=45, ha="right")
    plt.ylabel("Quality score")
    plt.title("Public LLM experiments: answer quality")
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "combined_public_llm_quality.png")

    # Figure 2: strict grounded rate
    plt.figure(figsize=(9.2, 5.0))
    plt.bar(x, df["Strict Grounded"])
    plt.xticks(x, labels, rotation=45, ha="right")
    plt.ylabel("Strict grounded rate")
    plt.title("Public LLM experiments: strict groundedness")
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "combined_public_llm_strict_grounded.png")

    # Figure 3: support rate
    plt.figure(figsize=(9.2, 5.0))
    plt.bar(x, df["Support Rate"])
    plt.xticks(x, labels, rotation=45, ha="right")
    plt.ylabel("Support rate")
    plt.title("Public LLM experiments: evidence support rate")
    plt.ylim(0, 1.05)
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "combined_public_llm_support_rate.png")

    # Figure 4: unsupported commits
    plt.figure(figsize=(9.2, 5.0))
    plt.bar(x, df["Unsupported Commits"])
    plt.xticks(x, labels, rotation=45, ha="right")
    plt.ylabel("Unsupported commits per task")
    plt.title("RiskRoll eliminates unsupported commits")
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "combined_public_llm_unsupported_commits.png")

    # Figure 5: unsafe prefix depth
    plt.figure(figsize=(9.2, 5.0))
    plt.bar(x, df["Unsafe Depth"])
    plt.xticks(x, labels, rotation=45, ha="right")
    plt.ylabel("Unsafe prefix depth")
    plt.title("RiskRoll eliminates unsafe prefix contamination")
    plt.grid(axis="y", alpha=0.3)
    savefig(FIG_DIR / "combined_public_llm_unsafe_depth.png")

    # Figure 6: quality vs unsupported commits
    plt.figure(figsize=(7.2, 5.4))
    for dataset in dataset_order:
        sub = df[df["Dataset"] == dataset]
        plt.scatter(sub["Unsupported Commits"], sub["Quality"], s=90, label=dataset)
        for _, row in sub.iterrows():
            plt.annotate(
                f"{dataset}-{row['Method']}",
                (row["Unsupported Commits"], row["Quality"]),
                textcoords="offset points",
                xytext=(6, 5),
                fontsize=7,
            )

    plt.xlabel("Unsupported commits per task")
    plt.ylabel("Quality score")
    plt.title("Safety-quality tradeoff on public LLM tasks")
    plt.grid(True, alpha=0.3)
    plt.legend()
    savefig(FIG_DIR / "combined_public_llm_quality_vs_unsupported.png")

    paragraph = """# Public LLM Results Paragraph

Across two public ALCE datasets, RiskRoll improves factual safety while remaining competitive in answer quality. On QAMPARI, retrieve-more RAG obtains the highest raw F1 (0.297), while RiskRoll remains close (0.284) and achieves the highest strict grounded rate (0.268) and support rate (0.990). More importantly, RiskRoll eliminates unsupported commits and unsafe-prefix contamination, reducing both metrics to 0.000, whereas retrieve-more and CRAG-style baselines still commit unsupported claims. On ASQA, retrieve-more obtains slightly higher claim accuracy (0.369 vs. 0.357), but RiskRoll again achieves the highest evidence support rate (0.877), zero unsupported commits, and zero unsafe prefix depth. These results support the central hypothesis that verify-before-commit rollback trades a small amount of raw recall for substantially safer long-form RAG generation.

## Short version for paper

RiskRoll is not designed to maximize answer recall at all costs. Instead, it prevents unsupported claims from entering the autoregressive prefix. Across QAMPARI and ASQA, RiskRoll remains competitive with retrieve-more RAG while consistently eliminating unsupported commits and unsafe-prefix contamination.
"""

    text_path = TEXT_DIR / "combined_public_llm_results_paragraph.md"
    text_path.write_text(paragraph, encoding="utf-8")
    print("Saved text:", text_path)

    print("\nAll combined public LLM assets saved.")


if __name__ == "__main__":
    main()

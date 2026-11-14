from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


PROJECT = Path(__file__).resolve().parents[1]

SUMMARY_PATH = PROJECT / "results" / "tables" / "experiment5_text_longform_contamination_summary.csv"
TASK_ROWS_PATH = PROJECT / "results" / "tables" / "experiment5_text_longform_contamination_task_rows.csv"

FIG_DIR = PROJECT / "results" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

DPI = 600
CLAIMS_PER_TASK = 5


def savefig(path):
    plt.tight_layout()
    plt.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close()
    print("Saved:", path)


summary = pd.read_csv(SUMMARY_PATH)
tasks = pd.read_csv(TASK_ROWS_PATH)

# Keep clean method order
method_order = [
    "Standard RAG",
    "Retrieve-more RAG",
    "Post-hoc correction",
    "CRAG-style correction",
    "RiskRoll",
]

summary["method"] = pd.Categorical(summary["method"], categories=method_order, ordered=True)
summary = summary.sort_values("method")

tasks["method"] = pd.Categorical(tasks["method"], categories=method_order, ordered=True)
tasks = tasks.sort_values("method")


# ---------------------------------------------------------------------
# Figure 1: Main grounded rate comparison
# ---------------------------------------------------------------------
plt.figure(figsize=(8, 4.8))
plt.bar(summary["method"], summary["mean_grounded_claim_rate"])
plt.ylabel("Grounded claim rate")
plt.xlabel("Method")
plt.title("RiskRoll improves grounded claims in long-form text RAG")
plt.ylim(0, 1.05)
plt.xticks(rotation=25, ha="right")
savefig(FIG_DIR / "experiment5_grounded_claim_rate.png")


# ---------------------------------------------------------------------
# Figure 2: Unsafe prefix depth
# ---------------------------------------------------------------------
plt.figure(figsize=(8, 4.8))
plt.bar(summary["method"], summary["mean_unsafe_prefix_depth"])
plt.ylabel("Unsafe prefix depth")
plt.xlabel("Method")
plt.title("RiskRoll prevents unsafe-prefix growth")
plt.xticks(rotation=25, ha="right")
savefig(FIG_DIR / "experiment5_unsafe_prefix_depth.png")


# ---------------------------------------------------------------------
# Figure 3: Clean task rate
# ---------------------------------------------------------------------
plt.figure(figsize=(8, 4.8))
plt.bar(summary["method"], summary["clean_task_rate"])
plt.ylabel("Clean task rate")
plt.xlabel("Method")
plt.title("RiskRoll preserves fully clean long-form outputs")
plt.ylim(0, 1.05)
plt.xticks(rotation=25, ha="right")
savefig(FIG_DIR / "experiment5_clean_task_rate.png")


# ---------------------------------------------------------------------
# Figure 4: Clean-prefix survival curve
# Survival at step k = fraction of tasks with no first bad step up to k.
# ---------------------------------------------------------------------
survival_rows = []

for method in method_order:
    sub = tasks[tasks["method"] == method].copy()

    for step in range(0, CLAIMS_PER_TASK + 1):
        if step == 0:
            survival = 1.0
        else:
            clean_until_step = (
                sub["first_bad_step"].isna()
                | (sub["first_bad_step"] > step)
            )
            survival = clean_until_step.mean()

        survival_rows.append({
            "method": method,
            "step": step,
            "clean_prefix_survival": survival,
        })

survival_df = pd.DataFrame(survival_rows)

plt.figure(figsize=(7.5, 4.8))
for method in method_order:
    sub = survival_df[survival_df["method"] == method]
    plt.plot(
        sub["step"],
        sub["clean_prefix_survival"],
        marker="o",
        label=method,
    )

plt.xlabel("Generation step / claim index")
plt.ylabel("Clean-prefix survival rate")
plt.title("Clean-prefix survival across long-form generation")
plt.ylim(0, 1.05)
plt.xticks(range(0, CLAIMS_PER_TASK + 1))
plt.grid(True, alpha=0.3)
plt.legend(fontsize=8)
savefig(FIG_DIR / "experiment5_clean_prefix_survival.png")


# ---------------------------------------------------------------------
# Figure 5: First bad step histogram
# ---------------------------------------------------------------------
hist_rows = []

for method in method_order:
    sub = tasks[tasks["method"] == method].copy()

    for step in range(1, CLAIMS_PER_TASK + 1):
        count = (sub["first_bad_step"] == step).sum()
        hist_rows.append({
            "method": method,
            "first_bad_step": step,
            "count": count,
        })

    clean_count = sub["first_bad_step"].isna().sum()
    hist_rows.append({
        "method": method,
        "first_bad_step": "No bad step",
        "count": clean_count,
    })

hist_df = pd.DataFrame(hist_rows)

# Plot one compact grouped line/bar-like figure using only bad-step positions.
plt.figure(figsize=(8, 4.8))
for method in method_order:
    sub = hist_df[
        (hist_df["method"] == method)
        & (hist_df["first_bad_step"] != "No bad step")
    ].copy()

    plt.plot(
        sub["first_bad_step"].astype(int),
        sub["count"],
        marker="o",
        label=method,
    )

plt.xlabel("First bad claim position")
plt.ylabel("Number of tasks")
plt.title("First unsupported claim appears immediately for baselines")
plt.xticks(range(1, CLAIMS_PER_TASK + 1))
plt.grid(True, alpha=0.3)
plt.legend(fontsize=8)
savefig(FIG_DIR / "experiment5_first_bad_step_histogram.png")


# ---------------------------------------------------------------------
# Figure 6: Accuracy vs contamination
# ---------------------------------------------------------------------
plt.figure(figsize=(6.8, 5.2))
plt.scatter(
    summary["mean_downstream_contaminated_claims"],
    summary["mean_grounded_claim_rate"],
    s=80,
)

for _, row in summary.iterrows():
    plt.annotate(
        row["method"],
        (
            row["mean_downstream_contaminated_claims"],
            row["mean_grounded_claim_rate"],
        ),
        textcoords="offset points",
        xytext=(6, 5),
        fontsize=8,
    )

plt.xlabel("Mean downstream contaminated claims")
plt.ylabel("Grounded claim rate")
plt.title("Grounding improves when downstream contamination is controlled")
plt.ylim(-0.02, 1.05)
plt.grid(True, alpha=0.3)
savefig(FIG_DIR / "experiment5_grounding_vs_contamination.png")


print(f"\nAll Experiment 5 figures saved at {DPI} dpi.")

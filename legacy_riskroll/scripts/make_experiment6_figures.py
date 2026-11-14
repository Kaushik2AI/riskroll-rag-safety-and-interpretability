from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


PROJECT = Path(__file__).resolve().parents[1]

SUMMARY_PATH = PROJECT / "results" / "tables" / "experiment6_text_noisy_verifier_sweep_summary.csv"
FIG_DIR = PROJECT / "results" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

DPI = 600

df = pd.read_csv(SUMMARY_PATH)

fa_df = df[df["sweep_type"] == "false_accept_sweep"].copy()
fr_df = df[df["sweep_type"] == "false_reject_sweep"].copy()

fa_df = fa_df.sort_values("false_accept_rate")
fr_df = fr_df.sort_values("false_reject_rate")

# Remove duplicate FR=0 row if present
fr_df = fr_df.drop_duplicates(
    subset=["false_accept_rate", "false_reject_rate", "sweep_type"],
    keep="first",
)


def savefig(path):
    plt.tight_layout()
    plt.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close()
    print("Saved:", path)


# ---------------------------------------------------------------------
# Figure 1: False accepts reduce grounding and evidence accuracy
# ---------------------------------------------------------------------
plt.figure(figsize=(7.4, 4.8))
plt.plot(
    fa_df["false_accept_rate"],
    fa_df["mean_grounded_claim_rate"],
    marker="o",
    label="Grounded claim rate",
)
plt.plot(
    fa_df["false_accept_rate"],
    fa_df["mean_evidence_accuracy"],
    marker="o",
    label="Evidence accuracy",
)
plt.plot(
    fa_df["false_accept_rate"],
    fa_df["clean_task_rate"],
    marker="o",
    label="Clean task rate",
)
plt.xlabel("Verifier false-accept rate")
plt.ylabel("Rate")
plt.title("False accepts reduce grounded long-form generation")
plt.ylim(0, 1.05)
plt.grid(True, alpha=0.3)
plt.legend()
savefig(FIG_DIR / "experiment6_false_accept_grounding_cleanrate.png")


# ---------------------------------------------------------------------
# Figure 2: False accepts increase contamination
# ---------------------------------------------------------------------
plt.figure(figsize=(7.4, 4.8))
plt.plot(
    fa_df["false_accept_rate"],
    fa_df["mean_downstream_contaminated_claims"],
    marker="o",
    label="Downstream contaminated claims",
)
plt.plot(
    fa_df["false_accept_rate"],
    fa_df["mean_unsafe_prefix_depth"],
    marker="o",
    label="Unsafe prefix depth",
)
plt.xlabel("Verifier false-accept rate")
plt.ylabel("Claims per task")
plt.title("False accepts increase semantic-prefix contamination")
plt.grid(True, alpha=0.3)
plt.legend()
savefig(FIG_DIR / "experiment6_false_accept_contamination.png")


# ---------------------------------------------------------------------
# Figure 3: False rejects increase abstention but not contamination
# ---------------------------------------------------------------------
plt.figure(figsize=(7.4, 4.8))
plt.plot(
    fr_df["false_reject_rate"],
    fr_df["mean_abstention_count"],
    marker="o",
    label="Abstentions",
)
plt.plot(
    fr_df["false_reject_rate"],
    fr_df["mean_downstream_contaminated_claims"],
    marker="o",
    label="Downstream contamination",
)
plt.plot(
    fr_df["false_reject_rate"],
    fr_df["mean_unsafe_prefix_depth"],
    marker="o",
    label="Unsafe prefix depth",
)
plt.xlabel("Verifier false-reject rate")
plt.ylabel("Claims per task")
plt.title("False rejects increase abstention, not contamination")
plt.grid(True, alpha=0.3)
plt.legend()
savefig(FIG_DIR / "experiment6_false_reject_abstention_vs_contamination.png")


# ---------------------------------------------------------------------
# Figure 4: Grounding-contamination frontier
# ---------------------------------------------------------------------
plt.figure(figsize=(6.8, 5.2))
plt.scatter(
    fa_df["mean_downstream_contaminated_claims"],
    fa_df["mean_grounded_claim_rate"],
    s=80,
)

for _, row in fa_df.iterrows():
    label = f"FA={row['false_accept_rate']:.2f}"
    plt.annotate(
        label,
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
plt.title("Grounding drops as contamination increases")
plt.ylim(0, 1.05)
plt.grid(True, alpha=0.3)
savefig(FIG_DIR / "experiment6_grounding_contamination_frontier.png")


# ---------------------------------------------------------------------
# Figure 5: False accepts collapse clean task survival
# ---------------------------------------------------------------------
plt.figure(figsize=(7.4, 4.8))
plt.plot(
    fa_df["false_accept_rate"],
    fa_df["clean_task_rate"],
    marker="o",
)
plt.xlabel("Verifier false-accept rate")
plt.ylabel("Clean task rate")
plt.title("False accepts collapse fully clean long-form outputs")
plt.ylim(0, 1.05)
plt.grid(True, alpha=0.3)
savefig(FIG_DIR / "experiment6_false_accept_clean_task_rate.png")


print(f"\nAll Experiment 6 figures saved at {DPI} dpi.")

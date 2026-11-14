from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


PROJECT = Path(__file__).resolve().parents[1]

summary_path = PROJECT / "results" / "tables" / "experiment4_detector_quality_sweep_summary.csv"
fig_dir = PROJECT / "results" / "figures"
fig_dir.mkdir(parents=True, exist_ok=True)

DPI = 600

df = pd.read_csv(summary_path)

fa_df = df[df["sweep_type"] == "false_accept_sweep"].copy()
fr_df = df[df["sweep_type"] == "false_reject_sweep"].copy()

# Figure 1: False accept vs grounding/evidence accuracy
plt.figure(figsize=(7, 4.5))
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
plt.xlabel("Verifier false-accept rate")
plt.ylabel("Rate")
plt.title("False accepts reduce grounding")
plt.ylim(0, 1.05)
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
out1 = fig_dir / "experiment4_false_accept_grounding.png"
plt.savefig(out1, dpi=DPI, bbox_inches="tight")
plt.close()

# Figure 2: False accept vs contamination
plt.figure(figsize=(7, 4.5))
plt.plot(
    fa_df["false_accept_rate"],
    fa_df["mean_downstream_contaminated_claims"],
    marker="o",
    label="Downstream contamination",
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
plt.tight_layout()
out2 = fig_dir / "experiment4_false_accept_contamination.png"
plt.savefig(out2, dpi=DPI, bbox_inches="tight")
plt.close()

# Figure 3: False reject vs abstention/contamination
plt.figure(figsize=(7, 4.5))
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
plt.xlabel("Verifier false-reject rate")
plt.ylabel("Claims per task")
plt.title("False rejects increase abstention, not contamination")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
out3 = fig_dir / "experiment4_false_reject_abstention.png"
plt.savefig(out3, dpi=DPI, bbox_inches="tight")
plt.close()

print(f"Saved figures at {DPI} dpi:")
print(out1)
print(out2)
print(out3)

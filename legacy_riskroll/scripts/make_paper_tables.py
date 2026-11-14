from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]

TABLE_DIR = PROJECT / "paper_assets" / "tables"
TABLE_DIR.mkdir(parents=True, exist_ok=True)

RESULT_TABLES = PROJECT / "results" / "tables"


EXP3_PATH = RESULT_TABLES / "experiment3_report_identity_summary.csv"
EXP5_PATH = RESULT_TABLES / "experiment5_text_longform_contamination_summary.csv"
EXP6_PATH = RESULT_TABLES / "experiment6_text_noisy_verifier_sweep_summary.csv"


METHOD_ORDER = [
    "Standard RAG",
    "Retrieve-more RAG",
    "Post-hoc correction",
    "CRAG-style correction",
    "RiskRoll",
]


def fmt3(x):
    if pd.isna(x):
        return ""
    return f"{float(x):.3f}"


def dataframe_to_markdown(df):
    """Small markdown table writer so we do not need tabulate."""
    cols = list(df.columns)

    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"

    rows = []
    for _, row in df.iterrows():
        vals = [str(row[c]) for c in cols]
        rows.append("| " + " | ".join(vals) + " |")

    return "\n".join([header, sep] + rows)


def save_all(df, stem):
    csv_path = TABLE_DIR / f"{stem}.csv"
    md_path = TABLE_DIR / f"{stem}.md"
    tex_path = TABLE_DIR / f"{stem}.tex"

    df.to_csv(csv_path, index=False)

    markdown = dataframe_to_markdown(df)
    md_path.write_text(markdown, encoding="utf-8")

    latex = df.to_latex(
        index=False,
        escape=True,
        column_format="l" + "r" * (len(df.columns) - 1),
    )
    tex_path.write_text(latex, encoding="utf-8")

    print("Saved:")
    print(" ", csv_path)
    print(" ", md_path)
    print(" ", tex_path)


def make_main_results_table():
    df = pd.read_csv(EXP5_PATH)

    df["method"] = pd.Categorical(df["method"], categories=METHOD_ORDER, ordered=True)
    df = df.sort_values("method")

    out = pd.DataFrame({
        "Method": df["method"].astype(str),
        "Claim Acc.": df["mean_claim_accuracy"].map(fmt3),
        "Evidence Acc.": df["mean_evidence_accuracy"].map(fmt3),
        "Grounded Rate": df["mean_grounded_claim_rate"].map(fmt3),
        "Wrong Evidence": df["mean_wrong_evidence_count"].map(fmt3),
        "Unsafe Depth": df["mean_unsafe_prefix_depth"].map(fmt3),
        "Clean Task Rate": df["clean_task_rate"].map(fmt3),
        "Rollbacks": df["mean_rollback_count"].map(fmt3),
    })

    save_all(out, "table1_main_text_longform_results")


def make_false_accept_table():
    df = pd.read_csv(EXP6_PATH)
    df = df[df["sweep_type"] == "false_accept_sweep"].copy()
    df = df.sort_values("false_accept_rate")

    out = pd.DataFrame({
        "False Accept Rate": df["false_accept_rate"].map(fmt3),
        "Grounded Rate": df["mean_grounded_claim_rate"].map(fmt3),
        "Evidence Acc.": df["mean_evidence_accuracy"].map(fmt3),
        "Contamination": df["mean_downstream_contaminated_claims"].map(fmt3),
        "Unsafe Depth": df["mean_unsafe_prefix_depth"].map(fmt3),
        "Clean Task Rate": df["clean_task_rate"].map(fmt3),
        "Abstentions": df["mean_abstention_count"].map(fmt3),
    })

    save_all(out, "table2_false_accept_sweep")


def make_false_reject_table():
    df = pd.read_csv(EXP6_PATH)
    df = df[df["sweep_type"] == "false_reject_sweep"].copy()
    df = df.sort_values("false_reject_rate")

    # Remove duplicate FA=0, FR=0 if duplicated.
    df = df.drop_duplicates(
        subset=["false_accept_rate", "false_reject_rate", "sweep_type"],
        keep="first",
    )

    out = pd.DataFrame({
        "False Reject Rate": df["false_reject_rate"].map(fmt3),
        "Grounded Rate": df["mean_grounded_claim_rate"].map(fmt3),
        "Evidence Acc.": df["mean_evidence_accuracy"].map(fmt3),
        "Contamination": df["mean_downstream_contaminated_claims"].map(fmt3),
        "Unsafe Depth": df["mean_unsafe_prefix_depth"].map(fmt3),
        "Clean Task Rate": df["clean_task_rate"].map(fmt3),
        "Abstentions": df["mean_abstention_count"].map(fmt3),
    })

    save_all(out, "table3_false_reject_sweep")


def make_controlled_stress_summary():
    rows = []

    if EXP3_PATH.exists():
        exp3 = pd.read_csv(EXP3_PATH)
        riskroll = exp3[exp3["method"] == "RiskRoll"].iloc[0]
        standard = exp3[exp3["method"] == "Standard RAG"].iloc[0]

        rows.append({
            "Experiment": "Report-identity near-miss",
            "Baseline Grounded": fmt3(standard["mean_grounded_claim_rate"]),
            "RiskRoll Grounded": fmt3(riskroll["mean_grounded_claim_rate"]),
            "Baseline Unsafe Depth": fmt3(standard["mean_unsafe_prefix_depth"]),
            "RiskRoll Unsafe Depth": fmt3(riskroll["mean_unsafe_prefix_depth"]),
            "RiskRoll Rollbacks": fmt3(riskroll["mean_rollback_count"]),
        })

    if EXP5_PATH.exists():
        exp5 = pd.read_csv(EXP5_PATH)
        riskroll = exp5[exp5["method"] == "RiskRoll"].iloc[0]
        standard = exp5[exp5["method"] == "Standard RAG"].iloc[0]

        rows.append({
            "Experiment": "Text long-form contamination",
            "Baseline Grounded": fmt3(standard["mean_grounded_claim_rate"]),
            "RiskRoll Grounded": fmt3(riskroll["mean_grounded_claim_rate"]),
            "Baseline Unsafe Depth": fmt3(standard["mean_unsafe_prefix_depth"]),
            "RiskRoll Unsafe Depth": fmt3(riskroll["mean_unsafe_prefix_depth"]),
            "RiskRoll Rollbacks": fmt3(riskroll["mean_rollback_count"]),
        })

    out = pd.DataFrame(rows)
    save_all(out, "table4_controlled_stress_summary")


def main():
    print("Making paper-ready tables...")
    make_main_results_table()
    make_false_accept_table()
    make_false_reject_table()
    make_controlled_stress_summary()
    print("\nDone. Tables are in:", TABLE_DIR)


if __name__ == "__main__":
    main()

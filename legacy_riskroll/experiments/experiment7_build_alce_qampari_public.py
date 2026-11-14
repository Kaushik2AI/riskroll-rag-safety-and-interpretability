from pathlib import Path
import sys
import json

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from src.data_builders.alce_qampari_adapter import (
    build_qampari_tasks,
    write_jsonl,
    write_json,
)


INPUT_PATH = PROJECT / "external" / "ALCE" / "data" / "qampari_eval_gtr_top100.json"

OUT_DIR = PROJECT / "data" / "public" / "alce_qampari"
REPORT_DIR = PROJECT / "results" / "reports"

OUT_TASKS = OUT_DIR / "alce_qampari_public_tasks.jsonl"
OUT_SAMPLE = OUT_DIR / "alce_qampari_public_sample.json"
OUT_SUMMARY = OUT_DIR / "alce_qampari_public_summary.json"
OUT_REPORT = REPORT_DIR / "EXPERIMENT7_ALCE_QAMPARI_ADAPTER_REPORT.md"


N_TASKS = 100
CLAIMS_PER_TASK = 5
RETRIEVAL_TOP_K = 20


def main():
    tasks, summary = build_qampari_tasks(
        input_path=INPUT_PATH,
        n_tasks=N_TASKS,
        claims_per_task=CLAIMS_PER_TASK,
        retrieval_top_k=RETRIEVAL_TOP_K,
        require_support_in_top100=True,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    write_jsonl(OUT_TASKS, tasks)
    write_json(OUT_SAMPLE, tasks[:3])
    write_json(OUT_SUMMARY, summary)

    report = []
    report.append("# Experiment 7: ALCE-QAMPARI Public Adapter")
    report.append("")
    report.append("## Purpose")
    report.append("")
    report.append(
        "Build a public text-only citation-aware benchmark adapter from ALCE-QAMPARI "
        "into the RiskRoll claim/evidence task format."
    )
    report.append("")
    report.append("## Configuration")
    report.append("")
    report.append(f"- Input file: `{INPUT_PATH}`")
    report.append(f"- Target tasks: {N_TASKS}")
    report.append(f"- Claims per task: {CLAIMS_PER_TASK}")
    report.append(f"- Candidate docs per claim: top-{RETRIEVAL_TOP_K}")
    report.append("")
    report.append("## Summary")
    report.append("")
    for k, v in summary.items():
        report.append(f"- {k}: {v}")
    report.append("")
    report.append("## Interpretation")
    report.append("")
    report.append(
        "Each QAMPARI question is converted into a multi-claim generation task. "
        "Each gold answer item becomes one atomic claim. Candidate evidence is drawn "
        "from the provided ALCE top-100 retrieval results. This gives RiskRoll a public "
        "claim-level citation grounding setting."
    )
    report.append("")
    report.append("## Next step")
    report.append("")
    report.append(
        "Run public-dataset baselines: Standard RAG, Retrieve-more RAG, Post-hoc correction, "
        "CRAG-style correction, and RiskRoll."
    )

    OUT_REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")

    print("=" * 90)
    print("Experiment 7: ALCE-QAMPARI adapter")
    print("=" * 90)
    for k, v in summary.items():
        print(f"{k}: {v}")

    print("")
    print("Saved:")
    print("Tasks:", OUT_TASKS)
    print("Sample:", OUT_SAMPLE)
    print("Summary:", OUT_SUMMARY)
    print("Report:", OUT_REPORT)


if __name__ == "__main__":
    main()

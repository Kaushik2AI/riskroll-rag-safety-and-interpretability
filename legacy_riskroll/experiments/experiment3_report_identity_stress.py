from pathlib import Path
import sys
import json
import csv
import random
from statistics import mean

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from riskroll import EvidenceCandidate, ClaimExample, RiskRollController
from verification import ControlledIdentityVerifier

from baselines.standard_rag import StandardRAGBaseline
from baselines.retrieve_more import RetrieveMoreBaseline
from baselines.posthoc_correction import PostHocCorrectionBaseline
from baselines.crag_style import CRAGStyleBaseline


random.seed(42)

OUT_RAW = PROJECT / "results" / "raw"
OUT_TABLES = PROJECT / "results" / "tables"
OUT_REPORTS = PROJECT / "results" / "reports"

for p in [OUT_RAW, OUT_TABLES, OUT_REPORTS]:
    p.mkdir(parents=True, exist_ok=True)


N_GROUPS = 10
REPORTS_PER_GROUP = 3
TOP_K = 3

CITIES = [
    "Boston", "Austin", "Seattle", "Denver", "Chicago",
    "Phoenix", "Atlanta", "Miami", "Dallas", "Portland",
]

DOMAINS = [
    "solar adoption", "water efficiency", "public transit", "air quality",
    "housing affordability", "digital access", "waste recycling", "green jobs",
    "public health", "green energy",
]


def build_values(base):
    return {
        "2024": base + random.randint(1, 5),
        "2025": base + random.randint(6, 12),
        "highest_year": random.choice(["2023", "2024", "2025"]),
    }


def make_answer_from_values(query_type, values):
    if query_type == "text_2025_score":
        return str(values["2025"])
    if query_type == "table_2024_score":
        return str(values["2024"])
    if query_type == "chart_highest_year":
        return str(values["highest_year"])
    return "UNKNOWN"


def make_evidence(report_id, city, domain, modality, metric, year, query_type, answer):
    if modality == "text":
        content = (
            f"Executive overview for {city} {domain}. "
            f"The {metric} in {year} is reported here. "
            f"Answer: {answer}"
        )
    elif modality == "table":
        content = (
            f"Table for {city} {domain}. "
            f"Metric: {metric}. Year: {year}. "
            f"Answer: {answer}"
        )
    else:
        content = (
            f"Chart for {city} {domain}. "
            f"Metric: {metric}. It shows the highest year. "
            f"Answer: {answer}"
        )

    return EvidenceCandidate(
        evidence_id=f"{report_id}_{modality}_{query_type}",
        content=content,
        modality=modality,
        metadata={
            "report_id": report_id,
            "city": city,
            "domain": domain,
            "modality": modality,
            "metric": metric,
            "year": year,
            "query_type": query_type,
        },
    )


def build_dataset():
    """
    Build groups of near-duplicate reports.

    Within each group:
    - same city
    - same domain
    - same modality
    - same metric
    - same year
    - different report_id
    - different answer

    This makes lexical baselines weak because wrong and gold evidence look almost identical.
    RiskRoll controlled verifier can reject wrong report identity.
    """

    tasks = {}

    for group_idx in range(N_GROUPS):
        city = CITIES[group_idx % len(CITIES)]
        domain = DOMAINS[group_idx % len(DOMAINS)]

        reports = []

        for r in range(REPORTS_PER_GROUP):
            report_id = f"report_g{group_idx:02d}_r{r:02d}"
            base = 40 + group_idx * 5 + r * 11
            values = build_values(base)

            reports.append({
                "report_id": report_id,
                "city": city,
                "domain": domain,
                "values": values,
            })

        for r, report in enumerate(reports):
            report_id = report["report_id"]
            wrong_report = reports[(r + 1) % REPORTS_PER_GROUP]

            examples = []

            claim_specs = [
                {
                    "suffix": "text",
                    "question": (
                        f"According to the executive overview, what score did "
                        f"{city} reach in {domain} by 2025?"
                    ),
                    "modality": "text",
                    "metric": "score",
                    "year": "2025",
                    "query_type": "text_2025_score",
                },
                {
                    "suffix": "table",
                    "question": (
                        f"In the table, what was the {domain} score for {city} in 2024?"
                    ),
                    "modality": "table",
                    "metric": "score",
                    "year": "2024",
                    "query_type": "table_2024_score",
                },
                {
                    "suffix": "chart",
                    "question": (
                        f"In the chart, which year had the highest {domain} score for {city}?"
                    ),
                    "modality": "chart",
                    "metric": "score",
                    "year": "highest_year",
                    "query_type": "chart_highest_year",
                },
            ]

            for spec in claim_specs:
                gold_answer = make_answer_from_values(
                    spec["query_type"],
                    report["values"],
                )

                wrong_answer = make_answer_from_values(
                    spec["query_type"],
                    wrong_report["values"],
                )

                gold_ev = make_evidence(
                    report_id=report_id,
                    city=city,
                    domain=domain,
                    modality=spec["modality"],
                    metric=spec["metric"],
                    year=spec["year"],
                    query_type=spec["query_type"],
                    answer=gold_answer,
                )

                wrong_ev = make_evidence(
                    report_id=wrong_report["report_id"],
                    city=city,
                    domain=domain,
                    modality=spec["modality"],
                    metric=spec["metric"],
                    year=spec["year"],
                    query_type=spec["query_type"],
                    answer=wrong_answer,
                )

                # Another distractor from same group, still wrong.
                other_wrong_report = reports[(r + 2) % REPORTS_PER_GROUP]
                other_wrong_answer = make_answer_from_values(
                    spec["query_type"],
                    other_wrong_report["values"],
                )

                other_wrong_ev = make_evidence(
                    report_id=other_wrong_report["report_id"],
                    city=city,
                    domain=domain,
                    modality=spec["modality"],
                    metric=spec["metric"],
                    year=spec["year"],
                    query_type=spec["query_type"],
                    answer=other_wrong_answer,
                )

                # rank 1 wrong near-miss, rank 2 gold, rank 3 wrong
                candidates = [wrong_ev, gold_ev, other_wrong_ev]

                example = ClaimExample(
                    example_id=f"{report_id}_{spec['suffix']}",
                    question=spec["question"],
                    gold_answer=gold_answer,
                    gold_evidence_id=gold_ev.evidence_id,
                    candidates=candidates,
                    metadata={
                        "report_id": report_id,
                        "city": city,
                        "domain": domain,
                        "modality": spec["modality"],
                        "metric": spec["metric"],
                        "year": spec["year"],
                        "query_type": spec["query_type"],
                    },
                )

                examples.append(example)

            tasks[report_id] = examples

    return tasks


def safe_get(summary, key, default=0):
    return summary.get(key, default)


def run_method_per_task(name, method, tasks):
    rows = []

    for task_id, examples in tasks.items():
        if name == "RiskRoll":
            result = method.run_sequence(examples)
        else:
            result = method.run_batch(examples)

        summary = result["summary"]

        rows.append({
            "task_id": task_id,
            "method": name,
            "claim_accuracy": safe_get(summary, "claim_accuracy"),
            "evidence_accuracy": safe_get(summary, "evidence_accuracy"),
            "grounded_claim_rate": safe_get(summary, "grounded_claim_rate"),
            "wrong_evidence_count": safe_get(summary, "wrong_evidence_count"),
            "unsafe_prefix_depth": safe_get(summary, "unsafe_prefix_depth"),
            "downstream_contaminated_claims": safe_get(summary, "downstream_contaminated_claims"),
            "rollback_count": safe_get(summary, "rollback_count"),
            "repair_count": safe_get(summary, "repair_count"),
            "abstention_count": safe_get(summary, "abstention_count"),
            "verifier_false_accepts": safe_get(summary, "verifier_false_accepts"),
            "verifier_false_rejects": safe_get(summary, "verifier_false_rejects"),
            "records": result.get("records", []),
            "events": result.get("events", []),
        })

    return rows


def aggregate(rows):
    keys = [
        "claim_accuracy",
        "evidence_accuracy",
        "grounded_claim_rate",
        "wrong_evidence_count",
        "unsafe_prefix_depth",
        "downstream_contaminated_claims",
        "rollback_count",
        "repair_count",
        "abstention_count",
        "verifier_false_accepts",
        "verifier_false_rejects",
    ]

    out = {
        "method": rows[0]["method"],
        "n_tasks": len(rows),
        "claims_per_task": 3,
        "total_claims": len(rows) * 3,
    }

    for key in keys:
        out[f"mean_{key}"] = mean(r[key] for r in rows)

    return out


def write_csv(path, rows):
    if not rows:
        return

    fieldnames = list(rows[0].keys())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    print("=" * 80)
    print("Experiment 3: Report-identity near-miss stress test")
    print("=" * 80)

    tasks = build_dataset()
    print("Tasks:", len(tasks))
    print("Total claims:", len(tasks) * 3)

    verifier = ControlledIdentityVerifier(
        required_keys=[
            "report_id",
            "city",
            "domain",
            "modality",
            "metric",
            "year",
        ]
    )

    methods = {
        "Standard RAG": StandardRAGBaseline(),
        "Retrieve-more RAG": RetrieveMoreBaseline(top_k=TOP_K),
        "Post-hoc correction": PostHocCorrectionBaseline(top_k=TOP_K),
        "CRAG-style correction": CRAGStyleBaseline(top_k=TOP_K),
        "RiskRoll": RiskRollController(
            verifier=verifier,
            top_k=TOP_K,
        ),
    }

    all_rows = []
    summary_rows = []

    for name, method in methods.items():
        rows = run_method_per_task(name, method, tasks)
        all_rows.extend(rows)
        summary_rows.append(aggregate(rows))

    raw_path = OUT_RAW / "experiment3_report_identity_rows.json"
    summary_csv = OUT_TABLES / "experiment3_report_identity_summary.csv"
    report_path = OUT_REPORTS / "EXPERIMENT3_REPORT_IDENTITY_REPORT.md"

    # JSON with full records/events
    raw_path.write_text(
        json.dumps(all_rows, indent=2),
        encoding="utf-8",
    )

    # CSV summary
    write_csv(summary_csv, summary_rows)

    print("\nSummary:")
    for row in summary_rows:
        print(
            f"{row['method']:<24} "
            f"claim_acc={row['mean_claim_accuracy']:.3f} | "
            f"evidence_acc={row['mean_evidence_accuracy']:.3f} | "
            f"grounded={row['mean_grounded_claim_rate']:.3f} | "
            f"wrong_ev={row['mean_wrong_evidence_count']:.3f} | "
            f"unsafe_depth={row['mean_unsafe_prefix_depth']:.3f} | "
            f"rollbacks={row['mean_rollback_count']:.3f}"
        )

    lines = []
    lines.append("# Experiment 3: Report-Identity Near-Miss Stress Test")
    lines.append("")
    lines.append("## Goal")
    lines.append("")
    lines.append(
        "Test a hard controlled setting where wrong evidence shares the same "
        "city, domain, modality, metric, and year as the gold evidence, but comes "
        "from the wrong report identity."
    )
    lines.append("")
    lines.append("## Why this matters")
    lines.append("")
    lines.append(
        "Lexical evidence selection can fail because wrong and gold candidates look "
        "nearly identical. RiskRoll uses a controlled identity verifier to reject "
        "wrong-report evidence before committing a claim."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Method | Claim Acc | Evidence Acc | Grounded Rate | Wrong Evidence | Unsafe Depth | Rollbacks |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")

    for row in summary_rows:
        lines.append(
            f"| {row['method']} | "
            f"{row['mean_claim_accuracy']:.3f} | "
            f"{row['mean_evidence_accuracy']:.3f} | "
            f"{row['mean_grounded_claim_rate']:.3f} | "
            f"{row['mean_wrong_evidence_count']:.3f} | "
            f"{row['mean_unsafe_prefix_depth']:.3f} | "
            f"{row['mean_rollback_count']:.3f} |"
        )

    report_path.write_text("\n".join(lines), encoding="utf-8")

    print("\nSaved:")
    print("Raw rows:", raw_path)
    print("Summary:", summary_csv)
    print("Report:", report_path)


if __name__ == "__main__":
    main()

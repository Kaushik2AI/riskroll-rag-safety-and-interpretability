from __future__ import annotations

import random

from riskroll import EvidenceCandidate, ClaimExample


CITIES = [
    "Boston", "Austin", "Seattle", "Denver", "Chicago",
    "Phoenix", "Atlanta", "Miami", "Dallas", "Portland",
]

DOMAINS = [
    "solar adoption", "water efficiency", "public transit", "air quality",
    "housing affordability", "digital access", "waste recycling", "green jobs",
    "public health", "green energy",
]


def _build_values(base: int, rng: random.Random) -> dict[str, int | str]:
    return {
        "2024": base + rng.randint(1, 5),
        "2025": base + rng.randint(6, 12),
        "highest_year": rng.choice(["2023", "2024", "2025"]),
    }


def _make_answer(query_type: str, values: dict[str, int | str]) -> str:
    if query_type == "text_2025_score":
        return str(values["2025"])
    if query_type == "table_2024_score":
        return str(values["2024"])
    if query_type == "chart_highest_year":
        return str(values["highest_year"])
    return "UNKNOWN"


def _make_evidence(
    report_id: str,
    city: str,
    domain: str,
    modality: str,
    metric: str,
    year: str,
    query_type: str,
    answer: str,
) -> EvidenceCandidate:
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


def build_report_identity_tasks(
    n_groups: int = 10,
    reports_per_group: int = 3,
    seed: int = 42,
) -> dict[str, list[ClaimExample]]:
    if n_groups <= 0:
        raise ValueError("n_groups must be greater than zero.")

    if reports_per_group < 3:
        raise ValueError(
            "reports_per_group must be at least 3 because each task uses "
            "one gold report and two distractor reports."
        )

    rng = random.Random(seed)
    tasks: dict[str, list[ClaimExample]] = {}

    claim_specs = [
        {
            "suffix": "text",
            "question_template": (
                "According to the executive overview, what score did "
                "{city} reach in {domain} by 2025?"
            ),
            "modality": "text",
            "metric": "score",
            "year": "2025",
            "query_type": "text_2025_score",
        },
        {
            "suffix": "table",
            "question_template": (
                "In the table, what was the {domain} score for {city} in 2024?"
            ),
            "modality": "table",
            "metric": "score",
            "year": "2024",
            "query_type": "table_2024_score",
        },
        {
            "suffix": "chart",
            "question_template": (
                "In the chart, which year had the highest "
                "{domain} score for {city}?"
            ),
            "modality": "chart",
            "metric": "score",
            "year": "highest_year",
            "query_type": "chart_highest_year",
        },
    ]

    for group_idx in range(n_groups):
        city = CITIES[group_idx % len(CITIES)]
        domain = DOMAINS[group_idx % len(DOMAINS)]

        reports = []

        for report_index in range(reports_per_group):
            report_id = f"report_g{group_idx:02d}_r{report_index:02d}"
            base = 40 + group_idx * 5 + report_index * 11

            reports.append(
                {
                    "report_id": report_id,
                    "city": city,
                    "domain": domain,
                    "values": _build_values(base, rng),
                }
            )

        for report_index, report in enumerate(reports):
            wrong_report = reports[
                (report_index + 1) % reports_per_group
            ]
            other_wrong_report = reports[
                (report_index + 2) % reports_per_group
            ]

            examples: list[ClaimExample] = []

            for spec in claim_specs:
                query_type = spec["query_type"]

                gold_answer = _make_answer(
                    query_type,
                    report["values"],
                )
                wrong_answer = _make_answer(
                    query_type,
                    wrong_report["values"],
                )
                other_wrong_answer = _make_answer(
                    query_type,
                    other_wrong_report["values"],
                )

                gold_evidence = _make_evidence(
                    report_id=report["report_id"],
                    city=city,
                    domain=domain,
                    modality=spec["modality"],
                    metric=spec["metric"],
                    year=spec["year"],
                    query_type=query_type,
                    answer=gold_answer,
                )

                wrong_evidence = _make_evidence(
                    report_id=wrong_report["report_id"],
                    city=city,
                    domain=domain,
                    modality=spec["modality"],
                    metric=spec["metric"],
                    year=spec["year"],
                    query_type=query_type,
                    answer=wrong_answer,
                )

                other_wrong_evidence = _make_evidence(
                    report_id=other_wrong_report["report_id"],
                    city=city,
                    domain=domain,
                    modality=spec["modality"],
                    metric=spec["metric"],
                    year=spec["year"],
                    query_type=query_type,
                    answer=other_wrong_answer,
                )

                examples.append(
                    ClaimExample(
                        example_id=(
                            f"{report['report_id']}_{spec['suffix']}"
                        ),
                        question=spec["question_template"].format(
                            city=city,
                            domain=domain,
                        ),
                        gold_answer=gold_answer,
                        gold_evidence_id=gold_evidence.evidence_id,
                        candidates=[
                            wrong_evidence,
                            gold_evidence,
                            other_wrong_evidence,
                        ],
                        metadata={
                            "report_id": report["report_id"],
                            "city": city,
                            "domain": domain,
                            "modality": spec["modality"],
                            "metric": spec["metric"],
                            "year": spec["year"],
                            "query_type": query_type,
                        },
                    )
                )

            tasks[report["report_id"]] = examples

    return tasks

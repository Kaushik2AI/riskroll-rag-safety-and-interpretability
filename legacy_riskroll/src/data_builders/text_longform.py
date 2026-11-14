import random
from typing import Dict, List, Any

from riskroll.schemas import EvidenceCandidate, ClaimExample


CITIES = [
    "Boston", "Austin", "Seattle", "Denver", "Chicago",
    "Phoenix", "Atlanta", "Miami", "Dallas", "Portland",
]

DOMAINS = [
    "renewable energy", "public transit", "water efficiency", "air quality",
    "housing affordability", "digital access", "waste recycling", "green jobs",
    "public health", "climate adaptation",
]


CLAIM_SPECS = [
    {
        "claim_name": "revenue_2024",
        "metric": "revenue",
        "year": "2024",
        "question_template": "What was the 2024 revenue for the target {city} {domain} report?",
    },
    {
        "claim_name": "profit_2024",
        "metric": "profit",
        "year": "2024",
        "question_template": "What was the 2024 profit for the target {city} {domain} report?",
    },
    {
        "claim_name": "margin_2024",
        "metric": "margin",
        "year": "2024",
        "question_template": "What was the 2024 margin for the target {city} {domain} report?",
    },
    {
        "claim_name": "risk_level",
        "metric": "risk_level",
        "year": "2024",
        "question_template": "What risk level was assigned in the target {city} {domain} report?",
    },
    {
        "claim_name": "recommendation",
        "metric": "recommendation",
        "year": "2024",
        "question_template": "What final recommendation was made in the target {city} {domain} report?",
    },
]


def _make_values(base: int, report_variant: int) -> Dict[str, str]:
    revenue = base + 10 + report_variant * 13
    profit = base // 2 + 5 + report_variant * 7
    margin = round((profit / revenue) * 100, 1)

    risk_levels = ["low", "medium", "high"]
    recommendations = ["expand", "monitor", "pause"]

    return {
        "revenue": str(revenue),
        "profit": str(profit),
        "margin": str(margin),
        "risk_level": risk_levels[report_variant % len(risk_levels)],
        "recommendation": recommendations[report_variant % len(recommendations)],
    }


def _make_evidence(
    report_id: str,
    city: str,
    domain: str,
    claim_name: str,
    metric: str,
    year: str,
    answer: str,
) -> EvidenceCandidate:
    """
    Intentionally do NOT place report_id in the text content.

    This creates hard near-miss evidence:
    - wrong and gold passages look lexically similar
    - report identity is available only through metadata
    - lexical post-hoc / CRAG-style baselines cannot easily distinguish
    - RiskRoll verifier can reject wrong report_id
    """

    content = (
        f"Evidence passage for the {city} {domain} analysis. "
        f"The {year} {metric} field is stated in this passage. "
        f"Answer: {answer}"
    )

    return EvidenceCandidate(
        evidence_id=f"{report_id}_{claim_name}",
        content=content,
        modality="text",
        metadata={
            "report_id": report_id,
            "city": city,
            "domain": domain,
            "claim_name": claim_name,
            "metric": metric,
            "year": year,
            "modality": "text",
        },
    )


def build_text_longform_tasks(
    n_groups: int = 20,
    reports_per_group: int = 3,
    seed: int = 7,
) -> Dict[str, List[ClaimExample]]:
    """
    Build long-form text-only RAG tasks.

    Each task is a sequence of 5 claims about one hidden target report.
    Each claim has:
    - rank 1 wrong near-miss evidence from another report
    - rank 2 gold evidence
    - rank 3 another wrong near-miss evidence

    This tests semantic-prefix contamination in long-form RAG.
    """

    random.seed(seed)
    tasks = {}

    for group_idx in range(n_groups):
        city = CITIES[group_idx % len(CITIES)]
        domain = DOMAINS[group_idx % len(DOMAINS)]

        reports = []

        for r in range(reports_per_group):
            report_id = f"text_report_g{group_idx:02d}_r{r:02d}"
            base = 80 + group_idx * 8
            values = _make_values(base=base, report_variant=r)

            reports.append({
                "report_id": report_id,
                "city": city,
                "domain": domain,
                "values": values,
            })

        for r, target_report in enumerate(reports):
            target_report_id = target_report["report_id"]
            wrong_report_1 = reports[(r + 1) % reports_per_group]
            wrong_report_2 = reports[(r + 2) % reports_per_group]

            examples = []

            for step_id, spec in enumerate(CLAIM_SPECS, start=1):
                claim_name = spec["claim_name"]
                metric = spec["metric"]
                year = spec["year"]

                gold_answer = target_report["values"][metric]
                wrong_answer_1 = wrong_report_1["values"][metric]
                wrong_answer_2 = wrong_report_2["values"][metric]

                gold_ev = _make_evidence(
                    report_id=target_report_id,
                    city=city,
                    domain=domain,
                    claim_name=claim_name,
                    metric=metric,
                    year=year,
                    answer=gold_answer,
                )

                wrong_ev_1 = _make_evidence(
                    report_id=wrong_report_1["report_id"],
                    city=city,
                    domain=domain,
                    claim_name=claim_name,
                    metric=metric,
                    year=year,
                    answer=wrong_answer_1,
                )

                wrong_ev_2 = _make_evidence(
                    report_id=wrong_report_2["report_id"],
                    city=city,
                    domain=domain,
                    claim_name=claim_name,
                    metric=metric,
                    year=year,
                    answer=wrong_answer_2,
                )

                question = spec["question_template"].format(
                    city=city,
                    domain=domain,
                )

                examples.append(
                    ClaimExample(
                        example_id=f"{target_report_id}_claim{step_id}_{claim_name}",
                        question=question,
                        gold_answer=gold_answer,
                        gold_evidence_id=gold_ev.evidence_id,
                        candidates=[
                            wrong_ev_1,
                            gold_ev,
                            wrong_ev_2,
                        ],
                        metadata={
                            "report_id": target_report_id,
                            "city": city,
                            "domain": domain,
                            "claim_name": claim_name,
                            "metric": metric,
                            "year": year,
                            "modality": "text",
                            "step_id": step_id,
                        },
                    )
                )

            tasks[target_report_id] = examples

    return tasks

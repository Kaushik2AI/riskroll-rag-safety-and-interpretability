from pathlib import Path
import csv


PROJECT = Path(__file__).resolve().parents[1]

OUT_DIR = PROJECT / "paper_assets" / "literature"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUT_DIR / "related_work_matrix.csv"
MD_PATH = OUT_DIR / "related_work_matrix.md"
TEX_PATH = OUT_DIR / "related_work_matrix.tex"
NOTES_PATH = OUT_DIR / "base_paper_decision.md"


rows = [
    {
        "Paper": "FLARE / Active Retrieval Augmented Generation",
        "Year": "2023",
        "Role in our paper": "Active retrieval baseline / related work",
        "Core idea": "Actively decides when and what to retrieve during long-form generation.",
        "Datasets / setting": "Long-form generation and knowledge-intensive QA settings.",
        "Metrics": "Task correctness, factuality, retrieval/generation quality depending on task.",
        "Limitation for our gap": "Retrieves during generation, but does not define a trusted semantic prefix or rollback unsafe committed claims.",
        "How RiskRoll differs": "RiskRoll controls claim commitment: unsupported claims are rolled back before entering the trusted prefix.",
        "Baseline status": "Implement as optional FLARE-style baseline if time permits; cite as key active-retrieval anchor.",
        "URL": "https://aclanthology.org/2023.emnlp-main.495/",
    },
    {
        "Paper": "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection",
        "Year": "2024",
        "Role in our paper": "Self-reflective RAG related work / optional baseline",
        "Core idea": "Trains a model to retrieve, generate, and critique using reflection tokens.",
        "Datasets / setting": "Open-domain QA, reasoning, fact verification, and long-form generation style tasks.",
        "Metrics": "Task accuracy, citation/factuality style metrics depending on dataset.",
        "Limitation for our gap": "Uses learned self-reflection, but does not explicitly rollback the answer to the last trusted semantic prefix.",
        "How RiskRoll differs": "RiskRoll is an inference-time controller that separates candidate claims from trusted committed claims.",
        "Baseline status": "Cite as key self-critique RAG anchor; implement only if time and code availability allow.",
        "URL": "https://openreview.net/forum?id=hSyW5go0v8",
    },
    {
        "Paper": "CRAG / Corrective Retrieval Augmented Generation",
        "Year": "2024",
        "Role in our paper": "Closest retrieval-correction baseline",
        "Core idea": "Evaluates retrieved document quality and triggers corrective retrieval actions when retrieval is poor.",
        "Datasets / setting": "Short-form and long-form RAG tasks with retrieval-quality failures.",
        "Metrics": "Generation accuracy and robustness under retrieval failure.",
        "Limitation for our gap": "Correction happens at retrieval-set level, not at the level of committing generated claims to a trusted prefix.",
        "How RiskRoll differs": "RiskRoll verifies claim-evidence support before semantic commitment and rolls back unsafe candidate spans.",
        "Baseline status": "Already implemented as CRAG-style evidence correction.",
        "URL": "https://arxiv.org/abs/2401.15884",
    },
    {
        "Paper": "RARR: Researching and Revising What Language Models Say",
        "Year": "2023",
        "Role in our paper": "Closest post-hoc revision baseline",
        "Core idea": "Finds attribution for generated output and post-edits unsupported content while preserving the original answer.",
        "Datasets / setting": "Attribution and factuality repair for generated text.",
        "Metrics": "Attribution quality, factuality, preservation of original response.",
        "Limitation for our gap": "Repair happens after generation; unsupported claims may already have influenced later text.",
        "How RiskRoll differs": "RiskRoll prevents unsupported claims from entering the trusted prefix in the first place.",
        "Baseline status": "Our post-hoc correction baseline approximates this category; cite directly.",
        "URL": "https://aclanthology.org/2023.acl-long.910/",
    },
    {
        "Paper": "FActScore: Fine-grained Atomic Evaluation of Factual Precision",
        "Year": "2023",
        "Role in our paper": "Evaluation foundation",
        "Core idea": "Breaks long-form generations into atomic facts and computes the percentage supported by reliable sources.",
        "Datasets / setting": "Long-form biography generation and factuality evaluation.",
        "Metrics": "Atomic fact support percentage.",
        "Limitation for our gap": "Evaluation framework, not a generation-time rollback method.",
        "How RiskRoll differs": "RiskRoll uses claim-level verification as an inference-time control action, not only as an evaluation.",
        "Baseline status": "Use to justify atomic-claim evaluation and supported-claim metrics.",
        "URL": "https://aclanthology.org/2023.emnlp-main.741/",
    },
    {
        "Paper": "LongFact / SAFE: Long-form factuality in large language models",
        "Year": "2024",
        "Role in our paper": "Long-form factuality evaluation anchor",
        "Core idea": "Creates long-form factuality prompts and evaluates generated facts using a search-augmented factuality evaluator.",
        "Datasets / setting": "Open-domain long-form factuality across many topics.",
        "Metrics": "SAFE factual precision/recall/F1-style measures.",
        "Limitation for our gap": "Evaluates factuality after generation; does not rollback unsafe claims during generation.",
        "How RiskRoll differs": "RiskRoll uses verification before commitment to prevent contamination while generating.",
        "Baseline status": "Use as public benchmark/evaluation candidate if implementation is feasible.",
        "URL": "https://arxiv.org/abs/2403.18802",
    },
    {
        "Paper": "VeriScore: Evaluating factuality of verifiable claims in long-form generation",
        "Year": "2024",
        "Role in our paper": "Evaluation foundation for verifiable claims",
        "Core idea": "Evaluates factuality in diverse long-form generation tasks containing verifiable and unverifiable content.",
        "Datasets / setting": "Multiple long-form generation tasks.",
        "Metrics": "Claim extraction and factuality score for verifiable claims.",
        "Limitation for our gap": "Evaluation metric, not rollback/recovery method.",
        "How RiskRoll differs": "RiskRoll actively manages which claims enter the trusted prefix.",
        "Baseline status": "Use to justify verifiable-claim-level evaluation.",
        "URL": "https://aclanthology.org/2024.findings-emnlp.552/",
    },
    {
        "Paper": "ALCE: Enabling LLMs to Generate Text with Citations",
        "Year": "2023",
        "Role in our paper": "Best public dataset candidate",
        "Core idea": "Benchmark for citation-aware generation with ASQA, QAMPARI, and ELI5.",
        "Datasets / setting": "ASQA, QAMPARI, ELI5.",
        "Metrics": "Fluency, correctness, citation quality.",
        "Limitation for our gap": "Benchmark/evaluation setup, not a rollback generation method.",
        "How RiskRoll differs": "RiskRoll can be tested as a claim/citation commitment controller on citation-aware long-form QA.",
        "Baseline status": "Recommended next public benchmark adapter.",
        "URL": "https://github.com/princeton-nlp/ALCE",
    },
    {
        "Paper": "RAGChecker: Fine-grained Framework for Diagnosing RAG",
        "Year": "2024",
        "Role in our paper": "Diagnostic evaluation related work",
        "Core idea": "Diagnoses retrieval and generation modules in RAG systems with fine-grained metrics.",
        "Datasets / setting": "RAG evaluation across retrieval and generation diagnostics.",
        "Metrics": "Retrieval and generation diagnostic metrics.",
        "Limitation for our gap": "Diagnoses RAG errors, but does not propose claim-level rollback control.",
        "How RiskRoll differs": "RiskRoll is an intervention/controller; RAGChecker is mainly diagnostic.",
        "Baseline status": "Cite for fine-grained RAG evaluation motivation.",
        "URL": "https://papers.nips.cc/paper_files/paper/2024/hash/27245589131d17368cccdfa990cbf16e-Abstract-Datasets_and_Benchmarks_Track.html",
    },
]


def write_csv(path, rows):
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def rows_to_markdown(rows):
    cols = [
        "Paper",
        "Year",
        "Role in our paper",
        "Core idea",
        "Limitation for our gap",
        "How RiskRoll differs",
        "Baseline status",
    ]

    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")

    for row in rows:
        values = [str(row[c]).replace("\n", " ") for c in cols]
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)


def rows_to_latex(rows):
    cols = [
        "Paper",
        "Year",
        "Role in our paper",
        "Limitation for our gap",
        "How RiskRoll differs",
    ]

    lines = []
    lines.append("\\begin{tabular}{p{3.2cm}p{0.9cm}p{3.0cm}p{4.0cm}p{4.0cm}}")
    lines.append("\\toprule")
    lines.append(" & ".join(cols) + " \\\\")
    lines.append("\\midrule")

    for row in rows:
        vals = []
        for c in cols:
            v = str(row[c])
            v = v.replace("&", "\\&").replace("_", "\\_").replace("%", "\\%")
            vals.append(v)
        lines.append(" & ".join(vals) + " \\\\")

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    return "\n".join(lines)


base_decision = """
# Base-paper decision for RiskRoll-RAG

RiskRoll-RAG should not be framed as being based on one single prior paper. It is best framed as an inference-time control layer at the intersection of active retrieval, corrective RAG, post-hoc revision, self-reflective RAG, and claim-level factuality evaluation.

## Closest anchors

1. FLARE / Active RAG:
   - Closest active-retrieval anchor.
   - It retrieves during generation, but does not rollback a semantic answer prefix.

2. CRAG:
   - Closest retrieval-correction baseline.
   - It evaluates retrieval quality, but does not decide whether a generated claim may enter a trusted prefix.

3. RARR:
   - Closest post-hoc revision baseline.
   - It fixes unsupported output after generation, while RiskRoll acts before unsafe content is committed.

4. Self-RAG:
   - Closest self-reflective RAG anchor.
   - It trains retrieval and critique behavior, but RiskRoll is an inference-time commit/rollback controller.

5. FActScore / LongFact-SAFE / VeriScore:
   - Evaluation foundations.
   - They justify atomic claim decomposition and evidence support checking, but they are not rollback methods.

## Working novelty claim

Existing RAG systems improve evidence access, self-critique, retrieval correction, or post-hoc revision. However, long-form RAG also has a state-contamination failure mode: once an unsupported claim is committed into the generated prefix, later claims may be conditioned on that unsafe state. RiskRoll-RAG introduces a trusted semantic prefix and an inference-time commit/rollback policy that verifies each claim before semantic commitment, rolls back unsafe candidate spans, repairs with targeted evidence, and continues generation from the last trusted state.

## Baseline decision

Required baselines:
- Standard RAG
- Retrieve-more RAG
- CRAG-style evidence correction
- Post-hoc correction / RARR-style revision
- RiskRoll-RAG

Optional stronger baselines:
- FLARE-style active retrieval
- Self-RAG-style self-critique
- RARR implementation if time permits

## Next public benchmark decision

Recommended next public benchmark:
- ALCE-QAMPARI or ALCE-ASQA

Reason:
- Citation-aware long-form QA aligns with claim/evidence commitment.
- It provides correctness and citation quality metrics.
- It is easier than multimodal verification and closer to our text-only RiskRoll story.
""".strip()


def main():
    write_csv(CSV_PATH, rows)
    MD_PATH.write_text(rows_to_markdown(rows), encoding="utf-8")
    TEX_PATH.write_text(rows_to_latex(rows), encoding="utf-8")
    NOTES_PATH.write_text(base_decision + "\n", encoding="utf-8")

    print("Saved:")
    print(CSV_PATH)
    print(MD_PATH)
    print(TEX_PATH)
    print(NOTES_PATH)


if __name__ == "__main__":
    main()

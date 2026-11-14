from pathlib import Path
from datetime import datetime

PROJECT = Path(__file__).resolve().parents[1]
TEXT_DIR = PROJECT / "paper_assets" / "text"
TABLE_DIR = PROJECT / "paper_assets" / "tables"
FIG_DIR = PROJECT / "results" / "figures"

OUT_PATH = TEXT_DIR / "aaai_full_paper_draft.md"
INVENTORY_PATH = TEXT_DIR / "aaai_paper_assets_inventory.md"


def read_section(filename: str, fallback_title: str) -> str:
    path = TEXT_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return f"# {fallback_title}\n\nTODO: Write this section.\n"


def file_exists(path: Path) -> str:
    return "YES" if path.exists() else "MISSING"


def main():
    sections = {
        "abstract": read_section("aaai_abstract_section_draft.md", "Abstract"),
        "intro": read_section("aaai_introduction_section_draft.md", "Introduction"),
        "related": read_section("aaai_related_work_section_draft.md", "Related Work"),
        "method": read_section("aaai_method_section_draft.md", "Method"),
        "setup": read_section("aaai_experiment_setup_section_draft.md", "Experimental Setup"),
        "results": read_section("aaai_results_section_draft.md", "Results"),
        "overhead": read_section("overhead_and_safety_cost_paragraph.md", "Overhead and Safety Cost"),
        "limitations": read_section("aaai_limitations_section_draft.md", "Limitations and Threats to Validity"),
        "conclusion": read_section("aaai_conclusion_section_draft.md", "Conclusion"),
    }

    table_paths = [
        TABLE_DIR / "table1_main_text_longform_results.md",
        TABLE_DIR / "table2_false_accept_sweep.md",
        TABLE_DIR / "table3_false_reject_sweep.md",
        TABLE_DIR / "table5_alce_qampari_public_diagnostic.md",
        TABLE_DIR / "table6_alce_qampari_commit_policy.md",
        TABLE_DIR / "table7_alce_qampari_qwen7b_llm_generation_100.md",
        TABLE_DIR / "table8_alce_asqa_qwen7b_llm_generation_73.md",
        TABLE_DIR / "table9_combined_public_llm_results.md",
        TABLE_DIR / "table10_public_llm_overhead_and_safety_cost.md",
    ]

    figure_paths = [
        FIG_DIR / "experiment5_grounded_claim_rate.png",
        FIG_DIR / "experiment5_unsafe_prefix_depth.png",
        FIG_DIR / "experiment6_false_accept_contamination.png",
        FIG_DIR / "experiment6_grounding_contamination_frontier.png",
        FIG_DIR / "experiment7d_qwen7b_answer_f1.png",
        FIG_DIR / "experiment7d_qwen7b_strict_grounded_rate.png",
        FIG_DIR / "experiment7d_qwen7b_unsupported_commits.png",
        FIG_DIR / "experiment8d_asqa_claim_accuracy.png",
        FIG_DIR / "experiment8d_asqa_strict_grounded_rate.png",
        FIG_DIR / "experiment8d_asqa_support_rate.png",
        FIG_DIR / "combined_public_llm_quality.png",
        FIG_DIR / "combined_public_llm_strict_grounded.png",
        FIG_DIR / "combined_public_llm_unsupported_commits.png",
        FIG_DIR / "combined_public_llm_quality_vs_unsupported.png",
    ]

    inventory_lines = []
    inventory_lines.append("# AAAI Paper Assets Inventory")
    inventory_lines.append("")
    inventory_lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    inventory_lines.append("")
    inventory_lines.append("## Tables")
    inventory_lines.append("")
    for p in table_paths:
        inventory_lines.append(f"- {file_exists(p)}: `{p.relative_to(PROJECT)}`")
    inventory_lines.append("")
    inventory_lines.append("## Figures")
    inventory_lines.append("")
    for p in figure_paths:
        inventory_lines.append(f"- {file_exists(p)}: `{p.relative_to(PROJECT)}`")
    inventory_lines.append("")
    INVENTORY_PATH.write_text("\n".join(inventory_lines), encoding="utf-8")

    full = []
    full.append("# RiskRoll-RAG: Inference-Time Rollback for Safer Long-Form Retrieval-Augmented Generation")
    full.append("")
    full.append("**Draft status:** first complete AAAI-style paper draft.")
    full.append("")
    full.append("**Core claim:** Long-form RAG needs verify-before-commit control. RiskRoll maintains a trusted semantic prefix and rolls back unsafe claims before they contaminate later generation.")
    full.append("")
    full.append("---")
    full.append("")
    full.append(sections["abstract"].replace("# Abstract", "## Abstract"))
    full.append("")
    full.append("---")
    full.append("")
    full.append(sections["intro"].replace("# Introduction", "## Introduction"))
    full.append("")
    full.append("---")
    full.append("")
    full.append(sections["related"].replace("# Related Work", "## Related Work"))
    full.append("")
    full.append("---")
    full.append("")
    full.append(sections["method"].replace("# Method: RiskRoll-RAG", "## Method: RiskRoll-RAG"))
    full.append("")
    full.append("---")
    full.append("")
    full.append(sections["setup"].replace("# Experimental Setup", "## Experimental Setup"))
    full.append("")
    full.append("---")
    full.append("")
    full.append(sections["results"].replace("# Results", "## Results"))
    full.append("")
    full.append("---")
    full.append("")
    full.append(sections["overhead"].replace("# Overhead and Safety-Cost Summary", "## Overhead and Safety-Cost Summary"))
    full.append("")
    full.append("---")
    full.append("")
    full.append(sections["limitations"].replace("# Limitations and Threats to Validity", "## Limitations and Threats to Validity"))
    full.append("")
    full.append("---")
    full.append("")
    full.append(sections["conclusion"].replace("# Conclusion", "## Conclusion"))
    full.append("")
    full.append("---")
    full.append("")
    full.append("## Paper Tables to Include")
    full.append("")
    full.append("Recommended main-paper tables:")
    full.append("")
    full.append("1. **Main controlled stress test table**: `table1_main_text_longform_results`")
    full.append("2. **Verifier sweep table/figure**: `table2_false_accept_sweep`, `table3_false_reject_sweep`")
    full.append("3. **Public LLM combined table**: `table9_combined_public_llm_results`")
    full.append("4. **Overhead and safety-cost table**: `table10_public_llm_overhead_and_safety_cost`")
    full.append("")
    full.append("Optional appendix tables:")
    full.append("")
    full.append("- `table5_alce_qampari_public_diagnostic`")
    full.append("- `table6_alce_qampari_commit_policy`")
    full.append("- `table7_alce_qampari_qwen7b_llm_generation_100`")
    full.append("- `table8_alce_asqa_qwen7b_llm_generation_73`")
    full.append("")
    full.append("## Paper Figures to Include")
    full.append("")
    full.append("Recommended main-paper figures:")
    full.append("")
    full.append("1. RiskRoll workflow diagram")
    full.append("2. Controlled stress test: grounded rate and unsafe prefix depth")
    full.append("3. Noisy verifier sweep: false accept contamination curve")
    full.append("4. Combined public LLM: unsupported commits and safety-quality tradeoff")
    full.append("")
    full.append("## Writing TODO")
    full.append("")
    full.append("- Add formal citations to Related Work.")
    full.append("- Convert this markdown draft into AAAI LaTeX.")
    full.append("- Reduce length to fit AAAI page budget.")
    full.append("- Move diagnostic tables and extended error analysis to appendix.")
    full.append("- Add concise algorithm box from `paper_assets/algorithms/algorithm1_riskroll.tex`.")
    full.append("- Add one clear method diagram.")
    full.append("- Polish abstract after final page-length pass.")
    full.append("")
    full.append("## Citation TODO")
    full.append("")
    full.append("Need citations for:")
    full.append("")
    full.append("- Retrieval-Augmented Generation / RAG")
    full.append("- ALCE benchmark")
    full.append("- ASQA")
    full.append("- QAMPARI")
    full.append("- CRAG or corrective RAG")
    full.append("- Claim-level factuality / verification")
    full.append("- Selective generation / abstention / conformal RAG")
    full.append("- Hallucination cascades / long-form factuality")
    full.append("- Qwen2.5 technical report/model card")
    full.append("")

    OUT_PATH.write_text("\n".join(full), encoding="utf-8")

    print("Saved full AAAI draft:")
    print(OUT_PATH)
    print("")
    print("Saved assets inventory:")
    print(INVENTORY_PATH)
    print("")
    print("Draft word count:")
    text = OUT_PATH.read_text(encoding="utf-8")
    words = text.split()
    print(len(words))
    print("")
    print("Asset inventory preview:")
    print(INVENTORY_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()

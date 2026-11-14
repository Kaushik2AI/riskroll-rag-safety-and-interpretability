# RiskRoll-RAG: Variance-Adaptive Semantic Rollback for Long-Form Retrieval-Augmented Generation

This repository contains the implementation and experimental artifacts for **RiskRoll-RAG**, a retrieval-augmented generation framework that improves factual reliability by rolling back generation to the last trusted semantic prefix whenever unsupported or high-risk claims are detected.

The repository includes the implementation, evaluation code, datasets used in the experiments, and scripts required to reproduce the results reported in the paper.

---

# Repository Structure

```
legacy_riskroll/
│
├── data/                     # Processed public ALCE-QAMPARI inputs
├── experiments/              # Experiment entry points (3–8d)
├── scripts/                  # Figure / table generation from saved results
├── paper_assets/             # Paper tables, figures, ablation, bootstrap CIs, drafts
├── results/                  # raw/ JSON, tables/ CSV, reports/ MD, figures/ PNG
├── src/
│   ├── baselines/
│   ├── data_builders/
│   ├── evaluation/
│   ├── riskroll/
│   ├── utils/
│   └── verification/
│
├── requirements.txt
└── README.md
```

---

# Method Overview

RiskRoll-RAG improves long-form Retrieval-Augmented Generation by introducing a semantic rollback mechanism.

Instead of continuing generation after an unsupported statement, the framework:

1. Retrieves supporting evidence.
2. Verifies each generated claim.
3. Commits only supported claims to a trusted semantic prefix.
4. Detects unsupported or risky claims.
5. Rolls generation back to the most recent trusted prefix.
6. Performs targeted retrieval for the unsupported span.
7. Repairs only the affected portion before continuing generation.

This reduces hallucinated claims while avoiding unnecessary regeneration of already verified content.

---

# Baselines

The repository includes implementations of the following methods:

- Standard Retrieval-Augmented Generation
- Retrieve-More
- Post-hoc Correction
- CRAG-style Verification
- RiskRoll-RAG (proposed)

---

# Experiments

The paper reports multiple experiments evaluating RiskRoll-RAG under different settings.

The repository includes scripts for:

- Experiment 3 — Report Identity Stress Test
- Experiment 4 — Detector Quality Sweep
- Experiment 5 — Long-Form Contamination Evaluation
- Experiment 6 — Noisy Verifier Analysis
- Experiment 7 — ALCE QAMPARI Evaluation
- Experiment 8 — ALCE ASQA Evaluation

Each experiment stores its outputs inside the `results/` directory.

---

# Running Experiments

Run experiments from the project root.

Example:

```bash
python experiments/experiment3_report_identity_stress.py
```

```bash
python experiments/experiment4_detector_quality_sweep.py
```

```bash
python experiments/experiment5_text_longform_contamination.py
```

```bash
python experiments/experiment6_text_noisy_verifier_sweep.py
```

```bash
python experiments/experiment7d_alce_qampari_llm_generation.py \
  --model_name_or_path /path/to/Qwen2.5-7B-Instruct --n_tasks 100 --output_tag qwen7b_qampari_100_v3
```

```bash
python experiments/experiment8d_alce_asqa_llm_generation.py \
  --model_name_or_path /path/to/Qwen2.5-7B-Instruct --n_tasks 73 --output_tag qwen7b_asqa_73_v1
```

Experiments 3, 4, 5, 6, 7b, 7c and 8b are CPU-only and reproduce the saved tables exactly. Experiments 7d and 8d need a GPU and local Qwen2.5-7B-Instruct weights.

---

# Results

Generated outputs are written to the `results/` directory.

Depending on the experiment, outputs may include:

- JSON reports
- CSV summaries
- evaluation metrics
- generated responses
- analysis tables

Paper figures are stored under `paper_assets/`.

---

# Data

The repository contains the processed datasets required to reproduce the reported experiments.

No additional preprocessing is required for the included datasets.

---

# Hardware

The experiments were developed and evaluated on GPU-enabled Linux systems.

Recommended:

- NVIDIA GPU
- CUDA-enabled PyTorch installation
- Python 3.10+

Some experiments may require substantial GPU memory depending on the selected language model.

---

# Notes

Some experiments require access to external language models or APIs.

Users should configure the appropriate model endpoints or API credentials according to their local environment before execution.

No API keys are included in this repository.

---

# Citation

If you use this repository, please cite the accompanying AAAI paper.

```text
Citation information will be updated after publication.
```

---

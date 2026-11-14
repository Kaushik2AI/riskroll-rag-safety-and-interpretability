from __future__ import annotations

import csv
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

import torch


# legacy_riskroll/ project root (this file lives in legacy_riskroll/paper_assets/ablation/)
ROOT = Path(__file__).resolve().parents[2]

# Local path to Qwen2.5-7B-Instruct weights. Set before running, e.g.:
#   export MODEL_PATH=/path/to/Qwen2.5-7B-Instruct
_model_path_env = os.environ.get("MODEL_PATH")
if not _model_path_env:
    sys.exit(
        "Set MODEL_PATH to a local Qwen2.5-7B-Instruct directory, e.g.\n"
        "  export MODEL_PATH=/path/to/Qwen2.5-7B-Instruct"
    )
MODEL_PATH = Path(_model_path_env)

EXPERIMENT_FILE = (
    ROOT
    / "experiments"
    / "experiment7d_alce_qampari_llm_generation.py"
)

ORIGINAL_TASK_ROWS_PATH = (
    ROOT
    / "results"
    / "tables"
    / (
        "experiment7d_alce_qampari_llm_generation_"
        "qwen7b_qampari_100_v3_task_rows.csv"
    )
)

OUT_DIR = ROOT / "paper_assets" / "ablation"

NEW_TASK_ROWS_PATH = (
    OUT_DIR
    / "qampari_ablation_new_variants_task_rows.csv"
)

NEW_SUMMARY_PATH = (
    OUT_DIR
    / "qampari_ablation_new_variants_summary.csv"
)

RAW_JSONL_PATH = (
    OUT_DIR
    / "qampari_ablation_new_variants_raw.jsonl"
)

COMBINED_TASK_ROWS_PATH = (
    OUT_DIR
    / "qampari_ablation_all_variants_task_rows.csv"
)

COMBINED_SUMMARY_PATH = (
    OUT_DIR
    / "qampari_ablation_all_variants_summary.csv"
)

PAPER_TABLE_CSV_PATH = (
    OUT_DIR
    / "table_qampari_riskroll_ablation.csv"
)

PAPER_TABLE_TEX_PATH = (
    OUT_DIR
    / "table_qampari_riskroll_ablation.tex"
)


N_TASKS = 100
TEMPERATURE = 0.0
LOAD_IN_4BIT = False
TRUST_REMOTE_CODE = False


OUT_DIR.mkdir(parents=True, exist_ok=True)

assert ROOT.exists(), f"Missing root: {ROOT}"
assert MODEL_PATH.exists(), f"Missing model: {MODEL_PATH}"
assert EXPERIMENT_FILE.exists(), f"Missing experiment: {EXPERIMENT_FILE}"
assert ORIGINAL_TASK_ROWS_PATH.exists(), (
    f"Missing original results: {ORIGINAL_TASK_ROWS_PATH}"
)


def import_experiment():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    spec = importlib.util.spec_from_file_location(
        "experiment7d_base",
        EXPERIMENT_FILE,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load Experiment 7D module.")

    module = importlib.util.module_from_spec(spec)
    sys.modules["experiment7d_base"] = module
    spec.loader.exec_module(module)

    return module


exp7d = import_experiment()


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        return list(csv.DictReader(f))


NUMERIC_FIELDS = {
    "answer_precision",
    "answer_recall",
    "answer_f1",
    "support_rate",
    "strict_grounded_rate",
    "clean_task",
    "unsupported_commits",
    "abstention_count",
    "unsafe_prefix_depth",
    "downstream_contaminated_claims",
    "rollback_count",
    "repair_count",
}


def coerce_numeric_fields(
    row: dict[str, Any],
) -> dict[str, Any]:
    converted = dict(row)

    for key in NUMERIC_FIELDS:
        value = converted.get(key)

        if value is None or value == "":
            converted[key] = 0.0
            continue

        converted[key] = float(value)

    return converted


def run_verify_schedule(
    tokenizer,
    model,
    task,
    temperature: float,
    windows: list[int],
):
    """
    Generic verify-before-commit ablation runner.

    windows=[20]:
        One top-20 attempt, verification, then abstention.

    windows=[1, 20]:
        Top-1 initial attempt and exactly one top-20 retry.
    """
    all_docs = task["claims"][0]["candidate_docs"][:20]

    committed = []
    evidence_docs_per_item = []
    raw_outputs = []

    rollback_count = 0
    repair_count = 0
    abstention_count = 0

    seen_candidate_norms = set()

    for window_index, k in enumerate(windows):
        if len(committed) >= 5:
            break

        docs = all_docs[:k]

        prompt = exp7d.make_list_prompt(
            task["question"],
            docs,
            n_items=8,
        )

        output = exp7d.generate_text(
            tokenizer,
            model,
            prompt,
            max_new_tokens=160,
            temperature=temperature,
        )

        raw_outputs.append(
            {
                "top_k": k,
                "window_index": window_index,
                "output": output,
            }
        )

        candidates = exp7d.parse_answer_items(
            output,
            max_items=8,
        )

        for item in candidates:
            if len(committed) >= 5:
                break

            item_normalized = exp7d.norm_text(item)

            if not item_normalized:
                continue

            if item_normalized == "unknown":
                continue

            if item_normalized in seen_candidate_norms:
                continue

            seen_candidate_norms.add(item_normalized)

            duplicate_commit = any(
                exp7d.norm_text(item) == exp7d.norm_text(existing)
                for existing in committed
            )

            supported = exp7d.item_supported_by_docs(
                item,
                docs,
            )

            if duplicate_commit:
                rollback_count += 1
                continue

            if supported:
                committed.append(item)
                evidence_docs_per_item.append(docs)

                if window_index > 0:
                    repair_count += 1
            else:
                rollback_count += 1

    while len(committed) < 5:
        committed.append("UNKNOWN")
        evidence_docs_per_item.append([])
        abstention_count += 1

    return {
        "items": committed[:5],
        "raw_outputs": raw_outputs,
        "evidence_docs_per_item": evidence_docs_per_item[:5],
        "rollback_count": rollback_count,
        "repair_count": repair_count,
        "riskroll_internal_abstentions": abstention_count,
    }


def run_verify_abstain_top20(
    tokenizer,
    model,
    task,
    temperature,
):
    return run_verify_schedule(
        tokenizer=tokenizer,
        model=model,
        task=task,
        temperature=temperature,
        windows=[20],
    )


def run_verify_single_retry(
    tokenizer,
    model,
    task,
    temperature,
):
    return run_verify_schedule(
        tokenizer=tokenizer,
        model=model,
        task=task,
        temperature=temperature,
        windows=[1, 20],
    )


ABLATION_METHODS = {
    "verify_abstain_top20": (
        "Verify + abstain top-20",
        run_verify_abstain_top20,
    ),
    "verify_single_retry_1_20": (
        "Verify + single retry 1-20",
        run_verify_single_retry,
    ),
}


def save_raw_record(record: dict[str, Any]) -> None:
    with RAW_JSONL_PATH.open(
        "a",
        encoding="utf-8",
    ) as f:
        f.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
            + "\n"
        )


def run_new_variants():
    tasks = exp7d.load_jsonl(exp7d.TASK_PATH)[:N_TASKS]

    existing_rows = [
        coerce_numeric_fields(row)
        for row in read_csv_rows(NEW_TASK_ROWS_PATH)
    ]

    completed = {
        (str(row["method"]), str(row["task_id"]))
        for row in existing_rows
    }

    expected_rows = len(tasks) * len(ABLATION_METHODS)

    print("=" * 90)
    print("QAMPARI RiskRoll Ablation")
    print("=" * 90)
    print("Tasks:", len(tasks))
    print("Expected new rows:", expected_rows)
    print("Already completed:", len(completed))
    print("Model:", MODEL_PATH)
    print("CUDA:", torch.cuda.is_available())

    if len(completed) >= expected_rows:
        print("All new ablation rows already exist.")
        return existing_rows

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU was not detected.")

    print("GPU:", torch.cuda.get_device_name(0))
    print("Loading Qwen model...")

    tokenizer, model = exp7d.load_model(
        str(MODEL_PATH),
        load_in_4bit=LOAD_IN_4BIT,
        trust_remote_code=TRUST_REMOTE_CODE,
    )

    model.eval()
    torch.set_grad_enabled(False)

    print("Model loaded successfully.")

    task_rows = list(existing_rows)

    for task_index, task in enumerate(tasks, start=1):
        task_id = str(task["task_id"])

        print()
        print(
            f"Task {task_index}/{len(tasks)} | "
            f"{task_id} | {task['question']}"
        )

        for method, (display, runner) in ABLATION_METHODS.items():
            completion_key = (method, task_id)

            if completion_key in completed:
                print(f"  Skipping completed: {display}")
                continue

            print(f"  Running: {display}")

            result = runner(
                tokenizer,
                model,
                task,
                temperature=TEMPERATURE,
            )

            items = result["items"]

            evaluation = exp7d.evaluate_items(
                task,
                items,
                result["evidence_docs_per_item"],
            )

            row = {
                "method": method,
                "method_display": display,
                "task_id": task["task_id"],
                "source_id": task["source_id"],
                "question": task["question"],
                "gold_answer_list": " | ".join(
                    task["gold_answer_list"]
                ),
                "predicted_items": " | ".join(items),
                "answer_precision": evaluation["answer_precision"],
                "answer_recall": evaluation["answer_recall"],
                "answer_f1": evaluation["answer_f1"],
                "support_rate": evaluation["support_rate"],
                "strict_grounded_rate": evaluation[
                    "strict_grounded_rate"
                ],
                "clean_task": evaluation["clean_task"],
                "unsupported_commits": evaluation[
                    "unsupported_commits"
                ],
                "abstention_count": evaluation[
                    "abstention_count"
                ],
                "first_unsafe_commit_step": evaluation[
                    "first_unsafe_commit_step"
                ],
                "unsafe_prefix_depth": evaluation[
                    "unsafe_prefix_depth"
                ],
                "downstream_contaminated_claims": evaluation[
                    "downstream_contaminated_claims"
                ],
                "rollback_count": result.get(
                    "rollback_count",
                    0,
                ),
                "repair_count": result.get(
                    "repair_count",
                    0,
                ),
            }

            task_rows.append(row)
            completed.add(completion_key)

            exp7d.write_csv(
                NEW_TASK_ROWS_PATH,
                task_rows,
            )

            save_raw_record(
                {
                    "method": method,
                    "method_display": display,
                    "task_id": task["task_id"],
                    "question": task["question"],
                    "items": items,
                    "raw_outputs": result.get(
                        "raw_outputs",
                        [],
                    ),
                    "rollback_count": result.get(
                        "rollback_count",
                        0,
                    ),
                    "repair_count": result.get(
                        "repair_count",
                        0,
                    ),
                    "evaluation": evaluation,
                }
            )

            print(
                f"    F1={evaluation['answer_f1']:.3f} | "
                f"strict={evaluation['strict_grounded_rate']:.3f} | "
                f"support={evaluation['support_rate']:.3f} | "
                f"unsupported={evaluation['unsupported_commits']} | "
                f"unsafe={evaluation['unsafe_prefix_depth']} | "
                f"abstain={evaluation['abstention_count']} | "
                f"rollback={result.get('rollback_count', 0)} | "
                f"repair={result.get('repair_count', 0)}"
            )

    new_summaries = exp7d.summarize(task_rows)

    exp7d.write_csv(
        NEW_SUMMARY_PATH,
        new_summaries,
    )

    return task_rows


def build_final_tables(
    new_rows: list[dict[str, Any]],
):
    original_rows = [
        coerce_numeric_fields(row)
        for row in read_csv_rows(ORIGINAL_TASK_ROWS_PATH)
    ]

    retrieve_more_rows = [
        row
        for row in original_rows
        if row["method"] == "retrieve_more_top20"
    ]

    full_riskroll_rows = [
        row
        for row in original_rows
        if row["method"] == "riskroll_top20"
    ]

    verify_abstain_rows = [
        row
        for row in new_rows
        if row["method"] == "verify_abstain_top20"
    ]

    single_retry_rows = [
        row
        for row in new_rows
        if row["method"] == "verify_single_retry_1_20"
    ]

    for row in retrieve_more_rows:
        row["method_display"] = "Retrieve-more top-20"

    for row in full_riskroll_rows:
        row["method_display"] = "RiskRoll full 1-5-10-20"

    combined_rows = (
        retrieve_more_rows
        + verify_abstain_rows
        + single_retry_rows
        + full_riskroll_rows
    )

    exp7d.write_csv(
        COMBINED_TASK_ROWS_PATH,
        combined_rows,
    )

    combined_summaries = exp7d.summarize(combined_rows)

    exp7d.write_csv(
        COMBINED_SUMMARY_PATH,
        combined_summaries,
    )

    paper_rows = []

    for summary in combined_summaries:
        paper_rows.append(
            {
                "Variant": summary["method_display"],
                "Quality": summary["answer_f1"],
                "Strict": summary["strict_grounded_rate"],
                "Support": summary["support_rate"],
                "Unsupported": summary[
                    "mean_unsupported_commits"
                ],
                "Unsafe": summary[
                    "mean_unsafe_prefix_depth"
                ],
                "Abstentions": summary[
                    "mean_abstention_count"
                ],
                "Rollbacks": summary[
                    "mean_rollback_count"
                ],
                "Repairs": summary[
                    "mean_repair_count"
                ],
            }
        )

    exp7d.write_csv(
        PAPER_TABLE_CSV_PATH,
        paper_rows,
    )

    latex_names = {
        "retrieve_more_top20": "Retrieve-more",
        "verify_abstain_top20": "Verify + abstain",
        "verify_single_retry_1_20": (
            r"Verify + one retry"
        ),
        "riskroll_top20": "Full RiskRoll",
    }

    latex_lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{2.0pt}",
        r"\begin{tabular}{lrrrrrrr}",
        r"\toprule",
        (
            r"Variant & Qual. & Strict & Supp. & "
            r"Unsup. & Unsafe & Abst. & RB/Rep. \\"
        ),
        r"\midrule",
    ]

    for summary in combined_summaries:
        method = summary["method"]
        display = latex_names[method]

        rb_rep = (
            f"{summary['mean_rollback_count']:.3f}/"
            f"{summary['mean_repair_count']:.3f}"
        )

        latex_lines.append(
            f"{display} & "
            f"{summary['answer_f1']:.3f} & "
            f"{summary['strict_grounded_rate']:.3f} & "
            f"{summary['support_rate']:.3f} & "
            f"{summary['mean_unsupported_commits']:.3f} & "
            f"{summary['mean_unsafe_prefix_depth']:.3f} & "
            f"{summary['mean_abstention_count']:.3f} & "
            f"{rb_rep} \\\\"
        )

    latex_lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            (
                r"\caption{QAMPARI ablation of "
                r"RiskRoll's commitment-control components.}"
            ),
            r"\label{tab:riskroll_ablation}",
            r"\end{table}",
        ]
    )

    PAPER_TABLE_TEX_PATH.write_text(
        "\n".join(latex_lines),
        encoding="utf-8",
    )

    print()
    print("=" * 90)
    print("FINAL ABLATION SUMMARY")
    print("=" * 90)

    for summary in combined_summaries:
        print(
            f"{summary['method_display']:<32} | "
            f"F1={summary['answer_f1']:.3f} | "
            f"Strict={summary['strict_grounded_rate']:.3f} | "
            f"Support={summary['support_rate']:.3f} | "
            f"Unsup={summary['mean_unsupported_commits']:.3f} | "
            f"Unsafe={summary['mean_unsafe_prefix_depth']:.3f} | "
            f"Abst={summary['mean_abstention_count']:.3f} | "
            f"RB={summary['mean_rollback_count']:.3f} | "
            f"Rep={summary['mean_repair_count']:.3f}"
        )

    print()
    print("Files created:")
    print(NEW_TASK_ROWS_PATH)
    print(NEW_SUMMARY_PATH)
    print(COMBINED_TASK_ROWS_PATH)
    print(COMBINED_SUMMARY_PATH)
    print(PAPER_TABLE_CSV_PATH)
    print(PAPER_TABLE_TEX_PATH)


def main():
    new_rows = run_new_variants()
    build_final_tables(new_rows)


if __name__ == "__main__":
    main()

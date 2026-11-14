#!/usr/bin/env python3
"""Run natural-vs-corrected prefix continuation pairs.

Example:
python run_prefix_counterfactual.py \
  --input-jsonl /path/to/asqa_qwen7b_natural_longform_full73_top3.jsonl \
  --model-path /path/to/Qwen2.5-7B-Instruct \
  --cases pilot_cases.json \
  --output natural_vs_corrected_prefix_pilot.json
"""

import argparse
import json
import re
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def split_sentences(text):
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x.strip()]


def load_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def get_record(records, task_id):
    matches = [r for r in records if r["task_id"] == task_id]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one record for {task_id}, found {len(matches)}")
    return matches[0]


def build_pair(record, case):
    sents = split_sentences(record["natural_generation"])
    end_idx = case["prefix_end_sentence_idx"]
    natural_prefix = " ".join(sents[: end_idx + 1])

    if natural_prefix.count(case["wrong_span"]) != 1:
        raise ValueError(
            f'{case["case_id"]}: wrong_span must occur exactly once in selected prefix.'
        )

    corrected_prefix = natural_prefix.replace(
        case["wrong_span"], case["correct_span"], 1
    )

    return {
        **case,
        "question": record["question"],
        "system_prompt": record["system_prompt"],
        "user_prompt": record["prompt"],
        "original_full_generation": record["natural_generation"],
        "natural_prefix": natural_prefix,
        "corrected_prefix": corrected_prefix,
    }


def generate_from_prefix(tokenizer, model, system_prompt, user_prompt, assistant_prefix, max_new_tokens):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": assistant_prefix},
    ]

    try:
        chat_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            continue_final_message=True,
        )
    except TypeError:
        chat_text = tokenizer.apply_chat_template(
            messages[:-1],
            tokenize=False,
            add_generation_prompt=True,
        )
        chat_text += assistant_prefix

    inputs = tokenizer(chat_text, return_tensors="pt", add_special_tokens=False)
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}
    input_len = inputs["input_ids"].shape[-1]

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            use_cache=True,
        )

    generated_ids = outputs[0, input_len:]
    return tokenizer.decode(generated_ids, skip_special_tokens=True).strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input-jsonl", required=True)
    p.add_argument("--model-path", required=True)
    p.add_argument("--cases", default="pilot_cases.json")
    p.add_argument("--output", required=True)
    p.add_argument("--max-new-tokens", type=int, default=160)
    args = p.parse_args()

    records = load_jsonl(args.input_jsonl)
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_path, local_files_only=True, trust_remote_code=True
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        local_files_only=True,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        low_cpu_mem_usage=True,
    )
    model.eval()

    outputs = []
    for case in cases:
        pair = build_pair(get_record(records, case["task_id"]), case)

        natural = generate_from_prefix(
            tokenizer, model,
            pair["system_prompt"], pair["user_prompt"], pair["natural_prefix"],
            args.max_new_tokens,
        )
        corrected = generate_from_prefix(
            tokenizer, model,
            pair["system_prompt"], pair["user_prompt"], pair["corrected_prefix"],
            args.max_new_tokens,
        )

        outputs.append({
            **pair,
            "natural_continuation": natural,
            "corrected_continuation": corrected,
        })

        print("=" * 100)
        print(case["case_id"])
        print("NATURAL:", natural)
        print("CORRECTED:", corrected)

    Path(args.output).write_text(
        json.dumps(outputs, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

import argparse
import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--judge-model", default="migrated-tokendance/ling-3.1-flash")
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    sys.path.insert(0, str(args.runtime / "src"))
    from researchbench.generation import parse_matched_score
    from researchbench.prompts import generation_score_prompt

    predictions = [json.loads(line) for line in (args.run / "results.jsonl").read_text().splitlines()]
    tasks = {row["task_id"]: row for row in [json.loads(line) for line in (args.run / "tasks.jsonl").read_text().splitlines()]}
    gold = {row["sample_id"]: row for row in [json.loads(line) for line in (args.runtime / "data/tiny/generation.jsonl").read_text().splitlines()]}
    expected = {(task_id, condition) for task_id in tasks for condition in ("direct", "reflection", "skill-prompt")}
    if len(tasks) != 12 or len(predictions) != 36 or {(row["task_id"], row["condition"]) for row in predictions} != expected:
        raise SystemExit("Require all 12 tasks and 36 recorded attempts before scoring.")
    args.output.mkdir(parents=True, exist_ok=False)
    shuffled = list(predictions)
    random.Random(20261008).shuffle(shuffled)
    mapping = {}
    requests = []
    failed_generations = []
    for index, row in enumerate(shuffled):
        label = f"item{index + 1:03}"
        sample = gold[tasks[row["task_id"]]["sample_id"]]
        prompt = generation_score_prompt(row.get("text", ""), sample["gold_hypothesis"], sample.get("gold_key_points") or sample["gold_hypothesis"])
        mapping[label] = {"task_id": row["task_id"], "sample_id": sample["sample_id"], "condition": row["condition"]}
        if row["status"] != "ok" or row.get("finish_reason") == "length":
            failed_generations.append({"item": label, "status": "generation_failure", "score": 0, "seconds": 0})
        else:
            requests.append((label, {"model": args.judge_model, "messages": [{"role": "user", "content": prompt}], "temperature": 0, "max_tokens": 8192}))
    (args.output / "mapping.json").write_text(json.dumps(mapping, indent=2) + "\n")
    (args.output / "config.json").write_text(json.dumps({"judge_model": args.judge_model, "prompt_source": str(args.runtime / 'src/researchbench/prompts.py'), "parser_source": str(args.runtime / 'src/researchbench/generation.py'), "max_tokens": 8192, "temperature": 0, "generation_count": len(requests), "blind_to_condition": True}, indent=2) + "\n")

    def call(item):
        label, request = item
        (args.output / f"{label}-request.json").write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n")
        started = time.monotonic()
        record = {"item": label, "status": "error"}
        try:
            response = httpx.post("http://127.0.0.1:3425/v1/chat/completions", headers={"Authorization": "Bearer magpie"}, json=request, timeout=180)
            response.raise_for_status()
            body = response.json()
            (args.output / f"{label}-response.json").write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n")
            text = body["choices"][0]["message"].get("content") or ""
            score = parse_matched_score(text)
            if body['choices'][0].get('finish_reason') == 'length':
                raise ValueError("Judge response was truncated.")
            if score is None or not 0 <= score <= 5:
                raise ValueError("Official score parser could not parse the response.")
            record.update({"status": "ok", "score": score, "reason": text, "usage": body.get("usage", {}), "returned_model": body.get("model"), "finish_reason": body["choices"][0].get("finish_reason")})
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as error:
            record["error"] = type(error).__name__
        record["seconds"] = time.monotonic() - started
        return record

    records = list(failed_generations)
    with (args.output / "results.jsonl").open("w") as log, ThreadPoolExecutor(max_workers=args.workers) as pool:
        for record in failed_generations:
            log.write(json.dumps(record) + "\n")
        log.flush()
        for future in as_completed([pool.submit(call, request) for request in requests]):
            record = future.result()
            records.append(record)
            log.write(json.dumps(record, ensure_ascii=False) + "\n")
            log.flush()
            print(f'{len(records)}/{len(requests)} {record["item"]} {record["status"]} score={record.get("score")}', flush=True)
    summary = {}
    for condition in sorted({item["condition"] for item in mapping.values()}):
        subset = [record for record in records if mapping[record['item']]['condition'] == condition]
        valid = [record["score"] for record in subset if record["status"] == "ok"]
        generation_failures = sum(record['status'] == 'generation_failure' for record in subset)
        judge_failures = sum(record['status'] == 'error' for record in subset)
        summary[condition] = {"expected": 12, "scored": len(valid), "generation_failures": generation_failures, "judge_failures": judge_failures, "mean_score": sum(valid) / 12 if judge_failures == 0 else None, "denominator_policy": "12 fixed tasks; generation failure scores zero; judge failure leaves mean unavailable.", "scorer": "OFFICIAL_PROMPT_AND_PARSER" if generation_failures == 0 else "GENERATION_FAILURE_AS_ZERO_PILOT_EXTENSION", "score_range": [min(valid), max(valid)] if valid else None, "per_task": [{**mapping[record["item"]], "score": record.get("score"), "status": record["status"]} for record in subset]}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if any(record["status"] != "ok" for record in records):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

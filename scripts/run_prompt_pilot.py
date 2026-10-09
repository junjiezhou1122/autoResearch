import argparse
import hashlib
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import httpx

from prompt_conditions import CONDITIONS, system_prompt


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", default=os.environ.get("PILOT_BASE_URL"))
    parser.add_argument("--key-env", default="PILOT_API_KEY")
    parser.add_argument("--max-tokens", type=int, default=1400)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20261008)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--conditions", nargs="+", choices=CONDITIONS, default=list(CONDITIONS))
    return parser.parse_args()


def run_call(task, condition, configuration, headers, root, output):
    directory = output / "calls" / task["task_id"] / condition
    directory.mkdir(parents=True, exist_ok=True)
    request = {
        "model": configuration["model"],
        "messages": [
            {"role": "system", "content": system_prompt(root, condition)},
            {"role": "user", "content": task["prompt"]},
        ],
        "max_tokens": configuration["max_tokens"],
        "temperature": configuration["temperature"],
        "stream": False,
    }
    (directory / "request.json").write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n")
    result = {"task_id": task["task_id"], "condition": condition, "status": "error", "attempts": []}
    started = time.monotonic()
    for attempt in range(2):
        attempt_started = time.monotonic()
        try:
            response = httpx.post(
                configuration["base_url"].rstrip("/") + "/chat/completions",
                headers=headers,
                json=request,
                timeout=configuration["timeout"],
            )
            result["attempts"].append({"status_code": response.status_code, "seconds": time.monotonic() - attempt_started})
            if response.status_code in (429, 502, 503, 504) and attempt == 0:
                time.sleep(2)
                continue
            response.raise_for_status()
            payload = response.json()
            (directory / "response.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            choice = payload["choices"][0]
            message = choice["message"]
            text = message.get("content") or ""
            result.update({"returned_model": payload.get("model"), "response_id": payload.get("id"), "finish_reason": choice.get("finish_reason"), "usage": payload.get("usage", {})})
            if choice.get("finish_reason") == "length":
                raise ValueError("Provider truncated output at the shared token cap.")
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Provider returned no final text.")
            result.update({
                "status": "ok",
                "text": text,
            })
            result.pop("error", None)
            result.pop("error_type", None)
            (directory / "output.txt").write_text(text + "\n")
            break
        except (httpx.HTTPError, ValueError, KeyError, IndexError) as error:
            if isinstance(error, httpx.TransportError):
                result["attempts"].append({"error_type": type(error).__name__, "seconds": time.monotonic() - attempt_started})
            result["error_type"] = type(error).__name__
            if isinstance(error, httpx.HTTPStatusError):
                result["error"] = f"HTTP {error.response.status_code}"
                safe_body = error.response.text[:4000].replace(os.environ[configuration["key_env"]], "[redacted]")
                (directory / "error-body.txt").write_text(safe_body)
            else:
                result["error"] = str(error)[:1000].replace(os.environ[configuration["key_env"]], "[redacted]")
            if attempt == 0 and isinstance(error, httpx.TransportError):
                time.sleep(2)
                continue
            break
    result["seconds"] = time.monotonic() - started
    (directory / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def main():
    args = parse_args()
    if not args.base_url or not os.environ.get(args.key_env):
        raise SystemExit("Supply a base URL and an API key through the configured environment variable.")
    if not 1 <= args.workers <= 8 or not 1 <= args.max_tokens <= 8192:
        raise SystemExit("Use 1–8 workers and a bounded output cap of 1–8192 tokens.")
    tasks = [json.loads(line) for line in args.tasks.read_text().splitlines() if line.strip()]
    if args.limit:
        tasks = tasks[:args.limit]
    ids = set()
    for task in tasks:
        identifier = task.get("task_id")
        if not isinstance(identifier, str) or not identifier or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in identifier):
            raise SystemExit("Each task needs a safe task_id.")
        if identifier in ids or not isinstance(task.get("prompt"), str) or not task["prompt"].strip():
            raise SystemExit("Task IDs must be unique and prompts must be nonempty.")
        ids.add(identifier)
    if not tasks:
        raise SystemExit("No tasks supplied.")
    args.output.mkdir(parents=True, exist_ok=True)
    if (args.output / "config.json").exists():
        raise SystemExit("Use a new output directory; existing runs are not overwritten.")
    root = Path(__file__).resolve().parents[1]
    configuration = {
        "model": args.model,
        "base_url": args.base_url,
        "key_env": args.key_env,
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
        "workers": args.workers,
        "seed": args.seed,
        "timeout": args.timeout,
        "conditions": args.conditions,
        "tasks": len(tasks),
        "task_sha256": hashlib.sha256(args.tasks.read_bytes()).hexdigest(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "instruction_sha256": {condition: hashlib.sha256(system_prompt(root, condition).encode()).hexdigest() for condition in args.conditions},
    }
    (args.output / "config.json").write_text(json.dumps(configuration, indent=2) + "\n")
    (args.output / "tasks.jsonl").write_text("".join(json.dumps(task, ensure_ascii=False) + "\n" for task in tasks))
    schedule = []
    rng = random.Random(args.seed)
    for task in tasks:
        conditions = list(args.conditions)
        rng.shuffle(conditions)
        schedule.extend((task, condition) for condition in conditions)
    (args.output / "schedule.json").write_text(json.dumps([(task["task_id"], condition) for task, condition in schedule], indent=2) + "\n")
    headers = {"Authorization": "Bearer " + os.environ[args.key_env], "Content-Type": "application/json"}
    results = []
    with (args.output / "results.jsonl").open("w") as log, ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_call, task, condition, configuration, headers, root, args.output) for task, condition in schedule]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            log.write(json.dumps(result, ensure_ascii=False) + "\n")
            log.flush()
            usage = result.get("usage", {})
            print(f'{len(results)}/{len(schedule)} {result["task_id"]} {result["condition"]} {result["status"]} {result["seconds"]:.1f}s tokens={usage.get("total_tokens", "unknown")}', flush=True)
    summary = {}
    for condition in args.conditions:
        rows = [row for row in results if row["condition"] == condition]
        summary[condition] = {
            "attempted": len(rows),
            "succeeded": sum(row["status"] == "ok" for row in rows),
            "failed": sum(row["status"] != "ok" for row in rows),
            "truncated": sum(row.get("finish_reason") == "length" for row in rows),
            "prompt_tokens": sum(row.get("usage", {}).get("prompt_tokens", 0) for row in rows),
            "completion_tokens": sum(row.get("usage", {}).get("completion_tokens", 0) for row in rows),
            "returned_models": sorted({row.get("returned_model") for row in rows if row.get("returned_model")}),
        }
    (args.output / "usage-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if any(row["status"] != "ok" for row in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

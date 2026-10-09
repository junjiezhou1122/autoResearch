import argparse
import hashlib
import json
import os
import random
import re
import shutil
import signal
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path


CONDITIONS = ("direct", "reflection", "skill-prompt")
REFLECTION = "Before answering, privately draft a response, critique its assumptions and evidence, and revise it. Return only the requested final output."
SKILL_REQUEST = """/autoresearch:research-mode
Use the research navigation to work through the following question. After choosing a useful operation, perform it by loading the corresponding skill, and continue with further operations when useful. Decide for yourself when the hypothesis is ready. Complete the research task and return only the requested final hypothesis, rather than stopping at a recommendation. Use only the supplied evidence.

"""


def read_stream(path):
    events = []
    malformed = 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except ValueError:
            malformed += 1
    return events, malformed


def summarize_stream(events):
    initial = next((event for event in events if event.get("type") == "system" and event.get("subtype") == "init"), {})
    final = next((event for event in reversed(events) if event.get("type") == "result"), {})
    calls = []
    outcomes = {}
    assistant_events = []
    for event in events:
        message = event.get("message", {})
        content = message.get("content", [])
        if not isinstance(content, list):
            continue
        if event.get("type") == "assistant":
            assistant_events.append(event)
            for block in content:
                if block.get("type") == "tool_use":
                    calls.append({"id": block.get("id"), "name": block.get("name"), "input": block.get("input", {})})
        for block in content:
            if block.get("type") == "tool_result":
                outcomes[block.get("tool_use_id")] = {"is_error": bool(block.get("is_error")), "content": block.get("content")}
    for call in calls:
        outcome = outcomes.get(call["id"])
        call["tool_result_seen"] = outcome is not None
        call["succeeded"] = outcome is not None and not outcome["is_error"]
    serialized = json.dumps(events, ensure_ascii=False)
    return {
        "init": initial,
        "native_result": final,
        "tool_calls": calls,
        "assistant_events": len(assistant_events),
        "assistant_models": sorted({event["message"].get("model", "unknown") for event in assistant_events}),
        "entry_body_seen": "Do not perform the routed skill's work here." in serialized,
        "entry_command_seen": any(event.get("type") == "user" and "<command-name>/autoresearch:research-mode</command-name>" in json.dumps(event.get("message", {})) for event in events),
    }


def run_candidate(task, condition, configuration, output):
    directory = output / "calls" / task["task_id"] / condition
    directory.mkdir(parents=True)
    workspace = Path(tempfile.mkdtemp(prefix="research-notes-"))
    prompt = task["prompt"]
    if condition == "reflection":
        prompt = REFLECTION + "\n\n" + prompt
    elif condition == "skill-prompt":
        prompt = SKILL_REQUEST + prompt
    argv = [
        configuration["launcher"], "-p", "--output-format", "stream-json", "--verbose",
        "--input-format", "stream-json", "--replay-user-messages", "--no-session-persistence", "--permission-mode", "dontAsk",
        "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
        "--append-system-prompt-file", configuration["protocol"], "--model", configuration["model"],
        "--tools", "Skill", "--allowedTools", "Skill",
    ]
    if condition == "skill-prompt":
        argv.extend(["--plugin-dir", configuration["plugin"]])
    (directory / "prompt.txt").write_text(prompt + "\n")
    (directory / "request.json").write_text(json.dumps({"argv": argv, "cwd": str(workspace), "timeout": configuration["timeout"]}, indent=2) + "\n")
    started = time.monotonic()
    timed_out = False
    with (directory / "stream.jsonl").open("w") as stdout, (directory / "stderr.txt").open("w") as stderr:
        process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True, cwd=workspace, start_new_session=True)
        try:
            user_message = {"type": "user", "message": {"role": "user", "content": prompt}}
            process.communicate(input=json.dumps(user_message) + "\n", timeout=configuration["timeout"])
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    seconds = time.monotonic() - started
    events, malformed = read_stream(directory / "stream.jsonl")
    observation = summarize_stream(events)
    final = observation["native_result"]
    text = final.get("result", "")
    status = "ok" if process.returncode == 0 and final.get("subtype") == "success" and not final.get("is_error") and isinstance(text, str) and text.strip() else "error"
    if timed_out:
        status = "timeout"
    result = {
        "task_id": task["task_id"], "sample_id": task["sample_id"], "condition": condition,
        "status": status, "exit_code": process.returncode, "seconds": seconds,
        "text": text if isinstance(text, str) else "", "finish_reason": final.get("stop_reason"),
        "usage": final.get("usage", {}), "model_usage": final.get("modelUsage", {}),
        "num_turns": final.get("num_turns"), "estimated_cost_usd": final.get("total_cost_usd"),
        "permission_denials": final.get("permission_denials", []), "malformed_stream_lines": malformed,
        "word_count": len(re.findall(r"\b[\w]+(?:[-'][\w]+)*\b", text)) if isinstance(text, str) else 0,
        **{key: value for key, value in observation.items() if key != "native_result"},
    }
    result["requested_word_range"] = 80 <= result["word_count"] <= 150
    (directory / "native-result.json").write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n")
    (directory / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if result["text"]:
        (directory / "output.txt").write_text(result["text"] + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="migrated-tokendance/mimo-v2.6-flash[1m]")
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--conditions", nargs="+", choices=CONDITIONS, default=list(CONDITIONS))
    parser.add_argument("--seed", type=int, default=20261008)
    args = parser.parse_args()
    if not 1 <= args.workers <= 3 or not 30 <= args.timeout <= 900:
        raise SystemExit("Use 1–3 workers and a timeout of 30–900 seconds.")
    tasks = [json.loads(line) for line in args.tasks.read_text().splitlines() if line.strip()]
    if args.limit:
        tasks = tasks[:args.limit]
    identifiers = [task["task_id"] for task in tasks]
    if not tasks or len(set(identifiers)) != len(identifiers) or any(not re.fullmatch(r"[A-Za-z0-9_-]+", identifier) for identifier in identifiers):
        raise SystemExit("Require unique safe task identifiers.")
    if any(not task.get("sample_id") or not isinstance(task.get("prompt"), str) or not task["prompt"].strip() for task in tasks):
        raise SystemExit("Every task needs a sample_id and nonempty prompt.")
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    frozen = Path(tempfile.mkdtemp(prefix="research-material-"))
    plugin = frozen / "autoresearch"
    plugin.mkdir()
    shutil.copytree(root / ".claude-plugin", plugin / ".claude-plugin")
    shutil.copytree(root / "skills", plugin / "skills")
    protocol = frozen / "guidance.md"
    shutil.copyfile(root / "CLAUDE.md", protocol)
    configuration = {
        "launcher": "/Users/junjie/.local/bin/claude-research", "model": args.model,
        "protocol": str(protocol), "plugin": str(plugin), "timeout": args.timeout, "workers": args.workers,
        "seed": args.seed, "conditions": args.conditions, "tasks": len(tasks),
        "created_at": datetime.now(timezone.utc).isoformat(), "design": "one native user request; autonomous agent stopping; unequal compute allowed",
        "condition_note": "skill-prompt is retained only as a scorer-compatible identifier; this condition uses the native plugin, not a suite prompt",
        "task_sha256": hashlib.sha256(args.tasks.read_bytes()).hexdigest(),
        "source_sha256": {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in [root / "CLAUDE.md", Path(__file__), *sorted((root / "skills").glob("*/SKILL.md"))]},
    }
    (args.output / "config.json").write_text(json.dumps(configuration, indent=2) + "\n")
    (args.output / "tasks.jsonl").write_text("".join(json.dumps(task, ensure_ascii=False) + "\n" for task in tasks))
    schedule = []
    randomizer = random.Random(args.seed)
    for task in tasks:
        conditions = list(args.conditions)
        randomizer.shuffle(conditions)
        schedule.extend((task, condition) for condition in conditions)
    (args.output / "schedule.json").write_text(json.dumps([(task["task_id"], condition) for task, condition in schedule], indent=2) + "\n")
    results = []
    with (args.output / "results.jsonl").open("w") as log, ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_candidate, task, condition, configuration, args.output) for task, condition in schedule]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            log.write(json.dumps(result, ensure_ascii=False) + "\n")
            log.flush()
            successful = sum(call["succeeded"] for call in result["tool_calls"])
            print(f'{len(results)}/{len(schedule)} {result["task_id"]} {result["condition"]} {result["status"]} {result["seconds"]:.1f}s turns={result["num_turns"]} skills={successful} words={result["word_count"]}', flush=True)
    (args.output / "predictions.jsonl").write_text("".join(json.dumps({"sample_id": result["sample_id"], "condition": result["condition"], "final_hypothesis": result["text"]}, ensure_ascii=False) + "\n" for result in results if result["status"] == "ok"))
    if any(result["status"] != "ok" for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

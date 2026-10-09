import argparse
import json
import subprocess
import tempfile
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="migrated-tokendance/mimo-v2.6-flash[1m]")
    parser.add_argument("--timeout", type=float, default=240)
    parser.add_argument("--entry", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    task = json.loads(args.tasks.read_text().splitlines()[0])
    args.output.mkdir(parents=True, exist_ok=False)
    workspace = Path(tempfile.mkdtemp(prefix="research-notes-"))
    (workspace / "evidence.txt").write_text(task["prompt"] + "\n")
    prompt = """Use /autoresearch:reconstruct on the supplied research question and reference abstracts. Then return the requested final hypothesis. Use only this supplied evidence. You may load that skill through the Skill tool; use no other tools or additional skills.

""" + task["prompt"]
    if args.entry:
        prompt = "/autoresearch:research-mode I have a research question and reference abstracts, but the causal mechanism is unclear. Recommend the smallest next skill or short flow, then stop.\n\n" + task["prompt"]
    argv = [
        "/Users/junjie/.local/bin/claude-research", "-p", "--output-format", "stream-json", "--verbose",
        "--no-session-persistence", "--append-system-prompt-file", str(root / "CLAUDE.md"),
        "--model", args.model, "--plugin-dir", str(root), "--tools", "Skill", "--allowedTools", "Skill",
    ]
    (args.output / "prompt.txt").write_text(prompt + "\n")
    (args.output / "config.json").write_text(json.dumps({"argv": argv, "cwd": str(workspace), "task_id": task["task_id"], "timeout": args.timeout}, indent=2) + "\n")
    started = time.monotonic()
    status = "error"
    with (args.output / "stream.jsonl").open("w") as stdout, (args.output / "stderr.txt").open("w") as stderr:
        try:
            completed = subprocess.run(argv, input=prompt, text=True, cwd=workspace, stdout=stdout, stderr=stderr, timeout=args.timeout)
            code = completed.returncode
            status = "ok" if code == 0 else "error"
        except subprocess.TimeoutExpired:
            code = None
            status = "timeout"
    events = []
    for line in (args.output / "stream.jsonl").read_text().splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    tools = []
    result = None
    initial = None
    for event in events:
        if event.get("type") == "system" and event.get("subtype") == "init":
            initial = event
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    tools.append({"name": block["name"], "input": block.get("input")})
        if event.get("type") == "result":
            result = event
    summary = {"status": status, "exit_code": code, "seconds": time.monotonic() - started, "init": initial, "tool_calls": tools, "result": result}
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": status, "seconds": summary["seconds"], "tools": tools, "model": initial.get("model") if initial else None, "result_subtype": result.get("subtype") if result else None}, ensure_ascii=False))
    if status != "ok" or not result or result.get("is_error"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

import argparse
import hashlib
import json
import sys
from pathlib import Path


CONDITIONS = ("direct", "reflection", "skill-prompt")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    args = parser.parse_args()
    root = args.directory
    sys.path.insert(0, str(args.benchmark / "src"))
    from researchbench.generation import parse_matched_score

    rows = [json.loads(line) for line in (root / "main/results.jsonl").read_text().splitlines()]
    tasks = [json.loads(line) for line in (root / "main/tasks.jsonl").read_text().splitlines()]
    expected = {(task["task_id"], condition) for task in tasks for condition in CONDITIONS}
    assert len(tasks) == 12 and len(rows) == 36
    assert {(row["task_id"], row["condition"]) for row in rows} == expected
    audit = json.loads((root / "main/delivery-audit.json").read_text())
    assert {(item["task_id"], item["condition"]) for item in audit["per_output"]} == expected
    recognition = []
    for row in rows:
        assert row["init"]["tools"] == ["Skill"] and row["init"]["mcp_servers"] == []
        plugins = [plugin["name"] for plugin in row["init"]["plugins"]]
        assert ("autoresearch" in plugins) == (row["condition"] == "skill-prompt")
        path = root / "main/calls" / row["task_id"] / row["condition"] / "stream.jsonl"
        events = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        recognized = any(event.get("type") == "user" and "<command-name>/autoresearch:research-mode</command-name>" in json.dumps(event.get("message", {})) for event in events)
        assert recognized == (row["condition"] == "skill-prompt")
        recognition.append({"task_id": row["task_id"], "condition": row["condition"], "native_command_markup_seen": recognized})
    (root / "main/invocation-verification.json").write_text(json.dumps({"recognition": recognition, "only_skill_no_mcp_all_36": True, "baseline_research_plugin_absent": True}, indent=2) + "\n")
    judged = [json.loads(line) for line in (root / "scores-final/results.jsonl").read_text().splitlines()]
    assert len(judged) == 36 and len({row["item"] for row in judged}) == 36
    reparsed = 0
    for row in judged:
        if row["status"] != "ok":
            continue
        directory = "scores-final" if row.get("retry_count") else "scores-main"
        payload = json.loads((root / directory / f"{row['item']}-response.json").read_text())
        choice = payload["choices"][0]
        assert choice.get("finish_reason") != "length"
        assert parse_matched_score(choice["message"]["content"]) == row["score"]
        reparsed += 1
    summary = json.loads((root / "summary.json").read_text())["conditions"]
    for condition in CONDITIONS:
        item = summary[condition]
        per_task = item["scores"]["per_task"]
        missing = sum(entry["score"] is None for entry in per_task)
        score_sum = sum(entry["score"] for entry in per_task if entry["score"] is not None)
        assert item["full_denominator_match_bounds"] == [score_sum / 12, (score_sum + missing * 5) / 12]
        assert item["scores"]["mean_score"] == (None if missing else score_sum / 12)
        subset = [row for row in rows if row["condition"] == condition]
        assert item["successful_skills"] == sum(call["name"] == "Skill" and call["succeeded"] for row in subset for call in row["tool_calls"])
        assert item["hypothesis_delivered"] == sum(entry["hypothesis_delivered"] for entry in audit["per_output"] if entry["condition"] == condition)
    config = json.loads((root / "main/config.json").read_text())
    for name, digest in config["source_sha256"].items():
        if name.startswith("skills/"):
            assert hashlib.sha256((Path(config["plugin"]) / name).read_bytes()).hexdigest() == digest
    verification = {"generation_records": 36, "delivery_audit_records": 36, "raw_judgments_reparsed": reparsed, "unresolved_judgments": sum(row["status"] == "error" for row in judged), "full_denominators_verified": True, "native_plugin_isolation_verified": True, "frozen_skills_verified": True, "made_no_model_calls": True}
    (root / "verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()

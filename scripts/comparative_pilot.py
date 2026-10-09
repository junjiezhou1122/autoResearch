import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path


def load_adapter(path):
    spec = importlib.util.spec_from_file_location("forecast_adapter", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "score"))
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--pairs", type=int, default=12)
    args = parser.parse_args()
    adapter = load_adapter(args.adapter)
    pairs = adapter.load_pairs("test", "1", args.pairs)
    if args.action == "prepare":
        tasks = []
        for pair in pairs:
            for task in pair:
                evidence = task.agent_input()
                prompt = f"""Which of these two proposed research approaches is more likely to achieve the research goal with better empirical performance? Use only the supplied descriptions. Return exactly one JSON object with one field, label. Use integer 1 if approach 1 is more likely to win, and integer 0 if approach 2 is more likely to win.

Research goal:
{evidence['research_goal']}

Approach 1:
{evidence['idea_1']}

Approach 2:
{evidence['idea_2']}"""
                tasks.append({"task_id": task.task_id, "comparison_id": task.comparison_id, "benchmark": "research-success-forecast", "prompt": prompt})
        args.directory.mkdir(parents=True, exist_ok=True)
        (args.directory / "approaches.jsonl").write_text("".join(json.dumps(task, ensure_ascii=False) + "\n" for task in tasks))
        (args.directory / "selection.json").write_text(json.dumps({"revision": adapter.REVISION, "split": "test", "sigma": "1", "selection_method": "first published comparisons in pinned adapter order", "pairs": args.pairs, "presentations": len(tasks)}, indent=2) + "\n")
        print(f"Prepared {len(tasks)} label-free presentations from {len(pairs)} pairs.")
        print(f"Prompt lengths: {min(len(task['prompt']) for task in tasks)}–{max(len(task['prompt']) for task in tasks)} characters.")
        return
    results = [json.loads(line) for line in (args.directory / "results.jsonl").read_text().splitlines()]
    summaries = {}
    for condition in sorted({row["condition"] for row in results}):
        predictions = []
        invalid = []
        for row in results:
            if row["condition"] != condition:
                continue
            try:
                if row["status"] != "ok" or row.get("finish_reason") == "length":
                    raise ValueError("Call failed or was truncated")
                text = row["text"].strip()
                if text.startswith("```"):
                    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
                response = json.loads(text)
                if set(response) != {"label"} or type(response["label"]) is not int or response["label"] not in (0, 1):
                    raise ValueError("Invalid label output")
                predictions.append({"task_id": row["task_id"], "label": response["label"]})
            except (ValueError, TypeError, KeyError):
                invalid.append(row["task_id"])
        by_id = {row["task_id"]: row["label"] for row in predictions}
        outcomes = [{"comparison_id": first.comparison_id, "correct": by_id.get(first.task_id) == first.row['label'] and by_id.get(second.task_id) == second.row['label'], "consistent": first.task_id in by_id and second.task_id in by_id and by_id[first.task_id] != by_id[second.task_id]} for first, second in pairs]
        if invalid:
            correct_rows = sum(task.task_id in by_id and by_id[task.task_id] == task.row['label'] for pair in pairs for task in pair)
            score = {"scorer": "FAILURE_AS_WRONG_PILOT_EXTENSION", "official_evaluator_available": False, "comparisons": len(pairs), "presentations": len(pairs) * 2, "invalid_task_ids": invalid, "invalid_outputs": len(invalid), "correct_comparisons": sum(row['correct'] for row in outcomes), "consistent_comparisons": sum(row['consistent'] for row in outcomes), "correct_presentations": correct_rows, "consistency_aware_accuracy": sum(row['correct'] for row in outcomes) / len(pairs), "consistency": sum(row['consistent'] for row in outcomes) / len(pairs), "presentation_accuracy": correct_rows / (len(pairs) * 2), "denominator_policy": "All selected tasks retained; invalid output is wrong; incomplete pair is inconsistent."}
        else:
            score = adapter.score(pairs, predictions)
            score["invalid_outputs"] = 0
        score["pair_outcomes"] = outcomes
        summaries[condition] = score
        (args.directory / f"predictions-{condition}.jsonl").write_text("".join(json.dumps(row) + "\n" for row in predictions))
    (args.directory / "scores.json").write_text(json.dumps(summaries, indent=2) + "\n")
    for condition, score in summaries.items():
        print(condition, json.dumps({key: value for key, value in score.items() if key != "pair_outcomes"}))


if __name__ == "__main__":
    main()

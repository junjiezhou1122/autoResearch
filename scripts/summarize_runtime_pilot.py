import argparse
import json
import statistics
from pathlib import Path

from summarize_pilot import paired_difference


LABELS = {"direct": "Direct", "reflection": "Reflection", "skill-prompt": "Native research skills"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in (args.run / "results.jsonl").read_text().splitlines()]
    scores = json.loads((args.scores / "summary.json").read_text())
    audit = json.loads((args.run / "delivery-audit.json").read_text())
    delivery = {(item["task_id"], item["condition"]): item for item in audit["per_output"]}
    summary = {}
    for condition, label in LABELS.items():
        subset = [row for row in rows if row["condition"] == condition]
        durations = [row["seconds"] for row in subset]
        usage = {key: sum(row["usage"].get(key, 0) for row in subset) for key in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "output_tokens")}
        skills = [call for row in subset for call in row["tool_calls"] if call["name"] == "Skill"]
        per_task = {row["task_id"]: [call["input"].get("skill") for call in row["tool_calls"] if call["name"] == "Skill" and call["succeeded"]] for row in subset}
        per_scores = scores[condition]["per_task"]
        available_sum = sum(item["score"] for item in per_scores if item["score"] is not None)
        missing_scores = sum(item["score"] is None for item in per_scores)
        bounds = [available_sum / len(subset), (available_sum + 5 * missing_scores) / len(subset)]
        delivered_sum = sum(item["score"] for item in per_scores if item["score"] is not None and delivery[(item["task_id"], condition)]["hypothesis_delivered"])
        summary[condition] = {
            "label": label,
            "full_denominator_match_bounds": bounds,
            "completion_as_zero_mean_local_extension": delivered_sum / len(subset) if missing_scores == 0 else None, "tasks": len(subset), "completed": sum(row["status"] == "ok" for row in subset),
            "hypothesis_delivered": sum(delivery[(row["task_id"], condition)]["hypothesis_delivered"] for row in subset),
            "missing_usage": sum(not row["usage"] for row in subset),
            "word_compliant": sum(row["requested_word_range"] for row in subset),
            "mean_seconds": statistics.mean(durations), "median_seconds": statistics.median(durations),
            "min_seconds": min(durations), "max_seconds": max(durations), "usage": usage,
            "total_input_tokens_including_cache": sum(usage[key] for key in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")),
            "skill_attempts": len(skills), "successful_skills": sum(call["succeeded"] for call in skills),
            "failed_tool_attempts": [{"task_id": row["task_id"], "name": call["name"], "input": call["input"]} for row in subset for call in row["tool_calls"] if not call["succeeded"]],
            "tasks_using_skills": sum(bool(value) for value in per_task.values()), "skills_by_task": per_task,
            "entry_body_observed": sum(row["entry_body_seen"] for row in subset),
            "native_turns": sum(row.get("num_turns") or 0 for row in subset), "scores": scores[condition],
            "failures": [{"task_id": row["task_id"], "status": row["status"], "exit_code": row["exit_code"]} for row in subset if row["status"] != "ok"],
        }
    paired = {}
    skill_scores = {row["task_id"]: row["score"] for row in scores["skill-prompt"]["per_task"] if row["score"] is not None}
    for baseline in ("direct", "reflection"):
        baseline_scores = {row["task_id"]: row["score"] for row in scores[baseline]["per_task"] if row["score"] is not None}
        paired[baseline] = paired_difference(baseline_scores, skill_scores)
    result = {"conditions": summary, "paired_skill_minus_baseline": paired}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    report = [
        "# Native Claude Code research results", "",
        "All three conditions ran through the same clean claude-research launcher and MiMo-V2.6-Flash[1m]. Each received one user request and the same twelve ResearchBench tiny evidence packages. The agent controlled its own research operations and stopping. Native research skills invoked research-mode in the request and loaded the frozen plugin. Extra steps and compute were allowed; this compares actual-use workflows rather than equal-compute instruction effects.", "",
        "| Condition | Runtime succeeded | Hypothesis delivered | Raw-reply match mean / 5 | Median seconds | Mean seconds | Total input tokens including cache | Output tokens | Successful Skill calls | Word compliance |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for condition, item in summary.items():
        score = item["scores"]["mean_score"]
        mean = f"{score:.3f}" if score is not None else "unavailable"
        report.append(f'| {item["label"]} | {item["completed"]}/12 | {item["hypothesis_delivered"]}/12 | {mean} | {item["median_seconds"]:.1f} | {item["mean_seconds"]:.1f} | {item["total_input_tokens_including_cache"]:,} | {item["usage"]["output_tokens"]:,} | {item["successful_skills"]}/{item["skill_attempts"]} | {item["word_compliant"]}/12 |')
    report.extend(["", "Runtime success only means the native CLI exited successfully with text. Hypothesis delivery is audited separately in main/delivery-audit.json. The official judge scores every raw reply without repairing or replacing intermediate notes; this can give content-match credit to an unfinished task. Interpret match score together with delivery rate. The input total includes uncached, cache-read and cache-creation tokens. Raw usage retains those fields separately. Missing terminal usage means unknown consumption, not zero. CLI estimated costs have an unknown basis and are not reported as billed costs. Native num_turns includes runtime/tool activity and is not an audited count of upstream transport attempts.", "", "## Paired differences", "", "| Skills minus baseline | Scored pairs | Mean score difference | Wins / ties / losses | Exploratory sign-flip p |", "| --- | ---: | ---: | --- | ---: |"])
    for baseline, difference in paired.items():
        if difference is None:
            report.append(f'| {LABELS[baseline]} | 0/12 | unavailable | unavailable | unavailable |')
            continue
        report.append(f'| {LABELS[baseline]} | {difference["n"]}/12 | {difference["mean_difference"]:.3f} | {difference["wins"]} / {difference["ties"]} / {difference["losses"]} | {difference["two_sided_sign_flip_p"]:.3f} |')
        if difference["n"] < 12:
            report.append(f'\nOnly {difference["n"]} pairs have scores for both skills and {LABELS[baseline]}; this paired comparison is partial.\n')
    lower, upper = summary["direct"]["full_denominator_match_bounds"]
    for condition, item in summary.items():
        missing = sum(entry["score"] is None for entry in item["scores"]["per_task"])
        if missing:
            lower, upper = item["full_denominator_match_bounds"]
            report.extend(["", f'{item["label"]} has {missing} unavailable judgments after the uniform retry. Its full twelve-task mean is bounded by {lower:.3f}–{upper:.3f}, assigning missing scores any value from 0 to 5.'])
    for condition, item in summary.items():
        sensitivity = item["completion_as_zero_mean_local_extension"]
        value = f"{sensitivity:.3f}" if sensitivity is not None else "unavailable because judging is incomplete"
        report.extend(["", f'{item["label"]} delivered {item["hypothesis_delivered"]}/12 final hypotheses. A separate local sensitivity analysis counting unfinished deliveries as zero gives {value}. This extension is not the official ResearchBench match score.'])
    report.extend(["", "## Actual skill use", ""])
    for task_id, skills in summary["skill-prompt"]["skills_by_task"].items():
        report.append(f'- {task_id}: ' + (" → ".join(skills) if skills else "No successful Skill result observed."))
    report.extend(["", "## Tool errors", ""])
    for condition, item in summary.items():
        failed = item["failed_tool_attempts"]
        report.append(f'- {item["label"]}: {len(failed)} unsuccessful tool attempts.')
        for call in failed:
            report.append(f'  - {call["task_id"]}: {call["name"]} {json.dumps(call["input"], ensure_ascii=False)}')
    report.extend(["", "Native command recognition is verified separately in main/invocation-verification.json; the entry body is not directly replayed.", "", "## Scope and limits", "",
        "- One generator model, twelve tasks, one run per task and one blinded judge model. Paired tests are exploratory without multiple-comparison correction.",
        "- The official ResearchBench scoring prompt and parser measure overlap with hidden target hypotheses. They do not establish novelty, factual validity or experimental success.",
        "- Hypothesis generation uses a local 80–150-word request. It is not an official multistep benchmark reproduction.",
        "- All groups had only Skill available. No web, filesystem, shell or agent tools were exposed; this is an evidence-bounded task rather than unrestricted open-ended research.",
        "- research-mode routes to leaf skills. The initial task asks the agent to continue until final delivery; this run's exact entry version is frozen and hashed in main/config.json. No scripted follow-up, routing loop or leaf-call count is added.",
        "- Baselines have no autoresearch plugin. Native built-in skills remain present. Init inventories and actual tools are saved for inspection.",
        "- The common project protocol is explicitly injected and mentions experiment rules. The task request contains no condition or judging labels, but this protocol means candidates are not fully blind to being constrained.",
        "- A 600-second timeout bounds each process; no candidate failures are selectively rerun. Native internal retries may occur and are not fully exposed in the result metadata.",
        "- The native runtime has different default output limits and prompts from the first API pilot; compare conditions within this run, not score changes between runs as an isolated runtime effect.",
        "", "## Artifacts", "", "- main/calls contains raw streams, prompts, argv, stderr, tool observations and final outputs.", "- main/all-outputs.md contains every generated hypothesis.", "- scores-main contains blinded scoring requests and responses; scores-final consolidates any uniform judge retry.",
    ])
    (args.output / "report.md").write_text("\n".join(report) + "\n")
    all_outputs = ["# Hypotheses from native runtime", ""]
    by_key = {(row["task_id"], row["condition"]): row for row in rows}
    for task_id in sorted({row["task_id"] for row in rows}):
        for condition, label in LABELS.items():
            row = by_key[(task_id, condition)]
            all_outputs.extend([f"## {task_id} {label}", "", row["text"] or f"No final hypothesis. Status {row['status']}.", ""])
    (args.run / "all-outputs.md").write_text("\n".join(all_outputs))
    print(args.output / "report.md")
    for condition, item in summary.items():
        print(condition, item["scores"]["mean_score"], item["median_seconds"], item["successful_skills"])


if __name__ == "__main__":
    main()

import argparse
import json
import statistics
from pathlib import Path


def paired_difference(first, second):
    keys = sorted(set(first) & set(second))
    differences = [second[key] - first[key] for key in keys]
    if not differences:
        return None
    observed = abs(sum(differences))
    extreme = 0
    for mask in range(1 << len(differences)):
        value = sum(difference if mask & (1 << index) else -difference for index, difference in enumerate(differences))
        extreme += abs(value) >= observed - 1e-9
    return {"n": len(differences), "mean_difference": statistics.mean(differences), "wins": sum(value > 0 for value in differences), "ties": sum(value == 0 for value in differences), "losses": sum(value < 0 for value in differences), "two_sided_sign_flip_p": extreme / (1 << len(differences))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    directory = args.directory
    comparative = json.loads((directory / "comparative-main/scores.json").read_text())
    score_directory = directory / 'researchbench-scores-final' if (directory / 'researchbench-scores-final/summary.json').exists() else directory / 'researchbench-scores-main'
    research = json.loads((score_directory / "summary.json").read_text())
    by_condition = {condition: {entry['task_id']: entry['score'] for entry in summary['per_task'] if entry['score'] is not None and entry['status'] == 'ok'} for condition, summary in research.items()}
    comparisons = {}
    for baseline in ('direct', 'reflection'):
        comparisons['researchbench-skill-vs-' + baseline] = paired_difference(by_condition[baseline], by_condition['skill-prompt'])
        baseline_pairs = {item['comparison_id']: int(item['correct']) for item in comparative[baseline]['pair_outcomes']}
        suite_pairs = {item['comparison_id']: int(item['correct']) for item in comparative['skill-prompt']['pair_outcomes']}
        comparisons['comparative-skill-vs-' + baseline] = paired_difference(baseline_pairs, suite_pairs)
    usage = {name: json.loads((directory / f'{name}-main/usage-summary.json').read_text()) for name in ('researchbench', 'comparative')}
    result = {'researchbench': research, 'comparative': comparative, 'paired_comparisons': comparisons, 'usage': usage, 'word_compliance': json.loads((directory / 'researchbench-main/word-compliance.json').read_text())}
    (directory / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    report = ['# First real pilot results', '', 'Generation used TokenDance MiMo-V2.6-Flash through Magpie. The same model, evidence, temperature 0.2 and 6000-token output cap were used across prompt conditions. Each task had one scheduled generation, with one automatic retry allowed for transport errors. Five cells retried after read timeouts: direct 0, reflection 1, skill-prompt 4. Usage of those timed-out requests is unknown. In the original result records, status is authoritative; four successful rows retain stale ReadTimeout metadata, documented in retry-audit.json.', '', '## ResearchBench tiny data', '', 'This is a local single-call generation protocol, not the official multistep generator. The 12-task matched score uses the official prompt and parser with a blinded Ling-3.1-Flash judge. Scores measure overlap with a target hypothesis.', '', '| Condition | Scored tasks | Mean match score / 5 | Word-format compliance | Input tokens | Output tokens |', '| --- | ---: | ---: | ---: | ---: | ---: |']
    for condition in ('direct', 'reflection', 'skill-prompt'):
        score = research[condition]
        tokens = usage['researchbench'][condition]
        compliance = result['word_compliance'][condition]
        value = f'{score["mean_score"]:.3f}' if score['mean_score'] is not None else 'unavailable'
        report.append(f'| {condition} | {score["scored"]}/12 | {value} | {compliance["requested_80_to_150_words"]}/12 | {tokens["prompt_tokens"]:,} | {tokens["completion_tokens"]:,} |')
    report.extend(['', '## Comparative research success', '', 'This uses the first 12 test/sigma-1 published comparisons in the pinned adapter order. Both display orders are included. An invalid or truncated response is counted wrong against the fixed denominator, marked as a pilot extension when needed.', '', '| Condition | Both orders correct | Presentations correct | Consistent pairs | Truncated | Malformed | Input tokens | Output tokens |', '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |'])
    for condition in ('direct', 'reflection', 'skill-prompt'):
        score = comparative[condition]
        tokens = usage['comparative'][condition]
        report.append(f'| {condition} | {score["correct_comparisons"]}/12 ({100*score["consistency_aware_accuracy"]:.1f}%) | {score["correct_presentations"]}/24 | {score["consistent_comparisons"]}/12 | {tokens["truncated"]} | {score.get("invalid_outputs",0) - tokens["truncated"]} | {tokens["prompt_tokens"]:,} | {tokens["completion_tokens"]:,} |')
    report.extend(['', '## Paired uncertainty', '', '| Comparison | Mean difference | Wins / ties / losses | Exact two-sided sign-flip p |', '| --- | ---: | --- | ---: |'])
    for name, comparison in comparisons.items():
        report.append(f'| {name} | {comparison["mean_difference"]:.3f} | {comparison["wins"]} / {comparison["ties"]} / {comparison["losses"]} | {comparison["two_sided_sign_flip_p"]:.3f} |')
    report.extend(['', 'These pilot comparisons are exploratory and do not adjust for multiple comparisons. A small difference is not evidence of general superiority.', '', '## Runtime evidence', '', 'The separate clean Claude Code task loaded autoresearch, had no MCP servers, called autoresearch:reconstruct through the Skill tool, and returned a hypothesis. The entry-only task recommended reconstruct and stopped, but its stream did not show a Skill call, so it is weaker evidence of entry loading. These runtime checks are not pooled into prompt scores.', '', '## Limits', '', '- One generation model, one judge and a small deterministic prefix of comparison tasks.', '- The skill prompt contains more instructions and input tokens; input length is not matched.', '- The prompt suite exposes all skills at once, unlike progressive disclosure or state-conditioned routing.', '- Public task and model-training overlap cannot be excluded.', '- ResearchBench generation uses a local 80–150-word template. One format violation is retained and reported.', '- In-flight usage from aborted calibration requests is unknown. Those runs are excluded from quality comparisons but their saved usage remains in researchbench/calibration-summary.json and comparative/calibration-summary.json.', '- TokenDance model listing did not expose verified prices. Token counts are reported; billed cost is not inferred.', '', '## Artifacts', '', '- researchbench-main/all-outputs.md contains all 36 hypotheses.', '- researchbench-scores-main contains the first complete blinded judging attempt; researchbench-scores-final contains consolidated scores after two uniform failed-judge retries.', '- comparative-main contains all task/condition calls, predictions and paired outcomes.', '- clean-runtime-retry/summary.json records the actual primitive call.', '- Original budget-calibration and failed-start directories are retained.'])
    (directory / 'report.md').write_text('\n'.join(report) + '\n')
    print(directory / 'report.md')
    print(json.dumps(comparisons, indent=2))


if __name__ == '__main__':
    main()

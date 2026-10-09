import argparse
import ast
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
out = args.output.resolve()
load = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
provenance = load(out / 'input-provenance.json')
for relative, expected in provenance['source_hashes'].items():
    assert sha(out / relative) == expected, relative
assert sha(out / 'tasks.json') == provenance['task_file_sha256']
for entry in provenance['references']:
    assert sha(Path(entry['text_path'])) == entry['sha256']
preflight = load(out / 'preflight.json')
assert preflight['passed'] and len(preflight['results']) == 3
records = [json.loads(line) for line in (out / 'results.jsonl').read_text().splitlines()]
tasks = {t['index']: t for t in load(out / 'tasks.json')}
expected = {(i, c) for i in tasks for c in ('direct', 'reflection', 'skills')}
assert {(r['index'], r['condition']) for r in records} == expected
assert len(records) == len(expected) == 9
inventories = []
for r in records:
    directory = out / 'calls' / str(r['index']) / r['condition']
    request = load(directory / 'request.json')
    assert request['wall_timeout'] is None
    prompt = (directory / 'prompt.txt').read_text()
    prefix = '/autoresearch:research-mode\n' if r['condition'] == 'skills' else ('Before answering, privately draft a response, critique its assumptions and evidence, and revise it. Return only the requested final output.\n\n' if r['condition'] == 'reflection' else '')
    assert prompt == prefix + tasks[r['index']]['prompt']
    events = [json.loads(line) for line in (directory / 'stream.jsonl').read_text().splitlines()]
    final = next(e for e in reversed(events) if e.get('type') == 'result')
    assert r['text'] == final.get('result', '') == (directory / 'output.txt').read_text()
    assert r['usage'] == final.get('usage')
    models = sorted({e['message'].get('model', 'unknown') for e in events if e.get('type') == 'assistant'})
    assert models == r['models']
    outcomes = {}
    actual_calls = []
    for e in events:
        content = e.get('message', {}).get('content', [])
        if not isinstance(content, list):
            continue
        for b in content:
            if e.get('type') == 'assistant' and b.get('type') == 'tool_use':
                actual_calls.append((b.get('id'), b.get('name'), b.get('input')))
            if b.get('type') == 'tool_result':
                outcomes[b.get('tool_use_id')] = not b.get('is_error', False)
    assert len(actual_calls) == len(r['tool_calls'])
    for c, actual in zip(r['tool_calls'], actual_calls):
        assert (c['id'], c['name'], c['input']) == actual
        assert c['succeeded'] == outcomes.get(c['id'], False)
    if r['condition'] == 'skills':
        assert r['entry_command_seen']
        assert any(p.get('name') == 'autoresearch' for p in r['init'].get('plugins', []))
    else:
        assert not any(p.get('name') == 'autoresearch' for p in r['init'].get('plugins', []))
    inventories.append({'index': r['index'], 'condition': r['condition'], 'tools': r['init'].get('tools'), 'models': models, 'skills': [c['input'].get('skill') for c in r['tool_calls'] if c['name'] == 'Skill' and c['succeeded']]})
score_records = load(out / 'scores.json')
source = out / 'frozen/compare_gt.py'
tree = ast.parse(source.read_text())
tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
builders = {'json': json}
exec(compile(tree, str(source), 'exec'), builders)
blind = {x['label']: x for x in load(out / 'blind-mapping.json')}
targets = {x['index']: x['summary'] for x in load(Path('/Users/junjie/Projects/idea-benchmarks/ai-idea-bench/data/target_paper_data.json'))}
for s in score_records:
    directory = out / 'evaluation' / s['label'] / s['metric']
    payload = load(directory / 'request.json')
    assert 'response_format' not in payload
    mapping = blind[s['label']]
    idea = load(out / 'calls' / str(mapping['index']) / mapping['condition'] / 'final_ideas.json')[0]['model_result'][0]
    target = targets[mapping['index']]
    if s['metric'] == 'experiment_similarity':
        reference = ''.join(ex['design_name'] + ': ' + ex['description'] + '\n' for ex in target['method']['targeted_designs_details'])
        system, user = builders['similarity_experiment_plan_w_experiment_plan'](idea['Experiment'], reference)
    elif s['metric'] == 'motivation_similarity':
        system, user = builders['similarity_motivation_w_motivation'](idea['Motivation'], target['motivation'])
    else:
        system, user = builders['generate_alignment_evaluation_prompts'](target.get('revised_topic') or target['topic'], idea['Motivation'], idea['Experiment'])
    assert payload['messages'] == [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}]
    if s['status'] != 'ok':
        continue
    raw = load(directory / ('raw-' + str(s['attempt']) + '.json'))
    choice = raw['choices'][0]
    assert choice['finish_reason'] == 'stop'
    content = choice['message']['content']
    assert isinstance(content, str) and content.strip()
    import re
    parsed = json.loads(re.sub(r'```json\n|\n```', '', content))
    assert parsed == s['parsed']
    assert s['source_field'] == 'content'
    if s['metric'] == 'topic_alignment':
        values = [parsed[k]['alignment'] for k in ('motivation', 'experiment_plan')]
    else:
        key = 'experiment_plan_similarity' if s['metric'] == 'experiment_similarity' else 'motivation_similarity'
        values = [parsed[key]['rating']]
    assert values == s['values'] and all(type(v) in (int, float) and 1 <= v <= 5 for v in values)
summary = load(out / 'summary.json')
for condition, entry in summary['conditions'].items():
    for metric in entry['metrics'].values():
        assert metric['denominator'] == 3
        assert metric['mean'] == (sum(metric['values']) / 3 if len(metric['values']) == 3 else None)
result = {'verified_records': len(records), 'valid_scores': sum(s['status'] == 'ok' for s in score_records), 'assigned_scores': len(records) * 3, 'frozen_hashes_match': True, 'reference_hashes_match': True, 'native_streams_match': True, 'final_content_only': True, 'no_candidate_wall_timeout': True, 'inventories': inventories}
(out / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'inventories'}, ensure_ascii=False))

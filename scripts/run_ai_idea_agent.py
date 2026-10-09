import argparse
import ast
import concurrent.futures
import hashlib
import json
import random
import re
import shutil
import statistics
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = Path('/Users/junjie/Projects/idea-benchmarks/ai-idea-bench')
MODEL = 'migrated-tokendance/mimo-v2.6-flash[1m]'
JUDGE = 'migrated-tokendance/ling-3.1-flash'
CONDITIONS = ('direct', 'reflection', 'skills')
REFLECTION = 'Before answering, privately draft a response, critique its assumptions and evidence, and revise it. Return only the requested final output.'
FIELDS = ('Name', 'Title', 'Motivation', 'Experiment', 'Interestingness', 'Feasibility', 'Novelty')
METRICS = ('experiment_similarity', 'motivation_similarity', 'topic_alignment')


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def definitions(path, names):
    tree = ast.parse(path.read_text())
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in selected} == set(names)
    namespace = {'json': json, 're': re}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def constants(path, names):
    found = {}
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in names and isinstance(node.value, ast.Constant):
                    found[target.id] = ast.literal_eval(node.value)
    assert set(found) == set(names)
    return found


def prepare(out):
    frozen = out / 'frozen'
    frozen.mkdir(exist_ok=False)
    files = {
        'generator.py': BENCH / 'AI-Scientist/generate_ideas_fron_papers.py',
        'llm.py': BENCH / 'AI-Scientist/ai_scientist/llm.py',
        'compare_gt.py': BENCH / 'prompt_template/compare_gt.py',
        'local-bench.py': BENCH / 'local/bench.py',
        'agent.md': ROOT / 'docs/research-agent.md',
        'launcher': Path('/Users/junjie/.local/bin/claude-research'),
        'runner.py': Path(__file__),
    }
    for name, source in files.items():
        shutil.copyfile(source, frozen / name)
    shutil.copytree(ROOT / '.claude-plugin', frozen / 'autoresearch/.claude-plugin')
    shutil.copytree(ROOT / 'skills', frozen / 'autoresearch/skills')
    official = constants(frozen / 'generator.py', ('idea_first_prompt', 'idea_system_prompt'))
    (frozen / 'system.md').write_text((frozen / 'agent.md').read_text() + '\n\n' + official['idea_system_prompt'] + '\n')
    rows = read(BENCH / 'data/target_paper_data.json')[:3]
    tasks = []
    provenance = []
    for row in rows:
        refs = []
        for ref in row['find_cite']['top_references']:
            name = Path(ref['paper_local_path']).name
            path = BENCH / 'data/paper_text' / (hashlib.sha256(name.encode()).hexdigest() + '.txt')
            refs.append({'title': ref['title'], 'text': path.read_text()})
            provenance.append({'index': row['index'], 'title': ref['title'], 'text_path': str(path), 'sha256': sha(path)})
        topic = row['summary']['revised_topic'] or row['summary']['topic']
        related = '\n'.join('Paper ' + str(i) + ': ' + ref['title'] + '\n' + ref['text'] for i, ref in enumerate(refs))
        prompt = official['idea_first_prompt'].format(task_description='You are given the following file to work with. The rearch topic is: ' + topic, prev_ideas_string=related, num_reflections=1)
        tasks.append({'index': row['index'], 'topic': topic, 'references': refs, 'prompt': prompt})
    write(out / 'tasks.json', tasks)
    write(out / 'input-provenance.json', {'references': provenance, 'interface': 'local/bench.py topic and full-reference-text interface; official generation template', 'author_preprocessing_reproduced': False, 'source_hashes': {str(p.relative_to(out)): sha(p) for p in frozen.rglob('*') if p.is_file()}, 'task_file_sha256': sha(out / 'tasks.json')})
    schedule = [(t['index'], c) for t in tasks for c in CONDITIONS]
    random.Random(20261009).shuffle(schedule)
    write(out / 'schedule.json', schedule)
    write(out / 'config.json', {'model': MODEL, 'judge': JUDGE, 'indices': [t['index'] for t in tasks], 'conditions': CONDITIONS, 'workers': 2, 'candidate_wall_timeout': None, 'candidate_retries': 0, 'judge_max_tokens': 8000, 'judge_attempts': 2, 'official_num_reflections_parameter': 1, 'input_interface': 'local_full_text', 'author_preprocessing_reproduced': False, 'official_multi_round_baseline_reproduced': False})
    print('Prepared tasks ' + str([t['index'] for t in tasks]), flush=True)


def judge_value(data, metric):
    if metric == 'topic_alignment':
        entries = [data.get(k) for k in ('motivation', 'experiment_plan')]
        value_key, text_key = 'alignment', 'comments'
    else:
        key = 'experiment_plan_similarity' if metric == 'experiment_similarity' else 'motivation_similarity'
        entries = [data.get(key)]
        value_key, text_key = 'rating', 'explanation'
    if any(not isinstance(e, dict) or type(e.get(value_key)) not in (int, float) or not 1 <= e[value_key] <= 5 or not isinstance(e.get(text_key), str) or not e[text_key].strip() for e in entries):
        raise ValueError('Missing official score fields')
    return [e[value_key] for e in entries]


def judge_call(folder, payload, metric):
    folder.mkdir(parents=True, exist_ok=True)
    write(folder / 'request.json', payload)
    for attempt in (1, 2):
        started = time.monotonic()
        try:
            req = urllib.request.Request('http://127.0.0.1:3425/v1/chat/completions', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json', 'Authorization': 'Bearer magpie'})
            with urllib.request.urlopen(req, timeout=180) as response:
                raw = json.load(response)
            write(folder / f'raw-{attempt}.json', raw)
            choice = raw['choices'][0]
            if choice.get('finish_reason') != 'stop':
                raise ValueError('Judge did not finish normally')
            content = choice['message'].get('content')
            if not isinstance(content, str) or not content.strip():
                raise ValueError('Missing final content; reasoning is not accepted')
            content = re.sub(r'```json\n|\n```', '', content)
            parsed = json.loads(content)
            values = judge_value(parsed, metric)
            result = {'status': 'ok', 'metric': metric, 'attempt': attempt, 'values': values, 'parsed': parsed, 'model': raw.get('model'), 'usage': raw.get('usage'), 'seconds': time.monotonic() - started, 'source_field': 'content'}
            write(folder / f'attempt-{attempt}.json', result)
            return result
        except Exception as exc:
            result = {'status': 'error', 'metric': metric, 'attempt': attempt, 'error_type': type(exc).__name__, 'error': str(exc), 'seconds': time.monotonic() - started}
            write(folder / f'attempt-{attempt}.json', result)
    return result


def preflight(out):
    old = ROOT / 'results/multi-bench-20261008T163557Z/ai-idea-bench/evaluation/b001/judge'
    mapping = {'experiment_similarity': 'igi-1', 'motivation_similarity': 'igi-2', 'topic_alignment': 'igt-1'}
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        jobs = []
        for metric, name in mapping.items():
            payload = read(old / name / 'request.json')
            payload.pop('response_format', None)
            jobs.append(pool.submit(judge_call, out / 'preflight' / metric, payload, metric))
        results = [f.result() for f in jobs]
    passed = all(r['status'] == 'ok' for r in results)
    write(out / 'preflight.json', {'passed': passed, 'results': results, 'scope': 'All three official judging request types; saved prior output, not a new candidate score'})
    print('Judge preflight ' + ('PASS' if passed else 'FAILED'), flush=True)
    if not passed:
        raise SystemExit('Do not generate candidates before all score types pass')


def candidate(out, task, condition):
    folder = out / 'calls' / str(task['index']) / condition
    folder.mkdir(parents=True, exist_ok=False)
    workspace = Path(tempfile.mkdtemp(prefix='research-notes-'))
    prompt = task['prompt']
    if condition == 'reflection':
        prompt = REFLECTION + '\n\n' + prompt
    elif condition == 'skills':
        prompt = '/autoresearch:research-mode\n' + prompt
    argv = ['/Users/junjie/.local/bin/claude-research', '-p', '--model', MODEL, '--output-format', 'stream-json', '--input-format', 'stream-json', '--replay-user-messages', '--verbose', '--no-session-persistence', '--permission-mode', 'dontAsk', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}', '--append-system-prompt-file', str(out / 'frozen/system.md'), '--tools', 'Skill', '--allowedTools', 'Skill']
    if condition == 'skills':
        argv.extend(['--plugin-dir', str(out / 'frozen/autoresearch')])
    (folder / 'prompt.txt').write_text(prompt)
    write(folder / 'request.json', {'argv': argv, 'cwd': str(workspace), 'wall_timeout': None})
    start = time.monotonic()
    with (folder / 'stream.jsonl').open('w') as stream, (folder / 'stderr.txt').open('w') as error:
        proc = subprocess.Popen(argv, cwd=workspace, stdin=subprocess.PIPE, stdout=stream, stderr=error, text=True, start_new_session=True)
        write(folder / 'process.json', {'pid': proc.pid, 'started_unix': time.time()})
        proc.communicate(json.dumps({'type': 'user', 'message': {'role': 'user', 'content': prompt}}) + '\n')
    events = [json.loads(line) for line in (folder / 'stream.jsonl').read_text().splitlines() if line.strip()]
    init = next((e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init'), {})
    final = next((e for e in reversed(events) if e.get('type') == 'result'), {})
    calls = []
    outcomes = {}
    models = set()
    for e in events:
        m = e.get('message', {})
        if e.get('type') == 'assistant':
            models.add(m.get('model', 'unknown'))
        content = m.get('content', [])
        if not isinstance(content, list):
            continue
        for b in content:
            if e.get('type') == 'assistant' and b.get('type') == 'tool_use':
                calls.append({'id': b.get('id'), 'name': b.get('name'), 'input': b.get('input')})
            if b.get('type') == 'tool_result':
                outcomes[b.get('tool_use_id')] = not b.get('is_error', False)
    for c in calls:
        c['succeeded'] = outcomes.get(c['id'], False)
    text = final.get('result', '')
    if not isinstance(text, str):
        text = ''
    (folder / 'output.txt').write_text(text)
    status = 'ok' if proc.returncode == 0 and final.get('subtype') == 'success' and not final.get('is_error') and text.strip() else 'error'
    parser = definitions(out / 'frozen/llm.py', ('extract_json_between_markers',))['extract_json_between_markers']
    idea = parser(text)
    parse_ok = isinstance(idea, dict) and all(isinstance(idea.get(k), str) and idea[k].strip() for k in ('Motivation', 'Experiment'))
    complete = parse_ok and all(isinstance(idea.get(k), str) and idea[k].strip() for k in FIELDS[:4]) and all(type(idea.get(k)) in (int, float) and 1 <= idea[k] <= 10 for k in FIELDS[4:])
    name_valid = parse_ok and isinstance(idea.get('Name'), str) and re.fullmatch('[a-z0-9_]+', idea['Name']) is not None
    result = {'index': task['index'], 'condition': condition, 'status': status, 'exit_code': proc.returncode, 'seconds': time.monotonic() - start, 'official_parser_returned_json': idea is not None, 'parser_success': parse_ok, 'all_requested_fields': complete, 'name_format_valid': name_valid, 'thought_marker': 'THOUGHT:' in text, 'idea_marker': 'NEW IDEA JSON:' in text, 'models': sorted(models), 'init': init, 'tool_calls': calls, 'entry_command_seen': any(e.get('type') == 'user' and '<command-name>/autoresearch:research-mode</command-name>' in json.dumps(e.get('message', {})) for e in events), 'usage': final.get('usage'), 'model_usage': final.get('modelUsage'), 'num_turns': final.get('num_turns'), 'estimated_cost_usd': final.get('total_cost_usd'), 'text': text}
    write(folder / 'result.json', result)
    if parse_ok:
        write(folder / 'final_ideas.json', [{'index': task['index'], 'model_result': [idea]}])
    print(str(task['index']) + ' ' + condition + ' ' + status + ' fields=' + str(complete) + ' seconds=' + str(round(result['seconds'], 1)), flush=True)
    return result


def run(out):
    if not read(out / 'preflight.json')['passed']:
        raise SystemExit('Judge preflight must pass')
    tasks = {t['index']: t for t in read(out / 'tasks.json')}
    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool, (out / 'results.jsonl').open('w') as log:
        futures = [pool.submit(candidate, out, tasks[index], condition) for index, condition in read(out / 'schedule.json')]
        for f in concurrent.futures.as_completed(futures):
            result = f.result()
            records.append(result)
            log.write(json.dumps(result, ensure_ascii=False) + '\n')
            log.flush()
    write(out / 'generation-status.json', {'assigned': len(CONDITIONS) * len(tasks), 'recorded': len(records), 'native_successes': sum(r['status'] == 'ok' for r in records), 'complete_fields': sum(r['all_requested_fields'] for r in records)})


def score(out):
    records = [json.loads(line) for line in (out / 'results.jsonl').read_text().splitlines()]
    targets = {r['index']: r for r in read(BENCH / 'data/target_paper_data.json')}
    funcs = definitions(out / 'frozen/compare_gt.py', ('similarity_experiment_plan_w_experiment_plan', 'similarity_motivation_w_motivation', 'generate_alignment_evaluation_prompts'))
    random.Random(928110).shuffle(records)
    mapping = []
    jobs = []
    for i, record in enumerate(records, 1):
        label = 'b' + str(i).zfill(3)
        entry = {'label': label, 'index': record['index'], 'condition': record['condition'], 'scoreable': record['status'] == 'ok' and record['parser_success']}
        mapping.append(entry)
        if not entry['scoreable']:
            continue
        idea = read(out / 'calls' / str(record['index']) / record['condition'] / 'final_ideas.json')[0]['model_result'][0]
        target = targets[record['index']]['summary']
        experiment_target = ''.join(ex['design_name'] + ': ' + ex['description'] + '\n' for ex in target['method']['targeted_designs_details'])
        prompts = {
            'experiment_similarity': funcs['similarity_experiment_plan_w_experiment_plan'](idea['Experiment'], experiment_target),
            'motivation_similarity': funcs['similarity_motivation_w_motivation'](idea['Motivation'], target['motivation']),
            'topic_alignment': funcs['generate_alignment_evaluation_prompts'](target.get('revised_topic') or target['topic'], idea['Motivation'], idea['Experiment']),
        }
        for metric, (system, user) in prompts.items():
            payload = {'model': JUDGE, 'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}], 'temperature': 0.6, 'max_tokens': 8000}
            jobs.append((label, metric, payload))
    write(out / 'blind-mapping.json', mapping)
    scores = []
    def one(job):
        label, metric, payload = job
        result = judge_call(out / 'evaluation' / label / metric, payload, metric)
        print('Score ' + label + ' ' + metric + ' ' + result['status'], flush=True)
        return {'label': label, **result}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        scores = list(pool.map(one, jobs))
    write(out / 'scores.json', scores)
    for entry in mapping:
        if not entry['scoreable']:
            continue
        folder = out / 'evaluation' / entry['label']
        source = read(out / 'calls' / str(entry['index']) / entry['condition'] / 'final_ideas.json')
        successful = {s['metric']: s['parsed'] for s in scores if s['label'] == entry['label'] and s['status'] == 'ok'}
        if all(m in successful for m in ('experiment_similarity', 'motivation_similarity')):
            ideas = json.loads(json.dumps(source))
            ideas[0]['model_result'][0]['IGI'] = {'motivation_similarity': successful['experiment_similarity'], 'experiment_plan_similarity': successful['motivation_similarity']}
            write(folder / 'IGI.json', ideas)
        if 'topic_alignment' in successful:
            ideas = json.loads(json.dumps(source))
            ideas[0]['model_result'][0]['IGT2P'] = successful['topic_alignment']
            write(folder / 'IGT2P.json', ideas)
    write(out / 'score-status.json', {'assigned_logical': len(records) * 3, 'requested_logical': len(jobs), 'valid_logical': sum(s['status'] == 'ok' for s in scores)})


def summarize(out):
    records = [json.loads(line) for line in (out / 'results.jsonl').read_text().splitlines()]
    mapping = {r['label']: r for r in read(out / 'blind-mapping.json')}
    scores = read(out / 'scores.json')
    summary = {}
    for condition in CONDITIONS:
        runs = [r for r in records if r['condition'] == condition]
        selected = [s for s in scores if mapping[s['label']]['condition'] == condition and s['status'] == 'ok']
        values = {m: [] for m in ('experiment_similarity', 'motivation_similarity', 'motivation_alignment', 'experiment_alignment')}
        for s in selected:
            if s['metric'] == 'topic_alignment':
                values['motivation_alignment'].append(s['values'][0])
                values['experiment_alignment'].append(s['values'][1])
            else:
                values[s['metric']].append(s['values'][0])
        usage = {k: sum((r.get('usage') or {}).get(k, 0) or 0 for r in runs) for k in ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens', 'output_tokens')}
        summary[condition] = {'assigned': len(runs), 'native_successes': sum(r['status'] == 'ok' for r in runs), 'official_parser_success': sum(r['official_parser_returned_json'] for r in runs), 'scoring_fields_valid': sum(r['parser_success'] for r in runs), 'all_requested_fields': sum(r['all_requested_fields'] for r in runs), 'successful_skill_tool_calls': sum(c['name'] == 'Skill' and c['succeeded'] for r in runs for c in r['tool_calls']), 'successful_research_leaf_calls': sum(c['name'] == 'Skill' and c['succeeded'] and c.get('input', {}).get('skill', '').startswith('autoresearch:') and c['input']['skill'] != 'autoresearch:research-mode' for r in runs for c in r['tool_calls']), 'official_format_markers': sum(r['thought_marker'] and r['idea_marker'] for r in runs), 'median_seconds': statistics.median(r['seconds'] for r in runs), 'range_seconds': [min(r['seconds'] for r in runs), max(r['seconds'] for r in runs)], 'usage': usage, 'metrics': {m: {'values': v, 'scored': len(v), 'denominator': 3, 'mean': statistics.mean(v) if len(v) == 3 else None} for m, v in values.items()}}
    write(out / 'summary.json', {'conditions': summary, 'quality_status': 'COMPLETE' if all(m['mean'] is not None for c in summary.values() for m in c['metrics'].values()) else 'INCOMPLETE', 'limitations': ['Three tasks, one run each', 'Local full-text input interface, not author SciPDF/summary preprocessing', 'Official prompt parameter num_reflections=1; autonomous Skills, no author multi-round reproduction', 'Generic reflection baseline is locally defined', 'Timing descriptive, billing unknown']})
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'preflight', 'run', 'score', 'summarize'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    globals()[args.phase](args.output.resolve())

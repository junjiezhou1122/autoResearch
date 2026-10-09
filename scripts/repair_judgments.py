import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.runtime / 'src'))
    from researchbench.generation import parse_matched_score
    records = [json.loads(line) for line in (args.source / 'results.jsonl').read_text().splitlines()]
    if len(records) != 36:
        raise SystemExit('Finish the full 36-item blinded scoring attempt first.')
    args.output.mkdir(parents=True, exist_ok=False)
    mapping = json.loads((args.source / 'mapping.json').read_text())
    (args.output / 'mapping.json').write_text(json.dumps(mapping, indent=2) + '\n')
    (args.output / 'config.json').write_text(json.dumps({'source': str(args.source), 'policy': 'One blinded retry for every failed judge response, same prompt/model/temperature, max_tokens increased to 16384. Generation outputs are unchanged.', 'max_tokens': 16384}, indent=2) + '\n')

    def retry(record):
        request = json.loads((args.source / f"{record['item']}-request.json").read_text())
        request['max_tokens'] = 16384
        (args.output / f"{record['item']}-request.json").write_text(json.dumps(request, ensure_ascii=False, indent=2) + '\n')
        started = time.monotonic()
        revised = dict(record, original_status=record['status'], retry_count=1)
        try:
            response = httpx.post('http://127.0.0.1:3425/v1/chat/completions', headers={'Authorization': 'Bearer magpie'}, json=request, timeout=240)
            response.raise_for_status()
            body = response.json()
            (args.output / f"{record['item']}-response.json").write_text(json.dumps(body, ensure_ascii=False, indent=2) + '\n')
            choice = body['choices'][0]
            text = choice['message'].get('content') or ''
            score = parse_matched_score(text)
            if choice.get('finish_reason') == 'length' or score is None or not 0 <= score <= 5:
                raise ValueError('Incomplete judge score')
            revised.update({'status': 'ok', 'score': score, 'reason': text, 'usage': body.get('usage', {}), 'returned_model': body.get('model'), 'finish_reason': choice.get('finish_reason')})
            revised.pop('error', None)
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as error:
            revised['status'] = 'error'
            revised['error'] = type(error).__name__
        revised['seconds'] = time.monotonic() - started
        return revised

    completed = {record['item']: record for record in records}
    failures = [record for record in records if record['status'] == 'error']
    with ThreadPoolExecutor(max_workers=3) as pool:
        for future in as_completed([pool.submit(retry, record) for record in failures]):
            record = future.result()
            completed[record['item']] = record
            print(record['item'], record['status'], record.get('score'), flush=True)
    final = sorted(completed.values(), key=lambda record: record['item'])
    (args.output / 'results.jsonl').write_text(''.join(json.dumps(record, ensure_ascii=False) + '\n' for record in final))
    summary = {}
    for condition in ('direct', 'reflection', 'skill-prompt'):
        subset = [record for record in final if mapping[record['item']]['condition'] == condition]
        valid = [record['score'] for record in subset if record['status'] == 'ok']
        errors = sum(record['status'] == 'error' for record in subset)
        generation_failures = sum(record['status'] == 'generation_failure' for record in subset)
        summary[condition] = {'expected': 12, 'scored': len(valid), 'generation_failures': generation_failures, 'judge_failures': errors, 'judge_retries': sum(record.get('retry_count', 0) for record in subset), 'mean_score': sum(valid) / 12 if errors == 0 else None, 'scorer': 'GENERATION_FAILURE_AS_ZERO_PILOT_EXTENSION' if generation_failures else 'OFFICIAL_PROMPT_AND_PARSER', 'score_range': [min(valid), max(valid)] if valid else None, 'per_task': [{**mapping[record['item']], 'score': record.get('score'), 'status': record['status']} for record in subset]}
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    if any(record['status'] == 'error' for record in final):
        raise SystemExit(1)


if __name__ == '__main__':
    main()

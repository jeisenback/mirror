#!/usr/bin/env python3
"""Validate JSON trace files under `docs/traces/` against `docs/trace_schema.json`.

Exits with code 0 if all traces validate, else non-zero and prints failures.
"""
import os
import sys
import json
from glob import glob
try:
    import jsonschema
    _HAS_JSONSCHEMA = True
except Exception:
    _HAS_JSONSCHEMA = False

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCHEMA_PATH = os.path.join(ROOT, 'docs', 'trace_schema.json')
TRACES_GLOBS = [
    os.path.join(ROOT, 'docs', 'traces', '*.json'),
    os.path.join(ROOT, 'examples', 'docs', 'traces', '*.json'),
]

def load_schema(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def iter_steps_from_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        txt = f.read().strip()
        if not txt:
            return []
        try:
            obj = json.loads(txt)
            if isinstance(obj, list):
                return obj
            if isinstance(obj, dict):
                return [obj]
        except Exception:
            # try line-delimited JSON (jsonl)
            steps = []
            for line in txt.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    steps.append(json.loads(line))
                except Exception:
                    raise
            return steps

def validate_step(step, schema):
    if _HAS_JSONSCHEMA:
        try:
            jsonschema.validate(step, schema)
            return True, None
        except jsonschema.ValidationError as e:
            return False, str(e.message)
    # fallback lightweight validation without external deps: check required and types per schema keys
    if 'step_id' not in step or not isinstance(step['step_id'], str):
        return False, 'missing or invalid step_id'
    # optional numeric fields
    for n in ('confidence', 'tokens_used', 'latency'):
        if n in step and not isinstance(step[n], (int, float)):
            return False, f'field {n} must be number'
    return True, None

def main():
    schema = load_schema(SCHEMA_PATH)
    files = []
    for g in TRACES_GLOBS:
        files.extend(glob(g))
    if not files:
        print('No trace files found in docs/traces')
        return 0
    failures = 0
    for p in files:
        try:
            steps = iter_steps_from_file(p)
        except Exception as e:
            print('ERROR parsing', p, e)
            failures += 1
            continue
        for i, s in enumerate(steps):
            ok, msg = validate_step(s, schema)
            if not ok:
                print(f'INVALID {p} [{i}]: {msg} -- {s}')
                failures += 1
    if failures:
        print(f'Validation failed: {failures} problems')
        return 2
    print('All trace files validate against schema (basic checks)')
    return 0

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Export prototype belief-store traces to a lightweight OTLP-like JSON file.

This converter reads trace JSON files from `docs/traces` and
`examples/docs/traces` and writes `docs/auto/otlp_traces.json` containing
a simplified OTLP-ish structure with `resourceSpans` and `spans`.

It's intentionally lightweight for the prototype; a production exporter
should use OpenTelemetry SDKs and export via OTLP/gRPC or OTLP/HTTP.
"""
import os
import sys
import json
import time
from glob import glob
from uuid import uuid4

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TRACES_GLOBS = [
    os.path.join(ROOT, 'docs', 'traces', '*.json'),
    os.path.join(ROOT, 'examples', 'docs', 'traces', '*.json'),
]
OUT_PATH = os.path.join(ROOT, 'docs', 'auto', 'otlp_traces.json')


def to_nano(ts):
    # Accept numeric seconds (float/int) or millisecond timestamps
    if ts is None:
        return None
    try:
        if isinstance(ts, (int, float)):
            v = float(ts)
            # heuristic: if > 1e12 assume already ns
            if v > 1e12:
                return int(v)
            # if >1e9 it's probably milliseconds
            if v > 1e9:
                return int(v * 1e6)
            return int(v * 1e9)
        # try parse ISO-like string via time parsing fallback
        # best-effort: not strict
        try:
            # removes microseconds if present
            tm = time.strptime(ts.split('.')[0], '%Y-%m-%dT%H:%M:%S')
            return int(time.mktime(tm) * 1e9)
        except Exception:
            return None
    except Exception:
        return None


def read_steps():
    files = []
    for g in TRACES_GLOBS:
        files.extend(glob(g))
    steps_by_file = []
    for p in sorted(files):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    steps = data
                elif isinstance(data, dict):
                    steps = [data]
                else:
                    steps = []
        except Exception:
            # try JSONL
            steps = []
            with open(p, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        steps.append(json.loads(line))
                    except Exception:
                        continue
        steps_by_file.append((p, steps))
    return steps_by_file


def step_to_span(step):
    trace_id = step.get('trace_id') or step.get('task_id') or str(uuid4())
    span_id = step.get('span_id') or step.get('step_id') or str(uuid4())
    name = step.get('name') or step.get('type') or 'step'
    start = to_nano(step.get('start_time') or step.get('timestamp') or step.get('time'))
    end = to_nano(step.get('end_time'))
    if end is None and start is not None and 'latency' in step:
        try:
            end = start + int(float(step.get('latency', 0)) * 1e9)
        except Exception:
            end = None

    attributes = []
    for k, v in (step.items() if isinstance(step, dict) else []):
        if k in ('trace_id', 'span_id', 'step_id', 'task_id', 'start_time', 'end_time', 'time'):
            continue
        # represent numbers and strings simply
        val = None
        if isinstance(v, (str, int, float, bool)):
            val = {'stringValue': str(v)}
        elif v is None:
            val = {'stringValue': 'null'}
        else:
            try:
                val = {'stringValue': json.dumps(v)}
            except Exception:
                val = {'stringValue': str(v)}
        attributes.append({'key': k, 'value': val})

    span = {
        'traceId': str(trace_id),
        'spanId': str(span_id),
        'name': name,
        'startTimeUnixNano': start,
        'endTimeUnixNano': end,
        'attributes': attributes,
    }
    if 'error' in step:
        span['status'] = {'code': 2, 'message': str(step.get('error'))}
    return span


def build_otlp(steps_by_file):
    resource_spans = []
    for p, steps in steps_by_file:
        spans = [step_to_span(s) for s in steps]
        resource = {
            'attributes': [
                {'key': 'source', 'value': {'stringValue': p}},
                {'key': 'file_count', 'value': {'stringValue': str(len(steps))}},
            ]
        }
        resource_spans.append({'resource': resource, 'instrumentationLibrarySpans': [{'spans': spans}]})
    return {'resourceSpans': resource_spans}


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    steps_by_file = read_steps()
    out = build_otlp(steps_by_file)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    print('Wrote OTLP-like traces to', OUT_PATH)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Merge trace JSON files into a simple dependency graph JSON for docs.

Produces docs/auto/merged_graph.json with nodes and edges.
"""
import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# search for trace dirs anywhere under the repo (e.g., examples/prototype/docs/traces)
trace_dirs = list(ROOT.glob('**/docs/traces'))
TRACES_DIR = None
if trace_dirs:
    TRACES_DIR = trace_dirs[0]
else:
    TRACES_DIR = ROOT / 'docs' / 'traces'
OUT_DIR = ROOT / 'docs' / 'auto'
OUT_DIR.mkdir(parents=True, exist_ok=True)

nodes = {}
edges = []

if not TRACES_DIR.exists():
    print('No traces directory, nothing to merge:', TRACES_DIR)
    exit(0)

trace_files = []
for td in list(ROOT.glob('**/docs/traces')):
    trace_files.extend([p for p in td.iterdir() if p.suffix == '.json'])
trace_files = sorted(trace_files)
for tf in trace_files:
    try:
        with open(tf, 'r', encoding='utf-8') as f:
            trace = json.load(f)
    except Exception as e:
        print('Failed to load', tf, e)
        continue
    # trace is expected to be list of belief records or dict with steps
    steps = trace if isinstance(trace, list) else trace.get('steps', [])
    prev_id = None
    for s in steps:
        sid = s.get('step_id') or s.get('id') or None
        if not sid:
            continue
        if sid not in nodes:
            nodes[sid] = {
                'id': sid,
                'task_id': s.get('task_id'),
                'label': s.get('label') or s.get('step_type') or '',
                'confidence': s.get('confidence'),
                'raw': s,
            }
        if prev_id:
            edges.append({'src': prev_id, 'dst': sid, 'kind': 'sequence', 'trace': tf.name})
        prev_id = sid

out = {'nodes': list(nodes.values()), 'edges': edges, 'trace_files': [p.name for p in trace_files]}
out_path = OUT_DIR / 'merged_graph.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2)

print('Wrote merged graph to', out_path)

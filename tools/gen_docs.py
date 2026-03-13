#!/usr/bin/env python3
"""Simple docs generator for prototype: runs emit_node.py and writes docs/auto/<id>.md
"""
import os
import sys
import json
import re
import subprocess
from datetime import datetime
import hashlib
import argparse
import logging
import time
import tempfile
try:
    import yaml
except Exception:
    yaml = None

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# CLI
parser = argparse.ArgumentParser(description='Generate docs/auto from emit_node.py')
parser.add_argument('--emit-script', default=os.environ.get('EMIT_SCRIPT', os.path.join(ROOT, 'examples', 'prototype', 'docs', 'hooks', 'emit_node.py')),
                    help='Path to emit_node.py (or script that prints JSON)')
parser.add_argument('--out-dir', default=os.environ.get('OUT_DIR', os.path.join(ROOT, 'docs', 'auto')),
                    help='Output directory for generated docs')
parser.add_argument('--force', action='store_true', help='Always write files even if unchanged')
parser.add_argument('--quiet', action='store_true', help='Minimal output')
parser.add_argument('--log-json', action='store_true', help='Emit logs as JSON lines')
parser.add_argument('--verbose', action='store_true', help='Verbose logging')
args = parser.parse_args()

EMIT_SCRIPT = args.emit_script
OUT_DIR = args.out_dir

os.makedirs(OUT_DIR, exist_ok=True)

# logging
logger = logging.getLogger('gen_docs')
if args.log_json:
    def _json_log(level, msg, **extra):
        rec = {'ts': int(time.time()), 'level': level, 'msg': msg}
        rec.update(extra)
        print(json.dumps(rec, ensure_ascii=False))
    log = lambda level, msg, **extra: _json_log(level, msg, **extra)
else:
    ch = logging.StreamHandler()
    fmt = '%(asctime)s %(levelname)s: %(message)s'
    ch.setFormatter(logging.Formatter(fmt))
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    def log(level, msg, **extra):
        if level == 'info':
            logger.info(msg)
        elif level == 'warning':
            logger.warning(msg)
        elif level == 'error':
            logger.error(msg)
        else:
            logger.debug(msg)

# simple cache file to avoid rewriting unchanged files
CACHE_PATH = os.path.join(OUT_DIR, '.gen_docs_cache.json')
try:
    with open(CACHE_PATH, encoding='utf-8') as cf:
        _cache = json.load(cf)
except Exception:
    _cache = {}

if not os.path.exists(EMIT_SCRIPT):
    log('error', f'emit script not found: {EMIT_SCRIPT}')
    sys.exit(2)

try:
    raw = subprocess.check_output([sys.executable, EMIT_SCRIPT], cwd=ROOT, stderr=subprocess.STDOUT)
except subprocess.CalledProcessError as e:
    out = e.output.decode('utf-8', errors='replace') if getattr(e, 'output', None) else str(e)
    log('error', f'emit script failed (exit {e.returncode}): {out}')
    sys.exit(3)

try:
    node = json.loads(raw.decode('utf-8'))
except Exception as e:
    log('error', f'Failed to parse JSON from emit script: {e}')
    sys.exit(4)
nodes = node if isinstance(node, list) else [node]

written = []
for node in nodes:
    # build a safe filename from the canonical id
    cid = node.get('id') or 'node'
    # sanitize filename to safe chars
    filename = re.sub(r'[^A-Za-z0-9_.-]', '_', cid.replace('::', '__').replace('/', '_')) + '.md'
    path = os.path.join(OUT_DIR, filename)

    front = {
        'id': node.get('id'),
        'type': node.get('type'),
        # prefer an explicit display name, fall back to id
        'display_name': node.get('display_name') or cid,
        'path': node.get('path'),
        'description': node.get('description'),
        'tags': node.get('tags'),
        'canonical_url': node.get('canonical_url')
    }

    # build content string
    parts = []
    if yaml is not None:
        try:
            front_yaml = yaml.safe_dump(front, sort_keys=False, default_flow_style=False)
            parts.append('---\n')
            parts.append(front_yaml)
            parts.append('---\n\n')
        except Exception:
            fm_lines = ['---\n']
            for k, v in front.items():
                if v is None:
                    v_str = ''
                else:
                    v_str = str(v)
                    if any(ch in v_str for ch in ':\n"\'"#{}[],&*?|<>!-') or v_str.strip() != v_str:
                        v_str = '"' + v_str.replace('\\', '\\\\').replace('"', '\\"') + '"'
                fm_lines.append(f"{k}: {v_str}\n")
            fm_lines.append('\n')
            parts.extend(fm_lines)
    else:
        fm_lines = ['---\n']
        for k, v in front.items():
            if v is None:
                v_str = ''
            else:
                v_str = str(v)
                if any(ch in v_str for ch in ':\n"\'"#{}[],&*?|<>!-') or v_str.strip() != v_str:
                    v_str = '"' + v_str.replace('\\', '\\\\').replace('"', '\\"') + '"'
            fm_lines.append(f"{k}: {v_str}\n")
        fm_lines.append('\n')
        parts.extend(fm_lines)

    parts.append(f"# {front.get('display_name')}\n\n")
    parts.append(f"**Type**: {front.get('type')}  \n")
    parts.append(f"**Source path**: {front.get('path')}\n\n")
    parts.append('Generated by tools/gen_docs.py from emit_node.py\n')

    content = ''.join(parts)

    # atomic write with cache check
    sha = hashlib.sha256(content.encode('utf-8')).hexdigest()
    prev = _cache.get(filename)
    if prev == sha and not args.force:
        log('info', f'Unchanged {path}')
    else:
        try:
            fd, tmp_path = tempfile.mkstemp(dir=OUT_DIR, prefix=filename + '.tmp.')
            with os.fdopen(fd, 'w', encoding='utf-8') as tf:
                tf.write(content)
            os.replace(tmp_path, path)
            _cache[filename] = sha
            log('info', f'Wrote {path}')
        except Exception as e:
            log('error', f'Failed to write {path}: {e}')
            sys.exit(5)
    written.append(path)

for p in written:
    log('info', f'Generated file: {p}')
# regenerate index.md with badges and a generated file listing
index_path = os.path.join(OUT_DIR, 'index.md')
# attempt to infer owner/repo from git remote
repo_spec = None
try:
    remote = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url'], cwd=ROOT)
    remote = remote.decode('utf-8').strip()
    m = re.search(r'[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$', remote)
    if m:
        repo_spec = f"{m.group('owner')}/{m.group('repo')}"
except Exception:
    repo_spec = None

if repo_spec:
    ci_badge = f"https://github.com/{repo_spec}/actions/workflows/ci.yml/badge.svg"
    pages_badge = f"https://github.com/{repo_spec}/actions/workflows/deploy_pages.yml/badge.svg"
else:
    ci_badge = None
    pages_badge = None
date_str = datetime.utcnow().strftime('%Y-%m-%d')
date_badge = f"https://img.shields.io/badge/Generated-{date_str}-blue"

lines = []
lines.append('---')
lines.append('id: index')
lines.append('title: Prototype Documentation')
lines.append('---\n')
lines.append('# Prototype Documentation\n')
if repo_spec and ci_badge and pages_badge:
    lines.append(f'![CI badge]({ci_badge})  ')
    lines.append(f'![Pages]({pages_badge})  ![Generated {date_str}]({date_badge})\n')
else:
    lines.append(f'![Generated {date_str}]({date_badge})\n')
lines.append('This folder contains generated documentation nodes for the prototype. Files are produced by `examples/prototype/docs/hooks/emit_node.py` and collected into `docs/auto` by `tools/gen_docs.py`.\n')
lines.append('## Generated nodes\n')

# collect generated markdown files
md_files = sorted([f for f in os.listdir(OUT_DIR) if f.endswith('.md') and f != 'index.md'])
for fn in md_files:
    title = None
    try:
        with open(os.path.join(OUT_DIR, fn), encoding='utf-8') as fh:
            for ln in fh:
                if ln.strip().startswith('# '):
                    title = ln.strip().lstrip('# ').strip()
                    break
    except Exception:
        title = None
    if not title:
        title = fn
    lines.append(f'- [{title}]({fn})')

lines.append('\nGenerated by `tools/gen_docs.py`.')

# write index atomically only when changed
index_content = '\n'.join(lines) + '\n'
index_sha = hashlib.sha256(index_content.encode('utf-8')).hexdigest()
prev_index = _cache.get('index.md')
if prev_index == index_sha:
    print('Unchanged', index_path)
else:
    with open(index_path, 'w', encoding='utf-8') as ix:
        ix.write(index_content)
    _cache['index.md'] = index_sha
    print('Wrote index', index_path)

# persist cache
try:
    with open(CACHE_PATH, 'w', encoding='utf-8') as cf:
        json.dump(_cache, cf, indent=2, ensure_ascii=False)
except Exception:
    pass

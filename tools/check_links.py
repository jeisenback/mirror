#!/usr/bin/env python3
"""Simple markdown local-link checker: ensures relative links point to existing files under repo."""
import sys
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if len(sys.argv) < 2:
    print('Usage: check_links.py <docs-dir>')
    sys.exit(2)

docs_dir = os.path.join(ROOT, sys.argv[1])
if not os.path.isdir(docs_dir):
    print('Docs dir not found:', docs_dir)
    sys.exit(1)

link_re = re.compile(r'\[[^\]]+\]\(([^)]+)\)')
errors = 0
for root, _, files in os.walk(docs_dir):
    for fn in files:
        if not fn.endswith('.md'):
            continue
        path = os.path.join(root, fn)
        with open(path, 'r', encoding='utf-8') as f:
            txt = f.read()
        for m in link_re.finditer(txt):
            target = m.group(1).strip()
            if target.startswith('http://') or target.startswith('https://') or target.startswith('#'):
                continue
            # resolve relative path
            tgt_path = os.path.normpath(os.path.join(root, target))
            if not os.path.exists(tgt_path):
                print(f'BROKEN LINK in {path}: {target} -> {tgt_path} (missing)')
                errors += 1

if errors:
    print(f'Found {errors} broken local links')
    sys.exit(1)
print('No broken local links found')
sys.exit(0)

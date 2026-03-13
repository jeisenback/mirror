#!/usr/bin/env python3
"""Generate mkdocs.yml nav section from docs/auto markdown files.

Writes a cleaned `mkdocs.yml` with `nav` containing Home and Generated sections.
"""
import os
import re
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DOCS_AUTO = os.path.join(ROOT, 'docs', 'auto')
MKDOCS = os.path.join(ROOT, 'mkdocs.yml')


def title_from_file(path):
    # prefer YAML front-matter display_name
    try:
        with open(path, encoding='utf-8') as fh:
            text = fh.read()
    except Exception:
        return os.path.basename(path)
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    if m:
        try:
            meta = yaml.safe_load(m.group(1))
            if meta and meta.get('display_name'):
                return str(meta.get('display_name'))
        except Exception:
            pass
    # fallback to first H1
    for ln in text.splitlines():
        if ln.startswith('# '):
            return ln.lstrip('# ').strip()
    return os.path.basename(path)


def build_nav():
    files = [f for f in os.listdir(DOCS_AUTO) if f.endswith('.md')]
    files.sort()
    # ensure index.md first
    if 'index.md' in files:
        files.remove('index.md')
        files.insert(0, 'index.md')

    generated = []
    for fn in files:
        if fn == 'index.md':
            continue
        title = title_from_file(os.path.join(DOCS_AUTO, fn))
        generated.append({title: f'auto/{fn}'})

    nav = [{ 'Home': 'auto/index.md' }, {'Generated': generated}]
    return nav


def write_mkdocs(nav):
    cfg = {
        'site_name': 'Framework Prototype Docs',
        'docs_dir': 'docs',
        'site_dir': 'site',
        'theme': {'name': 'material'},
        'nav': nav,
    }
    with open(MKDOCS, 'w', encoding='utf-8') as fh:
        yaml.safe_dump(cfg, fh, sort_keys=False)


def main():
    if not os.path.isdir(DOCS_AUTO):
        print('No docs/auto directory; run tools/gen_docs.py first')
        return
    nav = build_nav()
    write_mkdocs(nav)
    print('mkdocs.yml updated with generated nav')


if __name__ == '__main__':
    main()

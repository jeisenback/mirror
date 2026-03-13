#!/usr/bin/env python3
"""Run markdownlint on generated docs, with helpful install hints.

Tries the following (in order):
- `markdownlint` (global)
- `npx markdownlint-cli` (requires Node/npm)

Exits with the linter's exit code, or 0 if skipped.
"""
import shutil
import subprocess
import sys
import os

PATTERN = os.environ.get('MD_PATTERN', 'docs/auto/**/*.md')


def main():
    # prefer global markdownlint
    if shutil.which('markdownlint'):
        cmd = ['markdownlint', PATTERN]
        print('Running: ' + ' '.join(cmd))
        return subprocess.call(cmd)

    # try npx (comes with npm)
    if shutil.which('npx'):
        cmd = ['npx', 'markdownlint-cli', PATTERN]
        print('Running via npx: ' + ' '.join(cmd))
        return subprocess.call(cmd)

    print('markdownlint not found. Install via:')
    print('  npm install -g markdownlint-cli')
    print('or run:')
    print('  npx markdownlint-cli "docs/auto/**/*.md"')
    return 0


if __name__ == '__main__':
    sys.exit(main())

"""Simple promotion runner: given a proposal (JSON file or STDIN), run the
prototype product tests and, if they pass, append a promotion record to
docs/auto/promotions.jsonl.

This is intentionally simple for the prototype; production should include
sandboxing, policy checks, artifact signing, and audit trails.
"""
import json
import os
import subprocess
import sys
import time


def run_tests():
    cmd = [sys.executable, '-u', 'examples/prototype/tests/run_product_tests.py']
    try:
        subprocess.check_call(cmd)
        return True, 'tests passed'
    except subprocess.CalledProcessError as e:
        return False, f'tests failed (code {e.returncode})'


def promote(proposal: dict, out_path: str = 'docs/auto/promotions.jsonl'):
    ok, msg = run_tests()
    record = {
        'proposal': proposal,
        'promoted': ok,
        'message': msg,
        'time': time.time(),
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')
    return record


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, 'r', encoding='utf-8') as f:
            proposal = json.load(f)
    else:
        proposal = json.load(sys.stdin)

    rec = promote(proposal)
    print(json.dumps(rec, indent=2))


if __name__ == '__main__':
    main()

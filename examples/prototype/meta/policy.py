import os
import json
import shutil
import subprocess
from typing import Any, Dict


def opa_available() -> bool:
    return shutil.which('opa') is not None


def evaluate_policy(input_obj: Dict[str, Any], policy_path: str, query: str = 'data.main.allow') -> Dict[str, Any]:
    """Evaluate a Rego policy using the `opa` CLI if available.

    Returns a dict with keys: `allowed` (bool), `opa_available` (bool), `raw` (CLI output or message).
    When `opa` is not installed, the function returns permissive result but includes a warning.
    """
    if not os.path.exists(policy_path):
        return {'allowed': True, 'opa_available': False, 'raw': f'policy not found: {policy_path}'}

    if not opa_available():
        return {'allowed': True, 'opa_available': False, 'raw': 'opa CLI not available; permissive fallback'}

    # write input to temp file
    inp_path = policy_path + '.input.json'
    try:
        with open(inp_path, 'w', encoding='utf-8') as f:
            json.dump(input_obj, f)

        cmd = ['opa', 'eval', '-i', inp_path, '-d', policy_path, query, '--format', 'json']
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        res = json.loads(out.decode('utf-8'))
        # OPA's JSON has 'result' -> list of expressions
        allowed = False
        raw = res
        if isinstance(res, dict) and res.get('result'):
            # inspect first expression's value
            try:
                v = res['result'][0]['expressions'][0]['value']
                # accept boolean or object with allow key
                if isinstance(v, bool):
                    allowed = v
                elif isinstance(v, dict) and 'allow' in v:
                    allowed = bool(v['allow'])
            except Exception:
                pass

        return {'allowed': allowed, 'opa_available': True, 'raw': raw}
    finally:
        try:
            if os.path.exists(inp_path):
                os.remove(inp_path)
        except Exception:
            pass

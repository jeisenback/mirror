import subprocess
import sys
import os
import json
import urllib.request
import urllib.error

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SCRIPTS = [
    os.path.join('examples', 'prototype', 'tests', 'run_tests.py'),
    os.path.join('examples', 'prototype', 'tests', 'run_product_tests.py'),
]

results = []
for s in SCRIPTS:
    print('Running', s)
    rc = subprocess.call([sys.executable, s], cwd=ROOT)
    results.append((s, rc))
    # attempt to find trace file for this script and POST to meta/analyze
    try:
        traces_dir = os.path.join(ROOT, 'docs', 'traces')
        if os.path.isdir(traces_dir):
            # find newest trace for this script
            prefix = os.path.basename(s).replace('.py', '')
            matches = [f for f in os.listdir(traces_dir) if f.startswith(prefix)]
            if matches:
                latest = sorted(matches)[-1]
                path = os.path.join(traces_dir, latest)
                with open(path, 'r', encoding='utf-8') as f:
                    trace = json.load(f)
                # build minimal trace payload expected by meta service
                payload = {'run_id': latest, 'steps': trace}
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request('http://127.0.0.1:8001/meta/analyze', data=data, headers={'Content-Type': 'application/json'})
                try:
                    resp = urllib.request.urlopen(req, timeout=2)
                    an = resp.read().decode('utf-8')
                    out_dir = os.path.join(ROOT, 'docs', 'analysis')
                    os.makedirs(out_dir, exist_ok=True)
                    with open(os.path.join(out_dir, latest.replace('.json', '_analysis.json')), 'w', encoding='utf-8') as af:
                        af.write(an)
                    print('Posted trace', latest, 'to meta/analyze; analysis saved')
                except urllib.error.URLError:
                    print('Meta service not reachable; skipping analysis')
    except Exception:
        pass

ok = all(rc == 0 for _, rc in results)
with open(os.path.join(ROOT, 'docs', 'acceptance_report.txt'), 'w', encoding='utf-8') as f:
    for s, rc in results:
        f.write(f"{s}: {'PASS' if rc==0 else 'FAIL'} (rc={rc})\n")
    f.write('\nOverall: ' + ('PASS' if ok else 'FAIL') + '\n')

print('Acceptance run complete. Report written to docs/acceptance_report.txt')
if not ok:
    sys.exit(1)

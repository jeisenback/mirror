Prototype Runbook

Purpose
- Quick operational guide for running the Minimal Viable Engine (MVE) prototype locally and in CI.

Prerequisites
- Python 3.11
- Optional: Redis for the Redis Streams adapter

Setup (local)
1. Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1    # PowerShell on Windows
# or
.venv/bin/activate             # bash
```

2. Install dev requirements

```bash
pip install -r requirements-dev.txt
pip install -r examples/prototype/requirements.txt
```

Running the prototype scenarios
- Run sales + product scenario tests (no external services required):

```bash
python examples/prototype/tests/run_tests.py
python examples/prototype/tests/run_product_tests.py
```

Starting the meta-reasoner service (optional)

```bash
python examples/prototype/meta/run_service.py
# service runs at http://127.0.0.1:8001
```

Docs generation

```bash
python tools/gen_docs.py
python tools/check_links.py docs/auto
mkdocs build   # optional to build the site
```

Acceptance tests
- Run the acceptance harness which executes scenario tests and reports status:

```bash
python examples/prototype/tests/acceptance_tests.py
```

Troubleshooting
- Module import errors: ensure working directory is repo root and virtualenv is activated.
- Redis errors: ensure Redis is running and `examples/prototype/requirements.txt` dependencies are installed.

Next steps for operators
- Add a Redis instance to CI for integration tests.
- Add secrets management and OPA policy checks into CI pipeline.
- Wire artifact publishing from `tools/gen_docs.py` output into the Spec Registry.

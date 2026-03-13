# Minimal Agent Platform Prototype

This repository contains a minimal, auditable, token-efficient prototype for an agent platform. It demonstrates core ideas: an async-first executor, message bus adapters (in-memory, Redis Streams), a budgeted model provider, belief-store tracing, domain adapters, and a meta-reasoner.

Quick start (developer)

1. Create and activate a Python virtual environment (recommended):

```bash
python -m venv venv
source venv/Scripts/activate    # Windows PowerShell: venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

2. Run the local test scenarios (no external services required):

```bash
python -u examples/prototype/tests/run_tests.py
python -u examples/prototype/tests/run_product_tests.py
```

Async / Redis (optional)

- To exercise the async Redis Streams path and smoke test, start Redis locally and set `REDIS_URL`.

```bash
docker run -p 6379:6379 --name redis -d redis:7
export REDIS_URL=redis://localhost:6379/0   # Windows: set REDIS_URL=redis://localhost:6379/0
python -u examples/prototype/tests/run_redis_smoke.py
```

CI

- The GitHub Actions workflow in `.github/workflows/ci.yml` installs dev and prototype requirements, runs the unit scenarios, generates docs, and—if available—starts a Redis service and runs the async smoke test.

Docs & traces

- Doc nodes are emitted by `examples/prototype/docs/hooks/emit_node.py` and processed by `tools/gen_docs.py` into `docs/auto/`.
- Runtime traces and belief-store exports are written to `docs/traces/` and merged by `tools/merge_graphs.py` into `docs/auto/merged_graph.json` for inspection.

Previewing docs locally

- Install MkDocs and the Material theme, then serve the generated docs folder:

```bash
pip install mkdocs mkdocs-material
python tools/gen_docs.py
mkdocs serve --dev-addr 0.0.0.0:8000
```

This will build a local server at http://127.0.0.1:8000 showing the contents of `docs/auto`.

Architecture

- See `docs/ADR/0001-core-architecture.md` for the async-first architecture rationale and consequences.

Developer notes

- The codebase is async-first: prefer `AsyncTaskExecutor` and async adapters in server contexts. `TaskExecutor` is a sync convenience wrapper for local scripts and tests (it runs the async executor via `asyncio.run`).
- Token accounting is implemented using `tiktoken` when available; the budget wrapper falls back to a naive counter if not present.
- OPA policy hooks live under `examples/prototype/meta/policy.py` and are used by the meta-reasoner/promotion paths.

Contributing

- Follow the ADRs and update `docs/ADR/` for major design changes.
- Add tests in `examples/prototype/tests/` and ensure CI passes before merging.

---
Generated on 2026-03-13 by the prototype automation.

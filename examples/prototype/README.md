Minimal Prototype (MVE) - examples/prototype

Purpose
- Simple, token-efficient prototype demonstrating: executor, in-memory bus, mock Model Provider, Sales adapter, skill, belief store, and a test runner.

Run locally
- Run the test scenario (no external deps required):

```bash
python examples/prototype/tests/run_tests.py
```

Async / Redis
- The runtime prefers an async Redis Streams bus when `REDIS_URL` is set. To run the async path locally, start Redis and set `REDIS_URL`:

```bash
# start redis (linux/mac)
docker run -p 6379:6379 --name redis -d redis:7

export REDIS_URL=redis://localhost:6379/0
python examples/prototype/tests/run_redis_smoke.py
```

CI Integration
- The repository CI spins up a Redis service and runs an async smoke test (`examples/prototype/tests/run_redis_smoke.py`) to validate the Redis Streams integration.

Notes
- The code is async-first: core executor and Redis adapter are async. `TaskExecutor` is a sync wrapper that delegates to `AsyncTaskExecutor` for convenience in local tests. See `docs/ADR/0001-core-architecture.md` for the architecture rationale.

Files
- executor/worker.py - simple task executor
- bus/in_memory.py - in-memory message bus
- models/mock_provider.py - deterministic model provider
- adapters/sales/adapter.py - webhook -> task mapper
- skills/lead_qualification.py - sample skill logic
- belief_store/store.py - records intermediate reasoning
- tests/run_tests.py - runs a simple end-to-end scenario
- docs/hooks/emit_node.py - emits a sample node JSON for docs

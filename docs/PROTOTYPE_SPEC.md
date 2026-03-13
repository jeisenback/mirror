Prototype Specification: Minimal Viable Engine (MVE)

Overview
- Goal: deliver a small, token-efficient prototype that proves core runtime, reasoning, skill/task building, self-reflection, and documentation integration.
- Timebox: 1 week experiment (scoped; see acceptance criteria).
- Constraints: prioritize token efficiency, auditability, and integration with the documentation engine and dependency-mapping pipeline.

Minimal Scope (must-haves)
- Core Runtime: lightweight Python async executor with task lifecycle, idempotency, and hooks for policy checks.
- Message Bus: Redis Streams adapter (with in-memory fallback for local dev).
- Model Provider: pluggable adapter interface + a deterministic mock provider and a token-budgeting wrapper (`tiktoken` hooks).
- Domain Adapter: Sales adapter (webhook + simple CRM API action) as sample domain.
- Role Templates & Skills: declarative YAML skill manifest + sample skill for "lead qualification".
- Reasoning & Reflection: capture intermediate reasoning steps to a local Belief Store; a minimal self-reflection policy that retries or flags low-confidence decisions.
- Test Harness: scenario-based pytest tests with deterministic model stubs and trace recording for replay.
- Documentation hooks: generate per-function and per-skill docs and link artifacts into the docs engine pipeline.

Architecture (high level)
- `executor/` (Core Runtime): accepts task envelopes, schedules tasks, enforces concurrency and retries.
- `bus/` (Message Bus): Redis Streams adapter + simple in-memory queue for tests.
- `models/` (Model Provider): interface + `mock_provider.py` + `budgeted_provider.py` (token counting + caching).
- `adapters/sales/`: webhook receiver, mapping templates, outbound action runner (mock CRM).
- `skills/`: YAML manifests and small Python runtime hooks for skill logic.
- `belief_store/`: lightweight store (SQLite or JSONL) recording intermediate steps, confidences, and provenance.
- `meta/`: minimal meta-reasoner endpoints (analyze, simulate — call sandboxed local runner) for demos.
- `tests/`: scenario definitions, fixtures, and replay runners.
- `docs/hooks/`: scripts to export nodes/edges for the doc engine.

Component details
- Core Runtime
  - Interface: `POST /tasks` (task envelope JSON), worker loop consumes from Redis Stream.
  - Envelope: { id, type, spec_id, input, provenance, retry_count }
  - Hooks: `pre_execute` (policy), `on_complete` (emit trace), `on_error` (store failure + reflection trigger).
- Message Bus
  - Default: Redis Streams with groups for workers; in-memory queue implements same envelope semantics for local runs.
- Model Provider
  - API: `ModelProvider.generate(prompt, max_tokens, metadata)` synchronous and async variants.
  - Budgeting: `tiktoken` pre-count, reject or summarize input if budget exceeded, log token usage metrics.
  - Mock: returns deterministic outputs based on prompt hash for tests.
- Domain Sales Adapter
  - Ingest: simple FastAPI endpoint `/webhook/sales` that converts payload to a `lead_qualification` task.
  - Actions: `create_lead` (mock), `update_crm` (mock); skill uses model for classification only when needed.
- Skills & Role Templates
  - Skill manifest (YAML): id, inputs, outputs, auth scopes, version, test fixtures.
  - Runtime: small executor that validates inputs, calls skill code or model, writes outputs to bus.
- Reasoning & Self-Reflection
  - Capture: for each model-backed step, store step_id, prompt (redacted), model_output, confidence, timestamp.
  - Reflection policy: if confidence < threshold or repeated failures, meta job runs `analyze_trace` to propose retry, fallback, or escalate.
- Test Harness
  - Scenario format: `{ name, steps: [events], expected: [outcomes], trace_asserts }`.
  - Tools: fixtures to inject mock provider and in-memory bus; recorder to output OpenTelemetry-compatible JSON traces for docs.

Token-efficiency measures (prototype)
- Prefer deterministic local logic for common classification rules; only call ModelProvider for ambiguous cases.
- Use retrieval-lite: short context from vector store (Chroma) for small lookup only if necessary.
- Implement prompt templates with variable placeholders and pre-truncation summarizer.
- Introduce `budgeted_provider` that enforces per-run token caps and fallback strategies.
- Cache model responses by prompt hash and reuse across scenarios in tests.

Documentation & Dependency mapping integration
- Each module emits metadata (canonical ID, owner, spec_ref) via `docs/hooks/emit_node.py` during `gen_docs` run.
- Traces recorded by Test Harness are exported to `docs/traces/` and merged in CI by the doc engine pipeline.
- The prototype will populate `docs/auto/` with sample per-function and per-skill pages to validate the doc engine.

Security & Governance (prototype level)
- Secrets: use environment variables for local dev; integrate Vault in later stages.
- Policy: a simple pre-check `policy.py` with OPA-compatible JSON output; CI will run `policy.py` checks on generated docs and spec changes.

Files to create (examples/prototype skeleton)
- `examples/prototype/README.md` — run instructions
- `examples/prototype/requirements.txt` — minimal deps: fastapi, uvicorn, redis, aioredis, pytest, tiktoken, networkx, mkdocs
- `examples/prototype/executor/__init__.py` + `worker.py`
- `examples/prototype/bus/redis_adapter.py` + `bus/in_memory.py`
- `examples/prototype/models/mock_provider.py` + `budgeted_provider.py`
- `examples/prototype/adapters/sales/app.py` (FastAPI webhook)
- `examples/prototype/skills/sample_skill.yaml` + `skills/lead_qualification.py`
- `examples/prototype/belief_store/store.py`
- `examples/prototype/tests/test_scenario_sales.py` and fixtures
- `examples/prototype/docs/hooks/emit_node.py`

Run & test (local dev)
- Create virtualenv and install requirements

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r examples/prototype/requirements.txt
```

- Start in-memory services and run worker in one terminal, start sales adapter in another, run pytest for scenarios.

Acceptance criteria (end of 1-week experiment)
- End-to-end: receive a sample webhook, execute `lead_qualification` skill, write output to bus, and update mock CRM.
- Traces: scenario run produces an OpenTelemetry-like trace JSON; docs engine can ingest it and render a per-skill page.
- Token budget: budgeted provider logs token usage and enforces a per-run cap; no experiment run exceeds the cap.
- Reflection: at least one low-confidence scenario triggers the reflection policy and produces a proposed remediation artifact.

1-week sprint plan (high level)
- Day 1: scaffold repo layout, implement in-memory bus, core runtime skeleton, and mock model provider.
- Day 2: implement Sales adapter and a sample skill; wire end-to-end using in-memory bus.
- Day 3: add Redis Streams adapter, budgeted model wrapper, and token logging.
- Day 4: implement belief store and minimal reflection policy; add scenario test capturing traces.
- Day 5: integrate docs hooks, generate sample docs, run CI workflow locally, and prepare demo.

Future domains & practices (roadmap notes)
- Domains to add: Product Management, Business Analysis, Project Management, Finance, HR.
- Process & practices: embed Lean, Agile, XP idioms as role templates and skill libraries (e.g., backlog grooming skill, sprint planning assistant, retrospective summarizer).
- Meta: use experiments and retrospectives to validate each domain adapter and corresponding skills; apply token-efficiency patterns across domains.

Next actions I can take now
- Scaffold `examples/prototype/` with minimal files and a runnable `README.md`.
- Implement core runtime worker and an in-memory bus and run the first scenario test.


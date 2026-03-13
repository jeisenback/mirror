Prototype Design: Architecture, Interfaces, and Tasks

Purpose
- Capture the concrete design for the 1-week Minimal Viable Engine (MVE) prototype so tasks can be implemented and tracked.

High-level components
- Core Runtime (executor): consumes task envelopes, invokes skills, enforces idempotency, retries, and policy hooks.
- Message Bus: adapter interface with two implementations: InMemory (for local tests) and Redis Streams (for integration).
- Model Provider: pluggable adapter with a Mock provider for tests and a Budgeted wrapper that enforces token caps via `tiktoken`.
- Domain Adapters: connectors that map external inputs to canonical task envelopes (Sales, Product in prototype).
- Skills & Role Templates: YAML manifests + runtime function hooks that implement skill logic.
- Belief Store: lightweight store (JSONL or SQLite) capturing intermediate reasoning steps, confidence, and provenance.
- Test Harness: scenario runner producing deterministic traces and replay artifacts for docs and validation.
- Docs Hooks: emit canonical node/edge JSON and sample per-function metadata for the docs engine.
- Meta-Reasoner (minimal): endpoints to analyze traces and propose remediations (sandboxed simulation later).

Key data models
- Task Envelope
  - { id: UUID, type: string (skill id), spec_id?: string, input: object, provenance?: {source, event_id, timestamp}, retry_count: int }
- Skill Manifest (YAML)
  - { id, name, version, inputs:[], outputs:[], auth_scopes=[], tests:[] }
- Belief Record
  - { step_id, task_id, timestamp, step_type, data: { prompt_redacted?, model_output?, confidence?, metadata }}
- Doc Node
  - { id: canonical_id, type: function|file|skill|adapter, path, owner, spec_ref, commit }

Core interfaces
- ModelProvider
  - generate(prompt, max_tokens, metadata) -> { text, tokens_used, latency }
  - estimate_work(feature) -> { estimate, confidence }
- BusAdapter
  - publish(envelope)
  - consume_one() -> envelope | None
  - empty() -> bool
- Executor hooks
  - pre_execute(envelope) -> allow|deny|modify
  - on_complete(envelope, result)
  - on_error(envelope, error)
- Docs hooks
  - emit_node(node_json)
  - emit_edge(src_id, dst_id, kind)

Sequence: webhook -> story
1) External webhook (adapter) receives payload and calls `bus.publish(envelope)`.
2) Executor loop `consume_one()` -> envelope.
3) Executor calls `pre_execute` (policy checks, rate limits).
4) Executor finds skill by envelope.type and invokes skill function.
5) Skill executes: may call ModelProvider or local logic, records belief steps into Belief Store, writes outputs or side-effects (e.g., mock CRM, repo).
6) Executor calls `on_complete` to emit traces and docs hooks; if confidence low, triggers reflection (schedule meta job).

Acceptance criteria (prototype)
- End-to-end: webhook -> task -> skill -> side-effect (mock CRM/repo) verified by scenario test.
- Traces: scenario produces JSON traces consumable by docs pipeline and `merge_graphs.py`.
- Docs: doc hooks emit at least one canonical node artifact uploaded by CI.
- Token budget: budget wrapper logs tokens and enforces per-task cap; budget exceeded should trigger summarization or rejection.
- Reflection: A low-confidence decision results in a recorded reflection proposal (artifact) and a logged suggested remediation.

Design tasks (what to implement now)
- Design: finalize task envelope schema and skill manifest (this doc).
- Implement: in-memory Bus + Executor skeleton (done).
- Implement: Mock ModelProvider + estimate_work (done).
- Implement: Sales & Product adapters (done).
- Implement: Skills + manifests (done).
- Implement: Belief Store (done).
- Implement: Test Harness and two scenario tests (done).
- Implement: Docs hooks to emit node JSON (done).
- Implement: CI workflow to run tests and upload artifacts (done).
- Next: add Redis Streams adapter, budgeted ModelProvider enforcement, docs generation integration, and minimal meta-reasoner endpoints.

Operational notes
- Token efficiency: prefer local deterministic logic, cache model outputs by prompt hash, use short summaries for context, and use model cascades.
- Trace sampling: record full traces for test scenarios; in production sample traces and keep full audit when required.
- Security: do not store raw PII in belief store — redaction must be added before writing traces to disk.

Files to add next (implementation)
- `tools/` scripts for dependency mapping and doc merging (`merge_graphs.py`, `gen_docs.py`).
- `adapters/redis_adapter.py` for Redis Streams bus.
- `models/budgeted_provider.py` to wrap external model calls.
- `meta/service.py` with minimal `/meta/analyze` and `/meta/propose-change` endpoints (FastAPI).
- `docs/auto/` templates and CI `mkdocs` integration.


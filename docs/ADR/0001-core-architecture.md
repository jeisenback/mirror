<!-- ADR: 0001 - Core agent framework architecture -->

# ADR 0001 — Core agent framework architecture

Status: Accepted

Date: 2026-03-13

Context
-------
We are building an extensible, auditable, token-efficient agent platform that will run experiments and incrementally harden into production. Key non-functional requirements: token efficiency, auditability (traceable decisions), CI gating, and domain adapters. The prototype currently mixes sync and async components and stores traces under `docs/traces/`.

Decision
--------
Adopt a hybrid, async-first architecture with clear sync wrappers for simple local runs:

- Runtime: core runtime will be asynchronous (async/await) to support high-concurrency workloads and network IO (model calls, Redis, vector stores). Provide a small synchronous wrapper API and in-memory synchronous bus for simple local tests and acceptance runs.

- Message bus: Redis Streams is the primary message bus for scale and persistence. Keep an in-memory bus for unit scenarios. Provide both sync (`redis-py`) and async (`redis.asyncio`) adapters; prefer async adapter in the executor.

- Model Provider Interface: standardize a minimal interface with `generate(prompt, max_tokens=None, metadata=None)` and `estimate_work(feature)`; wrap real providers with `BudgetedProvider` that enforces token budgets and caching.

- Token accounting: use precise token counting via `tiktoken` in the budget wrapper; fall back to a naive counter only in developer setups. CI should install `tiktoken` and tests should assert accounting behavior.

- Tracing & Observability: emit structured step/traces to a belief-store JSONL with canonical node IDs and timestamps. Align trace schema with OpenTelemetry concepts (span id, parent, attributes) for future integration.

- Retrieval: provide an abstraction for vector stores; start with an in-memory placeholder and a planned integration with Chroma/FAISS + embedding providers.

- Meta-reasoner: FastAPI service will host `analyze`, `simulate`, and `propose` endpoints used by CI and manual reviewers. Promotion automation will run tests and append promotion records to `docs/auto/promotions.jsonl`.

- Governance: include OPA policy hooks in the meta pipeline. Use the `opa` CLI in CI or a hosted policy engine; default to permissive fallback locally but fail CI if policy binary or policy files are configured.

Consequences
------------
- Pros:
  - Async-first runtime scales for parallel model calls and IO-bound work.
  - Clear sync wrappers preserve ease-of-use for quick local runs and acceptance scenarios.
  - Using `tiktoken` ensures accurate token budgeting and better cost control.
  - Redis Streams gives durable task queues and consumer groups.

- Cons:
  - Increased complexity: async code paths require careful testing and CI coverage.
  - Developers need to run an async-capable environment for realistic tests.

Alternatives Considered
-----------------------
- Keep prototype fully synchronous: simpler but blocks scalability and efficient model parallelism.
- Use RabbitMQ/Kafka instead of Redis Streams: heavier infra and operational cost for this project stage.

Next Steps
----------
1. Write a short ADR (this document) and add it to `docs/ADR/`.
2. Update core executor to prefer the async Redis adapter and provide sync wrappers for tests.
3. Add CI job to install `tiktoken` and run token-accounting assertions.
4. Add an OPA policy check stage in CI; fail fast when policies are present and `opa` is configured.
5. Document trace schema and add an OpenTelemetry export plan.

References
----------
- Prototype files: `examples/prototype/executor/worker.py`, `examples/prototype/bus/redis_async_adapter.py`, `examples/prototype/models/budgeted_provider.py`
- Docs: `docs/COMPONENT_SPECS.md`, `docs/DOC_ENGINE_SPEC.md`

Documentation Engine Specification

Purpose
- Provide a single, auditable, standards-driven documentation engine that produces linked, machine-readable, and human-friendly artifacts for the entire platform (function→function, file→file, service→service, spec→artifact).
- Ensure every doc artifact includes provenance metadata, is validated in CI, and is stored/published with an immutable audit trail.

Requirements
- Linkability: every entity (function, class, file, module, skill, spec, adapter, endpoint) must have a canonical, resolvable ID and be cross-referenced.
- Auditable provenance: each generated artifact must include generator version, commit SHA, timestamp, input graph versions, and signatures where feasible.
- Standards & policy: follow OpenAPI for HTTP APIs, OpenTelemetry for traces, and an internal doc schema for code-level artifacts; enforce policies (security, privacy) via OPA policy checks in CI.
- Validation: broken links, unresolved references, schema violations, and policy violations must fail CI gates (configurable thresholds for experimental branches).
- Automation: docs are generated from source + runtime traces, validated, and published automatically during CI after tests pass.

Canonical ID scheme
- Use a uniform identifier format: <type>::<repo-relative-path-or-name>::<unique-suffix>
  - Examples:
    - function::src/module/submodule.py::my_function
    - file::src/module/submodule.py
    - service::sales-adapter::v1
    - spec::agents/sales/crm_lead_handler::v1
- IDs must be stable across runs for the same source; include spec version or commit as metadata for artifact immutability.

Data model for doc nodes
- Node: { id, type, display_name, path, signature, docstring, owner, spec_ref, version, provenance }
- Edge: { src_id, dst_id, kind: static|runtime|spec_link, weight?, trace_samples? }
- Artifact: { node_set, edge_set, generator_meta, timestamp, commit_sha, validation_report }

Inputs to generation
- Static analysis: AST-based extraction (signatures, docstrings, imports) and call-graph extraction (pyan/pycg/pyan3).
- Runtime traces: OpenTelemetry traces captured from representative scenario runs (Test Harness). Traces supply empirical edges and provenance (trace ids, timestamps, run metadata).
- Specs & manifests: YAML/JSON skill manifests, OpenAPI specs, and Spec Registry artifacts.
- Owner & policy metadata: from CODEOWNERS or a manifest mapping, and OPA policies for allowed changes.

Suggested tools & libraries
- Doc generation: MkDocs + mkdocstrings (Python), or Sphinx + autodoc; prefer MkDocs with `mkdocstrings` for concise modern docs and easy mermaid embedding.
- Auto-doc for Python: `mkdocstrings[pytkinter]` or `mkdocstrings[python]` to render docstrings and signatures automatically.
- OpenAPI: `fastapi`/`flask` + `openapi` generation and `spectral` for schema linting.
- Static dependency graphs: `pydeps`, `pyan3`, `networkx` for analysis/merging.
- Graph outputs: Mermaid and Graphviz (DOT) for embedding diagrams; `pyvis` for interactive HTML graphs.
- Runtime traces: OpenTelemetry + Jaeger; export traces to JSON for merging.
- Policy & governance: OPA (rego) for policy checks; HashiCorp Vault for secret management.
- Link validation: `markdown-link-check` or `mkdocs build` + `mkdocs-material` link check plugin.

Generation pipeline (high-level)
1) Collect sources: checkout code at CI commit and pull Spec Registry artifacts referenced by the commit.
2) Static extract: run `gen_static_graph.py` -> outputs node/edge JSON (static edges).
3) Run scenario traces (in CI or recorded): run Test Harness to produce OpenTelemetry traces -> export trace JSON.
4) Merge graphs: `merge_graphs.py` combines static + runtime graphs into weighted graph.
5) Enrich nodes: attach docstrings, owners, spec links; resolve canonical IDs; run policy annotations.
6) Render artifacts: per-node markdown pages, per-file pages, index, and graphs (Mermaid/DOT); generate OpenAPI site pages for HTTP services.
7) Validate: run link checks, schema checks (OpenAPI Spectral), OPA policy checks, and custom validation `validate_graph.py`.
8) Publish: on success, push generated artifacts to `docs/auto/` in the repo and to the Spec Registry as an immutable artifact (include metadata file with provenance).

CI integration
- Add a CI job `docs:generate-and-validate` with steps:
  - Install dev requirements: `pip install -r requirements-dev.txt`
  - `python tools/gen_static_graph.py --output graphs/static.json`
  - `pytest tests/scenarios --record-traces --output traces/` (or reuse recorded traces)
  - `python tools/merge_graphs.py --static graphs/static.json --traces traces/*.json --out graphs/merged.json`
  - `python tools/gen_docs.py --graph graphs/merged.json --out docs/auto/`
  - `npx markdown-link-check docs/auto/**/*.md` (or `mkdocs build` + linkcheck)
  - `opa eval -i docs/auto/ docs/policies/policy.rego` (policy checks)
  - On success: commit/publish artifacts as a pipeline artifact and tag registry with artifact metadata.

Auditability & provenance
- Every generated artifact includes a metadata header (YAML front matter): generator tool/version, commit SHA, generation timestamp, input trace IDs, spec references, CI run id, and optional GPG signature.
- Keep a `docs/auto/ARTIFACTS_INDEX.json` that lists artifacts and their provenance.
- Store signed artifacts in the Spec Registry alongside spec packages.

Validation rules (examples)
- No broken links: every node reference must resolve to an artifact or a spec; broken links fail CI.
- New runtime-only edges: must have an owner or a linked spec; otherwise flagged for review.
- High-risk changes (edges touching core runtime or meta-reasoner): require OPA policy pass and a human reviewer approval.
- Privacy rule: model inputs/outputs containing sensitive fields must be redacted before storage (use redaction tool during trace export).

Linking and navigation UX
- Per-function page: signature, docstring, callers (with links), callees, owner, tests, spec links, and recent runtime traces (sampled) with timestamps.
- Per-spec page: spec YAML, versions, linked artifacts, and generated change log.
- Operator UI: interactive graph with filters by type/owner/risk and ability to open doc pages.

Operational notes
- Generation should be idempotent and cheap for small diffs: support incremental generation by comparing static graphs and only re-rendering changed nodes.
- For large repos, support paginated or sharded generation in CI to keep run times reasonable.

Low-effort implementation plan (next actions I can implement)
1) Add `tools/` scripts: `gen_static_graph.py`, `merge_graphs.py`, `gen_docs.py`, `validate_graph.py` (Python + networkx).
2) Add `requirements-dev.txt` with needed tools: `pydeps`, `pyan3`, `networkx`, `mkdocs`, `mkdocstrings`, `markdown-link-check`, `oparg/opa` CLI.
3) Add a GitHub Actions workflow skeleton `.github/workflows/docs.yml` for generation/validation.
4) Scaffold `docs/auto/` output folder and sample per-function page template.


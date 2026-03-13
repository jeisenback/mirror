Dependency Mapping, Validation, and Documentation Process

Purpose
- Provide a repeatable process and tooling to map code dependencies (function→function, file→file, service→service), validate them, and produce living documentation that integrates with CI and the Spec Registry.

Process Overview (high-level)
1) Discover
- Static analysis: build import graphs and call graphs using AST-based tools.
- Runtime tracing: instrument runs with OpenTelemetry to capture actual call edges, cross-service traces, and provenance IDs.
- Combined view: merge static and runtime data to get a confidence-weighted dependency graph.

2) Analyze
- Normalize nodes (function ids, file paths, service names) and annotate with metadata: owners, version, spec references, risk tags.
- Compute dependency metrics: fan-in/fan-out, cycle detection, depth, critical-path latency impact.

3) Visualize
- Emit graph formats: DOT (Graphviz) and Mermaid for docs; interactive graphs using `networkx` + `pyvis` or `d3` in the Operator UI.
- Produce summaries per-module and per-skill with top dependencies and change hotspots.

4) Validate
- Contract tests: enforce function-level pre/post conditions and API contracts with automated tests.
- Scenario replay: run recorded traces through the Test Harness and assert behaviors remain within baselines.
- Drift detection: CI job compares current graph against last approved graph and flags new unexplained edges.

5) Document
- Generate living docs: per-file and per-function pages with dependency lists, owners, tests, and links to spec entries.
- Auto-insert diagrams into component docs and Spec Registry entries.

6) Automate & Integrate
- CI: add steps to generate graphs, run validation tests, and fail on regressions above thresholds.
- Spec Registry: when proposed changes are detected, create a draft artifact linking affected specs and tests.
- Governance: require human approval for high-risk dependency changes.

Concrete Tools & Commands (Python-first)
- Static graph (imports): `pydeps` (pip install pydeps)
  - Example: `pydeps my_package --noshow --show-deps --output-file=graphs/my_package.svg`
- Function call graph: `pyan` / `pycg` / `call-graph` variants
  - Example (pyan): `pyan my_package/**/*.py --dot > graphs/calls.dot` then `dot -Tpng graphs/calls.dot -o graphs/calls.png`
- Runtime traces: OpenTelemetry + Jaeger
  - Instrument app and run representative scenarios; export traces to Jaeger and export trace JSON for graph merging.
- Merge & analyze: small script `tools/merge_graphs.py` uses `networkx` to combine static and runtime graphs, attach weights, and compute metrics.
- Visualize: export Mermaid via a script or produce interactive HTML with `pyvis`.

Example CI snippet (GitHub Actions)
- Steps:
  - run `python -m pip install -r requirements-dev.txt`
  - run static graph generation (`pydeps`, `pyan`)
  - run `tools/merge_graphs.py --input-static graphs/static.dot --input-traces traces/run.json --output merged.json`
  - run validation: `python tools/validate_graph.py merged.json --baseline baseline/approved.json`
  - if validation fails above threshold, exit non-zero and create an issue with the diff summary.

Validation & Tests
- Contract tests: use `pytest` with parametrized inputs and explicit contract assertions.
- Scenario replay: reuse Test Harness scenarios; record expected edges and behavior; replay in sandboxed environment with mock Model Provider.
- Mutation testing: (optional) run targeted mutations to verify tests catch regressions on critical dependency paths.

Documentation generation
- Per-function pages: generate markdown with signature, docstring, callers, callees, owning spec link, and tests. Output to `docs/auto/functions/`.
- Per-file pages: same, plus a dependency diagram image or mermaid block.
- Index & changelog: maintain a `docs/auto/DEPENDENCY_CHANGELOG.md` that records diffs between successive approvals.

Representations & Data Model
- Node: { id, type: function|file|service, path, owner, spec_ref, version }
- Edge: { src, dst, kind: static|runtime, weight, trace_samples }
- Graph: JSON with metadata, summary metrics, and optional DOT/Mermaid exports.

Safety & Governance
- Risk scoring: assign risk to edges/nodes based on change frequency, critical-path presence, and owner SLAs.
- Approval gates: auto-block promotions when high-risk edges are added automatically; require `spec` update & reviewer approval.

Low-effort Next Steps (I can implement)
- Add `tools/` scripts: `gen_static_graph.py`, `gen_call_graph.sh`, `merge_graphs.py`, `validate_graph.py`, and `gen_docs.py`.
- Add a CI workflow skeleton that runs the generation and validation steps.
- Scaffold per-function docs generation and place outputs in `docs/auto/`.

References / Further reading
- `pydeps` project: https://github.com/thebjorn/pydeps
- `pyan3` (call graph): https://github.com/abentley/pyan
- OpenTelemetry Python: https://opentelemetry.io/
- Graph tools: `networkx`, `pyvis`, `graphviz`


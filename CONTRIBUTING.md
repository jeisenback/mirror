## Contributing — Developer Checklist

This file gives a quick checklist for contributing code and running the prototype locally.

- Create a branch from `main` named `feat/<short-desc>` or `fix/<short-desc>`.
- Open a PR with a concise description and link to any related ADRs or issues.
- Run the unit scenarios and product tests locally before pushing:

```bash
python -u examples/prototype/tests/run_tests.py
python -u examples/prototype/tests/run_product_tests.py
```

- To exercise Redis integration (optional):

```bash
docker run -p 6379:6379 --name redis -d redis:7
export REDIS_URL=redis://localhost:6379/0    # Windows: set REDIS_URL=redis://localhost:6379/0
python -u examples/prototype/tests/run_redis_smoke.py
```

- Update or create ADRs for major design changes: add files to `docs/ADR/`.
- If your change affects docs, run the docs generator and check links:

```bash
python tools/gen_docs.py
python tools/check_links.py docs/auto
```

- Commit messages: short subject line + optional body. Use present tense.
- Add tests for new behaviors and ensure CI passes.

CI notes
- CI runs unit scenarios, generates docs, and starts a Redis service to run an async smoke test. If your change affects runtime wiring, add or update CI steps accordingly.

Contact
- Add notes or questions to the project issue tracker; maintainers will review PRs and advise on ADR updates.

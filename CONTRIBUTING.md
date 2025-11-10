# Contributing to legends

Thanks for your interest in contributing! This project is a Python‑first repo
(primary package: **legends**) that shells out to `git` and `gh`.
We follow a lightweight process optimized for velocity and clarity.

## Quick Start (Developer Setup)

```bash
# 1) Create a venv and install (editable)
make install            # or: scripts/install.sh --dev

# 2) Verify local tooling (git, gh, identity)
make verify-env         # or: scripts/verify_env.sh

# 3) Run tests / linters
ruff .
black --check .
pytest
```

## Commit Style
Use **Conventional Commits** (e.g., `feat: ...`, `fix: ...`, `chore: ...`).
When crafting histories for demos, legends supports backdated commits and merges—
keep messages readable and truthful.

## Branching
- `main`: stable, released line
- `dev`: integration branch for feature PRs (when used)
- feature branches: `feat-<topic>`, `fix-<topic>`, `docs-<topic>`

## Pull Requests
- Include context in the PR body (what/why/how).
- Keep PRs focused; small is better.
- CI must be green (format, lint, tests).

## Pre‑commit (optional)
Add hooks locally if you like:
```bash
pip install pre-commit
pre-commit install
```

## Running the CLI Locally
```bash
legends --help
```

## Code of Conduct
Participation is governed by our [Code of Conduct](CODE_OF_CONDUCT.md).

## License
By contributing, you agree your contributions will be licensed under the
repository's open‑source license (see `LICENSE`).

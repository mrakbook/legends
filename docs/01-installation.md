# Installation

This project prefers a local, isolated environment and shells out to `git` and `gh`.

## Prerequisites

- **Python** ≥ 3.9
- **git** — https://git-scm.com/
- **GitHub CLI (`gh`)** — https://cli.github.com/ (login: `gh auth login`)

Verify quickly:

```bash
git --version
gh --version
gh auth status || gh auth login
```

You can also run the built-in check:

```bash
scripts/verify_env.sh
```

## Install (editable)

```bash
git clone <your-fork-or-path>/legends.git
cd legends
scripts/install.sh   # creates .venv and installs -e .
# or, manually:
# python3 -m venv .venv && source .venv/bin/activate
# pip install -U pip && pip install -e .
```

Confirm the CLI is on PATH (within the venv):

```bash
legends --help
```

## Optional: configure defaults

Create a `.env` (based on `.env.example`) and/or a YAML config. For example:

```yaml
# config/defaults.yaml
base_branch: main
remote_name: origin
visibility: private
owner: your-username-or-org
author:
  name: "Your Name"
  email: "you@example.com"
token_env: GITHUB_TOKEN
```

Use it via:

```bash
legends --config config/defaults.yaml --help
```

> **Precedence**: CLI flags > environment variables > YAML config > built-in defaults.
Environment variable keys include: `GHB_BASE_BRANCH`, `GHB_REMOTE`, `GHB_VISIBILITY`, `GHB_OWNER`,
`GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GHB_TOKEN_ENV`, `GHB_DRY_RUN`.

# Usage

The console entrypoint is **`legends`**. Global flags:

- `--config <file>` — load defaults from YAML
- `--dry-run` — print what would run
- `-v` / `-vv` — verbosity

> All date inputs are normalized to UTC and applied via `GIT_AUTHOR_DATE`/`GIT_COMMITTER_DATE`.

---

## create-repo

Create a new repository with a **backdated initial commit**, then create the remote on GitHub and push it.

```bash
legends create-repo demo-repo \
  --description "Demo backdated repo" \
  --date "2024-12-01T12:00:00" \
  --private \
  --branch main
```

**Args**

- `name` (positional) — directory/repo name
- `--owner` — GitHub user/org (optional; else your auth default)
- `--date` — ISO-like string (`YYYY-MM-DD[THH:MM[:SS]][Z|±HH:MM]`)
- `--private` / `--public`
- `--description` — repo description
- `--readme` — initial README filename (default `README.md`)
- `--branch` — default branch name (default from config)

---

## create-branch

Create a branch from base and add a **backdated empty “birth” commit**. In `v0.1.0` the branch is **pushed automatically**.

```bash
legends create-branch feature-login \
  --base main \
  --date "2025-02-01T09:00:00" \
  --message "chore(feature-login): branch birth"
```

**Args**

- `branch` (positional) — new branch name
- `--base` — base branch (default from config)
- `--date` — “birth” commit date
- `--message` — commit message (optional)

---

## commit

Create a **backdated commit** on a branch, then **push** the branch.

```bash
legends commit \
  --branch feature-login \
  --date "2025-02-10T15:00:00" \
  --message "Implement login backend" \
  --add-all
```

**Args**

- `--branch` — target branch
- `--date` — commit date
- `--message` — commit message
- `--allow-empty` — allow empty commit
- `--add-all` — stage all changes
- `--touch <file>` — create/modify a file before committing

---

## open-pr

Open a PR from branch to base using `gh` (real-time timestamps on GitHub).

```bash
legends open-pr \
  --branch feature-login \
  --base main \
  --title "Feature: User Login" \
  --body "Adds backend + UI for login." \
  --draft
```

**Args**

- `--branch` — head branch
- `--base` — base branch
- `--title`, `--body` — PR metadata
- `--draft` — open as draft

---

## merge-pr

Perform a **no‑ff merge** locally with a **backdated merge commit**, push base, and (by default) delete the remote branch / close the PR if known.

```bash
# Merge by branch name
legends merge-pr \
  --branch feature-login \
  --base main \
  --date "2025-03-01T17:00:00"

# Or merge by PR number (resolves head branch automatically)
legends merge-pr \
  --pr 42 \
  --base main \
  --date "2025-03-01 17:00"
```

**Args**

- `--branch` *or* `--pr <number>`
- `--base` — base branch
- `--date` — merge commit date
- `--message` — optional message override
- `--delete-branch` / `--no-delete-branch` — default: **delete**

---

## commit-all (one‑shot pipeline)

Backdated **commit → PR → backdated merge**, then close PR & delete remote branch.

```bash
legends commit-all \
  --branch feature-login \
  --base main \
  --commit-date "2025-02-10T15:00:00" \
  --message "Implement login" \
  --pr-title "Feature: Login" \
  --pr-body "Adds backend + UI." \
  --merge-date "2025-03-01T17:00:00"
```

### Sequence (what happens under the hood)

```mermaid
sequenceDiagram
  participant Dev as Developer
  participant CLI as legends
  participant G as git
  participant H as gh (GitHub CLI)
  participant Hub as GitHub

  Dev->>CLI: commit-all --branch ... --commit-date ... --merge-date ...
  CLI->>G: checkout base; checkout -b branch
  CLI->>G: commit -m "..." (backdated env)
  CLI->>G: push -u origin branch
  CLI->>H: pr create --head branch --base base
  H-->>CLI: PR number / URL
  CLI->>G: checkout base; pull
  CLI->>G: merge --no-ff --no-commit branch
  CLI->>G: commit -m "Merge..." (backdated env)
  CLI->>G: push origin base
  CLI->>H: pr close --delete-branch (by default)
```

---

## Dry‑run & verbosity

```bash
legends --dry-run -vv commit \
  --branch feature-x \
  --date "2025-02-14 10:00" \
  --message "Demo"
```

- `--dry-run` prints the exact `git`/`gh` commands that would be executed.
- `-v` and `-vv` increase logging detail.

---

## Scripts & Makefile

- `scripts/install.sh` — create venv & install
- `scripts/verify_env.sh` — prerequisite checks
- `scripts/bootstrap_repo.sh` — thin wrapper around `create-repo`
- `scripts/commit_all.sh` — wrapper around `commit-all`

> The provided `Makefile` includes convenience targets. If your CLI does **not** support `--push` on certain commands, remove those flags — the current entrypoint pushes automatically.

# Limitations & Notes

Backdating is powerful — but it has boundaries defined by git and GitHub.

## What is backdated

- **Commit timestamps** (`GIT_AUTHOR_DATE`, `GIT_COMMITTER_DATE`).
- **Merge commit timestamps** created locally and pushed to the base branch.
- The commit graph and history ordering as rendered by Git/GitHub.

## What is *not* backdated

- **PR creation time**, **comments**, **reviews/approvals** — those are server-side events created when you run the commands.
- Any **webhook delivery timestamps**, **checks**, and **statuses** created by external systems.
- The **push time** recorded by GitHub reflects when you pushed, not the backdated time.

> The GitHub UI can show several different dates in different places. The commit’s own timestamp
is backdated; other UI elements may show the real-time when that artifact was created on GitHub.

## Behavior notes (v0.1.0)

- `create-branch` and `commit` **push** by default in the main CLI.
- `merge-pr` **deletes** the remote branch by default (`--no-delete-branch` turns this off).
- `commit-all` performs PR close & branch deletion at the end.
- Time zone handling: naive times are treated as **local time**, then converted to **UTC**.
- The tool depends on `git` and `gh` being available on `PATH` and on a valid `gh auth login`.

## Operational constraints

- Ensure you have **permission** to create repos and push branches in your target org/user.
- You may hit **rate limits** with `gh` if running many operations in a tight loop.
- Backdating does **not** rewrite history; it creates new commits with controlled timestamps.

## Security & ethics

- Use responsibly and in accordance with your organization’s policies.
- Backdated histories should be clearly labeled if used for demos or educational content.

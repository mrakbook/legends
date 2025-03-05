#!/usr/bin/env bash

set -Eeuo pipefail

usage() {
	cat <<'USAGE'
Usage: scripts/commit_all.sh --branch <name> --commit-date <ISO> --message <msg> --merge-date <ISO>
                             [--base <name>] [--pr-title <title>] [--pr-body <body>]
                             [--draft] [--delete-branch] [--touch <file>] [--dry-run]

Examples:
  scripts/commit_all.sh \
    --branch feature-login \
    --base main \
    --commit-date "2025-02-10T15:00:00" \
    --message "Implement login" \
    --pr-title "Feature: Login" \
    --pr-body "Adds backend + UI." \
    --merge-date "2025-03-01T17:00:00" \
    --delete-branch
USAGE
}

BRANCH=""
BASE="main"
COMMIT_DATE=""
MESSAGE=""
PR_TITLE=""
PR_BODY=""
MERGE_DATE=""
DRAFT=0
DELETE_BRANCH=0
TOUCH=""
DRY=0

while [[ $# -gt 0 ]]; do
	case "$1" in
	-h | --help)
		usage
		exit 0
		;;
	--branch)
		BRANCH="${2:-}"
		shift 2
		;;
	--base)
		BASE="${2:-}"
		shift 2
		;;
	--commit-date)
		COMMIT_DATE="${2:-}"
		shift 2
		;;
	--message)
		MESSAGE="${2:-}"
		shift 2
		;;
	--pr-title)
		PR_TITLE="${2:-}"
		shift 2
		;;
	--pr-body)
		PR_BODY="${2:-}"
		shift 2
		;;
	--merge-date)
		MERGE_DATE="${2:-}"
		shift 2
		;;
	--draft)
		DRAFT=1
		shift
		;;
	--delete-branch)
		DELETE_BRANCH=1
		shift
		;;
	--touch)
		TOUCH="${2:-}"
		shift 2
		;;
	--dry-run)
		DRY=1
		shift
		;;
	*)
		echo "Unknown arg: $1" >&2
		usage
		exit 2
		;;
	esac
done

[[ -n "$BRANCH" ]] || {
	echo "Missing --branch"
	usage
	exit 2
}
[[ -n "$COMMIT_DATE" ]] || {
	echo "Missing --commit-date"
	usage
	exit 2
}
[[ -n "$MESSAGE" ]] || {
	echo "Missing --message"
	usage
	exit 2
}
[[ -n "$MERGE_DATE" ]] || {
	echo "Missing --merge-date"
	usage
	exit 2
}

if command -v legends >/dev/null 2>&1; then
	CLI=(legends)
elif python -c 'import legends' >/dev/null 2>&1; then
	CLI=(python -m legends)
else
	echo "CLI not found. Run scripts/install.sh first." >&2
	exit 1
fi

echo "==> Verifying environment"
scripts/verify_env.sh || true

ARGS=(commit-all "--branch" "$BRANCH" "--base" "$BASE" "--commit-date" "$COMMIT_DATE" "--message" "$MESSAGE" "--merge-date" "$MERGE_DATE")

[[ -n "$PR_TITLE" ]] && ARGS+=(--pr-title "$PR_TITLE")
[[ -n "$PR_BODY" ]] && ARGS+=(--pr-body "$PR_BODY")
[[ -n "$TOUCH" ]] && ARGS+=(--touch "$TOUCH")
((DRAFT)) && ARGS+=(--draft)
((DELETE_BRANCH)) && ARGS+=(--delete-branch)
((DRY)) && ARGS=(--dry-run "${ARGS[@]}")

echo "Running: ${CLI[*]} ${ARGS[*]}"
"${CLI[@]}" "${ARGS[@]}"

echo
echo "✅ commit-all flow completed."

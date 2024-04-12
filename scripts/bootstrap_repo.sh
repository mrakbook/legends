#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
	cat <<'USAGE'
Usage: scripts/bootstrap_repo.sh --name <repo> [--owner <owner>] [--date <ISO>]
                                 [--private|--public] [--desc <text>] [--branch <name>]
Examples:
  scripts/bootstrap_repo.sh --name demo-repo --date "2024-12-01T12:00:00" --private
  scripts/bootstrap_repo.sh --name demo --owner your-org --public --desc "Demo repo"
USAGE
}

NAME=""
OWNER=""
DATE=""
DESC=""
BRANCH="main"
VIS="private"

while [[ $# -gt 0 ]]; do
	case "$1" in
	-h | --help)
		usage
		exit 0
		;;
	--name)
		NAME="${2:-}"
		shift 2
		;;
	--owner)
		OWNER="${2:-}"
		shift 2
		;;
	--date)
		DATE="${2:-}"
		shift 2
		;;
	--desc | --description)
		DESC="${2:-}"
		shift 2
		;;
	--branch)
		BRANCH="${2:-}"
		shift 2
		;;
	--private)
		VIS="private"
		shift
		;;
	--public)
		VIS="public"
		shift
		;;
	*)
		echo "Unknown arg: $1" >&2
		usage
		exit 2
		;;
	esac
done

[[ -n "$NAME" ]] || {
	echo "Missing --name"
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

echo "==> Creating repo '$NAME' (visibility: $VIS) with initial backdated commit"
ARGS=(create-repo "$NAME" "--branch" "$BRANCH")
[[ -n "$OWNER" ]] && ARGS+=(--owner "$OWNER")
[[ -n "$DATE" ]] && ARGS+=(--date "$DATE")
[[ -n "$DESC" ]] && ARGS+=(--description "$DESC")
if [[ "$VIS" == "public" ]]; then
	ARGS+=(--public)
else
	ARGS+=(--private)
fi

echo "Running: ${CLI[*]} ${ARGS[*]}"
"${CLI[@]}" "${ARGS[@]}"

echo
echo "✅ Repo bootstrapped."

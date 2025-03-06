#!/usr/bin/env bash
set -Eeuo pipefail

RED=$'\e[31m'
YEL=$'\e[33m'
GRN=$'\e[32m'
NC=$'\e[0m'

fail() {
	echo "${RED}ERROR:${NC} $*" >&2
	exit 1
}
warn() { echo "${YEL}WARN:${NC}  $*" >&2; }
ok() { echo "${GRN}OK:${NC}    $*"; }

have() { command -v "$1" >/dev/null 2>&1; }

echo "==> Checking required tools"
have git || fail "git not found on PATH"
have gh || fail "GitHub CLI 'gh' not found on PATH"
ok "git: $(git --version)"
ok "gh:  $(gh --version | head -n1)"

echo "==> Checking gh auth status"
if gh auth status >/dev/null 2>&1; then
	ok "gh auth: logged in"
else
	warn "gh auth: not logged in. Run: gh auth login"
fi

echo "==> Checking Git identity"
git_user_name="$(git config user.name || true)"
git_user_email="$(git config user.email || true)"
if [[ -n "$git_user_name" ]]; then
	ok "git user.name: $git_user_name"
else
	warn "git user.name not set. Run: git config --global user.name 'Your Name'"
fi
if [[ -n "$git_user_email" ]]; then
	ok "git user.email: $git_user_email"
else
	warn "git user.email not set. Run: git config --global user.email 'you@example.com'"
fi

echo "==> Resolving GitHub identity (via gh api)"
gh_login="$(gh api user --jq .login 2>/dev/null || true)"
gh_name="$(gh api user --jq '.name // \"\"' 2>/dev/null || true)"
gh_id="$(gh api user --jq .id 2>/dev/null || true)"
if [[ -n "$gh_login" && -n "$gh_id" ]]; then
	ok "gh user: $gh_login${gh_name:+ ($gh_name)}"
	gh_noreply="${gh_id}+${gh_login}@users.noreply.github.com"
	ok "recommended noreply: $gh_noreply"
	gh_primary="$(gh api user/emails --jq 'map(select(.primary==true and .verified==true)) | .[0].email' 2>/dev/null || true)"
	if [[ -n "$gh_primary" && "$gh_primary" != "null" ]]; then
		ok "primary verified email: $gh_primary"
	fi
else
	warn "Could not resolve GH user via 'gh api user' (missing auth or scopes?)"
fi

if [[ -n "${git_user_email:-}" && -n "${gh_noreply:-}" ]]; then
	if [[ "$git_user_email" != "$gh_noreply" && (-z "${gh_primary:-}" || "$git_user_email" != "$gh_primary") ]]; then
		warn "git user.email does not match your GitHub identity (noreply/primary)."
		echo "    To use your GitHub identity for attribution, run one of:"
		echo "      git config --global user.email \"$gh_noreply\""
		if [[ -n "$gh_primary" && "$gh_primary" != "null" ]]; then
			echo "      git config --global user.email \"$gh_primary\"  # (uses your verified primary email)"
		fi
	fi
fi

echo "==> Checking token environment variables"
if [[ -n "${GITHUB_TOKEN:-}" || -n "${GH_TOKEN:-}" ]]; then
	ok "Token env present (GITHUB_TOKEN or GH_TOKEN)"
else
	warn "No token env set. gh may still work if you're logged in interactively."
fi

echo "==> Optional: Python environment"
if command -v python3 >/dev/null 2>&1; then
	ok "python3: $(python3 --version)"
else
	warn "python3 not found on PATH (only needed to run package locally)"
fi

echo
echo "✅ Environment looks sane."

SHELL := bash

PY        ?= python3
VENV      ?= .venv
PIP       := $(VENV)/bin/pip
RUN       := $(VENV)/bin/legends

REPO      ?= my-backdated-repo
OWNER     ?=
DESC      ?= Backdated repo created by automation
VIS       ?= private           # private|public
BASE      ?= main
REMOTE    ?= origin

INIT_DATE   ?= 2024-12-01T12:00:00
BRANCH      ?= feature-demo
BRANCH_DATE ?= 2025-02-01T09:00:00
COMMIT_DATE ?= 2025-02-10T15:00:00
MERGE_DATE  ?= 2025-03-01T17:00:00
MSG         ?= Demo: backdated change
PR_TITLE    ?= Demo PR
PR_BODY     ?= This PR demonstrates a backdated workflow.

GIT_AUTHOR_NAME  ?=
GIT_AUTHOR_EMAIL ?=

-include .env

ifeq ($(VIS),public)
  VISFLAG := --public
else
  VISFLAG := --private
endif

.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo
	@echo "Environment:"
	@echo "  REPO=$(REPO) OWNER=$(OWNER) VIS=$(VIS) BASE=$(BASE) REMOTE=$(REMOTE)"
	@echo "  INIT_DATE=$(INIT_DATE) BRANCH=$(BRANCH) BRANCH_DATE=$(BRANCH_DATE)"
	@echo "  COMMIT_DATE=$(COMMIT_DATE) MERGE_DATE=$(MERGE_DATE)"
	@echo "  MSG='$(MSG)' PR_TITLE='$(PR_TITLE)'"
	@echo
	@echo "Core:"
	@echo "  make install           # create venv and install package (editable)"
	@echo "  make verify-env        # check git, gh, and authentication"
	@echo "  make run-help          # show CLI help"
	@echo
	@echo "Workflow helpers (override variables as needed):"
	@echo "  make create-repo       # create repo with a backdated initial commit"
	@echo "  make create-branch     # create branch + backdated birth commit"
	@echo "  make commit            # backdated commit on BRANCH"
	@echo "  make open-pr           # open PR from BRANCH to BASE"
	@echo "  make merge-pr          # backdated local merge of BRANCH into BASE"
	@echo "  make commit-all        # commit -> PR -> backdated merge (one shot)"
	@echo
	@echo "Utilities:"
	@echo "  make clean             # remove venv and build artifacts"

$(VENV):
	$(PY) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip

.PHONY: install
install: $(VENV)
	$(PIP) install -e .

.PHONY: verify-env
verify-env:
	@command -v git >/dev/null 2>&1 || { echo "git not found"; exit 1; }
	@command -v gh  >/dev/null 2>&1 || { echo "gh (GitHub CLI) not found"; exit 1; }
	@gh --version | head -n 1
	@echo "Checking gh auth…"
	@gh auth status || { echo "Run: gh auth login"; exit 1; }
	@git --version
	@echo "OK"

.PHONY: run-help
run-help:
	$(RUN) --help

.PHONY: create-repo
create-repo: install
	$(RUN) create-repo $(REPO) $(VISFLAG) \
		--owner "$(OWNER)" \
		--description "$(DESC)" \
		--branch "$(BASE)" \
		--date "$(INIT_DATE)"

.PHONY: create-branch
create-branch: install
	$(RUN) create-branch $(BRANCH) \
		--base "$(BASE)" \
		--date "$(BRANCH_DATE)" \
		--message "chore($(BRANCH)): branch birth @ $(BRANCH_DATE)" \
		--push

.PHONY: commit
commit: install
	$(RUN) commit \
		--branch "$(BRANCH)" \
		--date "$(COMMIT_DATE)" \
		--message "$(MSG)" \
		--add-all \
		--push

.PHONY: open-pr
open-pr: install
	$(RUN) open-pr \
		--branch "$(BRANCH)" \
		--base "$(BASE)" \
		--title "$(PR_TITLE)" \
		--body "$(PR_BODY)"

.PHONY: merge-pr
merge-pr: install
	$(RUN) merge-pr \
		--branch "$(BRANCH)" \
		--base "$(BASE)" \
		--date "$(MERGE_DATE)" \
		--delete-branch

.PHONY: commit-all
commit-all: install
	$(RUN) commit-all \
		--base "$(BASE)" \
		--branch "$(BRANCH)" \
		--commit-date "$(COMMIT_DATE)" \
		--message "$(MSG)" \
		--pr-title "$(PR_TITLE)" \
		--pr-body "$(PR_BODY)" \
		--merge-date "$(MERGE_DATE)" \
		--delete-branch

.PHONY: clean
clean:
	rm -rf $(VENV) dist build *.egg-info .pytest_cache .mypy_cache

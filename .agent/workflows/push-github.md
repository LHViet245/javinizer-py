---
description: Safely commit and push code to GitHub
---

# /push-github — Safely commit and push code to GitHub

## Objective

Commit and push local changes to GitHub with:

- minimal but mandatory verification
- explicit disclosure of remote target
- explicit user confirmation (ASK_USER) before any push

## Disclosures

- Network domain used: `github.com`
- Remote name expected: `origin`

## Preconditions

- Must be inside a valid Git repository.
- Must have a configured remote named `origin`.
- Must not contain secrets in the diff (tokens, API keys, credentials, `.env` real values).
- Must not assume internet access beyond Git operations.

## Execution Steps

### 1) Repository sanity

Run:

- `git rev-parse --is-inside-work-tree`
- `git remote -v`
- `git status -sb`

Abort if:

- Not a git repo
- `origin` is missing
- `origin` is not a GitHub remote (or remote URL is unclear)

### 2) Sync and branch discipline

Run:

- `git fetch origin`
- `git branch --show-current`

If on `main` or `master` and changes are non-trivial:

- create a feature branch:
  - `git switch -c feature/<short-name>`

If remote branch exists and local is behind:

- `git pull --rebase origin <branch>`

### 3) Quality gate (Python)

Run only what exists/configured in the repo:

- If Ruff is present/configured:
  - `ruff check .`
  - `ruff format --check .`

- If mypy is present/configured:
  - `mypy src`

- If pytest is present/configured:
  - `pytest -q`

Self-heal policy:

- If a gate fails: analyze → fix → retry once.
- If it still fails after one retry: abort.

### 4) Review and stage

Run:

- `git diff`
- `git add -A`
- `git diff --cached`

Abort if no staged changes.

### 5) Commit

Commit message must follow Conventional Commits:

- `feat: ...`
- `fix: ...`
- `refactor: ...`
- `chore: ...`
- `test: ...`
- `docs: ...`

Run:

- `git commit -m "<type>: <message>"`

### 6) Pre-push disclosure + ASK_USER (MANDATORY)

Before pushing, print:

- `origin` remote URL (from `git remote -v`)
- Current branch name
- Upstream status: `git status -sb`
- Commit(s) to be pushed:
  - If upstream exists: `git rev-list --count @{u}..HEAD`
  - Else: `git rev-list --count HEAD`
- Summary of the last commit: `git log -1 --stat`

Then issue:

- **ASK_USER**: Confirm push to GitHub (`github.com`) to `origin/<branch>`.

### 7) Push

After confirmation:

- If upstream not set:
  - `git push -u origin <branch>`
- Else:
  - `git push`

### 8) Post-push verification

Run:

- `git status -sb`
- `git log -1 --oneline`

## Guardrails

- Never use force push (`--force` / `--force-with-lease`) without a separate ASK_USER and explicit justification.
- Never push if secret-like content is detected in staged diff.
- Never rewrite history (rebase/squash) across shared branches without ASK_USER.
- Never modify files outside the workspace root.

## Mandatory Completion Artifacts (Always output)

### A) Task List

Bullet list of executed steps and commands run.

### B) Implementation Plan

Short statement of what changed (or “commit/push only”), plus any files touched to pass quality gates.

### C) Walkthrough

Minimal manual steps to reproduce:

- `git status -sb`
- run quality gates (ruff/mypy/pytest as applicable)
- `git add -A && git commit -m "..."`
- `git push -u origin <branch>`

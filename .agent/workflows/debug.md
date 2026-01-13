---
description: Debug and fix a failing test or runtime error
---

# /debug — Debug and Fix Issues

## Objective

Systematically debug and fix a failing test or runtime error.

## Input Required

- Error message or failing test name
- Steps to reproduce (if applicable)

## Execution Steps

### 1) Reproduce the Issue

// turbo
Run the failing test or command to confirm the error:

```bash
pytest {test_file}::{test_name} -v --tb=long
```

### 2) Analyze Error

- Read the full traceback
- Identify the failing assertion or exception
- Locate the source file and line number

### 3) Investigate Root Cause

// turbo
Search for related code:

```bash
grep -rn "{error_keyword}" javinizer/
```

Review the failing code section using `view_file` with specific line ranges.

### 4) Formulate Hypothesis

Before fixing, state:

- What you think is causing the error
- What change you will make
- Why this should fix the issue

### 5) Implement Fix

Make the minimal change needed to fix the issue.

### 6) Verify Fix

// turbo

```bash
# Run the specific failing test
pytest {test_file}::{test_name} -v

# Run related tests to check for regressions
pytest tests/ -v --tb=short
```

### 7) Document

If the bug was significant, add a comment explaining the fix.

## Guardrails

- Never change test assertions without understanding why they exist
- Prefer fixing the code over changing the test
- If the fix affects multiple files, create an implementation plan first

## Output

- Fixed code with passing tests
- Brief explanation of what was wrong and how it was fixed

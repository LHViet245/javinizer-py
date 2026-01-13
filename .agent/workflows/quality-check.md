---
description: Run all quality checks before committing
---

# /quality-check — Pre-commit Quality Gate

// turbo-all

## Objective

Run all quality checks to ensure code is ready for commit.

## Execution Steps

### 1) Format Code

```bash
ruff format .
```

### 2) Lint Code

```bash
ruff check . --fix
```

### 3) Type Check (if mypy configured)

```bash
mypy javinizer/ --ignore-missing-imports
```

### 4) Run Tests

```bash
pytest tests/ -v --tb=short
```

### 5) Check Test Coverage

```bash
pytest tests/ --cov=javinizer --cov-report=term-missing
```

## Success Criteria

- All formatters pass
- No lint errors (warnings acceptable)
- All tests pass
- Coverage > 80%

## On Failure

- If format fails: Review and fix formatting issues
- If lint fails: Fix linting errors, show diff
- If tests fail: Switch to `/debug` workflow
- If coverage low: Identify untested code, suggest tests

## Output

Summary table:

| Check | Status | Details |
|-------|--------|---------|
| Format | ✅/❌ | ... |
| Lint | ✅/❌ | ... |
| Tests | ✅/❌ | X passed, Y failed |
| Coverage | ✅/❌ | X% |

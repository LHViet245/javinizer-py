---
description: REFACTOR - Refactor code while maintaining functionality
---

# /refactor

You are a refactoring specialist agent.

## Objective

Improve code quality without changing external behavior.

## Safety First

> [!CAUTION]
> Before refactoring:
>
> 1. Ensure all tests pass
> 2. Understand what the code does
> 3. Have a rollback plan

## Process

### 1. Analyze Current State

// turbo

```bash
pytest tests/ -v --tb=short
```

If tests fail → fix first, then refactor.

### 2. Identify Refactoring Targets

Common targets:

- Long functions (> 50 lines)
- Duplicate code
- Complex conditionals
- Poor naming
- Missing type hints
- Code smells

### 3. Plan Changes

For each target:

- What will change
- Why it improves code
- Risk assessment (low/medium/high)

### 4. Execute Incrementally

- One change at a time
- Run tests after each change
- Commit working states

### 5. Common Refactoring Patterns

| Pattern | When to Use |
|---------|-------------|
| Extract Function | Long function, reusable logic |
| Rename | Unclear naming |
| Move | Wrong location |
| Inline | Unnecessary abstraction |
| Replace Conditional | Complex if/else chains |

### 6. Verification (REQUIRED)

// turbo

```bash
ruff format .
ruff check . --fix
pytest tests/ -v --tb=short
```

All checks must pass before completing.

## Guardrails

❌ **Never**:

- Change public API without discussion
- Remove tests
- Skip verification
- Refactor and add features simultaneously

✅ **Always**:

- Keep commits atomic
- Run tests frequently
- Document significant changes

## Rollback Plan

If something breaks:

```bash
git stash        # Save current changes
git checkout .   # Revert to last commit
```

## Output

- Cleaner code
- Same functionality
- All tests passing
- Summary of changes

## Next Steps

After successful refactor:

1. Run `/review` for peer review
2. Run `/push-github` to commit

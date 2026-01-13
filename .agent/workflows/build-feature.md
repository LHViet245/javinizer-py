---
description: BUILDER - Build a new feature following project patterns
---

# /build-feature

// turbo-all

You are a software builder agent.

## Input

A finalized, high-quality prompt describing the feature to build.

## Process

### 1. Analyze Requirements

- Understand the feature scope
- Identify affected files
- Check existing patterns in codebase

### 2. Break Into Modules

- Split feature into logical components
- Define dependencies between modules
- Plan implementation order

### 3. Define File Structure

- List new files to create
- List existing files to modify
- Follow project structure conventions:
  - `javinizer/scrapers/` - Scrapers
  - `javinizer/commands/` - CLI commands
  - `javinizer/models.py` - Data models
  - `tests/` - Test files

### 4. Generate Code Incrementally

- Implement one module at a time
- Follow existing code patterns
- Add type hints
- Write docstrings

### 5. Add Tests

- Create unit tests for new functions
- Use pytest patterns from `tests/`
- Mock external API calls

### 6. Validate Logic

- Review code for correctness
- Check edge cases
- Verify integration points

### 7. Quality Gate (REQUIRED)

// turbo

```bash
ruff format .
ruff check . --fix
pytest tests/ -v --tb=short
```

If any check fails → fix and retry.

## Output

Complete implementation with:

- Working code
- Unit tests
- Documentation updates (if applicable)

## Success Criteria

- All tests pass
- Lint clean
- Feature works as specified

## Next Steps

After successful build:

1. Run `/review` for code review
2. Run `/update-docs` if needed
3. Run `/push-github` to commit

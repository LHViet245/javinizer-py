---
description: BUILDER - Build a new feature following project patterns
---

# /build-feature — Feature Implementation

## Objective

Build a new feature following project patterns and best practices.

## Input Required

- Feature description
- Target files/modules to modify
- Acceptance criteria

## Execution Steps

### 1) Understand Requirements

- Restate the feature in technical terms
- Identify affected components
- List dependencies

### 2) Create Implementation Plan

Before coding, create a plan:

- Files to create/modify
- Functions to add
- Tests needed

### 3) Implement Incrementally

#### a) Create/Update Models (if needed)

// turbo
Add new fields to `javinizer/models.py`

#### b) Implement Core Logic

Follow patterns from existing code:

```python
# Use async/await for I/O
async def new_function(...) -> ReturnType:
    """Docstring with description."""
    pass
```

#### c) Update Tests

// turbo
Add tests in `tests/test_{module}.py`

### 4) Verify Implementation

// turbo

```bash
pytest tests/ -v --tb=short
ruff check .
```

### 5) Update Documentation

Update README.md or GUIDE.md if needed.

## Guardrails

- Follow existing code patterns
- Write tests for new functionality
- Keep functions focused and small
- Add docstrings to public functions

## Output

- Implemented feature with passing tests
- Updated documentation if applicable

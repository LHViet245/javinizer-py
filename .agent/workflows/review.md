---
description: REVIEWER - Review generated code for quality and correctness
---

# /review — Code Review

## Objective

Review generated code or changes for quality, correctness, and adherence to project standards.

## Input

- Generated output, code changes, or PR diff

## Review Checklist

### 1) Correctness

- [ ] Logic is correct and handles all cases
- [ ] Edge cases are handled (empty, None, boundary)
- [ ] Error handling is appropriate
- [ ] Async patterns are correct (await, async with)

### 2) Code Quality

- [ ] Follows PEP 8 style
- [ ] Functions are focused (< 50 lines)
- [ ] Naming is clear and descriptive
- [ ] No code duplication
- [ ] Type hints are present

### 3) Testing

- [ ] Tests cover happy path
- [ ] Tests cover edge cases
- [ ] Tests cover error cases
- [ ] Mocks are used for external dependencies

### 4) Security

- [ ] No hardcoded secrets
- [ ] Input is validated
- [ ] No SQL injection risks
- [ ] No path traversal risks

### 5) Documentation

- [ ] Docstrings are present
- [ ] Complex logic is commented
- [ ] README updated if needed

## Output Format

For each issue found:

```
**[SEVERITY]** Location: file:line
Issue: Description
Fix: Suggested fix
```

Severity levels:

- 🔴 **CRITICAL**: Must fix before merge
- 🟠 **MAJOR**: Should fix
- 🟡 **MINOR**: Nice to fix
- 💡 **SUGGESTION**: Optional improvement

## Final Verdict

- ✅ **APPROVE**: No issues or only minor suggestions
- 🔄 **REQUEST CHANGES**: Has issues that need fixing
- ❓ **NEEDS DISCUSSION**: Has design questions

---
description: META PROMPT - Analyze and plan before executing any task
---

# /meta-prompt — Task Analysis and Planning

## Objective

Before performing any complex task, ensure full understanding and create a clear execution plan.

## Process

### 1) Restate the Task

Rephrase the user's request in precise technical terms:

- What is being asked?
- What is the expected output?
- What are the success criteria?

### 2) Identify Constraints & Missing Info

Ask yourself:

- What information is missing?
- What assumptions am I making?
- What are the boundaries/limitations?
- Are there dependencies on other tasks?

### 3) Identify Affected Components

List:

- Files to read/modify
- Functions to change
- Tests to update
- Documentation to update

### 4) Assess Complexity

| Complexity | Criteria | Action |
|------------|----------|--------|
| Low | Single file, < 50 lines | Execute directly |
| Medium | 2-5 files, clear scope | Brief plan, then execute |
| High | Multiple files, unclear scope | Full implementation plan |

### 5) Propose Execution Plan

For Medium/High complexity:

```markdown
## Implementation Plan

### Phase 1: [Name]
- Step 1: ...
- Step 2: ...

### Phase 2: [Name]
- Step 3: ...

### Verification
- Test: ...
```

### 6) Await Approval

For High complexity: **ASK_USER** before proceeding.

## Guardrails

- Do NOT skip steps
- Do NOT assume; ask when unclear
- Do NOT execute before plan approval (for High complexity)

## Output

- Restated task
- Identified gaps/questions
- Execution plan with steps

---
description: PROMPT ENGINEER - Transform vague prompts into high-quality instructions
---

# /prompt-engineer — Prompt Refinement

## Objective

Transform a vague or low-quality user prompt into a precise, model-readable instruction.

## Input

A vague or ambiguous user prompt.

## Process

### 1) Analyze Intent

- What is the user trying to achieve?
- What is the expected output format?
- What context is needed?

### 2) Identify Ambiguity

Common issues:

- Unclear scope ("improve the code")
- Missing context ("fix the bug")
- Vague criteria ("make it better")
- Multiple goals in one prompt

### 3) Ask Clarifying Questions

If critical information is missing:

```markdown
Before I can help, I need to clarify:
1. [Question about scope]
2. [Question about constraints]
3. [Question about expected output]
```

### 4) Rewrite the Prompt

Structure the improved prompt:

```markdown
## Task
[Clear, specific goal]

## Context
[Relevant background information]

## Requirements
- [Specific requirement 1]
- [Specific requirement 2]

## Constraints
- [Limitation 1]
- [Limitation 2]

## Expected Output
[Format and content of the result]

## Success Criteria
- [Measurable criterion 1]
- [Measurable criterion 2]
```

## Prompt Quality Checklist

- [ ] Single, focused goal
- [ ] Clear success criteria
- [ ] Specific constraints
- [ ] Expected output format defined
- [ ] No ambiguous terms

## Constraints

- Do NOT perform the task itself
- Only output the improved prompt
- Keep the improved prompt concise but complete

## Output

The refined, high-quality prompt ready for execution.

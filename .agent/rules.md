# Global Rules for Google Antigravity

## Overview

These rules guide the AI agent's behavior for optimal collaboration, context management, and workflow synchronization. Follow these rules to ensure consistent, high-quality assistance.

---

## 1. Language & Communication

### Response Language

- Respond in Vietnamese

### Communication Style

- Be concise and direct - avoid unnecessary verbosity
- Use markdown formatting for readability (headers, lists, code blocks)
- Use backticks for `file names`, `function names`, `variables`
- Provide code examples when explaining concepts
- Explain reasoning behind recommendations
- Ask clarifying questions when requirements are unclear

---

## 2. Agent Modes & Workflow

### Mode Definitions

| Mode | Purpose | When to Use |
|------|---------|-------------|
| **PLANNING** | Research, understand requirements, design approach | Starting new tasks, complex features, architecture changes |
| **EXECUTION** | Write code, implement changes | After plan approval or for simple tasks |
| **VERIFICATION** | Test changes, validate correctness | After implementation complete |

### Mode Switching Rules

```
PLANNING → EXECUTION: Only after user approves implementation plan
EXECUTION → VERIFICATION: After all code changes complete
VERIFICATION → PLANNING: If tests reveal design flaws
VERIFICATION → EXECUTION: If tests reveal minor bugs (stay in same TaskName)
```

### When to Skip Planning

- Simple, single-file edits (< 50 lines)
- Quick fixes with obvious solutions
- Answering questions without code changes
- Formatting or typo corrections

---

## 3. Artifacts & Documentation

### Required Artifacts

| Artifact | When to Create | Purpose |
|----------|----------------|---------|
| `task.md` | Complex, multi-step tasks | Track progress with checklist |
| `implementation_plan.md` | PLANNING mode for significant changes | Document approach, get approval |
| `walkthrough.md` | After VERIFICATION complete | Summarize work done, embed proof |

### Artifact Guidelines

- Keep artifacts **concise** - avoid redundancy
- Update `task.md` after each major step: `[ ]` → `[/]` → `[x]`
- Include file links: `[filename](file:///path/to/file)`
- Embed screenshots/recordings for UI changes
- Use `render_diffs(file:///path)` to show code changes

---

## 4. Context Management

### Context Preservation

- Reference previous conversation when relevant
- Maintain awareness of open files and cursor position
- Track changes made in current session
- Use existing code patterns in the project

### Context Optimization

- Prioritize viewing file outlines before full content
- Use `grep_search` for targeted searches
- Limit `view_file` to relevant line ranges
- Cache understanding of frequently accessed files

### Long Context Handling

- Summarize lengthy research before proceeding
- Break complex tasks into smaller, focused steps
- Reference artifacts instead of repeating content

---

## 5. Tool Usage Optimization

### Tool Selection Priority

| Task | Preferred Tool | Reason |
|------|----------------|--------|
| Explore file structure | `view_file_outline` | Faster, shows structure |
| Find specific code | `grep_search` | Targeted, efficient |
| Understand codebase | `find_by_name` + `view_file_outline` | Comprehensive overview |
| Make single edit | `replace_file_content` | Atomic change |
| Make multiple edits | `multi_replace_file_content` | Multiple non-adjacent changes |
| Run tests | `run_command` | Validate changes |

### Parallel Tool Calls

- Execute independent tool calls in parallel
- Never parallelize calls that depend on each other
- Never parallelize multiple edits to the same file
- Group related searches together

### Command Safety

- **Safe to auto-run**: `ls`, `cat`, `grep`, `find`, `pytest`, `git status`, `git log`
- **Require confirmation**: `rm`, `git push`, `pip install`, database changes
- **Never auto-run**: `rm -rf`, `DROP TABLE`, format commands

---

## 6. Code Quality Standards

### Python Style

- Follow PEP 8 style guide
- Use type hints for parameters and return values
- Write docstrings for public functions/classes
- Prefer descriptive variable names
- Maximum line length: 88 characters (Black compatible)

### Code Changes

- Always show changes before executing
- Preserve existing functionality unless explicitly asked
- Follow existing code patterns in the project
- Explain impact of significant changes

### Testing

- Run existing tests after making changes
- Create unit tests for new features
- Use pytest as the testing framework
- Mock external API calls in unit tests

---

## 7. Version Control

### Commit Standards

- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- Write clear, descriptive commit messages
- Keep commits atomic and focused
- Review changes before committing

### Git Safety

- Always ask confirmation before `git push`
- Show `git diff` before committing
- Verify branch before pushing
- Never force push to main/master

---

## 8. Error Handling & Recovery

### When Errors Occur

1. **Analyze**: Identify root cause from error message
2. **Search**: Look for similar patterns in codebase
3. **Research**: Use `search_web` if needed
4. **Fix**: Apply targeted fix
5. **Verify**: Run tests to confirm fix

### Recovery Strategies

| Scenario | Action |
|----------|--------|
| Build fails | Check error logs, fix syntax issues |
| Tests fail | Review test output, identify failing assertions |
| Command not found | Check PATH, install missing dependencies |
| File not found | Verify path, check case sensitivity |
| Permission denied | Suggest running with appropriate permissions |

### Backtracking

- If blocked in EXECUTION, switch back to PLANNING
- Update TaskSummary to explain direction change
- Keep same TaskName when backtracking mid-task

---

## 9. Workflow Synchronization

### Task Boundaries

- Call `task_boundary` at start of significant work
- Update status every ~5 tool calls
- TaskStatus describes **next steps**, not previous
- TaskSummary describes **what was done**

### Handoffs

- Document assumptions in artifacts
- Include verification steps for follow-up
- Link to relevant files and line numbers
- Note any pending items or blockers

### Multi-Agent Coordination

- Use artifacts as shared state between sessions
- Keep `task.md` updated for session continuity
- Document decisions and reasoning in plans
- Reference conversation history when relevant

---

## 10. Safety & Security

### Never Auto-Run

- Destructive commands (delete, drop, format)
- Commands that modify system state
- Network requests to unknown endpoints
- Commands with unclear side effects

### Always Confirm Before

- Deleting files or directories
- Making database changes
- Installing new dependencies
- Pushing code to remote repositories
- Making breaking API changes

### Security Best Practices

- Never commit secrets, API keys, passwords
- Use environment variables for sensitive data
- Validate and sanitize user inputs
- Be cautious with file paths from user input

---

## 11. Custom Preferences

<!-- Add your personal preferences below -->

### Project-Specific Rules

- Keep README.md, CONTRIBUTING.md, GUIDE.md updated
- Document all API changes
- Include code examples in documentation

### Preferred Behaviors

- Auto-run safe commands when appropriate
- Batch related questions together
- Provide options for complex decisions

---

## Quick Reference

### Mode Flow

```
User Request → PLANNING → (User Approval) → EXECUTION → VERIFICATION → Complete
                  ↑                              |
                  └──── (If design flaws) ───────┘
```

### Artifact Flow

```
Complex Task Start → task.md → implementation_plan.md → (Approval) → Code → walkthrough.md
```

### Tool Call Flow

```
1. view_file_outline (understand structure)
2. grep_search (find specific code)
3. view_file (read relevant sections)
4. replace_file_content / write_to_file (make changes)
5. run_command (test changes)
```

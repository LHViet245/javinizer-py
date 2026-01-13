---
description: Update project documentation
---

# /update-docs — Documentation Update

## Objective

Update project documentation to reflect current code state.

## Execution Steps

### 1) Analyze Current State

// turbo

```bash
# Check what files have changed recently
git diff --name-only HEAD~5

# List public modules
find javinizer -name "*.py" -not -name "__*"
```

### 2) Update README.md

Check and update:

- [ ] Installation instructions still work
- [ ] Usage examples are current
- [ ] Supported sources list is complete
- [ ] Configuration options are documented

### 3) Update CONTRIBUTING.md

Verify:

- [ ] Development setup instructions
- [ ] Testing instructions
- [ ] Code style guidelines
- [ ] PR process

### 4) Update GUIDE.md

Ensure:

- [ ] Detailed usage examples
- [ ] API documentation
- [ ] Troubleshooting section

### 5) Update Docstrings

For each public function/class:

```python
def function_name(param: Type) -> ReturnType:
    """Short description.
    
    Longer description if needed.
    
    Args:
        param: Description of parameter.
    
    Returns:
        Description of return value.
    
    Raises:
        ErrorType: When this error occurs.
    
    Example:
        >>> function_name("example")
        "result"
    """
```

### 6) Verify Links

// turbo

```bash
# Check for broken internal links in markdown
grep -rn "\[.*\](.*\.md)" *.md
```

## Output

- Updated documentation files
- Changelog entry if significant changes

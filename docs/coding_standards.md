# Coding Standards & Best Practices

## Python Dataclasses

### Mutable Default Arguments

Never use mutable default arguments (like `list` or `dict`) directly in dataclass fields, and avoid using `None` with a `__post_init__` workaround if possible.

**❌ Bad:**

```python
@dataclass
class Config:
    items: list = []  # Syntax error in some contexts or dangerous sharing
    # OR
    items: list = None
    def __post_init__(self):
        if self.items is None: self.items = []
```

**✅ Good:**

```python
from dataclasses import dataclass, field

@dataclass
class Config:
    items: list[str] = field(default_factory=list)
```

## Global State & Side Effects

### IO/Console Objects

Do not instantiate objects that interact with standard I/O (like `rich.Console`) at the module level. This causes side effects during imports (e.g., when running tests or generating documentation).

**❌ Bad:**

```python
# module.py
console = Console()  # Created on import
```

**✅ Good:**

```python
# module.py
def process():
    console = Console()
    console.print("...")
```

## File Handling

### Filename Sanitization

Windows filenames are restrictive. Always use a robust sanitization function.

- Replace restricted chars: `\/:*?"<>|`
- Standardize replacements: Map `:` to `-` (common in titles).
- Strip leading/trailing spaces and dots.

# Workspace Rules - Javinizer-py

> **Note**: General rules regarding code style, testing, version control, and security are defined in [GEMINI.md](file:///C:/Users/gadan/.gemini/GEMINI.md). This file only contains rules **specific to the javinizer-py project**.

---

## 1. Project Overview

**Javinizer-py** is a Python tool for organizing and managing metadata for JAV (Japanese Adult Video). The project uses scrapers to collect information from various sources.

### Tech Stack

- **Language**: Python 3.10+
- **Models**: Pydantic v2
- **HTTP**: httpx (async)
- **Testing**: pytest + pytest-asyncio
- **Linting/Formatting**: ruff

---

## 2. Virtual Environment (REQUIRED)

**ALWAYS** use the project's virtual environment for all Python operations.

### Agent Protocol (CRITICAL)

When executing `python` or `pip` commands in the terminal, you **MUST** ensure the project's virtual environment is used.

**Preferred Method:** Use the direct path to the executable. This is the safest way to guarantee the correct environment is used, regardless of shell activation state.

- **Windows**: `.\env\Scripts\python.exe`
- **Linux/macOS**: `./env/bin/python`

**Example**:

```powershell
# ✅ Correct
.\env\Scripts\python.exe -m javinizer.scrapers.dmm
.\env\Scripts\pip.exe install -r requirements.txt

# ❌ Incorrect (unless verified active)
python -m javinizer.scrapers.dmm
pip install package
```

### Rules

| Rule | Description |
|------|-------------|
| **Explicit Path** | **PREFER** using `.\env\Scripts\python.exe` over `python` |
| **Verify Context** | If using `python`, ensure it resolves to `.../env/...` using `where.exe python` |
| **Install safely** | Always use `.\env\Scripts\pip.exe` for package installation |

---

## 3. Project Structure

```
javinizer-py/
├── javinizer/              # Main source code
│   ├── __init__.py
│   ├── models.py           # Pydantic data models
│   ├── health.py           # Health check endpoints
│   ├── aggregator.py       # Multi-source data aggregation
│   └── scrapers/           # Website scrapers
│       ├── base.py         # Base scraper class
│       └── *.py            # Individual scrapers
├── tests/                  # Test files
│   ├── test_*.py
│   └── fixtures/           # Test data
├── .agent/                 # Agent configuration (gitignored)
│   ├── rules/              # Rules files
│   └── workflows/          # Workflow files
├── README.md
├── CONTRIBUTING.md
├── GUIDE.md
└── pyproject.toml
```

---

## 4. Scraper Development

### Base Class Interface

Every scraper **must** inherit from `BaseScraper` and implement:

```python
class MyScraper(BaseScraper):
    async def search(self, query: str) -> list[SearchResult]: ...
    async def get_metadata(self, id: str) -> Metadata: ...
    def validate(self, data: dict) -> bool: ...
```

### Scraper Requirements

| Requirement | Description |
|-------------|-------------|
| Rate Limiting | Use `asyncio.sleep()` between requests (min 1s) |
| Error Handling | Catch specific exceptions, log with context |
| Retry Logic | Implement exponential backoff for transient errors |
| User-Agent | Rotate user agents to avoid blocking |
| Timeout | Set request timeout (default: 30s) |

### Testing Scrapers

```bash
# Run scraper tests only
pytest tests/test_scrapers.py -v

# Test specific scraper
pytest tests/test_scrapers.py -v -k "DMMScraper"
```

---

## 5. Data Models

### Pydantic Model Guidelines

- Define all models in `javinizer/models.py`
- Use `Field()` with descriptions for all fields
- Implement validators for data sanitization
- Use `model_config` for JSON serialization settings

### Example Pattern

```python
from pydantic import BaseModel, Field, field_validator

class Metadata(BaseModel):
    id: str = Field(..., description="Unique identifier")
    title: str = Field(..., min_length=1)
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        return v.upper().strip()
```

---

## 6. Async Patterns

### Preferred Async Patterns

```python
# ✅ Good: Use httpx async client
async with httpx.AsyncClient() as client:
    response = await client.get(url)

# ✅ Good: Batch concurrent requests
results = await asyncio.gather(*[fetch(url) for url in urls])

# ❌ Bad: Blocking calls in async context
requests.get(url)  # Don't use requests in async code
```

### Rate Limiting Pattern

```python
async def fetch_with_rate_limit(urls: list[str], delay: float = 1.0):
    results = []
    for url in urls:
        result = await fetch(url)
        results.append(result)
        await asyncio.sleep(delay)
    return results
```

---

## 7. Available Workflows

Workflows available in `.agent/workflows/`:

| Workflow | Purpose |
|----------|---------|
| `/project-leader` | Orchestrate complex tasks |
| `/build-feature` | Build new features |
| `/add-scraper` | Add new website scraper |
| `/debug` | Debug failing tests |
| `/generate-tests` | Generate unit tests |
| `/refactor` | Safe code refactoring |
| `/review` | Code review |
| `/quality-check` | Pre-commit quality gate |
| `/push-github` | Push to GitHub |
| `/update-docs` | Update documentation |

---

## 8. Project-Specific Commands

### Common Commands

| Command | Description |
|---------|-------------|
| `pytest` | Run all tests |
| `pytest -x` | Stop on first failure |
| `pytest --cov=javinizer` | Run with coverage |
| `ruff check .` | Lint code |
| `ruff format .` | Format code |
| `python -m javinizer health` | Health check |

### Safe to Auto-Run

- `pytest`, `ruff check`, `ruff format`
- `python -m javinizer health`
- `git status`, `git diff`

---

## 9. Key Files Reference

| File | Purpose | When to Update |
|------|---------|----------------|
| `models.py` | Data schemas | Adding new fields |
| `aggregator.py` | Multi-source logic | Changing merge strategy |
| `scrapers/base.py` | Base interface | Adding common methods |
| `pyproject.toml` | Dependencies | Adding packages |
| `README.md` | User docs | New features |
| `CONTRIBUTING.md` | Dev docs | Process changes |
| `GUIDE.md` | Detailed guide | Workflow updates |

---

## 10. Known Issues & Gotchas

- **SSL Errors**: Some sites require custom SSL context
- **Cloudflare**: May need browser automation for CF-protected sites
- **Rate Limits**: Respect 1-2 second delays between requests
- **Encoding**: Always specify `encoding='utf-8'` for file I/O
- **Windows Paths**: Use `pathlib.Path` for cross-platform compatibility

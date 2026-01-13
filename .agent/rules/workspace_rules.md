# Workspace Rules - Javinizer-py

> **Note**: Các quy tắc chung về code style, testing, version control, security đã được định nghĩa trong [GEMINI.md](file:///C:/Users/gadan/.gemini/GEMINI.md). File này chỉ chứa các quy tắc **đặc thù cho dự án javinizer-py**.

---

## 1. Project Overview

**Javinizer-py** là công cụ Python để tổ chức và quản lý metadata cho JAV (Japanese Adult Video). Dự án sử dụng scrapers để thu thập thông tin từ nhiều nguồn khác nhau.

### Tech Stack

- **Language**: Python 3.10+
- **Models**: Pydantic v2
- **HTTP**: httpx (async)
- **Testing**: pytest + pytest-asyncio
- **Linting/Formatting**: ruff

---

## 2. Virtual Environment (REQUIRED)

**ALWAYS** use the project's virtual environment for all Python operations.

### Activation

```powershell
# Windows (PowerShell)
& env\Scripts\Activate.ps1

# Windows (CMD)
env\Scripts\activate.bat

# Linux/macOS
source env/bin/activate
```

### Rules

| Rule | Description |
|------|-------------|
| **Always activate first** | Before running any Python command, activate the venv |
| **Install packages in venv** | Never use `pip install` globally for project deps |
| **Use venv Python** | Run scripts with `python` after activation |
| **Check activation** | Prompt should show `(env)` prefix when activated |

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

Các workflows có sẵn trong `.agent/workflows/`:

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

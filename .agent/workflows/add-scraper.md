---
description: Add a new website scraper to the project
---

# /add-scraper

// turbo-all

## Objective

Add a new scraper for [WEBSITE_NAME] following javinizer-py patterns.

## Prerequisites

- Understanding of target website structure
- API documentation (if available)
- Test data samples

## Process

### 1. Research Phase

// turbo

```bash
# Check existing scrapers for patterns
type javinizer\scrapers\r18dev.py
type javinizer\scrapers\dmm.py
```

Key patterns to follow:

- Inherit from `BaseScraper`
- Implement `search()` and `get_metadata()`
- Use `httpx` for HTTP requests
- Handle rate limiting

### 2. Create Scraper File

Create `javinizer/scrapers/{website_name}.py`:

```python
"""
{Website Name} scraper for javinizer.

This scraper handles fetching metadata from {website}.
"""

import re
from typing import Optional

import httpx

from javinizer.models import Actress, MovieMetadata
from javinizer.scrapers.base import BaseScraper
from javinizer.scrapers.utils import normalize_id_variants


class {WebsiteName}Scraper(BaseScraper):
    """Scraper for {website name}."""
    
    name = "{website_name}"
    base_url = "https://{website}.com"
    
    async def search(self, movie_id: str) -> Optional[MovieMetadata]:
        """Search for a movie by ID."""
        # Implementation here
        pass
    
    async def get_metadata(self, url: str) -> Optional[MovieMetadata]:
        """Get metadata from a specific URL."""
        # Implementation here
        pass
```

### 3. Register Scraper

Update `javinizer/scrapers/__init__.py`:

```python
from javinizer.scrapers.{website_name} import {WebsiteName}Scraper

SCRAPERS = {
    # ... existing scrapers
    "{website_name}": {WebsiteName}Scraper,
}
```

### 4. Create Tests

Create `tests/test_scrapers_{website_name}.py` or add to `tests/test_scrapers.py`:

```python
class Test{WebsiteName}Scraper:
    """Tests for {WebsiteName}Scraper."""
    
    def test_normalize_id_variants(self):
        """Test ID normalization."""
        pass
    
    def test_search_returns_metadata(self):
        """Test search functionality."""
        pass
```

### 5. Run Tests

// turbo

```bash
pytest tests/test_scrapers.py -v -k "{website_name}"
```

### 6. Quality Gate (REQUIRED)

// turbo

```bash
ruff format javinizer/scrapers/{website_name}.py
ruff check javinizer/scrapers/{website_name}.py --fix
pytest tests/ -v --tb=short
```

### 7. Update Documentation

Update `README.md` to include new scraper in supported sources list.

## Checklist

- [ ] Scraper file created
- [ ] Registered in `__init__.py`
- [ ] Tests written
- [ ] All tests pass
- [ ] Lint clean
- [ ] README updated

## Output

- New scraper in `javinizer/scrapers/`
- Unit tests
- Updated documentation

## Next Steps

1. Run `/review` for code review
2. Test with real data: `javinizer find [ID] --source {website_name}`
3. Run `/push-github` to commit

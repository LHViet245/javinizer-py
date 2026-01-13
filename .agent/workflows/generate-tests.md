---
description: Generate unit tests for a module or function
---

# /generate-tests — Create Unit Tests

## Objective

Generate comprehensive unit tests for a specified module or function.

## Input Required

- Target file path (e.g., `javinizer/aggregator.py`)
- Specific function/class name (optional)

## Execution Steps

### 1) Analyze Target Code

Read the target file to understand:

- Function signatures and return types
- Input parameters and their types
- Edge cases and error conditions
- Dependencies that need mocking

### 2) Identify Test Cases

For each function, identify:

- **Happy path**: Normal successful execution
- **Edge cases**: Empty inputs, None values, boundary conditions
- **Error cases**: Invalid inputs, exceptions
- **Async handling**: If async function, test async behavior

### 3) Create Test File

Create `tests/test_{module_name}.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from javinizer.{module} import {TargetClass/function}

class Test{ClassName}:
    @pytest.fixture
    def instance(self):
        return {ClassName}()
    
    # Happy path tests
    def test_{function}_returns_expected(self, instance):
        result = instance.{function}(valid_input)
        assert result == expected_output
    
    # Edge case tests
    def test_{function}_handles_empty_input(self, instance):
        result = instance.{function}([])
        assert result == []
    
    # Error case tests
    def test_{function}_raises_on_invalid(self, instance):
        with pytest.raises(ValueError):
            instance.{function}(invalid_input)
    
    # Async tests
    @pytest.mark.asyncio
    async def test_{async_function}_awaits_correctly(self, instance):
        result = await instance.{async_function}()
        assert result is not None
```

### 4) Mock External Dependencies

For HTTP calls, database, or external services:

```python
@pytest.fixture
def mock_client():
    with patch('httpx.AsyncClient') as mock:
        yield mock

async def test_with_mocked_http(mock_client):
    mock_client.return_value.__aenter__.return_value.get.return_value = Mock(
        status_code=200,
        json=lambda: {"data": "test"}
    )
    # Test implementation
```

### 5) Run and Verify

// turbo

```bash
pytest tests/test_{module_name}.py -v --tb=short
```

### 6) Check Coverage

// turbo

```bash
pytest tests/test_{module_name}.py --cov=javinizer.{module} --cov-report=term-missing
```

## Test Naming Convention

- `test_{function_name}_{scenario}_{expected_result}`
- Example: `test_search_empty_query_returns_empty_list`

## Output

- New test file with comprehensive test cases
- Coverage report showing tested lines

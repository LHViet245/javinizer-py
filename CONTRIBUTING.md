# Contributing to Javinizer

First off, thanks for taking the time to contribute! We welcome contributions from everyone.

## Code Style

We follow strict Python code style guide to ensure consistency and maintainability.

### Formatting & Linting

We use [Ruff](https://github.com/astral-sh/ruff) for both formatting and linting.

To format your code:

```bash
ruff format .
```

To run the linter:

```bash
ruff check .
```

### Type Checking

We use [mypy](https://mypy.readthedocs.io/) for static type checking. All new code must be fully typed.

To run type checks:

```bash
mypy .
```

(Refer to valid configuration in `pyproject.toml` or `mypy.ini` if present)

## Testing

We use [pytest](https://docs.pytest.org/) for testing.

- **Location**: All tests are located in the `tests/` directory.
- **Naming**: Test files must start with `test_`.
- **Running Tests**:

  ```bash
  pytest
  ```

Please ensure you write unit tests for any new features or bug fixes.

## Documentation

- **Docstrings**: We prefer Google-style or NumPy-style docstrings for all functions and classes.
- **GUIDE.md**: If your changes affect user-facing functionality (e.g., new CLI flags), please update `GUIDE.md` and its translations.

## Pull Request Process

1. **Fork** the repo on GitHub.
2. **Clone** project to your own machine.
3. **Commit** changes to your own branch.
4. **Push** your work back up to your fork.
5. Submit a **Pull Request** so that we can review your changes.

### PR Checklist

- [ ] My code follows the code style of this project (`ruff format` & `ruff check`).
- [ ] I have added tests that prove my fix is effective or that my feature works.
- [ ] All new and existing tests passed.
- [ ] I have added necessary documentation (if appropriate).

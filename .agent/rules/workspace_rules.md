# Javinizer Workspace Rules

## 1. Technology Stack Implementation

- **Core**: Python 3.10+.
- **CLI**: Use `click` for all command-line interfaces. Use `rich` for terminal output/logging.
- **Networking**: Use `httpx` for HTTP requests. **DO NOT** use `requests`. Ensure SOCKS5 proxy support.
- **Validation**: Use `pydantic` (v2) for all data models and configuration parsing.
- **Parsing**: Use `beautifulsoup4` with `lxml` parser.

## 2. Code Quality & Standards

- **Linting & Formatting**: Strict adherence to `ruff` rules.
  - Run `ruff format .` for formatting.
  - Run `ruff check .` for linting.
- **Type Safety**: strict `mypy` compliance.
  - All functional arguments and return types MUST be typed.
  - No `Any` unless absolutely necessary and documented.
- **Docstrings**: Google-style docstrings for all modules, classes, and public functions.

## 3. Architecture & Patterns

- **Configuration**: Changes to config structure must be reflected in `jvSettings.json` handling.
- **Error Handling**:
  - Never crash with a raw stack trace for user-facing errors (network, parsing).
  - Use `rich.console` to print user-friendly error messages.
  - Log full debug info to `javinizer.log`.

## 4. Documentation & Maintenance

- **User Guide**: If CLI arguments or flags change, UPDATE `GUIDE.md` immediately.
- **Testing**: Add `pytest` cases in `tests/` for every new feature.

## 5. Interaction Guidelines

- **Language**: Vietnamese (Tiếng Việt).
- **Style**: Direct, professional, no fluff.

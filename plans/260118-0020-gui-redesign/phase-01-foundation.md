# Phase 01: Foundation (Setup)

Status: ⬜ Pending

## Objective

Establish the project structure, install dependencies, and create the base layout with the "Liquid Glass" design system.

## Requirements

### Functional

- [ ] FastAPI server running on `http://localhost:8000`.
- [ ] Static file serving configured.
- [ ] Base Jinja2 template with "Liquid Glass" CSS variables and Tailwind setup.
- [ ] Home page renders with the 3-panel layout (Sidebar, Main, Inspector).

### Non-Functional

- [ ] No Node.js required (use Tailwind CDN or standalone script for dev).
- [ ] Dark mode default.

## Implementation Steps

1. [ ] Install `fastapi`, `uvicorn`, `jinja2`, `python-multipart`.
2. [ ] Create directory structure (`javinizer/web/`, `templates/`, `static/`).
3. [ ] Create `javinizer/web/server.py` (FastAPI app).
4. [ ] Create `javinizer/web/static/css/liquid.css` (Glassmorphism styles from specs).
5. [ ] Create `javinizer/web/templates/base.html` and `index.html`.

## Files to Create

- `javinizer/web/server.py`
- `javinizer/web/static/css/liquid.css`
- `javinizer/web/templates/base.html`
- `javinizer/web/templates/index.html`

## Test Criteria

- [ ] Run `python -m javinizer.web.server` starts the server.
- [ ] Opening browser shows the "Liquid Glass" background and layout skeleton.
- [ ] CSS variables for colors (Neon/Dark) are working.

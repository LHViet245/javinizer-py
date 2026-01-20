# Specification: Javinizer Web Station

## 1. Executive Summary

Development of a modern, web-based GUI for Javinizer to replace/augment the CLI. Features a "Liquid Glass" aesthetic, recursive file management, visual metadata editing, and real-time process logging.

## 2. Tech Stack

- **Backend:** FastAPI (Python 3.10+)
- **Server:** Uvicorn
- **Templating:** Jinja2
- **Styling:** TailwindCSS (via CDN for dev) + Custom CSS variables
- **Interactivity:** HTMX + Alpine.js
- **Real-time:** Server-Sent Events (SSE)

## 3. Architecture

### Directory Structure

```
javinizer/
├── web/
│   ├── api/          # API Routers
│   │   ├── filesystem.py
│   │   ├── operations.py
│   │   └── settings.py
│   ├── static/       # CSS/JS/Images
│   ├── templates/    # Jinja2 HTML
│   │   ├── components/
│   │   └── layouts/
│   └── server.py     # FastAPI App Entry
```

### API Contract (Draft)

#### Filesystem

- `GET /api/fs/list?path={path}` -> `[ {name, type, path, ...} ]`

#### Operations

- `POST /api/ops/preview` -> `PreivewResult`
- `POST /api/ops/execute` -> `JobID`
- `GET /api/ops/job/{id}` -> `JobStatus`

#### Logs

- `GET /api/logs/stream` -> `EventSource` (text/event-stream)

## 4. UI Components

### Theme (Liquid Glass)

- Background: `#0f0c29` -> `#302b63` gradient.
- Panels: `backdrop-filter: blur(16px)`, `bg-white/5`.
- Font: Inter / System UI.

### Layout

- **Sidebar:** Fixed width 280px. Scrollable tree.
- **Main:** Flex-grow. Grid details.
- **Inspector:** Fixed width 350px. Form inputs.

## 5. Build Checklist

- [ ] Install deps: `pip install fastapi uvicorn Jinja2 python-multipart`
- [ ] Create `server.py` scaffold.
- [ ] Create `liquid.css` with Tailwind directives.

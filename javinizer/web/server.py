import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from rich.console import Console

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

console = Console()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown events"""
    console.print("[green]Javinizer Web Station starting...[/]")
    yield
    console.print("[yellow]Shutting down...[/]")

app = FastAPI(
    title="Javinizer Web Station",
    description="Modern Web GUI for Javinizer",
    version="0.1.0",
    lifespan=lifespan
)

# CORS - Configurable via environment variable
# Set ALLOWED_ORIGINS="http://localhost:8001,http://127.0.0.1:8001" in production
_cors_origins = os.environ.get("ALLOWED_ORIGINS", "*")
if _cors_origins == "*":
    # Development mode - allow all (convenient but insecure)
    allowed_origins = ["*"]
else:
    # Production mode - only allow specified origins
    allowed_origins = [origin.strip() for origin in _cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Limit to needed methods only
    allow_headers=["Content-Type", "Accept"],  # Limit to needed headers
)

# Static Files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@app.get("/")
async def index(request: Request):
    """Render home page with initial root listing"""
    # Get roots (Drives or /)
    from javinizer.web.api.filesystem import list_directory
    roots = await list_directory(None)
    return templates.TemplateResponse("index.html", {"request": request, "roots": roots})

# Import and mount API routers
from javinizer.web.api import filesystem  # noqa: E402
app.include_router(filesystem.router, prefix="/api/fs")

# Template endpoint for HTMX
@app.get("/api/fs/tree_fragment")
async def tree_fragment(request: Request, path: str):
    """Render a tree fragment for a given path (used by HTMX)"""
    from javinizer.web.api.filesystem import list_directory
    items = await list_directory(path)
    return templates.TemplateResponse(
        "components/file_tree.html", 
        {"request": request, "items": items}
    )

@app.get("/api/fs/grid_fragment")
async def grid_fragment(request: Request, path: str, q: str = None):
    """Render a folder grid/list for a given path"""
    from javinizer.web.api.filesystem import list_directory
    items = await list_directory(path, q=q)
    return templates.TemplateResponse(
        "components/file_grid.html", 
        {"request": request, "items": items, "current_path": path, "query": q}
    )

@app.get("/api/fs/inspector_fragment")
async def inspector_fragment(request: Request, path: str):
    """Render metadata inspector for a given file"""
    from pathlib import Path
    from javinizer.matcher import extract_movie_id
    from javinizer.cli_common import scrape_parallel, expand_sources
    from javinizer.config import settings
    
    p = Path(path)
    movie_id = extract_movie_id(p.name)
    
    metadata = {
        "name": p.name,
        "path": str(p),
        "is_file": p.is_file(),
        "size": f"{p.stat().st_size / (1024*1024):.2f} MB" if p.is_file() else "N/A",
        "movie_id": movie_id,
        "title": p.stem if p.is_file() else p.name
    }
    
    # Try to fetch real metadata if it's a video file and has ID
    if p.is_file() and movie_id:
        sources = expand_sources(["r18dev", "dmm_new"])
        # Run scraping in a thread to not block event loop (scrape_parallel is sync-ish with asyncio.run internal maybe?)
        # For now, let's just do a quick scrape if possible
        try:
            results = scrape_parallel(movie_id, sources, settings.proxy, settings, None)
            if results:
                from javinizer.aggregator import aggregate_metadata
                real_meta = aggregate_metadata(results, settings.priority)
                if real_meta:
                    metadata.update({
                        "title": real_meta.title,
                        "movie_id": real_meta.id,
                        "cover_url": real_meta.cover_url,
                        "release_date": str(real_meta.release_date) if real_meta.release_date else ""
                    })
        except Exception:
            pass

    return templates.TemplateResponse(
        "components/metadata_inspector.html", 
        {"request": request, "metadata": metadata}
    )

@app.post("/api/metadata/apply")
async def apply_metadata(request: Request):
    """Apply metadata changes to a file"""
    from html import escape
    
    form_data = await request.form()
    file_path = form_data.get("path")
    movie_id = form_data.get("movie_id") or ""
    title = form_data.get("title") or ""
    
    # In a real app, this would trigger renaming or NFO generation
    # For now, return a success fragment
    import logging
    logger = logging.getLogger("javinizer")
    logger.info(f"Applying metadata to {file_path}: [ID: {movie_id}] {title}")
    
    # SECURITY FIX: Escape user input to prevent XSS
    safe_movie_id = escape(str(movie_id))
    return f'<div class="p-4 bg-green-500/20 text-green-400 rounded-lg text-xs">Applied OK: {safe_movie_id}</div>'

@app.get("/api/logs/stream")
async def stream_logs():
    """SSE endpoint for real-time log streaming"""
    from javinizer.web.services.log_broadcaster import broadcaster
    return StreamingResponse(
        broadcaster.subscribe(),
        media_type="text/event-stream"
    )

# Setup Logging Integration
def setup_web_logging():
    import logging
    from javinizer.web.services.log_broadcaster import sse_handler
    logger = logging.getLogger("javinizer")
    # Add SSE handler if not already present
    if sse_handler not in logger.handlers:
        logger.addHandler(sse_handler)
        logger.info("Web log broadcaster linked successfully")

setup_web_logging()

# Operations API (Phase 3)
from javinizer.web.api import operations  # noqa: E402
app.include_router(operations.router, prefix="/api/ops")

from javinizer.web.api import settings  # noqa: E402
app.include_router(settings.router, prefix="/api/settings")

if __name__ == "__main__":
    import uvicorn
    # Use port 8001 by default as per session history
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(
        "javinizer.web.server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )


def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    """Run the Web Station server (called by CLI)"""
    import uvicorn
    console.print("[bold green]Starting Javinizer Web Station[/]")
    console.print(f"[dim]Server: http://{host}:{port}[/]")
    uvicorn.run(
        "javinizer.web.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


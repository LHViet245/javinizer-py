"""FastAPI application for Javinizer GUI"""

from pathlib import Path
from typing import Any, Optional

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.templating import Jinja2Templates
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    FastAPI = None  # type: ignore[misc,assignment]

from javinizer.config import load_settings, save_settings
from javinizer.logger import get_logger

logger = get_logger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent / "templates"


def create_app() -> "FastAPI":
    """Create and configure the FastAPI application"""
    if not HAS_FASTAPI:
        raise ImportError(
            "GUI dependencies not installed. Run: pip install javinizer[gui]"
        )

    app = FastAPI(
        title="Javinizer GUI",
        description="Web interface for Javinizer JAV metadata scraper",
        version="0.1.0",
    )

    # Setup templates
    templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request) -> HTMLResponse:
        """Home page with search and overview"""
        settings = load_settings()
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "title": "Javinizer",
                "settings": settings,
            },
        )

    @app.get("/search", response_class=HTMLResponse)
    async def search_page(request: Request, q: Optional[str] = None) -> HTMLResponse:
        """Search page for finding movies"""
        results: list[Any] = []
        if q:
            # TODO: Implement actual search
            pass
        return templates.TemplateResponse(
            "search.html",
            {
                "request": request,
                "title": "Search",
                "query": q,
                "results": results,
            },
        )

    @app.get("/settings", response_class=HTMLResponse)
    async def settings_page(request: Request) -> HTMLResponse:
        """Settings management page"""
        settings = load_settings()
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "title": "Settings",
                "settings": settings,
            },
        )

    @app.post("/api/settings")
    async def update_settings(request: Request) -> JSONResponse:
        """Update settings via API"""
        try:
            data = await request.json()
            settings = load_settings()
            
            # Update settings from form data
            for key, value in data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            
            save_settings(settings)
            return JSONResponse({"status": "ok", "message": "Settings saved"})
        except Exception as e:
            return JSONResponse(
                {"status": "error", "message": str(e)},
                status_code=400,
            )

    @app.get("/api/find/{movie_id}")
    async def api_find(movie_id: str, source: Optional[str] = None) -> dict[str, Any]:
        """API endpoint to find movie metadata"""
        from javinizer.cli_common import expand_sources, scrape_parallel
        from javinizer.aggregator import aggregate_metadata

        settings = load_settings()
        sources = expand_sources(
            source.split(",") if source else ["r18dev", "dmm"]
        )
        proxy_config = settings.proxy

        results = scrape_parallel(movie_id, sources, proxy_config, settings, None)

        if not results:
            raise HTTPException(status_code=404, detail="Movie not found")

        metadata = aggregate_metadata(results, settings.priority)
        if metadata is None:
            raise HTTPException(status_code=404, detail="Failed to aggregate metadata")
        return metadata.model_dump(mode="json")

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        """Health check endpoint"""
        return {"status": "ok", "version": "0.1.0"}

    return app


def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    """Run the GUI server"""
    if not HAS_FASTAPI:
        raise ImportError(
            "GUI dependencies not installed. Run: pip install javinizer[gui]"
        )

    # Ensure templates exist
    if not TEMPLATE_DIR.exists():
        TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
        logger.warning(f"Created template directory: {TEMPLATE_DIR}")

    app = create_app()
    uvicorn.run(app, host=host, port=port, reload=reload)


# CLI entry point
if __name__ == "__main__":
    run_server()

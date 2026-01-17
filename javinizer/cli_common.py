"""Shared CLI utilities and constants"""

from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from javinizer.models import Settings
from rich.console import Console

from javinizer.models import ProxyConfig
from javinizer.scrapers import (
    DMMScraper,
    R18DevScraper,
    JavlibraryScraper,
    DMMNewScraper,
    MGStageScraper,
)

# Global console instance
console = Console()

# Mapping of scraper names to classes
SCRAPERS = {
    "dmm": DMMScraper,
    "dmmja": DMMScraper,
    "r18dev": R18DevScraper,
    "r18": R18DevScraper,
    "javlibrary": JavlibraryScraper,
    "jav": JavlibraryScraper,
    "mgstage": MGStageScraper,
}

# Add dmm_new if playwright is available
if DMMNewScraper is not None:
    SCRAPERS["dmm_new"] = DMMNewScraper  # type: ignore[assignment]

# Alias expansion: when user specifies "dmm", try dmm_new first then dmm
SCRAPER_ALIASES: dict[str, list[str]] = {
    "dmm": ["dmm_new", "dmm"] if DMMNewScraper is not None else ["dmm"],
}


def expand_sources(source_list: list[str]) -> list[str]:
    """Expand source aliases to actual scraper names"""
    expanded = []
    for source in source_list:
        source_lower = source.strip().lower()
        if source_lower in SCRAPER_ALIASES:
            for alias in SCRAPER_ALIASES[source_lower]:
                if alias not in expanded:
                    expanded.append(alias)
        else:
            if source_lower not in expanded:
                expanded.append(source_lower)
    return expanded


def get_scraper(
    name: str,
    proxy: Optional[ProxyConfig] = None,
    cookies: Optional[dict[str, str]] = None,
    user_agent: Optional[str] = None,
) -> Any:
    """Get scraper instance by name"""
    name_lower = name.lower()
    scraper_class = SCRAPERS.get(name_lower)

    if scraper_class is None:
        return None

    # DMMNewScraper has different signature (no cookies/user_agent)
    if name_lower == "dmm_new":
        return scraper_class(proxy=proxy)

    return scraper_class(
        proxy=proxy,
        cookies=cookies,
        user_agent=user_agent,
    )


def scrape_parallel(
    movie_id: str,
    sources: list[str],
    proxy_config: Optional[ProxyConfig],
    settings: "Settings",
    console: Optional[Console],
    max_workers: int = 4,
) -> dict[str, Any]:
    """
    Run scrapers in parallel and collect results.

    Args:
        movie_id: ID to search for
        sources: List of source names (already expanded)
        proxy_config: Proxy configuration
        settings: Application settings object
        console: Console for output
        max_workers: Max parallel threads (default: 4)

    Returns:
        Dict mapping source name to MovieMetadata
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from javinizer.models import MovieMetadata

    results: dict[str, MovieMetadata] = {}

    def scrape_source(src: str) -> tuple[str, Any]:
        scraper = get_scraper(
            src,
            proxy=proxy_config,
            cookies=settings.javlibrary_cookies
            if src in ("javlibrary", "jav")
            else None,
            user_agent=settings.javlibrary_user_agent
            if src in ("javlibrary", "jav")
            else None,
        )

        if scraper is None:
            if console:
                console.print(f"[yellow]⚠️  Unknown source: {src}[/]")
            return src, None

        with scraper:
            try:
                # Use print() or logging but careful with console.print concurrency
                # We'll just capture output or let rich handle basic thread safety
                if console:
                    console.print(f"[dim]Scraping from {src}...[/]", end=" ")
                metadata = scraper.find(movie_id)
                if metadata:
                    if console:
                        console.print(f"[green]✓ ({src})[/]")
                    return src, metadata
                else:
                    if console:
                        console.print(f"[yellow]no results ({src})[/]")
                    return src, None
            except Exception as e:
                if console:
                    console.print(f"[red]error ({src}): {e}[/]")
                return src, None

    # Use ThreadPoolExecutor for I/O bound tasks
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}

        # Check if we should chain dmm_new -> dmm
        # This prevents dmm from running if dmm_new succeeds
        chain_dmm = "dmm_new" in sources and "dmm" in sources

        sources_to_submit = list(sources)
        if chain_dmm:
            sources_to_submit.remove("dmm_new")
            sources_to_submit.remove("dmm")

        def scrape_dmm_chain() -> tuple[str, Any]:
            """Try dmm_new, fallback to dmm on failure"""
            # Try dmm_new first
            src, meta = scrape_source("dmm_new")
            if meta:
                return src, meta

            # If dmm_new failed, try dmm
            # We don't print "no results" for dmm_new if we are falling back,
            # but scrape_source already prints "no results" or "error".
            # That's acceptable - user sees dmm_new failed, then dmm runs.
            return scrape_source("dmm")

        # Submit standard sources
        for src in sources_to_submit:
            futures[executor.submit(scrape_source, src)] = src

        # Submit dmm chain if needed
        if chain_dmm:
            futures[executor.submit(scrape_dmm_chain)] = "dmm_chain"

        # Process results
        for future in as_completed(futures):
            task_name = futures[future]
            try:
                result = future.result()
                if result:
                    result_src, metadata = result
                    if metadata:
                        results[result_src] = metadata
            except Exception as e:
                if console:
                    console.print(f"[red]Exception in thread for {task_name}: {e}[/]")

    return results

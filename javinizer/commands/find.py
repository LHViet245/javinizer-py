"""Find command module"""

import json
from typing import Optional

import click
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from javinizer.cli_common import console, expand_sources
from javinizer.models import MovieMetadata, ProxyConfig
from javinizer.config import load_settings
from javinizer.aggregator import aggregate_metadata
from javinizer.nfo import generate_nfo


@click.command()
@click.argument("movie_id")
@click.option(
    "--source",
    "-s",
    default="r18dev,javlibrary,dmm",
    help="Scraper source(s), comma-separated (dmm, r18dev, javlibrary). Default: all",
)
@click.option(
    "--proxy",
    "-p",
    default=None,
    help="Proxy URL (e.g., socks5://127.0.0.1:1080 or http://proxy:8080)",
)
@click.option("--nfo", is_flag=True, help="Output NFO XML")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option(
    "--no-aggregate",
    is_flag=True,
    help="Don't aggregate results, use first successful source only",
)
@click.option("--log-file", help="Path to log file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose (debug) logging")
def find(
    movie_id: str,
    source: str,
    proxy: Optional[str],
    nfo: bool,
    as_json: bool,
    no_aggregate: bool,
    log_file: Optional[str],
    verbose: bool,
):
    """Find metadata for a movie ID

    By default, searches all sources (r18dev, javlibrary, dmm) and aggregates results.

    Examples:

        javinizer find IPX-486

        javinizer find IPX-486 --source r18dev

        javinizer find IPX-486 --proxy socks5://127.0.0.1:1080
    """
    # Load settings first to check for default log file
    settings = load_settings()

    # Configure logging
    # CLI arg > Settings > None
    final_log_file = log_file or settings.log_file
    from javinizer.logger import configure_logging

    logger = configure_logging(verbose=verbose, log_file=final_log_file)

    logger.debug(f"Starting find command for {movie_id}")

    # Parse sources and expand aliases (dmm -> [dmm_new, dmm])
    sources = expand_sources([s.strip() for s in source.split(",")])

    console.print(f"[bold blue]🔍 Searching for:[/] {movie_id}")
    console.print(f"[dim]Sources: {', '.join(sources)}[/]")
    if final_log_file:
        console.print(f"[dim]Logging to: {final_log_file}[/]")

    # Override proxy if specified
    if proxy:
        proxy_config = ProxyConfig(enabled=True, url=proxy)
        console.print(f"[dim]Proxy: {proxy}[/]")
    else:
        proxy_config = settings.proxy
        if proxy_config.enabled:
            console.print(f"[dim]Proxy: {proxy_config.url}[/]")

    console.print()

    # Scrape from all sources
    results: dict[str, MovieMetadata] = {}

    from javinizer.cli_common import scrape_parallel

    results = scrape_parallel(movie_id, sources, proxy_config, settings, console)

    if not results:
        console.print(f"\n[yellow]⚠️  No results found for {movie_id}[/]")
        return

    console.print()

    # Aggregate results by default, unless --no-aggregate is specified
    if not no_aggregate and len(results) > 1:
        metadata = aggregate_metadata(results, settings.priority)
        console.print(f"[green]📦 Aggregated from {len(results)} sources[/]")
    else:
        # Use first available result
        metadata = list(results.values())[0]

    if metadata is None:
        console.print("[yellow]⚠️  Could not aggregate metadata[/]")
        return

    # Output based on format
    if nfo:
        _output_nfo(metadata)
    elif as_json:
        _output_json(metadata)
    else:
        _output_table(metadata)


def _output_table(metadata: MovieMetadata):
    """Pretty print metadata as table"""
    table = Table(title=f"📀 {metadata.display_name}", show_header=False, box=None)
    table.add_column("Field", style="cyan", width=15)
    table.add_column("Value", style="white")

    table.add_row("ID", metadata.id)
    table.add_row("Title", metadata.title)
    table.add_row("Source", f"[dim]{metadata.source}[/]")

    if metadata.original_title and metadata.original_title != metadata.title:
        table.add_row("Original", metadata.original_title)

    if metadata.release_date:
        table.add_row("Released", str(metadata.release_date))

    if metadata.runtime:
        table.add_row("Runtime", f"{metadata.runtime} min")

    if metadata.maker:
        table.add_row("Studio", metadata.maker)

    if metadata.label:
        table.add_row("Label", metadata.label)

    if metadata.director:
        table.add_row("Director", metadata.director)

    if metadata.series:
        table.add_row("Series", metadata.series)

    if metadata.actresses:
        names = [a.japanese_name or a.full_name for a in metadata.actresses]
        table.add_row("Actresses", ", ".join(names))

    if metadata.genres:
        table.add_row("Genres", ", ".join(metadata.genres[:5]))
        if len(metadata.genres) > 5:
            table.add_row("", f"... +{len(metadata.genres) - 5} more")

    if metadata.rating:
        table.add_row(
            "Rating", f"⭐ {metadata.rating.rating}/10 ({metadata.rating.votes} votes)"
        )

    if metadata.cover_url:
        table.add_row("Cover", f"[link={metadata.cover_url}]View[/link]")

    console.print(table)

    # Print description separately if exists
    if metadata.description:
        console.print()
        desc_preview = metadata.description[:300]
        if len(metadata.description) > 300:
            desc_preview += "..."
        console.print(Panel(desc_preview, title="Description", border_style="dim"))


def _output_nfo(metadata: MovieMetadata):
    """Output NFO XML"""
    nfo_content = generate_nfo(metadata)

    # Use syntax highlighting
    syntax = Syntax(nfo_content, "xml", theme="monokai", line_numbers=False)
    console.print(syntax)


def _output_json(metadata: MovieMetadata):
    """Output as JSON"""
    # Convert to dict, handling date serialization
    data = metadata.model_dump(mode="json")
    console.print_json(json.dumps(data, ensure_ascii=False, indent=2))

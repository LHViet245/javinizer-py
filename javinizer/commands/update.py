"""Update commands module"""

import asyncio
from typing import Optional, Any
from pathlib import Path

import click

from javinizer.cli_common import console, expand_sources, get_scraper
from javinizer.models import ProxyConfig
from javinizer.config import load_settings
from javinizer.matcher import extract_movie_id
from javinizer.downloader import ImageDownloader
from javinizer.nfo import generate_nfo
from javinizer.cli_helpers import process_thumbnails, translate_metadata_if_enabled


def update_folder_task(
    folder_path: Path,
    source: str,
    proxy_config: Optional[ProxyConfig],
    settings: Any,
    dry_run: bool,
    nfo_only: bool,
) -> bool:
    """Standalone update logic for a single folder"""
    if not folder_path.is_dir():
        console.print(f"[red]Not a folder: {folder_path}[/]")
        return False

    console.print(f"[bold cyan]Updating:[/] {folder_path.name}")

    # Extract movie ID from folder name
    movie_id = extract_movie_id(folder_path.name)
    if not movie_id:
        console.print(
            f"[red]Could not extract movie ID from folder name: {folder_path.name}[/]"
        )
        return False

    console.print(f"[cyan]Movie ID:[/] {movie_id}")

    # Fetch metadata - expand aliases (dmm -> [dmm_new, dmm])
    sources = expand_sources([s.strip() for s in source.split(",")])
    results = {}

    for src in sources:
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
            continue

        with scraper:
            try:
                console.print(f"[dim]Scraping from {src}...[/]", end=" ")
                metadata = scraper.find(movie_id)
                if metadata:
                    results[src] = metadata
                    console.print(f"[green]OK ({src})[/]")
                else:
                    console.print(f"[yellow]no results ({src})[/]")
            except Exception as e:
                console.print(f"[red]error ({src}): {e}[/]")

    if not results:
        console.print(f"[red]Could not find metadata for {movie_id}[/]")
        return False

    # Aggregate results if multiple sources found
    if len(results) > 1:
        from javinizer.aggregator import aggregate_metadata

        metadata = aggregate_metadata(results, settings.priority)
        console.print(f"[green]📦 Aggregated from {len(results)} sources[/]")
    else:
        metadata = list(results.values())[0]

    console.print(f"[green]Found:[/] {metadata.title}")

    if dry_run:
        console.print("[yellow]DRY RUN - No changes made[/]")
        return True

    # Get sort settings for filenames
    sort_settings = settings.sort

    # Determine file paths in folder
    nfo_path = (
        folder_path / f"{sort_settings.nfo_format.replace('<ID>', movie_id)}.nfo"
    )
    poster_path = folder_path / sort_settings.poster_filename
    backdrop_path = folder_path / sort_settings.backdrop_filename

    # Update images (default behavior)
    if not nfo_only and metadata.cover_url:
        downloader = ImageDownloader(
            proxy=proxy_config.httpx_proxy if proxy_config else None,
            timeout=settings.timeout,
        )

        console.print("[dim]Downloading images...[/]", end=" ")
        backdrop_ok, poster_ok = asyncio.run(
            downloader.download_cover_and_poster(
                metadata.cover_url,
                backdrop_path,
                poster_path,
            )
        )

        if backdrop_ok:
            console.print("[green]backdrop OK[/]", end=" ")
        if poster_ok:
            console.print("[green]poster OK[/]")
        else:
            console.print()

    # Process thumbnails and translation
    if not nfo_only:
        process_thumbnails(metadata, settings)
        translate_metadata_if_enabled(metadata, settings)

    # Update NFO
    nfo_content = generate_nfo(
        metadata,
        poster_filename=sort_settings.poster_filename,
        backdrop_filename=sort_settings.backdrop_filename,
        use_japanese_names=sort_settings.actress_language_ja,
    )
    nfo_path.write_text(nfo_content, encoding="utf-8")
    console.print(f"[green]NFO updated:[/] {nfo_path.name}")
    console.print(f"[bold green]Done![/] Updated: {folder_path.name}")
    return True


@click.command("update")
@click.argument("folder", type=click.Path(exists=True))
@click.option("--source", "-s", default="r18dev,dmm_new", help="Scraper sources")
@click.option("--proxy", "-p", help="Proxy URL")
@click.option("--dry-run", is_flag=True, help="Preview without changes")
@click.option("--nfo-only", is_flag=True, help="Only update NFO, skip images")
def update(
    folder: str,
    source: str,
    proxy: Optional[str],
    dry_run: bool,
    nfo_only: bool,
) -> None:
    """Update metadata for an already sorted folder.

    Re-scrapes metadata and refreshes NFO and images in-place.

    Example:
        javinizer update "D:/Movies/SDDE-761"
        javinizer update "D:/Movies/SDDE-761" --nfo-only
    """
    folder_path = Path(folder).resolve()
    settings = load_settings()
    proxy_config = None
    if proxy:
        proxy_config = ProxyConfig(enabled=True, url=proxy)
    elif settings.proxy.enabled:
        proxy_config = settings.proxy

    update_folder_task(folder_path, source, proxy_config, settings, dry_run, nfo_only)


@click.command("update-dir")
@click.argument("input_dir", type=click.Path(exists=True))
@click.option("--source", "-s", default="r18dev,dmm_new", help="Scraper sources")
@click.option("--proxy", "-p", help="Proxy URL")
@click.option(
    "--recursive", "-r", is_flag=True, help="Search subdirectories recursively"
)
@click.option("--dry-run", is_flag=True, help="Preview without changes")
@click.option("--nfo-only", is_flag=True, help="Only update NFO, skip images")
def update_dir(
    input_dir: str,
    source: str,
    proxy: Optional[str],
    recursive: bool,
    dry_run: bool,
    nfo_only: bool,
) -> None:
    """Update metadata for all sorted folders in a directory.

    Scans for folders containing .nfo files and re-scrapes metadata.

    Example:
        javinizer update-dir "D:/Movies" --recursive
    """
    input_path = Path(input_dir).resolve()
    console.print(f"[bold]Scanning for sorted folders in:[/] {input_path}")

    # Find folders with NFO files
    if recursive:
        nfo_files = list(input_path.rglob("*.nfo"))
    else:
        nfo_files = list(input_path.glob("*/*.nfo"))

    # Get unique parent folders
    folders = list(set(nfo.parent for nfo in nfo_files))
    folders.sort()

    if not folders:
        console.print("[yellow]No sorted folders found (no .nfo files)[/]")
        return

    console.print(f"[cyan]Found {len(folders)} folder(s) to update[/]")
    console.print()

    success_count = 0
    error_count = 0

    # Load settings once
    settings = load_settings()
    proxy_config = None
    if proxy:
        proxy_config = ProxyConfig(enabled=True, url=proxy)
    elif settings.proxy.enabled:
        proxy_config = settings.proxy

    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Parallel processing with ThreadPoolExecutor
    # Use max 4 workers to avoid rate limits
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(
                update_folder_task,
                folder,
                source,
                proxy_config,
                settings,
                dry_run,
                nfo_only,
            ): folder
            for folder in folders
        }

        for future in as_completed(futures):
            folder_arg = futures[future]
            try:
                success = future.result()
                if success:
                    success_count += 1
                else:
                    error_count += 1  # Logic failure (no ID, no results) counted as error or skip?
                    # The update_folder_task returns False on known failures, we can adjust counters
            except Exception as e:
                console.print(f"[red]Error updating {folder_arg.name}: {e}[/]")
                error_count += 1

    console.print()
    console.print("[bold]Summary:[/]")
    console.print(f"  Updated: {success_count}")

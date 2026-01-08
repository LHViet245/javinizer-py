"""Sort commands module"""

import asyncio
from typing import Optional
from pathlib import Path

import click

from javinizer.cli_common import console, expand_sources, get_scraper
from javinizer.models import ProxyConfig
from javinizer.config import load_settings
from javinizer.matcher import extract_movie_id, find_video_files
from javinizer.sorter import SortConfig, generate_sort_paths, execute_sort
from javinizer.downloader import ImageDownloader
from javinizer.nfo import generate_nfo
from javinizer.cli_helpers import process_thumbnails, translate_metadata_if_enabled


@click.command("sort")
@click.argument("video_file", type=click.Path(exists=True))
@click.option("--dest", "-d", type=click.Path(), help="Destination folder (default: same as video)")
@click.option("--source", "-s", default="r18dev,dmm_new", help="Scraper sources (comma-separated)")
@click.option("--proxy", "-p", help="Proxy URL (overrides config)")
@click.option("--dry-run", is_flag=True, help="Preview without making changes")
@click.option("--copy", is_flag=True, help="Copy files instead of moving")
def sort(video_file: str, dest: Optional[str], source: str, proxy: Optional[str], dry_run: bool, copy: bool):
    """Sort a single video file with metadata.

    This command will:
    1. Extract movie ID from filename
    2. Fetch metadata from scrapers
    3. Create folder structure, download images, generate NFO
    4. Move/copy video and subtitle files

    If --dest is not provided, sorts in-place (same folder as video).

    Examples:
        javinizer sort "D:/Videos/IPX-486.mp4" --dest "D:/Movies"
        javinizer sort "D:/Videos/IPX-486.mp4"  # In-place sorting
    """
    video_path = Path(video_file)

    # Default to in-place sorting (same folder as video)
    if dest:
        dest_path = Path(dest)
    else:
        dest_path = video_path.parent
        console.print(f"[dim]No --dest provided, sorting in-place[/]")

    # Extract movie ID
    movie_id = extract_movie_id(video_path.name)
    if not movie_id:
        console.print(f"[red]Could not extract movie ID from: {video_path.name}[/]")
        console.print("[dim]Expected format: ABC-123, SSNI-486, etc.[/]")
        return

    console.print(f"[cyan]Movie ID:[/] {movie_id}")

    # Load settings
    settings = load_settings()

    # Setup proxy
    proxy_config = None
    if proxy:
        proxy_config = ProxyConfig(enabled=True, url=proxy)
    elif settings.proxy.enabled:
        proxy_config = settings.proxy

    # Fetch metadata - expand aliases (dmm -> [dmm_new, dmm])
    sources = expand_sources([s.strip() for s in source.split(",")])
    results = {}

    for src in sources:
        scraper = get_scraper(
            src,
            proxy=proxy_config,
            cookies=settings.javlibrary_cookies if src in ("javlibrary", "jav") else None,
            user_agent=settings.javlibrary_user_agent if src in ("javlibrary", "jav") else None,
        )

        if scraper is None:
            continue

        with scraper:
            try:
                console.print(f"[dim]Scraping from {src}...[/]", end=" ")
                metadata = scraper.find(movie_id)
                if metadata:
                    results[src] = metadata
                    console.print("[green]OK[/]")
                    # aggregate mode: continue to next source
                else:
                    console.print("[yellow]no results[/]")
            except Exception as e:
                console.print(f"[red]error: {e}[/]")

    if not results:
        console.print(f"[red]Could not find metadata for {movie_id}[/]")
        return

    # Aggregate results if multiple sources found
    if len(results) > 1:
        from javinizer.aggregator import aggregate_metadata
        metadata = aggregate_metadata(results, settings.priority)
        console.print(f"[green]📦 Aggregated from {len(results)} sources[/]")
    else:
        # Use first available result
        metadata = list(results.values())[0]

    console.print(f"[green]Found:[/] {metadata.title}")

    # Setup sort config from settings
    sort_settings = settings.sort
    config = SortConfig(
        folder_format=sort_settings.folder_format,
        file_format=sort_settings.file_format,
        nfo_format=sort_settings.nfo_format,
        poster_filename=sort_settings.poster_filename,
        backdrop_filename=sort_settings.backdrop_filename,
        max_title_length=sort_settings.max_title_length,
        move_to_folder=True,
        rename_file=True,
        create_nfo=sort_settings.create_nfo,
        download_images=sort_settings.download_images,
        move_subtitles=sort_settings.move_subtitles,
    )

    # Generate paths
    paths = generate_sort_paths(video_path, dest_path, metadata, config)

    # Preview
    console.print()
    console.print("[bold]Output structure:[/]")
    console.print(f"  Folder:   {paths.folder_path}")
    console.print(f"  Video:    {paths.video_path.name}")
    if paths.nfo_path:
        console.print(f"  NFO:      {paths.nfo_path.name}")
    if paths.poster_path:
        console.print(f"  Poster:   {paths.poster_path.name}")
    if paths.backdrop_path:
        console.print(f"  Backdrop: {paths.backdrop_path.name}")
    for sub in paths.subtitle_paths:
        console.print(f"  Subtitle: {sub.name}")

    if dry_run:
        console.print()
        console.print("[yellow]DRY RUN - No changes made[/]")
        return

    console.print()

    # Execute sorting
    move = not copy
    success = execute_sort(paths, move=move, dry_run=False)

    if not success:
        console.print("[red]Error during file sorting[/]")
        return

    console.print(f"[green]{'Moved' if move else 'Copied'} video file[/]")

    # Download images
    if config.download_images and metadata.cover_url:
        downloader = ImageDownloader(
            proxy=proxy_config.httpx_proxy if proxy_config else None,
            timeout=settings.timeout,
        )

        console.print("[dim]Downloading images...[/]", end=" ")
        
        # Helper wrapper for coroutine
        async def run_download():
             return await downloader.download_cover_and_poster(
                metadata.cover_url,
                paths.backdrop_path,
                paths.poster_path,
            )

        backdrop_ok, poster_ok = asyncio.run(run_download())

        if backdrop_ok:
            console.print("[green]backdrop OK[/]", end=" ")
        if poster_ok:
            console.print("[green]poster OK[/]")
        else:
            console.print()

    # Process thumbnails and translation
    process_thumbnails(metadata, settings)
    translate_metadata_if_enabled(metadata, settings)

    # Generate NFO
    if config.create_nfo and paths.nfo_path:
        nfo_content = generate_nfo(
            metadata,
            poster_filename=config.poster_filename,
            backdrop_filename=config.backdrop_filename,
            use_japanese_names=sort_settings.actress_language_ja,
        )
        paths.nfo_path.write_text(nfo_content, encoding="utf-8")
        console.print("[green]NFO created[/]")

    console.print()
    console.print(f"[bold green]Done![/] Sorted to: {paths.folder_path}")


@click.command("sort-dir")
@click.argument("input_dir", type=click.Path(exists=True))
@click.option("--dest", "-d", required=True, type=click.Path(), help="Destination folder")
@click.option("--source", "-s", default="r18dev,dmm_new", help="Scraper sources")
@click.option("--proxy", "-p", help="Proxy URL")
@click.option("--recursive", "-r", is_flag=True, help="Search subdirectories")
@click.option("--dry-run", is_flag=True, help="Preview without changes")
@click.option("--copy", is_flag=True, help="Copy instead of move")
@click.option("--min-size", default=100, help="Minimum file size in MB")
def sort_dir(
    input_dir: str,
    dest: str,
    source: str,
    proxy: Optional[str],
    recursive: bool,
    dry_run: bool,
    copy: bool,
    min_size: int
):
    """Sort all video files in a directory.

    Example:
        javinizer sort-dir "D:/Videos" --dest "D:/Movies" --recursive
    """
    input_path = Path(input_dir)

    # Find video files
    console.print(f"[dim]Scanning {input_path}...[/]")
    videos = find_video_files(input_path, recursive=recursive, min_size_mb=min_size)

    if not videos:
        console.print("[yellow]No video files found[/]")
        return

    console.print(f"[cyan]Found {len(videos)} video files[/]")
    console.print()

    # Process each video
    success_count = 0
    skip_count = 0
    error_count = 0

    for video in videos:
        movie_id = extract_movie_id(video.name)

        if not movie_id:
            console.print(f"[yellow]Skip:[/] {video.name} (no ID found)")
            skip_count += 1
            continue

        console.print(f"[cyan]Processing:[/] {video.name} -> {movie_id}")

        if dry_run:
            console.print(f"  [dim]Would sort to: {dest}/{movie_id}...[/]")
            success_count += 1
        else:
            # Call sort_file programmatically
            try:
                # Use click context to invoke sort command
                ctx = click.Context(sort)
                ctx.invoke(
                    sort,
                    video_file=str(video),
                    dest=dest,
                    source=source,
                    proxy=proxy,
                    dry_run=False,
                    copy=copy,
                )
                success_count += 1
            except Exception as e:
                console.print(f"  [red]Error: {e}[/]")
                error_count += 1

        console.print()

    # Summary
    console.print()
    console.print(f"[bold]Summary:[/]")
    console.print(f"  Processed: {success_count}")
    console.print(f"  Skipped:   {skip_count}")
    console.print(f"  Errors:    {error_count}")

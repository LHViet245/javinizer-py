"""Command Line Interface for Javinizer"""

from pathlib import Path
from typing import Optional
import asyncio
import json

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from javinizer import __version__
from javinizer.models import MovieMetadata, ProxyConfig
from javinizer.scrapers import DMMScraper, R18DevScraper, JavlibraryScraper, DMMNewScraper, is_playwright_available
from javinizer.scrapers.base import BaseScraper
from javinizer.nfo import generate_nfo
from javinizer.config import load_settings, save_settings, update_proxy, get_config_path
from javinizer.aggregator import aggregate_metadata
from javinizer.thumbs import ActressDB


console = Console()

# Mapping of scraper names to classes
SCRAPERS = {
    "dmm": DMMScraper,
    "dmmja": DMMScraper,
    "r18dev": R18DevScraper,
    "r18": R18DevScraper,
    "javlibrary": JavlibraryScraper,
    "jav": JavlibraryScraper,
}

# Add dmm_new if playwright is available
if DMMNewScraper is not None:
    SCRAPERS["dmm_new"] = DMMNewScraper

# Alias expansion: when user specifies "dmm", try dmm_new first then dmm
SCRAPER_ALIASES = {
    "dmm": ["dmm_new", "dmm"] if DMMNewScraper else ["dmm"],
}


def expand_sources(source_list: list[str]) -> list[str]:
    """Expand source aliases to actual scraper names"""
    expanded = []
    for source in source_list:
        source_lower = source.lower()
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
):
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


@click.group()
@click.version_option(version=__version__)
def main():
    """Javinizer - JAV Metadata Scraper (Python Edition)

    A command-line tool to scrape and organize Japanese Adult Video metadata.

    Examples:

        javinizer find IPX-486

        javinizer find IPX-486 --source r18dev,dmm --aggregated

        javinizer find IPX-486 --proxy socks5://127.0.0.1:1080

        javinizer config --proxy socks5://127.0.0.1:1080
    """
    """
    pass


@main.command()
@click.argument("movie_id")
@click.option("--source", "-s", default="r18dev,javlibrary,dmm",
              help="Scraper source(s), comma-separated (dmm, r18dev, javlibrary). Default: all")
@click.option("--proxy", "-p", default=None,
              help="Proxy URL (e.g., socks5://127.0.0.1:1080 or http://proxy:8080)")
@click.option("--nfo", is_flag=True, help="Output NFO XML")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--no-aggregate", is_flag=True,
              help="Don't aggregate results, use first successful source only")
@click.option("--log-file", help="Path to log file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose (debug) logging")
def find(movie_id: str, source: str, proxy: Optional[str], nfo: bool, as_json: bool, no_aggregate: bool, log_file: Optional[str], verbose: bool):
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
    from javinizer.logger import configure_logging, get_logger
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

    for src in sources:
        scraper = get_scraper(
            src,
            proxy=proxy_config,
            cookies=settings.javlibrary_cookies if src in ("javlibrary", "jav") else None,
            user_agent=settings.javlibrary_user_agent if src in ("javlibrary", "jav") else None,
        )

        if scraper is None:
            console.print(f"[yellow]⚠️  Unknown source: {src}[/]")
            logger.warning(f"Unknown scraper source requested: {src}")
            continue

        with scraper:
            try:
                console.print(f"[dim]Scraping from {src}...[/]", end=" ")
                logger.debug(f"Scraping {movie_id} from {src}")
                metadata = scraper.find(movie_id)
                if metadata:
                    results[src] = metadata
                    console.print(f"[green]✓[/]")
                    logger.info(f"Found {movie_id} on {src}")
                else:
                    console.print(f"[yellow]no results[/]")
                    logger.debug(f"No results for {movie_id} on {src}")
            except Exception as e:
                console.print(f"[red]error: {e}[/]")
                logger.error(f"Error scraping {src}: {e}", exc_info=True)

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
        console.print(f"[yellow]⚠️  Could not aggregate metadata[/]")
        return

    # Output based on format
    if nfo:
        _output_nfo(metadata)
    elif as_json:
        _output_json(metadata)
    else:
        _output_table(metadata)


@main.group()
def config():
    """Manage Javinizer configuration"""
    pass


@config.command("show")
def config_show():
    """Show current configuration"""
    settings = load_settings()
    config_path = get_config_path()

    console.print(Panel.fit(
        f"[bold]Configuration[/]\n"
        f"Path: {config_path}\n"
        f"\n"
        f"[cyan]Scrapers:[/]\n"
        f"  DMM: {'✓' if settings.scraper_dmm else '✗'}\n"
        f"  R18Dev: {'✓' if settings.scraper_r18dev else '✗'}\n"
        f"  Javlibrary: {'✓' if settings.scraper_javlibrary else '✗'}\n"
        f"\n"
        f"[cyan]Proxy:[/]\n"
        f"  Enabled: {'✓' if settings.proxy.enabled else '✗'}\n"
        f"  URL: {settings.proxy.url or 'Not set'}\n"
        f"\n"
        f"[cyan]Request Settings:[/]\n"
        f"  Timeout: {settings.timeout}s\n"
        f"  Sleep: {settings.sleep_between_requests}s",
        title="⚙️  Config"
    ))


@config.command("set-proxy")
@click.argument("proxy_url", required=False)
@click.option("--disable", is_flag=True, help="Disable proxy")
def config_set_proxy(proxy_url: Optional[str], disable: bool):
    """Set proxy URL

    Examples:

        javinizer config set-proxy socks5://127.0.0.1:1080

        javinizer config set-proxy http://user:pass@proxy:8080

        javinizer config set-proxy --disable
    """
    if disable:
        settings = update_proxy(None)
        console.print("[green]✓ Proxy disabled[/]")
    elif proxy_url:
        settings = update_proxy(proxy_url)
        console.print(f"[green]✓ Proxy set to: {proxy_url}[/]")
    else:
        console.print("[yellow]Please provide a proxy URL or use --disable[/]")


@config.command("set-javlibrary-cookies")
@click.option("--cf-clearance", required=True, help="cf_clearance cookie value (required)")
@click.option("--cf-bm", default=None, help="__cf_bm cookie value (optional, not always present)")
@click.option("--user-agent", required=True, help="User agent used when getting cookies")
def config_set_javlibrary_cookies(cf_clearance: str, cf_bm: Optional[str], user_agent: str):
    """Set Javlibrary Cloudflare cookies for bypass

    You can get these cookies by:
    1. Opening Javlibrary in a browser
    2. Passing the Cloudflare challenge
    3. Open DevTools (F12) -> Application -> Cookies
    4. Copy cf_clearance value
    5. Copy User-Agent from Network tab request headers

    Example:
        javinizer config set-javlibrary-cookies \\
            --cf-clearance "abc123..." \\
            --user-agent "Mozilla/5.0..."
    """
    settings = load_settings()

    cookies = {"cf_clearance": cf_clearance}
    if cf_bm:
        cookies["__cf_bm"] = cf_bm

    settings.javlibrary_cookies = cookies
    settings.javlibrary_user_agent = user_agent
    save_settings(settings)
    console.print("[green]✓ Javlibrary cookies saved[/]")
    console.print(f"  cf_clearance: {cf_clearance[:20]}...")
    if cf_bm:
        console.print(f"  __cf_bm: {cf_bm[:20]}...")
    console.print(f"  User-Agent: {user_agent[:50]}...")


@config.command("get-javlibrary-cookies")
@click.option("--proxy", default=None, help="Proxy URL (e.g., socks5://127.0.0.1:10808)")
@click.option("--timeout", default=120, help="Timeout in seconds to wait for challenge (default: 120)")
def config_get_javlibrary_cookies(proxy: Optional[str], timeout: int):
    """Automatically capture Javlibrary Cloudflare cookies using browser

    This command opens a Chrome window (using undetected-chromedriver),
    navigates to Javlibrary, and waits for you to pass the Cloudflare challenge.
    Once passed, cookies are automatically saved.

    Example:
        javinizer config get-javlibrary-cookies
    """
    try:
        import undetected_chromedriver as uc
        import time
    except ImportError as e:
        console.print(f"[red]✗ undetected-chromedriver import failed: {e}[/]")
        console.print("  Install it with: pip install undetected-chromedriver")
        return

    console.print("[cyan]Opening Chrome to capture Javlibrary cookies...[/]")
    console.print("[yellow]   Please pass the Cloudflare challenge in the browser window.[/]")
    console.print(f"[dim]   Timeout: {timeout} seconds[/]\n")

    driver = None
    try:
        # Chrome options
        options = uc.ChromeOptions()
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')

        # Launch Chrome
        driver = uc.Chrome(options=options)

        # Navigate
        console.print("[cyan]   Navigating to Javlibrary...[/]")
        driver.get("https://www.javlibrary.com/en/")

        start_time = time.time()
        cf_clearance = None
        user_agent = driver.execute_script("return navigator.userAgent;")

        console.print("[yellow]   Waiting for Cloudflare challenge to be solved...[/]")

        while time.time() - start_time < timeout:
            cookies = driver.get_cookies()
            for cookie in cookies:
                if cookie["name"] == "cf_clearance":
                    cf_clearance = cookie["value"]
                    break

            if cf_clearance:
                # Wait a bit more to ensure page is fully loaded and cookie is stable
                time.sleep(2)
                break

            # Check if page is loaded correctly (title check)
            try:
                if "JAVLibrary" in driver.title and "challenge" not in driver.page_source.lower():
                    # Double check cookies
                    cookies = driver.get_cookies()
                    for cookie in cookies:
                        if cookie["name"] == "cf_clearance":
                            cf_clearance = cookie["value"]
                            break
                    if cf_clearance:
                        break
            except:
                pass

            time.sleep(1)

        if cf_clearance:
            # Save to config
            settings = load_settings()
            settings.javlibrary_cookies = {"cf_clearance": cf_clearance}
            settings.javlibrary_user_agent = user_agent
            save_settings(settings)

            console.print("\n[green]Cookies captured and saved successfully![/]")
            console.print(f"  cf_clearance: {cf_clearance[:30]}...")
            console.print(f"  User-Agent: {user_agent[:60]}...")
        else:
            console.print(f"\n[red]Timeout: Could not capture cookies within {timeout} seconds.[/]")
            console.print("  Please try again.")

    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


@main.command()
def info():
    """Show Javinizer information"""
    console.print(Panel.fit(
        f"[bold]Javinizer Python Edition[/]\n"
        f"Version: {__version__}\n"
        f"\n"
        f"[dim]A Python port of the PowerShell Javinizer module[/]\n"
        f"[dim]for scraping and organizing JAV metadata.[/]",
        title="ℹ️  Info"
    ))

    console.print()
    console.print("[bold]Available Scrapers:[/]")
    console.print("  • [cyan]r18dev[/] - R18.dev JSON API (recommended)")
    console.print("  • [cyan]dmm[/] - DMM/Fanza old site (Japanese)")

    # Check if dmm_new is available
    if is_playwright_available():
        console.print("  • [cyan]dmm_new[/] - DMM/Fanza new site (requires Playwright) [green]✓[/]")
    else:
        console.print("  • [dim]dmm_new[/] - DMM/Fanza new site [yellow](install: pip install javinizer[browser])[/]")

    console.print("  • [cyan]javlibrary[/] - Javlibrary (requires Cloudflare cookies)")
    console.print()
    console.print("[bold]Quick Start:[/]")
    console.print("  javinizer find IPX-486")
    console.print("  javinizer find IPX-486 --source r18dev,dmm --aggregated")
    console.print("  javinizer find IPX-486 --proxy socks5://127.0.0.1:1080")
    console.print()
    console.print("[bold]Config Commands:[/]")
    console.print("  javinizer config show")
    console.print("  javinizer config set-proxy socks5://127.0.0.1:1080")


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
        table.add_row("Rating", f"⭐ {metadata.rating.rating}/10 ({metadata.rating.votes} votes)")

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


# ==============================================================================
# SORT COMMANDS
# ==============================================================================

@main.command("sort")
@click.argument("video_file", type=click.Path(exists=True))
@click.option("--dest", "-d", type=click.Path(), help="Destination folder (default: same as video)")
@click.option("--source", "-s", default="r18dev,dmm_new", help="Scraper sources (comma-separated)")
@click.option("--proxy", "-p", help="Proxy URL (overrides config)")
@click.option("--dry-run", is_flag=True, help="Preview without making changes")
@click.option("--copy", is_flag=True, help="Copy files instead of moving")
def sort_file(video_file: str, dest: Optional[str], source: str, proxy: Optional[str], dry_run: bool, copy: bool):
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
    import asyncio
    from pathlib import Path

    from javinizer.matcher import extract_movie_id, find_subtitle_files
    from javinizer.sorter import SortConfig, generate_sort_paths, execute_sort, preview_sort, process_sort
    from javinizer.downloader import ImageDownloader
    from javinizer.nfo import generate_nfo

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
        backdrop_ok, poster_ok = asyncio.run(
            downloader.download_cover_and_poster(
                metadata.cover_url,
                paths.backdrop_path,
                paths.poster_path,
            )
        )

        if backdrop_ok:
            console.print("[green]backdrop OK[/]", end=" ")
        if poster_ok:
            console.print("[green]poster OK[/]")
        else:
            console.print()

    # Process thumbnails and translation using helper functions
    from javinizer.cli_helpers import process_thumbnails, translate_metadata_if_enabled
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


@main.command("sort-dir")
@click.argument("input_dir", type=click.Path(exists=True))
@click.option("--dest", "-d", required=True, type=click.Path(), help="Destination folder")
@click.option("--source", "-s", default="r18dev,dmm_new", help="Scraper sources")
@click.option("--proxy", "-p", help="Proxy URL")
@click.option("--recursive", "-r", is_flag=True, help="Search subdirectories")
@click.option("--dry-run", is_flag=True, help="Preview without changes")
@click.option("--copy", is_flag=True, help="Copy instead of move")
@click.option("--min-size", default=100, help="Minimum file size in MB")
def sort_directory(
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
    from pathlib import Path
    from javinizer.matcher import find_video_files, extract_movie_id

    input_path = Path(input_dir)

    # Find video files
    console.print(f"[dim]Scanning {input_path}...[/]")
    videos = find_video_files(input_path, recursive=recursive, min_size_mb=min_size)

    if not videos:
        console.print("[yellow]No video files found[/]")
        return

    console.print(f"[cyan]Found {len(videos)} video files[/]")
    console.print()

    # Expand sources
    sources = expand_sources([s.strip() for s in source.split(",")])

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
                ctx = click.Context(sort_file)
                ctx.invoke(
                    sort_file,
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


# ==============================================================================
# UPDATE COMMANDS
# ==============================================================================


@main.command("update")
@click.argument("folder", type=click.Path(exists=True))
@click.option("--source", "-s", default="r18dev,dmm_new", help="Scraper sources")
@click.option("--proxy", "-p", help="Proxy URL")
@click.option("--dry-run", is_flag=True, help="Preview without changes")
@click.option("--nfo-only", is_flag=True, help="Only update NFO, skip images")
def update_folder(
    folder: str,
    source: str,
    proxy: Optional[str],
    dry_run: bool,
    nfo_only: bool,
):
    """Update metadata for an already sorted folder.

    Re-scrapes metadata and refreshes NFO and images in-place.

    Example:
        javinizer update "D:/Movies/SDDE-761"
        javinizer update "D:/Movies/SDDE-761" --nfo-only
    """
    from javinizer.matcher import extract_movie_id
    from javinizer.downloader import ImageDownloader
    from javinizer.nfo import generate_nfo

    folder_path = Path(folder).resolve()

    if not folder_path.is_dir():
        console.print(f"[red]Not a folder: {folder_path}[/]")
        return

    console.print(f"[bold cyan]Updating:[/] {folder_path.name}")

    # Extract movie ID from folder name
    movie_id = extract_movie_id(folder_path.name)
    if not movie_id:
        console.print(f"[red]Could not extract movie ID from folder name: {folder_path.name}[/]")
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
        metadata = list(results.values())[0]

    console.print(f"[green]Found:[/] {metadata.title}")

    if dry_run:
        console.print()
        console.print("[yellow]DRY RUN - No changes made[/]")
        return

    # Get sort settings for filenames
    sort_settings = settings.sort

    # Determine file paths in folder
    nfo_path = folder_path / f"{sort_settings.nfo_format.replace('<ID>', movie_id)}.nfo"
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

    # Process thumbnails and translation using helper functions
    if not nfo_only:
        from javinizer.cli_helpers import process_thumbnails, translate_metadata_if_enabled
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

    console.print()
    console.print(f"[bold green]Done![/] Updated: {folder_path.name}")


@main.command("update-dir")
@click.argument("input_dir", type=click.Path(exists=True))
@click.option("--source", "-s", default="r18dev,dmm_new", help="Scraper sources")
@click.option("--proxy", "-p", help="Proxy URL")
@click.option("--recursive", "-r", is_flag=True, help="Search subdirectories recursively")
@click.option("--dry-run", is_flag=True, help="Preview without changes")
@click.option("--nfo-only", is_flag=True, help="Only update NFO, skip images")
def update_directory(
    input_dir: str,
    source: str,
    proxy: Optional[str],
    recursive: bool,
    dry_run: bool,
    nfo_only: bool,
):
    """Update metadata for all sorted folders in a directory.

    Scans for folders containing .nfo files and re-scrapes metadata.

    Example:
        javinizer update-dir "D:/Movies" --recursive
    """
    from javinizer.matcher import extract_movie_id

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
    skip_count = 0
    error_count = 0

    for folder in folders:
        # Check if we can extract movie ID
        movie_id = extract_movie_id(folder.name)
        if not movie_id:
            console.print(f"[yellow]Skipping:[/] {folder.name} (no movie ID)")
            skip_count += 1
            continue

        try:
            # Call update_folder via context
            ctx = click.Context(update_folder)
            ctx.invoke(
                update_folder,
                folder=str(folder),
                source=source,
                proxy=proxy,
                dry_run=dry_run,
                nfo_only=nfo_only,
            )
            success_count += 1
        except Exception as e:
            console.print(f"[red]Error updating {folder.name}: {e}[/]")
            error_count += 1

    console.print()
    console.print(f"[bold]Summary:[/]")
    console.print(f"  Updated: {success_count}")


@config.command("set-sort-format")
@click.option("--folder", help="Folder format template")
@click.option("--file", "file_fmt", help="File format template")
@click.option("--nfo", "nfo_fmt", help="NFO filename format template (default: <ID>)")
def config_set_sort_format(folder: Optional[str], file_fmt: Optional[str], nfo_fmt: Optional[str]):
    """Set sorting format templates.

    Placeholders: <ID>, <TITLE>, <STUDIO>, <YEAR>, <ACTORS>, <LABEL>

    Examples:
        javinizer config set-sort-format --folder "<TITLE> (<YEAR>) [<ID>]"
        javinizer config set-sort-format --file "<ID>"
        javinizer config set-sort-format --nfo "<ID>"
    """
    settings = load_settings()

    if folder:
        settings.sort.folder_format = folder
        console.print(f"[green]Folder format set to:[/] {folder}")

    if file_fmt:
        settings.sort.file_format = file_fmt
        console.print(f"[green]File format set to:[/] {file_fmt}")

    if nfo_fmt:
        settings.sort.nfo_format = nfo_fmt
        console.print(f"[green]NFO format set to:[/] {nfo_fmt}")

    if folder or file_fmt or nfo_fmt:
        save_settings(settings)
    else:
        console.print(f"Current folder format: {settings.sort.folder_format}")
        console.print(f"Current file format: {settings.sort.file_format}")
        console.print(f"Current NFO format: {settings.sort.nfo_format}")


@main.group()
def thumbs():
    """Manage Thumbnail Database"""
    pass


@thumbs.command("list")
@click.option("--filter", "-f", help="Filter by name")
def thumbs_list(filter: Optional[str]):
    """List actresses in database"""
    from javinizer.thumbs import ActressDB

    db = ActressDB()
    profiles = list(db.profiles.values())

    if filter:
        filter = filter.lower()
        profiles = [p for p in profiles if filter in p.name.lower()]

    console.print(f"[cyan]Found {len(profiles)} actresses[/]")

    table = Table(show_header=True)
    table.add_column("Name")
    table.add_column("Aliases")
    table.add_column("Image URL")
    table.add_column("Local Path")

    # Sort by name
    profiles.sort(key=lambda x: x.name)

    for p in profiles[:100]:  # Limit output
        table.add_row(
            p.name,
            ", ".join(p.aliases[:3]),
            "[green]Yes[/]" if p.image_url else "[red]No[/]",
            "[green]Yes[/]" if p.local_path else "[dim]No[/]"
        )

    console.print(table)
    if len(profiles) > 100:
        console.print(f"[dim]... and {len(profiles) - 100} more[/]")


@thumbs.command("update")
@click.option("--force", is_flag=True, help="Re-download existing images")
def thumbs_update(force: bool):
    """Update thumbnail database images (Bulk Download)"""
    from javinizer.thumbs import ActressDB
    import asyncio

    db = ActressDB()
    console.print(f"[cyan]Loaded DB with {len(db.profiles)} actresses[/]")

    async def run_update():
        tasks = []
        sem = asyncio.Semaphore(5)  # Limit concurrency

        async def process(profile):
            async with sem:
                if force and profile.local_path:
                    # TODO: Implement force logic cleanly
                    pass
                await db.get_local_path(profile)

        with console.status("[bold green]Updating thumbnails...[/]"):
            await asyncio.gather(*[process(p) for p in db.profiles.values() if p.image_url])

    asyncio.run(run_update())
    console.print("[green]Update complete![/]")


if __name__ == "__main__":
    main()

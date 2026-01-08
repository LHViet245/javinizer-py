"""Config commands module"""

from typing import Optional

import click
from rich.panel import Panel

from javinizer.cli_common import console
from javinizer.config import load_settings, save_settings, update_proxy, get_config_path


@click.group()
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

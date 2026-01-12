"""Info command module"""

import click
from rich.panel import Panel

from javinizer import __version__
from javinizer.cli_common import console
from javinizer.scrapers import is_playwright_available


@click.command()
def info():
    """Show Javinizer information"""
    console.print(
        Panel.fit(
            f"[bold]Javinizer Python Edition[/]\n"
            f"Version: {__version__}\n"
            f"\n"
            f"[dim]A Python port of the PowerShell Javinizer module[/]\n"
            f"[dim]for scraping and organizing JAV metadata.[/]",
            title="ℹ️  Info",
        )
    )

    console.print()
    console.print("[bold]Available Scrapers:[/]")
    console.print("  • [cyan]r18dev[/] - R18.dev JSON API (recommended)")
    console.print("  • [cyan]dmm[/] - DMM/Fanza old site (Japanese)")

    # Check if dmm_new is available
    if is_playwright_available():
        console.print(
            "  • [cyan]dmm_new[/] - DMM/Fanza new site (requires Playwright) [green]✓[/]"
        )
    else:
        console.print(
            "  • [dim]dmm_new[/] - DMM/Fanza new site [yellow](install: pip install javinizer[browser])[/]"
        )

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

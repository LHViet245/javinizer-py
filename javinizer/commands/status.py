# File: javinizer/commands/status.py
"""Status command for checking system health"""

import click
from rich.console import Console
from rich.table import Table

from javinizer.health import get_system_status


console = Console()


@click.command()
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def status(output_json: bool) -> None:
    """Check status of scrapers and system components.

    Shows health status of all configured scrapers and the cache system.

    Examples:

        javinizer status

        javinizer status --json
    """
    console.print("[bold]Checking system status...[/bold]\n")

    system_status = get_system_status()

    if output_json:
        import json

        console.print_json(json.dumps(system_status, indent=2))
        return

    # Display scraper status
    table = Table(title="Scraper Status")
    table.add_column("Scraper", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Latency", justify="right")
    table.add_column("Message")

    for result in system_status["scrapers"]["results"]:
        status_style = "green" if result["status"] == "ok" else "red"
        latency = f"{result['latency_ms']:.0f}ms" if result["latency_ms"] else "-"

        table.add_row(
            result["name"],
            f"[{status_style}]{result['status'].upper()}[/{status_style}]",
            latency,
            result["message"] or "",
        )

    console.print(table)
    console.print()

    # Display cache status
    cache = system_status["cache"]
    cache_style = "green" if cache["status"] == "ok" else "red"
    console.print(
        f"[bold]Cache:[/bold] [{cache_style}]{cache['status'].upper()}[/{cache_style}] - {cache['message']}"
    )

    if cache.get("details"):
        details = cache["details"]
        if details.get("enabled"):
            console.print(f"  Entries: {details.get('total_entries', 0)}")
            console.print(f"  Hits: {details.get('total_hits', 0)}")
            console.print(f"  TTL: {details.get('ttl_days', 0)} days")

    console.print()

    # Overall status
    overall = system_status["overall_status"]
    overall_style = "green" if overall == "ok" else "yellow"
    healthy = system_status["scrapers"]["healthy"]
    total = system_status["scrapers"]["total"]

    console.print(
        f"[bold]Overall:[/bold] [{overall_style}]{overall.upper()}[/{overall_style}] ({healthy}/{total} scrapers healthy)"
    )

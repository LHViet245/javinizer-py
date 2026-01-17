"""Thumbnail commands module"""

import click
from rich.table import Table

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from javinizer.thumbs import ActressProfile

from javinizer.cli_common import console


@click.group()
def thumbs() -> None:
    """Manage Thumbnail Database"""
    pass


@thumbs.command("list")
@click.option("--filter", "-f", help="Filter by name")
def thumbs_list(filter: Optional[str]) -> None:
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
            "[green]Yes[/]" if p.local_path else "[dim]No[/]",
        )

    console.print(table)
    if len(profiles) > 100:
        console.print(f"[dim]... and {len(profiles) - 100} more[/]")


@thumbs.command("update")
@click.option("--force", is_flag=True, help="Re-download existing images")
def thumbs_update(force: bool) -> None:
    """Update thumbnail database images (Bulk Download)"""
    from javinizer.thumbs import ActressDB
    import asyncio

    db = ActressDB()
    console.print(f"[cyan]Loaded DB with {len(db.profiles)} actresses[/]")

    async def run_update() -> None:
        # tasks = []
        sem = asyncio.Semaphore(5)  # Limit concurrency

        async def process(profile: "ActressProfile") -> None:
            async with sem:
                if force and profile.local_path:
                    # TODO: Implement force logic cleanly
                    pass
                await db.get_local_path(profile)

        with console.status("[bold green]Updating thumbnails...[/]"):
            await asyncio.gather(
                *[process(p) for p in db.profiles.values() if p.image_url]
            )

    asyncio.run(run_update())
    console.print("[green]Update complete![/]")

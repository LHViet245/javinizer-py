"""Helper functions for CLI commands to reduce code duplication"""

import asyncio

from rich.console import Console

from javinizer.models import MovieMetadata, Settings
from javinizer.thumbs import ActressDB


console = Console()


def process_thumbnails(metadata: MovieMetadata, settings: Settings) -> None:
    """
    Process thumbnail database for actresses in metadata.
    Downloads thumbnails if enabled and adds to local database.
    """
    if not settings.thumbs.enabled:
        return

    console.print("[dim]Processing thumbnails...[/]", end=" ")
    try:
        db = ActressDB()
        asyncio.run(db.process_metadata(metadata))
        console.print("[green]OK[/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")


def translate_metadata_if_enabled(metadata: MovieMetadata, settings: Settings) -> None:
    """
    Translate metadata title and description if translation is enabled.
    Preserves original title in original_title field.
    """
    if not settings.translation.enabled:
        return

    console.print("[dim]Translating...[/]", end=" ")
    try:
        from javinizer.translator import Translator, translate_metadata

        translator = Translator(
            provider=settings.translation.provider,
            target_language=settings.translation.target_language,
            deepl_api_key=settings.translation.deepl_api_key,
            timeout=settings.timeout,
        )
        translate_metadata(
            metadata,
            translator,
            translate_title=settings.translation.translate_title,
            translate_description=settings.translation.translate_description,
        )
        console.print("[green]OK[/]")
    except Exception as e:
        console.print(f"[yellow]Translation failed: {e}[/]")

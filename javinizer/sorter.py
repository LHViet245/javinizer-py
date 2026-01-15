"""File sorting and organization for JAV videos (Jellyfin optimized)"""

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any

from rich.console import Console

from .matcher import find_subtitle_files, get_subtitle_language
from .models import MovieMetadata

# Invalid characters for Windows filenames
INVALID_FILENAME_CHARS = r'\/:*?"<>|'


@dataclass
class SortConfig:
    """Configuration for file sorting"""

    # Format templates
    folder_format: str = "<TITLE> (<YEAR>) [<ID>]"
    file_format: str = "<TITLE> (<YEAR>) [<ID>]"
    nfo_format: str = "<TITLE> (<YEAR>) [<ID>]"

    # Multi-level output folder (e.g., ["<ACTORS>", "<YEAR>"])
    # Creates nested structure: dest/<ACTORS>/<YEAR>/<folder_format>/
    output_folder: list[str] = field(default_factory=list)

    # Image filenames (Jellyfin standard)
    poster_filename: str = "cover.jpg"
    backdrop_filename: str = "backdrop.jpg"

    # Options
    max_title_length: int = 80
    move_to_folder: bool = True
    rename_file: bool = True
    create_nfo: bool = True
    download_images: bool = True
    move_subtitles: bool = True

    # Actress format
    actress_delimiter: str = ", "
    actress_language_ja: bool = False
    first_name_order: bool = True  # Western order (First Last)
    group_actress: bool = True  # Use @Group for multiple actresses


@dataclass
class SortPaths:
    """Generated paths for sorted movie files"""

    folder_path: Path
    video_path: Path
    nfo_path: Optional[Path] = None
    poster_path: Optional[Path] = None
    backdrop_path: Optional[Path] = None
    subtitle_paths: list[Path] = field(default_factory=list)

    # Original paths for reference
    original_video: Optional[Path] = None
    original_subtitles: list[Path] = field(default_factory=list)


def sanitize_filename(name: str) -> str:
    """
    Remove invalid characters from filename.

    Args:
        name: Raw filename string

    Returns:
        Sanitized filename safe for Windows
    """
    # Replace invalid characters
    for char in INVALID_FILENAME_CHARS:
        if char == "/" or char == ":":
            name = name.replace(char, "-")
        else:
            name = name.replace(char, "")

    # Remove leading/trailing dots and spaces
    name = name.strip(". ")

    # Collapse multiple spaces
    name = re.sub(r"\s+", " ", name)

    return name


def truncate_title(title: str, max_length: int) -> str:
    """
    Truncate title intelligently, preserving whole words.

    Args:
        title: Original title
        max_length: Maximum length

    Returns:
        Truncated title with ellipsis if needed
    """
    if len(title) <= max_length:
        return title

    short = title[:max_length]

    # Check if title contains Japanese/Chinese characters
    if re.search(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]", short):
        return short + "..."

    # For Western text, try to preserve whole words
    words = short.rsplit(" ", 1)
    if len(words) > 1:
        result = words[0].rstrip(".,!?;:")
        return result + "..."

    return short + "..."


def format_actresses(
    metadata: MovieMetadata,
    delimiter: str = ", ",
    japanese: bool = False,
    first_name_order: bool = True,
    group_if_multiple: bool = True,
) -> str:
    """
    Format actress names as string.

    Args:
        metadata: Movie metadata
        delimiter: Separator between names
        japanese: Use Japanese names if available
        first_name_order: Western order (First Last) vs Japanese (Last First)
        group_if_multiple: Return "@Group" if multiple actresses

    Returns:
        Formatted actress string
    """
    if not metadata.actresses:
        return "@Unknown"

    names = []
    for actress in metadata.actresses:
        if japanese and actress.japanese_name:
            names.append(actress.japanese_name)
        elif first_name_order:
            names.append(actress.full_name)
        else:
            names.append(actress.full_name_japanese_order)

    if group_if_multiple and len(names) > 1:
        return "@Group"

    return delimiter.join(sorted(names))


def format_template(template: str, metadata: MovieMetadata, config: SortConfig) -> str:
    """
    Replace placeholders in template string with metadata values.

    Args:
        template: Template with placeholders like <ID>, <TITLE>
        metadata: Movie metadata
        config: Sort configuration

    Returns:
        Formatted string with placeholders replaced
    """
    # Prepare values
    title = metadata.title or "Unknown"
    if config.max_title_length > 0:
        title = truncate_title(title, config.max_title_length)

    year = str(metadata.year) if metadata.year else "Unknown"

    actresses = format_actresses(
        metadata,
        delimiter=config.actress_delimiter,
        japanese=config.actress_language_ja,
        first_name_order=config.first_name_order,
        group_if_multiple=config.group_actress,
    )

    # Replace placeholders
    result = template
    replacements = {
        "<ID>": metadata.id,
        "<TITLE>": title,
        "<ORIGINALTITLE>": metadata.original_title or title,
        "<STUDIO>": metadata.maker or "Unknown",
        "<YEAR>": year,
        "<RELEASEDATE>": str(metadata.release_date)
        if metadata.release_date
        else "Unknown",
        "<RUNTIME>": str(metadata.runtime) if metadata.runtime else "Unknown",
        "<ACTORS>": actresses,
        "<LABEL>": metadata.label or "",
        "<SET>": metadata.series or "",
        "<DIRECTOR>": metadata.director or "",
        "<CONTENTID>": metadata.content_id or metadata.id,
    }

    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)

    # Remove empty brackets and clean up
    result = re.sub(r"\[\s*\]", "", result)
    result = re.sub(r"\(\s*\)", "", result)
    result = re.sub(r"\s+", " ", result)
    result = result.strip()

    # Sanitize for filesystem
    result = sanitize_filename(result)

    return result


def generate_sort_paths(
    source_video: Path, dest_folder: Path, metadata: MovieMetadata, config: SortConfig
) -> SortPaths:
    """
    Generate all paths for sorted movie files.

    Args:
        source_video: Original video file path
        dest_folder: Destination root folder
        metadata: Movie metadata
        config: Sort configuration

    Returns:
        SortPaths with all generated paths
    """
    # Format names
    folder_name = format_template(config.folder_format, metadata, config)
    file_name = format_template(config.file_format, metadata, config)
    nfo_name = format_template(config.nfo_format, metadata, config)

    # Build path with optional nested output_folder structure
    # e.g., ["<ACTORS>", "<YEAR>"] -> dest/<ACTORS>/<YEAR>/<folder_format>/
    base_folder = dest_folder
    if config.output_folder:
        for level_template in config.output_folder:
            level_name = format_template(level_template, metadata, config)
            # Skip empty levels
            if level_name and level_name.strip():
                base_folder = base_folder / level_name

    movie_folder = base_folder / folder_name
    video_path = movie_folder / f"{file_name}{source_video.suffix}"

    paths = SortPaths(
        folder_path=movie_folder,
        video_path=video_path,
        original_video=source_video,
    )

    # NFO path
    if config.create_nfo:
        paths.nfo_path = movie_folder / f"{nfo_name}.nfo"

    # Image paths
    if config.download_images:
        paths.poster_path = movie_folder / config.poster_filename
        paths.backdrop_path = movie_folder / config.backdrop_filename

    # Find and map subtitle files
    if config.move_subtitles:
        original_subs = find_subtitle_files(source_video)
        paths.original_subtitles = original_subs

        for sub in original_subs:
            lang = get_subtitle_language(sub)
            if lang:
                new_sub = movie_folder / f"{file_name}.{lang}{sub.suffix}"
            else:
                new_sub = movie_folder / f"{file_name}{sub.suffix}"
            paths.subtitle_paths.append(new_sub)

    return paths


def execute_sort(paths: SortPaths, move: bool = True, dry_run: bool = False) -> bool:
    """
    Execute the file sorting operations.

    Args:
        paths: Generated sort paths
        move: Move files (True) or copy (False)
        dry_run: If True, don't actually perform operations

    Returns:
        True if successful, False otherwise
    """
    if dry_run:
        console = Console()
        console.print(f"[yellow][DRY RUN][/] Would create folder: {paths.folder_path}")
        console.print(
            f"[yellow][DRY RUN][/] Would {'move' if move else 'copy'} video to: {paths.video_path}"
        )
        if paths.nfo_path:
            console.print(f"[yellow][DRY RUN][/] Would create NFO: {paths.nfo_path}")
        if paths.poster_path:
            console.print(
                f"[yellow][DRY RUN][/] Would download poster: {paths.poster_path}"
            )
        if paths.backdrop_path:
            console.print(
                f"[yellow][DRY RUN][/] Would download backdrop: {paths.backdrop_path}"
            )
        for sub in paths.subtitle_paths:
            console.print(
                f"[yellow][DRY RUN][/] Would {'move' if move else 'copy'} subtitle to: {sub}"
            )
        return True

    try:
        # Create folder
        paths.folder_path.mkdir(parents=True, exist_ok=True)

        # Move/copy video
        if paths.original_video and paths.original_video.exists():
            if move:
                shutil.move(str(paths.original_video), str(paths.video_path))
            else:
                shutil.copy2(str(paths.original_video), str(paths.video_path))

        # Move/copy subtitles
        for orig_sub, new_sub in zip(paths.original_subtitles, paths.subtitle_paths):
            if orig_sub.exists():
                if move:
                    shutil.move(str(orig_sub), str(new_sub))
                else:
                    shutil.copy2(str(orig_sub), str(new_sub))

        return True

    except Exception as e:
        console = Console()
        console.print(f"[red]Error during sorting: {e}[/]")
        return False


def preview_sort(
    source_video: Path,
    dest_folder: Path,
    metadata: MovieMetadata,
    config: Optional[SortConfig] = None,
) -> dict[str, Any]:
    """
    Preview what the sort operation will do.

    Args:
        source_video: Original video file
        dest_folder: Destination folder
        metadata: Movie metadata
        config: Sort configuration (uses defaults if None)

    Returns:
        Dictionary with preview information
    """
    if config is None:
        config = SortConfig()

    paths = generate_sort_paths(source_video, dest_folder, metadata, config)

    return {
        "source_video": str(source_video),
        "destination_folder": str(paths.folder_path),
        "video_file": str(paths.video_path),
        "nfo_file": str(paths.nfo_path) if paths.nfo_path else None,
        "poster_file": str(paths.poster_path) if paths.poster_path else None,
        "backdrop_file": str(paths.backdrop_path) if paths.backdrop_path else None,
        "subtitle_files": [str(s) for s in paths.subtitle_paths],
        "original_subtitles": [str(s) for s in paths.original_subtitles],
    }

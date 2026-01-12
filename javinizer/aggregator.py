"""Metadata aggregator for combining results from multiple scrapers"""

from typing import Any, Optional

from javinizer.models import MovieMetadata, Actress, ScraperPriority


def aggregate_metadata(
    results: dict[str, MovieMetadata],
    priority: Optional[ScraperPriority] = None,
) -> Optional[MovieMetadata]:
    """
    Aggregate metadata from multiple scrapers based on priority

    Args:
        results: Dict mapping scraper name to MovieMetadata
        priority: ScraperPriority config for field selection

    Returns:
        Aggregated MovieMetadata or None if no valid results
    """
    if not results:
        return None

    if priority is None:
        priority = ScraperPriority()

    # Get first valid result as base
    base_source = list(results.keys())[0]
    base = results[base_source]

    # Alias expansion: "dmm" matches both "dmm_new" (preferred) and "dmm"
    SCRAPER_ALIASES = {
        "dmm": ["dmm_new", "dmm"],  # dmm_new is preferred over dmm
        "r18": ["r18dev"],
        "jav": ["javlibrary"],
    }

    def expand_sources(source_list: list[str]) -> list[str]:
        """Expand source aliases to actual scraper names"""
        expanded = []
        for source in source_list:
            if source in SCRAPER_ALIASES:
                expanded.extend(SCRAPER_ALIASES[source])
            else:
                expanded.append(source)
        return expanded

    # Helper function to get field by priority
    def get_field(field_name: str, priority_list: list[str]) -> Any:
        """Get field value from results based on priority order."""
        # Expand aliases in priority list
        expanded_priority = expand_sources(priority_list)
        for source in expanded_priority:
            if source in results:
                value = getattr(results[source], field_name, None)
                if value:
                    return value
        # Fallback to any available value
        for result in results.values():
            value = getattr(result, field_name, None)
            if value:
                return value
        return None

    # Merge actresses from all sources
    def merge_actresses() -> list[Actress]:
        all_actresses: dict[str, Actress] = {}

        expanded_actress_priority = expand_sources(priority.actress)
        for source in expanded_actress_priority:
            if source in results:
                for actress in results[source].actresses:
                    key = actress.japanese_name or actress.full_name
                    if key and key not in all_actresses:
                        all_actresses[key] = actress

        # Add any remaining from other sources
        for result in results.values():
            for actress in result.actresses:
                key = actress.japanese_name or actress.full_name
                if key and key not in all_actresses:
                    all_actresses[key] = actress

        return list(all_actresses.values())

    # Merge genres from all sources (union)
    def merge_genres() -> list[str]:
        all_genres = set()
        expanded_genre_priority = expand_sources(priority.genre)
        for source in expanded_genre_priority:
            if source in results:
                all_genres.update(results[source].genres)
        for result in results.values():
            all_genres.update(result.genres)
        return list(all_genres)

    # Build aggregated metadata
    aggregated = MovieMetadata(
        id=get_field("id", priority.title) or base.id,
        content_id=get_field("content_id", priority.title),
        title=get_field("title", priority.title) or base.title,
        original_title=get_field("original_title", priority.title),
        description=get_field("description", priority.description),
        release_date=get_field("release_date", priority.release_date),
        runtime=get_field("runtime", priority.runtime),
        director=get_field("director", priority.maker),
        maker=get_field("maker", priority.maker),
        label=get_field("label", priority.maker),
        series=get_field("series", priority.maker),
        actresses=merge_actresses(),
        genres=merge_genres(),
        tags=list(set(tag for r in results.values() for tag in r.tags)),
        rating=get_field("rating", priority.title),
        cover_url=get_field("cover_url", priority.cover_url),
        screenshot_urls=get_field("screenshot_urls", priority.cover_url) or [],
        trailer_url=get_field("trailer_url", priority.cover_url),
        source="aggregated",
    )

    return aggregated


def merge_two(primary: MovieMetadata, secondary: MovieMetadata) -> MovieMetadata:
    """
    Merge two metadata objects, preferring primary values

    Args:
        primary: Primary metadata (values preferred)
        secondary: Secondary metadata (fallback values)

    Returns:
        Merged MovieMetadata
    """
    return MovieMetadata(
        id=primary.id or secondary.id,
        content_id=primary.content_id or secondary.content_id,
        title=primary.title or secondary.title,
        original_title=primary.original_title or secondary.original_title,
        description=primary.description or secondary.description,
        release_date=primary.release_date or secondary.release_date,
        runtime=primary.runtime or secondary.runtime,
        director=primary.director or secondary.director,
        maker=primary.maker or secondary.maker,
        label=primary.label or secondary.label,
        series=primary.series or secondary.series,
        actresses=primary.actresses if primary.actresses else secondary.actresses,
        genres=list(set(primary.genres + secondary.genres)),
        tags=list(set(primary.tags + secondary.tags)),
        rating=primary.rating or secondary.rating,
        cover_url=primary.cover_url or secondary.cover_url,
        screenshot_urls=primary.screenshot_urls or secondary.screenshot_urls,
        trailer_url=primary.trailer_url or secondary.trailer_url,
        source=f"{primary.source}+{secondary.source}",
    )

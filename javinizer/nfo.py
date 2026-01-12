"""NFO XML generator for Jellyfin/Kodi/Plex/Emby compatibility"""

from xml.etree import ElementTree as ET
from xml.dom import minidom
from typing import Optional

from javinizer.models import MovieMetadata


def escape_xml_chars(text: str) -> str:
    """Escape special XML characters"""
    if not text:
        return ""
    # Only escape characters that are invalid in XML content
    # Note: / is valid in XML and should NOT be escaped
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_nfo(
    metadata: MovieMetadata,
    add_generic_role: bool = True,
    poster_filename: Optional[str] = "cover.jpg",
    backdrop_filename: Optional[str] = "backdrop.jpg",
    use_japanese_names: bool = False,
) -> str:
    """
    Generate Jellyfin/Kodi compatible NFO XML string from movie metadata.

    Args:
        metadata: MovieMetadata object with all movie information
        add_generic_role: Whether to add "Actress" role to actors
        poster_filename: Local poster filename (for thumb element)
        backdrop_filename: Local backdrop filename (for fanart element)
        use_japanese_names: Use Japanese names for actresses if available

    Returns:
        XML string compatible with Jellyfin/Kodi/Plex/Emby
    """
    # Create root element
    movie = ET.Element("movie")

    # Title - use plain title for Jellyfin (display_name includes [ID] prefix)
    _add_element(movie, "title", escape_xml_chars(metadata.title))
    _add_element(
        movie,
        "originaltitle",
        escape_xml_chars(metadata.original_title or metadata.title),
    )

    # Plot/Description
    _add_element(movie, "plot", escape_xml_chars(metadata.description or ""))

    # Runtime (in minutes)
    _add_element(movie, "runtime", str(metadata.runtime) if metadata.runtime else "")

    # Dates
    if metadata.release_date:
        _add_element(movie, "year", str(metadata.year))
        _add_element(movie, "premiered", metadata.release_date.isoformat())

    # Production info
    _add_element(movie, "studio", escape_xml_chars(metadata.maker or ""))
    _add_element(movie, "director", escape_xml_chars(metadata.director or ""))

    # Series/Set
    if metadata.series:
        set_elem = ET.SubElement(movie, "set")
        _add_element(set_elem, "name", escape_xml_chars(metadata.series))

    # Genres
    for genre in metadata.genres:
        _add_element(movie, "genre", escape_xml_chars(genre))

    # Tags
    for tag in metadata.tags:
        _add_element(movie, "tag", escape_xml_chars(tag))

    # Add label as tag if exists
    if metadata.label:
        _add_element(movie, "tag", escape_xml_chars(metadata.label))

    # MPAA rating
    _add_element(movie, "mpaa", "XXX")

    # Rating
    if metadata.rating:
        rating_elem = ET.SubElement(movie, "ratings")
        r = ET.SubElement(rating_elem, "rating", {"name": "default", "default": "true"})
        _add_element(r, "value", f"{metadata.rating.rating:.1f}")
        _add_element(r, "votes", str(metadata.rating.votes))

    # Actors/Actresses
    for actress in metadata.actresses:
        actor_elem = ET.SubElement(movie, "actor")

        # Determine display name based on preference
        if use_japanese_names and actress.japanese_name:
            name = actress.japanese_name
        else:
            name = actress.full_name

        _add_element(actor_elem, "name", escape_xml_chars(name))

        if add_generic_role:
            _add_element(actor_elem, "role", "Actress")

        if actress.thumb_url:
            _add_element(actor_elem, "thumb", actress.thumb_url)

    # Poster image (thumb with aspect)
    if poster_filename:
        thumb_elem = ET.SubElement(movie, "thumb", {"aspect": "poster"})
        thumb_elem.text = poster_filename

    # Backdrop/Fanart
    if backdrop_filename:
        fanart_elem = ET.SubElement(movie, "fanart")
        thumb_elem = ET.SubElement(fanart_elem, "thumb")
        thumb_elem.text = backdrop_filename

    # Unique IDs - important for Jellyfin to identify the media
    uniqueid_elem = ET.SubElement(
        movie, "uniqueid", {"type": "javid", "default": "true"}
    )
    uniqueid_elem.text = metadata.id

    if metadata.content_id:
        uniqueid_dmm = ET.SubElement(movie, "uniqueid", {"type": "dmm"})
        uniqueid_dmm.text = metadata.content_id

    # Trailer URL
    if metadata.trailer_url:
        _add_element(movie, "trailer", metadata.trailer_url)

    # Convert to pretty-printed XML string
    return _prettify(movie)


def _add_element(parent: ET.Element, tag: str, text: str | None) -> ET.Element:
    """Add a child element with text content"""
    elem = ET.SubElement(parent, tag)
    elem.text = text if text else ""
    return elem


def _prettify(elem: ET.Element) -> str:
    """Return a pretty-printed XML string"""
    rough_string = ET.tostring(elem, encoding="unicode")
    parsed = minidom.parseString(rough_string)

    # Format with proper indentation
    pretty = parsed.toprettyxml(indent="    ")

    # Remove extra blank lines and fix XML declaration
    lines = pretty.split("\n")
    # Replace default declaration with our preferred format
    lines[0] = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'

    # Filter out empty lines while preserving structure
    result = []
    for line in lines:
        if line.strip():
            result.append(line)

    return "\n".join(result)


def save_nfo(metadata: MovieMetadata, filepath: str, **kwargs) -> None:
    """Save NFO XML to file"""
    content = generate_nfo(metadata, **kwargs)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


# Example usage
if __name__ == "__main__":
    from javinizer.models import Actress, Rating
    from datetime import date

    # Create sample metadata
    sample = MovieMetadata(
        id="IPX-486",
        title="Sample Movie Title",
        original_title="サンプル映画タイトル",
        description="This is a sample description.",
        release_date=date(2020, 9, 12),
        runtime=120,
        maker="Idea Pocket",
        actresses=[
            Actress(
                first_name="Momo",
                last_name="Sakura",
                japanese_name="桜もも",
            )
        ],
        genres=["Beautiful Girl", "Featured Actress"],
        rating=Rating(rating=8.5, votes=100),
        source="dmm",
    )

    print(generate_nfo(sample))

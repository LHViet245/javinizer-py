# File: javinizer/scrapers/utils.py
"""Shared utility functions for scrapers"""

import re
from functools import lru_cache


@lru_cache(maxsize=256)
def normalize_id_variants(movie_id: str) -> list[str]:
    """
    Generate possible content ID formats for a movie ID.

    DMM and R18 use various content ID formats for the same movie:
    - Some IDs have digit prefixes: START-422 -> 1start422
    - Some use padding: IPX-486 -> ipx00486
    - Some have h_ prefix for amateur content

    Args:
        movie_id: Original movie ID (e.g., "IPX-486", "SSNI-123")

    Returns:
        List of possible content IDs to try, with most common formats first
    """
    movie_id = movie_id.upper().strip()

    match = re.match(r"([A-Z]+)-?(\d+)", movie_id)
    if not match:
        return [movie_id.lower()]

    prefix, number = match.groups()
    prefix_lower = prefix.lower()

    # Generate multiple possible formats
    variants = []

    # Format 1: prefix + padded number (ipx00486) - most common
    variants.append(f"{prefix_lower}{number.zfill(5)}")

    # Format 2: digit prefix + prefix + number (1start422)
    # Some content IDs have a leading digit (usually 1)
    variants.append(f"1{prefix_lower}{number}")

    # Format 3: prefix + number without padding
    variants.append(f"{prefix_lower}{number}")

    # Format 4: digit prefix + prefix + padded number
    variants.append(f"1{prefix_lower}{number.zfill(5)}")

    # Format 5: h_ prefix for amateur content
    variants.append(f"h_{prefix_lower}{number.zfill(5)}")

    return variants


@lru_cache(maxsize=256)
def normalize_id(movie_id: str) -> tuple[str, str]:
    """
    Convert movie ID to primary content ID format.

    Args:
        movie_id: Original movie ID (e.g., "IPX-486")

    Returns:
        Tuple of (normalized_id, display_id)
        - normalized_id: Content ID format (e.g., "ipx00486")
        - display_id: Display format (e.g., "IPX-486")
    """
    movie_id = movie_id.upper().strip()

    match = re.match(r"([A-Z]+)-?(\d+)", movie_id)
    if not match:
        return movie_id.lower(), movie_id

    prefix, number = match.groups()
    content_id = f"{prefix.lower()}{number.zfill(5)}"
    display_id = f"{prefix}-{number.zfill(3)}"

    return content_id, display_id


def content_id_to_movie_id(content_id: str) -> str:
    """
    Convert DMM/R18 content ID to standard movie ID format.

    Args:
        content_id: Content ID (e.g., "ipx00486", "1start422")

    Returns:
        Standard movie ID format (e.g., "IPX-486", "START-422")
    """
    # Pattern: optional digit prefix + letters + digits + optional suffix
    match = re.match(r"(\d*)([a-z]+)(\d+)(.*)$", content_id, re.IGNORECASE)
    if not match:
        return content_id.upper()

    _, prefix, number, suffix = match.groups()
    # Remove leading zeros but keep at least 3 digits
    number = number.lstrip("0").zfill(3)
    return f"{prefix.upper()}-{number}{suffix.upper()}"


def is_valid_actress_name(name: str) -> bool:
    """
    Check if a string is a valid actress name.

    Filters out promotional text, ads, and other invalid entries that may
    appear in actress link text on DMM.

    Args:
        name: Candidate actress name string

    Returns:
        True if name appears to be a valid actress name
    """
    # Names should be reasonable length (most Japanese names < 20 chars)
    if len(name) > 30:
        return False

    # Skip if contains promotional markers
    invalid_markers = [
        "★",
        "☆",
        "●",
        "◆",
        "■",  # Special markers
        "ご購入",
        "商品",
        "こちら",  # Purchase/product text
        "アダルトブック",
        "写真集",  # Book/photobook promo
        "http",
        "www",
        ".com",
        ".jp",  # URLs
        "限定",
        "特典",
        "キャンペーン",  # Limited/bonus/campaign
        "配信",
        "ダウンロード",  # Distribution/download
    ]

    for marker in invalid_markers:
        if marker in name:
            return False

    # Name should contain at least some Japanese or Latin characters
    has_valid_chars = bool(
        re.search(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf a-zA-Z]", name)
    )

    return has_valid_chars

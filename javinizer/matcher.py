"""File matching and movie ID extraction for JAV files"""

import re
from pathlib import Path
from typing import Optional


# Supported video extensions
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.wmv', '.mov', '.flv', '.m4v', '.rmvb', '.asf'}

# Supported subtitle extensions
SUBTITLE_EXTENSIONS = {'.srt', '.ass', '.ssa', '.sub', '.vtt'}

# Common JAV ID patterns
# Pattern examples: ABC-123, ABC123, T28-123, SSNI-486, 1PONDO-123456_789
JAV_ID_PATTERNS = [
    # Standard format: ABC-123 or ABC-1234
    r'([a-zA-Z]{2,10})-?(\d{2,5})',
    # With prefix number: 1ABC-123
    r'(\d)?([a-zA-Z]{2,10})-?(\d{2,5})',
    # Special studios: T28-123, S1-123
    r'([a-zA-Z]\d+)-(\d{2,5})',
    # FC2: FC2-PPV-1234567 or FC2PPV-1234567
    r'(FC2)[-_]?(PPV)?[-_]?(\d{5,7})',
    # HEYZO: HEYZO-1234
    r'(HEYZO)[-_]?(\d{4})',
    # Caribbeancom: 123456-789
    r'(\d{6})-(\d{3})',
]


def extract_movie_id(filename: str) -> Optional[str]:
    """
    Extract JAV movie ID from filename.

    Args:
        filename: Video filename (with or without extension)

    Returns:
        Extracted movie ID (e.g., "IPX-486") or None if not found

    Examples:
        >>> extract_movie_id("IPX-486.mp4")
        'IPX-486'
        >>> extract_movie_id("[SubGroup] SSNI-123 Title.mkv")
        'SSNI-123'
        >>> extract_movie_id("abc123.mp4")
        'ABC-123'
    """
    # Remove file extension
    name = Path(filename).stem

    # Remove common prefixes like [SubGroup], (Year), etc.
    name = re.sub(r'\[[^\]]*\]', '', name)
    name = re.sub(r'\([^)]*\)', '', name)
    name = name.strip()

    # Try FC2 pattern FIRST (before standard pattern catches it)
    fc2_match = re.search(r'FC2[-_]?(?:PPV)?[-_]?(\d{5,7})', name, re.IGNORECASE)
    if fc2_match:
        return f"FC2-PPV-{fc2_match.group(1)}"

    # Try HEYZO pattern
    heyzo_match = re.search(r'HEYZO[-_]?(\d{4})', name, re.IGNORECASE)
    if heyzo_match:
        return f"HEYZO-{heyzo_match.group(1)}"

    # Try Caribbeancom pattern (123456-789) before standard
    carib_match = re.search(r'(\d{6})[-_](\d{3})', name)
    if carib_match:
        return f"{carib_match.group(1)}-{carib_match.group(2)}"

    # Try special studios: T28-123, S1-123 (Letter + Digits)
    special_match = re.search(r'\b([a-zA-Z]\d+)[-_]?(\d{2,5})', name, re.IGNORECASE)
    if special_match:
        prefix = special_match.group(1).upper()
        number = special_match.group(2)
        return f"{prefix}-{number}"

    # Try standard JAV pattern (most common)
    # Match: ABC-123, ABC123, SSNI-486, etc.
    standard_match = re.search(r'([a-zA-Z]{2,10})[-_]?(\d{2,5})', name, re.IGNORECASE)
    if standard_match:
        prefix = standard_match.group(1).upper()
        number = standard_match.group(2).lstrip('0') or '0'
        return f"{prefix}-{number}"

    return None


def normalize_movie_id(movie_id: str) -> str:
    """
    Normalize movie ID to standard format.

    Args:
        movie_id: Raw movie ID

    Returns:
        Normalized ID (uppercase, with hyphen)

    Examples:
        >>> normalize_movie_id("ipx486")
        'IPX-486'
        >>> normalize_movie_id("SSNI-123")
        'SSNI-123'
    """
    movie_id = movie_id.upper().strip()

    # Already has hyphen
    if '-' in movie_id:
        return movie_id

    # Split letters and numbers
    match = re.match(r'([A-Z]+)(\d+)', movie_id)
    if match:
        prefix = match.group(1)
        number = match.group(2).lstrip('0') or '0'
        return f"{prefix}-{number}"

    return movie_id


def find_video_files(
    directory: Path,
    recursive: bool = False,
    min_size_mb: int = 0
) -> list[Path]:
    """
    Find all video files in a directory.

    Args:
        directory: Directory to search
        recursive: Search subdirectories
        min_size_mb: Minimum file size in MB (0 = no limit)

    Returns:
        List of video file paths
    """
    if not directory.is_dir():
        return []

    min_size_bytes = min_size_mb * 1024 * 1024
    videos = []

    pattern = '**/*' if recursive else '*'

    for path in directory.glob(pattern):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            if min_size_bytes == 0 or path.stat().st_size >= min_size_bytes:
                videos.append(path)

    return sorted(videos)


def find_subtitle_files(video_path: Path) -> list[Path]:
    """
    Find subtitle files that match a video file.

    Args:
        video_path: Path to video file

    Returns:
        List of matching subtitle file paths
    """
    if not video_path.exists():
        return []

    video_stem = video_path.stem
    video_dir = video_path.parent
    subtitles = []

    for sub_ext in SUBTITLE_EXTENSIONS:
        # Exact match: video.srt
        exact = video_dir / f"{video_stem}{sub_ext}"
        if exact.exists():
            subtitles.append(exact)

        # Language code match: video.en.srt, video.vi.srt
        for lang_sub in video_dir.glob(f"{video_stem}.*{sub_ext}"):
            if lang_sub not in subtitles:
                subtitles.append(lang_sub)

    return sorted(subtitles)


def get_subtitle_language(subtitle_path: Path) -> Optional[str]:
    """
    Extract language code from subtitle filename.

    Args:
        subtitle_path: Path to subtitle file

    Returns:
        Language code (e.g., "en", "vi") or None

    Examples:
        >>> get_subtitle_language(Path("movie.en.srt"))
        'en'
        >>> get_subtitle_language(Path("movie.vi.ass"))
        'vi'
    """
    stem = subtitle_path.stem
    parts = stem.rsplit('.', 1)

    if len(parts) == 2:
        lang = parts[1].lower()
        # Common language codes
        if len(lang) == 2 or len(lang) == 3 or lang in {'zh-hans', 'zh-hant', 'pt-br'}:
            return lang

    return None

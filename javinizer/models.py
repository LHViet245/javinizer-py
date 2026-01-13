"""Pydantic data models for JAV metadata"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class Actress(BaseModel):
    """Actress/Actor information"""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    japanese_name: Optional[str] = None
    thumb_url: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get full name in Western order (First Last)"""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or self.japanese_name or "Unknown"

    @property
    def full_name_japanese_order(self) -> str:
        """Get full name in Japanese order (Last First)"""
        parts = [self.last_name, self.first_name]
        return " ".join(p for p in parts if p) or self.japanese_name or "Unknown"


class Rating(BaseModel):
    """Movie rating with vote count"""

    rating: float = Field(ge=0, le=10)
    votes: int = Field(ge=0)


class MovieMetadata(BaseModel):
    """Complete movie metadata"""

    # Core identifiers
    id: str  # e.g., "IPX-486"
    content_id: Optional[str] = None  # DMM content ID

    # Titles
    title: str
    original_title: Optional[str] = None  # Japanese title

    # Basic info
    description: Optional[str] = None
    release_date: Optional[date] = None
    runtime: Optional[int] = None  # minutes

    # Studio/Production
    director: Optional[str] = None
    maker: Optional[str] = None  # Studio
    label: Optional[str] = None
    series: Optional[str] = None

    # Cast and tags
    actresses: list[Actress] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    # Rating
    rating: Optional[Rating] = None

    # Media URLs
    cover_url: Optional[str] = None
    screenshot_urls: list[str] = Field(default_factory=list)
    trailer_url: Optional[str] = None

    # Source tracking
    source: str = "unknown"

    @property
    def year(self) -> Optional[int]:
        """Extract year from release date"""
        return self.release_date.year if self.release_date else None

    @property
    def display_name(self) -> str:
        """Format display name as [ID] Title"""
        return f"[{self.id}] {self.title}"


class ProxyConfig(BaseModel):
    """Proxy configuration for HTTP/SOCKS5"""

    enabled: bool = False
    url: Optional[str] = (
        None  # e.g., "socks5://127.0.0.1:1080" or "http://user:pass@proxy:8080"
    )

    @property
    def httpx_proxy(self) -> Optional[str]:
        """Get proxy URL for httpx"""
        if self.enabled and self.url:
            return self.url
        return None


class ScraperPriority(BaseModel):
    """Priority configuration for metadata fields"""

    # Which scrapers to use for each field (first match wins)
    actress: list[str] = Field(default_factory=lambda: ["r18dev", "dmm", "javlibrary"])
    title: list[str] = Field(default_factory=lambda: ["r18dev", "javlibrary", "dmm"])
    cover_url: list[str] = Field(
        default_factory=lambda: ["r18dev", "dmm", "javlibrary"]
    )
    description: list[str] = Field(default_factory=lambda: ["dmm", "r18dev"])
    genre: list[str] = Field(default_factory=lambda: ["r18dev", "javlibrary", "dmm"])
    release_date: list[str] = Field(
        default_factory=lambda: ["r18dev", "javlibrary", "dmm"]
    )
    runtime: list[str] = Field(default_factory=lambda: ["r18dev", "javlibrary", "dmm"])
    maker: list[str] = Field(default_factory=lambda: ["r18dev", "javlibrary", "dmm"])


class SortSettings(BaseModel):
    """Sorting configuration for Jellyfin compatibility"""

    # Enable/disable sorting features
    enabled: bool = True
    move_files: bool = True  # Move (True) or copy (False)
    create_nfo: bool = True
    download_images: bool = True
    move_subtitles: bool = True

    # Format templates (Jellyfin optimized)
    folder_format: str = "<TITLE> (<YEAR>) [<ID>]"
    file_format: str = "<TITLE> (<YEAR>) [<ID>]"
    nfo_format: str = "<TITLE> (<YEAR>) [<ID>]"

    # Image filenames (Jellyfin standard)
    poster_filename: str = "cover.jpg"
    backdrop_filename: str = "backdrop.jpg"

    # Title settings
    max_title_length: int = 80

    # Actress format
    actress_delimiter: str = ", "
    actress_language_ja: bool = False
    first_name_order: bool = True
    group_actress: bool = True

    # File matching
    min_file_size_mb: int = 100  # Minimum video file size in MB


class ThumbsSettings(BaseModel):
    """Thumbnail database settings"""

    enabled: bool = True
    storage_path: str = "thumbs"  # Relative to config or absolute
    csv_file: str = "actresses.csv"  # Relative to config or absolute
    path_mapping: dict[str, str] = Field(
        default_factory=dict
    )  # e.g., {"E:/Javinizer/thumbs": "/media/thumbs"}
    auto_download: bool = True  # Add new actresses found during scrape
    download_on_sort: bool = True  # Download thumb ONLY when sorting
    verify_ssl: bool = True


class TranslationSettings(BaseModel):
    """Translation settings for Japanese to other languages"""

    enabled: bool = False
    provider: str = "google"  # "google" or "deepl"
    target_language: str = "en"
    deepl_api_key: Optional[str] = None
    translate_title: bool = True
    translate_description: bool = True


class RetrySettings(BaseModel):
    """HTTP retry settings with exponential backoff"""

    enabled: bool = True
    max_retries: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds cap
    exponential_base: float = 2.0
    retryable_status_codes: list[int] = Field(
        default_factory=lambda: [429, 500, 502, 503, 504]
    )


class RateLimitSettings(BaseModel):
    """Rate limiting settings per domain"""

    enabled: bool = True
    default_delay: float = 1.0  # seconds between requests to same domain
    domain_delays: dict[str, float] = Field(
        default_factory=dict
    )  # per-domain overrides


class Settings(BaseModel):
    """Application settings with versioning support.

    The schema_version field tracks the config format version for
    future migrations when the settings structure changes.
    """

    # Schema version for config migration
    schema_version: str = "1.0"

    # Scraper enable/disable
    scraper_dmm: bool = True
    scraper_r18dev: bool = True
    scraper_javlibrary: bool = False  # Requires cookies for Cloudflare

    # Scraper priority for aggregation
    priority: ScraperPriority = Field(default_factory=ScraperPriority)

    # Proxy settings
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)

    # Request settings
    timeout: float = 30.0
    sleep_between_requests: float = 1.0
    log_file: Optional[str] = (
        None  # Path to log file (default: None for no file logging)
    )

    # Javlibrary specific (Cloudflare cookies)
    javlibrary_cookies: dict[str, str] = Field(default_factory=dict)
    javlibrary_user_agent: str = ""

    # Sorting settings (Jellyfin optimized)
    sort: SortSettings = Field(default_factory=SortSettings)

    # NFO settings
    nfo_add_generic_role: bool = True
    nfo_actress_language_ja: bool = False

    # Thumbnail DB
    thumbs: ThumbsSettings = Field(default_factory=ThumbsSettings)

    # Translation
    translation: TranslationSettings = Field(default_factory=TranslationSettings)

    # HTTP Retry settings
    retry: RetrySettings = Field(default_factory=RetrySettings)

    # Rate limiting settings
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)

    # Cache settings
    cache_enabled: bool = True
    cache_ttl_days: int = 30
    cache_path: str = "cache/metadata.db"

    # Concurrency settings
    max_concurrent_downloads: int = 5
    max_concurrent_scrapers: int = 3


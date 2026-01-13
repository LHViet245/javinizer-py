"""Custom exception hierarchy for Javinizer.

This module defines all custom exceptions used throughout the application.
Using custom exceptions allows for better error handling and user-friendly
error messages in the CLI.
"""

from typing import Optional


class JavinizerError(Exception):
    """Base exception for all Javinizer errors.

    All custom exceptions should inherit from this class to allow
    catching all Javinizer-specific errors with a single except clause.
    """

    def __init__(self, message: str, *args: object) -> None:
        self.message = message
        super().__init__(message, *args)


# ============================================================================
# Scraper Exceptions
# ============================================================================


class ScraperError(JavinizerError):
    """Base exception for scraper-related errors."""

    def __init__(
        self,
        message: str,
        scraper_name: Optional[str] = None,
        movie_id: Optional[str] = None,
    ) -> None:
        self.scraper_name = scraper_name
        self.movie_id = movie_id
        super().__init__(message)


class NetworkError(ScraperError):
    """Raised when a network request fails.

    This includes connection errors, timeouts, and DNS resolution failures.
    """

    def __init__(
        self,
        message: str,
        scraper_name: Optional[str] = None,
        movie_id: Optional[str] = None,
        status_code: Optional[int] = None,
        url: Optional[str] = None,
    ) -> None:
        self.status_code = status_code
        self.url = url
        super().__init__(message, scraper_name, movie_id)


class ParseError(ScraperError):
    """Raised when parsing scraped content fails.

    This includes HTML/JSON parsing errors and missing expected data.
    """

    def __init__(
        self,
        message: str,
        scraper_name: Optional[str] = None,
        movie_id: Optional[str] = None,
        content_snippet: Optional[str] = None,
    ) -> None:
        self.content_snippet = content_snippet
        super().__init__(message, scraper_name, movie_id)


class RateLimitError(ScraperError):
    """Raised when rate limited by a website.

    Contains information about when to retry.
    """

    def __init__(
        self,
        message: str,
        scraper_name: Optional[str] = None,
        movie_id: Optional[str] = None,
        retry_after: Optional[float] = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, scraper_name, movie_id)


class CloudflareError(ScraperError):
    """Raised when Cloudflare blocks the request.

    This usually means cookies need to be refreshed.
    """

    pass


class MovieNotFoundError(ScraperError):
    """Raised when a movie cannot be found on any source."""

    pass


# ============================================================================
# Configuration Exceptions
# ============================================================================


class ConfigError(JavinizerError):
    """Base exception for configuration-related errors."""

    pass


class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails.

    Contains details about which field failed validation.
    """

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[str] = None,
    ) -> None:
        self.field_name = field_name
        self.field_value = field_value
        super().__init__(message)


class ConfigMigrationError(ConfigError):
    """Raised when configuration migration fails.

    This occurs when upgrading config from an older schema version.
    """

    def __init__(
        self,
        message: str,
        from_version: Optional[str] = None,
        to_version: Optional[str] = None,
    ) -> None:
        self.from_version = from_version
        self.to_version = to_version
        super().__init__(message)


# ============================================================================
# Sorter Exceptions
# ============================================================================


class SorterError(JavinizerError):
    """Base exception for sorting/organizing errors."""

    pass


class FileOperationError(SorterError):
    """Raised when file operations (move, copy, rename) fail."""

    def __init__(
        self,
        message: str,
        source_path: Optional[str] = None,
        dest_path: Optional[str] = None,
    ) -> None:
        self.source_path = source_path
        self.dest_path = dest_path
        super().__init__(message)


class MatcherError(SorterError):
    """Raised when filename matching/ID extraction fails."""

    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
    ) -> None:
        self.filename = filename
        super().__init__(message)


# ============================================================================
# Cache Exceptions
# ============================================================================


class CacheError(JavinizerError):
    """Base exception for cache-related errors."""

    pass


class CacheReadError(CacheError):
    """Raised when reading from cache fails."""

    pass


class CacheWriteError(CacheError):
    """Raised when writing to cache fails."""

    pass


# ============================================================================
# Download Exceptions
# ============================================================================


class DownloadError(JavinizerError):
    """Base exception for download-related errors."""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
    ) -> None:
        self.url = url
        super().__init__(message)


class ImageDownloadError(DownloadError):
    """Raised when image download fails."""

    pass

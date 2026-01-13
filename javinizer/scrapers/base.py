"""Base scraper abstract class"""

from abc import ABC, abstractmethod
from typing import Optional
import ssl

import httpx

from javinizer.models import MovieMetadata, ProxyConfig
from javinizer.logger import get_logger
from javinizer.http.rate_limiter import DomainRateLimiter, get_rate_limiter
from javinizer.exceptions import (
    NetworkError,
    ParseError,
    RateLimitError,
    MovieNotFoundError,
)

logger = get_logger(__name__)


# Legacy SSL context for servers with older TLS configurations
# Only created when verify_ssl=False is explicitly set
def _create_legacy_ssl_context() -> ssl.SSLContext:
    """
    Create SSL context for legacy servers requiring insecure connections.

    WARNING: Only use when absolutely necessary (e.g., legacy server endpoints).
    This disables certificate verification and is vulnerable to MITM attacks.
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        ctx.options |= 0x4  # SSL_OP_LEGACY_SERVER_CONNECT
    except AttributeError:
        pass
    return ctx


# Lazy-initialized legacy context (only created if needed)
_LEGACY_SSL_CONTEXT: Optional[ssl.SSLContext] = None


def get_legacy_ssl_context() -> ssl.SSLContext:
    """Get or create the legacy SSL context."""
    global _LEGACY_SSL_CONTEXT
    if _LEGACY_SSL_CONTEXT is None:
        _LEGACY_SSL_CONTEXT = _create_legacy_ssl_context()
        logger.warning("Using insecure SSL context - certificate verification disabled")
    return _LEGACY_SSL_CONTEXT


# Default user agent
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class BaseScraper(ABC):
    """Abstract base class for all scrapers"""

    name: str = "base"
    base_url: str = ""

    def __init__(
        self,
        timeout: float = 30.0,
        proxy: Optional[ProxyConfig] = None,
        cookies: Optional[dict[str, str]] = None,
        user_agent: Optional[str] = None,
        verify_ssl: bool = True,
        rate_limiter: Optional[DomainRateLimiter] = None,
    ):
        """
        Initialize scraper with optional proxy and cookie support

        Args:
            timeout: Request timeout in seconds
            proxy: ProxyConfig for HTTP/SOCKS5 proxy
            cookies: Dict of cookies to include in requests
            user_agent: Custom user agent string
            verify_ssl: Enable SSL certificate verification (default: True).
                        Set to False only for legacy servers with SSL issues.
            rate_limiter: Optional rate limiter instance (uses global if None)
        """
        self.timeout = timeout
        self.proxy = proxy
        self.cookies = cookies or {}
        self.user_agent = user_agent or DEFAULT_USER_AGENT
        self.verify_ssl = verify_ssl
        self.rate_limiter = rate_limiter
        self._client: Optional[httpx.Client] = None

    def _get_proxy_url(self) -> Optional[str]:
        """Get proxy URL if configured"""
        if self.proxy and self.proxy.enabled and self.proxy.url:
            return self.proxy.url
        return None

    @property
    def client(self):
        """Lazy-initialized HTTP client"""
        if self._client is None:
            proxy_url = self._get_proxy_url()

            # Use httpx for SOCKS proxy (curl_cffi has TLS issues with SOCKS on Windows)
            use_httpx = proxy_url and proxy_url.startswith("socks")

            if not use_httpx:
                try:
                    from curl_cffi import requests

                    # Setup headers
                    headers = {"User-Agent": self.user_agent}

                    # Initialize curl_cffi session with Chrome impersonation
                    self._client = requests.Session(
                        impersonate="chrome124",  # Match modern Chrome
                        headers=headers,
                        cookies=self.cookies,
                        proxies={"http": proxy_url, "https": proxy_url}
                        if proxy_url
                        else None,
                        timeout=self.timeout,
                        allow_redirects=True,
                        verify=self.verify_ssl,
                    )
                    return self._client
                except ImportError as e:
                    logger.debug(
                        f"curl_cffi not available: {e}. Falling back to httpx."
                    )
                    use_httpx = True
                except Exception as e:
                    logger.warning(
                        f"curl_cffi initialization failed: {e}. Falling back to httpx."
                    )
                    use_httpx = True

            if use_httpx:
                # Fallback to httpx (better SOCKS support)
                import httpx

                client_kwargs = {
                    "timeout": self.timeout,
                    "headers": {"User-Agent": self.user_agent},
                    "follow_redirects": True,
                    "cookies": self.cookies,
                }
                if proxy_url:
                    client_kwargs["proxy"] = proxy_url
                    client_kwargs["verify"] = self.verify_ssl
                else:
                    # Use legacy context only if SSL verification is disabled
                    client_kwargs["verify"] = (
                        True if self.verify_ssl else get_legacy_ssl_context()
                    )

                self._client = httpx.Client(**client_kwargs)

        return self._client

    def close(self) -> None:
        """Close the HTTP client"""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "BaseScraper":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    @abstractmethod
    def get_search_url(self, movie_id: str) -> str:
        """Build search URL for a movie ID"""
        ...

    @abstractmethod
    def get_movie_url(self, movie_id: str) -> Optional[str]:
        """Find the direct movie page URL from ID"""
        ...

    @abstractmethod
    def scrape(self, url: str) -> Optional[MovieMetadata]:
        """Scrape metadata from a movie page URL"""
        ...

    def find(self, movie_id: str) -> Optional[MovieMetadata]:
        """
        Find and scrape metadata for a movie ID

        This is the main entry point for scraping.

        Raises:
            NetworkError: When network request fails
            ParseError: When parsing response fails
            RateLimitError: When rate limited by the server
        """
        try:
            url = self.get_movie_url(movie_id)
            if url is None:
                logger.debug(f"[{self.name}] Movie not found: {movie_id}")
                return None

            # Apply rate limiting before making request
            limiter = self.rate_limiter or get_rate_limiter()
            limiter.acquire(url)

            return self.scrape(url)

        except (NetworkError, ParseError, RateLimitError):
            # Re-raise our custom exceptions
            raise
        except httpx.TimeoutException as e:
            raise NetworkError(
                f"Request timed out after {self.timeout}s",
                scraper_name=self.name,
                movie_id=movie_id,
                url=str(e.request.url) if e.request else None,
            ) from e
        except httpx.ConnectError as e:
            raise NetworkError(
                f"Connection failed: {e}",
                scraper_name=self.name,
                movie_id=movie_id,
            ) from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError(
                    f"Rate limited by {self.name}",
                    scraper_name=self.name,
                    movie_id=movie_id,
                ) from e
            raise NetworkError(
                f"HTTP {e.response.status_code}: {e.response.reason_phrase}",
                scraper_name=self.name,
                movie_id=movie_id,
                status_code=e.response.status_code,
                url=str(e.request.url),
            ) from e
        except Exception as e:
            # Log unexpected errors but don't wrap them
            logger.error(f"[{self.name}] Unexpected error for {movie_id}: {e}")
            raise

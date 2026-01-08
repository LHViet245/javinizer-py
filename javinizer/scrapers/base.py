"""Base scraper abstract class"""

from abc import ABC, abstractmethod
from typing import Optional
import ssl

import httpx

from javinizer.models import MovieMetadata, ProxyConfig


# Create SSL context that allows legacy renegotiation
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE
# Try to enable legacy server connect if available
try:
    SSL_CONTEXT.options |= 0x4  # SSL_OP_LEGACY_SERVER_CONNECT
except Exception:
    pass

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
    ):
        """
        Initialize scraper with optional proxy and cookie support

        Args:
            timeout: Request timeout in seconds
            proxy: ProxyConfig for HTTP/SOCKS5 proxy
            cookies: Dict of cookies to include in requests
            user_agent: Custom user agent string
        """
        self.timeout = timeout
        self.proxy = proxy
        self.cookies = cookies or {}
        self.user_agent = user_agent or DEFAULT_USER_AGENT
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
                        proxies={"http": proxy_url, "https": proxy_url} if proxy_url else None,
                        timeout=self.timeout,
                        allow_redirects=True,
                    )
                    return self._client
                except (ImportError, Exception):
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
                    client_kwargs["verify"] = True
                else:
                    client_kwargs["verify"] = SSL_CONTEXT

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
        """
        url = self.get_movie_url(movie_id)
        if url is None:
            return None
        return self.scrape(url)


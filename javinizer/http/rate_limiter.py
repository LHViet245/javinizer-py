# File: javinizer/http/rate_limiter.py
"""Per-domain rate limiting for HTTP requests"""

import time
import threading
from typing import Optional
from urllib.parse import urlparse

from javinizer.logger import get_logger

logger = get_logger(__name__)


class DomainRateLimiter:
    """Thread-safe per-domain rate limiter.

    Enforces minimum delay between requests to the same domain to avoid
    overwhelming target servers.

    Attributes:
        default_delay: Default delay in seconds between requests to same domain
        domain_delays: Optional per-domain delay overrides

    Example:
        limiter = DomainRateLimiter(default_delay=1.0)
        limiter.acquire("https://www.dmm.co.jp/path")  # Blocks if needed
        # Make request...
    """

    def __init__(
        self,
        default_delay: float = 1.0,
        domain_delays: Optional[dict[str, float]] = None,
    ):
        """Initialize rate limiter.

        Args:
            default_delay: Default delay in seconds between requests
            domain_delays: Optional dict mapping domain to custom delay
        """
        self.default_delay = default_delay
        self.domain_delays = domain_delays or {}
        self._last_request: dict[str, float] = {}
        self._lock = threading.Lock()

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL.

        Args:
            url: Full URL string

        Returns:
            Domain portion of URL (e.g., "www.dmm.co.jp")
        """
        parsed = urlparse(url)
        return parsed.netloc.lower()

    def _get_delay(self, domain: str) -> float:
        """Get configured delay for a domain.

        Args:
            domain: Domain string

        Returns:
            Delay in seconds to use for this domain
        """
        return self.domain_delays.get(domain, self.default_delay)

    def acquire(self, url: str) -> float:
        """Acquire permission to make a request, blocking if needed.

        Thread-safe. Will block the calling thread if a request was made
        to the same domain too recently.

        Args:
            url: URL about to be requested

        Returns:
            Actual wait time in seconds (0 if no wait was needed)
        """
        domain = self._extract_domain(url)
        delay = self._get_delay(domain)

        with self._lock:
            now = time.time()
            last = self._last_request.get(domain, 0)
            elapsed = now - last

            wait_time = 0.0
            if elapsed < delay:
                wait_time = delay - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for {domain}")
                time.sleep(wait_time)

            self._last_request[domain] = time.time()
            return wait_time

    def reset(self, domain: Optional[str] = None) -> None:
        """Reset rate limit tracking.

        Args:
            domain: Specific domain to reset, or None to reset all
        """
        with self._lock:
            if domain:
                self._last_request.pop(domain, None)
            else:
                self._last_request.clear()

    def set_delay(self, domain: str, delay: float) -> None:
        """Set custom delay for a specific domain.

        Args:
            domain: Domain to configure
            delay: Delay in seconds for this domain
        """
        self.domain_delays[domain] = delay


# Global rate limiter instance (can be configured at startup)
_global_limiter: Optional[DomainRateLimiter] = None


def get_rate_limiter() -> DomainRateLimiter:
    """Get or create the global rate limiter instance.

    Returns:
        Global DomainRateLimiter instance
    """
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = DomainRateLimiter()
    return _global_limiter


def configure_rate_limiter(
    default_delay: float = 1.0, domain_delays: Optional[dict[str, float]] = None
) -> DomainRateLimiter:
    """Configure the global rate limiter.

    Args:
        default_delay: Default delay between requests
        domain_delays: Per-domain delay overrides

    Returns:
        Configured global rate limiter
    """
    global _global_limiter
    _global_limiter = DomainRateLimiter(default_delay, domain_delays)
    return _global_limiter

# File: javinizer/health.py
"""Health check utilities for scrapers and services"""

import time
from dataclasses import dataclass, field
from typing import Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from javinizer.logger import get_logger

logger = get_logger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: str  # "ok", "error", "timeout"
    latency_ms: float = 0.0
    message: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        return self.status == "ok"


def check_scraper_health(
    scraper_class: Any,
    test_id: str = "IPX-001",
    timeout: float = 10.0,
) -> HealthCheckResult:
    """Check if a scraper is responding.

    Args:
        scraper_class: Scraper class to test
        test_id: Test movie ID to search for
        timeout: Timeout in seconds

    Returns:
        HealthCheckResult with status and latency
    """
    name = getattr(scraper_class, "name", scraper_class.__name__)
    start_time = time.time()

    try:
        with scraper_class(timeout=timeout) as scraper:
            # Just try to get a search URL or make a basic request
            # url = scraper.get_search_url(test_id)

            # Try to reach the base URL
            response = scraper.client.head(scraper.base_url, timeout=timeout)
            latency_ms = (time.time() - start_time) * 1000

            if response.status_code < 400:
                return HealthCheckResult(
                    name=name,
                    status="ok",
                    latency_ms=latency_ms,
                    message=f"Responding ({response.status_code})",
                    details={
                        "url": scraper.base_url,
                        "status_code": response.status_code,
                    },
                )
            else:
                return HealthCheckResult(
                    name=name,
                    status="error",
                    latency_ms=latency_ms,
                    message=f"HTTP {response.status_code}",
                    details={
                        "url": scraper.base_url,
                        "status_code": response.status_code,
                    },
                )

    except TimeoutError:
        latency_ms = (time.time() - start_time) * 1000
        return HealthCheckResult(
            name=name,
            status="timeout",
            latency_ms=latency_ms,
            message=f"Timeout after {timeout}s",
        )
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return HealthCheckResult(
            name=name, status="error", latency_ms=latency_ms, message=str(e)
        )


def check_all_scrapers(timeout: float = 10.0) -> list[HealthCheckResult]:
    """Check health of all available scrapers.

    Args:
        timeout: Timeout per scraper in seconds

    Returns:
        List of HealthCheckResult for each scraper
    """
    from javinizer.scrapers.dmm import DMMScraper
    from javinizer.scrapers.r18dev import R18DevScraper

    scrapers = [DMMScraper, R18DevScraper]
    results = []

    # Check in parallel for faster results
    with ThreadPoolExecutor(max_workers=len(scrapers)) as executor:
        futures = {
            executor.submit(check_scraper_health, s, "IPX-001", timeout): s
            for s in scrapers
        }

        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                scraper = futures[future]
                name = getattr(scraper, "name", scraper.__name__)
                results.append(
                    HealthCheckResult(name=name, status="error", message=str(e))
                )

    # Sort by name for consistent output
    results.sort(key=lambda r: r.name)
    return results


def check_cache_health() -> HealthCheckResult:
    """Check cache system health.

    Returns:
        HealthCheckResult with cache status
    """
    try:
        from javinizer.cache import CacheManager, CacheConfig
        from pathlib import Path

        start_time = time.time()

        # Try to create a temporary cache
        cache = CacheManager(
            CacheConfig(
                db_path=Path(":memory:"),  # In-memory for test
                enabled=True,
            )
        )

        stats = cache.get_stats()
        cache.close()

        latency_ms = (time.time() - start_time) * 1000

        return HealthCheckResult(
            name="cache",
            status="ok",
            latency_ms=latency_ms,
            message="SQLite cache operational",
            details=stats,
        )

    except Exception as e:
        return HealthCheckResult(name="cache", status="error", message=str(e))


def get_system_status() -> dict[str, Any]:
    """Get overall system status.

    Returns:
        Dict with scraper and cache health status
    """
    scraper_results = check_all_scrapers(timeout=5.0)
    cache_result = check_cache_health()

    healthy_scrapers = sum(1 for r in scraper_results if r.is_healthy)
    total_scrapers = len(scraper_results)

    return {
        "overall_status": "ok" if healthy_scrapers > 0 else "degraded",
        "scrapers": {
            "healthy": healthy_scrapers,
            "total": total_scrapers,
            "results": [
                {
                    "name": r.name,
                    "status": r.status,
                    "latency_ms": round(r.latency_ms, 1),
                    "message": r.message,
                }
                for r in scraper_results
            ],
        },
        "cache": {
            "status": cache_result.status,
            "message": cache_result.message,
            "details": cache_result.details,
        },
    }

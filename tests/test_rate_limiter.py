# File: tests/test_rate_limiter.py
"""Tests for per-domain rate limiter module"""

import time
import threading

from javinizer.http.rate_limiter import (
    DomainRateLimiter,
    get_rate_limiter,
    configure_rate_limiter,
)


class TestDomainRateLimiter:
    """Test DomainRateLimiter class"""

    def test_init_default_delay(self):
        """Test default delay configuration"""
        limiter = DomainRateLimiter()
        assert limiter.default_delay == 1.0
        assert limiter.domain_delays == {}

    def test_init_custom_delay(self):
        """Test custom delay configuration"""
        limiter = DomainRateLimiter(
            default_delay=2.0, domain_delays={"example.com": 0.5}
        )
        assert limiter.default_delay == 2.0
        assert limiter.domain_delays["example.com"] == 0.5

    def test_extract_domain(self):
        """Test domain extraction from URLs"""
        limiter = DomainRateLimiter()

        assert limiter._extract_domain("https://www.dmm.co.jp/path") == "www.dmm.co.jp"
        assert limiter._extract_domain("http://r18.dev/api/v1") == "r18.dev"
        assert limiter._extract_domain("https://Example.COM/") == "example.com"

    def test_get_delay_default(self):
        """Test getting default delay for unknown domain"""
        limiter = DomainRateLimiter(default_delay=1.5)
        assert limiter._get_delay("unknown.com") == 1.5

    def test_get_delay_custom(self):
        """Test getting custom delay for configured domain"""
        limiter = DomainRateLimiter(default_delay=1.0, domain_delays={"fast.com": 0.1})
        assert limiter._get_delay("fast.com") == 0.1
        assert limiter._get_delay("slow.com") == 1.0

    def test_acquire_first_request_no_wait(self):
        """Test first request to domain doesn't wait"""
        limiter = DomainRateLimiter(default_delay=1.0)

        start = time.time()
        wait_time = limiter.acquire("https://example.com/page1")
        elapsed = time.time() - start

        assert wait_time == 0.0
        assert elapsed < 0.1  # Should be essentially instant

    def test_acquire_subsequent_request_waits(self):
        """Test subsequent request to same domain waits"""
        limiter = DomainRateLimiter(default_delay=0.1)

        # First request - no wait
        limiter.acquire("https://example.com/page1")

        # Second request - should wait
        start = time.time()
        wait_time = limiter.acquire("https://example.com/page2")
        elapsed = time.time() - start

        assert wait_time > 0
        assert elapsed >= 0.05  # At least some waiting

    def test_acquire_different_domains_no_wait(self):
        """Test requests to different domains don't wait"""
        limiter = DomainRateLimiter(default_delay=1.0)

        limiter.acquire("https://domain1.com/page")

        start = time.time()
        wait_time = limiter.acquire("https://domain2.com/page")
        elapsed = time.time() - start

        assert wait_time == 0.0
        assert elapsed < 0.1

    def test_reset_single_domain(self):
        """Test resetting rate limit for single domain"""
        limiter = DomainRateLimiter(default_delay=0.1)

        limiter.acquire("https://example.com/")
        limiter.reset("example.com")

        # After reset, no wait should be needed
        wait_time = limiter.acquire("https://example.com/page2")
        assert wait_time == 0.0

    def test_reset_all_domains(self):
        """Test resetting all rate limits"""
        limiter = DomainRateLimiter(default_delay=0.1)

        limiter.acquire("https://domain1.com/")
        limiter.acquire("https://domain2.com/")
        limiter.reset()

        # After reset, no wait for any domain
        assert limiter.acquire("https://domain1.com/") == 0.0
        assert limiter.acquire("https://domain2.com/") == 0.0

    def test_set_delay(self):
        """Test setting custom delay for domain"""
        limiter = DomainRateLimiter(default_delay=1.0)

        limiter.set_delay("fast.com", 0.01)
        assert limiter._get_delay("fast.com") == 0.01

    def test_thread_safety(self):
        """Test that rate limiter is thread-safe"""
        limiter = DomainRateLimiter(default_delay=0.01)
        errors = []

        def make_request():
            try:
                for _ in range(5):
                    limiter.acquire("https://example.com/")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=make_request) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestGlobalRateLimiter:
    """Test global rate limiter singleton"""

    def test_get_rate_limiter_creates_instance(self):
        """Test get_rate_limiter creates instance if none exists"""
        # Reset global state
        import javinizer.http.rate_limiter as module

        module._global_limiter = None

        limiter = get_rate_limiter()
        assert limiter is not None
        assert isinstance(limiter, DomainRateLimiter)

    def test_get_rate_limiter_returns_same_instance(self):
        """Test get_rate_limiter returns same instance"""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        assert limiter1 is limiter2

    def test_configure_rate_limiter(self):
        """Test configure_rate_limiter sets new instance"""
        limiter = configure_rate_limiter(
            default_delay=2.0, domain_delays={"test.com": 0.5}
        )

        assert limiter.default_delay == 2.0
        assert limiter.domain_delays["test.com"] == 0.5

        # Should be the global instance now
        assert get_rate_limiter() is limiter

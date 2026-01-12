# File: tests/test_concurrency.py
"""Tests for concurrency control module"""

import pytest
import asyncio
import threading
import time

from javinizer.http.concurrency import (
    ConcurrencyLimiter,
    SyncConcurrencyLimiter,
)


class TestConcurrencyLimiter:
    """Test async ConcurrencyLimiter"""

    def test_init_valid(self):
        """Test valid initialization"""
        limiter = ConcurrencyLimiter(max_concurrent=3)
        assert limiter.max_concurrent == 3
        assert limiter.active_count == 0

    def test_init_invalid_raises(self):
        """Test invalid max_concurrent raises error"""
        with pytest.raises(ValueError):
            ConcurrencyLimiter(max_concurrent=0)
        with pytest.raises(ValueError):
            ConcurrencyLimiter(max_concurrent=-1)

    def test_acquire_increments_count(self):
        """Test that acquiring increments active count"""

        async def run_test():
            limiter = ConcurrencyLimiter(max_concurrent=5)

            async with limiter.acquire():
                assert limiter.active_count == 1

            assert limiter.active_count == 0

        asyncio.run(run_test())

    def test_total_count_increments(self):
        """Test that total count tracks all operations"""

        async def run_test():
            limiter = ConcurrencyLimiter(max_concurrent=5)

            for _ in range(3):
                async with limiter.acquire():
                    pass

            assert limiter.total_count == 3

        asyncio.run(run_test())

    def test_limits_concurrency(self):
        """Test that concurrency is actually limited"""

        async def run_test():
            limiter = ConcurrencyLimiter(max_concurrent=2)
            max_observed = 0

            async def task():
                nonlocal max_observed
                async with limiter.acquire():
                    max_observed = max(max_observed, limiter.active_count)
                    await asyncio.sleep(0.05)

            await asyncio.gather(*[task() for _ in range(5)])

            assert max_observed <= 2

        asyncio.run(run_test())

    def test_reset_stats(self):
        """Test resetting statistics"""

        async def run_test():
            limiter = ConcurrencyLimiter(max_concurrent=5)

            async with limiter.acquire():
                pass

            assert limiter.total_count == 1
            limiter.reset_stats()
            assert limiter.total_count == 0

        asyncio.run(run_test())


class TestSyncConcurrencyLimiter:
    """Test sync SyncConcurrencyLimiter"""

    def test_init_valid(self):
        """Test valid initialization"""
        limiter = SyncConcurrencyLimiter(max_concurrent=3)
        assert limiter.max_concurrent == 3

    def test_init_invalid_raises(self):
        """Test invalid max_concurrent raises error"""
        with pytest.raises(ValueError):
            SyncConcurrencyLimiter(max_concurrent=0)

    def test_context_manager(self):
        """Test context manager usage"""
        limiter = SyncConcurrencyLimiter(max_concurrent=5)

        with limiter:
            assert limiter.active_count == 1

        assert limiter.active_count == 0

    def test_limits_concurrency_threads(self):
        """Test that concurrency is limited across threads"""
        limiter = SyncConcurrencyLimiter(max_concurrent=2)
        max_observed = 0
        lock = threading.Lock()

        def task():
            nonlocal max_observed
            with limiter:
                with lock:
                    max_observed = max(max_observed, limiter.active_count)
                time.sleep(0.05)

        threads = [threading.Thread(target=task) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert max_observed <= 2

    def test_total_count(self):
        """Test total count tracking"""
        limiter = SyncConcurrencyLimiter(max_concurrent=5)

        for _ in range(3):
            with limiter:
                pass

        assert limiter.total_count == 3

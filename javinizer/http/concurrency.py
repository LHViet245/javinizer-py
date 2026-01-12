# File: javinizer/http/concurrency.py
"""Concurrency control for HTTP requests and downloads"""

import asyncio
from typing import Optional
from contextlib import asynccontextmanager

from javinizer.logger import get_logger

logger = get_logger(__name__)


class ConcurrencyLimiter:
    """Semaphore-based concurrency limiter for async operations.
    
    Limits the number of concurrent operations to prevent overwhelming
    target servers or local resources.
    
    Example:
        limiter = ConcurrencyLimiter(max_concurrent=5)
        
        async def fetch_all(urls):
            tasks = [fetch_with_limit(url, limiter) for url in urls]
            return await asyncio.gather(*tasks)
        
        async def fetch_with_limit(url, limiter):
            async with limiter.acquire():
                return await fetch(url)
    """
    
    def __init__(self, max_concurrent: int = 5):
        """Initialize concurrency limiter.
        
        Args:
            max_concurrent: Maximum number of concurrent operations
        """
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be at least 1")
        
        self.max_concurrent = max_concurrent
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._active_count = 0
        self._total_count = 0
    
    def _get_semaphore(self) -> asyncio.Semaphore:
        """Get or create semaphore for current event loop."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
        return self._semaphore
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a slot for concurrent operation.
        
        Blocks if max_concurrent limit is reached.
        
        Yields:
            None when slot is acquired
        """
        semaphore = self._get_semaphore()
        
        await semaphore.acquire()
        self._active_count += 1
        self._total_count += 1
        
        try:
            yield
        finally:
            self._active_count -= 1
            semaphore.release()
    
    @property
    def active_count(self) -> int:
        """Number of currently active operations."""
        return self._active_count
    
    @property
    def total_count(self) -> int:
        """Total number of operations processed."""
        return self._total_count
    
    def reset_stats(self) -> None:
        """Reset operation counters."""
        self._total_count = 0


class SyncConcurrencyLimiter:
    """Thread-based concurrency limiter for synchronous operations.
    
    Uses threading.Semaphore for synchronous code.
    """
    
    import threading
    
    def __init__(self, max_concurrent: int = 5):
        """Initialize synchronous concurrency limiter.
        
        Args:
            max_concurrent: Maximum number of concurrent operations
        """
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be at least 1")
        
        self.max_concurrent = max_concurrent
        self._semaphore = self.threading.Semaphore(max_concurrent)
        self._active_count = 0
        self._total_count = 0
        self._lock = self.threading.Lock()
    
    def acquire(self) -> bool:
        """Acquire a slot for concurrent operation.
        
        Blocks if max_concurrent limit is reached.
        
        Returns:
            True when slot is acquired
        """
        self._semaphore.acquire()
        with self._lock:
            self._active_count += 1
            self._total_count += 1
        return True
    
    def release(self) -> None:
        """Release a slot."""
        with self._lock:
            self._active_count -= 1
        self._semaphore.release()
    
    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, *args):
        self.release()
    
    @property
    def active_count(self) -> int:
        """Number of currently active operations."""
        return self._active_count
    
    @property
    def total_count(self) -> int:
        """Total number of operations processed."""
        return self._total_count


# Global limiters
_async_limiter: Optional[ConcurrencyLimiter] = None
_sync_limiter: Optional[SyncConcurrencyLimiter] = None


def get_async_limiter(max_concurrent: int = 5) -> ConcurrencyLimiter:
    """Get or create global async concurrency limiter."""
    global _async_limiter
    if _async_limiter is None:
        _async_limiter = ConcurrencyLimiter(max_concurrent)
    return _async_limiter


def get_sync_limiter(max_concurrent: int = 5) -> SyncConcurrencyLimiter:
    """Get or create global sync concurrency limiter."""
    global _sync_limiter
    if _sync_limiter is None:
        _sync_limiter = SyncConcurrencyLimiter(max_concurrent)
    return _sync_limiter


def configure_concurrency(max_concurrent: int = 5) -> tuple:
    """Configure global concurrency limiters.
    
    Args:
        max_concurrent: Maximum concurrent operations
        
    Returns:
        Tuple of (async_limiter, sync_limiter)
    """
    global _async_limiter, _sync_limiter
    _async_limiter = ConcurrencyLimiter(max_concurrent)
    _sync_limiter = SyncConcurrencyLimiter(max_concurrent)
    return _async_limiter, _sync_limiter

# File: javinizer/http/retry.py
"""Retry logic with exponential backoff for HTTP requests"""

import time
import functools
from dataclasses import dataclass, field
from typing import Callable, TypeVar, Optional, Any

from javinizer.logger import get_logger

logger = get_logger(__name__)

# Default retryable HTTP status codes
DEFAULT_RETRYABLE_STATUS_CODES = [429, 500, 502, 503, 504]


@dataclass
class RetryConfig:
    """Configuration for HTTP retry behavior.
    
    Attributes:
        max_retries: Maximum number of retry attempts (0 = no retries)
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay cap in seconds
        exponential_base: Base for exponential backoff calculation
        retryable_status_codes: HTTP status codes that trigger retry
        jitter_enabled: Whether to add random jitter (disabled by default for determinism)
    """
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    retryable_status_codes: list[int] = field(
        default_factory=lambda: DEFAULT_RETRYABLE_STATUS_CODES.copy()
    )
    jitter_enabled: bool = False  # Disabled for determinism

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given retry attempt.
        
        Args:
            attempt: Retry attempt number (0-indexed)
            
        Returns:
            Delay in seconds before next retry
        """
        delay = self.initial_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


class RetryableError(Exception):
    """Exception that indicates the operation should be retried."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


T = TypeVar('T')


def with_retry(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that adds retry logic with exponential backoff.
    
    Args:
        config: RetryConfig instance (uses defaults if None)
        on_retry: Optional callback(attempt, exception, delay) called before each retry
        
    Returns:
        Decorated function with retry behavior
        
    Example:
        @with_retry(RetryConfig(max_retries=3))
        def fetch_data(url: str) -> Response:
            return client.get(url)
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except RetryableError as e:
                    last_exception = e
                    if attempt < config.max_retries:
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                            f"after {delay:.1f}s (status={e.status_code})"
                        )
                        if on_retry:
                            on_retry(attempt, e, delay)
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Max retries ({config.max_retries}) exceeded for {func.__name__}"
                        )
                except Exception as e:
                    # Non-retryable exception, raise immediately
                    raise
            
            # If we exhausted retries, raise the last exception
            if last_exception:
                raise last_exception
            
            # Should never reach here, but satisfy type checker
            raise RuntimeError("Unexpected retry loop exit")
        
        return wrapper
    return decorator


def is_retryable_status(status_code: int, config: Optional[RetryConfig] = None) -> bool:
    """Check if a status code should trigger a retry.
    
    Args:
        status_code: HTTP status code
        config: RetryConfig (uses defaults if None)
        
    Returns:
        True if the status code is retryable
    """
    if config is None:
        config = RetryConfig()
    return status_code in config.retryable_status_codes

# File: tests/test_retry.py
"""Tests for HTTP retry logic module"""

import pytest

from javinizer.http.retry import (
    RetryConfig,
    RetryableError,
    with_retry,
    is_retryable_status,
)


class TestRetryConfig:
    """Test RetryConfig dataclass"""

    def test_default_values(self):
        """Test default configuration values"""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 2.0
        assert 429 in config.retryable_status_codes
        assert 500 in config.retryable_status_codes

    def test_custom_values(self):
        """Test custom configuration"""
        config = RetryConfig(
            max_retries=5,
            initial_delay=0.5,
            max_delay=60.0,
        )
        assert config.max_retries == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 60.0

    def test_calculate_delay_exponential(self):
        """Test exponential backoff delay calculation"""
        config = RetryConfig(initial_delay=1.0, exponential_base=2.0)

        assert config.calculate_delay(0) == 1.0  # 1 * 2^0
        assert config.calculate_delay(1) == 2.0  # 1 * 2^1
        assert config.calculate_delay(2) == 4.0  # 1 * 2^2
        assert config.calculate_delay(3) == 8.0  # 1 * 2^3

    def test_calculate_delay_respects_max(self):
        """Test that delay is capped at max_delay"""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=5.0,
        )

        assert config.calculate_delay(0) == 1.0
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(2) == 4.0
        assert config.calculate_delay(3) == 5.0  # Capped
        assert config.calculate_delay(10) == 5.0  # Still capped


class TestWithRetryDecorator:
    """Test with_retry decorator"""

    def test_success_no_retry(self):
        """Test function succeeds on first attempt"""
        call_count = 0

        @with_retry(RetryConfig(max_retries=3))
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_retryable_error(self):
        """Test function retries on RetryableError"""
        call_count = 0
        config = RetryConfig(max_retries=3, initial_delay=0.01)

        @with_retry(config)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableError("temporary failure", status_code=500)
            return "success"

        result = failing_func()
        assert result == "success"
        assert call_count == 3

    def test_max_retries_exceeded(self):
        """Test that max retries raises exception"""
        call_count = 0
        config = RetryConfig(max_retries=2, initial_delay=0.01)

        @with_retry(config)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise RetryableError("always fails", status_code=500)

        with pytest.raises(RetryableError):
            always_fails()

        assert call_count == 3  # Initial + 2 retries

    def test_non_retryable_exception_not_caught(self):
        """Test that non-RetryableError is raised immediately"""
        call_count = 0
        config = RetryConfig(max_retries=3, initial_delay=0.01)

        @with_retry(config)
        def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            raises_value_error()

        assert call_count == 1  # Only called once

    def test_on_retry_callback(self):
        """Test on_retry callback is called"""
        retry_attempts = []
        config = RetryConfig(max_retries=2, initial_delay=0.01)

        def on_retry_callback(attempt, exc, delay):
            retry_attempts.append((attempt, exc.status_code, delay))

        @with_retry(config, on_retry=on_retry_callback)
        def fails_twice():
            if len(retry_attempts) < 2:
                raise RetryableError("temp", status_code=503)
            return "done"

        result = fails_twice()
        assert result == "done"
        assert len(retry_attempts) == 2
        assert retry_attempts[0][1] == 503
        assert retry_attempts[1][1] == 503


class TestIsRetryableStatus:
    """Test is_retryable_status helper"""

    def test_default_retryable_codes(self):
        """Test default retryable status codes"""
        assert is_retryable_status(429) is True
        assert is_retryable_status(500) is True
        assert is_retryable_status(502) is True
        assert is_retryable_status(503) is True
        assert is_retryable_status(504) is True

    def test_non_retryable_codes(self):
        """Test non-retryable status codes"""
        assert is_retryable_status(200) is False
        assert is_retryable_status(400) is False
        assert is_retryable_status(401) is False
        assert is_retryable_status(404) is False

    def test_custom_config(self):
        """Test with custom retryable codes"""
        config = RetryConfig(retryable_status_codes=[418, 503])
        assert is_retryable_status(418, config) is True
        assert is_retryable_status(503, config) is True
        assert is_retryable_status(500, config) is False

from __future__ import annotations

import time

import pytest

from ai.backend.common.resilience.policies.retry import (
    BackoffStrategy,
    ResilienceRetryError,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.resilience.resilience import Resilience


class TestRetryPolicy:
    @pytest.mark.asyncio
    async def test_success_without_retry(self) -> None:
        """Test that successful operations don't trigger retries."""
        call_count = 0

        @Resilience(policies=[RetryPolicy(RetryArgs(max_retries=3))]).apply()
        async def successful_operation() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_operation()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self) -> None:
        """Test that transient failures trigger retries until success."""
        call_count = 0

        @Resilience(policies=[RetryPolicy(RetryArgs(max_retries=5, retry_delay=0.01))]).apply()
        async def eventually_successful_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Transient error")
            return "success"

        result = await eventually_successful_operation()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhaustion(self) -> None:
        """Test that retries are exhausted and final exception is raised."""
        call_count = 0

        @Resilience(policies=[RetryPolicy(RetryArgs(max_retries=3, retry_delay=0.01))]).apply()
        async def always_failing_operation() -> str:
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent error")

        with pytest.raises(ConnectionError, match="Persistent error"):
            await always_failing_operation()

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_non_retryable_exception(self) -> None:
        """Test that non-retryable exceptions are not retried."""
        call_count = 0

        @Resilience(
            policies=[
                RetryPolicy(
                    RetryArgs(max_retries=3, non_retryable_exceptions=(ResilienceRetryError,))
                )
            ]
        ).apply()
        async def operation_with_non_retryable_error() -> str:
            nonlocal call_count
            call_count += 1
            raise ResilienceRetryError("Non-retryable error")

        with pytest.raises(ResilienceRetryError, match="Non-retryable error"):
            await operation_with_non_retryable_error()

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_fixed_backoff_strategy(self) -> None:
        """Test that fixed backoff strategy uses consistent delay."""
        call_count = 0

        @Resilience(
            policies=[
                RetryPolicy(
                    RetryArgs(
                        max_retries=5, retry_delay=0.1, backoff_strategy=BackoffStrategy.FIXED
                    )
                )
            ]
        ).apply()
        async def eventually_successful_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Transient error")
            return "success"

        start_time = time.perf_counter()
        result = await eventually_successful_operation()
        elapsed_time = time.perf_counter() - start_time

        assert result == "success"
        assert call_count == 3
        # 2 retries with 0.1s fixed delay each = ~0.2s minimum
        assert elapsed_time >= 0.2

    @pytest.mark.asyncio
    async def test_exponential_backoff_strategy(self) -> None:
        """Test that exponential backoff strategy increases delay."""
        call_count = 0

        @Resilience(
            policies=[
                RetryPolicy(
                    RetryArgs(
                        max_retries=5,
                        retry_delay=0.1,
                        backoff_strategy=BackoffStrategy.EXPONENTIAL,
                        max_delay=1.0,
                    )
                )
            ]
        ).apply()
        async def eventually_successful_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Transient error")
            return "success"

        start_time = time.perf_counter()
        result = await eventually_successful_operation()
        elapsed_time = time.perf_counter() - start_time

        assert result == "success"
        assert call_count == 3
        # First retry: 0.1s, second retry: 0.2s = ~0.3s minimum
        assert elapsed_time >= 0.3

    @pytest.mark.asyncio
    async def test_max_delay_cap(self) -> None:
        """Test that exponential backoff respects max_delay."""
        call_count = 0

        @Resilience(
            policies=[
                RetryPolicy(
                    RetryArgs(
                        max_retries=5,
                        retry_delay=0.1,
                        backoff_strategy=BackoffStrategy.EXPONENTIAL,
                        max_delay=0.15,  # Cap delays at 0.15s
                    )
                )
            ]
        ).apply()
        async def eventually_successful_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise ConnectionError("Transient error")
            return "success"

        start_time = time.perf_counter()
        result = await eventually_successful_operation()
        elapsed_time = time.perf_counter() - start_time

        assert result == "success"
        assert call_count == 4
        # All delays capped at 0.15s, 3 retries = ~0.3-0.45s
        # First retry: 0.1s, second: min(0.2, 0.15) = 0.15s, third: min(0.4, 0.15) = 0.15s
        # Total: 0.1 + 0.15 + 0.15 = 0.4s (but allow some tolerance)
        assert elapsed_time >= 0.3
        # Should not exceed much more since delays are capped
        assert elapsed_time < 1.0

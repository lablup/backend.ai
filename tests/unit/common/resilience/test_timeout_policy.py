from __future__ import annotations

import asyncio

import pytest

from ai.backend.common.resilience.policies.timeout import (
    ResilienceTimeoutError,
    TimeoutArgs,
    TimeoutPolicy,
)
from ai.backend.common.resilience.resilience import Resilience


class TestTimeoutPolicy:
    @pytest.mark.asyncio
    async def test_success_within_timeout(self) -> None:
        """Test that operations completing within timeout succeed."""

        @Resilience(policies=[TimeoutPolicy(TimeoutArgs(timeout=1.0))]).apply()
        async def quick_operation() -> str:
            await asyncio.sleep(0.1)
            return "success"

        result = await quick_operation()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_timeout_exceeded(self) -> None:
        """Test that operations exceeding timeout raise ResilienceTimeoutError."""

        @Resilience(policies=[TimeoutPolicy(TimeoutArgs(timeout=0.1))]).apply()
        async def slow_operation() -> str:
            await asyncio.sleep(1.0)
            return "success"

        with pytest.raises(ResilienceTimeoutError, match="Operation exceeded timeout"):
            await slow_operation()

    @pytest.mark.asyncio
    async def test_timeout_with_exception(self) -> None:
        """Test that exceptions within timeout are propagated correctly."""

        @Resilience(policies=[TimeoutPolicy(TimeoutArgs(timeout=1.0))]).apply()
        async def failing_operation() -> str:
            await asyncio.sleep(0.1)
            raise ValueError("Operation failed")

        with pytest.raises(ValueError, match="Operation failed"):
            await failing_operation()

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

import pytest

from ai.backend.common.resilience.policy import Policy
from ai.backend.common.resilience.resilience import Resilience

P = ParamSpec("P")
R = TypeVar("R")


class TestPolicyComposition:
    @pytest.mark.asyncio
    async def test_single_policy_execution(self) -> None:
        """Test that a single policy's execute is called correctly."""
        execute_called = False

        class MockPolicy(Policy):
            async def execute(
                self,
                next_call: Callable[P, Awaitable[R]],
                *args: P.args,
                **kwargs: P.kwargs,
            ) -> R:
                nonlocal execute_called
                execute_called = True
                return await next_call(*args, **kwargs)

        mock_policy = MockPolicy()

        @Resilience(policies=[mock_policy]).apply()
        async def operation() -> str:
            return "success"

        result = await operation()

        assert result == "success"
        assert execute_called

    @pytest.mark.asyncio
    async def test_multiple_policies_execution_order(self) -> None:
        """Test that multiple policies are executed in correct order."""
        execution_order: list[str] = []

        class MockPolicy1(Policy):
            async def execute(
                self,
                next_call: Callable[P, Awaitable[R]],
                *args: P.args,
                **kwargs: P.kwargs,
            ) -> R:
                execution_order.append("policy1_before")
                result = await next_call(*args, **kwargs)
                execution_order.append("policy1_after")
                return result

        class MockPolicy2(Policy):
            async def execute(
                self,
                next_call: Callable[P, Awaitable[R]],
                *args: P.args,
                **kwargs: P.kwargs,
            ) -> R:
                execution_order.append("policy2_before")
                result = await next_call(*args, **kwargs)
                execution_order.append("policy2_after")
                return result

        class MockPolicy3(Policy):
            async def execute(
                self,
                next_call: Callable[P, Awaitable[R]],
                *args: P.args,
                **kwargs: P.kwargs,
            ) -> R:
                execution_order.append("policy3_before")
                result = await next_call(*args, **kwargs)
                execution_order.append("policy3_after")
                return result

        @Resilience(policies=[MockPolicy1(), MockPolicy2(), MockPolicy3()]).apply()
        async def operation() -> str:
            execution_order.append("operation")
            return "success"

        result = await operation()

        assert result == "success"
        # Policies should execute in order, then unwind in reverse order
        assert execution_order == [
            "policy1_before",
            "policy2_before",
            "policy3_before",
            "operation",
            "policy3_after",
            "policy2_after",
            "policy1_after",
        ]

    @pytest.mark.asyncio
    async def test_exception_propagation_through_policies(self) -> None:
        """Test that exceptions propagate correctly through nested policies."""
        execution_order: list[str] = []

        class MockPolicy1(Policy):
            async def execute(
                self,
                next_call: Callable[P, Awaitable[R]],
                *args: P.args,
                **kwargs: P.kwargs,
            ) -> R:
                execution_order.append("policy1_before")
                try:
                    return await next_call(*args, **kwargs)
                finally:
                    execution_order.append("policy1_after")

        class MockPolicy2(Policy):
            async def execute(
                self,
                next_call: Callable[P, Awaitable[R]],
                *args: P.args,
                **kwargs: P.kwargs,
            ) -> R:
                execution_order.append("policy2_before")
                try:
                    return await next_call(*args, **kwargs)
                finally:
                    execution_order.append("policy2_after")

        @Resilience(policies=[MockPolicy1(), MockPolicy2()]).apply()
        async def failing_operation() -> str:
            execution_order.append("operation")
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await failing_operation()

        # All policies should execute before and after even with exception
        assert execution_order == [
            "policy1_before",
            "policy2_before",
            "operation",
            "policy2_after",
            "policy1_after",
        ]

    @pytest.mark.asyncio
    async def test_empty_policy_list(self) -> None:
        """Test that operations work with no policies applied."""

        @Resilience(policies=[]).apply()
        async def operation() -> str:
            return "success"

        result = await operation()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_policy_exception_handling(self) -> None:
        """Test that exceptions from policies themselves are propagated."""

        class FailingMockPolicy(Policy):
            async def execute(
                self,
                next_call: Callable[P, Awaitable[R]],
                *args: P.args,
                **kwargs: P.kwargs,
            ) -> R:
                raise RuntimeError("Policy error")

        @Resilience(policies=[FailingMockPolicy()]).apply()
        async def operation() -> str:
            return "success"

        with pytest.raises(RuntimeError, match="Policy error"):
            await operation()

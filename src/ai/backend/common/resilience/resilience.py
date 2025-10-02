from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable, Iterable
from contextlib import AsyncExitStack
from typing import ParamSpec, TypeVar

from .policy import Policy

P = ParamSpec("P")
R = TypeVar("R")


class Resilience:
    """
    Main executor that chains multiple resilience policies and applies them as a decorator.

    Policies are executed in the order they are provided, with each policy
    wrapping the next one in the chain using async context managers.

    Example:
        >>> resilience = Resilience(policies=[
        ...     MetricPolicy(domain=DomainType.CLIENT, layer=LayerType.AGENT_CLIENT),
        ...     CircuitBreakerPolicy(failure_threshold=5),
        ...     RetryPolicy(max_retries=3, backoff_strategy=BackoffStrategy.EXPONENTIAL),
        ... ])
        >>> @resilience.apply()
        ... async def my_function():
        ...     return await external_service_call()
    """

    _policies: Iterable[Policy]

    def __init__(self, policies: Iterable[Policy]) -> None:
        """
        Initialize Resilience with a list of policies.

        Args:
            policies: Iterable of policies to apply, in execution order
        """
        self._policies = policies

    def apply(self) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
        """
        Create a decorator that applies all policies to an async function.

        Returns:
            A decorator function that wraps the target function with all policies
        """

        def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
            @functools.wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                # Use AsyncExitStack to manage nested async context managers
                async with AsyncExitStack() as stack:
                    # Enter all policy contexts in order
                    for policy in self._policies:
                        await stack.enter_async_context(policy.execute())

                    # Execute the actual function within all policy contexts
                    return await func(*args, **kwargs)

            return wrapper

        return decorator

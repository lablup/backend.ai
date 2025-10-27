from __future__ import annotations

import functools
from collections.abc import Callable, Coroutine, Iterable
from contextvars import ContextVar
from typing import Any, Optional, ParamSpec, TypeVar

from .policy import Policy

P = ParamSpec("P")
R = TypeVar("R")

# Context variable to store the current operation name
_current_operation: ContextVar[Optional[str]] = ContextVar("resilience_operation", default=None)


def get_current_operation() -> Optional[str]:
    """
    Get the current operation name from context.

    This is used by policies (like MetricPolicy) to access the operation name
    without requiring it to be passed through the constructor.

    Returns:
        The current operation name, or None if not set
    """
    return _current_operation.get()


class Resilience:
    """
    Main executor that chains multiple resilience policies and applies them as a decorator.

    Policies are executed in the order they are provided, with each policy
    wrapping the next one in the chain using the middleware pattern.

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

    def apply(
        self,
    ) -> Callable[[Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]]:
        """
        Create a decorator that applies all policies to an async function.

        The decorator sets the operation name in context before executing policies,
        allowing policies to access it via get_current_operation().

        Returns:
            A decorator function that wraps the target function with all policies
        """

        def decorator(
            func: Callable[P, Coroutine[Any, Any, R]],
        ) -> Callable[P, Coroutine[Any, Any, R]]:
            @functools.wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                # Set the current operation name in context
                token = _current_operation.set(func.__name__)
                try:
                    # Build middleware chain from policies
                    next_call: Callable[P, Coroutine[Any, Any, R]] = func

                    # Wrap function with policies in reverse order
                    # so that first policy in list becomes outermost wrapper
                    for policy in reversed(list(self._policies)):

                        def make_wrapper(
                            p: Policy, next_fn: Callable[P, Coroutine[Any, Any, R]]
                        ) -> Callable[P, Coroutine[Any, Any, R]]:
                            async def policy_call(
                                *inner_args: P.args, **inner_kwargs: P.kwargs
                            ) -> R:
                                return await p.execute(next_fn, *inner_args, **inner_kwargs)

                            return policy_call

                        next_call = make_wrapper(policy, next_call)

                    # Execute the chain
                    return await next_call(*args, **kwargs)
                finally:
                    # Reset context variable
                    _current_operation.reset(token)

            return wrapper

        return decorator

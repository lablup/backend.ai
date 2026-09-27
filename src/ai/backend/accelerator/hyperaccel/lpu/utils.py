import functools
from collections.abc import Callable
from typing import TypeVar

from ai.backend.common.asyncio import run_in_executor_with_context

T = TypeVar("T")


async def blocking_job[T](fn: Callable[..., T], *args, **kwargs) -> T:
    return await run_in_executor_with_context(
        None,
        functools.partial(fn, *args, **kwargs),
    )

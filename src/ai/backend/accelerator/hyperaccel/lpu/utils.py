import asyncio
import functools
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


async def blocking_job[T](fn: Callable[..., T], *args, **kwargs) -> T:
    return await asyncio.get_running_loop().run_in_executor(
        None,
        functools.partial(fn, *args, **kwargs),
    )

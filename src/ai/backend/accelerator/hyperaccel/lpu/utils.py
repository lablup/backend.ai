import asyncio
import functools
from typing import Callable, TypeVar

T = TypeVar("T")


async def blocking_job(fn: Callable[..., T], *args, **kwargs) -> T:
    return await asyncio.get_running_loop().run_in_executor(
        None,
        functools.partial(fn, *args, **kwargs),
    )

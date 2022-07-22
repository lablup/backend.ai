from __future__ import annotations

import asyncio
import socket
from contextlib import closing
from typing import TYPE_CHECKING, Callable, Mapping, TypeVar

import aiohttp
from async_timeout import timeout as _timeout

if TYPE_CHECKING:
    import yarl

__all__ = (
    "find_free_port",
    "curl",
)

T = TypeVar("T")


async def curl(
    url: str | yarl.URL,
    default_value: str | T | Callable[[], str | T],
    params: Mapping[str, str] = None,
    headers: Mapping[str, str] = None,
    timeout: float = 0.2,
) -> str | T:
    """
    A simple curl-like helper function that uses aiohttp to fetch some string/data
    from a remote HTTP endpoint.
    """
    try:
        async with aiohttp.ClientSession() as sess:
            async with _timeout(timeout):
                async with sess.get(url, params=params, headers=headers) as resp:
                    assert resp.status == 200
                    body = await resp.text()
                    return body.strip()
    except (asyncio.TimeoutError, aiohttp.ClientError, AssertionError):
        if callable(default_value):
            return default_value()
        return default_value


def find_free_port(bind_addr: str = "127.0.0.1") -> int:
    """
    Find a freely available TCP port in the current host.
    Note that since under certain conditions this may have races.
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind((bind_addr, 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

from __future__ import annotations

import asyncio
import socket
from contextlib import closing
from typing import TYPE_CHECKING, Callable, Mapping, Optional, TypeVar, overload

import aiohttp

if TYPE_CHECKING:
    import yarl

__all__ = (
    "find_free_port",
    "curl",
)

T = TypeVar("T")


@overload
async def curl(
    url: str | yarl.URL,
    default_value: None = None,
    *,
    params: Optional[Mapping[str, str]] = None,
    headers: Optional[Mapping[str, str]] = None,
    timeout: float = 0.2,
) -> Optional[str]: ...


@overload
async def curl(
    url: str | yarl.URL,
    default_value: str | Callable[[], str],
    *,
    params: Optional[Mapping[str, str]] = None,
    headers: Optional[Mapping[str, str]] = None,
    timeout: float = 0.2,
) -> str: ...


async def curl(
    url: str | yarl.URL,
    default_value: str | Callable[[], str] | None = None,
    *,
    params: Optional[Mapping[str, str]] = None,
    headers: Optional[Mapping[str, str]] = None,
    timeout: float = 0.2,
) -> Optional[str]:
    """
    A simple curl-like helper function that uses aiohttp to fetch some string/data
    from a remote HTTP endpoint.
    """
    try:
        async with aiohttp.ClientSession(
            raise_for_status=True,
            timeout=aiohttp.ClientTimeout(connect=timeout),
        ) as sess:
            async with sess.get(url, params=params, headers=headers) as resp:
                body = await resp.text()
                result = body.strip()
                return result
    except (asyncio.TimeoutError, aiohttp.ClientError):
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

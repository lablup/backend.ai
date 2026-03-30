from __future__ import annotations

import socket
from collections.abc import Callable, Mapping
from contextlib import closing
from typing import TYPE_CHECKING, TypeVar, overload

import aiohttp

if TYPE_CHECKING:
    import yarl

__all__ = (
    "curl",
    "find_free_port",
)

T = TypeVar("T")


@overload
async def curl(
    url: str | yarl.URL,
    default_value: None = None,
    *,
    params: Mapping[str, str] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout_seconds: float = 0.2,
) -> str | None: ...


@overload
async def curl(
    url: str | yarl.URL,
    default_value: str | Callable[[], str],
    *,
    params: Mapping[str, str] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout_seconds: float = 0.2,
) -> str: ...


async def curl(
    url: str | yarl.URL,
    default_value: str | Callable[[], str] | None = None,
    *,
    params: Mapping[str, str] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout_seconds: float = 0.2,
) -> str | None:
    """
    A simple curl-like helper function that uses aiohttp to fetch some string/data
    from a remote HTTP endpoint.
    """
    try:
        async with (
            aiohttp.ClientSession(
                raise_for_status=True,
                timeout=aiohttp.ClientTimeout(connect=timeout_seconds),
            ) as sess,
            sess.get(url, params=params, headers=headers) as resp,
        ):
            body = await resp.text()
            return body.strip()
    except (TimeoutError, aiohttp.ClientError):
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
        result: int = s.getsockname()[1]
        return result

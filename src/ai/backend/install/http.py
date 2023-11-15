from __future__ import annotations

from contextlib import asynccontextmanager as actxmgr
from pathlib import Path
from typing import AsyncIterator

import aiohttp
from textual.widgets import ProgressBar


@actxmgr
async def request(
    method: str,
    url: str,
    **kwargs,
) -> AsyncIterator[aiohttp.ClientResponse]:
    connector = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=connector) as s:
        async with s.request(method, url, **kwargs) as r:
            yield r


@actxmgr
async def request_unix(
    method: str,
    socket_path: str,
    url: str,
    **kwargs,
) -> AsyncIterator[aiohttp.ClientResponse]:
    connector = aiohttp.UnixConnector(socket_path)
    async with aiohttp.ClientSession(connector=connector) as s:
        async with s.request(method, url, **kwargs) as r:
            yield r


async def wget(
    url: str,
    target_path: Path,
    progress: ProgressBar | None = None,
) -> None:
    chunk_size = 16384
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "wb") as out:
        async with request("GET", url, raise_for_status=True) as r:
            if progress is not None and r.content_length:
                progress.update(total=r.content_length)
            while True:
                chunk = await r.content.read(chunk_size)
                if not chunk:
                    break
                out.write(chunk)
                if progress is not None:
                    progress.advance(len(chunk))

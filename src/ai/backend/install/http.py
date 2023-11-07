import asyncio
from contextlib import asynccontextmanager as actxmgr
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


async def wget(url: str, progress: ProgressBar) -> None:
    chunk_size = 16384
    async with request("GET", url, raise_for_status=True) as r:
        progress.total = r.content_length
        print(f"wget {url=} {r.history=} {progress.total=}")
        while True:
            chunk = await r.content.read(chunk_size)
            if not chunk:
                break
            await asyncio.sleep(0.3)
            progress.advance(len(chunk))

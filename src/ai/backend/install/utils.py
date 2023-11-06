from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator

import aiohttp


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

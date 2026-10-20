from __future__ import annotations

import asyncio
from http import HTTPStatus

from aiohttp import web


class ServerDrainNotifier:
    _draining: bool

    def __init__(self) -> None:
        self._draining = False

    def notify_draining(self) -> None:
        self._draining = True

    async def drain(self, drain_period: float) -> None:
        self.notify_draining()
        await asyncio.sleep(drain_period)

    @property
    def is_draining(self) -> bool:
        return self._draining

    async def on_response_prepare(self, request: web.Request, response: web.StreamResponse) -> None:
        if self.is_draining and response.status != HTTPStatus.SWITCHING_PROTOCOLS:
            response.force_close()
            response.headers["Connection"] = "close"

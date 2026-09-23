from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus

from aiohttp import web


@dataclass
class ShutdownState:
    draining: bool = False

    async def on_response_prepare(self, request: web.Request, response: web.StreamResponse) -> None:
        if self.draining and response.status != HTTPStatus.SWITCHING_PROTOCOLS:
            response.force_close()
            response.headers["Connection"] = "close"

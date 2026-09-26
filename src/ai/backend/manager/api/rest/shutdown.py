from __future__ import annotations

from http import HTTPStatus

from aiohttp import web


class ServerDrainNotifier:
    _draining: bool

    def __init__(self) -> None:
        self._draining = False

    def notify_draining(self) -> None:
        self._draining = True

    @property
    def is_draining(self) -> bool:
        return self._draining

    async def on_response_prepare(self, request: web.Request, response: web.StreamResponse) -> None:
        if self.is_draining and response.status != HTTPStatus.SWITCHING_PROTOCOLS:
            response.force_close()
            response.headers["Connection"] = "close"

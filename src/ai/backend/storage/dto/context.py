from __future__ import annotations

from typing import Self, override

from aiohttp import web
from pydantic import ConfigDict

from ai.backend.common.api_handlers import MiddlewareParam

from ..context import RootContext


class StorageRootCtx(MiddlewareParam):
    """Middleware parameter for accessing storage proxy RootContext."""

    root_ctx: RootContext

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        return cls(root_ctx=request.app["ctx"])

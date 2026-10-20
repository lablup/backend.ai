from __future__ import annotations

from typing import Self, override

from aiohttp import web
from pydantic import ConfigDict

from ai.backend.appproxy.worker.ingress.factory import IngressState
from ai.backend.common.api_handlers import MiddlewareParam


class IngressStateCtx(MiddlewareParam):
    ingress_state: IngressState

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        return cls(ingress_state=request.app["_root.context"].ingress_state)

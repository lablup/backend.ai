from __future__ import annotations

from typing import Self, override

from aiohttp import web
from pydantic import ConfigDict

from ai.backend.appproxy.coordinator.services.ingress import IngressService
from ai.backend.common.api_handlers import MiddlewareParam


class IngressServiceCtx(MiddlewareParam):
    ingress_service: IngressService

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        return cls(ingress_service=request.app["_root.context"].ingress_service)

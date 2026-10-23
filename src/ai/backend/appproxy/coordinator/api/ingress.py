from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus

import aiohttp_cors
from aiohttp import web

from ai.backend.appproxy.common.types import CORSOptions, WebMiddleware
from ai.backend.appproxy.coordinator.api.utils import auth_required
from ai.backend.appproxy.coordinator.dto.context import IngressServiceCtx
from ai.backend.common.api_handlers import APIResponse, BodyParam, api_handler
from ai.backend.common.dto.appproxy.v2.ingress.request import (
    IngressRemoveRequest,
    IngressUpsertRequest,
)


class IngressHandler:
    @api_handler
    async def upsert(
        self, ctx: IngressServiceCtx, body: BodyParam[IngressUpsertRequest]
    ) -> APIResponse:
        await ctx.ingress_service.upsert(body.parsed.ingresses)
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    @api_handler
    async def remove(
        self, ctx: IngressServiceCtx, body: BodyParam[IngressRemoveRequest]
    ) -> APIResponse:
        await ctx.ingress_service.remove(body.parsed.keys)
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "v2/ingress"
    handler = IngressHandler()
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    cors.add(add_route("POST", "/upsert", auth_required("manager")(handler.upsert)))
    cors.add(add_route("POST", "/remove", auth_required("manager")(handler.remove)))
    return app, []

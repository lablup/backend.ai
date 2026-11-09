from __future__ import annotations

import hmac
from collections.abc import Iterable
from http import HTTPStatus

from aiohttp import web

from ai.backend.appproxy.common.errors.http import AuthorizationFailed
from ai.backend.appproxy.common.types import (
    CORSOptions,
    IngressDeliveryMode,
    WebMiddleware,
    WebRequestHandler,
)
from ai.backend.appproxy.worker.config import IngressConfig
from ai.backend.appproxy.worker.dto.context import IngressConfigCtx, IngressStateCtx
from ai.backend.appproxy.worker.errors.ingress import IngressWriteNotSupportedError
from ai.backend.appproxy.worker.ingress.factory import IngressState
from ai.backend.appproxy.worker.ingress.validating import ValidatingIngressWriter
from ai.backend.appproxy.worker.types import RootContext
from ai.backend.common.api_handlers import APIResponse, BodyParam, api_handler
from ai.backend.common.dto.appproxy.v2.ingress.request import (
    IngressRemoveRequest,
    IngressReplaceRequest,
    IngressUpsertRequest,
)
from ai.backend.common.dto.appproxy.v2.ingress.response import IngressRevisionsResponse

TOKEN_HEADER = "X-BackendAI-Token"


@web.middleware
async def coordinator_auth_middleware(
    request: web.Request, handler: WebRequestHandler
) -> web.StreamResponse:
    root_ctx: RootContext = request.app["_root.context"]
    token = request.headers.get(TOKEN_HEADER, "")
    if not hmac.compare_digest(token, root_ctx.local_config.secrets.api_secret):
        raise AuthorizationFailed("Unauthorized access")
    return await handler(request)


class IngressHandler:
    @api_handler
    async def upsert(
        self,
        state_ctx: IngressStateCtx,
        config_ctx: IngressConfigCtx,
        body: BodyParam[IngressUpsertRequest],
    ) -> APIResponse:
        writer = self._writer(state_ctx.ingress_state, config_ctx.ingress_config)
        await writer.apply(body.parsed.ingresses)
        # The writer applies every ingress or raises, so each sent revision is the one held.
        response = IngressRevisionsResponse(
            revisions={
                ingress.frontend.key(): ingress.revision for ingress in body.parsed.ingresses
            }
        )
        return APIResponse.build(HTTPStatus.OK, response)

    @api_handler
    async def remove(
        self,
        state_ctx: IngressStateCtx,
        config_ctx: IngressConfigCtx,
        body: BodyParam[IngressRemoveRequest],
    ) -> APIResponse:
        writer = self._writer(state_ctx.ingress_state, config_ctx.ingress_config)
        await writer.remove(body.parsed.keys)
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    @api_handler
    async def replace(
        self,
        state_ctx: IngressStateCtx,
        config_ctx: IngressConfigCtx,
        body: BodyParam[IngressReplaceRequest],
    ) -> APIResponse:
        writer = self._writer(state_ctx.ingress_state, config_ctx.ingress_config)
        await writer.replace_all(body.parsed.ingresses)
        response = IngressRevisionsResponse(
            revisions={
                ingress.frontend.key(): ingress.revision for ingress in body.parsed.ingresses
            }
        )
        return APIResponse.build(HTTPStatus.OK, response)

    @api_handler
    async def revisions(self, state_ctx: IngressStateCtx) -> APIResponse:
        ingresses = await state_ctx.ingress_state.reader.get_all()
        response = IngressRevisionsResponse(
            revisions={ingress.frontend.key(): ingress.revision for ingress in ingresses}
        )
        return APIResponse.build(HTTPStatus.OK, response)

    def _writer(self, state: IngressState, config: IngressConfig) -> ValidatingIngressWriter:
        if config.delivery_mode != IngressDeliveryMode.API or state.writer is None:
            raise IngressWriteNotSupportedError
        return state.writer


def create_app(
    _default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application(middlewares=[coordinator_auth_middleware])
    app["prefix"] = "v2/ingress"
    handler = IngressHandler()
    app.router.add_route("POST", "/upsert", handler.upsert)
    app.router.add_route("POST", "/remove", handler.remove)
    app.router.add_route("POST", "/replace", handler.replace)
    app.router.add_route("GET", "/revisions", handler.revisions)
    return app, []

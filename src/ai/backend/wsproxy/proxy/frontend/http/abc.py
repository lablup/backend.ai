import logging
from typing import Generic

import aiohttp_jinja2
import jwt
from aiohttp import web

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.wsproxy.defs import RootContext
from ai.backend.wsproxy.exceptions import BackendError, InvalidCredentials
from ai.backend.wsproxy.proxy.backend.http import HTTPBackend
from ai.backend.wsproxy.types import (
    PERMIT_COOKIE_NAME,
    Circuit,
    InferenceAppInfo,
    InteractiveAppInfo,
    RouteInfo,
    TCircuitKey,
    WebRequestHandler,
)
from ai.backend.wsproxy.utils import ensure_json_serializable, is_permit_valid, mime_match

from ..abc import AbstractFrontend

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class AbstractHTTPFrontend(Generic[TCircuitKey], AbstractFrontend[HTTPBackend, TCircuitKey]):
    root_context: RootContext

    def ensure_credential(self, request: web.Request, circuit: Circuit) -> None:
        if circuit.open_to_public:
            return

        match circuit.app_info:
            case InteractiveAppInfo():
                permit_hash = request.cookies.get(PERMIT_COOKIE_NAME)
                if not permit_hash:
                    raise InvalidCredentials("E20004: Authorization cookie not provided")
                if not is_permit_valid(
                    self.root_context.local_config.wsproxy.permit_hash_key,
                    circuit.app_info.user_id,
                    permit_hash,
                ):
                    raise InvalidCredentials("E20005: Invalid authorization cookie")
            case InferenceAppInfo():
                auth_header = request.headers.get("Authorization")
                if not auth_header:
                    raise InvalidCredentials("E20006: Authorization header not provided")
                auth_type, auth_key = auth_header.split(" ", maxsplit=2)
                if auth_type == "BackendAI":
                    token = auth_key
                else:
                    raise InvalidCredentials(
                        f"E20007: Unsupported authorization method {auth_type}"
                    )

                try:
                    decoded = jwt.decode(
                        token,
                        key=self.root_context.local_config.wsproxy.jwt_encrypt_key,
                        algorithms=["HS256"],
                    )
                except jwt.PyJWTError as e:
                    raise InvalidCredentials from e

                if decoded.get("id") != circuit.id:
                    raise InvalidCredentials("E20008: Authorization token mismatch")

    async def initialize_backend(self, circuit: Circuit, routes: list[RouteInfo]) -> HTTPBackend:
        return HTTPBackend(routes, self.root_context, circuit)

    async def update_backend(self, backend: HTTPBackend, routes: list[RouteInfo]) -> HTTPBackend:
        backend.routes = routes
        return backend

    async def terminate_backend(self, backend: HTTPBackend) -> None:
        return

    async def proxy(self, request: web.Request) -> web.StreamResponse | web.WebSocketResponse:
        backend: HTTPBackend = request["backend"]

        if (
            request.headers.get("connection", "").lower() == "upgrade"
            and request.headers.get("upgrade", "").lower() == "websocket"
        ):
            return await backend.proxy_ws(request)
        else:
            return await backend.proxy_http(request)

    @web.middleware
    async def exception_middleware(
        self, request: web.Request, handler: WebRequestHandler
    ) -> web.StreamResponse:
        try:
            resp = await handler(request)
        except BackendError as ex:
            if ex.status_code == 500:
                log.exception("Internal server error raised inside handlers")
            if mime_match(
                request.headers.get("accept", "text/html"), "application/json", strict=True
            ):
                return web.json_response(
                    ensure_json_serializable(ex.body_dict),
                    status=ex.status_code,
                )
            else:
                return aiohttp_jinja2.render_template(
                    "error.jinja2",
                    request,
                    ex.body_dict,
                )
        return resp

    @web.middleware
    async def cors_middleware(
        self, request: web.Request, handler: WebRequestHandler
    ) -> web.StreamResponse:
        resp = await handler(request)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp

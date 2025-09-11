import logging
import time
from typing import Generic

import aiohttp_jinja2
import jwt
from aiohttp import web

from ai.backend.appproxy.common.defs import PERMIT_COOKIE_NAME
from ai.backend.appproxy.common.exceptions import BackendError, InvalidCredentials
from ai.backend.appproxy.common.types import RouteInfo, WebRequestHandler
from ai.backend.appproxy.common.utils import ensure_json_serializable, is_permit_valid, mime_match
from ai.backend.appproxy.worker.proxy.backend.http import HTTPBackend
from ai.backend.appproxy.worker.types import (
    Circuit,
    InferenceAppInfo,
    InteractiveAppInfo,
    RootContext,
    TCircuitKey,
)
from ai.backend.logging import BraceStyleAdapter

from ..base import BaseFrontend

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class BaseHTTPFrontend(Generic[TCircuitKey], BaseFrontend[HTTPBackend, TCircuitKey]):
    root_context: RootContext

    def ensure_credential(self, request: web.Request, circuit: Circuit) -> None:
        if circuit.open_to_public or request.method == "OPTIONS":
            return

        match circuit.app_info:
            case InteractiveAppInfo():
                permit_hash = request.cookies.get(PERMIT_COOKIE_NAME)
                if not permit_hash:
                    raise InvalidCredentials("E20004: Authorization cookie not provided")
                if not is_permit_valid(
                    self.root_context.local_config.permit_hash,
                    circuit.app_info.user_id,
                    permit_hash,
                ):
                    raise InvalidCredentials("E20005: Invalid authorization cookie")
            case InferenceAppInfo():
                auth_header = request.headers.get("Authorization")
                if not auth_header:
                    raise InvalidCredentials("E20006: Authorization header not provided")
                auth_type, _, auth_key = auth_header.partition(" ")
                if auth_type in ("BackendAI", "Bearer"):
                    token = auth_key
                else:
                    raise InvalidCredentials(
                        f"E20007: Unsupported authorization method {auth_type}"
                    )

                try:
                    decoded = jwt.decode(
                        token,
                        key=self.root_context.local_config.secrets.jwt_secret,
                        algorithms=["HS256"],
                    )
                except jwt.PyJWTError as e:
                    raise InvalidCredentials(f"E20008: Invalid authorization token ({e})") from e

                if decoded.get("id") != str(circuit.id):
                    raise InvalidCredentials("E20009: Authorization token mismatch")

    async def initialize_backend(self, circuit: Circuit, routes: list[RouteInfo]) -> HTTPBackend:
        return HTTPBackend(routes, self.root_context, circuit)

    async def update_backend(self, backend: HTTPBackend, routes: list[RouteInfo]) -> HTTPBackend:
        await backend.update_routes(routes)
        return backend

    async def terminate_backend(self, backend: HTTPBackend) -> None:
        await backend.close()

    async def list_inactive_circuits(self, threshold: int) -> list[Circuit]:
        now = time.time()
        return [
            self.circuits[key]
            for key, backend in self.backends.items()
            if (backend.last_used - now) >= threshold
        ]

    def _is_websocket_request(self, request: web.Request) -> bool:
        return (
            "upgrade" in request.headers.get("connection", "").lower()
            and request.headers.get("upgrade", "").lower() == "websocket"
        )

    async def proxy(self, request: web.Request) -> web.StreamResponse | web.WebSocketResponse:
        backend: HTTPBackend = request["backend"]

        if self._is_websocket_request(request):
            return await backend.proxy_ws(request)
        else:
            return await backend.proxy_http(request)

    async def exception_safe_handler_wrapper(
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
                    headers={"Access-Control-Allow-Origin": "*"},
                )
            else:
                return aiohttp_jinja2.render_template(
                    "error.jinja2",
                    request,
                    ex.body_dict,
                    status=ex.status_code,
                )
        return resp

    @web.middleware
    async def exception_middleware(
        self, request: web.Request, handler: WebRequestHandler
    ) -> web.StreamResponse:
        return await self.exception_safe_handler_wrapper(request, handler)

    @web.middleware
    async def metric_collector_middleware(
        self, request: web.Request, handler: WebRequestHandler
    ) -> web.StreamResponse:
        metrics = self.root_context.metrics
        response: web.StreamResponse | None = None

        remote = request.remote or ""
        start = time.monotonic()
        try:
            if not self._is_websocket_request(request):
                metrics.proxy.observe_downstream_http_request(remote=remote)
            response = await handler(request)
            return response
        finally:
            end = time.monotonic()
            if not self._is_websocket_request(request):
                metrics.proxy.observe_downstream_http_response(
                    remote=remote, duration=int(end - start)
                )

    async def append_cors_headers(
        self,
        request: web.Request,
        response: web.StreamResponse,
    ) -> None:
        response.headers["Access-Control-Allow-Origin"] = "*"
        allowed_headers = set()
        if _existing_headers := response.headers.get("Access-Control-Allow-Headers", ""):
            allowed_headers.update(_existing_headers.split(","))
        allowed_headers.add("authorization")
        response.headers["Access-Control-Allow-Headers"] = ",".join(allowed_headers)

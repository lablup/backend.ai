from __future__ import annotations

import asyncio
import base64
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any, Final, cast

import aiohttp
from aiohttp import ClientConnectionError, web
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from multidict import CIMultiDict
from trafaret import DataError

from ai.backend.client.exceptions import BackendAPIError, BackendClientError
from ai.backend.client.request import Request, RequestContent, SessionMode
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.web.session import STORAGE_KEY, extra_config_headers, get_session
from ai.backend.logging import BraceStyleAdapter
from ai.backend.web.clients.endpoint_pool import AcquiredEndpoint, HealthyEndpointPool
from ai.backend.web.config.unified import WebServerUnifiedConfig
from ai.backend.web.errors import InvalidAPIConfigurationError

from .auth import (
    fill_forwarding_hdrs_to_api_session,
    generate_jwt_token_for_session,
    get_anonymous_session,
    get_api_session,
)
from .stats import WebStats

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

HTTP_HEADERS_TO_FORWARD = [
    "Accept-Language",
    "Authorization",
]

CHUNK_SIZE: Final[int] = 64 * 1024

HOP_ONLY_HEADERS: Final[CIMultiDict[int]] = CIMultiDict([
    ("Connection", 1),
    ("Keep-Alive", 1),
    ("Proxy-Authenticate", 1),
    ("Proxy-Authorization", 1),
    ("TE", 1),
    ("Trailers", 1),
    ("Transfer-Encoding", 1),
    ("Upgrade", 1),
])


class WebSocketProxy:
    __slots__ = (
        "down_conn",
        "downstream_task",
        "up_conn",
        "upstream_buffer",
        "upstream_buffer_task",
    )

    up_conn: aiohttp.ClientWebSocketResponse
    down_conn: web.WebSocketResponse
    upstream_buffer: asyncio.Queue[tuple[str | bytes, aiohttp.WSMsgType]]
    upstream_buffer_task: asyncio.Task[Any] | None
    downstream_task: asyncio.Future[None] | None

    def __init__(
        self, up_conn: aiohttp.ClientWebSocketResponse, down_conn: web.WebSocketResponse
    ) -> None:
        self.up_conn = up_conn
        self.down_conn = down_conn
        self.upstream_buffer = asyncio.Queue()
        self.upstream_buffer_task = None
        self.downstream_task = None

    async def proxy(self) -> None:
        self.downstream_task = asyncio.ensure_future(self.downstream())
        await self.upstream()

    async def upstream(self) -> None:
        try:
            async for msg in self.down_conn:
                if msg.type in (aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.BINARY):
                    await self.send(msg.data, msg.type)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    log.error(
                        "WebSocketProxy: connection closed with exception {}",
                        self.up_conn.exception(),
                    )
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    break
            # here, client gracefully disconnected
        except asyncio.CancelledError:
            # here, client forcibly disconnected
            pass
        finally:
            await self.close_downstream()

    async def downstream(self) -> None:
        try:
            self.upstream_buffer_task = asyncio.create_task(self.consume_upstream_buffer())
            async for msg in self.up_conn:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self.down_conn.send_str(msg.data)
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    await self.down_conn.send_bytes(msg.data)
                elif msg.type == aiohttp.WSMsgType.CLOSED or msg.type == aiohttp.WSMsgType.ERROR:
                    break
            # here, server gracefully disconnected
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error("WebSocketProxy: unexpected error: {}", e)
        finally:
            await self.close_upstream()

    async def consume_upstream_buffer(self) -> None:
        try:
            while True:
                data, tp = await self.upstream_buffer.get()
                if not self.up_conn.closed:
                    if tp == aiohttp.WSMsgType.BINARY:
                        await self.up_conn.send_bytes(cast(bytes, data))
                    elif tp == aiohttp.WSMsgType.TEXT:
                        await self.up_conn.send_str(cast(str, data))
        except asyncio.CancelledError:
            pass

    async def send(self, msg: str, tp: aiohttp.WSMsgType) -> None:
        await self.upstream_buffer.put((msg, tp))

    async def close_downstream(self) -> None:
        if not self.down_conn.closed:
            await self.down_conn.close()

    async def close_upstream(self) -> None:
        if self.upstream_buffer_task is not None and not self.upstream_buffer_task.done():
            self.upstream_buffer_task.cancel()
            await self.upstream_buffer_task
        if not self.up_conn.closed:
            await self.up_conn.close()


def _decrypt_payload(endpoint: str, payload: bytes) -> bytes:
    iv, real_payload = payload.split(b":")
    key = (base64.b64encode(endpoint.encode("ascii")) + iv + iv)[:32]
    crypt = AES.new(key, AES.MODE_CBC, iv)
    b64p = base64.b64decode(real_payload)
    return unpad(crypt.decrypt(bytes(b64p)), 16)


@web.middleware
async def decrypt_payload(
    request: web.Request,
    handler: Callable[[web.Request], Awaitable[web.StreamResponse]],
) -> web.StreamResponse:
    config: WebServerUnifiedConfig = request.app["config"]
    try:
        request_headers = extra_config_headers.check(request.headers)
    except DataError as e:
        raise InvalidAPIParameters(f"Invalid request headers: {e}") from e
    secure_context = request_headers.get("X-BackendAI-Encoded", None)
    if secure_context:
        if not request.body_exists:  # designated as encrypted but has an empty payload
            request["payload"] = None
            return await handler(request)
        scheme = (
            str(config.service.force_endpoint_protocol)
            if config.service.force_endpoint_protocol
            else None
        )
        if scheme is None:
            scheme = request.scheme
        api_endpoint = f"{scheme}://{request.host}"
        payload = await request.read()
        request["payload"] = _decrypt_payload(api_endpoint, payload)
    else:
        # For all other requests without explicit encryption,
        # let the handler decide how to read the body.
        request["payload"] = None
    return await handler(request)


def _is_websocket_upgrade(request: web.Request) -> bool:
    return (
        request.headers.get("Upgrade", "").lower() == "websocket"
        and "upgrade" in request.headers.get("Connection", "").lower()
    )


def _strip_route_prefix(request: web.Request, *, prefix: str) -> str | None:
    """Resolve the upstream path from the incoming request.

    Routes that declare ``{path:.*$}`` populate ``match_info['path']`` directly;
    routes without a captured name fall back to stripping the URL prefix.
    """
    path = request.match_info.get("path", None)
    if path is not None:
        return path
    request_path = request.path
    if request_path.startswith(prefix):
        return request_path.removeprefix(prefix)
    return None


async def _run_proxy_request(
    frontend_rqst: web.Request,
    *,
    acquire_ctx: AbstractAsyncContextManager[AcquiredEndpoint],
    path: str | None,
    is_anonymous: bool,
    http_headers_to_forward_extra: Iterable[str] | None,
    log_prefix: str,
) -> web.StreamResponse:
    """Shared HTTP proxy body for the manager and pipeline handlers.

    ``acquire_ctx`` decides how to obtain the upstream endpoint: a real
    healthy-endpoint pool for the manager case, a static one-shot
    :func:`_direct_acquire` for the pipeline case.
    """
    stats: WebStats = frontend_rqst.app["stats"]
    stats.active_proxy_api_handlers.add(asyncio.current_task())  # type: ignore
    open_session = get_anonymous_session if is_anonymous else get_api_session
    try:
        async with acquire_ctx as acquired:
            api_session = await asyncio.shield(open_session(frontend_rqst, acquired))
            http_headers_to_forward_extra = http_headers_to_forward_extra or []
            async with api_session:
                # We perform request signing by ourselves using the HTTP session
                # data, but need to keep the client's version header so that
                # the final clients may perform its own API versioning support.
                backend_rqst_hdrs = extra_config_headers.check(frontend_rqst.headers)
                request_api_version = backend_rqst_hdrs.get("X-BackendAI-Version", None)
                secure_context = backend_rqst_hdrs.get("X-BackendAI-Encoded", None)
                decrypted_payload_length = 0
                content: RequestContent = None
                if frontend_rqst.body_exists:
                    if secure_context:
                        # Use the decrypted payload as request content
                        content = cast(bytes, frontend_rqst["payload"])
                        decrypted_payload_length = len(content)
                    else:
                        # Passthrough the streamed content
                        content = frontend_rqst.content
                fill_forwarding_hdrs_to_api_session(frontend_rqst, api_session)
                # Deliver cookie for token-based authentication.
                api_session.aiohttp_session.cookie_jar.update_cookies(frontend_rqst.cookies)
                backend_rqst = Request(
                    frontend_rqst.method,
                    path,
                    content,
                    params=frontend_rqst.query,
                    override_api_version=request_api_version,
                    session_mode=(
                        SessionMode.PROXY if api_session.proxy_mode else SessionMode.CLIENT
                    ),
                )
                if "Content-Type" in frontend_rqst.headers:
                    backend_rqst.content_type = frontend_rqst.content_type  # set for signing
                    backend_rqst.headers["Content-Type"] = frontend_rqst.headers[
                        "Content-Type"
                    ]  # preserve raw value
                if "Content-Length" in frontend_rqst.headers and not secure_context:
                    backend_rqst.headers["Content-Length"] = frontend_rqst.headers["Content-Length"]
                if "Content-Length" in frontend_rqst.headers and secure_context:
                    backend_rqst.headers["Content-Length"] = str(decrypted_payload_length)
                for key in {*HTTP_HEADERS_TO_FORWARD, *http_headers_to_forward_extra}:
                    # Prevent malicious or accidental modification of critical
                    # headers.
                    if key in backend_rqst.headers:
                        continue
                    if (value := frontend_rqst.headers.get(key)) is not None:
                        backend_rqst.headers[key] = value
                async with backend_rqst.fetch() as backend_resp:
                    frontend_resp_hdrs = {
                        key: value
                        for key, value in backend_resp.headers.items()
                        if key not in HOP_ONLY_HEADERS
                    }
                    frontend_resp = web.StreamResponse(
                        status=backend_resp.status,
                        reason=backend_resp.reason,
                        headers=frontend_resp_hdrs,
                    )
                    await frontend_resp.prepare(frontend_rqst)
                    try:
                        while True:
                            chunk = await backend_resp.read(CHUNK_SIZE)
                            if not chunk:
                                break
                            await frontend_resp.write(chunk)
                    finally:
                        await frontend_resp.write_eof()
                    return frontend_resp
    except asyncio.CancelledError:
        raise
    except BackendAPIError as e:
        return web.Response(
            body=json.dumps(e.data),
            content_type="application/problem+json",
            status=e.status,
            reason=e.reason,
        )
    except BackendClientError:
        log.exception("{}: BackendClientError", log_prefix)
        return web.HTTPBadGateway(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/bad-gateway",
                "title": "The proxy target server is inaccessible.",
            }),
            content_type="application/problem+json",
        )
    except ClientConnectionError:
        log.warning(
            "{}: ClientConnectionError - Client disconnected during proxying: method: {}, path: {}",
            log_prefix,
            frontend_rqst.method,
            path,
        )
        raise
    except web.HTTPException:
        # BackendAIError instances that double-inherit aiohttp.web.HTTPException
        # (e.g. ManagerConnectionUnavailable -> 503) must surface as their own
        # status code, not get rewritten to 500 by the generic catch below.
        raise
    except Exception:
        log.exception("{}: unexpected error", log_prefix)
        return web.HTTPInternalServerError(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/internal-server-error",
                "title": "Something has gone wrong.",
            }),
            content_type="application/problem+json",
        )


async def web_handler(
    frontend_rqst: web.Request,
    *,
    endpoint_pool: HealthyEndpointPool,
    is_anonymous: bool = False,
    http_headers_to_forward_extra: Iterable[str] | None = None,
) -> web.StreamResponse:
    if _is_websocket_upgrade(frontend_rqst):
        return await websocket_handler(
            frontend_rqst,
            endpoint_pool=endpoint_pool,
            is_anonymous=is_anonymous,
        )
    return await _run_proxy_request(
        frontend_rqst,
        acquire_ctx=endpoint_pool.acquire(),
        path=_strip_route_prefix(frontend_rqst, prefix="/func"),
        is_anonymous=is_anonymous,
        http_headers_to_forward_extra=http_headers_to_forward_extra,
        log_prefix="web_handler",
    )


async def pipeline_handler(
    frontend_rqst: web.Request,
    *,
    pipeline_endpoint: str,
    is_anonymous: bool = False,
    http_headers_to_forward_extra: Iterable[str] | None = None,
) -> web.StreamResponse:
    """Pass-through proxy for the pipeline service.

    Pipeline runs as a separate upstream and is not (yet) managed by a
    healthy-endpoint pool; the chosen endpoint comes straight from the
    webserver config. A follow-up will introduce a PipelineClientPool with
    the same shape as ManagerClientPool / ApolloRouterClientPool.
    """
    if _is_websocket_upgrade(frontend_rqst):
        return await websocket_handler(
            frontend_rqst,
            static_endpoint=pipeline_endpoint,
            is_anonymous=is_anonymous,
        )
    return await _run_proxy_request(
        frontend_rqst,
        acquire_ctx=_direct_acquire(pipeline_endpoint),
        path=_strip_route_prefix(frontend_rqst, prefix="/pipeline"),
        is_anonymous=is_anonymous,
        http_headers_to_forward_extra=http_headers_to_forward_extra,
        log_prefix="pipeline_handler",
    )


async def web_handler_with_jwt(
    frontend_rqst: web.Request,
    *,
    endpoint_pool: HealthyEndpointPool,
    http_headers_to_forward_extra: Iterable[str] | None = None,
) -> web.StreamResponse:
    """
    Web handler with JWT authentication for Apollo Router GraphQL requests.

    Generates a JWT token from the user's web session and adds it to the
    X-BackendAI-Token header when proxying through Apollo Router (a.k.a.
    Hive Router). Routes go through ``endpoint_pool`` so unhealthy Apollo
    Router replicas are skipped and connection failures are recorded.
    """
    # Generate JWT token from session (needed for both HTTP and WebSocket)
    jwt_token = await generate_jwt_token_for_session(frontend_rqst)
    log.debug(
        "web_handler_with_jwt: Generated JWT token (length: {}, path: {})",
        len(jwt_token) if jwt_token else 0,
        frontend_rqst.path,
    )

    # Check if this is a WebSocket upgrade request (for GraphQL subscriptions)
    if _is_websocket_upgrade(frontend_rqst):
        return await websocket_handler(
            frontend_rqst,
            endpoint_pool=endpoint_pool,
            is_anonymous=False,
            jwt_token=jwt_token,
        )

    stats: WebStats = frontend_rqst.app["stats"]
    stats.active_proxy_api_handlers.add(asyncio.current_task())  # type: ignore
    path = _strip_route_prefix(frontend_rqst, prefix="/func")
    http_headers_to_forward_extra = http_headers_to_forward_extra or []

    try:
        async with endpoint_pool.acquire() as acquired:
            api_session = await asyncio.shield(get_api_session(frontend_rqst, acquired))
            async with api_session:
                # Prepare backend request headers
                backend_rqst_hdrs = extra_config_headers.check(frontend_rqst.headers)
                request_api_version = backend_rqst_hdrs.get("X-BackendAI-Version", None)
                secure_context = backend_rqst_hdrs.get("X-BackendAI-Encoded", None)
                decrypted_payload_length = 0
                content: RequestContent = None

                if frontend_rqst.body_exists:
                    if secure_context:
                        # Use the decrypted payload as request content
                        content = cast(bytes, frontend_rqst["payload"])
                        decrypted_payload_length = len(content)
                    else:
                        # Passthrough the streamed content
                        content = frontend_rqst.content

                fill_forwarding_hdrs_to_api_session(frontend_rqst, api_session)

                # Deliver cookie for token-based authentication (if needed)
                api_session.aiohttp_session.cookie_jar.update_cookies(frontend_rqst.cookies)

                # Create backend request
                backend_rqst = Request(
                    frontend_rqst.method,
                    path,
                    content,
                    params=frontend_rqst.query,
                    override_api_version=request_api_version,
                    session_mode=(
                        SessionMode.PROXY if api_session.proxy_mode else SessionMode.CLIENT
                    ),
                )

                # Add JWT token to request header
                backend_rqst.headers["X-BackendAI-Token"] = jwt_token

                if "Content-Type" in frontend_rqst.headers:
                    backend_rqst.content_type = frontend_rqst.content_type  # set for signing
                    backend_rqst.headers["Content-Type"] = frontend_rqst.headers[
                        "Content-Type"
                    ]  # preserve raw value
                if "Content-Length" in frontend_rqst.headers and not secure_context:
                    backend_rqst.headers["Content-Length"] = frontend_rqst.headers["Content-Length"]
                if "Content-Length" in frontend_rqst.headers and secure_context:
                    backend_rqst.headers["Content-Length"] = str(decrypted_payload_length)

                for key in {*HTTP_HEADERS_TO_FORWARD, *http_headers_to_forward_extra}:
                    # Prevent malicious or accidental modification of critical headers.
                    if key in backend_rqst.headers:
                        continue
                    if (value := frontend_rqst.headers.get(key)) is not None:
                        backend_rqst.headers[key] = value

                # Fetch from backend and stream response
                async with backend_rqst.fetch() as backend_resp:
                    frontend_resp_hdrs = {
                        key: value
                        for key, value in backend_resp.headers.items()
                        if key not in HOP_ONLY_HEADERS
                    }
                    frontend_resp = web.StreamResponse(
                        status=backend_resp.status,
                        reason=backend_resp.reason,
                        headers=frontend_resp_hdrs,
                    )
                    await frontend_resp.prepare(frontend_rqst)
                    try:
                        while True:
                            chunk = await backend_resp.read(CHUNK_SIZE)
                            if not chunk:
                                break
                            await frontend_resp.write(chunk)
                    finally:
                        await frontend_resp.write_eof()
                    return frontend_resp
    except asyncio.CancelledError:
        raise
    except BackendAPIError as e:
        return web.Response(
            body=json.dumps(e.data),
            content_type="application/problem+json",
            status=e.status,
            reason=e.reason,
        )
    except BackendClientError:
        log.exception("web_handler_with_jwt: BackendClientError")
        return web.HTTPBadGateway(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/bad-gateway",
                "title": "The proxy target server is inaccessible.",
            }),
            content_type="application/problem+json",
        )
    except ClientConnectionError:
        log.warning(
            "web_handler_with_jwt: ClientConnectionError - Client disconnected during proxying: method: {}, path: {}",
            frontend_rqst.method,
            path,
        )
        raise
    except web.HTTPException:
        # BackendAIError instances that double-inherit aiohttp.web.HTTPException
        # (e.g. ManagerConnectionUnavailable -> 503) must surface as their own
        # status code, not get rewritten to 500 by the generic catch below.
        raise
    except Exception:
        log.exception("web_handler_with_jwt: unexpected error")
        return web.HTTPInternalServerError(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/internal-server-error",
                "title": "Something has gone wrong.",
            }),
            content_type="application/problem+json",
        )


async def web_plugin_handler(
    frontend_rqst: web.Request,
    *,
    endpoint_pool: HealthyEndpointPool,
    is_anonymous: bool = False,
) -> web.StreamResponse:
    """
    This handler is almost same to web_handler, but does not manipulate the
    content-type and content-length headers before sending up-requests.
    It also configures the domain in the json body for "auth/signup" requests.
    """
    stats: WebStats = frontend_rqst.app["stats"]
    stats.active_proxy_plugin_handlers.add(asyncio.current_task())  # type: ignore
    path = frontend_rqst.match_info["path"]
    config: WebServerUnifiedConfig = frontend_rqst.app["config"]
    open_session = get_anonymous_session if is_anonymous else get_api_session
    try:
        async with endpoint_pool.acquire() as acquired:
            api_session = await asyncio.shield(open_session(frontend_rqst, acquired))
            content: RequestContent = None
            async with api_session:
                if frontend_rqst.body_exists:
                    content = frontend_rqst.content
                    if path == "auth/signup":
                        body = await frontend_rqst.json()
                        body["domain"] = config.api.domain
                        content = json.dumps(body).encode("utf8")
                request_api_version = frontend_rqst.headers.get("X-BackendAI-Version", None)
                fill_forwarding_hdrs_to_api_session(frontend_rqst, api_session)
                # Deliver cookie for token-based authentication.
                api_session.aiohttp_session.cookie_jar.update_cookies(frontend_rqst.cookies)
                backend_rqst = Request(
                    frontend_rqst.method,
                    path,
                    content,
                    params=frontend_rqst.query,
                    content_type=frontend_rqst.content_type,
                    override_api_version=request_api_version,
                    session_mode=(
                        SessionMode.PROXY if api_session.proxy_mode else SessionMode.CLIENT
                    ),
                )
                for key in HTTP_HEADERS_TO_FORWARD:
                    if (value := frontend_rqst.headers.get(key)) is not None:
                        backend_rqst.headers[key] = value
                async with backend_rqst.fetch() as backend_resp:
                    frontend_resp_hdrs = {
                        key: value
                        for key, value in backend_resp.headers.items()
                        if key not in HOP_ONLY_HEADERS
                    }
                    frontend_resp = web.StreamResponse(
                        status=backend_resp.status,
                        reason=backend_resp.reason,
                        headers=frontend_resp_hdrs,
                    )
                    await frontend_resp.prepare(frontend_rqst)
                    try:
                        while True:
                            chunk = await backend_resp.read(CHUNK_SIZE)
                            if not chunk:
                                break
                            await frontend_resp.write(chunk)
                    finally:
                        await frontend_resp.write_eof()
                    return frontend_resp
    except asyncio.CancelledError:
        raise
    except BackendAPIError as e:
        return web.Response(
            body=json.dumps(e.data),
            content_type="application/problem+json",
            status=e.status,
            reason=e.reason,
        )
    except BackendClientError:
        log.exception("web_plugin_handler: BackendClientError")
        return web.HTTPBadGateway(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/bad-gateway",
                "title": "The proxy target server is inaccessible.",
            }),
            content_type="application/problem+json",
        )
    except web.HTTPException:
        raise
    except Exception:
        log.exception("web_plugin_handler: unexpected error")
        return web.HTTPInternalServerError(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/internal-server-error",
                "title": "Something has gone wrong.",
            }),
            content_type="application/problem+json",
        )


@asynccontextmanager
async def _direct_acquire(endpoint: str) -> AsyncIterator[AcquiredEndpoint]:
    """Pool-free acquire for Apollo Router URLs.

    The Apollo Router upstream is not part of HealthyEndpointPool yet (the
    follow-up ApolloRouterClientPool commit handles it). Until then, the JWT
    handler hands a chosen endpoint string and websocket_handler wraps it in
    an AcquiredEndpoint without any health gating or outcome recording.
    """
    yield AcquiredEndpoint(endpoint=endpoint)


def _to_ws_endpoint(endpoint: str) -> str:
    if endpoint.startswith("http://"):
        return endpoint.replace("http://", "ws://", 1)
    if endpoint.startswith("https://"):
        return endpoint.replace("https://", "wss://", 1)
    return endpoint


async def websocket_handler(
    request: web.Request,
    *,
    endpoint_pool: HealthyEndpointPool | None = None,
    is_anonymous: bool = False,
    static_endpoint: str | None = None,
    jwt_token: str | None = None,
) -> web.StreamResponse:
    # Exactly one of endpoint_pool / static_endpoint must be provided. The
    # Apollo Router and pipeline upstreams are not (yet) managed by a
    # healthy-endpoint pool, so their callers hand a chosen URL directly.
    stats: WebStats = request.app["stats"]
    stats.active_proxy_websocket_handlers.add(asyncio.current_task())  # type: ignore
    path = request.match_info.get("path", None)
    if path is None:
        request_path = request.path
        if request_path.startswith("/func"):
            path = request_path.removeprefix("/func")
    session = await get_session(request)
    app = request.query.get("app")

    # Sticky-by-session for the configured upstream so a long-lived web app
    # stays pinned to the same backend; the Apollo Router path bypasses the
    # pool because Apollo is not (yet) managed by HealthyEndpointPool.
    should_save_session = False
    if static_endpoint is not None:
        acquire_ctx = _direct_acquire(static_endpoint)
    elif endpoint_pool is not None:
        saved_endpoint = session.get("api_endpoints", {}).get(app)
        if saved_endpoint and endpoint_pool.is_healthy(saved_endpoint):
            acquire_ctx = endpoint_pool.acquire_sticky(saved_endpoint)
        else:
            acquire_ctx = endpoint_pool.acquire()
            should_save_session = True
    else:
        raise InvalidAPIConfigurationError(
            "websocket_handler requires endpoint_pool or static_endpoint"
        )

    # HMAC or JWT both go through get_api_session (JWT is added via the
    # X-BackendAI-Token header below); only fully anonymous traffic skips it.
    open_session = get_anonymous_session if is_anonymous else get_api_session
    try:
        async with acquire_ctx as acquired:
            # The HTTP endpoint URL is rewritten to its ws/wss equivalent so
            # api_request.connect_websocket dials the right scheme.
            ws_acquired = AcquiredEndpoint(endpoint=_to_ws_endpoint(acquired.endpoint))
            api_session = await asyncio.shield(open_session(request, ws_acquired))
            async with api_session:
                request_api_version = request.headers.get("X-BackendAI-Version", None)
                fill_forwarding_hdrs_to_api_session(request, api_session)
                api_request = Request(
                    request.method,
                    path,
                    request.content,
                    params=request.query,
                    content_type=request.content_type,
                    override_api_version=request_api_version,
                )

                # Add JWT token to request header if provided
                if jwt_token:
                    api_request.headers["X-BackendAI-Token"] = jwt_token

                # Extract WebSocket subprotocols (e.g., graphql-ws for GraphQL
                # subscriptions).
                protocols_header: str = request.headers.get("Sec-WebSocket-Protocol", "")
                protocols = tuple([p.strip() for p in protocols_header.split(",") if p.strip()])
                async with api_request.connect_websocket(protocols=protocols) as up_conn:
                    down_conn = web.WebSocketResponse(protocols=protocols)
                    await down_conn.prepare(request)
                    web_socket_proxy = WebSocketProxy(up_conn.raw_websocket, down_conn)
                    await web_socket_proxy.proxy()
                    if should_save_session:
                        if "api_endpoints" not in session:
                            session["api_endpoints"] = {}
                        session["api_endpoints"][app] = acquired.endpoint
                        storage = request.get(STORAGE_KEY)
                        if storage is None:
                            raise RuntimeError("Session storage is not available in the request.")
                        config = cast(WebServerUnifiedConfig, request.app["config"])
                        extension_sec = config.session.login_session_extension_sec
                        await storage.save_session(request, down_conn, session, extension_sec)
                    return down_conn
    except asyncio.CancelledError:
        raise
    except BackendAPIError as e:
        return web.Response(
            body=json.dumps(e.data),
            content_type="application/problem+json",
            status=e.status,
            reason=e.reason,
        )
    except BackendClientError:
        log.exception("websocket_handler: BackendClientError")
        return web.HTTPBadGateway(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/bad-gateway",
                "title": "The proxy target server is inaccessible.",
            }),
            content_type="application/problem+json",
        )
    except web.HTTPException:
        raise
    except Exception:
        log.exception("websocket_handler: unexpected error")
        return web.HTTPInternalServerError(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/internal-server-error",
                "title": "Something has gone wrong.",
            }),
            content_type="application/problem+json",
        )

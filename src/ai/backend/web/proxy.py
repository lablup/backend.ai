from __future__ import annotations

import asyncio
import base64
import json
import logging
import random
from typing import Final, Iterable, Optional, Tuple, Union, cast

import aiohttp
from aiohttp import web
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from multidict import CIMultiDict
from trafaret import DataError

from ai.backend.client.exceptions import BackendAPIError, BackendClientError
from ai.backend.client.request import Request, RequestContent, SessionMode
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.web.session import STORAGE_KEY, extra_config_headers, get_session
from ai.backend.logging import BraceStyleAdapter
from ai.backend.web.config.unified import WebServerUnifiedConfig

from .auth import fill_forwarding_hdrs_to_api_session, get_anonymous_session, get_api_session
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
        "up_conn",
        "down_conn",
        "upstream_buffer",
        "upstream_buffer_task",
    )

    up_conn: aiohttp.ClientWebSocketResponse
    down_conn: web.WebSocketResponse
    upstream_buffer: asyncio.Queue[Tuple[Union[str, bytes], aiohttp.WSMsgType]]
    upstream_buffer_task: Optional[asyncio.Task]

    def __init__(
        self, up_conn: aiohttp.ClientWebSocketResponse, down_conn: web.WebSocketResponse
    ) -> None:
        self.up_conn = up_conn
        self.down_conn = down_conn
        self.upstream_buffer = asyncio.Queue()
        self.upstream_buffer_task = None

    async def proxy(self) -> None:
        asyncio.ensure_future(self.downstream())
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
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
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
async def decrypt_payload(request: web.Request, handler) -> web.StreamResponse:
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


async def web_handler(
    frontend_rqst: web.Request,
    *,
    is_anonymous: bool = False,
    api_endpoint: Optional[str] = None,
    http_headers_to_forward_extra: Iterable[str] | None = None,
) -> web.StreamResponse:
    stats: WebStats = frontend_rqst.app["stats"]
    stats.active_proxy_api_handlers.add(asyncio.current_task())  # type: ignore
    path = frontend_rqst.match_info.get("path", "")
    if is_anonymous:
        api_session = await asyncio.shield(get_anonymous_session(frontend_rqst, api_endpoint))
    else:
        api_session = await asyncio.shield(get_api_session(frontend_rqst, api_endpoint))
    http_headers_to_forward_extra = http_headers_to_forward_extra or []
    try:
        async with api_session:
            # We perform request signing by ourselves using the HTTP session data,
            # but need to keep the client's version header so that
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
                session_mode=SessionMode.PROXY if api_session.proxy_mode else SessionMode.CLIENT,
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
                # Prevent malicious or accidental modification of critical headers.
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
        log.exception("web_handler: BackendClientError")
        return web.HTTPBadGateway(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/bad-gateway",
                "title": "The proxy target server is inaccessible.",
            }),
            content_type="application/problem+json",
        )
    except Exception:
        log.exception("web_handler: unexpected error")
        return web.HTTPInternalServerError(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/internal-server-error",
                "title": "Something has gone wrong.",
            }),
            content_type="application/problem+json",
        )
    finally:
        await api_session.close()


async def web_plugin_handler(
    frontend_rqst: web.Request,
    *,
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
    if is_anonymous:
        api_session = await asyncio.shield(get_anonymous_session(frontend_rqst))
    else:
        api_session = await asyncio.shield(get_api_session(frontend_rqst))
    config: WebServerUnifiedConfig = frontend_rqst.app["config"]
    try:
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
                session_mode=SessionMode.PROXY if api_session.proxy_mode else SessionMode.CLIENT,
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
    except Exception:
        log.exception("web_plugin_handler: unexpected error")
        return web.HTTPInternalServerError(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/internal-server-error",
                "title": "Something has gone wrong.",
            }),
            content_type="application/problem+json",
        )


async def websocket_handler(
    request, *, is_anonymous=False, api_endpoint: Optional[str] = None
) -> web.StreamResponse:
    stats: WebStats = request.app["stats"]
    stats.active_proxy_websocket_handlers.add(asyncio.current_task())  # type: ignore
    path = request.match_info["path"]
    session = await get_session(request)
    app = request.query.get("app")

    # Choose a specific Manager endpoint for persistent web app connection.
    should_save_session = False
    config = cast(WebServerUnifiedConfig, request.app["config"])
    configured_endpoints = config.api.endpoint
    if session.get("api_endpoints", {}).get(app):
        stringified_endpoints = [str(e) for e in configured_endpoints]
        if session["api_endpoints"][app] in stringified_endpoints:
            api_endpoint = session["api_endpoints"][app]
    if api_endpoint is None:
        api_endpoint = random.choice(configured_endpoints)
        if "api_endpoints" not in session:
            session["api_endpoints"] = {}
        session["api_endpoints"][app] = str(api_endpoint)
        should_save_session = True

    if is_anonymous:
        api_session = await asyncio.shield(get_anonymous_session(request, api_endpoint))
    else:
        api_session = await asyncio.shield(get_api_session(request, api_endpoint))
    try:
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
            async with api_request.connect_websocket() as up_conn:
                down_conn = web.WebSocketResponse()
                await down_conn.prepare(request)
                web_socket_proxy = WebSocketProxy(up_conn.raw_websocket, down_conn)
                await web_socket_proxy.proxy()
                if should_save_session:
                    storage = request.get(STORAGE_KEY)
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
    except Exception:
        log.exception("websocket_handler: unexpected error")
        return web.HTTPInternalServerError(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/internal-server-error",
                "title": "Something has gone wrong.",
            }),
            content_type="application/problem+json",
        )

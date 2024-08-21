from __future__ import annotations

import asyncio
import base64
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Optional, Tuple, Union, cast

import aiohttp
import jwt
from aiohttp import web
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from ai.backend.client.exceptions import BackendAPIError, BackendClientError
from ai.backend.client.request import Request
from ai.backend.common.web.session import STORAGE_KEY, extra_config_headers, get_session

from .auth import fill_forwarding_hdrs_to_api_session, get_anonymous_session, get_api_session
from .logging import BraceStyleAdapter
from .stats import WebStats

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

HTTP_HEADERS_TO_FORWARD = [
    "Accept-Language",
    "Authorization",
]


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
    request_headers = extra_config_headers.check(request.headers)
    secure_context = request_headers.get("X-BackendAI-Encoded", None)
    if secure_context:
        if not request.can_read_body:  # designated as encrypted but has an empty payload
            request["payload"] = ""
            return await handler(request)
        config = request.app["config"]
        scheme = config["service"]["force_endpoint_protocol"]
        if scheme is None:
            scheme = request.scheme
        api_endpoint = f"{scheme}://{request.host}"
        payload = await request.read()
        request["payload"] = _decrypt_payload(api_endpoint, payload)
    else:
        # For all other requests without explicit encryption,
        # let the handler decide how to read the body.
        request["payload"] = ""
    return await handler(request)


async def web_handler(request: web.Request, *, is_anonymous=False) -> web.StreamResponse:
    stats: WebStats = request.app["stats"]
    stats.active_proxy_api_handlers.add(asyncio.current_task())  # type: ignore
    config = request.app["config"]
    path = request.match_info.get("path", "")
    proxy_path, _, real_path = request.path.lstrip("/").partition("/")
    if proxy_path == "pipeline":
        pipeline_config = config["pipeline"]
        if not pipeline_config:
            raise RuntimeError("'pipeline' config must be set to handle pipeline requests.")
        endpoint = pipeline_config["endpoint"]
        log.info(f"WEB_HANDLER: {request.path} -> {endpoint}/{real_path}")
        api_session = await asyncio.shield(get_api_session(request, endpoint))
    elif is_anonymous:
        api_session = await asyncio.shield(get_anonymous_session(request))
    else:
        api_session = await asyncio.shield(get_api_session(request))
    try:
        async with api_session:
            # We perform request signing by ourselves using the HTTP session data,
            # but need to keep the client's version header so that
            # the final clients may perform its own API versioning support.
            request_headers = extra_config_headers.check(request.headers)
            request_api_version = request_headers.get("X-BackendAI-Version", None)
            secure_context = request_headers.get("X-BackendAI-Encoded", None)
            decrypted_payload_length = 0
            if secure_context:
                payload = request["payload"]
                decrypted_payload_length = len(payload)
            else:
                payload = request.content
            fill_forwarding_hdrs_to_api_session(request, api_session)
            # Deliver cookie for token-based authentication.
            api_session.aiohttp_session.cookie_jar.update_cookies(request.cookies)
            # We treat all requests and responses as streaming universally
            # to be a transparent proxy.
            api_rqst = Request(
                request.method,
                path,
                payload,
                params=request.query,
                override_api_version=request_api_version,
            )
            if "Content-Type" in request.headers:
                api_rqst.content_type = request.content_type  # set for signing
                api_rqst.headers["Content-Type"] = request.headers[
                    "Content-Type"
                ]  # preserve raw value
            if "Content-Length" in request.headers and not secure_context:
                api_rqst.headers["Content-Length"] = request.headers["Content-Length"]
            if "Content-Length" in request.headers and secure_context:
                api_rqst.headers["Content-Length"] = str(decrypted_payload_length)
            for hdr in HTTP_HEADERS_TO_FORWARD:
                if request.headers.get(hdr) is not None:
                    api_rqst.headers[hdr] = request.headers[hdr]
            if proxy_path == "pipeline":
                session_id = request.headers.get("X-BackendAI-SessionID", "")
                if not (sso_token := request.headers.get("X-BackendAI-SSO")):
                    jwt_secret = config["pipeline"]["jwt"]["secret"]
                    now = datetime.now().astimezone()
                    payload = {
                        # Registered claims
                        "exp": now + timedelta(seconds=config["session"]["max_age"]),
                        "iss": "Backend.AI Webserver",
                        "iat": now,
                        # Private claims
                        "aiohttp_session": session_id,
                        "access_key": api_session.config.access_key,  # since 23.03.10
                    }
                    sso_token = jwt.encode(payload, key=jwt_secret, algorithm="HS256")
                api_rqst.headers["X-BackendAI-SSO"] = sso_token
                api_rqst.headers["X-BackendAI-SessionID"] = session_id
            # Uploading request body happens at the entering of the block,
            # and downloading response body happens in the read loop inside.
            async with api_rqst.fetch() as up_resp:
                down_resp = web.StreamResponse()
                down_resp.set_status(up_resp.status, up_resp.reason)
                down_resp.headers.update(up_resp.headers)
                # We already have configured CORS handlers and the API server
                # also provides those headers.  Just let them as-is.
                await down_resp.prepare(request)
                while True:
                    chunk = await up_resp.read(8192)
                    if not chunk:
                        break
                    await down_resp.write(chunk)
                return down_resp
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


async def web_plugin_handler(request, *, is_anonymous=False) -> web.StreamResponse:
    """
    This handler is almost same to web_handler, but does not manipulate the
    content-type and content-length headers before sending up-requests.
    It also configures the domain in the json body for "auth/signup" requests.
    """
    stats: WebStats = request.app["stats"]
    stats.active_proxy_plugin_handlers.add(asyncio.current_task())  # type: ignore
    path = request.match_info["path"]
    if is_anonymous:
        api_session = await asyncio.shield(get_anonymous_session(request))
    else:
        api_session = await asyncio.shield(get_api_session(request))
    try:
        async with api_session:
            content = request.content
            if path == "auth/signup":
                body = await request.json()
                body["domain"] = request.app["config"]["api"]["domain"]
                content = json.dumps(body).encode("utf8")
            request_api_version = request.headers.get("X-BackendAI-Version", None)
            fill_forwarding_hdrs_to_api_session(request, api_session)
            # Deliver cookie for token-based authentication.
            api_session.aiohttp_session.cookie_jar.update_cookies(request.cookies)
            api_rqst = Request(
                request.method,
                path,
                content,
                params=request.query,
                content_type=request.content_type,
                override_api_version=request_api_version,
            )
            for hdr in HTTP_HEADERS_TO_FORWARD:
                if request.headers.get(hdr) is not None:
                    api_rqst.headers[hdr] = request.headers[hdr]
            async with api_rqst.fetch() as up_resp:
                down_resp = web.StreamResponse()
                down_resp.set_status(up_resp.status, up_resp.reason)
                down_resp.headers.update(up_resp.headers)
                # We already have configured CORS handlers and the API server
                # also provides those headers.  Just let them as-is.
                await down_resp.prepare(request)
                while True:
                    chunk = await up_resp.read(8192)
                    if not chunk:
                        break
                    await down_resp.write(chunk)
                return down_resp
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


async def websocket_handler(request, *, is_anonymous=False) -> web.StreamResponse:
    stats: WebStats = request.app["stats"]
    stats.active_proxy_websocket_handlers.add(asyncio.current_task())  # type: ignore
    path = request.match_info["path"]
    session = await get_session(request)
    app = request.query.get("app")

    # Choose a specific Manager endpoint for persistent web app connection.
    api_endpoint = None
    should_save_session = False
    configured_endpoints = request.app["config"]["api"]["endpoint"]
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

    proxy_path, _, real_path = request.path.lstrip("/").partition("/")
    if proxy_path == "pipeline":
        pipeline_config = request.app["config"]["pipeline"]
        if not pipeline_config:
            raise RuntimeError("'pipeline' config must be set to handle pipeline requests.")
        endpoint = pipeline_config["endpoint"].with_scheme("ws")
        log.info(f"WEBSOCKET_HANDLER {request.path} -> {endpoint}/{real_path}")
        api_session = await asyncio.shield(get_anonymous_session(request, endpoint))
    elif is_anonymous:
        api_session = await asyncio.shield(get_anonymous_session(request, api_endpoint))
    else:
        api_session = await asyncio.shield(get_api_session(request, api_endpoint))
    try:
        async with api_session:
            request_api_version = request.headers.get("X-BackendAI-Version", None)
            fill_forwarding_hdrs_to_api_session(request, api_session)
            api_rqst = Request(
                request.method,
                path,
                request.content,
                params=request.query,
                content_type=request.content_type,
                override_api_version=request_api_version,
            )
            async with api_rqst.connect_websocket() as up_conn:
                down_conn = web.WebSocketResponse()
                await down_conn.prepare(request)
                web_socket_proxy = WebSocketProxy(up_conn.raw_websocket, down_conn)
                await web_socket_proxy.proxy()
                if should_save_session:
                    storage = request.get(STORAGE_KEY)
                    await storage.save_session(request, down_conn, session)
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

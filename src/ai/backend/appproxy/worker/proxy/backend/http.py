from __future__ import annotations

import asyncio
import logging
import random
import time
from contextlib import asynccontextmanager
from functools import partial
from typing import AsyncIterator, Final, override

import aiohttp
import aiotools
from aiohttp import ClientConnectorError, web
from multidict import CIMultiDict
from yarl import URL

from ai.backend.appproxy.common.exceptions import ContainerConnectionRefused, WorkerNotAvailable
from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.common.clients.http_client.client_pool import (
    ClientKey,
    ClientPool,
    tcp_client_session_factory,
)
from ai.backend.logging import BraceStyleAdapter

from .base import BaseBackend, HttpRequest

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

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


class HTTPBackend(BaseBackend):
    routes: list[RouteInfo]

    def __init__(self, routes: list[RouteInfo], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.routes = routes
        client_timeout = aiohttp.ClientTimeout(
            total=None,
            connect=10.0,
            sock_connect=10.0,
            sock_read=None,
        )
        cleanup_interval = self.root_context.local_config.proxy_worker.client_pool_cleanup_interval
        self.client_pool = ClientPool(
            partial(
                tcp_client_session_factory,
                timeout=client_timeout,
                auto_decompress=False,  # transparently pass the response body
            ),
            cleanup_interval_seconds=cleanup_interval,
        )

    @override
    async def close(self) -> None:
        await self.client_pool.close()

    @property
    def selected_route(self) -> RouteInfo:
        if len(self.routes) == 0:
            raise WorkerNotAvailable
        elif len(self.routes) == 1:
            selected_route = self.routes[0]
            if selected_route.traffic_ratio == 0:
                raise WorkerNotAvailable
        else:
            ratios: list[float] = [r.traffic_ratio for r in self.routes]
            selected_route = random.choices(self.routes, weights=ratios, k=1)[0]
        return selected_route

    def get_x_forwarded_proto(self, request: web.Request) -> str:
        use_tls = (
            self.root_context.local_config.proxy_worker.tls_advertised
            or self.root_context.local_config.proxy_worker.tls_listen
        )
        return request.headers.get("x-forwarded-proto") or ("https" if use_tls else "http")

    def get_x_forwarded_host(self, request: web.Request) -> str | None:
        return request.headers.get("x-forwarded-host") or request.headers.get("host")

    @asynccontextmanager
    async def request_http(
        self, route: RouteInfo, request: HttpRequest
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        metrics = self.root_context.metrics
        remote = f"{route.current_kernel_host}:{route.kernel_port}"
        metrics.proxy.observe_upstream_http_request(remote=remote, total_bytes_size=0)
        client_key = ClientKey(
            endpoint=f"http://{route.current_kernel_host}:{route.kernel_port}",
            domain=str(route.route_id),
        )
        client_session = self.client_pool.load_client_session(client_key)
        async with client_session.request(
            request.method,
            request.path,
            headers=request.headers,
            allow_redirects=False,
            data=request.body,
            auto_decompress=False,  # transparently pass the response body
            compress=None,  # transparently pass the request body
        ) as response:
            metrics.proxy.observe_upstream_http_response(remote=remote, total_bytes_size=0)
            yield response

    @asynccontextmanager
    async def connect_websocket(
        self, route: RouteInfo, request: web.Request, protocols: list[str] = []
    ) -> AsyncIterator[aiohttp.ClientWebSocketResponse]:
        client_key = ClientKey(
            endpoint=f"http://{route.current_kernel_host}:{route.kernel_port}",
            domain=str(route.route_id),
        )
        client_session = self.client_pool.load_client_session(client_key)
        log.trace("connecting to {}", URL(client_key.endpoint).with_path(request.path))
        async with client_session.ws_connect(request.rel_url, protocols=protocols) as ws:
            yield ws

    async def proxy_http(self, frontend_request: web.Request) -> web.StreamResponse:
        protocol = self.get_x_forwarded_proto(frontend_request)
        host = self.get_x_forwarded_host(frontend_request)
        remote_host, remote_port = (
            frontend_request.transport.get_extra_info("peername")
            if frontend_request.transport
            else None,
            None,
        )
        backend_rqst_hdrs = {}
        # copy frontend request headers without hop-by-hop headers
        for key, value in frontend_request.headers.items():
            if key not in HOP_ONLY_HEADERS:
                backend_rqst_hdrs[key] = value
        # overwrite proxy-related headers
        backend_rqst_hdrs["x-forwarded-proto"] = protocol
        if self.circuit.app == "rstudio":
            backend_rqst_hdrs["x-rstudio-proto"] = protocol
        if host:
            backend_rqst_hdrs["forwarded"] = f"host={host};proto={protocol}"
            backend_rqst_hdrs["x-forwarded-host"] = host
            if self.circuit.app == "rstudio":
                backend_rqst_hdrs["x-rstudio-request"] = (
                    f"{protocol}://{host}{frontend_request.path or ''}"
                )
            split = host.split(":")
            if len(split) >= 2:
                backend_rqst_hdrs["x-forwarded-port"] = split[1]
            elif remote_port:
                backend_rqst_hdrs["x-forwarded-port"] = remote_port
        if remote_host:
            backend_rqst_hdrs["x-forwarded-for"] = f"{remote_host[0]}:{remote_host[1]}"
        if frontend_request.body_exists:
            backend_rqst_body = frontend_request.content.iter_any()
        else:
            backend_rqst_body = None
        backend_request = HttpRequest(
            frontend_request.method,
            frontend_request.rel_url,
            backend_rqst_hdrs,
            backend_rqst_body,
        )
        route = self.selected_route
        await self.mark_last_used_time(route)
        await self.increase_request_counter()
        log.trace(
            "proxying {} {} HTTP Request to {}:{}",
            frontend_request.method,
            frontend_request.rel_url,
            route.current_kernel_host,
            route.kernel_port,
        )
        try:
            async with self.request_http(route, backend_request) as backend_response:
                frontend_resp_hdrs = {}
                for key, value in backend_response.headers.items():
                    if key not in HOP_ONLY_HEADERS:
                        frontend_resp_hdrs[key] = value
                frontend_resp_hdrs["Access-Control-Allow-Origin"] = "*"
                frontend_response = web.StreamResponse(
                    status=backend_response.status,
                    reason=backend_response.reason,
                    headers=frontend_resp_hdrs,
                )
                if "Content-Length" not in backend_response.headers:
                    frontend_response.enable_chunked_encoding()
                await frontend_response.prepare(frontend_request)
                recv_len = 0
                try:
                    async for data in backend_response.content.iter_any():
                        recv_len += len(data)
                        await frontend_response.write(data)
                except aiohttp.ClientPayloadError as e:
                    log.exception(
                        "{!r} (recv-len: {}, content-length: {}, headers: {!r})",
                        e,
                        recv_len,
                        backend_response.content_length,
                        frontend_resp_hdrs,
                    )
                finally:
                    await frontend_response.write_eof()
                return frontend_response
        except ConnectionResetError:
            raise asyncio.CancelledError()
        except aiohttp.ClientOSError as e:
            raise ContainerConnectionRefused from e
        except:
            log.exception("Unhandled exception while proxying HTTP request")
            raise

    async def proxy_ws(self, request: web.Request) -> web.WebSocketResponse:
        metrics = self.root_context.metrics
        stop_event = asyncio.Event()
        total_bytes = 0

        async def _proxy_task(
            left: web.WebSocketResponse | aiohttp.ClientWebSocketResponse,
            right: web.WebSocketResponse | aiohttp.ClientWebSocketResponse,
            tag="(unknown)",
        ) -> None:
            nonlocal total_bytes

            try:
                async for msg in left:
                    match msg.type:
                        case aiohttp.WSMsgType.TEXT:
                            total_bytes += len(msg.data)
                            metrics.proxy.observe_upstream_ws_traffic_chunk(
                                total_bytes_size=total_bytes
                            )
                            await right.send_str(msg.data)
                        case aiohttp.WSMsgType.BINARY:
                            total_bytes += len(msg.data)
                            metrics.proxy.observe_upstream_ws_traffic_chunk(
                                total_bytes_size=total_bytes
                            )
                            await right.send_bytes(msg.data)
                        case aiohttp.WSMsgType.PING:
                            await right.ping(msg.data)
                        case aiohttp.WSMsgType.PONG:
                            await right.pong(msg.data)
                        case aiohttp.WSMsgType.CLOSE:
                            log.debug("{}: websocket closed", tag)
                            await right.close(code=msg.data)
                        case aiohttp.WSMsgType.ERROR:
                            log.debug("{}: websocket closed with error", tag)
                            await right.close()
                        case _:
                            log.debug("{}: Unhandled message type {}", tag, msg.type)
            except ConnectionResetError:
                pass
            except Exception:
                log.exception("")
                raise
            finally:
                log.debug("setting stop event")
                stop_event.set()

        async def _last_access_marker_task(interval: float) -> None:
            await self.mark_last_used_time(route)

        route = self.selected_route
        log.trace(
            "Proxying {} {} WS Request to {}:{}",
            request.method,
            request.path or "/",
            route.current_kernel_host,
            route.kernel_port,
        )

        if "Sec-WebSocket-Protocol" in request.headers:
            protocols = list(request.headers["Sec-WebSocket-Protocol"].split(","))
        else:
            protocols = []

        downstream_ws = web.WebSocketResponse(protocols=protocols)
        await downstream_ws.prepare(request)

        metrics.proxy.observe_upstream_ws_connection_start()
        start = time.monotonic()

        marker_task = aiotools.create_timer(_last_access_marker_task, 1.5)
        await self.increase_request_counter()

        try:
            async with self.connect_websocket(route, request, protocols=protocols) as upstream_ws:
                try:
                    async with asyncio.TaskGroup() as group:
                        group.create_task(
                            _proxy_task(upstream_ws, downstream_ws, tag="(up -> down)")
                        )
                        group.create_task(
                            _proxy_task(downstream_ws, upstream_ws, tag="(down -> up)")
                        )
                        log.debug("created tasks, now waiting until one of two tasks end")
                        await stop_event.wait()
                finally:
                    marker_task.cancel()
                    await marker_task
                    if not downstream_ws.closed:
                        await downstream_ws.close()
                    if not upstream_ws.closed:
                        await upstream_ws.close()
            log.trace("websocket connection closed")
        except ClientConnectorError:
            log.trace("upstream connection closed")
            if not downstream_ws.closed:
                await downstream_ws.close()
        finally:
            end = time.monotonic()
            metrics.proxy.observe_upstream_ws_connection_end(
                duration=int(end - start), total_bytes_size=total_bytes
            )

        return downstream_ws

import asyncio
import logging
import random
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator, Final

import aiohttp
import aiotools
from aiohttp import ClientConnectorError, web

from ai.backend.appproxy.common.exceptions import ContainerConnectionRefused, WorkerNotAvailable
from ai.backend.appproxy.common.logging_utils import BraceStyleAdapter
from ai.backend.appproxy.common.types import RouteInfo

from .abc import AbstractBackend, HttpRequest

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

CHUNK_SIZE = 1 * 1024 * 1024  # 1 KiB
SKIP_HEADERS: Final[set[str]] = {"connection"}


class HTTPBackend(AbstractBackend):
    routes: list[RouteInfo]

    def __init__(self, routes: list[RouteInfo], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.routes = routes

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
        remote = f"{route.kernel_host}:{route.kernel_port}"

        base_url = f"http://{route.kernel_host}:{route.kernel_port}"
        headers = dict(request.headers)

        if headers.get("Transfer-Encoding", "").lower() == "chunked":
            del headers["Transfer-Encoding"]

        timeout = aiohttp.ClientTimeout(
            total=None,
            connect=10.0,
            sock_connect=10.0,
            sock_read=None,
        )
        async with aiohttp.ClientSession(
            base_url=base_url,
            auto_decompress=False,
            timeout=timeout,
        ) as session:
            metrics.proxy.observe_upstream_http_request(
                remote=remote, total_bytes_size=request.body.total_bytes
            )
            async with session.request(
                request.method,
                request.path,
                headers=headers,
                data=request.body,
            ) as response:
                metrics.proxy.observe_upstream_http_response(
                    remote=remote, total_bytes_size=response.content.total_bytes
                )

                yield response

    @asynccontextmanager
    async def connect_websocket(
        self, route: RouteInfo, request: web.Request, protocols: list[str] = []
    ) -> AsyncIterator[aiohttp.ClientWebSocketResponse]:
        base_url = f"http://{route.kernel_host}:{route.kernel_port}"

        timeout = aiohttp.ClientTimeout(
            total=None,
            connect=10.0,
            sock_connect=10.0,
            sock_read=None,
        )
        async with aiohttp.ClientSession(
            base_url=base_url,
            auto_decompress=False,
            timeout=timeout,
        ) as session:
            log.debug("connecting to {}{}", base_url, request.rel_url)
            async with session.ws_connect(request.rel_url, protocols=protocols) as ws:
                log.debug("connected")
                yield ws

    async def proxy_http(self, request: web.Request) -> web.StreamResponse:
        protocol = self.get_x_forwarded_proto(request)
        host = self.get_x_forwarded_host(request)
        remote_host, remote_port = (
            request.transport.get_extra_info("peername") if request.transport else None,
            None,
        )
        headers = {
            "x-forwarded-proto": protocol,
        }
        if self.circuit.app == "rstudio":
            headers["x-rstudio-proto"] = protocol
        if host:
            headers["forwarded"] = f"host={host};proto={protocol}"
            headers["x-forwarded-host"] = host
            if self.circuit.app == "rstudio":
                headers["x-rstudio-request"] = f"{protocol}://{host}{request.path or ''}"
            split = host.split(":")
            if len(split) >= 2:
                headers["x-forwarded-port"] = split[1]
            elif remote_port:
                headers["x-forwarded-port"] = remote_port
        if remote_host:
            headers["x-forwarded-for"] = f"{remote_host[0]}:{remote_host[1]}"
        headers_to_skip = set(headers.keys()) | SKIP_HEADERS
        for key, value in request.headers.items():
            if key.lower() not in headers_to_skip:
                headers[key] = value
        upstream_request = HttpRequest(
            request.method,
            request.rel_url,
            headers,
            request.content,
        )
        route = self.selected_route
        await self.mark_last_used_time(route)
        await self.increase_request_counter()
        log.debug(
            "Proxying {} {} HTTP Request to {}:{}",
            request.method,
            request.rel_url,
            route.kernel_host,
            route.kernel_port,
        )

        try:
            async with self.request_http(route, upstream_request) as backend_response:
                response = web.StreamResponse(
                    status=backend_response.status,
                    headers={**backend_response.headers, "Access-Control-Allow-Origin": "*"},
                )
                await response.prepare(request)
                async for data in backend_response.content.iter_chunked(CHUNK_SIZE):
                    await response.write(data)
                await response.drain()

                return response
        except aiohttp.ClientOSError as e:
            raise ContainerConnectionRefused from e
        except:
            log.exception("")
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
        log.debug(
            "Proxying {} {} WS Request to {}:{}",
            request.method,
            request.path or "/",
            route.kernel_host,
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
                    log.debug("tasks ended")
                    marker_task.cancel()
                    await marker_task
                    if not downstream_ws.closed:
                        await downstream_ws.close()
                    if not upstream_ws.closed:
                        await upstream_ws.close()
            log.debug("websocket connection closed")
        except ClientConnectorError:
            log.debug("upstream connection closed")
            if not downstream_ws.closed:
                await downstream_ws.close()
        finally:
            end = time.monotonic()
            metrics.proxy.observe_upstream_ws_connection_end(
                duration=int(end - start), total_bytes_size=total_bytes
            )

        return downstream_ws

import asyncio
import logging
import random
from contextlib import asynccontextmanager
from typing import AsyncIterator

import aiohttp
from aiohttp import ClientConnectorError, web

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.wsproxy.exceptions import ContainerConnectionRefused, WorkerNotAvailable
from ai.backend.wsproxy.types import RouteInfo

from .abc import AbstractBackend, HttpRequest

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

CHUNK_SIZE = 1 * 1024 * 1024  # 1 KiB


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
            routes = [
                r for r in sorted(self.routes, key=lambda r: r.traffic_ratio) if r.traffic_ratio > 0
            ]
            ranges: list[float] = []
            ratio_sum = 0.0
            for route in routes:
                ratio_sum += route.traffic_ratio
                ranges.append(ratio_sum)
            rand = random.random() * ranges[-1]
            for i in range(len(ranges)):
                ceiling = ranges[0]
                if (i == 0 and rand < ceiling) or (ranges[i - 1] <= rand and rand < ceiling):
                    selected_route = routes[i]
                    break
            else:
                selected_route = routes[-1]
        return selected_route

    def get_x_forwarded_proto(self, request: web.Request) -> str:
        return request.headers.get("x-forwarded-proto") or "http"

    def get_x_forwarded_host(self, request: web.Request) -> str | None:
        return request.headers.get("x-forwarded-host") or request.headers.get("host")

    @asynccontextmanager
    async def request_http(
        self, route: RouteInfo, request: HttpRequest
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        base_url = f"http://{route.kernel_host}:{route.kernel_port}"
        headers = dict(request.headers)

        if headers.get("Transfer-Encoding", "").lower() == "chunked":
            del headers["Transfer-Encoding"]
        async with aiohttp.ClientSession(
            base_url=base_url,
            auto_decompress=False,
        ) as session:
            async with session.request(
                request.method,
                request.path,
                headers=headers,
                data=request.body,
            ) as response:
                yield response

    @asynccontextmanager
    async def connect_websocket(
        self, route: RouteInfo, request: web.Request, protocols: list[str] = []
    ) -> AsyncIterator[aiohttp.ClientWebSocketResponse]:
        base_url = f"http://{route.kernel_host}:{route.kernel_port}"
        async with aiohttp.ClientSession(
            base_url=base_url,
            auto_decompress=False,
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
            **request.headers,
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
        upstream_request = HttpRequest(
            request.method,
            request.rel_url,
            headers,
            request.content,
        )
        route = self.selected_route
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
        stop_event = asyncio.Event()

        async def _proxy_task(
            left: web.WebSocketResponse | aiohttp.ClientWebSocketResponse,
            right: web.WebSocketResponse | aiohttp.ClientWebSocketResponse,
            tag="(unknown)",
        ) -> None:
            try:
                async for msg in left:
                    match msg.type:
                        case aiohttp.WSMsgType.TEXT:
                            await right.send_str(msg.data)
                        case aiohttp.WSMsgType.BINARY:
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
                    if not downstream_ws.closed:
                        await downstream_ws.close()
                    if not upstream_ws.closed:
                        await upstream_ws.close()
            log.debug("websocket connection closed")
        except ClientConnectorError:
            log.debug("upstream connection closed")
            if not downstream_ws.closed:
                await downstream_ws.close()
        return downstream_ws

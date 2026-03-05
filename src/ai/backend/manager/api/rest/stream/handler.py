"""Stream handler class using constructor dependency injection.

WebSocket-based streaming kernel interaction APIs migrated from
module-level functions to Handler class pattern with typed parameters.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import secrets
import uuid
import weakref
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
)
from urllib.parse import urlparse

import aiohttp
import aiotools
import attrs
import zmq
import zmq.asyncio
from aiohttp import web
from aiotools import apartial

from ai.backend.common.api_handlers import PathParam, QueryParam
from ai.backend.common.dto.manager.stream.request import SessionNamePath, StreamProxyRequest
from ai.backend.common.dto.manager.stream.response import StreamAppItem
from ai.backend.common.exception import BackendAIError
from ai.backend.common.json import dump_json, load_json
from ai.backend.common.types import AccessKey, KernelId, SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.utils import call_non_bursty
from ai.backend.manager.api.wsproxy import TCPProxy
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.kernel import InvalidStreamMode
from ai.backend.manager.errors.resource import AppNotFound, NoCurrentTaskContext
from ai.backend.manager.errors.service import AppServiceStartFailed
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.services.stream.actions.execute_in_stream import ExecuteInStreamAction
from ai.backend.manager.services.stream.actions.gc_stale_connections import (
    GCStaleConnectionsAction,
)
from ai.backend.manager.services.stream.actions.get_streaming_session import (
    GetStreamingSessionAction,
)
from ai.backend.manager.services.stream.actions.interrupt_in_stream import InterruptInStreamAction
from ai.backend.manager.services.stream.actions.restart_in_stream import RestartInStreamAction
from ai.backend.manager.services.stream.actions.start_service_in_stream import (
    StartServiceInStreamAction,
)
from ai.backend.manager.services.stream.actions.track_connection import TrackConnectionAction
from ai.backend.manager.services.stream.actions.untrack_connection import UntrackConnectionAction

if TYPE_CHECKING:
    from ai.backend.common.plugin.monitor import ErrorPluginContext
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.event_dispatcher.handlers.stream_cleanup import (
        StreamCleanupEventHandler,
    )
    from ai.backend.manager.services.stream.processors import StreamProcessors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    database_ptask_group: aiotools.PersistentTaskGroup
    rpc_ptask_group: aiotools.PersistentTaskGroup
    stream_pty_handlers: defaultdict[KernelId, weakref.WeakSet[asyncio.Task[Any]]]
    stream_execute_handlers: defaultdict[KernelId, weakref.WeakSet[asyncio.Task[Any]]]
    stream_proxy_handlers: defaultdict[KernelId, weakref.WeakSet[asyncio.Task[Any]]]
    stream_stdin_socks: defaultdict[KernelId, weakref.WeakSet[zmq.asyncio.Socket]]
    zctx: zmq.asyncio.Context
    conn_tracker_lock: asyncio.Lock
    conn_tracker_gc_task: asyncio.Task[Any]
    active_session_ids: defaultdict[KernelId, int]


class StreamHandler:
    """Stream API handler with constructor-injected dependencies."""

    def __init__(
        self,
        *,
        private_ctx: PrivateContext,
        stream_processors: StreamProcessors,
        config_provider: ManagerConfigProvider,
        error_monitor: ErrorPluginContext,
    ) -> None:
        self._ctx = private_ctx
        self._stream = stream_processors
        self.config_provider = config_provider
        self.error_monitor = error_monitor

    # ------------------------------------------------------------------
    # stream_pty (GET /stream/session/{session_name}/pty)
    # ------------------------------------------------------------------

    async def stream_pty(
        self,
        path: PathParam[SessionNamePath],
        ctx: RequestCtx,
        user_ctx: UserContext,
    ) -> web.StreamResponse:
        request = ctx.request
        app_ctx = self._ctx
        session_name = path.parsed.session_name
        access_key = AccessKey(user_ctx.access_key)
        api_version = request["api_version"]
        result = await self._stream.get_streaming_session.wait_for_complete(
            GetStreamingSessionAction(session_name=session_name, access_key=access_key),
        )
        log.info("STREAM_PTY(ak:{0}, s:{1})", access_key, session_name)
        stream_key = KernelId(uuid.UUID(result.kernel_id))
        kernel_host: str
        if result.kernel_host is None:
            hostname = urlparse(result.agent_addr).hostname
            if hostname is None:
                raise InvalidAPIParameters(
                    f"Cannot determine kernel host from agent address: {result.agent_addr}"
                )
            kernel_host = hostname.decode() if isinstance(hostname, bytes) else hostname
        else:
            kernel_host = result.kernel_host
        repl_in_port = result.repl_in_port
        repl_out_port = result.repl_out_port

        ws = web.WebSocketResponse(max_msg_size=self.config_provider.config.manager.max_wsmsg_size)
        await ws.prepare(request)

        myself = asyncio.current_task()
        if myself is None:
            raise NoCurrentTaskContext("No current task context")
        app_ctx.stream_pty_handlers[stream_key].add(myself)

        async def connect_streams(
            _kernel_host: str,
            _repl_in_port: int,
            _repl_out_port: int,
        ) -> tuple[zmq.asyncio.Socket, zmq.asyncio.Socket]:
            stdin_addr = f"tcp://{_kernel_host}:{_repl_in_port}"
            log.debug("stream_pty({0}): stdin: {1}", stream_key, stdin_addr)
            stdin_sock = app_ctx.zctx.socket(zmq.PUB)
            stdin_sock.connect(stdin_addr)
            stdin_sock.setsockopt(zmq.LINGER, 100)
            stdout_addr = f"tcp://{_kernel_host}:{_repl_out_port}"
            log.debug("stream_pty({0}): stdout: {1}", stream_key, stdout_addr)
            stdout_sock = app_ctx.zctx.socket(zmq.SUB)
            stdout_sock.connect(stdout_addr)
            stdout_sock.setsockopt(zmq.LINGER, 100)
            stdout_sock.subscribe(b"")
            return stdin_sock, stdout_sock

        socks = list(await connect_streams(kernel_host, repl_in_port, repl_out_port))
        app_ctx.stream_stdin_socks[stream_key].add(socks[0])
        stream_sync = asyncio.Event()

        async def stream_stdin() -> None:
            nonlocal socks
            try:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = load_json(msg.data)
                        if data["type"] == "stdin":
                            raw_data = base64.b64decode(data["chars"].encode("ascii"))
                            try:
                                await socks[0].send_multipart([raw_data])
                            except (RuntimeError, zmq.error.ZMQError):
                                app_ctx.stream_stdin_socks[stream_key].discard(socks[0])
                                socks[1].close()
                                stdin_sock, stdout_sock = await connect_streams(
                                    kernel_host, repl_in_port, repl_out_port
                                )
                                socks[0] = stdin_sock
                                socks[1] = stdout_sock
                                app_ctx.stream_stdin_socks[stream_key].add(socks[0])
                                await socks[0].send_multipart([raw_data])
                                log.debug("stream_stdin({0}): zmq stream reset", stream_key)
                                stream_sync.set()
                                continue
                        else:
                            run_id = secrets.token_hex(8)
                            if data["type"] == "resize":
                                code = f"%resize {data['rows']} {data['cols']}"
                                await self._stream.execute_in_stream.wait_for_complete(
                                    ExecuteInStreamAction(
                                        session_name=session_name,
                                        access_key=access_key,
                                        api_version=api_version,
                                        run_id=run_id,
                                        mode="query",
                                        code=code,
                                        opts={},
                                        flush_timeout=None,
                                    ),
                                )
                            elif data["type"] == "ping":
                                await self._stream.execute_in_stream.wait_for_complete(
                                    ExecuteInStreamAction(
                                        session_name=session_name,
                                        access_key=access_key,
                                        api_version=api_version,
                                        run_id=run_id,
                                        mode="query",
                                        code="%ping",
                                        opts={},
                                        flush_timeout=None,
                                    ),
                                )
                            elif data["type"] == "restart":
                                log.debug("stream_stdin: restart requested")
                                if not socks[0].closed:
                                    await self._stream.restart_in_stream.wait_for_complete(
                                        RestartInStreamAction(
                                            session_name=session_name,
                                            access_key=access_key,
                                        ),
                                    )
                                    socks[0].close()
                                else:
                                    log.warning(
                                        "stream_stdin({0}): "
                                        "duplicate kernel restart request; "
                                        "ignoring it.",
                                        stream_key,
                                    )
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        log.warning(
                            "stream_stdin({0}): connection closed ({1})",
                            stream_key,
                            ws.exception(),
                        )
            except asyncio.CancelledError:
                raise
            except Exception:
                await self.error_monitor.capture_exception(context={"user": user_ctx.user_uuid})
                log.exception("stream_stdin({0}): unexpected error", stream_key)
            finally:
                log.debug("stream_stdin({0}): terminated", stream_key)
                if not socks[0].closed:
                    socks[0].close()

        async def stream_stdout() -> None:
            nonlocal socks
            log.debug("stream_stdout({0}): started", stream_key)
            data: list[bytes] = []
            try:
                while True:
                    try:
                        data = await socks[1].recv_multipart()
                    except (asyncio.CancelledError, zmq.error.ZMQError):
                        if socks[0] not in app_ctx.stream_stdin_socks:
                            return
                        await stream_sync.wait()
                        stream_sync.clear()
                        log.debug("stream_stdout({0}): zmq stream reset", stream_key)
                        continue
                    if ws.closed:
                        break
                    await ws.send_bytes(
                        dump_json({
                            "type": "out",
                            "data": base64.b64encode(data[0]).decode("ascii"),
                        })
                    )
            except asyncio.CancelledError:
                pass
            except Exception:
                await self.error_monitor.capture_exception(context={"user": user_ctx.user_uuid})
                log.exception("stream_stdout({0}): unexpected error", stream_key)
            finally:
                log.debug("stream_stdout({0}): terminated", stream_key)
                socks[1].close()

        stdout_task = asyncio.create_task(stream_stdout())
        try:
            await stream_stdin()
        except Exception:
            await self.error_monitor.capture_exception(context={"user": user_ctx.user_uuid})
            log.exception("stream_pty({0}): unexpected error", stream_key)
        finally:
            app_ctx.stream_pty_handlers[stream_key].discard(myself)
            app_ctx.stream_stdin_socks[stream_key].discard(socks[0])
            stdout_task.cancel()
            await stdout_task
        return ws

    # ------------------------------------------------------------------
    # stream_execute (GET /stream/session/{session_name}/execute)
    # ------------------------------------------------------------------

    async def stream_execute(
        self,
        path: PathParam[SessionNamePath],
        ctx: RequestCtx,
        user_ctx: UserContext,
    ) -> web.StreamResponse:
        """WebSocket-version of gateway.kernel.execute()."""
        request = ctx.request
        app_ctx = self._ctx

        config = self.config_provider.config
        session_name = path.parsed.session_name
        access_key = AccessKey(user_ctx.access_key)
        api_version = request["api_version"]
        log.info("STREAM_EXECUTE(ak:{0}, s:{1})", access_key, session_name)
        session_result = await self._stream.get_streaming_session.wait_for_complete(
            GetStreamingSessionAction(session_name=session_name, access_key=access_key),
        )
        stream_key = KernelId(uuid.UUID(session_result.kernel_id))

        ws = web.WebSocketResponse(max_msg_size=config.manager.max_wsmsg_size)
        await ws.prepare(request)

        myself = asyncio.current_task()
        if myself is None:
            raise NoCurrentTaskContext("No current task context")
        app_ctx.stream_execute_handlers[stream_key].add(myself)

        run_id = secrets.token_hex(8)

        try:
            if ws.closed:
                log.debug("STREAM_EXECUTE: client disconnected (cancelled)")
                return ws
            params = await ws.receive_json()
            if not params.get("mode"):
                raise InvalidStreamMode("mode is missing or empty!")
            mode = params["mode"]
            if mode not in {"query", "batch"}:
                raise InvalidStreamMode("mode has an invalid value.")
            code = params.get("code", "")
            opts = params.get("options", None) or {}

            while True:
                exec_result = await self._stream.execute_in_stream.wait_for_complete(
                    ExecuteInStreamAction(
                        session_name=session_name,
                        access_key=access_key,
                        api_version=api_version,
                        run_id=run_id,
                        mode=mode,
                        code=code,
                        opts=opts,
                        flush_timeout=0.2,
                    ),
                )
                raw_result = exec_result.result
                if ws.closed:
                    log.debug("STREAM_EXECUTE: client disconnected (interrupted)")  # type: ignore[unreachable]
                    await self._stream.interrupt_in_stream.wait_for_complete(
                        InterruptInStreamAction(
                            session_name=session_name,
                            access_key=access_key,
                        ),
                    )
                    break
                await ws.send_json({
                    "status": raw_result["status"],
                    "console": raw_result.get("console"),
                    "exitCode": raw_result.get("exitCode"),
                    "options": raw_result.get("options"),
                    "files": raw_result.get("files"),
                })
                if raw_result["status"] == "waiting-input":
                    mode = "input"
                    code = await ws.receive_str()
                elif raw_result["status"] == "finished":
                    break
                else:
                    mode = "continue"
                    code = ""
                    opts.clear()
        except (json.decoder.JSONDecodeError, AssertionError) as e:
            log.warning("STREAM_EXECUTE: invalid/missing parameters: {0!r}", e)
            if not ws.closed:
                await ws.send_json({
                    "status": "error",
                    "msg": f"Invalid API parameters: {e!r}",
                })
        except BackendAIError as e:
            log.exception("STREAM_EXECUTE: exception")
            if not ws.closed:
                await ws.send_json({
                    "status": "error",
                    "msg": f"BackendError: {e!r}",
                })
            raise
        except asyncio.CancelledError:
            if not ws.closed:
                await ws.send_json({
                    "status": "server-restarting",
                    "msg": (
                        "The API server is going to restart for maintenance. "
                        "Please connect again with the same run ID."
                    ),
                })
            raise
        finally:
            app_ctx.stream_execute_handlers[stream_key].discard(myself)
            return ws

    # ------------------------------------------------------------------
    # stream_proxy (GET /stream/session/{session_name}/httpproxy,tcpproxy)
    # ------------------------------------------------------------------

    async def stream_proxy(
        self,
        path: PathParam[SessionNamePath],
        query: QueryParam[StreamProxyRequest],
        ctx: RequestCtx,
        user_ctx: UserContext,
    ) -> web.StreamResponse:
        request = ctx.request
        app_ctx = self._ctx
        rpc_ptask_group = app_ctx.rpc_ptask_group
        session_name: str = path.parsed.session_name
        access_key = AccessKey(user_ctx.access_key)
        params = query.parsed
        service: str = params.app
        myself = asyncio.current_task()
        if myself is None:
            raise NoCurrentTaskContext("No current task context")
        session_result = await self._stream.get_streaming_session.wait_for_complete(
            GetStreamingSessionAction(session_name=session_name, access_key=access_key),
        )
        kernel_id = KernelId(uuid.UUID(session_result.kernel_id))
        session_id = SessionId(uuid.UUID(session_result.session_id))
        stream_key = kernel_id
        stream_id = uuid.uuid4().hex
        app_ctx.stream_proxy_handlers[stream_key].add(myself)
        kernel_host: str
        if session_result.kernel_host is None:
            hostname = urlparse(session_result.agent_addr).hostname
            if hostname is None:
                raise InvalidAPIParameters(
                    f"Cannot determine kernel host from agent address: {session_result.agent_addr}"
                )
            kernel_host = hostname.decode() if isinstance(hostname, bytes) else hostname
        else:
            kernel_host = session_result.kernel_host
        service_ports: list[dict[str, Any]] = session_result.service_ports
        sport: dict[str, Any] = {}
        host_port: int = 0
        dest: tuple[str, int] = ("", 0)
        for sport in service_ports:
            if sport["name"] == service:
                if params.port:
                    try:
                        hport_idx = sport["container_ports"].index(params.port)
                    except ValueError as e:
                        raise InvalidAPIParameters(
                            f"Service {service} does not open the port number {params.port}."
                        ) from e
                    host_port = sport["host_ports"][hport_idx]
                else:
                    if "host_ports" not in sport:
                        host_port = sport["host_port"]
                    else:
                        host_port = sport["host_ports"][0]
                dest = (kernel_host, host_port)
                break
        else:
            raise AppNotFound(f"{session_name}:{service}")

        log.info(
            "STREAM_WSPROXY (ak:{}, s:{}): tunneling {}:{} to {}",
            access_key,
            session_name,
            service,
            sport["protocol"],
            "{}:{}".format(*dest),
        )
        if sport["protocol"] == "tcp":
            proxy_cls = TCPProxy
        elif sport["protocol"] == "pty":
            raise NotImplementedError
        elif sport["protocol"] in ("http", "preopen", "vnc", "rdp"):
            proxy_cls = TCPProxy
        else:
            raise InvalidAPIParameters(f"Unsupported service protocol: {sport['protocol']}")

        conn_tracker_key = f"session.{kernel_id}.active_app_connections"
        update_connection_tracker = self._stream.create_connection_refresh_callback(
            kernel_id, service, stream_id
        )

        async def refresh_cb(_kernel_id_str: str, _data: bytes) -> None:
            await asyncio.shield(
                rpc_ptask_group.create_task(
                    call_non_bursty(
                        conn_tracker_key,
                        update_connection_tracker,
                        max_bursts=128,
                        max_idle=5000,
                    ),
                )
            )

        down_cb = apartial(refresh_cb, str(kernel_id))
        up_cb = apartial(refresh_cb, str(kernel_id))
        ping_cb = apartial(refresh_cb, str(kernel_id))

        async def add_conn_track() -> None:
            async with app_ctx.conn_tracker_lock:
                app_ctx.active_session_ids[kernel_id] += 1
                await self._stream.track_connection.wait_for_complete(
                    TrackConnectionAction(
                        kernel_id=kernel_id,
                        session_id=session_id,
                        service=service,
                        stream_id=stream_id,
                    ),
                )

        async def clear_conn_track() -> None:
            async with app_ctx.conn_tracker_lock:
                app_ctx.active_session_ids[kernel_id] -= 1
                if app_ctx.active_session_ids[kernel_id] <= 0:
                    del app_ctx.active_session_ids[kernel_id]
                await self._stream.untrack_connection.wait_for_complete(
                    UntrackConnectionAction(
                        kernel_id=kernel_id,
                        session_id=session_id,
                        service=service,
                        stream_id=stream_id,
                    ),
                )

        try:
            await add_conn_track()

            opts: dict[str, Any] = {}
            if params.arguments is not None:
                opts["arguments"] = load_json(params.arguments)
            if params.envs is not None:
                opts["envs"] = load_json(params.envs)

            start_result = await self._stream.start_service_in_stream.wait_for_complete(
                StartServiceInStreamAction(
                    session_name=session_name,
                    access_key=access_key,
                    service=service,
                    opts=opts,
                ),
            )
            if start_result.result.get("status") == "failed":
                raise AppServiceStartFailed(
                    "Failed to launch the app service",
                    extra_data=start_result.result.get("error"),
                )

            ws = web.WebSocketResponse(
                autoping=False,
                max_msg_size=self.config_provider.config.manager.max_wsmsg_size,
            )
            await ws.prepare(request)
            proxy = proxy_cls(
                ws,
                dest[0],
                dest[1],
                downstream_callback=down_cb,
                upstream_callback=up_cb,
                ping_callback=ping_cb,
            )
            return await proxy.proxy()
        except asyncio.CancelledError:
            log.debug("stream_proxy({}, {}) cancelled", stream_key, service)
            raise
        finally:
            app_ctx.stream_proxy_handlers[stream_key].discard(myself)
            await clear_conn_track()

    # ------------------------------------------------------------------
    # get_stream_apps (GET /stream/session/{session_name}/apps)
    # ------------------------------------------------------------------

    async def get_stream_apps(
        self,
        path: PathParam[SessionNamePath],
        ctx: RequestCtx,
        user_ctx: UserContext,
    ) -> web.StreamResponse:
        session_name = path.parsed.session_name
        access_key = AccessKey(user_ctx.access_key)
        result = await self._stream.get_streaming_session.wait_for_complete(
            GetStreamingSessionAction(session_name=session_name, access_key=access_key),
        )
        service_ports: list[dict[str, Any]] = result.service_ports
        if not service_ports:
            return web.json_response([])
        resp: list[dict[str, Any]] = []
        for item in service_ports:
            app_item = StreamAppItem(
                name=item["name"],
                protocol=item["protocol"],
                ports=item["container_ports"],
                url_template=item.get("url_template"),
                allowed_arguments=item.get("allowed_arguments"),
                allowed_envs=item.get("allowed_envs"),
            )
            resp.append(app_item.model_dump(mode="json", exclude_none=True))
        return web.json_response(resp)


# ------------------------------------------------------------------
# Application lifecycle helpers (used by create_app shim)
# ------------------------------------------------------------------


async def handle_kernel_terminating(
    kernel: KernelRow,
    *,
    app_ctx: PrivateContext,
) -> None:
    """Cleanup callback invoked by StreamCleanupEventHandler."""
    stream_key = kernel.id
    cancelled_tasks: list[asyncio.Task[Any]] = []
    for sock in app_ctx.stream_stdin_socks[stream_key]:
        sock.close()
    for handler in list(app_ctx.stream_pty_handlers.get(stream_key, [])):
        handler.cancel()
        cancelled_tasks.append(handler)
    for handler in list(app_ctx.stream_execute_handlers.get(stream_key, [])):
        handler.cancel()
        cancelled_tasks.append(handler)
    for handler in list(app_ctx.stream_proxy_handlers.get(stream_key, [])):
        handler.cancel()
        cancelled_tasks.append(handler)
    if cancelled_tasks:
        await asyncio.gather(*cancelled_tasks, return_exceptions=True)


async def stream_conn_tracker_gc(
    app_ctx: PrivateContext,
    *,
    stream_processors: StreamProcessors,
) -> None:
    try:
        while True:
            active_ids = list(app_ctx.active_session_ids.keys())
            if active_ids:
                try:
                    await stream_processors.gc_stale_connections.wait_for_complete(
                        GCStaleConnectionsAction(active_session_ids=active_ids),
                    )
                except Exception:
                    log.warning("stream_conn_tracker_gc(): error during GC, retrying...")
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        pass


async def stream_app_ctx(
    _app: web.Application,
    priv_ctx: PrivateContext,
    *,
    stream_processors: StreamProcessors,
    stream_cleanup_handler: StreamCleanupEventHandler,
) -> AsyncIterator[None]:
    """Initialize stream application context."""
    app_ctx = priv_ctx

    app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()
    app_ctx.rpc_ptask_group = aiotools.PersistentTaskGroup()
    app_ctx.stream_pty_handlers = defaultdict(weakref.WeakSet)
    app_ctx.stream_execute_handlers = defaultdict(weakref.WeakSet)
    app_ctx.stream_proxy_handlers = defaultdict(weakref.WeakSet)
    app_ctx.stream_stdin_socks = defaultdict(weakref.WeakSet)
    app_ctx.zctx = zmq.asyncio.Context()
    app_ctx.conn_tracker_lock = asyncio.Lock()
    app_ctx.active_session_ids = defaultdict(int)
    app_ctx.conn_tracker_gc_task = asyncio.create_task(
        stream_conn_tracker_gc(
            app_ctx,
            stream_processors=stream_processors,
        )
    )

    stream_cleanup_handler.register_cleanup_callback(
        lambda kernel: handle_kernel_terminating(kernel, app_ctx=app_ctx),
    )

    yield

    app_ctx.zctx.term()


async def stream_shutdown(
    _app: web.Application,
    priv_ctx: PrivateContext,
) -> None:
    """Shutdown handler for stream app."""
    await priv_ctx.database_ptask_group.shutdown()
    await priv_ctx.rpc_ptask_group.shutdown()
    cancelled_tasks: list[asyncio.Task[Any]] = []
    app_ctx = priv_ctx
    app_ctx.conn_tracker_gc_task.cancel()
    cancelled_tasks.append(app_ctx.conn_tracker_gc_task)
    for per_kernel_handlers in app_ctx.stream_pty_handlers.values():
        for handler in list(per_kernel_handlers):
            if not handler.done():
                handler.cancel()
                cancelled_tasks.append(handler)
    for per_kernel_handlers in app_ctx.stream_execute_handlers.values():
        for handler in list(per_kernel_handlers):
            if not handler.done():
                handler.cancel()
                cancelled_tasks.append(handler)
    for per_kernel_handlers in app_ctx.stream_proxy_handlers.values():
        for handler in list(per_kernel_handlers):
            if not handler.done():
                handler.cancel()
                cancelled_tasks.append(handler)
    await asyncio.gather(*cancelled_tasks, return_exceptions=True)

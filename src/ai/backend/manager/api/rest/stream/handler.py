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
from collections.abc import AsyncIterator, MutableMapping
from datetime import timedelta
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
from etcd_client import GRPCStatusCode, GRPCStatusError

from ai.backend.common import validators as tx
from ai.backend.common.api_handlers import PathParam, QueryParam
from ai.backend.common.dto.manager.stream.request import SessionNamePath, StreamProxyRequest
from ai.backend.common.dto.manager.stream.response import StreamAppItem
from ai.backend.common.events.event_types.kernel.broadcast import (
    KernelTerminatingBroadcastEvent,
)
from ai.backend.common.exception import BackendAIError
from ai.backend.common.json import dump_json, load_json
from ai.backend.common.types import AccessKey, AgentId, KernelId, SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.utils import call_non_bursty
from ai.backend.manager.api.wsproxy import TCPProxy
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.kernel import (
    InvalidStreamMode,
    SessionNotFound,
    TooManySessionsMatched,
)
from ai.backend.manager.errors.resource import AppNotFound, NoCurrentTaskContext
from ai.backend.manager.errors.service import AppServiceStartFailed
from ai.backend.manager.idle import AppStreamingStatus
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.session import KernelLoadingStrategy, SessionRow

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
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

    def __init__(self) -> None:
        pass

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
        root_ctx: RootContext = request.app["_root.context"]
        app_ctx: PrivateContext = request.app["stream.context"]
        database_ptask_group: aiotools.PersistentTaskGroup = request.app["database_ptask_group"]
        session_name = path.parsed.session_name
        access_key = AccessKey(user_ctx.access_key)
        api_version = request["api_version"]
        try:
            async with root_ctx.db.begin_readonly_session() as db_sess:
                session = await asyncio.shield(
                    database_ptask_group.create_task(
                        SessionRow.get_session(
                            db_sess,
                            session_name,
                            access_key,
                            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                        )
                    ),
                )
        except SessionNotFound:
            raise
        log.info("STREAM_PTY(ak:{0}, s:{1})", access_key, session_name)
        compute_session: KernelRow = session.main_kernel
        stream_key = compute_session.id

        await asyncio.shield(
            database_ptask_group.create_task(
                root_ctx.registry.increment_session_usage(session),
            )
        )
        ws = web.WebSocketResponse(
            max_msg_size=root_ctx.config_provider.config.manager.max_wsmsg_size
        )
        await ws.prepare(request)

        myself = asyncio.current_task()
        if myself is None:
            raise NoCurrentTaskContext("No current task context")
        app_ctx.stream_pty_handlers[stream_key].add(myself)

        async def connect_streams(
            kernel: KernelRow,
        ) -> tuple[zmq.asyncio.Socket, zmq.asyncio.Socket]:
            if kernel.kernel_host is None:
                hostname = urlparse(kernel.agent_addr).hostname
                kernel_host = hostname.decode() if isinstance(hostname, bytes) else hostname
            else:
                kernel_host = kernel.kernel_host
            stdin_addr = f"tcp://{kernel_host}:{kernel.repl_in_port}"
            log.debug("stream_pty({0}): stdin: {1}", stream_key, stdin_addr)
            stdin_sock = app_ctx.zctx.socket(zmq.PUB)
            stdin_sock.connect(stdin_addr)
            stdin_sock.setsockopt(zmq.LINGER, 100)
            stdout_addr = f"tcp://{kernel_host}:{kernel.repl_out_port}"
            log.debug("stream_pty({0}): stdout: {1}", stream_key, stdout_addr)
            stdout_sock = app_ctx.zctx.socket(zmq.SUB)
            stdout_sock.connect(stdout_addr)
            stdout_sock.setsockopt(zmq.LINGER, 100)
            stdout_sock.subscribe(b"")
            return stdin_sock, stdout_sock

        socks = list(await connect_streams(compute_session))
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
                                stdin_sock, stdout_sock = await connect_streams(compute_session)
                                socks[0] = stdin_sock
                                socks[1] = stdout_sock
                                app_ctx.stream_stdin_socks[stream_key].add(socks[0])
                                await socks[0].send_multipart([raw_data])
                                log.debug("stream_stdin({0}): zmq stream reset", stream_key)
                                stream_sync.set()
                                continue
                        else:
                            await asyncio.shield(
                                database_ptask_group.create_task(
                                    root_ctx.registry.increment_session_usage(session),
                                ),
                            )
                            run_id = secrets.token_hex(8)
                            if data["type"] == "resize":
                                code = f"%resize {data['rows']} {data['cols']}"
                                await root_ctx.registry.execute(
                                    session,
                                    api_version,
                                    run_id,
                                    "query",
                                    code,
                                    {},
                                    flush_timeout=None,
                                )
                            elif data["type"] == "ping":
                                await root_ctx.registry.execute(
                                    session,
                                    api_version,
                                    run_id,
                                    "query",
                                    "%ping",
                                    {},
                                    flush_timeout=None,
                                )
                            elif data["type"] == "restart":
                                log.debug("stream_stdin: restart requested")
                                if not socks[0].closed:
                                    await asyncio.shield(
                                        database_ptask_group.create_task(
                                            root_ctx.registry.restart_session(
                                                session,
                                            ),
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
                await root_ctx.error_monitor.capture_exception(context={"user": user_ctx.user_uuid})
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
                await root_ctx.error_monitor.capture_exception(context={"user": user_ctx.user_uuid})
                log.exception("stream_stdout({0}): unexpected error", stream_key)
            finally:
                log.debug("stream_stdout({0}): terminated", stream_key)
                socks[1].close()

        stdout_task = asyncio.create_task(stream_stdout())
        try:
            await stream_stdin()
        except Exception:
            await root_ctx.error_monitor.capture_exception(context={"user": user_ctx.user_uuid})
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
        root_ctx: RootContext = request.app["_root.context"]
        app_ctx: PrivateContext = request.app["stream.context"]
        database_ptask_group: aiotools.PersistentTaskGroup = request.app["database_ptask_group"]
        rpc_ptask_group: aiotools.PersistentTaskGroup = request.app["rpc_ptask_group"]

        config = root_ctx.config_provider.config
        registry = root_ctx.registry
        session_name = path.parsed.session_name
        access_key = AccessKey(user_ctx.access_key)
        api_version = request["api_version"]
        log.info("STREAM_EXECUTE(ak:{0}, s:{1})", access_key, session_name)
        try:
            async with root_ctx.db.begin_readonly_session() as db_sess:
                session: SessionRow = await asyncio.shield(
                    database_ptask_group.create_task(
                        SessionRow.get_session(
                            db_sess,
                            session_name,
                            access_key,
                            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                        ),
                    ),
                )
        except SessionNotFound:
            raise
        stream_key = session.main_kernel.id

        await asyncio.shield(
            database_ptask_group.create_task(
                registry.increment_session_usage(session),
            )
        )
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
                raw_result = await registry.execute(
                    session, api_version, run_id, mode, code, opts, flush_timeout=0.2
                )
                if ws.closed:
                    log.debug("STREAM_EXECUTE: client disconnected (interrupted)")  # type: ignore[unreachable]
                    await asyncio.shield(
                        rpc_ptask_group.create_task(
                            registry.interrupt_session(session),
                        )
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
        root_ctx: RootContext = request.app["_root.context"]
        app_ctx: PrivateContext = request.app["stream.context"]
        database_ptask_group: aiotools.PersistentTaskGroup = request.app["database_ptask_group"]
        rpc_ptask_group: aiotools.PersistentTaskGroup = request.app["rpc_ptask_group"]
        session_name: str = path.parsed.session_name
        access_key = AccessKey(user_ctx.access_key)
        params = query.parsed
        service: str = params.app
        myself = asyncio.current_task()
        if myself is None:
            raise NoCurrentTaskContext("No current task context")
        try:
            async with root_ctx.db.begin_readonly_session() as db_sess:
                session = await asyncio.shield(
                    database_ptask_group.create_task(
                        SessionRow.get_session(
                            db_sess,
                            session_name,
                            access_key,
                            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                        ),
                    )
                )
        except (SessionNotFound, TooManySessionsMatched):
            raise
        kernel: KernelRow = session.main_kernel
        kernel_id = kernel.id
        session_id = SessionId(session.id)
        stream_key = kernel_id
        stream_id = uuid.uuid4().hex
        app_ctx.stream_proxy_handlers[stream_key].add(myself)
        kernel_host: str
        if kernel.kernel_host is None:
            hostname = urlparse(kernel.agent_addr).hostname
            if hostname is None:
                raise InvalidAPIParameters(
                    f"Cannot determine kernel host from agent address: {kernel.agent_addr}"
                )
            kernel_host = hostname.decode() if isinstance(hostname, bytes) else hostname
        else:
            kernel_host = kernel.kernel_host
        service_ports: list[dict[str, Any]] = kernel.service_ports or []
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

        valkey_live = root_ctx.valkey_live
        conn_tracker_key = f"session.{kernel_id}.active_app_connections"

        async def update_connection_tracker() -> None:
            await valkey_live.update_app_connection_tracker(str(kernel_id), service, stream_id)

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
                await valkey_live.update_connection_tracker(str(kernel_id), service, stream_id)
                await root_ctx.idle_checker_host.update_app_streaming_status(
                    session_id,
                    AppStreamingStatus.HAS_ACTIVE_CONNECTIONS,
                )

        async def clear_conn_track() -> None:
            async with app_ctx.conn_tracker_lock:
                app_ctx.active_session_ids[kernel_id] -= 1
                if app_ctx.active_session_ids[kernel_id] <= 0:
                    del app_ctx.active_session_ids[kernel_id]
                await valkey_live.remove_connection_tracker(str(kernel_id), service, stream_id)
                remaining_count = await valkey_live.count_active_connections(str(kernel_id))
                if remaining_count == 0:
                    await root_ctx.idle_checker_host.update_app_streaming_status(
                        session_id,
                        AppStreamingStatus.NO_ACTIVE_CONNECTIONS,
                    )

        try:
            await asyncio.shield(
                database_ptask_group.create_task(
                    add_conn_track(),
                )
            )
            await asyncio.shield(
                database_ptask_group.create_task(
                    root_ctx.registry.increment_session_usage(session),
                )
            )

            opts: MutableMapping[str, None | str | list[str]] = {}
            if params.arguments is not None:
                opts["arguments"] = load_json(params.arguments)
            if params.envs is not None:
                opts["envs"] = load_json(params.envs)

            result = await asyncio.shield(
                rpc_ptask_group.create_task(
                    root_ctx.registry.start_service(session, service, opts),
                ),
            )
            if result["status"] == "failed":
                raise AppServiceStartFailed(
                    "Failed to launch the app service", extra_data=result["error"]
                )

            ws = web.WebSocketResponse(
                autoping=False,
                max_msg_size=root_ctx.config_provider.config.manager.max_wsmsg_size,
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
            await asyncio.shield(database_ptask_group.create_task(clear_conn_track()))

    # ------------------------------------------------------------------
    # get_stream_apps (GET /stream/session/{session_name}/apps)
    # ------------------------------------------------------------------

    async def get_stream_apps(
        self,
        path: PathParam[SessionNamePath],
        ctx: RequestCtx,
        user_ctx: UserContext,
    ) -> web.StreamResponse:
        request = ctx.request
        session_name = path.parsed.session_name
        access_key = AccessKey(user_ctx.access_key)
        root_ctx: RootContext = request.app["_root.context"]
        async with root_ctx.db.begin_readonly_session() as db_sess:
            compute_session = await SessionRow.get_session(
                db_sess,
                session_name,
                access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
        raw_service_ports = compute_session.main_kernel.service_ports
        if raw_service_ports is None:
            return web.json_response([])
        service_ports: list[dict[str, Any]] = raw_service_ports
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
    app: web.Application,
    _source: AgentId,
    event: KernelTerminatingBroadcastEvent,
) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["stream.context"]
    try:
        kernel = await KernelRow.get_kernel(
            root_ctx.db,
            event.kernel_id,
            allow_stale=True,
        )
    except SessionNotFound:
        return
    if kernel.cluster_role == DEFAULT_ROLE:
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
        await asyncio.gather(*cancelled_tasks, return_exceptions=True)


async def stream_conn_tracker_gc(root_ctx: RootContext, app_ctx: PrivateContext) -> None:
    valkey_live = root_ctx.valkey_live
    try:
        while True:
            try:
                no_packet_timeout: timedelta = tx.TimeDuration().check(
                    await root_ctx.etcd.get("config/idle/app-streaming-packet-timeout") or "5m",
                )
            except GRPCStatusError as e:
                err_detail = e.args[0]
                if err_detail["code"] == GRPCStatusCode.Unavailable:
                    log.warning(
                        "stream_conn_tracker_gc(): error while connecting to Etcd server,"
                        " retrying..."
                    )
                    continue
                raise e
            async with app_ctx.conn_tracker_lock:
                now = await valkey_live.get_server_time()
                for session_id in app_ctx.active_session_ids.keys():
                    prev_remaining_count = await valkey_live.count_active_connections(
                        str(session_id)
                    )
                    removed_count = await valkey_live.remove_stale_connections(
                        str(session_id),
                        now - no_packet_timeout.total_seconds(),
                    )
                    remaining_count = await valkey_live.count_active_connections(str(session_id))
                    log.debug(
                        f"conn_tracker: gc {session_id} "
                        f"removed/remaining = {removed_count}/{remaining_count}",
                    )
                    if prev_remaining_count > 0 and remaining_count == 0:
                        await root_ctx.idle_checker_host.update_app_streaming_status(
                            SessionId(session_id),
                            AppStreamingStatus.NO_ACTIVE_CONNECTIONS,
                        )
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        pass


async def stream_app_ctx(app: web.Application) -> AsyncIterator[None]:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["stream.context"]

    app_ctx.stream_pty_handlers = defaultdict(weakref.WeakSet)
    app_ctx.stream_execute_handlers = defaultdict(weakref.WeakSet)
    app_ctx.stream_proxy_handlers = defaultdict(weakref.WeakSet)
    app_ctx.stream_stdin_socks = defaultdict(weakref.WeakSet)
    app_ctx.zctx = zmq.asyncio.Context()
    app_ctx.conn_tracker_lock = asyncio.Lock()
    app_ctx.active_session_ids = defaultdict(int)
    app_ctx.conn_tracker_gc_task = asyncio.create_task(stream_conn_tracker_gc(root_ctx, app_ctx))

    root_ctx.event_dispatcher.subscribe(
        KernelTerminatingBroadcastEvent, app, handle_kernel_terminating
    )

    yield

    app_ctx.zctx.term()


async def stream_shutdown(app: web.Application) -> None:
    database_ptask_group: aiotools.PersistentTaskGroup = app["database_ptask_group"]
    rpc_ptask_group: aiotools.PersistentTaskGroup = app["rpc_ptask_group"]
    await database_ptask_group.shutdown()
    await rpc_ptask_group.shutdown()
    cancelled_tasks: list[asyncio.Task[Any]] = []
    app_ctx: PrivateContext = app["stream.context"]
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

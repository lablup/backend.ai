'''
WebSocket-based streaming kernel interaction APIs.

NOTE: For nginx-based setups, we need to gather all websocket-based API handlers
      under this "/stream/"-prefixed app.
'''

from __future__ import annotations

import asyncio
import base64
from collections import defaultdict
from datetime import timedelta
import json
import logging
import secrets
import textwrap
from typing import (
    Any,
    AsyncIterator,
    DefaultDict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    TYPE_CHECKING,
    Tuple,
    Union,
)
from urllib.parse import urlparse
import uuid
import weakref

import aiohttp
import aiotools
from aiohttp import web
import aiohttp_cors
from aiotools import apartial, adefer
import attr
import trafaret as t
import zmq, zmq.asyncio

from ai.backend.common import redis, validators as tx
from ai.backend.common.events import KernelTerminatingEvent
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    KernelId, SessionId,
)

from ai.backend.manager.idle import AppStreamingStatus

from ..defs import DEFAULT_ROLE
from ..models import kernels
from .auth import auth_required
from .exceptions import (
    AppNotFound,
    BackendError,
    InternalServerError,
    InvalidAPIParameters,
    SessionNotFound,
    TooManySessionsMatched,
)
from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params, call_non_bursty
from .wsproxy import TCPProxy
if TYPE_CHECKING:
    from ..config import SharedConfig
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__name__))


@server_status_required(READ_ALLOWED)
@auth_required
@adefer
async def stream_pty(defer, request: web.Request) -> web.StreamResponse:
    root_ctx: RootContext = request.app['_root.context']
    app_ctx: PrivateContext = request.app['stream.context']
    database_ptask_group: aiotools.PersistentTaskGroup = request.app['database_ptask_group']
    session_name = request.match_info['session_name']
    access_key = request['keypair']['access_key']
    api_version = request['api_version']
    try:
        compute_session = await asyncio.shield(
            database_ptask_group.create_task(root_ctx.registry.get_session(session_name, access_key)),
        )
    except SessionNotFound:
        raise
    log.info('STREAM_PTY(ak:{0}, s:{1})', access_key, session_name)
    stream_key = compute_session['id']

    await asyncio.shield(database_ptask_group.create_task(
        root_ctx.registry.increment_session_usage(session_name, access_key),
    ))
    ws = web.WebSocketResponse(max_msg_size=root_ctx.local_config['manager']['max-wsmsg-size'])
    await ws.prepare(request)

    myself = asyncio.current_task()
    assert myself is not None
    app_ctx.stream_pty_handlers[stream_key].add(myself)
    defer(lambda: app_ctx.stream_pty_handlers[stream_key].discard(myself))

    async def connect_streams(compute_session) -> Tuple[zmq.asyncio.Socket, zmq.asyncio.Socket]:
        # TODO: refactor as custom row/table method
        if compute_session.kernel_host is None:
            kernel_host = urlparse(compute_session.agent_addr).hostname
        else:
            kernel_host = compute_session.kernel_host
        stdin_addr = f'tcp://{kernel_host}:{compute_session.stdin_port}'
        log.debug('stream_pty({0}): stdin: {1}', stream_key, stdin_addr)
        stdin_sock = await app_ctx.zctx.socket(zmq.PUB)
        stdin_sock.connect(stdin_addr)
        stdin_sock.setsockopt(zmq.LINGER, 100)
        stdout_addr = f'tcp://{kernel_host}:{compute_session.stdout_port}'
        log.debug('stream_pty({0}): stdout: {1}', stream_key, stdout_addr)
        stdout_sock = await app_ctx.zctx.socket(zmq.SUB)
        stdout_sock.connect(stdout_addr)
        stdout_sock.setsockopt(zmq.LINGER, 100)
        stdout_sock.subscribe(b'')
        return stdin_sock, stdout_sock

    # Wrap sockets in a list so that below coroutines can share reference changes.
    socks = list(await connect_streams(compute_session))
    app_ctx.stream_stdin_socks[stream_key].add(socks[0])
    defer(lambda: app_ctx.stream_stdin_socks[stream_key].discard(socks[0]))
    stream_sync = asyncio.Event()

    async def stream_stdin():
        nonlocal socks
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data['type'] == 'stdin':
                        raw_data = base64.b64decode(data['chars'].encode('ascii'))
                        try:
                            await socks[0].send_mlutipart([raw_data])
                        except (RuntimeError, zmq.error.ZMQError):
                            # when socks[0] is closed, re-initiate the connection.
                            app_ctx.stream_stdin_socks[stream_key].discard(socks[0])
                            socks[1].close()
                            kernel = await asyncio.shield(
                                database_ptask_group.create_task(
                                    root_ctx.registry.get_session(
                                        session_name,
                                        access_key,
                                    ),
                                ),
                            )
                            stdin_sock, stdout_sock = await connect_streams(kernel)
                            socks[0] = stdin_sock
                            socks[1] = stdout_sock
                            app_ctx.stream_stdin_socks[stream_key].add(socks[0])
                            socks[0].write([raw_data])
                            log.debug('stream_stdin({0}): zmq stream reset',
                                      stream_key)
                            stream_sync.set()
                            continue
                    else:
                        await asyncio.shield(
                            database_ptask_group.create_task(
                                root_ctx.registry.increment_session_usage(session_name, access_key),
                            ),
                        )
                        run_id = secrets.token_hex(8)
                        if data['type'] == 'resize':
                            code = f"%resize {data['rows']} {data['cols']}"
                            await root_ctx.registry.execute(
                                session_name, access_key,
                                api_version, run_id, 'query', code, {},
                                flush_timeout=None,
                            )
                        elif data['type'] == 'ping':
                            await root_ctx.registry.execute(
                                session_name, access_key,
                                api_version, run_id, 'query', '%ping', {},
                                flush_timeout=None,
                            )
                        elif data['type'] == 'restart':
                            # Close existing zmq sockets and let stream
                            # handlers get a new one with changed stdin/stdout
                            # ports.
                            log.debug('stream_stdin: restart requested')
                            if not socks[0].closed:
                                await asyncio.shield(
                                    database_ptask_group.create_task(
                                        root_ctx.registry.restart_session(
                                            run_id,
                                            session_name,
                                            access_key,
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
                    log.warning('stream_stdin({0}): connection closed ({1})',
                                stream_key, ws.exception())
        except asyncio.CancelledError:
            # Agent or kernel is terminated.
            raise
        except Exception:
            await root_ctx.error_monitor.capture_exception(context={'user': request['user']['uuid']})
            log.exception('stream_stdin({0}): unexpected error', stream_key)
        finally:
            log.debug('stream_stdin({0}): terminated', stream_key)
            if not socks[0].closed:
                socks[0].close()

    async def stream_stdout():
        nonlocal socks
        log.debug('stream_stdout({0}): started', stream_key)
        try:
            while True:
                try:
                    data = await socks[1].recv_multipart()
                except (asyncio.CancelledError, zmq.error.ZMQError):
                    if socks[0] not in app_ctx.stream_stdin_socks:
                        # we are terminating
                        return
                    # connection is closed, so wait until stream_stdin() recovers it.
                    await stream_sync.wait()
                    stream_sync.clear()
                    log.debug('stream_stdout({0}): zmq stream reset', stream_key)
                    continue
                if ws.closed:
                    break
                await ws.send_str(json.dumps({
                    'type': 'out',
                    'data': base64.b64encode(data[0]).decode('ascii'),
                }, ensure_ascii=False))
        except asyncio.CancelledError:
            pass
        except:
            await root_ctx.error_monitor.capture_exception(context={'user': request['user']['uuid']})
            log.exception('stream_stdout({0}): unexpected error', stream_key)
        finally:
            log.debug('stream_stdout({0}): terminated', stream_key)
            socks[1].close()

    # According to aiohttp docs, reading ws must be done inside this task.
    # We execute the stdout handler as another task.
    stdout_task = asyncio.create_task(stream_stdout())
    try:
        await stream_stdin()
    except Exception:
        await root_ctx.error_monitor.capture_exception(context={'user': request['user']['uuid']})
        log.exception('stream_pty({0}): unexpected error', stream_key)
    finally:
        stdout_task.cancel()
        await stdout_task
    return ws


@server_status_required(READ_ALLOWED)
@auth_required
@adefer
async def stream_execute(defer, request: web.Request) -> web.StreamResponse:
    '''
    WebSocket-version of gateway.kernel.execute().
    '''
    root_ctx: RootContext = request.app['_root.context']
    app_ctx: PrivateContext = request.app['stream.context']
    database_ptask_group: aiotools.PersistentTaskGroup = request.app['database_ptask_group']
    rpc_ptask_group: aiotools.PersistentTaskGroup = request.app['rpc_ptask_group']

    local_config = root_ctx.local_config
    registry = root_ctx.registry
    session_name = request.match_info['session_name']
    access_key = request['keypair']['access_key']
    api_version = request['api_version']
    log.info('STREAM_EXECUTE(ak:{0}, s:{1})', access_key, session_name)
    try:
        compute_session = await asyncio.shield(
            database_ptask_group.create_task(
                registry.get_session(session_name, access_key),  # noqa
            ),
        )
    except SessionNotFound:
        raise
    stream_key = compute_session['id']

    await asyncio.shield(database_ptask_group.create_task(
        registry.increment_session_usage(session_name, access_key),
    ))
    ws = web.WebSocketResponse(max_msg_size=local_config['manager']['max-wsmsg-size'])
    await ws.prepare(request)

    myself = asyncio.current_task()
    assert myself is not None
    app_ctx.stream_execute_handlers[stream_key].add(myself)
    defer(lambda: app_ctx.stream_execute_handlers[stream_key].discard(myself))

    # This websocket connection itself is a "run".
    run_id = secrets.token_hex(8)

    try:
        if ws.closed:
            log.debug('STREAM_EXECUTE: client disconnected (cancelled)')
            return ws
        params = await ws.receive_json()
        assert params.get('mode'), 'mode is missing or empty!'
        mode = params['mode']
        assert mode in {'query', 'batch'}, 'mode has an invalid value.'
        code = params.get('code', '')
        opts = params.get('options', None) or {}

        while True:
            # TODO: rewrite agent and kernel-runner for unbuffered streaming.
            raw_result = await registry.execute(
                session_name, access_key,
                api_version, run_id, mode, code, opts,
                flush_timeout=0.2)
            if ws.closed:
                log.debug('STREAM_EXECUTE: client disconnected (interrupted)')
                await asyncio.shield(rpc_ptask_group.create_task(
                    registry.interrupt_session(session_name, access_key),
                ))
                break
            if raw_result is None:
                # repeat until we get finished
                log.debug('STREAM_EXECUTE: none returned, continuing...')
                mode = 'continue'
                code = ''
                opts.clear()
                continue
            await ws.send_json({
                'status': raw_result['status'],
                'console': raw_result.get('console'),
                'exitCode': raw_result.get('exitCode'),
                'options': raw_result.get('options'),
                'files': raw_result.get('files'),
            })
            if raw_result['status'] == 'waiting-input':
                mode = 'input'
                code = await ws.receive_str()
            elif raw_result['status'] == 'finished':
                break
            else:
                # repeat until we get finished
                mode = 'continue'
                code = ''
                opts.clear()
    except (json.decoder.JSONDecodeError, AssertionError) as e:
        log.warning('STREAM_EXECUTE: invalid/missing parameters: {0!r}', e)
        if not ws.closed:
            await ws.send_json({
                'status': 'error',
                'msg': f'Invalid API parameters: {e!r}',
            })
    except BackendError as e:
        log.exception('STREAM_EXECUTE: exception')
        if not ws.closed:
            await ws.send_json({
                'status': 'error',
                'msg': f'BackendError: {e!r}',
            })
        raise
    except asyncio.CancelledError:
        if not ws.closed:
            await ws.send_json({
                'status': 'server-restarting',
                'msg': 'The API server is going to restart for maintenance. '
                       'Please connect again with the same run ID.',
            })
        raise
    finally:
        return ws


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(['app', 'service']): t.String,
        # The port argument is only required to use secondary ports
        # when the target app listens multiple TCP ports.
        # Otherwise it should be omitted or set to the same value of
        # the actual port number used by the app.
        tx.AliasedKey(['port'], default=None): t.Null | t.Int[1024:65535],
        tx.AliasedKey(['envs'], default=None): t.Null | t.String,  # stringified JSON
                                                                   # e.g., '{"PASSWORD": "12345"}'
        tx.AliasedKey(['arguments'], default=None): t.Null | t.String,  # stringified JSON
                                                                        # e.g., '{"-P": "12345"}'
                                                                        # The value can be one of:
                                                                        # None, str, List[str]
    }))
@adefer
async def stream_proxy(defer, request: web.Request, params: Mapping[str, Any]) -> web.StreamResponse:
    root_ctx: RootContext = request.app['_root.context']
    app_ctx: PrivateContext = request.app['stream.context']
    database_ptask_group: aiotools.PersistentTaskGroup = request.app['database_ptask_group']
    rpc_ptask_group: aiotools.PersistentTaskGroup = request.app['rpc_ptask_group']
    session_name: str = request.match_info['session_name']
    access_key: AccessKey = request['keypair']['access_key']
    service: str = params['app']
    myself = asyncio.current_task()
    assert myself is not None
    try:
        kernel = await asyncio.shield(database_ptask_group.create_task(
            root_ctx.registry.get_session(session_name, access_key),
        ))
    except (SessionNotFound, TooManySessionsMatched):
        raise
    stream_key = kernel['id']
    stream_id = uuid.uuid4().hex
    app_ctx.stream_proxy_handlers[stream_key].add(myself)
    defer(lambda: app_ctx.stream_proxy_handlers[stream_key].discard(myself))
    if kernel['kernel_host'] is None:
        kernel_host = urlparse(kernel['agent_addr']).hostname
    else:
        kernel_host = kernel['kernel_host']
    for sport in kernel['service_ports']:
        if sport['name'] == service:
            if params['port']:
                # using one of the primary/secondary ports of the app
                try:
                    hport_idx = sport['container_ports'].index(params['port'])
                except ValueError:
                    raise InvalidAPIParameters(
                        f"Service {service} does not open the port number {params['port']}.")
                host_port = sport['host_ports'][hport_idx]
            else:                    # using the default (primary) port of the app
                if 'host_ports' not in sport:
                    host_port = sport['host_port']  # legacy kernels
                else:
                    host_port = sport['host_ports'][0]
            dest = (kernel_host, host_port)
            break
    else:
        raise AppNotFound(f'{session_name}:{service}')

    log.info(
        'STREAM_WSPROXY (ak:{}, s:{}): tunneling {}:{} to {}',
        access_key, session_name,
        service, sport['protocol'], '{}:{}'.format(*dest),
    )
    if sport['protocol'] == 'tcp':
        proxy_cls = TCPProxy
    elif sport['protocol'] == 'pty':
        raise NotImplementedError
    elif sport['protocol'] == 'http':
        proxy_cls = TCPProxy
    elif sport['protocol'] == 'preopen':
        proxy_cls = TCPProxy
    else:
        raise InvalidAPIParameters(
            f"Unsupported service protocol: {sport['protocol']}")

    redis_live = root_ctx.redis_live
    conn_tracker_key = f"session.{kernel['id']}.active_app_connections"
    conn_tracker_val = f"{kernel['id']}:{service}:{stream_id}"

    _conn_tracker_script = textwrap.dedent('''
        local now = redis.call('TIME')
        now = now[1] + (now[2] / (10^6))
        redis.call('ZADD', KEYS[1], now, ARGV[1])
    ''')

    async def refresh_cb(kernel_id: str, data: bytes) -> None:
        await asyncio.shield(rpc_ptask_group.create_task(
            call_non_bursty(
                conn_tracker_key,
                apartial(
                    redis.execute_script,
                    redis_live, 'update_conn_tracker', _conn_tracker_script,
                    [conn_tracker_key],
                    [conn_tracker_val],
                ),
                max_bursts=128, max_idle=5000,
            ),
        ))

    down_cb = apartial(refresh_cb, kernel['id'])
    up_cb = apartial(refresh_cb, kernel['id'])
    ping_cb = apartial(refresh_cb, kernel['id'])

    kernel_id = kernel['id']

    async def add_conn_track() -> None:
        async with app_ctx.conn_tracker_lock:
            app_ctx.active_session_ids[kernel_id] += 1
            now = await redis.execute(redis_live, lambda r: r.time())
            now = now[0] + (now[1] / (10**6))
            await redis.execute(
                redis_live,
                # aioredis' ZADD implementation flattens mapping in value-key order
                lambda r: r.zadd(conn_tracker_key, {conn_tracker_val: now}),
            )
            await root_ctx.idle_checker_host.update_app_streaming_status(
                kernel_id,
                AppStreamingStatus.HAS_ACTIVE_CONNECTIONS,
            )

    async def clear_conn_track() -> None:
        async with app_ctx.conn_tracker_lock:
            app_ctx.active_session_ids[kernel_id] -= 1
            if app_ctx.active_session_ids[kernel_id] <= 0:
                del app_ctx.active_session_ids[kernel_id]
            await redis.execute(redis_live, lambda r: r.zrem(conn_tracker_key, conn_tracker_val))
            remaining_count = await redis.execute(
                redis_live,
                lambda r: r.zcount(
                    conn_tracker_key,
                    float('-inf'), float('+inf'),
                ),
            )
            if remaining_count == 0:
                await root_ctx.idle_checker_host.update_app_streaming_status(
                    kernel_id,
                    AppStreamingStatus.NO_ACTIVE_CONNECTIONS,
                )

    try:
        await asyncio.shield(database_ptask_group.create_task(
            add_conn_track(),
        ))
        await asyncio.shield(database_ptask_group.create_task(
            root_ctx.registry.increment_session_usage(session_name, access_key),
        ))

        opts: MutableMapping[str, Union[None, str, List[str]]] = {}
        if params['arguments'] is not None:
            opts['arguments'] = json.loads(params['arguments'])
        if params['envs'] is not None:
            opts['envs'] = json.loads(params['envs'])

        result = await asyncio.shield(
            rpc_ptask_group.create_task(
                root_ctx.registry.start_service(session_name, access_key, service, opts),
            ),
        )
        if result['status'] == 'failed':
            raise InternalServerError(
                "Failed to launch the app service",
                extra_data=result['error'])

        # TODO: weakref to proxies for graceful shutdown?
        ws = web.WebSocketResponse(
            autoping=False,
            max_msg_size=root_ctx.local_config['manager']['max-wsmsg-size'],
        )
        await ws.prepare(request)
        proxy = proxy_cls(
            ws, dest[0], dest[1],
            downstream_callback=down_cb,
            upstream_callback=up_cb,
            ping_callback=ping_cb,
        )
        return await proxy.proxy()
    except asyncio.CancelledError:
        log.debug('stream_proxy({}, {}) cancelled', stream_key, service)
        raise
    finally:
        await asyncio.shield(database_ptask_group.create_task(clear_conn_track()))


@server_status_required(READ_ALLOWED)
@auth_required
async def get_stream_apps(request: web.Request) -> web.Response:
    session_name = request.match_info['session_name']
    access_key = request['keypair']['access_key']
    root_ctx: RootContext = request.app['_root.context']
    compute_session = await root_ctx.registry.get_session(session_name, access_key)
    if compute_session['service_ports'] is None:
        return web.json_response([])
    resp = []
    for item in compute_session['service_ports']:
        response_dict = {
            'name': item['name'],
            'protocol': item['protocol'],
            'ports': item['container_ports'],
        }
        if 'url_template' in item.keys():
            response_dict['url_template'] = item['url_template']
        if 'allowed_arguments' in item.keys():
            response_dict['allowed_arguments'] = item['allowed_arguments']
        if 'allowed_envs' in item.keys():
            response_dict['allowed_envs'] = item['allowed_envs']
        resp.append(response_dict)
    return web.json_response(resp)


async def handle_kernel_terminating(
    app: web.Application,
    source: AgentId,
    event: KernelTerminatingEvent,
) -> None:
    root_ctx: RootContext = app['_root.context']
    app_ctx: PrivateContext = app['stream.context']
    try:
        kernel = await root_ctx.registry.get_kernel(
            event.kernel_id,
            (kernels.c.cluster_role, kernels.c.status),
            allow_stale=True,
        )
    except SessionNotFound:
        return
    if kernel['cluster_role'] == DEFAULT_ROLE:
        stream_key = kernel['id']
        cancelled_tasks = []
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
        # TODO: reconnect if restarting?


async def stream_conn_tracker_gc(root_ctx: RootContext, app_ctx: PrivateContext) -> None:
    redis_live = root_ctx.redis_live
    shared_config: SharedConfig = root_ctx.shared_config
    try:
        while True:
            no_packet_timeout: timedelta = tx.TimeDuration().check(
                await shared_config.etcd.get('config/idle/app-streaming-packet-timeout') or '5m',
            )
            async with app_ctx.conn_tracker_lock:
                now = await redis.execute(redis_live, lambda r: r.time())
                now = now[0] + (now[1] / (10**6))
                for session_id in app_ctx.active_session_ids.keys():
                    conn_tracker_key = f"session.{session_id}.active_app_connections"
                    prev_remaining_count = await redis.execute(
                        redis_live,
                        lambda r: r.zcount(conn_tracker_key, float('-inf'), float('+inf')),
                    )
                    removed_count = await redis.execute(
                        redis_live,
                        lambda r: r.zremrangebyscore(
                            conn_tracker_key, float('-inf'), now - no_packet_timeout.total_seconds(),
                        ),
                    )
                    remaining_count = await redis.execute(
                        redis_live,
                        lambda r: r.zcount(conn_tracker_key, float('-inf'), float('+inf')),
                    )
                    log.debug(f"conn_tracker: gc {session_id} "
                              f"removed/remaining = {removed_count}/{remaining_count}")
                    if prev_remaining_count > 0 and remaining_count == 0:
                        await root_ctx.idle_checker_host.update_app_streaming_status(
                            session_id,
                            AppStreamingStatus.NO_ACTIVE_CONNECTIONS,
                        )
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        pass


@attr.s(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    stream_pty_handlers: DefaultDict[KernelId, weakref.WeakSet[asyncio.Task]]
    stream_execute_handlers: DefaultDict[KernelId, weakref.WeakSet[asyncio.Task]]
    stream_proxy_handlers: DefaultDict[KernelId, weakref.WeakSet[asyncio.Task]]
    stream_stdin_socks: DefaultDict[KernelId, weakref.WeakSet[zmq.asyncio.Socket]]
    zctx: zmq.asyncio.Context
    conn_tracker_lock: asyncio.Lock
    conn_tracker_gc_task: asyncio.Task
    active_session_ids: DefaultDict[SessionId, int]


async def stream_app_ctx(app: web.Application) -> AsyncIterator[None]:
    root_ctx: RootContext = app['_root.context']
    app_ctx: PrivateContext = app['stream.context']

    app_ctx.stream_pty_handlers = defaultdict(weakref.WeakSet)
    app_ctx.stream_execute_handlers = defaultdict(weakref.WeakSet)
    app_ctx.stream_proxy_handlers = defaultdict(weakref.WeakSet)
    app_ctx.stream_stdin_socks = defaultdict(weakref.WeakSet)
    app_ctx.zctx = zmq.asyncio.Context()
    app_ctx.conn_tracker_lock = asyncio.Lock()
    app_ctx.active_session_ids = defaultdict(int)  # multiset[int]
    app_ctx.conn_tracker_gc_task = asyncio.create_task(stream_conn_tracker_gc(root_ctx, app_ctx))

    root_ctx.event_dispatcher.subscribe(KernelTerminatingEvent, app, handle_kernel_terminating)

    yield

    # The shutdown handler below is called before this cleanup.
    app_ctx.zctx.term()


async def stream_shutdown(app: web.Application) -> None:
    database_ptask_group: aiotools.PersistentTaskGroup = app['database_ptask_group']
    rpc_ptask_group: aiotools.PersistentTaskGroup = app['rpc_ptask_group']
    await database_ptask_group.shutdown()
    await rpc_ptask_group.shutdown()
    cancelled_tasks: List[asyncio.Task] = []
    app_ctx: PrivateContext = app['stream.context']
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


def create_app(default_cors_options: CORSOptions) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app.cleanup_ctx.append(stream_app_ctx)
    app.on_shutdown.append(stream_shutdown)
    app['prefix'] = 'stream'
    app['api_versions'] = (2, 3, 4)
    app['stream.context'] = PrivateContext()
    app["database_ptask_group"] = aiotools.PersistentTaskGroup()
    app["rpc_ptask_group"] = aiotools.PersistentTaskGroup()
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    cors.add(add_route('GET', r'/session/{session_name}/pty', stream_pty))
    cors.add(add_route('GET', r'/session/{session_name}/execute', stream_execute))
    cors.add(add_route('GET', r'/session/{session_name}/apps', get_stream_apps))
    # internally both tcp/http proxies use websockets as API/agent-level transports,
    # and thus they have the same implementation here.
    cors.add(add_route('GET', r'/session/{session_name}/httpproxy', stream_proxy))
    cors.add(add_route('GET', r'/session/{session_name}/tcpproxy', stream_proxy))
    return app, []

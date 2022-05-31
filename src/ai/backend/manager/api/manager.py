from __future__ import annotations

import asyncio
import enum
import functools
import json
import logging
import socket
import sqlalchemy as sa
import trafaret as t
from typing import (
    Any,
    Final,
    FrozenSet,
    Iterable,
    Tuple,
    TYPE_CHECKING,
)

from aiohttp import web
import aiohttp_cors
from aiotools import aclosing
import attr
import graphene

from ai.backend.common import validators as tx
from ai.backend.common.events import DoScheduleEvent
from ai.backend.common.logging import BraceStyleAdapter

from .. import __version__
from ..defs import DEFAULT_ROLE
from ..models import agents, kernels, AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES
from . import ManagerStatus
from .auth import superadmin_required
from .exceptions import (
    InstanceNotFound,
    InvalidAPIParameters,
    GenericBadRequest,
    ServerFrozen,
    ServiceUnavailable,
)
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params

if TYPE_CHECKING:
    from .context import RootContext
    from ai.backend.manager.models.gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__name__))


class SchedulerOps(enum.Enum):
    INCLUDE_AGENTS = 'include-agents'
    EXCLUDE_AGENTS = 'exclude-agents'


def server_status_required(allowed_status: FrozenSet[ManagerStatus]):

    def decorator(handler):

        @functools.wraps(handler)
        async def wrapped(request, *args, **kwargs):
            root_ctx: RootContext = request.app['_root.context']
            status = await root_ctx.shared_config.get_manager_status()
            if status not in allowed_status:
                if status == ManagerStatus.FROZEN:
                    raise ServerFrozen
                msg = f'Server is not in the required status: {allowed_status}'
                raise ServiceUnavailable(msg)
            return (await handler(request, *args, **kwargs))

        return wrapped

    return decorator


READ_ALLOWED: Final = frozenset({ManagerStatus.RUNNING, ManagerStatus.FROZEN})
ALL_ALLOWED: Final = frozenset({ManagerStatus.RUNNING})


class GQLMutationUnfrozenRequiredMiddleware:

    def resolve(self, next, root, info: graphene.ResolveInfo, **args) -> Any:
        graph_ctx: GraphQueryContext = info.context
        if info.operation.operation == 'mutation' and \
                graph_ctx.manager_status == ManagerStatus.FROZEN:
            raise ServerFrozen
        return next(root, info, **args)


async def detect_status_update(root_ctx: RootContext) -> None:
    try:
        async with aclosing(root_ctx.shared_config.watch_manager_status()) as agen:
            async for ev in agen:
                if ev.event == 'put':
                    root_ctx.shared_config.get_manager_status.cache_clear()
                    updated_status = await root_ctx.shared_config.get_manager_status()
                    log.debug('Process-{0} detected manager status update: {1}',
                              root_ctx.pidx, updated_status)
    except asyncio.CancelledError:
        pass


async def fetch_manager_status(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    log.info('MANAGER.FETCH_MANAGER_STATUS ()')
    try:
        status = await root_ctx.shared_config.get_manager_status()
        # etcd_info = await root_ctx.shared_config.get_manager_nodes_info()
        configs = root_ctx.local_config['manager']

        async with root_ctx.db.begin() as conn:
            query = (
                sa.select([sa.func.count()])
                .select_from(kernels)
                .where(
                    (kernels.c.cluster_role == DEFAULT_ROLE) &
                    (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
                )
            )
            active_sessions_num = await conn.scalar(query)

            _id = configs['id'] if configs.get('id') else socket.gethostname()
            nodes = [
                {
                    'id': _id,
                    'num_proc': configs['num-proc'],
                    'service_addr': str(configs['service-addr']),
                    'heartbeat_timeout': configs['heartbeat-timeout'],
                    'ssl_enabled': configs['ssl-enabled'],
                    'active_sessions': active_sessions_num,
                    'status': status.value,
                    'version': __version__,
                    'api_version': request['api_version'],
                },
            ]
            return web.json_response({
                'nodes': nodes,
                'status': status.value,                  # legacy?
                'active_sessions': active_sessions_num,  # legacy?
            })
    except:
        log.exception('GET_MANAGER_STATUS: exception')
        raise


@superadmin_required
@check_api_params(
    t.Dict({
        t.Key('status'): tx.Enum(ManagerStatus, use_name=True),
        t.Key('force_kill', default=False): t.ToBool,
    }))
async def update_manager_status(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    log.info('MANAGER.UPDATE_MANAGER_STATUS (status:{}, force_kill:{})',
             params['status'], params['force_kill'])
    try:
        params = await request.json()
        status = params['status']
        force_kill = params['force_kill']
    except json.JSONDecodeError:
        raise InvalidAPIParameters(extra_msg='No request body!')
    except (AssertionError, ValueError) as e:
        raise InvalidAPIParameters(extra_msg=str(e.args[0]))

    if force_kill:
        await root_ctx.registry.kill_all_sessions()
    await root_ctx.shared_config.update_manager_status(status)

    return web.Response(status=204)


async def get_announcement(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    data = await root_ctx.shared_config.etcd.get('manager/announcement')
    if data is None:
        ret = {'enabled': False, 'message': ''}
    else:
        ret = {'enabled': True, 'message': data}
    return web.json_response(ret)


@superadmin_required
@check_api_params(
    t.Dict({
        t.Key('enabled', default='false'): t.ToBool,
        t.Key('message', default=None): t.Null | t.String,
    }))
async def update_announcement(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    if params['enabled']:
        if not params['message']:
            raise InvalidAPIParameters(extra_msg='Empty message not allowed to enable announcement')
        await root_ctx.shared_config.etcd.put('manager/announcement', params['message'])
    else:
        await root_ctx.shared_config.etcd.delete('manager/announcement')
    return web.Response(status=204)


iv_scheduler_ops_args = {
    SchedulerOps.INCLUDE_AGENTS: t.List(t.String),
    SchedulerOps.EXCLUDE_AGENTS: t.List(t.String),
}


@superadmin_required
@check_api_params(
    t.Dict({
        t.Key('op'): tx.Enum(SchedulerOps),
        t.Key('args'): t.Any,
    }))
async def perform_scheduler_ops(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    try:
        args = iv_scheduler_ops_args[params['op']].check(params['args'])
    except t.DataError as e:
        raise InvalidAPIParameters(
            f"Input validation failed for args with {params['op']}",
            extra_data=e.as_dict(),
        )
    if params['op'] in (SchedulerOps.INCLUDE_AGENTS, SchedulerOps.EXCLUDE_AGENTS):
        schedulable = (params['op'] == SchedulerOps.INCLUDE_AGENTS)
        async with root_ctx.db.begin() as conn:
            query = (
                agents.update()
                .values(schedulable=schedulable)
                .where(agents.c.id.in_(args))
            )
            result = await conn.execute(query)
            if result.rowcount < len(args):
                raise InstanceNotFound()
        if schedulable:
            # trigger scheduler
            await root_ctx.event_producer.produce_event(DoScheduleEvent())
    else:
        raise GenericBadRequest('Unknown scheduler operation')
    return web.Response(status=204)


@attr.s(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    status_watch_task: asyncio.Task


async def init(app: web.Application) -> None:
    root_ctx: RootContext = app['_root.context']
    app_ctx: PrivateContext = app['manager.context']
    app_ctx.status_watch_task = asyncio.create_task(detect_status_update(root_ctx))


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app['manager.context']
    if app_ctx.status_watch_task is not None:
        app_ctx.status_watch_task.cancel()
        await app_ctx.status_watch_task


def create_app(default_cors_options: CORSOptions) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app['api_versions'] = (2, 3, 4)
    app['manager.context'] = PrivateContext()
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    status_resource = cors.add(app.router.add_resource('/status'))
    cors.add(status_resource.add_route('GET', fetch_manager_status))
    cors.add(status_resource.add_route('PUT', update_manager_status))
    announcement_resource = cors.add(app.router.add_resource('/announcement'))
    cors.add(announcement_resource.add_route('GET', get_announcement))
    cors.add(announcement_resource.add_route('POST', update_announcement))
    cors.add(app.router.add_route('POST', '/scheduler/operation', perform_scheduler_ops))
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    return app, []

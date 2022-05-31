"""
REST-style session management APIs.
"""
from __future__ import annotations

import asyncio
import base64
import functools
import json
import logging
import re
import secrets
import time
import uuid
import yarl
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Set,
    Tuple,
    Union,
    TYPE_CHECKING,
    cast,
)
from decimal import Decimal
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import PurePosixPath
from urllib.parse import urlparse

import aiohttp
import aiohttp_cors
import aioredis
import aiotools
import attr
import multidict
import sqlalchemy as sa
import trafaret as t
from aiohttp import web, hdrs
from async_timeout import timeout
from dateutil.parser import isoparse
from dateutil.tz import tzutc
from sqlalchemy.sql.expression import true, null

from ai.backend.manager.models.image import ImageRow

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection

from ai.backend.common import redis, validators as tx
from ai.backend.common.docker import ImageRef
from ai.backend.common.exception import (
    UnknownImageReference,
    AliasResolutionFailed,
)
from ai.backend.common.events import (
    AgentHeartbeatEvent,
    AgentStartedEvent,
    AgentTerminatedEvent,
    DoSyncKernelLogsEvent,
    DoSyncKernelStatsEvent,
    DoTerminateSessionEvent,
    KernelCancelledEvent,
    KernelCreatingEvent,
    KernelPreparingEvent,
    KernelPullingEvent,
    KernelStartedEvent,
    KernelTerminatedEvent,
    KernelTerminatingEvent,
    SessionEnqueuedEvent,
    SessionScheduledEvent,
    SessionPreparingEvent,
    SessionCancelledEvent,
    SessionFailureEvent,
    SessionStartedEvent,
    SessionSuccessEvent,
    SessionTerminatedEvent,
)
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.utils import cancel_tasks, str_to_timedelta
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    KernelId,
    ClusterMode,
    KernelEnqueueingConfig,
    SessionTypes,
    check_typed_dict,
)
from ai.backend.common.plugin.monitor import GAUGE

from ..config import DEFAULT_CHUNK_SIZE
from ..defs import DEFAULT_IMAGE_ARCH, DEFAULT_ROLE, REDIS_STREAM_DB
from ..types import UserScope
from ..models import (
    domains,
    association_groups_users as agus, groups,
    keypairs, kernels, AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    query_bootstrap_script,
    keypair_resource_policies,
    scaling_groups,
    users, UserRole,
    vfolders,
    AgentStatus, KernelStatus,
    query_accessible_vfolders,
    session_templates,
    verify_vfolder_name,
    DEAD_KERNEL_STATUSES,
)
from ..models.kernel import match_session_ids
from ..models.utils import execute_with_retry
from .exceptions import (
    AppNotFound,
    InvalidAPIParameters,
    ObjectNotFound,
    ImageNotFound,
    InsufficientPrivilege,
    ServiceUnavailable,
    SessionNotFound,
    SessionAlreadyExists,
    TooManySessionsMatched,
    BackendError,
    InternalServerError,
    TaskTemplateNotFound,
    StorageProxyError,
    UnknownImageReferenceError,
)
from .auth import auth_required
from .types import CORSOptions, WebMiddleware
from .utils import (
    catch_unexpected, check_api_params, get_access_key_scopes, undefined,
)
from .manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__name__))

_json_loads = functools.partial(json.loads, parse_float=Decimal)


class UndefChecker(t.Trafaret):
    def check_and_return(self, value: Any) -> object:
        if value == undefined:
            return value
        else:
            self._failure('Invalid Undef format', value=value)
            return None


creation_config_v1 = t.Dict({
    t.Key('mounts', default=None): t.Null | t.List(t.String),
    t.Key('environ', default=None): t.Null | t.Mapping(t.String, t.String),
    t.Key('clusterSize', default=None): t.Null | t.Int[1:],
})
creation_config_v2 = t.Dict({
    t.Key('mounts', default=None): t.Null | t.List(t.String),
    t.Key('environ', default=None): t.Null | t.Mapping(t.String, t.String),
    t.Key('clusterSize', default=None): t.Null | t.Int[1:],
    t.Key('instanceMemory', default=None): t.Null | tx.BinarySize,
    t.Key('instanceCores', default=None): t.Null | t.Int,
    t.Key('instanceGPUs', default=None): t.Null | t.Float,
    t.Key('instanceTPUs', default=None): t.Null | t.Int,
})
creation_config_v3 = t.Dict({
    t.Key('mounts', default=None): t.Null | t.List(t.String),
    t.Key('environ', default=None): t.Null | t.Mapping(t.String, t.String),
    tx.AliasedKey(['cluster_size', 'clusterSize'], default=None):
        t.Null | t.Int[1:],
    tx.AliasedKey(['scaling_group', 'scalingGroup'], default=None):
        t.Null | t.String,
    t.Key('resources', default=None): t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(['resource_opts', 'resourceOpts'], default=None):
        t.Null | t.Mapping(t.String, t.Any),
})
creation_config_v3_template = t.Dict({
    t.Key('mounts', default=undefined): UndefChecker | t.Null | t.List(t.String),
    t.Key('environ', default=undefined): UndefChecker | t.Null | t.Mapping(t.String, t.String),
    tx.AliasedKey(['cluster_size', 'clusterSize'], default=undefined):
        UndefChecker | t.Null | t.Int[1:],
    tx.AliasedKey(['scaling_group', 'scalingGroup'], default=undefined):
        UndefChecker | t.Null | t.String,
    t.Key('resources', default=undefined): UndefChecker | t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(['resource_opts', 'resourceOpts'], default=undefined):
        UndefChecker | t.Null | t.Mapping(t.String, t.Any),
})
creation_config_v4 = t.Dict({
    t.Key('mounts', default=None): t.Null | t.List(t.String),
    tx.AliasedKey(['mount_map', 'mountMap'], default=None): t.Null | t.Mapping(t.String, t.String),
    t.Key('environ', default=None): t.Null | t.Mapping(t.String, t.String),
    tx.AliasedKey(['cluster_size', 'clusterSize'], default=None): t.Null | t.Int[1:],
    tx.AliasedKey(['scaling_group', 'scalingGroup'], default=None): t.Null | t.String,
    t.Key('resources', default=None): t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(['resource_opts', 'resourceOpts'], default=None): t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(['preopen_ports', 'preopenPorts'], default=None): t.Null | t.List(t.Int[1024:65535]),
})
creation_config_v4_template = t.Dict({
    t.Key('mounts', default=undefined): UndefChecker | t.Null | t.List(t.String),
    tx.AliasedKey(['mount_map', 'mountMap'], default=undefined):
        UndefChecker | t.Null | t.Mapping(t.String, t.String),
    t.Key('environ', default=undefined): UndefChecker | t.Null | t.Mapping(t.String, t.String),
    tx.AliasedKey(['cluster_size', 'clusterSize'], default=undefined):
        UndefChecker | t.Null | t.Int[1:],
    tx.AliasedKey(['scaling_group', 'scalingGroup'], default=undefined):
        UndefChecker | t.Null | t.String,
    t.Key('resources', default=undefined): UndefChecker | t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(['resource_opts', 'resourceOpts'], default=undefined):
        UndefChecker | t.Null | t.Mapping(t.String, t.Any),
})
creation_config_v5 = t.Dict({
    t.Key('mounts', default=None): t.Null | t.List(t.String),
    tx.AliasedKey(['mount_map', 'mountMap'], default=None):
        t.Null | t.Mapping(t.String, t.String),
    t.Key('environ', default=None): t.Null | t.Mapping(t.String, t.String),
    # cluster_size is moved to the root-level parameters
    tx.AliasedKey(['scaling_group', 'scalingGroup'], default=None): t.Null | t.String,
    t.Key('resources', default=None): t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(['resource_opts', 'resourceOpts'], default=None): t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(['preopen_ports', 'preopenPorts'], default=None): t.Null | t.List(t.Int[1024:65535]),
    tx.AliasedKey(['agent_list', 'agentList'], default=None): t.Null | t.List(t.String),
})
creation_config_v5_template = t.Dict({
    t.Key('mounts', default=undefined): UndefChecker | t.Null | t.List(t.String),
    tx.AliasedKey(['mount_map', 'mountMap'], default=undefined):
        UndefChecker | t.Null | t.Mapping(t.String, t.String),
    t.Key('environ', default=undefined): UndefChecker | t.Null | t.Mapping(t.String, t.String),
    # cluster_size is moved to the root-level parameters
    tx.AliasedKey(['scaling_group', 'scalingGroup'], default=undefined):
        UndefChecker | t.Null | t.String,
    t.Key('resources', default=undefined): UndefChecker | t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(['resource_opts', 'resourceOpts'], default=undefined):
        UndefChecker | t.Null | t.Mapping(t.String, t.Any),
})


overwritten_param_check = t.Dict({
    t.Key('template_id'): tx.UUID,
    t.Key('session_name'): t.Regexp(r'^(?=.{4,64}$)\w[\w.-]*\w$', re.ASCII),
    t.Key('image', default=None): t.Null | t.String,
    tx.AliasedKey(['session_type', 'sess_type']): tx.Enum(SessionTypes),
    t.Key('group', default=None): t.Null | t.String,
    t.Key('domain', default=None): t.Null | t.String,
    t.Key('config', default=None): t.Null | t.Mapping(t.String, t.Any),
    t.Key('tag', default=None): t.Null | t.String,
    t.Key('enqueue_only', default=False): t.ToBool,
    t.Key('max_wait_seconds', default=0): t.Int[0:],
    t.Key('reuse', default=True): t.ToBool,
    t.Key('startup_command', default=None): t.Null | t.String,
    t.Key('bootstrap_script', default=None): t.Null | t.String,
    t.Key('owner_access_key', default=None): t.Null | t.String,
    tx.AliasedKey(['scaling_group', 'scalingGroup'], default=None): t.Null | t.String,
    tx.AliasedKey(['cluster_size', 'clusterSize'], default=None): t.Null | t.Int[1:],
    tx.AliasedKey(['cluster_mode', 'clusterMode'], default='single-node'): tx.Enum(ClusterMode),
    tx.AliasedKey(['starts_at', 'startsAt'], default=None): t.Null | t.String,
}).allow_extra('*')


def sub(d, old, new):
    for k, v in d.items():
        if isinstance(v, Mapping) or isinstance(v, dict):
            d[k] = sub(v, old, new)
        elif d[k] == old:
            d[k] = new
    return d


def drop(d, dropval):
    newd = {}
    for k, v in d.items():
        if isinstance(v, Mapping) or isinstance(v, dict):
            newval = drop(v, dropval)
            if len(newval.keys()) > 0:  # exclude empty dict always
                newd[k] = newval
        elif v != dropval:
            newd[k] = v
    return newd


async def _query_userinfo(
    request: web.Request,
    params: Any,
    conn: SAConnection,
) -> Tuple[uuid.UUID, uuid.UUID, dict]:
    if params['domain'] is None:
        params['domain'] = request['user']['domain_name']
    scopes_param = {
        'owner_access_key': (
            None if params['owner_access_key'] is undefined
            else params['owner_access_key']
        ),
    }
    requester_access_key, owner_access_key = await get_access_key_scopes(request, scopes_param)
    requester_uuid = request['user']['uuid']

    owner_uuid = None
    group_id = None
    resource_policy = None

    if requester_access_key != owner_access_key:
        # Admin or superadmin is creating sessions for another user.
        # The check for admin privileges is already done in get_access_key_scope().
        query = (
            sa.select([keypairs.c.user, keypairs.c.resource_policy,
                        users.c.role, users.c.domain_name])
            .select_from(sa.join(keypairs, users, keypairs.c.user == users.c.uuid))
            .where(keypairs.c.access_key == owner_access_key)
        )
        result = await conn.execute(query)
        row = result.first()
        owner_domain = row['domain_name']
        owner_uuid = row['user']
        owner_role = row['role']
        query = (
            sa.select([keypair_resource_policies])
            .select_from(keypair_resource_policies)
            .where(keypair_resource_policies.c.name == row['resource_policy'])
        )
        result = await conn.execute(query)
        resource_policy = result.first()
    else:
        # Normal case when the user is creating her/his own session.
        owner_domain = request['user']['domain_name']
        owner_uuid = requester_uuid
        owner_role = UserRole.USER
        resource_policy = request['keypair']['resource_policy']

    query = (
        sa.select([domains.c.name])
        .select_from(domains)
        .where(
            (domains.c.name == owner_domain) &
            (domains.c.is_active),
        )
    )
    qresult = await conn.execute(query)
    domain_name = qresult.scalar()
    if domain_name is None:
        raise InvalidAPIParameters('Invalid domain')

    if owner_role == UserRole.SUPERADMIN:
        # superadmin can spawn container in any designated domain/group.
        query = (
            sa.select([groups.c.id])
            .select_from(groups)
            .where(
                (groups.c.domain_name == params['domain']) &
                (groups.c.name == params['group']) &
                (groups.c.is_active),
            ))
        qresult = await conn.execute(query)
        group_id = qresult.scalar()
    elif owner_role == UserRole.ADMIN:
        # domain-admin can spawn container in any group in the same domain.
        if params['domain'] != owner_domain:
            raise InvalidAPIParameters("You can only set the domain to the owner's domain.")
        query = (
            sa.select([groups.c.id])
            .select_from(groups)
            .where(
                (groups.c.domain_name == owner_domain) &
                (groups.c.name == params['group']) &
                (groups.c.is_active),
            ))
        qresult = await conn.execute(query)
        group_id = qresult.scalar()
    else:
        # normal users can spawn containers in their group and domain.
        if params['domain'] != owner_domain:
            raise InvalidAPIParameters("You can only set the domain to your domain.")
        query = (
            sa.select([agus.c.group_id])
            .select_from(agus.join(groups, agus.c.group_id == groups.c.id))
            .where(
                (agus.c.user_id == owner_uuid) &
                (groups.c.domain_name == owner_domain) &
                (groups.c.name == params['group']) &
                (groups.c.is_active),
            ))
        qresult = await conn.execute(query)
        group_id = qresult.scalar()
    if group_id is None:
        raise InvalidAPIParameters('Invalid group')

    return owner_uuid, group_id, resource_policy


async def _create(request: web.Request, params: dict[str, Any]) -> web.Response:
    if params['domain'] is None:
        params['domain'] = request['user']['domain_name']
    scopes_param = {
        'owner_access_key': (
            None if params['owner_access_key'] is undefined
            else params['owner_access_key']
        ),
    }
    requester_access_key, owner_access_key = await get_access_key_scopes(request, scopes_param)
    log.info('GET_OR_CREATE (ak:{0}/{1}, img:{2}, s:{3})',
             requester_access_key, owner_access_key if owner_access_key != requester_access_key else '*',
             params['image'], params['session_name'])

    root_ctx: RootContext = request.app['_root.context']
    app_ctx: PrivateContext = request.app['session.context']

    resp: MutableMapping[str, Any] = {}
    current_task = asyncio.current_task()
    assert current_task is not None

    # Check work directory and reserved name directory.
    mount_map = params['config'].get('mount_map')
    if mount_map is not None:
        original_folders = mount_map.keys()
        alias_folders = mount_map.values()
        if len(alias_folders) != len(set(alias_folders)):
            raise InvalidAPIParameters('Duplicate alias folder name exists.')

        alias_name: str
        for alias_name in alias_folders:
            if alias_name is None:
                continue
            if alias_name.startswith("/home/work/"):
                alias_name = alias_name.replace('/home/work/', '')
            if alias_name == '':
                raise InvalidAPIParameters('Alias name cannot be empty.')
            if not verify_vfolder_name(alias_name):
                raise InvalidAPIParameters(str(alias_name) + ' is reserved for internal path.')
            if alias_name in original_folders:
                raise InvalidAPIParameters('Alias name cannot be set to an existing folder name: '
                                            + str(alias_name))

    # Resolve the image reference.
    try:
        async with root_ctx.db.begin_readonly_session() as session:
            image_row = await ImageRow.resolve(session, [
                ImageRef(params['image'], ['*'], params['architecture']),
                params['image'],
            ])
        requested_image_ref = image_row.image_ref
        async with root_ctx.db.begin_readonly() as conn:
            query = (
                sa.select([domains.c.allowed_docker_registries])
                .select_from(domains)
                .where(domains.c.name == params['domain'])
            )
            allowed_registries = await conn.scalar(query)
            if requested_image_ref.registry not in allowed_registries:
                raise AliasResolutionFailed
    except AliasResolutionFailed:
        raise ImageNotFound('unknown alias or disallowed registry')

    # Check existing (owner_access_key, session_name) instance
    try:
        # NOTE: We can reuse the session IDs of TERMINATED sessions only.
        # NOTE: Reusing a session in the PENDING status returns an empty value in service_ports.
        kern = await root_ctx.registry.get_session(params['session_name'], owner_access_key)
        running_image_ref = ImageRef(kern['image'], [kern['registry']], kern['architecture'])
        if running_image_ref != requested_image_ref:
            # The image must be same if get_or_create() called multiple times
            # against an existing (non-terminated) session
            raise SessionAlreadyExists(extra_data={'existingSessionId': str(kern['id'])})
        if not params['reuse']:
            # Respond as error since the client did not request to reuse,
            # but provide the overlapping session ID for later use.
            raise SessionAlreadyExists(extra_data={'existingSessionId': str(kern['id'])})
        # Respond as success with the reused session's information.
        return web.json_response({
            'sessionId': str(kern['id']),
            'sessionName': str(kern['session_name']),
            'status': kern['status'].name,
            'service_ports': kern['service_ports'],
            'created': False,
        }, status=200)
    except SessionNotFound:
        # It's time to create a new session.
        pass

    if params['session_type'] == SessionTypes.BATCH and not params['startup_command']:
        raise InvalidAPIParameters('Batch sessions must have a non-empty startup command.')
    if params['session_type'] != SessionTypes.BATCH and params['starts_at']:
        raise InvalidAPIParameters('Parameter starts_at should be used only for batch sessions')
    starts_at: Union[datetime, None] = None
    if params['starts_at']:
        try:
            starts_at = isoparse(params['starts_at'])
        except ValueError:
            _td = str_to_timedelta(params['starts_at'])
            starts_at = datetime.now(tzutc()) + _td

    if params['cluster_size'] > 1:
        log.debug(" -> cluster_mode:{} (replicate)", params['cluster_mode'])

    if params['dependencies'] is None:
        params['dependencies'] = []

    session_creation_id = secrets.token_urlsafe(16)
    start_event = asyncio.Event()
    kernel_id: Optional[KernelId] = None
    session_creation_tracker = app_ctx.session_creation_tracker
    session_creation_tracker[session_creation_id] = start_event

    async with root_ctx.db.begin_readonly() as conn:
        owner_uuid, group_id, resource_policy = await _query_userinfo(request, params, conn)

        # Use keypair bootstrap_script if it is not delivered as a parameter
        # (only for INTERACTIVE sessions).
        if params['session_type'] == SessionTypes.INTERACTIVE and not params['bootstrap_script']:
            script, _ = await query_bootstrap_script(conn, owner_access_key)
            params['bootstrap_script'] = script

    try:
        kernel_id = await asyncio.shield(app_ctx.database_ptask_group.create_task(
            root_ctx.registry.enqueue_session(
                session_creation_id,
                params['session_name'], owner_access_key,
                [{
                    'image_ref': requested_image_ref,
                    'cluster_role': DEFAULT_ROLE,
                    'cluster_idx': 1,
                    'cluster_hostname': f"{DEFAULT_ROLE}1",
                    'creation_config': params['config'],
                    'bootstrap_script': params['bootstrap_script'],
                    'startup_command': params['startup_command'],
                }],
                params['config']['scaling_group'],
                params['session_type'],
                resource_policy,
                user_scope=UserScope(
                    domain_name=params['domain'],  # type: ignore  # params always have it
                    group_id=group_id,
                    user_uuid=owner_uuid,
                    user_role=request['user']['role'],
                ),
                cluster_mode=params['cluster_mode'],
                cluster_size=params['cluster_size'],
                session_tag=params['tag'],
                starts_at=starts_at,
                agent_list=params['config']['agent_list'],
                dependency_sessions=params['dependencies'],
                callback_url=params['callback_url'],
            )),
        )
        resp['sessionId'] = str(kernel_id)  # changed since API v5
        resp['sessionName'] = str(params['session_name'])
        resp['status'] = 'PENDING'
        resp['servicePorts'] = []
        resp['created'] = True

        if not params['enqueue_only']:
            app_ctx.pending_waits.add(current_task)
            max_wait = params['max_wait_seconds']
            try:
                if max_wait > 0:
                    with timeout(max_wait):
                        await start_event.wait()
                else:
                    await start_event.wait()
            except asyncio.TimeoutError:
                resp['status'] = 'TIMEOUT'
            else:
                await asyncio.sleep(0.5)
                async with root_ctx.db.begin_readonly() as conn:
                    query = (
                        sa.select([
                            kernels.c.status,
                            kernels.c.service_ports,
                        ])
                        .select_from(kernels)
                        .where(kernels.c.id == kernel_id)
                    )
                    result = await conn.execute(query)
                    row = result.first()
                if row['status'] == KernelStatus.RUNNING:
                    resp['status'] = 'RUNNING'
                    for item in row['service_ports']:
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
                        resp['servicePorts'].append(response_dict)
                else:
                    resp['status'] = row['status'].name
    except asyncio.CancelledError:
        raise
    except BackendError:
        log.exception('GET_OR_CREATE: exception')
        raise
    except UnknownImageReference:
        raise UnknownImageReferenceError(f"Unknown image reference: {params['image']}")
    except Exception:
        await root_ctx.error_monitor.capture_exception(context={'user': owner_uuid})
        log.exception('GET_OR_CREATE: unexpected error!')
        raise InternalServerError
    finally:
        app_ctx.pending_waits.discard(current_task)
        del session_creation_tracker[session_creation_id]
    return web.json_response(resp, status=201)


@server_status_required(ALL_ALLOWED)
@auth_required
@check_api_params(t.Dict(
    {
        tx.AliasedKey(['template_id', 'templateId']): t.Null | tx.UUID,
        tx.AliasedKey(['name', 'clientSessionToken'], default=undefined) >> 'session_name':
            UndefChecker | t.Regexp(r'^(?=.{4,64}$)\w[\w.-]*\w$', re.ASCII),
        tx.AliasedKey(['image', 'lang'], default=undefined): UndefChecker | t.Null | t.String,
        tx.AliasedKey(['arch', 'architecture'], default=DEFAULT_IMAGE_ARCH) >> 'architecture': t.String,
        tx.AliasedKey(['type', 'sessionType'], default='interactive') >> 'session_type':
            tx.Enum(SessionTypes),
        tx.AliasedKey(['group', 'groupName', 'group_name'], default=undefined):
            UndefChecker | t.Null | t.String,
        tx.AliasedKey(['domain', 'domainName', 'domain_name'], default=undefined):
            UndefChecker | t.Null | t.String,
        tx.AliasedKey(['cluster_size', 'clusterSize'], default=1):
            t.ToInt[1:],           # new in APIv6
        tx.AliasedKey(['cluster_mode', 'clusterMode'], default='single-node'):
            tx.Enum(ClusterMode),  # new in APIv6
        t.Key('config', default=dict): t.Mapping(t.String, t.Any),
        t.Key('tag', default=undefined): UndefChecker | t.Null | t.String,
        t.Key('enqueueOnly', default=False) >> 'enqueue_only': t.ToBool,
        t.Key('maxWaitSeconds', default=0) >> 'max_wait_seconds': t.Int[0:],
        tx.AliasedKey(['starts_at', 'startsAt'], default=None): t.Null | t.String,
        t.Key('reuseIfExists', default=True) >> 'reuse': t.ToBool,
        t.Key('startupCommand', default=None) >> 'startup_command':
            UndefChecker | t.Null | t.String,
        tx.AliasedKey(['bootstrap_script', 'bootstrapScript'], default=undefined):
            UndefChecker | t.Null | t.String,
        t.Key('dependencies', default=None):
            UndefChecker | t.Null | t.List(tx.UUID) | t.List(t.String),
        tx.AliasedKey(['callback_url', 'callbackUrl', 'callbackURL'], default=None):
            UndefChecker | t.Null | tx.URL,
        t.Key('owner_access_key', default=undefined): UndefChecker | t.Null | t.String,
    },
), loads=_json_loads)
async def create_from_template(request: web.Request, params: dict[str, Any]) -> web.Response:
    # TODO: we need to refactor session_template model to load the template configs
    #       by one batch. Currently, we need to set every template configs one by one.
    root_ctx: RootContext = request.app['_root.context']

    if params['image'] is None and params['template_id'] is None:
        raise InvalidAPIParameters('Both image and template_id can\'t be None!')

    api_version = request['api_version']
    try:
        if 6 <= api_version[0]:
            params['config'] = creation_config_v5_template.check(params['config'])
        elif 5 <= api_version[0]:
            params['config'] = creation_config_v4_template.check(params['config'])
        elif (4, '20190315') <= api_version:
            params['config'] = creation_config_v3_template.check(params['config'])
    except t.DataError as e:
        log.debug('Validation error: {0}', e.as_dict())
        raise InvalidAPIParameters('Input validation error',
                                   extra_data=e.as_dict())
    async with root_ctx.db.begin_readonly() as conn:
        query = (
            sa.select([session_templates])
            .select_from(session_templates)
            .where(
                (session_templates.c.id == params['template_id']) &
                session_templates.c.is_active,
            )
        )
        result = await conn.execute(query)
        template_info = result.fetchone()
        template = template_info['template']
        if not template:
            raise TaskTemplateNotFound
        group_name = None
        if template_info['domain_name'] and template_info['group_id']:
            query = (
                sa.select([groups.c.name])
                .select_from(groups)
                .where(
                    (groups.c.domain_name == template_info['domain_name']) &
                    (groups.c.id == template_info['group_id']),
                )
            )
            group_name = await conn.scalar(query)

    if isinstance(template, str):
        template = json.loads(template)
    log.debug('Template: {0}', template)

    param_from_template = {
        'image': template['spec']['kernel']['image'],
        'architecture': template['spec']['kernel'].get('architecture', DEFAULT_IMAGE_ARCH),
    }
    if 'domain_name' in template_info:
        param_from_template['domain'] = template_info['domain_name']
    if group_name:
        param_from_template['group'] = group_name
    if template['spec']['session_type'] == 'interactive':
        param_from_template['session_type'] = SessionTypes.INTERACTIVE
    elif template['spec']['session_type'] == 'batch':
        param_from_template['session_type'] = SessionTypes.BATCH

    # TODO: Remove `type: ignore` when mypy supports type inference for walrus operator
    # Check https://github.com/python/mypy/issues/7316
    # TODO: remove `NOQA` when flake8 supports Python 3.8 and walrus operator
    # Check https://gitlab.com/pycqa/flake8/issues/599
    if tag := template['metadata'].get('tag'):  # noqa
        param_from_template['tag'] = tag
    if runtime_opt := template['spec']['kernel']['run']:  # noqa
        if bootstrap := runtime_opt['bootstrap']:  # noqa
            param_from_template['bootstrap_script'] = bootstrap
        if startup := runtime_opt['startup_command']:  # noqa
            param_from_template['startup_command'] = startup

    config_from_template: MutableMapping[Any, Any] = {}
    if scaling_group := template['spec'].get('scaling_group'):  # noqa
        config_from_template['scaling_group'] = scaling_group
    if mounts := template['spec'].get('mounts'):  # noqa
        config_from_template['mounts'] = list(mounts.keys())
        config_from_template['mount_map'] = {
            key: value
            for (key, value) in mounts.items()
            if len(value) > 0
        }
    if environ := template['spec']['kernel'].get('environ'):  # noqa
        config_from_template['environ'] = environ
    if resources := template['spec'].get('resources'):  # noqa
        config_from_template['resources'] = resources
    if 'agent_list' in template['spec']:
        config_from_template['agent_list'] = template['spec']['agent_list']

    override_config = drop(dict(params['config']), undefined)
    override_params = drop(dict(params), undefined)

    log.debug('Default config: {0}', config_from_template)
    log.debug('Default params: {0}', param_from_template)

    log.debug('Override config: {0}', override_config)
    log.debug('Override params: {0}', override_params)
    if override_config:
        config_from_template.update(override_config)
    if override_params:
        param_from_template.update(override_params)
    try:
        params = overwritten_param_check.check(param_from_template)
    except RuntimeError as e1:
        log.exception(e1)
    except t.DataError as e2:
        log.debug('Error: {0}', str(e2))
        raise InvalidAPIParameters('Error while validating template')
    params['config'] = config_from_template

    log.debug('Updated param: {0}', params)

    if git := template['spec']['kernel']['git']:  # noqa
        if _dest := git.get('dest_dir'):  # noqa
            target = _dest
        else:
            target = git['repository'].split('/')[-1]

        cmd_builder = 'git clone '
        if credential := git.get('credential'):  # noqa
            proto, url = git['repository'].split('://')
            cmd_builder += f'{proto}://{credential["username"]}:{credential["password"]}@{url}'
        else:
            cmd_builder += git['repository']
        if branch := git.get('branch'):  # noqa
            cmd_builder += f' -b {branch}'
        cmd_builder += f' {target}\n'

        if commit := git.get('commit'):  # noqa
            cmd_builder = 'CWD=$(pwd)\n' + cmd_builder
            cmd_builder += f'cd {target}\n'
            cmd_builder += f'git checkout {commit}\n'
            cmd_builder += 'cd $CWD\n'

        bootstrap = base64.b64decode(params.get('bootstrap_script') or b'').decode()
        bootstrap += '\n'
        bootstrap += cmd_builder
        params['bootstrap_script'] = base64.b64encode(bootstrap.encode()).decode()
    return await _create(request, params)


@server_status_required(ALL_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(['name', 'clientSessionToken']) >> 'session_name':
            t.Regexp(r'^(?=.{4,64}$)\w[\w.-]*\w$', re.ASCII),
        tx.AliasedKey(['image', 'lang']): t.String,
        tx.AliasedKey(['arch', 'architecture'], default=DEFAULT_IMAGE_ARCH) >> 'architecture': t.String,
        tx.AliasedKey(['type', 'sessionType'], default='interactive') >> 'session_type':
            tx.Enum(SessionTypes),
        tx.AliasedKey(['group', 'groupName', 'group_name'], default='default'): t.String,
        tx.AliasedKey(['domain', 'domainName', 'domain_name'], default='default'): t.String,
        tx.AliasedKey(['cluster_size', 'clusterSize'], default=1):
            t.ToInt[1:],             # new in APIv6
        tx.AliasedKey(['cluster_mode', 'clusterMode'], default='single-node'):
            tx.Enum(ClusterMode),    # new in APIv6
        t.Key('config', default=dict): t.Mapping(t.String, t.Any),
        t.Key('tag', default=None): t.Null | t.String,
        t.Key('enqueueOnly', default=False) >> 'enqueue_only': t.ToBool,
        t.Key('maxWaitSeconds', default=0) >> 'max_wait_seconds': t.ToInt[0:],
        tx.AliasedKey(['starts_at', 'startsAt'], default=None): t.Null | t.String,
        t.Key('reuseIfExists', default=True) >> 'reuse': t.ToBool,
        t.Key('startupCommand', default=None) >> 'startup_command': t.Null | t.String,
        tx.AliasedKey(['bootstrap_script', 'bootstrapScript'], default=None): t.Null | t.String,
        t.Key('dependencies', default=None): t.Null | t.List(tx.UUID) | t.List(t.String),
        tx.AliasedKey(['callback_url', 'callbackUrl', 'callbackURL'], default=None): t.Null | tx.URL,
        t.Key('owner_access_key', default=None): t.Null | t.String,
    }),
    loads=_json_loads)
async def create_from_params(request: web.Request, params: dict[str, Any]) -> web.Response:
    if params['session_name'] in ['from-template']:
        raise InvalidAPIParameters(f'Requested session ID {params["session_name"]} is reserved word')
    api_version = request['api_version']
    if 6 <= api_version[0]:
        creation_config = creation_config_v5.check(params['config'])
    elif 5 <= api_version[0]:
        creation_config = creation_config_v4.check(params['config'])
    elif (4, '20190315') <= api_version:
        creation_config = creation_config_v3.check(params['config'])
    elif 2 <= api_version[0] <= 4:
        creation_config = creation_config_v2.check(params['config'])
    elif api_version[0] == 1:
        creation_config = creation_config_v1.check(params['config'])
    else:
        raise InvalidAPIParameters('API version not supported')
    params['config'] = creation_config
    if params['config']['agent_list'] is not None and request['user']['role'] != (UserRole.SUPERADMIN):
        raise InsufficientPrivilege('You are not allowed to manually assign agents for your session.')
    if request['user']['role'] == (UserRole.SUPERADMIN):
        if not params['config']['agent_list']:
            pass
        else:
            agent_count = len(params['config']['agent_list'])
            if params['cluster_mode'] == "multi-node":
                if agent_count != params['cluster_size']:
                    raise InvalidAPIParameters(
                        "For multi-node cluster sessions, the number of manually assigned agents "
                        "must be same to the clsuter size. "
                        "Note that you may specify duplicate agents in the list.",
                    )
            else:
                if agent_count != 1:
                    raise InvalidAPIParameters(
                        "For non-cluster sessions and single-node cluster sessions, "
                        "you may specify only one manually assigned agent.",
                    )
    return await _create(request, params)


@server_status_required(ALL_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key('clientSessionToken') >> 'session_name':
            t.Regexp(r'^(?=.{4,64}$)\w[\w.-]*\w$', re.ASCII),
        tx.AliasedKey(['template_id', 'templateId']): t.Null | tx.UUID,
        tx.AliasedKey(['type', 'sessionType'], default='interactive') >> 'sess_type':
            tx.Enum(SessionTypes),
        tx.AliasedKey(['group', 'groupName', 'group_name'], default='default'): t.String,
        tx.AliasedKey(['domain', 'domainName', 'domain_name'], default='default'): t.String,
        tx.AliasedKey(['scaling_group', 'scalingGroup'], default=None): t.Null | t.String,
        t.Key('tag', default=None): t.Null | t.String,
        t.Key('enqueueOnly', default=False) >> 'enqueue_only': t.ToBool,
        t.Key('maxWaitSeconds', default=0) >> 'max_wait_seconds': t.Int[0:],
        t.Key('owner_access_key', default=None): t.Null | t.String,
    }),
    loads=_json_loads)
async def create_cluster(request: web.Request, params: dict[str, Any]) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    app_ctx: PrivateContext = request.app['session.context']
    if params['domain'] is None:
        params['domain'] = request['user']['domain_name']
    scopes_param = {
        'owner_access_key': (
            None if params['owner_access_key'] is undefined
            else params['owner_access_key']
        ),
    }
    requester_access_key, owner_access_key = await get_access_key_scopes(request, scopes_param)
    log.info('CREAT_CLUSTER (ak:{0}/{1}, s:{3})',
             requester_access_key, owner_access_key if owner_access_key != requester_access_key else '*',
             params['session_name'])

    resp: MutableMapping[str, Any] = {}

    # Check existing (owner_access_key, session) kernel instance
    try:
        # NOTE: We can reuse the session IDs of TERMINATED sessions only.
        # NOTE: Reusing a session in the PENDING status returns an empty value in service_ports.
        await root_ctx.registry.get_session(params['session_name'], owner_access_key)
    except SessionNotFound:
        pass
    except TooManySessionsMatched:
        raise SessionAlreadyExists
    else:
        raise SessionAlreadyExists

    async with root_ctx.db.begin_readonly() as conn:
        query = (
            sa.select([session_templates.c.template])
            .select_from(session_templates)
            .where(
                (session_templates.c.id == params['template_id']) &
                session_templates.c.is_active,
            )
        )
        template = await conn.scalar(query)
        log.debug('task template: {}', template)
        if not template:
            raise TaskTemplateNotFound

    mounts = []
    mount_map = {}
    environ = {}

    if _mounts := template['spec'].get('mounts'):  # noqa
        mounts = list(_mounts.keys())
        mount_map = {
            key: value
            for (key, value) in _mounts.items()
            if len(value) > 0
        }
    if _environ := template['spec'].get('environ'):  # noqa
        environ = _environ

    log.debug('cluster template: {}', template)

    kernel_configs: List[KernelEnqueueingConfig] = []
    for node in template['spec']['nodes']:
        # Resolve session template.
        kernel_config = {
            'image': template['spec']['kernel']['image'],
            'architecture': template['spec']['kernel'].get('architecture', DEFAULT_IMAGE_ARCH),
            'cluster_role': node['cluster_role'],
            'creation_config': {
                'mount': mounts,
                'mount_map': mount_map,
                'environ': environ,
            },
        }

        if template['spec']['sess_type'] == 'interactive':
            kernel_config['sess_type'] = SessionTypes.INTERACTIVE
        elif template['spec']['sess_type'] == 'batch':
            kernel_config['sess_type'] = SessionTypes.BATCH

        if tag := template['metadata'].get('tag', None):
            kernel_config['tag'] = tag
        if runtime_opt := template['spec']['kernel']['run']:
            if bootstrap := runtime_opt['bootstrap']:
                kernel_config['bootstrap_script'] = bootstrap
            if startup := runtime_opt['startup_command']:
                kernel_config['startup_command'] = startup

        if resources := template['spec'].get('resources'):
            kernel_config['creation_config']['resources'] = resources

        if git := template['spec']['kernel']['git']:
            if _dest := git.get('dest_dir'):
                target = _dest
            else:
                target = git['repository'].split('/')[-1]

            cmd_builder = 'git clone '
            if credential := git.get('credential'):
                proto, url = git['repository'].split('://')
                cmd_builder += f'{proto}://{credential["username"]}:{credential["password"]}@{url}'
            else:
                cmd_builder += git['repository']
            if branch := git.get('branch'):
                cmd_builder += f' -b {branch}'
            cmd_builder += f' {target}\n'

            if commit := git.get('commit'):
                cmd_builder = 'CWD=$(pwd)\n' + cmd_builder
                cmd_builder += f'cd {target}\n'
                cmd_builder += f'git checkout {commit}\n'
                cmd_builder += 'cd $CWD\n'

            bootstrap = base64.b64decode(kernel_config.get('bootstrap_script') or b'').decode()
            bootstrap += '\n'
            bootstrap += cmd_builder
            kernel_config['bootstrap_script'] = base64.b64encode(bootstrap.encode()).decode()

        # Resolve the image reference.
        try:
            async with root_ctx.db.begin_readonly_session() as session:
                image_row = await ImageRow.resolve(session, [
                    ImageRef(kernel_config['image'], ['*'], kernel_config['architecture']),
                    kernel_config['image'],
                ])
            requested_image_ref = image_row.image_ref
            async with root_ctx.db.begin_readonly() as conn:
                query = (
                    sa.select([domains.c.allowed_docker_registries])
                    .select_from(domains)
                    .where(domains.c.name == params['domain'])
                )
                allowed_registries = await conn.scalar(query)
                if requested_image_ref.registry not in allowed_registries:
                    raise AliasResolutionFailed
                kernel_config['image_ref'] = requested_image_ref
        except AliasResolutionFailed:
            raise ImageNotFound('unknown alias or disallowed registry')

        for i in range(node['replicas']):
            kernel_config['cluster_idx'] = i + 1
            kernel_configs.append(
                check_typed_dict(kernel_config, KernelEnqueueingConfig),  # type: ignore
            )

    session_creation_id = secrets.token_urlsafe(16)
    start_event = asyncio.Event()
    kernel_id: Optional[KernelId] = None
    session_creation_tracker = app_ctx.session_creation_tracker
    session_creation_tracker[session_creation_id] = start_event
    current_task = asyncio.current_task()
    assert current_task is not None

    try:
        async with root_ctx.db.begin_readonly() as conn:
            owner_uuid, group_id, resource_policy = await _query_userinfo(request, params, conn)

        session_id = await asyncio.shield(app_ctx.database_ptask_group.create_task(
            root_ctx.registry.enqueue_session(
                session_creation_id,
                params['session_name'],
                owner_access_key,
                kernel_configs,
                params['scaling_group'],
                params['sess_type'],
                resource_policy,
                user_scope=UserScope(
                    domain_name=params['domain'],  # type: ignore
                    group_id=group_id,
                    user_uuid=owner_uuid,
                    user_role=request['user']['role'],
                ),
                session_tag=params['tag'],
            ),
        ))
        kernel_id = cast(KernelId, session_id)  # the main kernel's ID is the session ID.
        resp['kernelId'] = str(kernel_id)
        resp['status'] = 'PENDING'
        resp['servicePorts'] = []
        resp['created'] = True

        if not params['enqueue_only']:
            app_ctx.pending_waits.add(current_task)
            max_wait = params['max_wait_seconds']
            try:
                if max_wait > 0:
                    with timeout(max_wait):
                        await start_event.wait()
                else:
                    await start_event.wait()
            except asyncio.TimeoutError:
                resp['status'] = 'TIMEOUT'
            else:
                await asyncio.sleep(0.5)
                async with root_ctx.db.begin_readonly() as conn:
                    query = (
                        sa.select([
                            kernels.c.status,
                            kernels.c.service_ports,
                        ])
                        .select_from(kernels)
                        .where(kernels.c.id == kernel_id)
                    )
                    result = await conn.execute(query)
                    row = result.first()
                if row['status'] == KernelStatus.RUNNING:
                    resp['status'] = 'RUNNING'
                    for item in row['service_ports']:
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
                        resp['servicePorts'].append(response_dict)
                else:
                    resp['status'] = row['status'].name

    except asyncio.CancelledError:
        raise
    except BackendError:
        log.exception('GET_OR_CREATE: exception')
        raise
    except UnknownImageReference:
        raise UnknownImageReferenceError(f"Unknown image reference: {params['image']}")
    except Exception:
        await root_ctx.error_monitor.capture_exception()
        log.exception('GET_OR_CREATE: unexpected error!')
        raise InternalServerError
    finally:
        app_ctx.pending_waits.discard(current_task)
        del session_creation_tracker[session_creation_id]
    return web.json_response(resp, status=201)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key('login_session_token', default=None): t.Null | t.String,
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
async def start_service(request: web.Request, params: Mapping[str, Any]) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    session_name: str = request.match_info['session_name']
    app_ctx: PrivateContext = request.app['session.context']
    access_key: AccessKey = request['keypair']['access_key']
    service: str = params['app']
    myself = asyncio.current_task()
    assert myself is not None
    try:
        kernel = await asyncio.shield(app_ctx.database_ptask_group.create_task(
            root_ctx.registry.get_session(session_name, access_key),
        ))
    except (SessionNotFound, TooManySessionsMatched):
        raise

    query = (sa.select([scaling_groups.c.wsproxy_addr])
               .select_from(scaling_groups)
               .where((scaling_groups.c.name == kernel['scaling_group'])))

    async with root_ctx.db.begin_readonly() as conn:
        result = await conn.execute(query)
        sgroup = result.first()
    wsproxy_addr = sgroup['wsproxy_addr']
    if not wsproxy_addr:
        raise ServiceUnavailable('No coordinator configured for this resource group')

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
            else:
                # using the default (primary) port of the app
                if 'host_ports' not in sport:
                    host_port = sport['host_port']  # legacy kernels
                else:
                    host_port = sport['host_ports'][0]
            break
    else:
        raise AppNotFound(f'{session_name}:{service}')

    await asyncio.shield(app_ctx.database_ptask_group.create_task(
        root_ctx.registry.increment_session_usage(session_name, access_key),
    ))

    opts: MutableMapping[str, Union[None, str, List[str]]] = {}
    if params['arguments'] is not None:
        opts['arguments'] = json.loads(params['arguments'])
    if params['envs'] is not None:
        opts['envs'] = json.loads(params['envs'])

    result = await asyncio.shield(
        app_ctx.rpc_ptask_group.create_task(
            root_ctx.registry.start_service(session_name, access_key, service, opts),
        ),
    )
    if result['status'] == 'failed':
        raise InternalServerError(
            "Failed to launch the app service",
            extra_data=result['error'])

    async with aiohttp.ClientSession() as session:
        async with session.post(f'{wsproxy_addr}/v2/conf', json={
            'login_session_token': params['login_session_token'],
            'kernel_host': kernel_host,
            'kernel_port': host_port,
        }) as resp:
            token_json = await resp.json()
            return web.json_response({
                'token': token_json['token'],
                'wsproxy_addr': wsproxy_addr,
            })


async def handle_kernel_creation_lifecycle(
    app: web.Application,
    source: AgentId,
    event: (KernelPreparingEvent | KernelPullingEvent | KernelCreatingEvent |
            KernelStartedEvent | KernelCancelledEvent),
) -> None:
    """
    Update the database and perform post_create_kernel() upon
    the events for each step of kernel creation.

    To avoid race condition between consumer and subscriber event handlers,
    we only have this handler to subscribe all kernel creation events,
    but distinguish which one to process using a unique creation_id
    generated when initiating the create_kernels() agent RPC call.
    """
    root_ctx: RootContext = app['_root.context']
    # ck_id = (event.creation_id, event.kernel_id)
    ck_id = event.kernel_id
    if ck_id in root_ctx.registry.kernel_creation_tracker:
        log.debug(
            "handle_kernel_creation_lifecycle: ev:{} k:{}",
            event.name, event.kernel_id,
        )
    if isinstance(event, KernelPreparingEvent):
        # State transition is done by the DoPrepareEvent handler inside the scheduler-distpacher object.
        pass
    elif isinstance(event, KernelPullingEvent):
        await root_ctx.registry.set_kernel_status(event.kernel_id, KernelStatus.PULLING, event.reason)
    elif isinstance(event, KernelCreatingEvent):
        await root_ctx.registry.set_kernel_status(event.kernel_id, KernelStatus.PREPARING, event.reason)
    elif isinstance(event, KernelStartedEvent):
        # post_create_kernel() coroutines are waiting for the creation tracker events to be set.
        if (tracker := root_ctx.registry.kernel_creation_tracker.get(ck_id)) and not tracker.done():
            tracker.set_result(None)
    elif isinstance(event, KernelCancelledEvent):
        if (tracker := root_ctx.registry.kernel_creation_tracker.get(ck_id)) and not tracker.done():
            tracker.cancel()


async def handle_kernel_termination_lifecycle(
    app: web.Application,
    source: AgentId,
    event: KernelTerminatingEvent | KernelTerminatedEvent,
) -> None:
    root_ctx: RootContext = app['_root.context']
    if isinstance(event, KernelTerminatingEvent):
        # The destroy_kernel() API handler will set the "TERMINATING" status.
        pass
    elif isinstance(event, KernelTerminatedEvent):
        await root_ctx.registry.mark_kernel_terminated(event.kernel_id, event.reason, event.exit_code)
        await root_ctx.registry.check_session_terminated(event.kernel_id, event.reason)


async def handle_session_creation_lifecycle(
    app: web.Application,
    source: AgentId,
    event: SessionStartedEvent | SessionCancelledEvent,
) -> None:
    """
    Update the database according to the session-level lifecycle events
    published by the manager.
    """
    app_ctx: PrivateContext = app['session.context']
    if event.creation_id not in app_ctx.session_creation_tracker:
        return
    log.debug('handle_session_creation_lifecycle: ev:{} s:{}', event.name, event.session_id)
    if isinstance(event, SessionStartedEvent):
        if tracker := app_ctx.session_creation_tracker.get(event.creation_id):
            tracker.set()
    elif isinstance(event, SessionCancelledEvent):
        if tracker := app_ctx.session_creation_tracker.get(event.creation_id):
            tracker.set()


async def handle_session_termination_lifecycle(
    app: web.Application,
    agent_id: AgentId,
    event: SessionTerminatedEvent,
) -> None:
    """
    Update the database according to the session-level lifecycle events
    published by the manager.
    """
    root_ctx: RootContext = app['_root.context']
    if isinstance(event, SessionTerminatedEvent):
        await root_ctx.registry.mark_session_terminated(event.session_id, event.reason)


async def handle_destroy_session(
    app: web.Application,
    source: AgentId,
    event: DoTerminateSessionEvent,
) -> None:
    root_ctx: RootContext = app['_root.context']
    await root_ctx.registry.destroy_session(
        functools.partial(
            root_ctx.registry.get_session_by_session_id,
            event.session_id,
        ),
        forced=False,
        reason=event.reason or 'killed-by-event',
    )


async def handle_kernel_stat_sync(
    app: web.Application,
    agent_id: AgentId,
    event: DoSyncKernelStatsEvent,
) -> None:
    root_ctx: RootContext = app['_root.context']
    if root_ctx.local_config['debug']['periodic-sync-stats']:
        await root_ctx.registry.sync_kernel_stats(event.kernel_ids)


async def _make_session_callback(data: dict[str, Any], url: yarl.URL) -> None:
    log_func = log.info
    log_msg: str = ""
    log_fmt: str = ""
    log_arg: Any = None
    begin = time.monotonic()
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30.0),
        ) as session:
            try:
                async with session.post(url, json=data) as response:
                    if response.content_length is not None and response.content_length > 0:
                        log_func = log.warning
                        log_msg = "warning"
                        log_fmt = "{3[0]} {3[1]} - the callback response body was not empty! " \
                                  "(len: {3[2]:,} bytes)"
                        log_arg = (response.status, response.reason, response.content_length)
                    else:
                        log_msg = "result"
                        log_fmt = "{3[0]} {3[1]}"
                        log_arg = (response.status, response.reason)
            except aiohttp.ClientError as e:
                log_func = log.warning
                log_msg, log_fmt, log_arg = "failed", "{3}", repr(e)
    except asyncio.CancelledError:
        log_func = log.warning
        log_msg, log_fmt, log_arg = "cancelled", "elapsed_time = {3:.6f}", time.monotonic() - begin
    except asyncio.TimeoutError:
        log_func = log.warning
        log_msg, log_fmt, log_arg = "timeout", "elapsed_time = {3:.6f}", time.monotonic() - begin
    finally:
        log_func(
            "Session lifecycle callback " + log_msg + " (e:{0}, s:{1}, url:{2}): " + log_fmt,
            data['event'], data['session_id'], url,
            log_arg,
        )


async def invoke_session_callback(
    app: web.Application,
    source: AgentId,
    event: SessionEnqueuedEvent | SessionScheduledEvent | SessionPreparingEvent
        | SessionStartedEvent | SessionCancelledEvent | SessionTerminatedEvent
        | SessionSuccessEvent | SessionFailureEvent,
) -> None:
    app_ctx: PrivateContext = app['session.context']
    root_ctx: RootContext = app['_root.context']
    data = {
        "type": "session_lifecycle",
        "event": event.name.removeprefix("session_"),
        "session_id": str(event.session_id),
        "when": datetime.now(tzutc()).isoformat(),
    }
    try:
        async with root_ctx.db.begin_readonly() as db:
            session = await root_ctx.registry.get_session_by_session_id(
                event.session_id,
                db_connection=db,
            )
    except SessionNotFound:
        return
    url = session['callback_url']
    if url is None:
        return
    app_ctx.webhook_ptask_group.create_task(
        _make_session_callback(data, url),
    )


async def handle_batch_result(
    app: web.Application,
    source: AgentId,
    event: SessionSuccessEvent | SessionFailureEvent,
) -> None:
    """
    Update the database according to the batch-job completion results
    """
    root_ctx: RootContext = app['_root.context']
    if isinstance(event, SessionSuccessEvent):
        await root_ctx.registry.set_session_result(event.session_id, True, event.exit_code)
    elif isinstance(event, SessionFailureEvent):
        await root_ctx.registry.set_session_result(event.session_id, False, event.exit_code)
    await root_ctx.registry.destroy_session(
        functools.partial(
            root_ctx.registry.get_session_by_session_id,
            event.session_id,
        ),
        reason='task-finished',
    )


async def handle_agent_lifecycle(
    app: web.Application,
    source: AgentId,
    event: AgentStartedEvent | AgentTerminatedEvent,
) -> None:
    root_ctx: RootContext = app['_root.context']
    if isinstance(event, AgentStartedEvent):
        log.info('instance_lifecycle: ag:{0} joined ({1})', source, event.reason)
        await root_ctx.registry.update_instance(source, {
            'status': AgentStatus.ALIVE,
        })
    if isinstance(event, AgentTerminatedEvent):
        if event.reason == 'agent-lost':
            await root_ctx.registry.mark_agent_terminated(source, AgentStatus.LOST)
        elif event.reason == 'agent-restart':
            log.info('agent@{0} restarting for maintenance.', source)
            await root_ctx.registry.update_instance(source, {
                'status': AgentStatus.RESTARTING,
            })
        else:
            # On normal instance termination, kernel_terminated events were already
            # triggered by the agent.
            await root_ctx.registry.mark_agent_terminated(source, AgentStatus.TERMINATED)


async def handle_agent_heartbeat(
    app: web.Application,
    source: AgentId,
    event: AgentHeartbeatEvent,
) -> None:
    root_ctx: RootContext = app['_root.context']
    await root_ctx.registry.handle_heartbeat(source, event.agent_info)


@catch_unexpected(log)
async def check_agent_lost(root_ctx: RootContext, interval: float) -> None:
    try:
        now = datetime.now(tzutc())
        timeout = timedelta(seconds=root_ctx.local_config['manager']['heartbeat-timeout'])

        async def _check_impl(r: aioredis.Redis):
            async for agent_id, prev in r.hscan_iter('agent.last_seen'):
                prev = datetime.fromtimestamp(float(prev), tzutc())
                if now - prev > timeout:
                    await root_ctx.event_producer.produce_event(
                        AgentTerminatedEvent("agent-lost"),
                        source=agent_id.decode())

        await redis.execute(root_ctx.redis_live, _check_impl)
    except asyncio.CancelledError:
        pass


async def handle_kernel_log(
    app: web.Application,
    source: AgentId,
    event: DoSyncKernelLogsEvent,
) -> None:
    root_ctx: RootContext = app['_root.context']
    redis_conn = redis.get_redis_object(root_ctx.shared_config.data['redis'], db=REDIS_STREAM_DB)
    # The log data is at most 10 MiB.
    log_buffer = BytesIO()
    log_key = f'containerlog.{event.container_id}'
    try:
        list_size = await redis.execute(
            redis_conn,
            lambda r: r.llen(log_key),
        )
        if list_size is None:
            # The log data is expired due to a very slow event delivery.
            # (should never happen!)
            log.warning('tried to store console logs for cid:{}, but the data is expired',
                        event.container_id)
            return
        for _ in range(list_size):
            # Read chunk-by-chunk to allow interleaving with other Redis operations.
            chunk = await redis.execute(redis_conn, lambda r: r.lpop(log_key))
            if chunk is None:  # maybe missing
                log_buffer.write(b"(container log unavailable)\n")
                break
            log_buffer.write(chunk)
        try:
            log_data = log_buffer.getvalue()

            async def _update_log() -> None:
                async with root_ctx.db.begin() as conn:
                    update_query = (
                        sa.update(kernels)
                        .values(container_log=log_data)
                        .where(kernels.c.id == event.kernel_id)
                    )
                    await conn.execute(update_query)

            await execute_with_retry(_update_log)
        finally:
            # Clear the log data from Redis when done.
            await redis.execute(
                redis_conn,
                lambda r: r.delete(log_key),
            )
    finally:
        log_buffer.close()
        await redis_conn.close()


async def report_stats(root_ctx: RootContext, interval: float) -> None:
    stats_monitor = root_ctx.stats_monitor
    await stats_monitor.report_metric(
        GAUGE, 'ai.backend.manager.coroutines', len(asyncio.all_tasks()))

    all_inst_ids = [
        inst_id async for inst_id
        in root_ctx.registry.enumerate_instances()]
    await stats_monitor.report_metric(
        GAUGE, 'ai.backend.manager.agent_instances', len(all_inst_ids))

    async with root_ctx.db.begin_readonly() as conn:
        query = (
            sa.select([sa.func.count()])
            .select_from(kernels)
            .where(
                (kernels.c.cluster_role == DEFAULT_ROLE) &
                (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
            )
        )
        n = await conn.scalar(query)
        await stats_monitor.report_metric(
            GAUGE, 'ai.backend.manager.active_kernels', n)
        subquery = (
            sa.select([sa.func.count()])
            .select_from(keypairs)
            .where(keypairs.c.is_active == true())
            .group_by(keypairs.c.user_id)
        )
        query = sa.select([sa.func.count()]).select_from(subquery.alias())
        n = await conn.scalar(query)
        await stats_monitor.report_metric(
            GAUGE, 'ai.backend.users.has_active_key', n)

        subquery = subquery.where(keypairs.c.last_used != null())
        query = sa.select([sa.func.count()]).select_from(subquery.alias())
        n = await conn.scalar(query)
        await stats_monitor.report_metric(
            GAUGE, 'ai.backend.users.has_used_key', n)

        """
        query = sa.select([sa.func.count()]).select_from(usage)
        n = await conn.scalar(query)
        await stats_monitor.report_metric(
            GAUGE, 'ai.backend.manager.accum_kernels', n)
        """


@server_status_required(ALL_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(['name', 'clientSessionToken']) >> 'session_name':
            t.Regexp(r'^(?=.{4,64}$)\w[\w.-]*\w$', re.ASCII),
    }),
)
async def rename_session(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    session_name = request.match_info['session_name']
    new_name = params['session_name']
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info(
        'RENAME_SESSION (ak:{0}/{1}, s:{2}, newname:{3})',
        request, owner_access_key, session_name, new_name,
    )
    async with root_ctx.db.begin() as conn:
        compute_session = await root_ctx.registry.get_session(
            session_name, owner_access_key,
            allow_stale=True,
            db_connection=conn,
            for_update=True,
        )
        if compute_session['status'] != KernelStatus.RUNNING:
            raise InvalidAPIParameters('Can\'t change name of not running session')
        update_query = (
            sa.update(kernels)
            .values(session_name=new_name)
            .where(kernels.c.session_id == compute_session['session_id'])
        )
        await conn.execute(update_query)

    return web.Response(status=204)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key('forced', default='false'): t.ToBool(),
        t.Key('owner_access_key', default=None): t.Null | t.String,
    }))
async def destroy(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    session_name = request.match_info['session_name']
    if params['forced'] and request['user']['role'] not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        raise InsufficientPrivilege('You are not allowed to force-terminate')
    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    # domain_name = None
    # if requester_access_key != owner_access_key and \
    #         not request['is_superadmin'] and request['is_admin']:
    #     domain_name = request['user']['domain_name']
    log.info('DESTROY (ak:{0}/{1}, s:{2}, forced:{3})',
             requester_access_key, owner_access_key, session_name, params['forced'])
    last_stat = await root_ctx.registry.destroy_session(
        functools.partial(
            root_ctx.registry.get_session,
            session_name, owner_access_key,
            # domain_name=domain_name,
        ),
        forced=params['forced'],
    )
    resp = {
        'stats': last_stat,
    }
    return web.json_response(resp, status=200)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key('id'): t.String(),
    }))
async def match_sessions(request: web.Request, params: Any) -> web.Response:
    """
    A quick session-ID matcher API for use with auto-completion in CLI.
    """
    root_ctx: RootContext = request.app['_root.context']
    id_or_name_prefix = params['id']
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info('MATCH_SESSIONS(ak:{0}/{1}, prefix:{2})',
             requester_access_key, owner_access_key, id_or_name_prefix)
    matches: List[Dict[str, Any]] = []
    async with root_ctx.db.begin_readonly() as conn:
        session_infos = await match_session_ids(
            id_or_name_prefix,
            owner_access_key,
            db_connection=conn,
        )
    if session_infos:
        matches.extend({
            'id': str(item['session_id']),
            'name': item['session_name'],
            'status': item['status'].name,
        } for item in session_infos)
    return web.json_response({
        'matches': matches,
    }, status=200)


@server_status_required(READ_ALLOWED)
@auth_required
async def get_info(request: web.Request) -> web.Response:
    # NOTE: This API should be replaced with GraphQL version.
    resp = {}
    root_ctx: RootContext = request.app['_root.context']
    session_name = request.match_info['session_name']
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info('GET_INFO (ak:{0}/{1}, s:{2})',
             requester_access_key, owner_access_key, session_name)
    try:
        await root_ctx.registry.increment_session_usage(session_name, owner_access_key)
        kern = await root_ctx.registry.get_session(session_name, owner_access_key)
        resp['domainName'] = kern['domain_name']
        resp['groupId'] = str(kern['group_id'])
        resp['userId'] = str(kern['user_uuid'])
        resp['lang'] = kern['image']  # legacy
        resp['image'] = kern['image']
        resp['architecture'] = kern['architecture']
        resp['registry'] = kern['registry']
        resp['tag'] = kern['tag']

        # Resource occupation
        resp['containerId'] = str(kern['container_id'])
        resp['occupiedSlots'] = str(kern['occupied_slots'])
        resp['occupiedShares'] = str(kern['occupied_shares'])
        resp['environ'] = str(kern['environ'])

        # Lifecycle
        resp['status'] = kern['status'].name  # "e.g. 'KernelStatus.RUNNING' -> 'RUNNING' "
        resp['statusInfo'] = str(kern['status_info'])
        resp['statusData'] = kern['status_data']
        age = datetime.now(tzutc()) - kern['created_at']
        resp['age'] = int(age.total_seconds() * 1000)  # age in milliseconds
        resp['creationTime'] = str(kern['created_at'])
        resp['terminationTime'] = str(kern['terminated_at']) if kern['terminated_at'] else None

        resp['numQueriesExecuted'] = kern['num_queries']
        resp['lastStat'] = kern['last_stat']

        # Resource limits collected from agent heartbeats were erased, as they were deprecated
        # TODO: factor out policy/image info as a common repository

        log.info('information retrieved: {0!r}', resp)
    except BackendError:
        log.exception('GET_INFO: exception')
        raise
    return web.json_response(resp, status=200)


@server_status_required(READ_ALLOWED)
@auth_required
async def restart(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    session_creation_id = secrets.token_urlsafe(16)
    session_name = request.match_info['session_name']
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info('RESTART (ak:{0}/{1}, s:{2})',
             requester_access_key, owner_access_key, session_name)
    try:
        await root_ctx.registry.increment_session_usage(session_name, owner_access_key)
        await root_ctx.registry.restart_session(session_creation_id, session_name, owner_access_key)
    except BackendError:
        log.exception('RESTART: exception')
        raise
    except:
        await root_ctx.error_monitor.capture_exception(context={'user': request['user']['uuid']})
        log.exception('RESTART: unexpected error')
        raise web.HTTPInternalServerError
    return web.Response(status=204)


@server_status_required(READ_ALLOWED)
@auth_required
async def execute(request: web.Request) -> web.Response:
    resp = {}
    root_ctx: RootContext = request.app['_root.context']
    session_name = request.match_info['session_name']
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    try:
        params = await request.json(loads=json.loads)
        log.info('EXECUTE(ak:{0}/{1}, s:{2})',
                 requester_access_key, owner_access_key, session_name)
    except json.decoder.JSONDecodeError:
        log.warning('EXECUTE: invalid/missing parameters')
        raise InvalidAPIParameters
    try:
        await root_ctx.registry.increment_session_usage(session_name, owner_access_key)
        api_version = request['api_version']
        if api_version[0] == 1:
            run_id = params.get('runId', secrets.token_hex(8))
            mode = 'query'
            code = params.get('code', None)
            opts = None
        elif api_version[0] >= 2:
            assert 'runId' in params, 'runId is missing!'
            run_id = params['runId']  # maybe None
            assert params.get('mode'), 'mode is missing or empty!'
            mode = params['mode']
            assert mode in {'query', 'batch', 'complete', 'continue', 'input'}, \
                   'mode has an invalid value.'
            if mode in {'continue', 'input'}:
                assert run_id is not None, 'continuation requires explicit run ID'
            code = params.get('code', None)
            opts = params.get('options', None)
        else:
            raise RuntimeError("should not reach here")
        # handle cases when some params are deliberately set to None
        if code is None: code = ''  # noqa
        if opts is None: opts = {}  # noqa
        if mode == 'complete':
            # For legacy
            resp['result'] = await root_ctx.registry.get_completions(
                session_name, owner_access_key, code, opts)
        else:
            raw_result = await root_ctx.registry.execute(
                session_name, owner_access_key,
                api_version, run_id, mode, code, opts,
                flush_timeout=2.0)
            if raw_result is None:
                # the kernel may have terminated from its side,
                # or there was interruption of agents.
                resp['result'] = {
                    'status': 'finished',
                    'runId': run_id,
                    'exitCode': 130,
                    'options': {},
                    'files': [],
                    'console': [],
                }
                return web.json_response(resp, status=200)
            # Keep internal/public API compatilibty
            result = {
                'status': raw_result['status'],
                'runId': raw_result['runId'],
                'exitCode': raw_result.get('exitCode'),
                'options': raw_result.get('options'),
                'files': raw_result.get('files'),
            }
            if api_version[0] == 1:
                result['stdout'] = raw_result.get('stdout')
                result['stderr'] = raw_result.get('stderr')
                result['media'] = raw_result.get('media')
                result['html'] = raw_result.get('html')
            else:
                result['console'] = raw_result.get('console')
            resp['result'] = result
    except AssertionError as e:
        log.warning('EXECUTE: invalid/missing parameters: {0!r}', e)
        raise InvalidAPIParameters(extra_msg=e.args[0])
    except BackendError:
        log.exception('EXECUTE: exception')
        raise
    return web.json_response(resp, status=200)


@server_status_required(READ_ALLOWED)
@auth_required
async def interrupt(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    session_name = request.match_info['session_name']
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info('INTERRUPT(ak:{0}/{1}, s:{2})',
             requester_access_key, owner_access_key, session_name)
    try:
        await root_ctx.registry.increment_session_usage(session_name, owner_access_key)
        await root_ctx.registry.interrupt_session(session_name, owner_access_key)
    except BackendError:
        log.exception('INTERRUPT: exception')
        raise
    return web.Response(status=204)


@server_status_required(READ_ALLOWED)
@auth_required
async def complete(request: web.Request) -> web.Response:
    resp = {
        'result': {
            'status': 'finished',
            'completions': [],
        },
    }
    root_ctx: RootContext = request.app['_root.context']
    session_name = request.match_info['session_name']
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    try:
        params = await request.json(loads=json.loads)
        log.info('COMPLETE(ak:{0}/{1}, s:{2})',
                 requester_access_key, owner_access_key, session_name)
    except json.decoder.JSONDecodeError:
        raise InvalidAPIParameters
    try:
        code = params.get('code', '')
        opts = params.get('options', None) or {}
        await root_ctx.registry.increment_session_usage(session_name, owner_access_key)
        resp['result'] = cast(
            Dict[str, Any],
            await root_ctx.registry.get_completions(session_name, owner_access_key, code, opts),
        )
    except AssertionError:
        raise InvalidAPIParameters
    except BackendError:
        log.exception('COMPLETE: exception')
        raise
    return web.json_response(resp, status=200)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key('service_name'): t.String,
    }))
async def shutdown_service(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    session_name = request.match_info['session_name']
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info('SHUTDOWN_SERVICE (ak:{0}/{1}, s:{2})',
             requester_access_key, owner_access_key, session_name)
    service_name = params.get('service_name')
    try:
        await root_ctx.registry.shutdown_service(session_name, owner_access_key, service_name)
    except BackendError:
        log.exception('SHUTDOWN_SERVICE: exception')
        raise
    return web.Response(status=204)


@server_status_required(READ_ALLOWED)
@auth_required
async def upload_files(request: web.Request) -> web.Response:
    loop = asyncio.get_event_loop()
    reader = await request.multipart()
    root_ctx: RootContext = request.app['_root.context']
    session_name = request.match_info['session_name']
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info('UPLOAD_FILE (ak:{0}/{1}, s:{2})',
             requester_access_key, owner_access_key, session_name)
    try:
        await root_ctx.registry.increment_session_usage(session_name, owner_access_key)
        file_count = 0
        upload_tasks = []
        async for file in aiotools.aiter(reader.next, None):
            if file_count == 20:
                raise InvalidAPIParameters('Too many files')
            file_count += 1
            # This API handles only small files, so let's read it at once.
            chunks = []
            recv_size = 0
            while True:
                chunk = await file.read_chunk(size=1048576)
                if not chunk:
                    break
                chunk_size = len(chunk)
                if recv_size + chunk_size >= 1048576:
                    raise InvalidAPIParameters('Too large file')
                chunks.append(chunk)
                recv_size += chunk_size
            data = file.decode(b''.join(chunks))
            log.debug('received file: {0} ({1:,} bytes)', file.filename, recv_size)
            t = loop.create_task(
                root_ctx.registry.upload_file(session_name, owner_access_key,
                                              file.filename, data))
            upload_tasks.append(t)
        await asyncio.gather(*upload_tasks)
    except BackendError:
        log.exception('UPLOAD_FILES: exception')
        raise
    return web.Response(status=204)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        tx.MultiKey('files'): t.List(t.String),
    }))
async def download_files(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    session_name = request.match_info['session_name']
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    files = params.get('files')
    log.info(
        'DOWNLOAD_FILE (ak:{0}/{1}, s:{2}, path:{3!r})',
        requester_access_key, owner_access_key, session_name,
        files[0],
    )
    try:
        assert len(files) <= 5, 'Too many files'
        await root_ctx.registry.increment_session_usage(session_name, owner_access_key)
        # TODO: Read all download file contents. Need to fix by using chuncking, etc.
        results = await asyncio.gather(
            *map(
                functools.partial(root_ctx.registry.download_file, session_name, owner_access_key),
                files,
            ),
        )
        log.debug('file(s) inside container retrieved')
    except asyncio.CancelledError:
        raise
    except BackendError:
        log.exception('DOWNLOAD_FILE: exception')
        raise
    except (ValueError, FileNotFoundError):
        raise InvalidAPIParameters('The file is not found.')
    except Exception:
        await root_ctx.error_monitor.capture_exception(context={'user': request['user']['uuid']})
        log.exception('DOWNLOAD_FILE: unexpected error!')
        raise InternalServerError

    with aiohttp.MultipartWriter('mixed') as mpwriter:
        headers = multidict.MultiDict({'Content-Encoding': 'identity'})
        for tarbytes in results:
            mpwriter.append(tarbytes, headers)
        return web.Response(body=mpwriter, status=200)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key('file'): t.String,
    }))
async def download_single(request: web.Request, params: Any) -> web.Response:
    """
    Download a single file from the scratch root. Only for small files.
    """
    root_ctx: RootContext = request.app['_root.context']
    session_name = request.match_info['session_name']
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    file = params['file']
    log.info(
        'DOWNLOAD_SINGLE (ak:{0}/{1}, s:{2}, path:{3!r})',
        requester_access_key, owner_access_key, session_name, file,
    )
    try:
        await root_ctx.registry.increment_session_usage(session_name, owner_access_key)
        result = await root_ctx.registry.download_file(session_name, owner_access_key, file)
    except asyncio.CancelledError:
        raise
    except BackendError:
        log.exception('DOWNLOAD_SINGLE: exception')
        raise
    except (ValueError, FileNotFoundError):
        raise InvalidAPIParameters('The file is not found.')
    except Exception:
        await root_ctx.error_monitor.capture_exception(context={'user': request['user']['uuid']})
        log.exception('DOWNLOAD_SINGLE: unexpected error!')
        raise InternalServerError
    return web.Response(body=result, status=200)


@server_status_required(READ_ALLOWED)
@auth_required
async def list_files(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    try:
        session_name = request.match_info['session_name']
        requester_access_key, owner_access_key = await get_access_key_scopes(request)
        params = await request.json(loads=json.loads)
        path = params.get('path', '.')
        log.info(
            'LIST_FILES (ak:{0}/{1}, s:{2}, path:{3})',
            requester_access_key, owner_access_key, session_name, path,
        )
    except (asyncio.TimeoutError, AssertionError,
            json.decoder.JSONDecodeError) as e:
        log.warning('LIST_FILES: invalid/missing parameters, {0!r}', e)
        raise InvalidAPIParameters(extra_msg=str(e.args[0]))
    resp: MutableMapping[str, Any] = {}
    try:
        await root_ctx.registry.increment_session_usage(session_name, owner_access_key)
        result = await root_ctx.registry.list_files(session_name, owner_access_key, path)
        resp.update(result)
        log.debug('container file list for {0} retrieved', path)
    except asyncio.CancelledError:
        raise
    except BackendError:
        log.exception('LIST_FILES: exception')
        raise
    except Exception:
        await root_ctx.error_monitor.capture_exception(context={'user': request['user']['uuid']})
        log.exception('LIST_FILES: unexpected error!')
        raise InternalServerError
    return web.json_response(resp, status=200)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key('owner_access_key', default=None): t.Null | t.String,
    }))
async def get_container_logs(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    session_name: str = request.match_info['session_name']
    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    log.info('GET_CONTAINER_LOG (ak:{}/{}, s:{})',
             requester_access_key, owner_access_key, session_name)
    resp = {'result': {'logs': ''}}
    async with root_ctx.db.begin_readonly() as conn:
        compute_session = await root_ctx.registry.get_session(
            session_name, owner_access_key,
            allow_stale=True,
            db_connection=conn,
        )
        if (
            compute_session['status'] in DEAD_KERNEL_STATUSES
            and compute_session['container_log'] is not None
        ):
            log.debug('returning log from database record')
            resp['result']['logs'] = compute_session['container_log'].decode('utf-8')
            return web.json_response(resp, status=200)
    try:
        registry = root_ctx.registry
        await registry.increment_session_usage(session_name, owner_access_key)
        resp['result']['logs'] = await registry.get_logs_from_agent(session_name, owner_access_key)
        log.debug('returning log from agent')
    except BackendError:
        log.exception('GET_CONTAINER_LOG(ak:{}/{}, s:{}): unexpected error',
                      requester_access_key, owner_access_key, session_name)
        raise
    return web.json_response(resp, status=200)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(['session_name', 'sessionName', 'task_id', 'taskId']) >> 'kernel_id': tx.UUID,
    }))
async def get_task_logs(request: web.Request, params: Any) -> web.StreamResponse:
    log.info('GET_TASK_LOG (ak:{}, k:{})',
             request['keypair']['access_key'], params['kernel_id'])
    root_ctx: RootContext = request.app['_root.context']
    domain_name = request['user']['domain_name']
    user_role = request['user']['role']
    user_uuid = request['user']['uuid']
    kernel_id_str = params['kernel_id'].hex
    async with root_ctx.db.begin_readonly() as conn:
        matched_vfolders = await query_accessible_vfolders(
            conn, user_uuid,
            user_role=user_role, domain_name=domain_name,
            allowed_vfolder_types=['user'],
            extra_vf_conds=(vfolders.c.name == '.logs'))
        if not matched_vfolders:
            raise ObjectNotFound(
                extra_data={'vfolder_name': '.logs'},
                object_name='vfolder',
            )
        log_vfolder = matched_vfolders[0]

    proxy_name, volume_name = root_ctx.storage_manager.split_host(log_vfolder['host'])
    response = web.StreamResponse(status=200)
    response.headers[hdrs.CONTENT_TYPE] = "text/plain"
    prepared = False
    try:
        async with root_ctx.storage_manager.request(
            log_vfolder['host'], 'POST', 'folder/file/fetch',
            json={
                'volume': volume_name,
                'vfid': str(log_vfolder['id']),
                'relpath': str(
                    PurePosixPath('task')
                    / kernel_id_str[:2] / kernel_id_str[2:4]
                    / f'{kernel_id_str[4:]}.log',
                ),
            },
            raise_for_status=True,
        ) as (_, storage_resp):
            while True:
                chunk = await storage_resp.content.read(DEFAULT_CHUNK_SIZE)
                if not chunk:
                    break
                if not prepared:
                    await response.prepare(request)
                    prepared = True
                await response.write(chunk)
    except aiohttp.ClientResponseError as e:
        raise StorageProxyError(status=e.status, extra_msg=e.message)
    finally:
        if prepared:
            await response.write_eof()
    return response


@attr.s(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    session_creation_tracker: Dict[str, asyncio.Event]
    pending_waits: Set[asyncio.Task[None]]
    agent_lost_checker: asyncio.Task[None]
    stats_task: asyncio.Task[None]
    database_ptask_group: aiotools.PersistentTaskGroup
    rpc_ptask_group: aiotools.PersistentTaskGroup
    webhook_ptask_group: aiotools.PersistentTaskGroup


async def init(app: web.Application) -> None:
    root_ctx: RootContext = app['_root.context']
    app_ctx: PrivateContext = app['session.context']
    app_ctx.session_creation_tracker = {}
    app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()
    app_ctx.rpc_ptask_group = aiotools.PersistentTaskGroup()
    app_ctx.webhook_ptask_group = aiotools.PersistentTaskGroup()

    # passive events
    evd = root_ctx.event_dispatcher
    evd.subscribe(KernelPreparingEvent, app, handle_kernel_creation_lifecycle, name="api.session.kprep")
    evd.subscribe(KernelPullingEvent, app, handle_kernel_creation_lifecycle, name="api.session.kpull")
    evd.subscribe(KernelCreatingEvent, app, handle_kernel_creation_lifecycle, name="api.session.kcreat")
    evd.subscribe(KernelStartedEvent, app, handle_kernel_creation_lifecycle, name="api.session.kstart")
    evd.subscribe(KernelCancelledEvent, app, handle_kernel_creation_lifecycle, name="api.session.kstart")
    evd.subscribe(
        SessionStartedEvent, app, handle_session_creation_lifecycle, name="api.session.sstart",
    )
    evd.subscribe(
        SessionCancelledEvent, app, handle_session_creation_lifecycle, name="api.session.scancel",
    )
    evd.consume(
        KernelTerminatingEvent, app, handle_kernel_termination_lifecycle, name="api.session.kterming",
    )
    evd.consume(
        KernelTerminatedEvent, app, handle_kernel_termination_lifecycle, name="api.session.kterm",
    )
    evd.consume(
        SessionTerminatedEvent, app, handle_session_termination_lifecycle, name="api.session.sterm",
    )
    evd.consume(SessionEnqueuedEvent, app, invoke_session_callback)
    evd.consume(SessionScheduledEvent, app, invoke_session_callback)
    evd.consume(SessionPreparingEvent, app, invoke_session_callback)
    evd.consume(SessionStartedEvent, app, invoke_session_callback)
    evd.consume(SessionCancelledEvent, app, invoke_session_callback)
    evd.consume(SessionTerminatedEvent, app, invoke_session_callback)
    evd.consume(SessionSuccessEvent, app, invoke_session_callback)
    evd.consume(SessionFailureEvent, app, invoke_session_callback)
    evd.consume(SessionSuccessEvent, app, handle_batch_result)
    evd.consume(SessionFailureEvent, app, handle_batch_result)
    evd.consume(AgentStartedEvent, app, handle_agent_lifecycle)
    evd.consume(AgentTerminatedEvent, app, handle_agent_lifecycle)
    evd.consume(AgentHeartbeatEvent, app, handle_agent_heartbeat)

    # action-trigerring events
    evd.consume(DoSyncKernelStatsEvent, app, handle_kernel_stat_sync, name="api.session.synckstat")
    evd.consume(DoSyncKernelLogsEvent, app, handle_kernel_log, name="api.session.syncklog")
    evd.consume(DoTerminateSessionEvent, app, handle_destroy_session, name="api.session.doterm")

    app_ctx.pending_waits = set()

    # Scan ALIVE agents
    app_ctx.agent_lost_checker = aiotools.create_timer(
        functools.partial(check_agent_lost, root_ctx), 1.0)
    app_ctx.stats_task = aiotools.create_timer(
        functools.partial(report_stats, root_ctx), 5.0,
    )


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app['session.context']
    app_ctx.agent_lost_checker.cancel()
    await app_ctx.agent_lost_checker
    app_ctx.stats_task.cancel()
    await app_ctx.stats_task

    await app_ctx.webhook_ptask_group.shutdown()
    await app_ctx.database_ptask_group.shutdown()
    await app_ctx.rpc_ptask_group.shutdown()

    await cancel_tasks(app_ctx.pending_waits)


def create_app(default_cors_options: CORSOptions) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app['api_versions'] = (1, 2, 3, 4)
    app['session.context'] = PrivateContext()
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route('POST', '', create_from_params))
    cors.add(app.router.add_route('POST', '/_/create', create_from_params))
    cors.add(app.router.add_route('POST', '/_/create-from-template', create_from_template))
    cors.add(app.router.add_route('POST', '/_/create-cluster', create_cluster))
    cors.add(app.router.add_route('GET',  '/_/match', match_sessions))
    session_resource = cors.add(app.router.add_resource(r'/{session_name}'))
    cors.add(session_resource.add_route('GET',    get_info))
    cors.add(session_resource.add_route('PATCH',  restart))
    cors.add(session_resource.add_route('DELETE', destroy))
    cors.add(session_resource.add_route('POST',   execute))
    task_log_resource = cors.add(app.router.add_resource(r'/_/logs'))
    cors.add(task_log_resource.add_route('HEAD', get_task_logs))
    cors.add(task_log_resource.add_route('GET',  get_task_logs))
    cors.add(app.router.add_route('GET',  '/{session_name}/logs', get_container_logs))
    cors.add(app.router.add_route('POST', '/{session_name}/rename', rename_session))
    cors.add(app.router.add_route('POST', '/{session_name}/interrupt', interrupt))
    cors.add(app.router.add_route('POST', '/{session_name}/complete', complete))
    cors.add(app.router.add_route('POST', '/{session_name}/shutdown-service', shutdown_service))
    cors.add(app.router.add_route('POST', '/{session_name}/upload', upload_files))
    cors.add(app.router.add_route('GET',  '/{session_name}/download', download_files))
    cors.add(app.router.add_route('GET',  '/{session_name}/download_single', download_single))
    cors.add(app.router.add_route('GET',  '/{session_name}/files', list_files))
    cors.add(app.router.add_route('POST', '/{session_name}/start-service', start_service))
    return app, []

"""
Resource preset APIs.
"""

import copy
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import functools
import json
import logging
import re
from typing import (
    Any,
    Iterable,
    TYPE_CHECKING,
    Tuple,
    MutableMapping,
)

import aiohttp
from aiohttp import web
import aiohttp_cors
from aioredis import Redis
from aioredis.client import Pipeline as RedisPipeline
from async_timeout import timeout as _timeout
from dateutil.tz import tzutc
import msgpack
import sqlalchemy as sa
import trafaret as t
import yarl

from ai.backend.common import redis, validators as tx
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.utils import nmget
from ai.backend.common.types import DefaultForUnspecified, ResourceSlot

from ..models import (
    agents, resource_presets,
    domains, groups, kernels, users,
    AgentStatus,
    association_groups_users,
    query_allowed_sgroups,
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    RESOURCE_USAGE_KERNEL_STATUSES, LIVE_STATUS,
)
from .auth import auth_required, superadmin_required
from .exceptions import (
    InvalidAPIParameters,
)
from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__name__))

_json_loads = functools.partial(json.loads, parse_float=Decimal)


@auth_required
async def list_presets(request: web.Request) -> web.Response:
    """
    Returns the list of all resource presets.
    """
    log.info('LIST_PRESETS (ak:{})', request['keypair']['access_key'])
    root_ctx: RootContext = request.app['_root.context']
    await root_ctx.shared_config.get_resource_slots()
    async with root_ctx.db.begin_readonly() as conn:
        query = (
            sa.select([resource_presets])
            .select_from(resource_presets)
        )
        # TODO: uncomment when we implement scaling group.
        # scaling_group = request.query.get('scaling_group')
        # if scaling_group is not None:
        #     query = query.where(resource_presets.c.scaling_group == scaling_group)
        resp: MutableMapping[str, Any] = {'presets': []}
        async for row in (await conn.stream(query)):
            preset_slots = row['resource_slots'].normalize_slots(ignore_unknown=True)
            resp['presets'].append({
                'name': row['name'],
                'shared_memory': str(row['shared_memory']) if row['shared_memory'] else None,
                'resource_slots': preset_slots.to_json(),
            })
        return web.json_response(resp, status=200)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key('scaling_group', default=None): t.Null | t.String,
        t.Key('group', default='default'): t.String,
    }))
async def check_presets(request: web.Request, params: Any) -> web.Response:
    """
    Returns the list of all resource presets in the current scaling group,
    with additional information including allocatability of each preset,
    amount of total remaining resources, and the current keypair resource limits.
    """
    root_ctx: RootContext = request.app['_root.context']
    try:
        access_key = request['keypair']['access_key']
        resource_policy = request['keypair']['resource_policy']
        domain_name = request['user']['domain_name']
        # TODO: uncomment when we implement scaling group.
        # scaling_group = request.query.get('scaling_group')
        # assert scaling_group is not None, 'scaling_group parameter is missing.'
    except (json.decoder.JSONDecodeError, AssertionError) as e:
        raise InvalidAPIParameters(extra_msg=str(e.args[0]))
    known_slot_types = await root_ctx.shared_config.get_resource_slots()
    resp: MutableMapping[str, Any] = {
        'keypair_limits': None,
        'keypair_using': None,
        'keypair_remaining': None,
        'scaling_group_remaining': None,
        'scaling_groups': None,
        'presets': [],
    }
    log.info('CHECK_PRESETS (ak:{}, g:{}, sg:{})',
             request['keypair']['access_key'], params['group'], params['scaling_group'])

    async with root_ctx.db.begin_readonly() as conn:
        # Check keypair resource limit.
        keypair_limits = ResourceSlot.from_policy(resource_policy, known_slot_types)
        keypair_occupied = await root_ctx.registry.get_keypair_occupancy(access_key, conn=conn)
        keypair_remaining = keypair_limits - keypair_occupied

        # Check group resource limit and get group_id.
        j = sa.join(
            groups, association_groups_users,
            association_groups_users.c.group_id == groups.c.id,
        )
        query = (
            sa.select([groups.c.id, groups.c.total_resource_slots])
            .select_from(j)
            .where(
                (association_groups_users.c.user_id == request['user']['uuid']) &
                (groups.c.name == params['group']) &
                (domains.c.name == domain_name),
            )
        )
        result = await conn.execute(query)
        row = result.first()
        group_id = row['id']
        group_resource_slots = row['total_resource_slots']
        if group_id is None:
            raise InvalidAPIParameters('Unknown user group')
        group_resource_policy = {
            'total_resource_slots': group_resource_slots,
            'default_for_unspecified': DefaultForUnspecified.UNLIMITED,
        }
        group_limits = ResourceSlot.from_policy(group_resource_policy, known_slot_types)
        group_occupied = await root_ctx.registry.get_group_occupancy(group_id, conn=conn)
        group_remaining = group_limits - group_occupied

        # Check domain resource limit.
        query = (sa.select([domains.c.total_resource_slots])
                   .where(domains.c.name == domain_name))
        domain_resource_slots = await conn.scalar(query)
        domain_resource_policy = {
            'total_resource_slots': domain_resource_slots,
            'default_for_unspecified': DefaultForUnspecified.UNLIMITED,
        }
        domain_limits = ResourceSlot.from_policy(domain_resource_policy, known_slot_types)
        domain_occupied = await root_ctx.registry.get_domain_occupancy(domain_name, conn=conn)
        domain_remaining = domain_limits - domain_occupied

        # Take minimum remaining resources. There's no need to merge limits and occupied.
        # To keep legacy, we just merge all remaining slots into `keypair_remainig`.
        for slot in known_slot_types:
            keypair_remaining[slot] = min(
                keypair_remaining[slot],
                group_remaining[slot],
                domain_remaining[slot],
            )

        # Prepare per scaling group resource.
        sgroups = await query_allowed_sgroups(conn, domain_name, group_id, access_key)
        sgroup_names = [sg.name for sg in sgroups]
        if params['scaling_group'] is not None:
            if params['scaling_group'] not in sgroup_names:
                raise InvalidAPIParameters('Unknown scaling group')
            sgroup_names = [params['scaling_group']]
        per_sgroup = {
            sgname: {
                'using': ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()}),
                'remaining': ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()}),
            } for sgname in sgroup_names
        }

        # Per scaling group resource using from resource occupying kernels.
        query = (
            sa.select([kernels.c.occupied_slots, kernels.c.scaling_group])
            .select_from(kernels)
            .where(
                (kernels.c.user_uuid == request['user']['uuid']) &
                (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)) &
                (kernels.c.scaling_group.in_(sgroup_names)),
            )
        )
        async for row in (await conn.stream(query)):
            per_sgroup[row['scaling_group']]['using'] += row['occupied_slots']

        # Per scaling group resource remaining from agents stats.
        sgroup_remaining = ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()})
        query = (
            sa.select([agents.c.available_slots, agents.c.occupied_slots, agents.c.scaling_group])
            .select_from(agents)
            .where(
                (agents.c.status == AgentStatus.ALIVE) &
                (agents.c.scaling_group.in_(sgroup_names)),
            )
        )
        agent_slots = []
        async for row in (await conn.stream(query)):
            remaining = row['available_slots'] - row['occupied_slots']
            remaining += ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()})
            sgroup_remaining += remaining
            agent_slots.append(remaining)
            per_sgroup[row['scaling_group']]['remaining'] += remaining

        # Take maximum allocatable resources per sgroup.
        for sgname, sgfields in per_sgroup.items():
            for rtype, slots in sgfields.items():
                if rtype == 'remaining':
                    for slot in known_slot_types.keys():
                        if slot in slots:
                            slots[slot] = min(keypair_remaining[slot], slots[slot])
                per_sgroup[sgname][rtype] = slots.to_json()  # type: ignore  # it's serialization
        for slot in known_slot_types.keys():
            sgroup_remaining[slot] = min(keypair_remaining[slot], sgroup_remaining[slot])

        # Fetch all resource presets in the current scaling group.
        query = (
            sa.select([resource_presets])
            .select_from(resource_presets)
        )
        async for row in (await conn.stream(query)):
            # Check if there are any agent that can allocate each preset.
            allocatable = False
            preset_slots = row['resource_slots'].normalize_slots(ignore_unknown=True)
            for agent_slot in agent_slots:
                if agent_slot >= preset_slots and keypair_remaining >= preset_slots:
                    allocatable = True
                    break
            resp['presets'].append({
                'name': row['name'],
                'resource_slots': preset_slots.to_json(),
                'shared_memory': str(row['shared_memory']) if row['shared_memory'] is not None else None,
                'allocatable': allocatable,
            })

        # Return group resource status as NaN if not allowed.
        group_resource_visibility = \
            await root_ctx.shared_config.get_raw('config/api/resources/group_resource_visibility')
        group_resource_visibility = t.ToBool().check(group_resource_visibility)
        if not group_resource_visibility:
            group_limits = ResourceSlot({k: Decimal('NaN') for k in known_slot_types.keys()})
            group_occupied = ResourceSlot({k: Decimal('NaN') for k in known_slot_types.keys()})
            group_remaining = ResourceSlot({k: Decimal('NaN') for k in known_slot_types.keys()})

        resp['keypair_limits'] = keypair_limits.to_json()
        resp['keypair_using'] = keypair_occupied.to_json()
        resp['keypair_remaining'] = keypair_remaining.to_json()
        resp['group_limits'] = group_limits.to_json()
        resp['group_using'] = group_occupied.to_json()
        resp['group_remaining'] = group_remaining.to_json()
        resp['scaling_group_remaining'] = sgroup_remaining.to_json()
        resp['scaling_groups'] = per_sgroup
    return web.json_response(resp, status=200)


@server_status_required(READ_ALLOWED)
@superadmin_required
async def recalculate_usage(request: web.Request) -> web.Response:
    """
    Update `keypair_resource_usages` in redis and `agents.c.occupied_slots`.

    Those two values are sometimes out of sync. In that case, calling this API
    re-calculates the values for running containers and updates them in DB.
    """
    log.info('RECALCULATE_USAGE ()')
    root_ctx: RootContext = request.app['_root.context']
    await root_ctx.registry.recalc_resource_usage()
    return web.json_response({}, status=200)


async def get_container_stats_for_period(request: web.Request, start_date, end_date, group_ids=None):
    root_ctx: RootContext = request.app['_root.context']
    async with root_ctx.db.begin_readonly() as conn:
        j = (
            kernels
            .join(groups, groups.c.id == kernels.c.group_id)
            .join(users, users.c.uuid == kernels.c.user_uuid)
        )
        query = (
            sa.select([
                kernels.c.id,
                kernels.c.container_id,
                kernels.c.session_name,
                kernels.c.access_key,
                kernels.c.agent,
                kernels.c.domain_name,
                kernels.c.group_id,
                kernels.c.attached_devices,
                kernels.c.occupied_slots,
                kernels.c.resource_opts,
                kernels.c.vfolder_mounts,
                kernels.c.mounts,
                kernels.c.image,
                kernels.c.status,
                kernels.c.status_changed,
                kernels.c.last_stat,
                kernels.c.created_at,
                kernels.c.terminated_at,
                groups.c.name,
                users.c.email,
            ])
            .select_from(j)
            .where(
                # Filter sessions which existence period overlaps with requested period
                ((kernels.c.terminated_at >= start_date) & (kernels.c.created_at < end_date) &
                 (kernels.c.status.in_(RESOURCE_USAGE_KERNEL_STATUSES))) |
                # Or, filter running sessions which created before requested end_date
                ((kernels.c.created_at < end_date) & (kernels.c.status.in_(LIVE_STATUS))),
            )
            .order_by(sa.asc(kernels.c.terminated_at))
        )
        if group_ids:
            query = query.where(kernels.c.group_id.in_(group_ids))
        result = await conn.execute(query)
        rows = result.fetchall()

    def _pipe_builder(r: Redis) -> RedisPipeline:
        pipe = r.pipeline()
        for row in rows:
            pipe.get(str(row['id']))
        return pipe

    raw_stats = await redis.execute(root_ctx.redis_stat, _pipe_builder)

    objs_per_group = {}
    local_tz = root_ctx.shared_config['system']['timezone']

    for row, raw_stat in zip(rows, raw_stats):
        group_id = str(row['group_id'])
        last_stat = row['last_stat']
        if not last_stat:
            if raw_stat is None:
                log.warn('stat object for {} not found on redis, skipping', str(row['id']))
                continue
            last_stat = msgpack.unpackb(raw_stat)
        nfs = None
        if row['vfolder_mounts']:
            # For >=22.03, return used host directories instead of volume host, which is not so useful.
            nfs = list(set([str(mount.host_path) for mount in row['vfolder_mounts']]))
        elif row['mounts'] and isinstance(row['mounts'][0], list):
            # For the kernel records that have legacy contents of `mounts`.
            nfs = list(set([mount[2] for mount in row['mounts']]))
        if row['terminated_at'] is None:
            used_time = used_days = None
        else:
            used_time = str(row['terminated_at'] - row['created_at'])
            used_days = (row['terminated_at'].astimezone(local_tz).toordinal() -
                         row['created_at'].astimezone(local_tz).toordinal() + 1)
        device_type = set()
        smp = 0
        gpu_mem_allocated = 0
        if row.attached_devices and row.attached_devices.get('cuda'):
            for dev_info in row.attached_devices['cuda']:
                if dev_info.get('model_name'):
                    device_type.add(dev_info['model_name'])
                smp += int(nmget(dev_info, 'data.smp', 0))
                gpu_mem_allocated += int(nmget(dev_info, 'data.mem', 0))
        gpu_allocated = 0
        if 'cuda.devices' in row.occupied_slots:
            gpu_allocated = row.occupied_slots['cuda.devices']
        if 'cuda.shares' in row.occupied_slots:
            gpu_allocated = row.occupied_slots['cuda.shares']
        c_info = {
            'id': str(row['id']),
            'container_id': row['container_id'],
            'domain_name': row['domain_name'],
            'group_id': str(row['group_id']),
            'group_name': row['name'],
            'name': row['session_name'],
            'access_key': row['access_key'],
            'email': row['email'],
            'agent': row['agent'],
            'cpu_allocated': float(row.occupied_slots.get('cpu', 0)),
            'cpu_used': float(nmget(last_stat, 'cpu_used.current', 0)),
            'mem_allocated': int(row.occupied_slots.get('mem', 0)),
            'mem_used': int(nmget(last_stat, 'mem.capacity', 0)),
            'shared_memory': int(nmget(row.resource_opts, 'shmem', 0)),
            'disk_allocated': 0,  # TODO: disk quota limit
            'disk_used': (int(nmget(last_stat, 'io_scratch_size/stats.max', 0, '/'))),
            'io_read': int(nmget(last_stat, 'io_read.current', 0)),
            'io_write': int(nmget(last_stat, 'io_write.current', 0)),
            'used_time': used_time,
            'used_days': used_days,
            'device_type': list(device_type),
            'smp': float(smp),
            'gpu_mem_allocated': float(gpu_mem_allocated),
            'gpu_allocated': float(gpu_allocated),  # devices or shares
            'nfs': nfs,
            'image_id': row['image'],  # TODO: image id
            'image_name': row['image'],
            'created_at': str(row['created_at']),
            'terminated_at': str(row['terminated_at']),
            'status': row['status'].name,
            'status_changed': str(row['status_changed']),
        }
        if group_id not in objs_per_group:
            objs_per_group[group_id] = {
                'domain_name': row['domain_name'],
                'g_id': group_id,
                'g_name': row['name'],  # this is group's name
                'g_cpu_allocated': c_info['cpu_allocated'],
                'g_cpu_used': c_info['cpu_used'],
                'g_mem_allocated': c_info['mem_allocated'],
                'g_mem_used': c_info['mem_used'],
                'g_shared_memory': c_info['shared_memory'],
                'g_disk_allocated': c_info['disk_allocated'],
                'g_disk_used': c_info['disk_used'],
                'g_io_read': c_info['io_read'],
                'g_io_write': c_info['io_write'],
                'g_device_type': copy.deepcopy(c_info['device_type']),
                'g_smp': c_info['smp'],
                'g_gpu_mem_allocated': c_info['gpu_mem_allocated'],
                'g_gpu_allocated': c_info['gpu_allocated'],
                'c_infos': [c_info],
            }
        else:
            objs_per_group[group_id]['g_cpu_allocated'] += c_info['cpu_allocated']
            objs_per_group[group_id]['g_cpu_used'] += c_info['cpu_used']
            objs_per_group[group_id]['g_mem_allocated'] += c_info['mem_allocated']
            objs_per_group[group_id]['g_mem_used'] += c_info['mem_used']
            objs_per_group[group_id]['g_shared_memory'] += c_info['shared_memory']
            objs_per_group[group_id]['g_disk_allocated'] += c_info['disk_allocated']
            objs_per_group[group_id]['g_disk_used'] += c_info['disk_used']
            objs_per_group[group_id]['g_io_read'] += c_info['io_read']
            objs_per_group[group_id]['g_io_write'] += c_info['io_write']
            for device in c_info['device_type']:
                if device not in objs_per_group[group_id]['g_device_type']:
                    g_dev_type = objs_per_group[group_id]['g_device_type']
                    g_dev_type.append(device)
                    objs_per_group[group_id]['g_device_type'] = list(set(g_dev_type))
            objs_per_group[group_id]['g_smp'] += c_info['smp']
            objs_per_group[group_id]['g_gpu_mem_allocated'] += c_info['gpu_mem_allocated']
            objs_per_group[group_id]['g_gpu_allocated'] += c_info['gpu_allocated']
            objs_per_group[group_id]['c_infos'].append(c_info)
    return list(objs_per_group.values())


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.MultiKey('group_ids'): t.List(t.String) | t.Null,
        t.Key('month'): t.Regexp(r'^\d{6}', re.ASCII),
    }),
    loads=_json_loads)
async def usage_per_month(request: web.Request, params: Any) -> web.Response:
    """
    Return usage statistics of terminated containers for a specified month.
    The date/time comparison is done using the configured timezone.

    :param group_ids: If not None, query containers only in those groups.
    :param month: The year-month to query usage statistics. ex) "202006" to query for Jun 2020
    """
    log.info('USAGE_PER_MONTH (g:[{}], month:{})',
             ','.join(params['group_ids']), params['month'])
    root_ctx: RootContext = request.app['_root.context']
    local_tz = root_ctx.shared_config['system']['timezone']
    try:
        start_date = datetime.strptime(params['month'], '%Y%m').replace(tzinfo=local_tz)
        end_date = start_date + relativedelta(months=+1)
    except ValueError:
        raise InvalidAPIParameters(extra_msg='Invalid date values')
    resp = await get_container_stats_for_period(request, start_date, end_date, params['group_ids'])
    log.debug('container list are retrieved for month {0}', params['month'])
    return web.json_response(resp, status=200)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        t.Key('group_id'): t.String | t.Null,
        t.Key('start_date'): t.Regexp(r'^\d{8}$', re.ASCII),
        t.Key('end_date'): t.Regexp(r'^\d{8}$', re.ASCII),
    }),
    loads=_json_loads)
async def usage_per_period(request: web.Request, params: Any) -> web.Response:
    """
    Return usage statistics of terminated containers belonged to the given group for a specified
    period in dates.
    The date/time comparison is done using the configured timezone.

    :param group_id: If not None, query containers only in the group.
    :param start_date str: "yyyymmdd" format.
    :param end_date str: "yyyymmdd" format.
    """
    root_ctx: RootContext = request.app['_root.context']
    group_id = params['group_id']
    local_tz = root_ctx.shared_config['system']['timezone']
    try:
        start_date = datetime.strptime(params['start_date'], '%Y%m%d').replace(tzinfo=local_tz)
        end_date = datetime.strptime(params['end_date'], '%Y%m%d').replace(tzinfo=local_tz)
        end_date = end_date + timedelta(days=1)  # include sessions in end_date
        if end_date - start_date > timedelta(days=100):
            raise InvalidAPIParameters('Cannot query more than 100 days')
    except ValueError:
        raise InvalidAPIParameters(extra_msg='Invalid date values')
    if end_date <= start_date:
        raise InvalidAPIParameters(extra_msg='end_date must be later than start_date.')
    log.info('USAGE_PER_MONTH (g:{}, start_date:{}, end_date:{})',
             group_id, start_date, end_date)
    group_ids = [group_id] if group_id is not None else None
    resp = await get_container_stats_for_period(request, start_date, end_date, group_ids=group_ids)
    log.debug('container list are retrieved from {0} to {1}', start_date, end_date)
    return web.json_response(resp, status=200)


async def get_time_binned_monthly_stats(request: web.Request, user_uuid=None):
    """
    Generate time-binned (15 min) stats for the last one month (2880 points).
    The structure of the result would be:

        [
          # [
          #     timestamp, num_sessions,
          #     cpu_allocated, mem_allocated, gpu_allocated,
          #     io_read, io_write, scratch_used,
          # ]
            [1562083808.657106, 1, 1.2, 1073741824, ...],
            [1562084708.657106, 2, 4.0, 1073741824, ...],
        ]

    Note that the timestamp is in UNIX-timestamp.
    """
    # Get all or user kernels for the last month from DB.
    time_window = 900  # 15 min
    now = datetime.now(tzutc())
    start_date = now - timedelta(days=30)
    root_ctx: RootContext = request.app['_root.context']
    async with root_ctx.db.begin_readonly() as conn:
        query = (
            sa.select([kernels])
            .select_from(kernels)
            .where(
                (kernels.c.terminated_at >= start_date) &
                (kernels.c.status.in_(RESOURCE_USAGE_KERNEL_STATUSES)),
            )
            .order_by(sa.asc(kernels.c.created_at))
        )
        if user_uuid is not None:
            query = query.where(kernels.c.user_uuid == user_uuid)
        result = await conn.execute(query)
        rows = result.fetchall()

    # Build time-series of time-binned stats.
    rowcount = len(rows)
    now_ts = now.timestamp()
    start_date_ts = start_date.timestamp()
    ts = start_date_ts
    idx = 0
    tseries = []
    # Iterate over each time window.
    while ts < now_ts:
        # Initialize the time-binned stats.
        num_sessions = 0
        cpu_allocated = 0
        mem_allocated = 0
        gpu_allocated = Decimal(0)
        io_read_bytes = 0
        io_write_bytes = 0
        disk_used = 0
        # Accumulate stats for containers overlapping with this time window.
        while idx < rowcount and \
              ts + time_window > rows[idx].created_at.timestamp() and \
              ts < rows[idx].terminated_at.timestamp():
            # Accumulate stats for overlapping containers in this time window.
            row = rows[idx]
            num_sessions += 1
            cpu_allocated += int(row.occupied_slots.get('cpu', 0))
            mem_allocated += int(row.occupied_slots.get('mem', 0))
            if 'cuda.devices' in row.occupied_slots:
                gpu_allocated += int(row.occupied_slots['cuda.devices'])
            if 'cuda.shares' in row.occupied_slots:
                gpu_allocated += Decimal(row.occupied_slots['cuda.shares'])
            raw_stat = await redis.execute(root_ctx.redis_stat, lambda r: r.get(str(row['id'])))
            if raw_stat:
                last_stat = msgpack.unpackb(raw_stat)
                io_read_bytes += int(nmget(last_stat, 'io_read.current', 0))
                io_write_bytes += int(nmget(last_stat, 'io_write.current', 0))
                disk_used += int(nmget(last_stat, 'io_scratch_size/stats.max', 0, '/'))
            idx += 1
        stat = {
            "date": ts,
            "num_sessions": {
                "value": num_sessions,
                "unit_hint": "count",
            },
            "cpu_allocated": {
                "value": cpu_allocated,
                "unit_hint": "count",
            },
            "mem_allocated": {
                "value": mem_allocated,
                "unit_hint": "bytes",
            },
            "gpu_allocated": {
                "value": float(gpu_allocated),
                "unit_hint": "count",
            },
            "io_read_bytes": {
                "value": io_read_bytes,
                "unit_hint": "bytes",
            },
            "io_write_bytes": {
                "value": io_write_bytes,
                "unit_hint": "bytes",
            },
            "disk_used": {
                "value ": disk_used,
                "unit_hint": "bytes",
            },
        }
        tseries.append(stat)
        ts += time_window
    return tseries


@server_status_required(READ_ALLOWED)
@auth_required
async def user_month_stats(request: web.Request) -> web.Response:
    """
    Return time-binned (15 min) stats for terminated user sessions
    over last 30 days.
    """
    access_key = request['keypair']['access_key']
    user_uuid = request['user']['uuid']
    log.info('USER_LAST_MONTH_STATS (ak:{}, u:{})', access_key, user_uuid)
    stats = await get_time_binned_monthly_stats(request, user_uuid=user_uuid)
    return web.json_response(stats, status=200)


@server_status_required(READ_ALLOWED)
@superadmin_required
async def admin_month_stats(request: web.Request) -> web.Response:
    """
    Return time-binned (15 min) stats for all terminated sessions
    over last 30 days.
    """
    log.info('ADMIN_LAST_MONTH_STATS ()')
    stats = await get_time_binned_monthly_stats(request, user_uuid=None)
    return web.json_response(stats, status=200)


async def get_watcher_info(request: web.Request, agent_id: str) -> dict:
    """
    Get watcher information.

    :return addr: address of agent watcher (eg: http://127.0.0.1:6009)
    :return token: agent watcher token ("insecure" if not set in config server)
    """
    root_ctx: RootContext = request.app['_root.context']
    token = root_ctx.shared_config['watcher']['token']
    if token is None:
        token = 'insecure'
    agent_ip = await root_ctx.shared_config.etcd.get(f'nodes/agents/{agent_id}/ip')
    raw_watcher_port = await root_ctx.shared_config.etcd.get(
        f'nodes/agents/{agent_id}/watcher_port',
    )
    watcher_port = 6099 if raw_watcher_port is None else int(raw_watcher_port)
    # TODO: watcher scheme is assumed to be http
    addr = yarl.URL(f'http://{agent_ip}:{watcher_port}')
    return {
        'addr': addr,
        'token': token,
    }


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(['agent_id', 'agent']): t.String,
    }))
async def get_watcher_status(request: web.Request, params: Any) -> web.Response:
    log.info('GET_WATCHER_STATUS (ag:{})', params['agent_id'])
    watcher_info = await get_watcher_info(request, params['agent_id'])
    connector = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=connector) as sess:
        with _timeout(5.0):
            headers = {'X-BackendAI-Watcher-Token': watcher_info['token']}
            async with sess.get(watcher_info['addr'], headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return web.json_response(data, status=resp.status)
                else:
                    data = await resp.text()
                    return web.Response(text=data, status=resp.status)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(['agent_id', 'agent']): t.String,
    }))
async def watcher_agent_start(request: web.Request, params: Any) -> web.Response:
    log.info('WATCHER_AGENT_START (ag:{})', params['agent_id'])
    watcher_info = await get_watcher_info(request, params['agent_id'])
    connector = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=connector) as sess:
        with _timeout(20.0):
            watcher_url = watcher_info['addr'] / 'agent/start'
            headers = {'X-BackendAI-Watcher-Token': watcher_info['token']}
            async with sess.post(watcher_url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return web.json_response(data, status=resp.status)
                else:
                    data = await resp.text()
                    return web.Response(text=data, status=resp.status)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(['agent_id', 'agent']): t.String,
    }))
async def watcher_agent_stop(request: web.Request, params: Any) -> web.Response:
    log.info('WATCHER_AGENT_STOP (ag:{})', params['agent_id'])
    watcher_info = await get_watcher_info(request, params['agent_id'])
    connector = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=connector) as sess:
        with _timeout(20.0):
            watcher_url = watcher_info['addr'] / 'agent/stop'
            headers = {'X-BackendAI-Watcher-Token': watcher_info['token']}
            async with sess.post(watcher_url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return web.json_response(data, status=resp.status)
                else:
                    data = await resp.text()
                    return web.Response(text=data, status=resp.status)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(['agent_id', 'agent']): t.String,
    }))
async def watcher_agent_restart(request: web.Request, params: Any) -> web.Response:
    log.info('WATCHER_AGENT_RESTART (ag:{})', params['agent_id'])
    watcher_info = await get_watcher_info(request, params['agent_id'])
    connector = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=connector) as sess:
        with _timeout(20.0):
            watcher_url = watcher_info['addr'] / 'agent/restart'
            headers = {'X-BackendAI-Watcher-Token': watcher_info['token']}
            async with sess.post(watcher_url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return web.json_response(data, status=resp.status)
                else:
                    data = await resp.text()
                    return web.Response(text=data, status=resp.status)


def create_app(default_cors_options: CORSOptions) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app['api_versions'] = (4,)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    cors.add(add_route('GET',  '/presets', list_presets))
    cors.add(add_route('POST', '/check-presets', check_presets))
    cors.add(add_route('POST', '/recalculate-usage', recalculate_usage))
    cors.add(add_route('GET',  '/usage/month', usage_per_month))
    cors.add(add_route('GET',  '/usage/period', usage_per_period))
    cors.add(add_route('GET',  '/stats/user/month', user_month_stats))
    cors.add(add_route('GET',  '/stats/admin/month', admin_month_stats))
    cors.add(add_route('GET',  '/watcher', get_watcher_status))
    cors.add(add_route('POST', '/watcher/agent/start', watcher_agent_start))
    cors.add(add_route('POST', '/watcher/agent/stop', watcher_agent_stop))
    cors.add(add_route('POST', '/watcher/agent/restart', watcher_agent_restart))
    return app, []

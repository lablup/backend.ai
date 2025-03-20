"""
Resource preset APIs.
"""

from __future__ import annotations

import functools
import json
import logging
import re
from decimal import Decimal
from http import HTTPStatus
from typing import (
    TYPE_CHECKING,
    Any,
    Iterable,
    Tuple,
)

import aiohttp
import aiohttp_cors
import trafaret as t
import yarl
from aiohttp import web
from async_timeout import timeout as _timeout

from ai.backend.common import validators as tx
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.services.resource.actions.admin_month_stats import AdminMonthStatsAction
from ai.backend.manager.services.resource.actions.check_presets import CheckResourcePresetsAction
from ai.backend.manager.services.resource.actions.list_presets import ListResourcePresetsAction
from ai.backend.manager.services.resource.actions.recalculate_usage import RecalculateUsageAction
from ai.backend.manager.services.resource.actions.usage_per_month import UsagePerMonthAction
from ai.backend.manager.services.resource.actions.usage_per_period import UsagePerPeriodAction
from ai.backend.manager.services.resource.actions.user_month_stats import UserMonthStatsAction

from .auth import auth_required, superadmin_required
from .exceptions import InvalidAPIParameters
from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_json_loads = functools.partial(json.loads, parse_float=Decimal)


@auth_required
async def list_presets(request: web.Request) -> web.Response:
    """
    Returns the list of all resource presets.
    """
    log.info("LIST_PRESETS (ak:{})", request["keypair"]["access_key"])
    root_ctx: RootContext = request.app["_root.context"]
    await root_ctx.shared_config.get_resource_slots()
    async with root_ctx.db.begin_readonly_session() as db_session:
        query = sa.select(ResourcePresetRow)
        query_condition = ResourcePresetRow.scaling_group_name.is_(sa.null())
        scaling_group_name = request.query.get("scaling_group")
        if scaling_group_name is not None:
            query_condition = sa.or_(
                query_condition, ResourcePresetRow.scaling_group_name == scaling_group_name
            )
        query = query.where(query_condition)
        resp: MutableMapping[str, Any] = {"presets": []}
        async for row in await db_session.stream_scalars(query):
            row = cast(ResourcePresetRow, row)
            preset_slots = row.resource_slots.normalize_slots(ignore_unknown=True)
            resp["presets"].append({
                "id": str(row.id),
                "name": row.name,
                "shared_memory": str(row.shared_memory) if row.shared_memory else None,
                "resource_slots": preset_slots.to_json(),
            })
        return web.json_response(resp, status=HTTPStatus.OK)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key("scaling_group", default=None): t.Null | t.String,
        t.Key("group", default="default"): t.String,
    })
)
async def check_presets(request: web.Request, params: Any) -> web.Response:
    """
    Returns the list of all resource presets in the current scaling group,
    with additional information including allocatability of each preset,
    amount of total remaining resources, and the current keypair resource limits.
    """
    root_ctx: RootContext = request.app["_root.context"]
    try:
        access_key = request["keypair"]["access_key"]
        resource_policy = request["keypair"]["resource_policy"]
        domain_name = request["user"]["domain_name"]
        # TODO: uncomment when we implement scaling group.
        # scaling_group = request.query.get('scaling_group')
        # assert scaling_group is not None, 'scaling_group parameter is missing.'
    except (json.decoder.JSONDecodeError, AssertionError) as e:
        raise InvalidAPIParameters(extra_msg=str(e.args[0]))

    log.info(
        "CHECK_PRESETS (ak:{}, g:{}, sg:{})",
        access_key,
        params["group"],
        params["scaling_group"],
    )

    result = await root_ctx.processors.resource.check_presets.wait_for_complete(
        CheckResourcePresetsAction(
            access_key=access_key,
            resource_policy=resource_policy,
            domain_name=domain_name,
            user_id=request["user"]["uuid"],
            group=params["group"],
            scaling_group=params["scaling_group"],
        )
    )

    resp = {
        "presets": result.presets,
        "keypair_limits": result.keypair_limits,
        "keypair_using": result.keypair_using,
        "keypair_remaining": result.keypair_remaining,
        "group_limits": result.group_limits,
        "group_using": result.group_using,
        "group_remaining": result.group_remaining,
        "scaling_group_remaining": result.scaling_group_remaining,
        "scaling_groups": result.scaling_groups,
    }

        # Check domain resource limit.
        query = sa.select([domains.c.total_resource_slots]).where(domains.c.name == domain_name)
        domain_resource_slots = await conn.scalar(query)
        domain_resource_policy = {
            "total_resource_slots": domain_resource_slots,
            "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
        }
        domain_limits = ResourceSlot.from_policy(domain_resource_policy, known_slot_types)
        domain_occupied = await root_ctx.registry.get_domain_occupancy(
            domain_name, db_sess=SASession(conn)
        )
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
        if params["scaling_group"] is not None:
            if params["scaling_group"] not in sgroup_names:
                raise InvalidAPIParameters("Unknown scaling group")
            sgroup_names = [params["scaling_group"]]
        per_sgroup = {
            sgname: {
                "using": ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()}),
                "remaining": ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()}),
            }
            for sgname in sgroup_names
        }

        # Per scaling group resource using from resource occupying kernels.
        j = sa.join(KernelRow, SessionRow, KernelRow.session_id == SessionRow.id)
        query = (
            sa.select([KernelRow.occupied_slots, SessionRow.scaling_group_name])
            .select_from(j)
            .where(
                (KernelRow.user_uuid == request["user"]["uuid"])
                & (KernelRow.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                & (SessionRow.scaling_group_name.in_(sgroup_names)),
            )
        )
        async for row in await conn.stream(query):
            per_sgroup[row["scaling_group_name"]]["using"] += row["occupied_slots"]

        # Per scaling group resource remaining from agents stats.
        sgroup_remaining = ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()})
        query = (
            sa.select([agents.c.available_slots, agents.c.occupied_slots, agents.c.scaling_group])
            .select_from(agents)
            .where(
                (agents.c.status == AgentStatus.ALIVE) & (agents.c.scaling_group.in_(sgroup_names)),
            )
        )
        agent_slots = []
        async for row in await conn.stream(query):
            remaining = row["available_slots"] - row["occupied_slots"]
            remaining += ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()})
            sgroup_remaining += remaining
            agent_slots.append(remaining)
            per_sgroup[row["scaling_group"]]["remaining"] += remaining

        # Take maximum allocatable resources per sgroup.
        for sgname, sgfields in per_sgroup.items():
            for rtype, slots in sgfields.items():
                if rtype == "remaining":
                    for slot in known_slot_types.keys():
                        if slot in slots:
                            slots[slot] = min(keypair_remaining[slot], slots[slot])
                per_sgroup[sgname][rtype] = slots.to_json()  # type: ignore  # it's serialization
        for slot in known_slot_types.keys():
            sgroup_remaining[slot] = min(keypair_remaining[slot], sgroup_remaining[slot])

        # Fetch all resource presets in the current scaling group.
        resource_preset_query = sa.select(ResourcePresetRow)
        query_condition = ResourcePresetRow.scaling_group_name.is_(sa.null())
        if params["scaling_group"] is not None:
            query_condition = sa.or_(
                query_condition,
                ResourcePresetRow.scaling_group_name == params["scaling_group"],
            )
        resource_preset_query = resource_preset_query.where(query_condition)
        async for row in await SASession(conn).stream_scalars(resource_preset_query):
            # Check if there are any agent that can allocate each preset.
            row = cast(ResourcePresetRow, row)
            allocatable = False
            preset_slots = row.resource_slots.normalize_slots(ignore_unknown=True)
            for agent_slot in agent_slots:
                if agent_slot >= preset_slots and keypair_remaining >= preset_slots:
                    allocatable = True
                    break
            resp["presets"].append({
                "id": str(row.id),
                "name": row.name,
                "resource_slots": preset_slots.to_json(),
                "shared_memory": (
                    str(row.shared_memory) if row.shared_memory is not None else None
                ),
                "allocatable": allocatable,
            })

        # Return group resource status as NaN if not allowed.
        group_resource_visibility = await root_ctx.shared_config.get_raw(
            "config/api/resources/group_resource_visibility"
        )
        group_resource_visibility = t.ToBool().check(group_resource_visibility)
        if not group_resource_visibility:
            group_limits = ResourceSlot({k: Decimal("NaN") for k in known_slot_types.keys()})
            group_occupied = ResourceSlot({k: Decimal("NaN") for k in known_slot_types.keys()})
            group_remaining = ResourceSlot({k: Decimal("NaN") for k in known_slot_types.keys()})

        resp["keypair_limits"] = keypair_limits.to_json()
        resp["keypair_using"] = keypair_occupied.to_json()
        resp["keypair_remaining"] = keypair_remaining.to_json()
        resp["group_limits"] = group_limits.to_json()
        resp["group_using"] = group_occupied.to_json()
        resp["group_remaining"] = group_remaining.to_json()
        resp["scaling_group_remaining"] = sgroup_remaining.to_json()
        resp["scaling_groups"] = per_sgroup
    return web.json_response(resp, status=HTTPStatus.OK)


@server_status_required(READ_ALLOWED)
@superadmin_required
async def recalculate_usage(request: web.Request) -> web.Response:
    """
    Update `keypair_resource_usages` in redis and `agents.c.occupied_slots`.

    Those two values are sometimes out of sync. In that case, calling this API
    re-calculates the values for running containers and updates them in DB.
    """
    log.info("RECALCULATE_USAGE ()")
    root_ctx: RootContext = request.app["_root.context"]
    await root_ctx.registry.recalc_resource_usage()
    return web.json_response({}, status=HTTPStatus.OK)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.MultiKey("group_ids"): t.List(t.String) | t.Null,
        t.Key("month"): t.Regexp(r"^\d{6}", re.ASCII),
    }),
    loads=_json_loads,
)
async def usage_per_month(request: web.Request, params: Any) -> web.Response:
    """
    Return usage statistics of terminated containers for a specified month.
    The date/time comparison is done using the configured timezone.

    :param group_ids: If not None, query containers only in those groups.
    :param month: The year-month to query usage statistics. ex) "202006" to query for Jun 2020
    """
    log.info("USAGE_PER_MONTH (g:[{}], month:{})", ",".join(params["group_ids"]), params["month"])
    root_ctx: RootContext = request.app["_root.context"]
    local_tz = root_ctx.shared_config["system"]["timezone"]
    try:
        start_date = datetime.strptime(params["month"], "%Y%m").replace(tzinfo=local_tz)
        end_date = start_date + relativedelta(months=+1)
    except ValueError:
        raise InvalidAPIParameters(extra_msg="Invalid date values")
    resp = await get_container_stats_for_period(request, start_date, end_date, params["group_ids"])
    log.debug("container list are retrieved for month {0}", params["month"])
    return web.json_response(resp, status=HTTPStatus.OK)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["project_id", "group_id"], default=None): t.Null | t.String,
        t.Key("start_date"): t.Regexp(r"^\d{8}$", re.ASCII),
        t.Key("end_date"): t.Regexp(r"^\d{8}$", re.ASCII),
    }),
    loads=_json_loads,
)
async def usage_per_period(request: web.Request, params: Any) -> web.Response:
    """
    Return usage statistics of terminated containers belonged to the given group for a specified
    period in dates.
    The date/time comparison is done using the configured timezone.

    :param project_id: If not None, query containers only in the project.
    :param start_date str: "yyyymmdd" format.
    :param end_date str: "yyyymmdd" format.
    """
    root_ctx: RootContext = request.app["_root.context"]

    result = await root_ctx.processors.resource.usage_per_period.wait_for_complete(
        UsagePerPeriodAction(
            project_id=params["project_id"],
            start_date=params["start_date"],
            end_date=params["end_date"],
        )
    )
    resp = [p_usage.to_json(child=True) for p_usage in usage_map.values()]
    log.debug("container list are retrieved from {0} to {1}", start_date, end_date)
    return web.json_response(resp, status=HTTPStatus.OK)


@server_status_required(READ_ALLOWED)
@auth_required
async def user_month_stats(request: web.Request) -> web.Response:
    """
    Return time-binned (15 min) stats for terminated user sessions
    over last 30 days.
    """
    access_key = request["keypair"]["access_key"]
    user_uuid = request["user"]["uuid"]
    log.info("USER_LAST_MONTH_STATS (ak:{}, u:{})", access_key, user_uuid)
    stats = await get_time_binned_monthly_stats(request, user_uuid=user_uuid)
    return web.json_response(stats, status=HTTPStatus.OK)


@server_status_required(READ_ALLOWED)
@superadmin_required
async def admin_month_stats(request: web.Request) -> web.Response:
    """
    Return time-binned (15 min) stats for all terminated sessions
    over last 30 days.
    """
    log.info("ADMIN_LAST_MONTH_STATS ()")
    stats = await get_time_binned_monthly_stats(request, user_uuid=None)
    return web.json_response(stats, status=HTTPStatus.OK)


async def get_watcher_info(request: web.Request, agent_id: str) -> dict:
    """
    Get watcher information.

    :return addr: address of agent watcher (eg: http://127.0.0.1:6009)
    :return token: agent watcher token ("insecure" if not set in config server)
    """
    root_ctx: RootContext = request.app["_root.context"]
    token = root_ctx.shared_config["watcher"]["token"]
    if token is None:
        token = "insecure"
    agent_ip = await root_ctx.shared_config.etcd.get(f"nodes/agents/{agent_id}/ip")
    raw_watcher_port = await root_ctx.shared_config.etcd.get(
        f"nodes/agents/{agent_id}/watcher_port",
    )
    watcher_port = 6099 if raw_watcher_port is None else int(raw_watcher_port)
    # TODO: watcher scheme is assumed to be http
    addr = yarl.URL(f"http://{agent_ip}:{watcher_port}")
    return {
        "addr": addr,
        "token": token,
    }


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["agent_id", "agent"]): t.String,
    })
)
async def get_watcher_status(request: web.Request, params: Any) -> web.Response:
    log.info("GET_WATCHER_STATUS (ag:{})", params["agent_id"])
    watcher_info = await get_watcher_info(request, params["agent_id"])
    connector = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=connector) as sess:
        with _timeout(5.0):
            headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
            async with sess.get(watcher_info["addr"], headers=headers) as resp:
                if resp.status == HTTPStatus.OK:
                    data = await resp.json()
                    return web.json_response(data, status=resp.status)
                else:
                    data = await resp.text()
                    return web.Response(text=data, status=resp.status)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["agent_id", "agent"]): t.String,
    })
)
async def watcher_agent_start(request: web.Request, params: Any) -> web.Response:
    log.info("WATCHER_AGENT_START (ag:{})", params["agent_id"])
    watcher_info = await get_watcher_info(request, params["agent_id"])
    connector = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=connector) as sess:
        with _timeout(20.0):
            watcher_url = watcher_info["addr"] / "agent/start"
            headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
            async with sess.post(watcher_url, headers=headers) as resp:
                if resp.status == HTTPStatus.OK:
                    data = await resp.json()
                    return web.json_response(data, status=resp.status)
                else:
                    data = await resp.text()
                    return web.Response(text=data, status=resp.status)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["agent_id", "agent"]): t.String,
    })
)
async def watcher_agent_stop(request: web.Request, params: Any) -> web.Response:
    log.info("WATCHER_AGENT_STOP (ag:{})", params["agent_id"])
    watcher_info = await get_watcher_info(request, params["agent_id"])
    connector = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=connector) as sess:
        with _timeout(20.0):
            watcher_url = watcher_info["addr"] / "agent/stop"
            headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
            async with sess.post(watcher_url, headers=headers) as resp:
                if resp.status == HTTPStatus.OK:
                    data = await resp.json()
                    return web.json_response(data, status=resp.status)
                else:
                    data = await resp.text()
                    return web.Response(text=data, status=resp.status)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["agent_id", "agent"]): t.String,
    })
)
async def watcher_agent_restart(request: web.Request, params: Any) -> web.Response:
    log.info("WATCHER_AGENT_RESTART (ag:{})", params["agent_id"])
    watcher_info = await get_watcher_info(request, params["agent_id"])
    connector = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=connector) as sess:
        with _timeout(20.0):
            watcher_url = watcher_info["addr"] / "agent/restart"
            headers = {"X-BackendAI-Watcher-Token": watcher_info["token"]}
            async with sess.post(watcher_url, headers=headers) as resp:
                if resp.status == HTTPStatus.OK:
                    data = await resp.json()
                    return web.json_response(data, status=resp.status)
                else:
                    data = await resp.text()
                    return web.Response(text=data, status=resp.status)


@superadmin_required
async def get_container_registries(request: web.Request) -> web.Response:
    """
    Returns the list of all registered container registries.
    """
    root_ctx: RootContext = request.app["_root.context"]
    async with root_ctx.db.begin_session() as session:
        _registries = await ContainerRegistryRow.get_known_container_registries(session)

    known_registries = {}
    for project, registries in _registries.items():
        for registry_name, url in registries.items():
            if project not in known_registries:
                known_registries[f"{project}/{registry_name}"] = url.human_repr()

    return web.json_response(known_registries, status=HTTPStatus.OK)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (4,)
    app["prefix"] = "resource"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    cors.add(add_route("GET", "/presets", list_presets))
    cors.add(add_route("GET", "/container-registries", get_container_registries))
    cors.add(add_route("POST", "/check-presets", check_presets))
    cors.add(add_route("POST", "/recalculate-usage", recalculate_usage))
    cors.add(add_route("GET", "/usage/month", usage_per_month))
    cors.add(add_route("GET", "/usage/period", usage_per_period))
    cors.add(add_route("GET", "/stats/user/month", user_month_stats))
    cors.add(add_route("GET", "/stats/admin/month", admin_month_stats))
    cors.add(add_route("GET", "/watcher", get_watcher_status))
    cors.add(add_route("POST", "/watcher/agent/start", watcher_agent_start))
    cors.add(add_route("POST", "/watcher/agent/stop", watcher_agent_stop))
    cors.add(add_route("POST", "/watcher/agent/restart", watcher_agent_restart))
    return app, []

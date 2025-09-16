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

import aiohttp_cors
import trafaret as t
import yarl
from aiohttp import web

from ai.backend.common import validators as tx
from ai.backend.common.types import LegacyResourceSlotState as ResourceSlotState
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.services.agent.actions.get_watcher_status import GetWatcherStatusAction
from ai.backend.manager.services.agent.actions.recalculate_usage import RecalculateUsageAction
from ai.backend.manager.services.agent.actions.watcher_agent_restart import (
    WatcherAgentRestartAction,
)
from ai.backend.manager.services.agent.actions.watcher_agent_start import WatcherAgentStartAction
from ai.backend.manager.services.agent.actions.watcher_agent_stop import WatcherAgentStopAction
from ai.backend.manager.services.container_registry.actions.get_container_registries import (
    GetContainerRegistriesAction,
)
from ai.backend.manager.services.group.actions.usage_per_month import UsagePerMonthAction
from ai.backend.manager.services.group.actions.usage_per_period import UsagePerPeriodAction
from ai.backend.manager.services.resource_preset.actions.check_presets import (
    CheckResourcePresetsAction,
)
from ai.backend.manager.services.resource_preset.actions.list_presets import (
    ListResourcePresetsAction,
)
from ai.backend.manager.services.user.actions.admin_month_stats import AdminMonthStatsAction
from ai.backend.manager.services.user.actions.user_month_stats import UserMonthStatsAction

from ..errors.api import InvalidAPIParameters
from .auth import auth_required, superadmin_required
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

    scaling_group_name = request.query.get("scaling_group")
    result = await root_ctx.processors.resource_preset.list_presets.wait_for_complete(
        ListResourcePresetsAction(
            access_key=request["keypair"]["access_key"],
            scaling_group=scaling_group_name,
        )
    )
    return web.json_response({"presets": result.presets}, status=HTTPStatus.OK)


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

    result = await root_ctx.processors.resource_preset.check_presets.wait_for_complete(
        CheckResourcePresetsAction(
            access_key=access_key,
            resource_policy=resource_policy,
            domain_name=domain_name,
            user_id=request["user"]["uuid"],
            group=params["group"],
            scaling_group=params["scaling_group"],
        )
    )

    # Convert ResourceSlot objects to JSON for API response
    scaling_groups_json = {}
    for sgname, sg_data in result.scaling_groups.items():
        scaling_groups_json[sgname] = {
            ResourceSlotState.OCCUPIED: sg_data[ResourceSlotState.OCCUPIED].to_json(),
            ResourceSlotState.AVAILABLE: sg_data[ResourceSlotState.AVAILABLE].to_json(),
        }

    resp = {
        "presets": result.presets,
        "keypair_limits": result.keypair_limits.to_json(),
        "keypair_using": result.keypair_using.to_json(),
        "keypair_remaining": result.keypair_remaining.to_json(),
        "group_limits": result.group_limits.to_json(),
        "group_using": result.group_using.to_json(),
        "group_remaining": result.group_remaining.to_json(),
        "scaling_group_remaining": result.scaling_group_remaining.to_json(),
        "scaling_groups": scaling_groups_json,
    }

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
    await root_ctx.processors.agent.recalculate_usage.wait_for_complete(RecalculateUsageAction())

    return web.json_response({}, status=HTTPStatus.OK)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        t.Key("group_ids"): tx.DelimiterSeperatedList[str](t.String) | t.Null,
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

    result = await root_ctx.processors.group.usage_per_month.wait_for_complete(
        UsagePerMonthAction(
            group_ids=params["group_ids"],
            month=params["month"],
        )
    )
    return web.json_response(result.result, status=HTTPStatus.OK)


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

    result = await root_ctx.processors.group.usage_per_period.wait_for_complete(
        UsagePerPeriodAction(
            project_id=params["project_id"],
            start_date=params["start_date"],
            end_date=params["end_date"],
        )
    )

    return web.json_response(result.result, status=HTTPStatus.OK)


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
    root_ctx: RootContext = request.app["_root.context"]

    result = await root_ctx.processors.user.user_month_stats.wait_for_complete(
        UserMonthStatsAction(
            user_id=user_uuid,
        )
    )

    return web.json_response(result.stats, status=HTTPStatus.OK)


@server_status_required(READ_ALLOWED)
@superadmin_required
async def admin_month_stats(request: web.Request) -> web.Response:
    """
    Return time-binned (15 min) stats for all terminated sessions
    over last 30 days.
    """
    log.info("ADMIN_LAST_MONTH_STATS ()")
    root_ctx: RootContext = request.app["_root.context"]

    result = await root_ctx.processors.user.admin_month_stats.wait_for_complete(
        AdminMonthStatsAction()
    )

    return web.json_response(result.stats, status=HTTPStatus.OK)


# TODO: get_watcher_info overlaps with service-side method.
# Keeping it because it's used by vfolder.
async def get_watcher_info(request: web.Request, agent_id: str) -> dict:
    """
    Get watcher information.

    :return addr: address of agent watcher (eg: http://127.0.0.1:6009)
    :return token: agent watcher token ("insecure" if not set in config server)
    """
    root_ctx: RootContext = request.app["_root.context"]
    token = root_ctx.config_provider.config.watcher.token
    if token is None:
        token = "insecure"
    agent_ip = await root_ctx.etcd.get(f"nodes/agents/{agent_id}/ip")
    raw_watcher_port = await root_ctx.etcd.get(
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
    root_ctx: RootContext = request.app["_root.context"]

    result = await root_ctx.processors.agent.get_watcher_status.wait_for_complete(
        GetWatcherStatusAction(agent_id=params["agent_id"])
    )

    if result.resp.status == HTTPStatus.OK:
        data = await result.resp.json()
        return web.json_response(data, status=result.resp.status)
    else:
        data = await result.resp.text()
        return web.Response(text=data, status=result.resp.status)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["agent_id", "agent"]): t.String,
    })
)
async def watcher_agent_start(request: web.Request, params: Any) -> web.Response:
    log.info("WATCHER_AGENT_START (ag:{})", params["agent_id"])
    root_ctx: RootContext = request.app["_root.context"]

    result = await root_ctx.processors.agent.watcher_agent_start.wait_for_complete(
        WatcherAgentStartAction(agent_id=params["agent_id"])
    )

    if result.resp.status == HTTPStatus.OK:
        data = await result.resp.json()
        return web.json_response(data, status=result.resp.status)
    else:
        data = await result.resp.text()
        return web.Response(text=data, status=result.resp.status)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["agent_id", "agent"]): t.String,
    })
)
async def watcher_agent_stop(request: web.Request, params: Any) -> web.Response:
    log.info("WATCHER_AGENT_STOP (ag:{})", params["agent_id"])
    root_ctx: RootContext = request.app["_root.context"]

    result = await root_ctx.processors.agent.watcher_agent_stop.wait_for_complete(
        WatcherAgentStopAction(agent_id=params["agent_id"])
    )

    if result.resp.status == HTTPStatus.OK:
        data = await result.resp.json()
        return web.json_response(data, status=result.resp.status)
    else:
        data = await result.resp.text()
        return web.Response(text=data, status=result.resp.status)


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["agent_id", "agent"]): t.String,
    })
)
async def watcher_agent_restart(request: web.Request, params: Any) -> web.Response:
    log.info("WATCHER_AGENT_RESTART (ag:{})", params["agent_id"])
    root_ctx: RootContext = request.app["_root.context"]

    result = await root_ctx.processors.agent.watcher_agent_restart.wait_for_complete(
        WatcherAgentRestartAction(
            agent_id=params["agent_id"],
        )
    )

    if result.resp.status == HTTPStatus.OK:
        data = await result.resp.json()
        return web.json_response(data, status=result.resp.status)
    else:
        data = await result.resp.text()
        return web.Response(text=data, status=result.resp.status)


@superadmin_required
async def get_container_registries(request: web.Request) -> web.Response:
    """
    Returns the list of all registered container registries.
    """
    root_ctx: RootContext = request.app["_root.context"]

    result = (
        await root_ctx.processors.container_registry.get_container_registries.wait_for_complete(
            GetContainerRegistriesAction()
        )
    )

    return web.json_response(result.registries, status=HTTPStatus.OK)


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

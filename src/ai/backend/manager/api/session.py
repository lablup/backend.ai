"""
REST-style session management APIs.
"""

from __future__ import annotations

import asyncio
import functools
import json
import logging
from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated, Any, Optional, cast, get_args
from uuid import UUID

import aiohttp_cors
import aiotools
import attrs
import sqlalchemy as sa
import sqlalchemy.exc
import trafaret as t
from aiohttp import web
from dateutil.tz import tzutc
from pydantic import AliasChoices, Field
from sqlalchemy.sql.expression import null, true

from ai.backend.common.data.session.types import CustomizedImageVisibilityScope
from ai.backend.common.json import read_json
from ai.backend.manager.services.agent.actions.sync_agent_registry import SyncAgentRegistryAction
from ai.backend.manager.services.session.actions.check_and_transit_status import (
    CheckAndTransitStatusAction,
)
from ai.backend.manager.services.session.actions.commit_session import CommitSessionAction
from ai.backend.manager.services.session.actions.complete import CompleteAction
from ai.backend.manager.services.session.actions.convert_session_to_image import (
    ConvertSessionToImageAction,
)
from ai.backend.manager.services.session.actions.create_cluster import CreateClusterAction
from ai.backend.manager.services.session.actions.create_from_params import (
    CreateFromParamsAction,
    CreateFromParamsActionParams,
)
from ai.backend.manager.services.session.actions.create_from_template import (
    CreateFromTemplateAction,
    CreateFromTemplateActionParams,
)
from ai.backend.manager.services.session.actions.destroy_session import DestroySessionAction
from ai.backend.manager.services.session.actions.download_file import DownloadFileAction
from ai.backend.manager.services.session.actions.download_files import DownloadFilesAction
from ai.backend.manager.services.session.actions.execute_session import (
    ExecuteSessionAction,
    ExecuteSessionActionParams,
)
from ai.backend.manager.services.session.actions.get_abusing_report import GetAbusingReportAction
from ai.backend.manager.services.session.actions.get_commit_status import GetCommitStatusAction
from ai.backend.manager.services.session.actions.get_container_logs import GetContainerLogsAction
from ai.backend.manager.services.session.actions.get_dependency_graph import (
    GetDependencyGraphAction,
)
from ai.backend.manager.services.session.actions.get_direct_access_info import (
    GetDirectAccessInfoAction,
)
from ai.backend.manager.services.session.actions.get_session_info import GetSessionInfoAction
from ai.backend.manager.services.session.actions.get_status_history import GetStatusHistoryAction
from ai.backend.manager.services.session.actions.interrupt_session import InterruptSessionAction
from ai.backend.manager.services.session.actions.list_files import ListFilesAction
from ai.backend.manager.services.session.actions.match_sessions import MatchSessionsAction
from ai.backend.manager.services.session.actions.rename_session import RenameSessionAction
from ai.backend.manager.services.session.actions.restart_session import RestartSessionAction
from ai.backend.manager.services.session.actions.shutdown_service import ShutdownServiceAction
from ai.backend.manager.services.session.actions.start_service import StartServiceAction
from ai.backend.manager.services.session.actions.upload_files import UploadFilesAction
from ai.backend.manager.services.vfolder.actions.base import GetTaskLogsAction

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common import validators as tx
from ai.backend.common.defs.session import (
    SESSION_PRIORITY_DEFAULT,
    SESSION_PRIORITY_MAX,
    SESSION_PRIORITY_MIN,
)
from ai.backend.common.events.event_types.agent.anycast import (
    AgentTerminatedEvent,
)
from ai.backend.common.exception import BackendAIError
from ai.backend.common.plugin.monitor import GAUGE
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    KernelId,
    MountPermission,
    MountTypes,
    SessionId,
    SessionTypes,
)
from ai.backend.logging import BraceStyleAdapter

from ..defs import DEFAULT_IMAGE_ARCH, DEFAULT_ROLE
from ..errors.api import InvalidAPIParameters
from ..errors.auth import InsufficientPrivilege
from ..models import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    SessionDependencyRow,
    SessionRow,
    UserRole,
    kernels,
    keypairs,
)
from ..utils import query_userinfo as _query_userinfo
from .auth import auth_required
from .manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware
from .utils import (
    LegacyBaseRequestModel,
    LegacyBaseResponseModel,
    Undefined,
    catch_unexpected,
    check_api_params,
    deprecated_stub,
    get_access_key_scopes,
    pydantic_params_api_handler,
    undefined,
)

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_json_loads = functools.partial(json.loads, parse_float=Decimal)


class UndefChecker(t.Trafaret):
    def check_and_return(self, value: Any) -> object:
        if value == undefined:
            return value
        else:
            self._failure("Invalid Undef format", value=value)
            return None


resource_opts_iv = t.Dict({
    t.Key("shmem", default=None): t.Null | tx.BinarySize,
    t.Key("allow_fractional_resource_fragmentation", default=None): t.Null | t.ToBool,
}).allow_extra("*")

creation_config_v1 = t.Dict({
    t.Key("mounts", default=None): t.Null | t.List(t.String),
    t.Key("environ", default=None): t.Null | t.Mapping(t.String, t.String),
    t.Key("clusterSize", default=None): t.Null | t.Int[1:],
})
creation_config_v2 = t.Dict({
    t.Key("mounts", default=None): t.Null | t.List(t.String),
    t.Key("environ", default=None): t.Null | t.Mapping(t.String, t.String),
    t.Key("clusterSize", default=None): t.Null | t.Int[1:],
    t.Key("instanceMemory", default=None): t.Null | tx.BinarySize,
    t.Key("instanceCores", default=None): t.Null | t.Int,
    t.Key("instanceGPUs", default=None): t.Null | t.Float,
    t.Key("instanceTPUs", default=None): t.Null | t.Int,
})
creation_config_v3 = t.Dict({
    t.Key("mounts", default=None): t.Null | t.List(t.String),
    t.Key("environ", default=None): t.Null | t.Mapping(t.String, t.String),
    tx.AliasedKey(["cluster_size", "clusterSize"], default=None): t.Null | t.Int[1:],
    tx.AliasedKey(["scaling_group", "scalingGroup"], default=None): t.Null | t.String,
    t.Key("resources", default=None): t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(["resource_opts", "resourceOpts"], default=None): t.Null | resource_opts_iv,
})
creation_config_v3_template = t.Dict({
    t.Key("mounts", default=undefined): UndefChecker | t.Null | t.List(t.String),
    t.Key("environ", default=undefined): UndefChecker | t.Null | t.Mapping(t.String, t.String),
    tx.AliasedKey(["cluster_size", "clusterSize"], default=undefined): (
        UndefChecker | t.Null | t.Int[1:]
    ),
    tx.AliasedKey(["scaling_group", "scalingGroup"], default=undefined): (
        UndefChecker | t.Null | t.String
    ),
    t.Key("resources", default=undefined): UndefChecker | t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(["resource_opts", "resourceOpts"], default=undefined): (
        UndefChecker | resource_opts_iv
    ),
})
creation_config_v4 = t.Dict({
    t.Key("mounts", default=None): t.Null | t.List(t.String),
    tx.AliasedKey(["mount_map", "mountMap"], default=None): t.Null | t.Mapping(t.String, t.String),
    t.Key("environ", default=None): t.Null | t.Mapping(t.String, t.String),
    tx.AliasedKey(["cluster_size", "clusterSize"], default=None): t.Null | t.Int[1:],
    tx.AliasedKey(["scaling_group", "scalingGroup"], default=None): t.Null | t.String,
    t.Key("resources", default=None): t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(["resource_opts", "resourceOpts"], default=None): t.Null | resource_opts_iv,
    tx.AliasedKey(["preopen_ports", "preopenPorts"], default=None): t.Null
    | t.List(t.Int[1024:65535]),
})
creation_config_v4_template = t.Dict({
    t.Key("mounts", default=undefined): UndefChecker | t.Null | t.List(t.String),
    tx.AliasedKey(["mount_map", "mountMap"], default=undefined): (
        UndefChecker | t.Null | t.Mapping(t.String, t.String)
    ),
    t.Key("environ", default=undefined): UndefChecker | t.Null | t.Mapping(t.String, t.String),
    tx.AliasedKey(["cluster_size", "clusterSize"], default=undefined): (
        UndefChecker | t.Null | t.Int[1:]
    ),
    tx.AliasedKey(["scaling_group", "scalingGroup"], default=undefined): (
        UndefChecker | t.Null | t.String
    ),
    t.Key("resources", default=undefined): UndefChecker | t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(["resource_opts", "resourceOpts"], default=undefined): (
        UndefChecker | t.Null | resource_opts_iv
    ),
})
creation_config_v5 = t.Dict({
    t.Key("mounts", default=None): t.Null | t.List(t.String),
    tx.AliasedKey(["mount_map", "mountMap"], default=None): t.Null | t.Mapping(t.String, t.String),
    tx.AliasedKey(["mount_options", "mountOptions"], default=None): t.Null
    | t.Mapping(
        t.String,
        t.Dict({
            t.Key("type", default=MountTypes.BIND): tx.Enum(MountTypes),
            tx.AliasedKey(["permission", "perm"], default=None): t.Null | tx.Enum(MountPermission),
        }).ignore_extra("*"),
    ),
    t.Key("environ", default=None): t.Null | t.Mapping(t.String, t.String),
    # cluster_size is moved to the root-level parameters
    tx.AliasedKey(["scaling_group", "scalingGroup"], default=None): t.Null | t.String,
    t.Key("resources", default=None): t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(["resource_opts", "resourceOpts"], default=None): t.Null | resource_opts_iv,
    tx.AliasedKey(["preopen_ports", "preopenPorts"], default=None): t.Null
    | t.List(t.Int[1024:65535]),
    tx.AliasedKey(["agent_list", "agentList"], default=None): t.Null | t.List(t.String),
})
creation_config_v5_template = t.Dict({
    t.Key("mounts", default=undefined): UndefChecker | t.Null | t.List(t.String),
    tx.AliasedKey(["mount_map", "mountMap"], default=undefined): (
        UndefChecker | t.Null | t.Mapping(t.String, t.String)
    ),
    t.Key("environ", default=undefined): UndefChecker | t.Null | t.Mapping(t.String, t.String),
    # cluster_size is moved to the root-level parameters
    tx.AliasedKey(["scaling_group", "scalingGroup"], default=undefined): (
        UndefChecker | t.Null | t.String
    ),
    t.Key("resources", default=undefined): UndefChecker | t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(["resource_opts", "resourceOpts"], default=undefined): (
        UndefChecker | t.Null | resource_opts_iv
    ),
})
creation_config_v6 = t.Dict({
    t.Key("mounts", default=None): t.Null | t.List(t.String),
    tx.AliasedKey(["mount_map", "mountMap"], default=None): t.Null | t.Mapping(t.String, t.String),
    tx.AliasedKey(["mount_options", "mountOptions"], default=None): t.Null
    | t.Mapping(
        t.String,
        t.Dict({
            t.Key("type", default=MountTypes.BIND): tx.Enum(MountTypes),
            tx.AliasedKey(["permission", "perm"], default=None): t.Null | tx.Enum(MountPermission),
        }).ignore_extra("*"),
    ),
    t.Key("environ", default=None): t.Null | t.Mapping(t.String, t.String),
    # cluster_size is moved to the root-level parameters
    tx.AliasedKey(["scaling_group", "scalingGroup"], default=None): t.Null | t.String,
    t.Key("resources", default=None): t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(["resource_opts", "resourceOpts"], default=None): t.Null | resource_opts_iv,
    tx.AliasedKey(["preopen_ports", "preopenPorts"], default=None): t.Null
    | t.List(t.Int[1024:65535]),
    tx.AliasedKey(["agent_list", "agentList"], default=None): t.Null | t.List(t.String),
    tx.AliasedKey(["attach_network", "attachNetwork"], default=None): t.Null | tx.UUID,
})
creation_config_v6_template = t.Dict({
    t.Key("mounts", default=undefined): UndefChecker | t.Null | t.List(t.String),
    tx.AliasedKey(["mount_map", "mountMap"], default=undefined): (
        UndefChecker | t.Null | t.Mapping(t.String, t.String)
    ),
    t.Key("environ", default=undefined): UndefChecker | t.Null | t.Mapping(t.String, t.String),
    # cluster_size is moved to the root-level parameters
    tx.AliasedKey(["scaling_group", "scalingGroup"], default=undefined): (
        UndefChecker | t.Null | t.String
    ),
    t.Key("resources", default=undefined): UndefChecker | t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(["resource_opts", "resourceOpts"], default=undefined): (
        UndefChecker | t.Null | resource_opts_iv
    ),
    tx.AliasedKey(["attach_network", "attachNetwork"], default=undefined): (
        UndefChecker | t.Null | tx.UUID
    ),
})

creation_config_v7 = t.Dict({
    t.Key("mounts", default=None): t.Null | t.List(t.String),  # deprecated
    tx.AliasedKey(["mount_map", "mountMap"], default=None): t.Null
    | t.Mapping(t.String, t.String),  # deprecated
    t.Key("mount_ids", default=None): t.Null | t.List(tx.UUID),
    tx.AliasedKey(["mount_id_map", "mountIdMap"], default=None): t.Null
    | t.Mapping(tx.UUID, t.String),
    tx.AliasedKey(["mount_options", "mountOptions"], default=None): t.Null
    | t.Mapping(
        t.String,
        t.Dict({
            t.Key("type", default=MountTypes.BIND): tx.Enum(MountTypes),
            tx.AliasedKey(["permission", "perm"], default=None): t.Null | tx.Enum(MountPermission),
        }).ignore_extra("*"),
    ),
    t.Key("environ", default=None): t.Null | t.Mapping(t.String, t.String),
    # cluster_size is moved to the root-level parameters
    tx.AliasedKey(["scaling_group", "scalingGroup"], default=None): t.Null | t.String,
    t.Key("resources", default=None): t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(["resource_opts", "resourceOpts"], default=None): t.Null | resource_opts_iv,
    tx.AliasedKey(["preopen_ports", "preopenPorts"], default=None): t.Null
    | t.List(t.Int[1024:65535]),
    tx.AliasedKey(["agent_list", "agentList"], default=None): t.Null | t.List(t.String),
    tx.AliasedKey(["attach_network", "attachNetwork"], default=None): t.Null | tx.UUID,
})

overwritten_param_check = t.Dict({
    t.Key("template_id"): tx.UUID,
    t.Key("session_name"): tx.SessionName,
    t.Key("image", default=None): t.Null | t.String,
    tx.AliasedKey(["session_type", "sess_type"]): tx.Enum(SessionTypes),
    t.Key("group", default=None): t.Null | t.String,
    t.Key("domain", default=None): t.Null | t.String,
    t.Key("config", default=None): t.Null | t.Mapping(t.String, t.Any),
    t.Key("tag", default=None): t.Null | t.String,
    t.Key("enqueue_only", default=False): t.ToBool,
    t.Key("max_wait_seconds", default=0): t.Int[0:],
    t.Key("reuse", default=True): t.ToBool,
    t.Key("startup_command", default=None): t.Null | t.String,
    t.Key("bootstrap_script", default=None): t.Null | t.String,
    t.Key("owner_access_key", default=None): t.Null | t.String,
    tx.AliasedKey(["scaling_group", "scalingGroup"], default=None): t.Null | t.String,
    tx.AliasedKey(["cluster_size", "clusterSize"], default=None): t.Null | t.Int[1:],
    tx.AliasedKey(["cluster_mode", "clusterMode"], default="SINGLE_NODE"): tx.Enum(ClusterMode),
    tx.AliasedKey(["starts_at", "startsAt"], default=None): t.Null | t.String,
    tx.AliasedKey(["batch_timeout", "batchTimeout"], default=None): t.Null | tx.TimeDuration,
}).allow_extra("*")


def sub(d, old, new):
    for k, v in d.items():
        if isinstance(v, Mapping) or isinstance(v, dict):
            d[k] = sub(v, old, new)
        elif d[k] == old:
            d[k] = new
    return d


def drop_undefined(d):
    newd = {}
    for k, v in d.items():
        if isinstance(v, Mapping) or isinstance(v, dict):
            newval = drop_undefined(v)
            if len(newval.keys()) > 0:  # exclude empty dict always
                newd[k] = newval
        elif not isinstance(v, Undefined):
            newd[k] = v
    return newd


async def query_userinfo(
    request: web.Request,
    params: Any,
    conn: SAConnection,
) -> tuple[UUID, UUID, dict]:
    try:
        return await _query_userinfo(
            conn,
            request["user"]["uuid"],
            request["keypair"]["access_key"],
            request["user"]["role"],
            request["user"]["domain_name"],
            request["keypair"]["resource_policy"],
            params["domain"] or request["user"]["domain_name"],
            params["group"],
            query_on_behalf_of=(
                None if params["owner_access_key"] is undefined else params["owner_access_key"]
            ),
        )
    except ValueError as e:
        raise InvalidAPIParameters(str(e))


@server_status_required(ALL_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["template_id", "templateId"]): t.Null | tx.UUID,
        tx.AliasedKey(["name", "session_name", "clientSessionToken"], default=undefined)
        >> "session_name": UndefChecker | tx.SessionName,
        t.Key("priority", default=SESSION_PRIORITY_DEFAULT): t.ToInt(
            gte=SESSION_PRIORITY_MIN, lte=SESSION_PRIORITY_MAX
        ),
        tx.AliasedKey(["image", "lang"], default=undefined): UndefChecker | t.Null | t.String,
        tx.AliasedKey(["arch", "architecture"], default=undefined) >> "architecture": t.String
        | UndefChecker,
        tx.AliasedKey(["type", "sessionType"], default=undefined) >> "session_type": tx.Enum(
            SessionTypes
        )
        | UndefChecker,
        tx.AliasedKey(["group", "groupName", "group_name"], default=undefined): (
            UndefChecker | t.Null | t.String
        ),
        tx.AliasedKey(["domain", "domainName", "domain_name"], default=undefined): (
            UndefChecker | t.Null | t.String
        ),
        tx.AliasedKey(["cluster_size", "clusterSize"], default=1): t.ToInt[1:],  # new in APIv6
        tx.AliasedKey(["cluster_mode", "clusterMode"], default="SINGLE_NODE"): tx.Enum(
            ClusterMode
        ),  # new in APIv6
        t.Key("config", default=dict): t.Mapping(t.String, t.Any),
        t.Key("tag", default=undefined): UndefChecker | t.Null | t.String,
        t.Key("enqueueOnly", default=False) >> "enqueue_only": t.ToBool,
        t.Key("maxWaitSeconds", default=0) >> "max_wait_seconds": t.Int[0:],
        tx.AliasedKey(["starts_at", "startsAt"], default=None): t.Null | t.String,
        tx.AliasedKey(["batch_timeout", "batchTimeout"], default=None): t.Null | tx.TimeDuration,
        t.Key("reuseIfExists", default=True) >> "reuse": t.ToBool,
        t.Key("startupCommand", default=None) >> "startup_command": UndefChecker
        | t.Null
        | t.String,
        tx.AliasedKey(["bootstrap_script", "bootstrapScript"], default=undefined): (
            UndefChecker | t.Null | t.String
        ),
        t.Key("dependencies", default=None): (
            UndefChecker | t.Null | t.List(tx.UUID) | t.List(t.String)
        ),
        tx.AliasedKey(["callback_url", "callbackUrl", "callbackURL"], default=None): (
            UndefChecker | t.Null | tx.URL
        ),
        t.Key("owner_access_key", default=undefined): UndefChecker | t.Null | t.String,
    }),
    loads=_json_loads,
)
async def create_from_template(request: web.Request, params: dict[str, Any]) -> web.Response:
    # TODO: we need to refactor session_template model to load the template configs
    #       by one batch. Currently, we need to set every template configs one by one.
    root_ctx: RootContext = request.app["_root.context"]

    if params["image"] is None and params["template_id"] is None:
        raise InvalidAPIParameters("Both image and template_id can't be None!")

    api_version = request["api_version"]
    try:
        if 8 <= api_version[0]:
            params["config"] = creation_config_v6_template.check(params["config"])
        elif 6 <= api_version[0]:
            params["config"] = creation_config_v5_template.check(params["config"])
        elif 5 <= api_version[0]:
            params["config"] = creation_config_v4_template.check(params["config"])
        elif (4, "20190315") <= api_version:
            params["config"] = creation_config_v3_template.check(params["config"])
    except t.DataError as e:
        log.debug("Validation error: {0}", e.as_dict())
        raise InvalidAPIParameters("Input validation error", extra_data=e.as_dict())

    scopes_param = {
        "owner_access_key": (
            None if params["owner_access_key"] is undefined else params["owner_access_key"]
        ),
    }

    requester_access_key, owner_access_key = await get_access_key_scopes(request, scopes_param)
    log.info(
        "GET_OR_CREATE (ak:{0}/{1}, img:{2}, s:{3})",
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else "*",
        params["image"],
        params["session_name"],
    )

    if params["domain"] is None:
        domain_name = request["user"]["domain_name"]
    else:
        domain_name = params["domain"]

    result = await root_ctx.processors.session.create_from_template.wait_for_complete(
        CreateFromTemplateAction(
            params=CreateFromTemplateActionParams(
                template_id=params["template_id"],
                session_name=params["session_name"],
                image=params["image"],
                architecture=params["architecture"],
                session_type=params["session_type"],
                group_name=params["group"],
                domain_name=domain_name,
                cluster_size=params["cluster_size"],
                cluster_mode=params["cluster_mode"],
                config=params["config"],
                tag=params["tag"],
                enqueue_only=params["enqueue_only"],
                max_wait_seconds=params["max_wait_seconds"],
                reuse_if_exists=params["reuse"],
                startup_command=params["startup_command"],
                bootstrap_script=params["bootstrap_script"],
                dependencies=params["dependencies"],
                callback_url=params["callback_url"],
                priority=params["priority"],
                starts_at=params["starts_at"],
                batch_timeout=params["batch_timeout"],
                owner_access_key=owner_access_key,
            ),
            user_id=request["user"]["uuid"],
            user_role=request["user"]["role"],
            requester_access_key=requester_access_key,
            sudo_session_enabled=request["user"]["sudo_session_enabled"],
            keypair_resource_policy=request["keypair"]["resource_policy"],
        )
    )

    return web.json_response(result.result, status=HTTPStatus.CREATED)


@server_status_required(ALL_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["name", "session_name", "clientSessionToken"])
        >> "session_name": tx.SessionName,
        t.Key("priority", default=SESSION_PRIORITY_DEFAULT): t.ToInt(
            gte=SESSION_PRIORITY_MIN, lte=SESSION_PRIORITY_MAX
        ),
        tx.AliasedKey(["image", "lang"]): t.String,
        tx.AliasedKey(["arch", "architecture"], default=DEFAULT_IMAGE_ARCH)
        >> "architecture": t.String,
        tx.AliasedKey(["type", "sessionType"], default="interactive") >> "session_type": tx.Enum(
            SessionTypes
        ),
        tx.AliasedKey(["group", "groupName", "group_name"], default="default"): t.String,
        tx.AliasedKey(["domain", "domainName", "domain_name"], default="default"): t.String,
        tx.AliasedKey(["cluster_size", "clusterSize"], default=1): t.ToInt[1:],  # new in APIv6
        tx.AliasedKey(["cluster_mode", "clusterMode"], default="SINGLE_NODE"): tx.Enum(
            ClusterMode
        ),  # new in APIv6
        t.Key("config", default=dict): t.Mapping(t.String, t.Any),
        t.Key("tag", default=None): t.Null | t.String,
        t.Key("enqueueOnly", default=False) >> "enqueue_only": t.ToBool,
        t.Key("maxWaitSeconds", default=0) >> "max_wait_seconds": t.ToInt[0:],
        tx.AliasedKey(["starts_at", "startsAt"], default=None): t.Null | t.String,
        tx.AliasedKey(["batch_timeout", "batchTimeout"], default=None): t.Null | tx.TimeDuration,
        t.Key("reuseIfExists", default=True) >> "reuse": t.ToBool,
        t.Key("startupCommand", default=None) >> "startup_command": t.Null | t.String,
        tx.AliasedKey(["bootstrap_script", "bootstrapScript"], default=None): t.Null | t.String,
        t.Key("dependencies", default=None): t.Null | t.List(tx.UUID) | t.List(t.String),
        tx.AliasedKey(["callback_url", "callbackUrl", "callbackURL"], default=None): (
            t.Null | tx.URL
        ),
        t.Key("owner_access_key", default=None): t.Null | t.String,
    }),
    loads=_json_loads,
)
async def create_from_params(request: web.Request, params: dict[str, Any]) -> web.Response:
    if params["session_name"] in ["from-template"]:
        raise InvalidAPIParameters(
            f"Requested session ID {params['session_name']} is reserved word"
        )
    api_version = request["api_version"]
    if 9 <= api_version[0]:
        creation_config = creation_config_v7.check(params["config"])
    elif 8 <= api_version[0]:
        creation_config = creation_config_v6.check(params["config"])
    elif 6 <= api_version[0]:
        creation_config = creation_config_v5.check(params["config"])
    elif 5 <= api_version[0]:
        creation_config = creation_config_v4.check(params["config"])
    elif (4, "20190315") <= api_version:
        creation_config = creation_config_v3.check(params["config"])
    elif 2 <= api_version[0] <= 4:
        creation_config = creation_config_v2.check(params["config"])
    elif api_version[0] == 1:
        creation_config = creation_config_v1.check(params["config"])
    else:
        raise InvalidAPIParameters("API version not supported")
    params["config"] = creation_config

    root_ctx: RootContext = request.app["_root.context"]

    agent_list = cast(Optional[list[str]], params["config"]["agent_list"])
    if agent_list is not None:
        if (
            request["user"]["role"] != UserRole.SUPERADMIN
            and root_ctx.config_provider.config.manager.hide_agents
        ):
            raise InsufficientPrivilege(
                "You are not allowed to manually assign agents for your session."
            )
        agent_count = len(agent_list)
        if params["cluster_mode"] == ClusterMode.MULTI_NODE:
            if agent_count != params["cluster_size"]:
                raise InvalidAPIParameters(
                    "For multi-node cluster sessions, the number of manually assigned"
                    " agents must be same to the cluster size. Note that you may specify"
                    " duplicate agents in the list.",
                )

    if params["domain"] is None:
        domain_name = request["user"]["domain_name"]
    else:
        domain_name = params["domain"]
    scopes_param = {
        "owner_access_key": (
            None if params["owner_access_key"] is undefined else params["owner_access_key"]
        ),
    }
    requester_access_key, owner_access_key = await get_access_key_scopes(request, scopes_param)
    log.info(
        "GET_OR_CREATE (ak:{0}/{1}, img:{2}, s:{3})",
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else "*",
        params["image"],
        params["session_name"],
    )

    result = await root_ctx.processors.session.create_from_params.wait_for_complete(
        CreateFromParamsAction(
            params=CreateFromParamsActionParams(
                session_name=params["session_name"],
                image=params["image"],
                architecture=params["architecture"],
                session_type=params["session_type"],
                group_name=params["group"],
                domain_name=domain_name,
                cluster_size=params["cluster_size"],
                cluster_mode=params["cluster_mode"],
                config=params["config"],
                tag=params["tag"],
                enqueue_only=params["enqueue_only"],
                max_wait_seconds=params["max_wait_seconds"],
                reuse_if_exists=params["reuse"],
                startup_command=params["startup_command"],
                bootstrap_script=params["bootstrap_script"],
                dependencies=params["dependencies"],
                callback_url=params["callback_url"],
                priority=params["priority"],
                starts_at=params["starts_at"],
                batch_timeout=params["batch_timeout"],
                owner_access_key=owner_access_key,
            ),
            user_id=request["user"]["uuid"],
            user_role=request["user"]["role"],
            requester_access_key=requester_access_key,
            sudo_session_enabled=request["user"]["sudo_session_enabled"],
            keypair_resource_policy=request["keypair"]["resource_policy"],
        )
    )

    return web.json_response(result.result, status=HTTPStatus.CREATED)


@server_status_required(ALL_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key("clientSessionToken") >> "session_name": tx.SessionName,
        tx.AliasedKey(["template_id", "templateId"]): t.Null | tx.UUID,
        tx.AliasedKey(["type", "sessionType"], default="interactive") >> "sess_type": tx.Enum(
            SessionTypes
        ),
        tx.AliasedKey(["group", "groupName", "group_name"], default="default"): t.String,
        tx.AliasedKey(["domain", "domainName", "domain_name"], default="default"): t.String,
        tx.AliasedKey(["scaling_group", "scalingGroup"], default=None): t.Null | t.String,
        t.Key("tag", default=None): t.Null | t.String,
        t.Key("enqueueOnly", default=False) >> "enqueue_only": t.ToBool,
        t.Key("maxWaitSeconds", default=0) >> "max_wait_seconds": t.Int[0:],
        t.Key("owner_access_key", default=None): t.Null | t.String,
    }),
    loads=_json_loads,
)
async def create_cluster(request: web.Request, params: dict[str, Any]) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    if params["domain"] is None:
        domain_name = request["user"]["domain_name"]
    else:
        domain_name = params["domain"]
    scopes_param = {
        "owner_access_key": (
            None if params["owner_access_key"] is undefined else params["owner_access_key"]
        ),
    }
    requester_access_key, owner_access_key = await get_access_key_scopes(request, scopes_param)
    log.info(
        "CREAT_CLUSTER (ak:{0}/{1}, s:{2})",
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else "*",
        params["session_name"],
    )

    result = await root_ctx.processors.session.create_cluster.wait_for_complete(
        CreateClusterAction(
            session_name=params["session_name"],
            user_id=request["user"]["uuid"],
            user_role=request["user"]["role"],
            domain_name=domain_name,
            group_name=params["group"],
            requester_access_key=requester_access_key,
            owner_access_key=owner_access_key,
            scaling_group_name=params["scaling_group"],
            tag=params["tag"],
            session_type=params["sess_type"],
            enqueue_only=params["enqueue_only"],
            template_id=params["template_id"],
            sudo_session_enabled=request["user"]["sudo_session_enabled"],
            max_wait_seconds=params["max_wait_seconds"],
            keypair_resource_policy=request["keypair"]["resource_policy"],
        )
    )

    return web.json_response(result.result, status=HTTPStatus.CREATED)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key("login_session_token", default=None): t.Null | t.String,
        tx.AliasedKey(["app", "service"]): t.String,
        # The port argument is only required to use secondary ports
        # when the target app listens multiple TCP ports.
        # Otherwise it should be omitted or set to the same value of
        # the actual port number used by the app.
        tx.AliasedKey(["port"], default=None): t.Null | t.Int[1024:65535],
        tx.AliasedKey(["envs"], default=None): t.Null | t.String,  # stringified JSON
        # e.g., '{"PASSWORD": "12345"}'
        tx.AliasedKey(["arguments"], default=None): t.Null | t.String,  # stringified JSON
        # e.g., '{"-P": "12345"}'
        # The value can be one of:
        # None, str, List[str]
    })
)
async def start_service(request: web.Request, params: Mapping[str, Any]) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name: str = request.match_info["session_name"]
    access_key: AccessKey = request["keypair"]["access_key"]
    service: str = params["app"]
    myself = asyncio.current_task()
    assert myself is not None
    result = await root_ctx.processors.session.start_service.wait_for_complete(
        StartServiceAction(
            session_name=session_name,
            access_key=access_key,
            service=service,
            login_session_token=params.get("login_session_token"),
            port=params.get("port"),
            envs=params.get("envs"),
            arguments=params.get("arguments"),
        )
    )

    return web.json_response({
        "token": result.token,
        "wsproxy_addr": result.wsproxy_addr,
    })


@server_status_required(ALL_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key("login_session_token", default=None): t.Null | t.String,
    }),
    loads=_json_loads,
)
async def get_commit_status(request: web.Request, params: Mapping[str, Any]) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name: str = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)

    myself = asyncio.current_task()
    assert myself is not None

    log.info(
        "GET_COMMIT_STATUS (ak:{}/{}, s:{})", requester_access_key, owner_access_key, session_name
    )
    result = await root_ctx.processors.session.get_commit_status.wait_for_complete(
        GetCommitStatusAction(
            session_name=session_name,
            owner_access_key=owner_access_key,
        )
    )
    resp = result.commit_info.asdict()
    return web.json_response(resp, status=HTTPStatus.OK)


@server_status_required(ALL_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key("login_session_token", default=None): t.Null | t.String,
    }),
    loads=_json_loads,
)
async def get_abusing_report(request: web.Request, params: Mapping[str, Any]) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name: str = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)

    log.info(
        "GET_ABUSING_REPORT (ak:{}/{}, s:{})", requester_access_key, owner_access_key, session_name
    )
    result = await root_ctx.processors.session.get_abusing_report.wait_for_complete(
        GetAbusingReportAction(
            session_name=session_name,
            owner_access_key=owner_access_key,
        )
    )
    return web.json_response(result.abuse_report or {}, status=HTTPStatus.OK)


@server_status_required(ALL_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key("agent"): t.String,
    }),
)
async def sync_agent_registry(request: web.Request, params: Any) -> web.StreamResponse:
    root_ctx: RootContext = request.app["_root.context"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)

    agent_id = AgentId(params["agent"])
    log.info(
        "SYNC_AGENT_REGISTRY (ak:{}/{}, a:{})", requester_access_key, owner_access_key, agent_id
    )
    await root_ctx.processors.agent.sync_agent_registry.wait_for_complete(
        SyncAgentRegistryAction(
            agent_id=agent_id,
        )
    )
    return web.json_response({}, status=HTTPStatus.OK)


class TransitSessionStatusRequestModel(LegacyBaseRequestModel):
    ids: list[UUID] = Field(
        validation_alias=AliasChoices("session_ids", "sessionIds", "SessionIds"),
        description="ID array of sessions to check and transit status.",
    )


class SessionStatusResponseModel(LegacyBaseResponseModel):
    session_status_map: dict[SessionId, str]


@auth_required
@server_status_required(ALL_ALLOWED)
@pydantic_params_api_handler(TransitSessionStatusRequestModel)
async def check_and_transit_status(
    request: web.Request, params: TransitSessionStatusRequestModel
) -> SessionStatusResponseModel:
    root_ctx: RootContext = request.app["_root.context"]
    session_ids = [SessionId(id) for id in params.ids]
    user_role = cast(UserRole, request["user"]["role"])
    user_id = cast(UUID, request["user"]["uuid"])
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info("TRANSIT_STATUS (ak:{}/{}, s:{})", requester_access_key, owner_access_key, session_ids)

    session_status_map = {}
    for session_id in session_ids:
        result = await root_ctx.processors.session.check_and_transit_status.wait_for_complete(
            CheckAndTransitStatusAction(
                user_id=user_id,
                user_role=user_role,
                session_id=session_id,
            )
        )
        session_status_map.update(result.result)
    return SessionStatusResponseModel(session_status_map=session_status_map)


@server_status_required(ALL_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key("login_session_token", default=None): t.Null | t.String,
        # if `dst` is None, it will be agent's default destination.
        tx.AliasedKey(["filename", "fname"], default=None): t.Null | t.String,
    }),
    loads=_json_loads,
)
async def commit_session(request: web.Request, params: Mapping[str, Any]) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name: str = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    filename: Optional[str] = params["filename"]

    log.info(
        "COMMIT_SESSION (ak:{}/{}, s:{})", requester_access_key, owner_access_key, session_name
    )

    action_result = await root_ctx.processors.session.commit_session.wait_for_complete(
        CommitSessionAction(
            session_name=session_name,
            owner_access_key=owner_access_key,
            filename=filename,
        )
    )

    return web.json_response(action_result.commit_result, status=HTTPStatus.CREATED)


class ConvertSessionToImageRequesteModel(LegacyBaseRequestModel):
    image_name: str = Field(
        pattern=r"[a-zA-Z0-9\.\-_]+",
        description="Name of the image to be created.",
    )
    login_session_token: Annotated[Optional[str], Field(default=None)]
    image_visibility: CustomizedImageVisibilityScope = Field(
        default=CustomizedImageVisibilityScope.USER,
        description="Visibility scope of newly created image. currently only supports `USER` scope. Setting this to value other than `USER` will raise error.",
    )


class ConvertSessionToImageResponseModel(LegacyBaseResponseModel):
    task_id: str


@auth_required
@server_status_required(ALL_ALLOWED)
@pydantic_params_api_handler(ConvertSessionToImageRequesteModel)
async def convert_session_to_image(
    request: web.Request, params: ConvertSessionToImageRequesteModel
) -> ConvertSessionToImageResponseModel:
    root_ctx: RootContext = request.app["_root.context"]
    session_name: str = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)

    log.info(
        "CONVERT_SESSION_TO_IMAGE (ak:{}/{}, s:{})",
        requester_access_key,
        owner_access_key,
        session_name,
    )

    result = await root_ctx.processors.session.convert_session_to_image.wait_for_complete(
        ConvertSessionToImageAction(
            session_name=session_name,
            owner_access_key=owner_access_key,
            image_name=params.image_name,
            image_visibility=params.image_visibility,
            image_owner_id=request["user"]["uuid"],
            user_email=request["user"]["email"],
            max_customized_image_count=request["user"]["resource_policy"][
                "max_customized_image_count"
            ],
        )
    )
    return ConvertSessionToImageResponseModel(task_id=str(result.task_id))


@catch_unexpected(log)
async def check_agent_lost(root_ctx: RootContext, interval: float) -> None:
    try:
        now = datetime.now(tzutc())
        timeout = timedelta(seconds=root_ctx.config_provider.config.manager.heartbeat_timeout)

        agent_last_seen = await root_ctx.valkey_live.scan_agent_last_seen()
        for agent_id, prev_timestamp in agent_last_seen:
            prev = datetime.fromtimestamp(prev_timestamp, tzutc())
            if now - prev > timeout:
                await root_ctx.event_producer.anycast_event(
                    AgentTerminatedEvent("agent-lost"),
                    source_override=AgentId(agent_id),
                )
    except asyncio.CancelledError:
        pass


@catch_unexpected(log)
async def report_stats(root_ctx: RootContext, interval: float) -> None:
    try:
        stats_monitor = root_ctx.stats_monitor
        await stats_monitor.report_metric(
            GAUGE, "ai.backend.manager.coroutines", len(asyncio.all_tasks())
        )

        all_inst_ids = [inst_id async for inst_id in root_ctx.registry.enumerate_instances()]
        await stats_monitor.report_metric(
            GAUGE, "ai.backend.manager.agent_instances", len(all_inst_ids)
        )

        async with root_ctx.db.begin_readonly() as conn:
            query = (
                sa.select([sa.func.count()])
                .select_from(kernels)
                .where(
                    (kernels.c.cluster_role == DEFAULT_ROLE)
                    & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
                )
            )
            n = await conn.scalar(query)
            await stats_monitor.report_metric(GAUGE, "ai.backend.manager.active_kernels", n)
            subquery = (
                sa.select([sa.func.count()])
                .select_from(keypairs)
                .where(keypairs.c.is_active == true())
                .group_by(keypairs.c.user_id)
            )
            query = sa.select([sa.func.count()]).select_from(subquery.alias())
            n = await conn.scalar(query)
            await stats_monitor.report_metric(GAUGE, "ai.backend.users.has_active_key", n)

            subquery = subquery.where(keypairs.c.last_used != null())
            query = sa.select([sa.func.count()]).select_from(subquery.alias())
            n = await conn.scalar(query)
            await stats_monitor.report_metric(GAUGE, "ai.backend.users.has_used_key", n)

            """
            query = sa.select([sa.func.count()]).select_from(usage)
            n = await conn.scalar(query)
            await stats_monitor.report_metric(
                GAUGE, 'ai.backend.manager.accum_kernels', n)
            """
    except (sqlalchemy.exc.InterfaceError, ConnectionRefusedError):
        log.warning("report_stats(): error while connecting to PostgreSQL server")


@server_status_required(ALL_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["name", "session_name", "clientSessionToken"])
        >> "session_name": tx.SessionName,
    }),
)
async def rename_session(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    new_name = params["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info(
        "RENAME_SESSION (ak:{0}/{1}, s:{2}, newname:{3})",
        request,
        owner_access_key,
        session_name,
        new_name,
    )

    await root_ctx.processors.session.rename_session.wait_for_complete(
        RenameSessionAction(
            session_name=session_name,
            new_name=new_name,
            owner_access_key=owner_access_key,
        )
    )

    return web.Response(status=HTTPStatus.NO_CONTENT)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key("forced", default="false"): t.ToBool(),
        t.Key("recursive", default="false"): t.ToBool(),
        t.Key("owner_access_key", default=None): t.Null | t.String,
    })
)
async def destroy(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    user_role = cast(UserRole, request["user"]["role"])
    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    if requester_access_key != owner_access_key and user_role not in (
        UserRole.ADMIN,
        UserRole.SUPERADMIN,
    ):
        raise InsufficientPrivilege("You are not allowed to force-terminate others's sessions")

    log.info(
        "DESTROY (ak:{0}/{1}, s:{2}, forced:{3}, recursive: {4})",
        requester_access_key,
        owner_access_key,
        session_name,
        params["forced"],
        params["recursive"],
    )

    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)

    result = await root_ctx.processors.session.destroy_session.wait_for_complete(
        DestroySessionAction(
            session_name=session_name,
            owner_access_key=owner_access_key,
            user_role=user_role,
            forced=params["forced"],
            recursive=params["recursive"],
        )
    )
    return web.json_response(result.result, status=HTTPStatus.OK)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key("id"): t.String(),
    })
)
async def match_sessions(request: web.Request, params: Any) -> web.Response:
    """
    A quick session-ID matcher API for use with auto-completion in CLI.
    """
    root_ctx: RootContext = request.app["_root.context"]
    id_or_name_prefix = params["id"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info(
        "MATCH_SESSIONS(ak:{0}/{1}, prefix:{2})",
        requester_access_key,
        owner_access_key,
        id_or_name_prefix,
    )
    result = await root_ctx.processors.session.match_sessions.wait_for_complete(
        MatchSessionsAction(
            id_or_name_prefix=id_or_name_prefix,
            owner_access_key=owner_access_key,
        )
    )

    return web.json_response(
        {
            "matches": result.result,
        },
        status=HTTPStatus.OK,
    )


@server_status_required(READ_ALLOWED)
@auth_required
async def get_direct_access_info(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    _, owner_access_key = await get_access_key_scopes(request)

    result = await root_ctx.processors.session.get_direct_access_info.wait_for_complete(
        GetDirectAccessInfoAction(
            session_name=session_name,
            owner_access_key=owner_access_key,
        )
    )
    return web.json_response(result.result)


@server_status_required(READ_ALLOWED)
@auth_required
async def get_info(request: web.Request) -> web.Response:
    # NOTE: This API should be replaced with GraphQL version.
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info("GET_INFO (ak:{0}/{1}, s:{2})", requester_access_key, owner_access_key, session_name)
    try:
        result = await root_ctx.processors.session.get_session_info.wait_for_complete(
            GetSessionInfoAction(
                session_name=session_name,
                owner_access_key=owner_access_key,
            )
        )
    except BackendAIError:
        log.exception("GET_INFO: exception")
        raise
    return web.json_response(result.session_info.asdict(), status=HTTPStatus.OK)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key("owner_access_key", default=None): t.Null | t.String,
    })
)
async def restart(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    log.info("RESTART (ak:{0}/{1}, s:{2})", requester_access_key, owner_access_key, session_name)

    try:
        await root_ctx.processors.session.restart_session.wait_for_complete(
            RestartSessionAction(
                session_name=session_name,
                owner_access_key=owner_access_key,
            )
        )
    except BackendAIError:
        log.exception("RESTART: exception")
        raise
    except Exception:
        await root_ctx.error_monitor.capture_exception(context={"user": request["user"]["uuid"]})
        log.exception("RESTART: unexpected error")
        raise web.HTTPInternalServerError
    return web.Response(status=HTTPStatus.NO_CONTENT)


@server_status_required(READ_ALLOWED)
@auth_required
async def execute(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    try:
        params = await read_json(request)
        log.info("EXECUTE(ak:{0}/{1}, s:{2})", requester_access_key, owner_access_key, session_name)
    except json.decoder.JSONDecodeError:
        log.warning("EXECUTE: invalid/missing parameters")
        raise InvalidAPIParameters

    result = await root_ctx.processors.session.execute_session.wait_for_complete(
        ExecuteSessionAction(
            session_name=session_name,
            owner_access_key=owner_access_key,
            api_version=request["api_version"],
            params=ExecuteSessionActionParams(
                mode=params.get("mode", None),
                run_id=params.get("run_id", None),
                code=params.get("code", None),
                options=params.get("options", None),
            ),
        )
    )
    return web.json_response(result.result, status=HTTPStatus.OK)


@server_status_required(READ_ALLOWED)
@auth_required
async def interrupt(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info("INTERRUPT(ak:{0}/{1}, s:{2})", requester_access_key, owner_access_key, session_name)

    try:
        await root_ctx.processors.session.interrupt.wait_for_complete(
            InterruptSessionAction(
                session_name=session_name,
                owner_access_key=owner_access_key,
            )
        )
    except BackendAIError:
        log.exception("INTERRUPT: exception")
        raise
    return web.Response(status=HTTPStatus.NO_CONTENT)


@server_status_required(READ_ALLOWED)
@auth_required
async def complete(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)

    try:
        params = await read_json(request)
        code = params.get("code", "")
        opts = params.get("options", None) or {}
    except json.decoder.JSONDecodeError:
        raise InvalidAPIParameters

    log.info("COMPLETE(ak:{0}/{1}, s:{2})", requester_access_key, owner_access_key, session_name)

    action_result = await root_ctx.processors.session.complete.wait_for_complete(
        CompleteAction(
            session_name=session_name,
            owner_access_key=owner_access_key,
            code=code,
            options=opts,
        )
    )

    return web.json_response(action_result.result.as_dict(), status=HTTPStatus.OK)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key("service_name"): t.String,
    })
)
async def shutdown_service(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info(
        "SHUTDOWN_SERVICE (ak:{0}/{1}, s:{2})", requester_access_key, owner_access_key, session_name
    )
    service_name = params.get("service_name")

    try:
        await root_ctx.processors.session.shutdown_service.wait_for_complete(
            ShutdownServiceAction(
                session_name=session_name,
                owner_access_key=owner_access_key,
                service_name=service_name,
            )
        )
    except BackendAIError:
        log.exception("SHUTDOWN_SERVICE: exception")
        raise
    return web.Response(status=HTTPStatus.NO_CONTENT)


async def find_dependent_sessions(
    root_session_name_or_id: str | UUID,
    db_session: SASession,
    access_key: AccessKey,
    *,
    allow_stale: bool = False,
) -> set[UUID]:
    async def _find_dependent_sessions(session_id: UUID) -> set[UUID]:
        result = await db_session.execute(
            sa.select(SessionDependencyRow).where(SessionDependencyRow.depends_on == session_id)
        )
        dependent_sessions: set[UUID] = {x.session_id for x in result.scalars()}

        recursive_dependent_sessions: list[set[UUID]] = [
            await _find_dependent_sessions(dependent_session)
            for dependent_session in dependent_sessions
        ]

        for recursive_dependent_session in recursive_dependent_sessions:
            dependent_sessions |= recursive_dependent_session

        return dependent_sessions

    root_session = await SessionRow.get_session(
        db_session,
        root_session_name_or_id,
        access_key=access_key,
        allow_stale=allow_stale,
    )
    return await _find_dependent_sessions(cast(UUID, root_session.id))


@aiotools.lru_cache(maxsize=100)
async def _find_dependency_sessions(
    session_name_or_id: UUID | str,
    db_session: SASession,
    access_key: AccessKey,
):
    sessions = await SessionRow.match_sessions(
        db_session,
        session_name_or_id,
        access_key=access_key,
    )

    assert len(sessions) >= 1, "session not found!"

    session_id = str(sessions[0].id)
    session_name = sessions[0].name

    assert isinstance(session_id, get_args(UUID | str))
    assert isinstance(session_name, str)

    kernel_query = (
        sa.select([
            kernels.c.status,
            kernels.c.status_changed,
        ])
        .select_from(kernels)
        .where(kernels.c.session_id == session_id)
    )

    dependency_session_ids: list[SessionDependencyRow] = (
        await db_session.execute(
            sa.select(SessionDependencyRow.depends_on).where(
                SessionDependencyRow.session_id == session_id
            )
        )
    ).first()

    if not dependency_session_ids:
        dependency_session_ids = []

    kernel_query_result = (await db_session.execute(kernel_query)).first()

    session_info: dict[str, list | str] = {
        "session_id": session_id,
        "session_name": session_name,
        "status": str(kernel_query_result[0]),
        "status_changed": str(kernel_query_result[1]),
        "depends_on": [
            await _find_dependency_sessions(dependency_session_id, db_session, access_key)
            for dependency_session_id in dependency_session_ids
        ],
    }

    return session_info


async def find_dependency_sessions(
    session_name_or_id: UUID | str,
    db_session: SASession,
    access_key: AccessKey,
):
    return await _find_dependency_sessions(session_name_or_id, db_session, access_key)


@server_status_required(READ_ALLOWED)
@auth_required
async def get_dependency_graph(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    root_session_name = request.match_info["session_name"]

    requester_access_key, owner_access_key = await get_access_key_scopes(request)

    log.info(
        "GET_DEPENDENCY_GRAPH (ak:{0}/{1}, s:{2})",
        requester_access_key,
        owner_access_key,
        root_session_name,
    )

    result = await root_ctx.processors.session.get_dependency_graph.wait_for_complete(
        GetDependencyGraphAction(
            root_session_name=root_session_name,
            owner_access_key=owner_access_key,
        )
    )

    return web.json_response(
        result.result,
        status=HTTPStatus.OK,
    )


@server_status_required(READ_ALLOWED)
@auth_required
async def upload_files(request: web.Request) -> web.Response:
    reader = await request.multipart()
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info(
        "UPLOAD_FILE (ak:{0}/{1}, s:{2})", requester_access_key, owner_access_key, session_name
    )

    try:
        await root_ctx.processors.session.upload_files.wait_for_complete(
            UploadFilesAction(
                session_name=session_name,
                owner_access_key=owner_access_key,
                reader=reader,
            )
        )
    except BackendAIError:
        log.exception("UPLOAD_FILES: exception")
        raise
    return web.Response(status=HTTPStatus.NO_CONTENT)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        tx.MultiKey("files"): t.List(t.String),
    })
)
async def download_files(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    files = params.get("files")
    log.info(
        "DOWNLOAD_FILE (ak:{0}/{1}, s:{2}, path:{3!r})",
        requester_access_key,
        owner_access_key,
        session_name,
        files[0],
    )
    result = await root_ctx.processors.session.download_files.wait_for_complete(
        DownloadFilesAction(
            user_id=request["user"]["uuid"],
            owner_access_key=owner_access_key,
            session_name=session_name,
            files=files,
        )
    )
    return web.Response(body=result.result, status=HTTPStatus.OK)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key("file"): t.String,
    })
)
async def download_single(request: web.Request, params: Any) -> web.Response:
    """
    Download a single file from the scratch root. Only for small files.
    """
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    file = params["file"]
    log.info(
        "DOWNLOAD_SINGLE (ak:{0}/{1}, s:{2}, path:{3!r})",
        requester_access_key,
        owner_access_key,
        session_name,
        file,
    )

    result = await root_ctx.processors.session.download_file.wait_for_complete(
        DownloadFileAction(
            user_id=request["user"]["uuid"],
            session_name=session_name,
            owner_access_key=owner_access_key,
            file=file,
        )
    )
    return web.Response(body=result.bytes, status=HTTPStatus.OK)


@server_status_required(READ_ALLOWED)
@auth_required
async def list_files(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    try:
        session_name = request.match_info["session_name"]
        requester_access_key, owner_access_key = await get_access_key_scopes(request)
        params = await read_json(request)
        path = params.get("path", ".")
        log.info(
            "LIST_FILES (ak:{0}/{1}, s:{2}, path:{3})",
            requester_access_key,
            owner_access_key,
            session_name,
            path,
        )
        result = await root_ctx.processors.session.list_files.wait_for_complete(
            ListFilesAction(
                user_id=request["user"]["uuid"],
                path=path,
                session_name=session_name,
                owner_access_key=owner_access_key,
            )
        )
    except (asyncio.TimeoutError, AssertionError, json.decoder.JSONDecodeError) as e:
        log.warning("LIST_FILES: invalid/missing parameters, {0!r}", e)
        raise InvalidAPIParameters(extra_msg=str(e.args[0]))

    return web.json_response(result.result, status=HTTPStatus.OK)


class ContainerLogRequestModel(LegacyBaseRequestModel):
    owner_access_key: Optional[str] = Field(
        default=None,
        alias="ownerAccessKey",
    )
    kernel_id: Optional[UUID] = Field(
        description="Target kernel to get container logs.",
        default=None,
        alias="kernelId",
    )


@server_status_required(READ_ALLOWED)
@auth_required
@pydantic_params_api_handler(ContainerLogRequestModel)
async def get_container_logs(
    request: web.Request, params: ContainerLogRequestModel
) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name: str = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(
        request, {"owner_access_key": params.owner_access_key}
    )
    # assume retrieving container log of main kernel when `params.kernel_id` is None
    kernel_id = KernelId(params.kernel_id) if params.kernel_id is not None else None
    log.info(
        "GET_CONTAINER_LOG (ak:{}/{}, s:{}, k:{})",
        requester_access_key,
        owner_access_key,
        session_name,
        kernel_id,
    )

    try:
        result = await root_ctx.processors.session.get_container_logs.wait_for_complete(
            GetContainerLogsAction(
                session_name=session_name,
                owner_access_key=owner_access_key,
                kernel_id=kernel_id,
            )
        )
    except BackendAIError:
        log.exception(
            "GET_CONTAINER_LOG(ak:{}/{}, kernel_id: {}, s:{}): unexpected error",
            requester_access_key,
            owner_access_key,
            kernel_id,
            session_name,
        )
        raise
    return web.json_response(result.result, status=HTTPStatus.OK)


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["session_name", "sessionName", "task_id", "taskId"]) >> "kernel_id": tx.UUID,
    })
)
async def get_task_logs(request: web.Request, params: Any) -> web.StreamResponse:
    log.info("GET_TASK_LOG (ak:{}, k:{})", request["keypair"]["access_key"], params["kernel_id"])
    root_ctx: RootContext = request.app["_root.context"]
    domain_name = request["user"]["domain_name"]
    user_role = request["user"]["role"]
    user_uuid = request["user"]["uuid"]
    kernel_id_str = KernelId(params["kernel_id"])

    result = await root_ctx.processors.vfolder.get_task_logs.wait_for_complete(
        GetTaskLogsAction(
            user_id=user_uuid,
            domain_name=domain_name,
            user_role=user_role,
            kernel_id=KernelId(kernel_id_str),
            owner_access_key=request["keypair"]["access_key"],
            request=request,
        )
    )
    return result.response


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        t.Key("owner_access_key", default=None): t.Null | t.String,
    })
)
async def get_status_history(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name: str = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    log.info(
        "GET_STATUS_HISTORY (ak:{}/{}, s:{})", requester_access_key, owner_access_key, session_name
    )

    resp: dict[str, Mapping] = {"result": {}}
    result = await root_ctx.processors.session.get_status_history.wait_for_complete(
        GetStatusHistoryAction(
            session_name=session_name,
            owner_access_key=request["keypair"]["access_key"],
        )
    )

    resp["result"] = result.status_history
    return web.json_response(resp, status=200)


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    agent_lost_checker: asyncio.Task[None]
    stats_task: asyncio.Task[None]
    database_ptask_group: aiotools.PersistentTaskGroup
    rpc_ptask_group: aiotools.PersistentTaskGroup
    webhook_ptask_group: aiotools.PersistentTaskGroup


async def init(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["session.context"]
    app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()
    app_ctx.rpc_ptask_group = aiotools.PersistentTaskGroup()
    app_ctx.webhook_ptask_group = aiotools.PersistentTaskGroup()

    # Scan ALIVE agents
    app_ctx.agent_lost_checker = aiotools.create_timer(
        functools.partial(check_agent_lost, root_ctx), 1.0
    )
    app_ctx.agent_lost_checker.set_name("agent_lost_checker")
    app_ctx.stats_task = aiotools.create_timer(
        functools.partial(report_stats, root_ctx),
        5.0,
    )
    app_ctx.stats_task.set_name("stats_task")


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["session.context"]
    app_ctx.agent_lost_checker.cancel()
    await app_ctx.agent_lost_checker
    app_ctx.stats_task.cancel()
    await app_ctx.stats_task

    await app_ctx.webhook_ptask_group.shutdown()
    await app_ctx.database_ptask_group.shutdown()
    await app_ctx.rpc_ptask_group.shutdown()


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["api_versions"] = (1, 2, 3, 4)
    app["session.context"] = PrivateContext()
    app["prefix"] = "session"
    deprecated_get_stub = deprecated_stub(
        "Use the HTTP POST method to invoke this API with parameters in the request body."
    )
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("POST", "", create_from_params))
    cors.add(app.router.add_route("POST", "/_/create", create_from_params))
    cors.add(app.router.add_route("POST", "/_/create-from-template", create_from_template))
    cors.add(app.router.add_route("POST", "/_/create-cluster", create_cluster))
    cors.add(app.router.add_route("GET", "/_/match", match_sessions))
    cors.add(app.router.add_route("POST", "/_/sync-agent-registry", sync_agent_registry))
    cors.add(app.router.add_route("POST", "/_/transit-status", check_and_transit_status))
    session_resource = cors.add(app.router.add_resource(r"/{session_name}"))
    cors.add(session_resource.add_route("GET", get_info))
    cors.add(session_resource.add_route("PATCH", restart))
    cors.add(session_resource.add_route("DELETE", destroy))
    cors.add(session_resource.add_route("POST", execute))
    task_log_resource = cors.add(app.router.add_resource(r"/_/logs"))
    cors.add(task_log_resource.add_route("HEAD", get_task_logs))
    cors.add(task_log_resource.add_route("GET", get_task_logs))
    cors.add(
        app.router.add_route("GET", "/{session_name}/direct-access-info", get_direct_access_info)
    )
    cors.add(app.router.add_route("GET", "/{session_name}/logs", get_container_logs))
    cors.add(app.router.add_route("POST", "/{session_name}/rename", rename_session))
    cors.add(app.router.add_route("POST", "/{session_name}/interrupt", interrupt))
    cors.add(app.router.add_route("POST", "/{session_name}/complete", complete))
    cors.add(app.router.add_route("POST", "/{session_name}/shutdown-service", shutdown_service))
    cors.add(app.router.add_route("POST", "/{session_name}/upload", upload_files))
    cors.add(app.router.add_route("GET", "/{session_name}/download", deprecated_get_stub))
    cors.add(app.router.add_route("GET", "/{session_name}/download_single", deprecated_get_stub))
    cors.add(app.router.add_route("POST", "/{session_name}/download", download_files))
    cors.add(app.router.add_route("POST", "/{session_name}/download_single", download_single))
    cors.add(app.router.add_route("GET", "/{session_name}/files", list_files))
    cors.add(app.router.add_route("POST", "/{session_name}/start-service", start_service))
    cors.add(app.router.add_route("POST", "/{session_name}/commit", commit_session))
    cors.add(app.router.add_route("POST", "/{session_name}/imagify", convert_session_to_image))
    cors.add(app.router.add_route("GET", "/{session_name}/commit", get_commit_status))
    cors.add(app.router.add_route("GET", "/{session_name}/status-history", get_status_history))
    cors.add(app.router.add_route("GET", "/{session_name}/abusing-report", get_abusing_report))
    cors.add(app.router.add_route("GET", "/{session_name}/dependency-graph", get_dependency_graph))
    return app, []

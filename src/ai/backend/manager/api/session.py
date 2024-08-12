"""
REST-style session management APIs.
"""

from __future__ import annotations

import asyncio
import base64
import enum
import functools
import json
import logging
import re
import secrets
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import PurePosixPath
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Set,
    Tuple,
    Union,
    cast,
    get_args,
)
from urllib.parse import urlparse

import aiohttp
import aiohttp_cors
import aiotools
import attrs
import multidict
import sqlalchemy as sa
import sqlalchemy.exc
import trafaret as t
from aiohttp import hdrs, web
from dateutil.tz import tzutc
from pydantic import AliasChoices, BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy.orm import noload, selectinload
from sqlalchemy.sql.expression import null, true

from ai.backend.common.bgtask import ProgressReporter
from ai.backend.common.docker import ImageRef
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import rescan_images

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common import redis_helper
from ai.backend.common import validators as tx
from ai.backend.common.events import (
    AgentTerminatedEvent,
    BgtaskCancelledEvent,
    BgtaskDoneEvent,
    BgtaskFailedEvent,
)
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.plugin.monitor import GAUGE
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    ImageRegistry,
    KernelId,
    MountPermission,
    MountTypes,
    SessionTypes,
    VFolderID,
)

from ..config import DEFAULT_CHUNK_SIZE
from ..defs import DEFAULT_IMAGE_ARCH, DEFAULT_ROLE
from ..models import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    DEAD_SESSION_STATUSES,
    ImageRow,
    KernelLoadingStrategy,
    KernelRole,
    SessionDependencyRow,
    SessionRow,
    SessionStatus,
    UserRole,
    groups,
    kernels,
    keypairs,
    query_accessible_vfolders,
    scaling_groups,
    session_templates,
    vfolders,
)
from ..types import UserScope
from ..utils import query_userinfo as _query_userinfo
from .auth import auth_required
from .exceptions import (
    AppNotFound,
    BackendError,
    GenericForbidden,
    InsufficientPrivilege,
    InternalServerError,
    InvalidAPIParameters,
    ObjectNotFound,
    QuotaExceeded,
    ServiceUnavailable,
    SessionAlreadyExists,
    SessionNotFound,
    StorageProxyError,
    TaskTemplateNotFound,
    TooManySessionsMatched,
    UnknownImageReferenceError,
)
from .manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from .scaling_group import query_wsproxy_status
from .types import CORSOptions, WebMiddleware
from .utils import (
    BaseResponseModel,
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
    tx.AliasedKey(["resource_opts", "resourceOpts"], default=None): t.Null
    | t.Mapping(t.String, t.Any),
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
        UndefChecker | t.Null | t.Mapping(t.String, t.Any)
    ),
})
creation_config_v4 = t.Dict({
    t.Key("mounts", default=None): t.Null | t.List(t.String),
    tx.AliasedKey(["mount_map", "mountMap"], default=None): t.Null | t.Mapping(t.String, t.String),
    t.Key("environ", default=None): t.Null | t.Mapping(t.String, t.String),
    tx.AliasedKey(["cluster_size", "clusterSize"], default=None): t.Null | t.Int[1:],
    tx.AliasedKey(["scaling_group", "scalingGroup"], default=None): t.Null | t.String,
    t.Key("resources", default=None): t.Null | t.Mapping(t.String, t.Any),
    tx.AliasedKey(["resource_opts", "resourceOpts"], default=None): t.Null
    | t.Mapping(t.String, t.Any),
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
        UndefChecker | t.Null | t.Mapping(t.String, t.Any)
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
    tx.AliasedKey(["resource_opts", "resourceOpts"], default=None): t.Null
    | t.Mapping(t.String, t.Any),
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
        UndefChecker | t.Null | t.Mapping(t.String, t.Any)
    ),
})


overwritten_param_check = t.Dict({
    t.Key("template_id"): tx.UUID,
    t.Key("session_name"): t.Regexp(r"^(?=.{4,64}$)\w[\w.-]*\w$", re.ASCII),
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
    tx.AliasedKey(["cluster_mode", "clusterMode"], default="single-node"): tx.Enum(ClusterMode),
    tx.AliasedKey(["starts_at", "startsAt"], default=None): t.Null | t.String,
}).allow_extra("*")


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


async def query_userinfo(
    request: web.Request,
    params: Any,
    conn: SAConnection,
) -> Tuple[uuid.UUID, uuid.UUID, dict]:
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


async def _create(request: web.Request, params: dict[str, Any]) -> web.Response:
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

    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin_readonly() as conn:
        owner_uuid, group_id, resource_policy = await query_userinfo(request, params, conn)

    sudo_session_enabled = request["user"]["sudo_session_enabled"]

    try:
        resp = await root_ctx.registry.create_session(
            params["session_name"],
            params["image"],
            params["architecture"],
            UserScope(
                domain_name=domain_name,
                group_id=group_id,
                user_uuid=request["user"]["uuid"],
                user_role=request["user"]["role"],
            ),
            owner_access_key,
            resource_policy,
            params["session_type"],
            params["config"],
            params["cluster_mode"],
            params["cluster_size"],
            reuse=params["reuse"],
            enqueue_only=params["enqueue_only"],
            max_wait_seconds=params["max_wait_seconds"],
            bootstrap_script=params["bootstrap_script"],
            dependencies=params["dependencies"],
            startup_command=params["startup_command"],
            starts_at_timestamp=params["starts_at"],
            tag=params["tag"],
            callback_url=params["callback_url"],
            sudo_session_enabled=sudo_session_enabled,
        )
        return web.json_response(resp, status=201)
    except UnknownImageReference:
        raise UnknownImageReferenceError(f"Unknown image reference: {params['image']}")
    except BackendError:
        log.exception("GET_OR_CREATE: exception")
        raise
    except Exception:
        await root_ctx.error_monitor.capture_exception(context={"user": owner_uuid})
        log.exception("GET_OR_CREATE: unexpected error!")
        raise InternalServerError


@server_status_required(ALL_ALLOWED)
@auth_required
@check_api_params(
    t.Dict(
        {
            tx.AliasedKey(["template_id", "templateId"]): t.Null | tx.UUID,
            tx.AliasedKey(["name", "session_name", "clientSessionToken"], default=undefined)
            >> "session_name": UndefChecker | t.Regexp(r"^(?=.{4,64}$)\w[\w.-]*\w$", re.ASCII),
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
            tx.AliasedKey(["cluster_mode", "clusterMode"], default="single-node"): tx.Enum(
                ClusterMode
            ),  # new in APIv6
            t.Key("config", default=dict): t.Mapping(t.String, t.Any),
            t.Key("tag", default=undefined): UndefChecker | t.Null | t.String,
            t.Key("enqueueOnly", default=False) >> "enqueue_only": t.ToBool,
            t.Key("maxWaitSeconds", default=0) >> "max_wait_seconds": t.Int[0:],
            tx.AliasedKey(["starts_at", "startsAt"], default=None): t.Null | t.String,
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
        },
    ),
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
        if 6 <= api_version[0]:
            params["config"] = creation_config_v5_template.check(params["config"])
        elif 5 <= api_version[0]:
            params["config"] = creation_config_v4_template.check(params["config"])
        elif (4, "20190315") <= api_version:
            params["config"] = creation_config_v3_template.check(params["config"])
    except t.DataError as e:
        log.debug("Validation error: {0}", e.as_dict())
        raise InvalidAPIParameters("Input validation error", extra_data=e.as_dict())
    async with root_ctx.db.begin_readonly() as conn:
        query = (
            sa.select([session_templates])
            .select_from(session_templates)
            .where(
                (session_templates.c.id == params["template_id"]) & session_templates.c.is_active,
            )
        )
        result = await conn.execute(query)
        template_info = result.fetchone()
        template = template_info["template"]
        if not template:
            raise TaskTemplateNotFound
        group_name = None
        if template_info["domain_name"] and template_info["group_id"]:
            query = (
                sa.select([groups.c.name])
                .select_from(groups)
                .where(
                    (groups.c.domain_name == template_info["domain_name"])
                    & (groups.c.id == template_info["group_id"]),
                )
            )
            group_name = await conn.scalar(query)

    if isinstance(template, str):
        template = json.loads(template)
    log.debug("Template: {0}", template)

    param_from_template = {
        "image": template["spec"]["kernel"]["image"],
        "architecture": template["spec"]["kernel"]["architecture"],
    }
    if "domain_name" in template_info:
        param_from_template["domain"] = template_info["domain_name"]
    if group_name:
        param_from_template["group"] = group_name
    if template["spec"]["session_type"] == "interactive":
        param_from_template["session_type"] = SessionTypes.INTERACTIVE
    elif template["spec"]["session_type"] == "batch":
        param_from_template["session_type"] = SessionTypes.BATCH
    elif template["spec"]["session_type"] == "inference":
        param_from_template["session_type"] = SessionTypes.INFERENCE

    if tag := template["metadata"].get("tag"):
        param_from_template["tag"] = tag
    if runtime_opt := template["spec"]["kernel"]["run"]:
        if bootstrap := runtime_opt["bootstrap"]:
            param_from_template["bootstrap_script"] = bootstrap
        if startup := runtime_opt["startup_command"]:
            param_from_template["startup_command"] = startup

    config_from_template: MutableMapping[Any, Any] = {}
    if scaling_group := template["spec"].get("scaling_group"):
        config_from_template["scaling_group"] = scaling_group
    if mounts := template["spec"].get("mounts"):
        config_from_template["mounts"] = list(mounts.keys())
        config_from_template["mount_map"] = {
            key: value for (key, value) in mounts.items() if len(value) > 0
        }
    if environ := template["spec"]["kernel"].get("environ"):
        config_from_template["environ"] = environ
    if resources := template["spec"].get("resources"):
        config_from_template["resources"] = resources
    if "agent_list" in template["spec"]:
        config_from_template["agent_list"] = template["spec"]["agent_list"]

    override_config = drop(dict(params["config"]), undefined)
    override_params = drop(dict(params), undefined)

    log.debug("Default config: {0}", config_from_template)
    log.debug("Default params: {0}", param_from_template)

    log.debug("Override config: {0}", override_config)
    log.debug("Override params: {0}", override_params)
    if override_config:
        config_from_template.update(override_config)
    if override_params:
        param_from_template.update(override_params)
    try:
        params = overwritten_param_check.check(param_from_template)
    except RuntimeError as e1:
        log.exception(e1)
    except t.DataError as e2:
        log.debug("Error: {0}", str(e2))
        raise InvalidAPIParameters("Error while validating template")
    params["config"] = config_from_template

    log.debug("Updated param: {0}", params)

    if git := template["spec"]["kernel"]["git"]:
        if _dest := git.get("dest_dir"):
            target = _dest
        else:
            target = git["repository"].split("/")[-1]

        cmd_builder = "git clone "
        if credential := git.get("credential"):
            proto, url = git["repository"].split("://")
            cmd_builder += f'{proto}://{credential["username"]}:{credential["password"]}@{url}'
        else:
            cmd_builder += git["repository"]
        if branch := git.get("branch"):
            cmd_builder += f" -b {branch}"
        cmd_builder += f" {target}\n"

        if commit := git.get("commit"):
            cmd_builder = "CWD=$(pwd)\n" + cmd_builder
            cmd_builder += f"cd {target}\n"
            cmd_builder += f"git checkout {commit}\n"
            cmd_builder += "cd $CWD\n"

        bootstrap = base64.b64decode(params.get("bootstrap_script") or b"").decode()
        bootstrap += "\n"
        bootstrap += cmd_builder
        params["bootstrap_script"] = base64.b64encode(bootstrap.encode()).decode()
    return await _create(request, params)


@server_status_required(ALL_ALLOWED)
@auth_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["name", "session_name", "clientSessionToken"]) >> "session_name": t.Regexp(
            r"^(?=.{4,64}$)\w[\w.-]*\w$", re.ASCII
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
        tx.AliasedKey(["cluster_mode", "clusterMode"], default="single-node"): tx.Enum(
            ClusterMode
        ),  # new in APIv6
        t.Key("config", default=dict): t.Mapping(t.String, t.Any),
        t.Key("tag", default=None): t.Null | t.String,
        t.Key("enqueueOnly", default=False) >> "enqueue_only": t.ToBool,
        t.Key("maxWaitSeconds", default=0) >> "max_wait_seconds": t.ToInt[0:],
        tx.AliasedKey(["starts_at", "startsAt"], default=None): t.Null | t.String,
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
            f'Requested session ID {params["session_name"]} is reserved word'
        )
    api_version = request["api_version"]
    if 6 <= api_version[0]:
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
    if params["config"]["agent_list"] is not None and request["user"]["role"] != (
        UserRole.SUPERADMIN
    ):
        raise InsufficientPrivilege(
            "You are not allowed to manually assign agents for your session."
        )
    if request["user"]["role"] == (UserRole.SUPERADMIN):
        if not params["config"]["agent_list"]:
            pass
        else:
            agent_count = len(params["config"]["agent_list"])
            if params["cluster_mode"] == "multi-node":
                if agent_count != params["cluster_size"]:
                    raise InvalidAPIParameters(
                        "For multi-node cluster sessions, the number of manually assigned"
                        " agents must be same to the cluster size. Note that you may specify"
                        " duplicate agents in the list.",
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
        t.Key("clientSessionToken") >> "session_name": t.Regexp(
            r"^(?=.{4,64}$)\w[\w.-]*\w$", re.ASCII
        ),
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
        "CREAT_CLUSTER (ak:{0}/{1}, s:{3})",
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else "*",
        params["session_name"],
    )

    async with root_ctx.db.begin_readonly() as conn:
        query = (
            sa.select([session_templates.c.template])
            .select_from(session_templates)
            .where(
                (session_templates.c.id == params["template_id"]) & session_templates.c.is_active,
            )
        )
        template = await conn.scalar(query)
        log.debug("task template: {}", template)
        if not template:
            raise TaskTemplateNotFound
        owner_uuid, group_id, resource_policy = await query_userinfo(request, params, conn)
        sudo_session_enabled = request["user"]["sudo_session_enabled"]

    try:
        resp = await root_ctx.registry.create_cluster(
            template,
            params["session_name"],
            UserScope(
                domain_name=domain_name,
                group_id=group_id,
                user_uuid=request["user"]["uuid"],
                user_role=request["user"]["role"],
            ),
            owner_access_key,
            resource_policy,
            params["scaling_group"],
            params["sess_type"],
            params["tag"],
            enqueue_only=params["enqueue_only"],
            max_wait_seconds=params["max_wait_seconds"],
            sudo_session_enabled=sudo_session_enabled,
        )
        return web.json_response(resp, status=201)
    except TooManySessionsMatched:
        raise SessionAlreadyExists
    except BackendError:
        log.exception("GET_OR_CREATE: exception")
        raise
    except UnknownImageReference:
        raise UnknownImageReferenceError(f"Unknown image reference: {params['image']}")
    except Exception:
        await root_ctx.error_monitor.capture_exception()
        log.exception("GET_OR_CREATE: unexpected error!")
        raise InternalServerError


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
    app_ctx: PrivateContext = request.app["session.context"]
    access_key: AccessKey = request["keypair"]["access_key"]
    service: str = params["app"]
    myself = asyncio.current_task()
    assert myself is not None
    try:
        async with root_ctx.db.begin_readonly_session() as db_sess:
            session = await asyncio.shield(
                app_ctx.database_ptask_group.create_task(
                    SessionRow.get_session(
                        db_sess,
                        session_name,
                        access_key,
                        kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                        eager_loading_op=[
                            selectinload(SessionRow.routing).options(noload("*")),
                        ],
                    ),
                )
            )
    except (SessionNotFound, TooManySessionsMatched):
        raise

    query = (
        sa.select([scaling_groups.c.wsproxy_addr])
        .select_from(scaling_groups)
        .where((scaling_groups.c.name == session.scaling_group_name))
    )

    async with root_ctx.db.begin_readonly() as conn:
        result = await conn.execute(query)
        sgroup = result.first()
    wsproxy_addr = sgroup["wsproxy_addr"]
    if not wsproxy_addr:
        raise ServiceUnavailable("No coordinator configured for this resource group")
    wsproxy_status = await query_wsproxy_status(wsproxy_addr)
    if advertise_addr := wsproxy_status.get("advertise_address"):
        wsproxy_advertise_addr = advertise_addr
    else:
        wsproxy_advertise_addr = wsproxy_addr

    if session.main_kernel.kernel_host is None:
        kernel_host = urlparse(session.main_kernel.agent_addr).hostname
    else:
        kernel_host = session.main_kernel.kernel_host
    for sport in session.main_kernel.service_ports:
        if sport["name"] == service:
            if sport["is_inference"]:
                raise InvalidAPIParameters(
                    f"{service} is an inference app. Starting inference apps can only be done by"
                    " starting an inference service."
                )
            if params["port"]:
                # using one of the primary/secondary ports of the app
                try:
                    hport_idx = sport["container_ports"].index(params["port"])
                except ValueError:
                    raise InvalidAPIParameters(
                        f"Service {service} does not open the port number {params['port']}."
                    )
                host_port = sport["host_ports"][hport_idx]
            else:
                # using the default (primary) port of the app
                if "host_ports" not in sport:
                    host_port = sport["host_port"]  # legacy kernels
                else:
                    host_port = sport["host_ports"][0]
            break
    else:
        raise AppNotFound(f"{session_name}:{service}")

    await asyncio.shield(
        app_ctx.database_ptask_group.create_task(
            root_ctx.registry.increment_session_usage(session),
        )
    )

    opts: MutableMapping[str, Union[None, str, List[str]]] = {}
    if params["arguments"] is not None:
        opts["arguments"] = json.loads(params["arguments"])
    if params["envs"] is not None:
        opts["envs"] = json.loads(params["envs"])

    result = await asyncio.shield(
        app_ctx.rpc_ptask_group.create_task(
            root_ctx.registry.start_service(session, service, opts),
        ),
    )
    if result["status"] == "failed":
        raise InternalServerError("Failed to launch the app service", extra_data=result["error"])

    body = {
        "login_session_token": params["login_session_token"],
        "kernel_host": kernel_host,
        "kernel_port": host_port,
        "session": {
            "id": str(session.id),
            "user_uuid": str(session.user_uuid),
            "group_id": str(session.group_id),
            "access_key": session.access_key,
            "domain_name": session.domain_name,
        },
    }

    async with aiohttp.ClientSession() as req:
        async with req.post(
            f"{wsproxy_addr}/v2/conf",
            json=body,
        ) as resp:
            token_json = await resp.json()
            return web.json_response({
                "token": token_json["token"],
                "wsproxy_addr": wsproxy_advertise_addr,
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
    try:
        async with root_ctx.db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
        statuses = await root_ctx.registry.get_commit_status([session.main_kernel.id])
    except BackendError:
        log.exception("GET_COMMIT_STATUS: exception")
        raise
    resp = {"status": statuses[session.main_kernel.id], "kernel": str(session.main_kernel.id)}
    return web.json_response(resp, status=200)


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
    try:
        async with root_ctx.db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
        kernel = session.main_kernel
        report = await root_ctx.registry.get_abusing_report(kernel.id)
    except BackendError:
        log.exception("GET_ABUSING_REPORT: exception")
        raise
    return web.json_response(report or {}, status=200)


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
    try:
        await root_ctx.registry.sync_agent_kernel_registry(agent_id)
    except BackendError:
        log.exception("SYNC_AGENT_REGISTRY: exception")
        raise
    return web.json_response({}, status=200)


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
    app_ctx: PrivateContext = request.app["session.context"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    filename: str | None = params["filename"]

    myself = asyncio.current_task()
    assert myself is not None

    log.info(
        "COMMIT_SESSION (ak:{}/{}, s:{})", requester_access_key, owner_access_key, session_name
    )
    try:
        async with root_ctx.db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )

        resp: Mapping[str, Any] = await asyncio.shield(
            app_ctx.rpc_ptask_group.create_task(
                root_ctx.registry.commit_session_to_file(session, filename),
            ),
        )
    except BackendError:
        log.exception("COMMIT_SESSION: exception")
        raise
    return web.json_response(resp, status=201)


class CustomizedImageVisibilityScope(str, enum.Enum):
    USER = "user"
    PROJECT = "project"


class ConvertSessionToImageRequesteModel(BaseModel):
    image_name: str = Field(
        pattern=r"[a-zA-Z0-9\.\-_]+",
        description="Name of the image to be created.",
    )
    login_session_token: Annotated[str | None, Field(default=None)]
    image_visibility: CustomizedImageVisibilityScope = Field(
        default=CustomizedImageVisibilityScope.USER,
        description="Visibility scope of newly created image. currently only supports `USER` scope. Setting this to value other than `USER` will raise error.",
    )


class ConvertSessionToImageResponseModel(BaseResponseModel):
    task_id: str


@auth_required
@server_status_required(ALL_ALLOWED)
@pydantic_params_api_handler(ConvertSessionToImageRequesteModel)
async def convert_session_to_image(
    request: web.Request, params: ConvertSessionToImageRequesteModel
) -> ConvertSessionToImageResponseModel:
    root_ctx: RootContext = request.app["_root.context"]
    background_task_manager = root_ctx.background_task_manager

    session_name: str = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)

    myself = asyncio.current_task()
    assert myself is not None

    if params.image_visibility != CustomizedImageVisibilityScope.USER:
        raise InvalidAPIParameters(f"Unsupported visibility scope {params.image_visibility}")

    log.info(
        "CONVERT_SESSION_TO_IMAGE (ak:{}/{}, s:{})",
        requester_access_key,
        owner_access_key,
        session_name,
    )
    async with root_ctx.db.begin_readonly_session() as db_sess:
        session = await SessionRow.get_session(
            db_sess,
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            eager_loading_op=[selectinload(SessionRow.group)],
        )

    project: GroupRow = session.group
    if not project.container_registry:
        raise InvalidAPIParameters(
            "Project not ready to convert session image (registry configuration not populated)"
        )

    registry_hostname = project.container_registry["registry"]
    registry_project = project.container_registry["project"]
    registry_conf = await root_ctx.shared_config.get_container_registry(registry_hostname)
    if not registry_conf:
        raise InvalidAPIParameters(f"Registry {registry_hostname} not found")
    if registry_project not in registry_conf.get("project", ""):
        raise InvalidAPIParameters(f"Project {registry_project} not found")

    base_image_ref = session.main_kernel.image_ref

    image_owner_id = request["user"]["uuid"]

    async def _commit_and_upload(reporter: ProgressReporter) -> None:
        reporter.total_progress = 3
        await reporter.update(message="Commit started")
        try:
            if "/" in base_image_ref.name:
                new_name = base_image_ref.name.split("/", maxsplit=1)[1]
            else:
                # for cases where project name is not specified (e.g. redis, nginx, ...)
                new_name = base_image_ref.name

            # remove any existing customized related tag from base canonical
            filtered_tag_set = [
                x for x in base_image_ref.tag.split("-") if not x.startswith("customized_")
            ]

            new_canonical = (
                f"{registry_hostname}/{registry_project}/{new_name}:{'-'.join(filtered_tag_set)}"
            )

            async with root_ctx.db.begin_readonly_session() as sess:
                # check if user has passed its limit of customized image count
                query = (
                    sa.select([sa.func.count()])
                    .select_from(ImageRow)
                    .where(
                        (
                            ImageRow.labels["ai.backend.customized-image.owner"].as_string()
                            == f"{params.image_visibility.value}:{image_owner_id}"
                        )
                    )
                )
                existing_image_count = await sess.scalar(query)

                customized_image_count_limit = request["user"]["resource_policy"][
                    "max_customized_image_count"
                ]
                if customized_image_count_limit <= existing_image_count:
                    raise QuotaExceeded(
                        extra_msg="You have reached your customized image count quota",
                        extra_data={
                            "limit": customized_image_count_limit,
                            "current": existing_image_count,
                        },
                    )

                # check if image with same name exists and reuse ID it if is
                query = sa.select(ImageRow).where(
                    ImageRow.name.like(f"{new_canonical}%")
                    & (
                        ImageRow.labels["ai.backend.customized-image.owner"].as_string()
                        == f"{params.image_visibility.value}:{image_owner_id}"
                    )
                    & (
                        ImageRow.labels["ai.backend.customized-image.name"].as_string()
                        == params.image_name
                    )
                )
                existing_row = await sess.scalar(query)

                customized_image_id: str
                if existing_row:
                    customized_image_id = existing_row.labels["ai.backend.customized-image.id"]
                    log.debug("reusing existing customized image ID {}", customized_image_id)
                else:
                    customized_image_id = str(uuid.uuid4())

            new_canonical += f"-customized_{customized_image_id.replace('-', '')}"
            new_image_ref: ImageRef = ImageRef(
                new_canonical,
                architecture=base_image_ref.architecture,
                known_registries=["*"],
                is_local=base_image_ref.is_local,
            )

            image_labels = {
                "ai.backend.customized-image.owner": f"{params.image_visibility.value}:{image_owner_id}",
                "ai.backend.customized-image.name": params.image_name,
                "ai.backend.customized-image.id": customized_image_id,
            }
            match params.image_visibility:
                case CustomizedImageVisibilityScope.USER:
                    image_labels["ai.backend.customized-image.user.email"] = request["user"][
                        "email"
                    ]

            # commit image with new tag set
            resp = await root_ctx.registry.commit_session(
                session,
                new_image_ref,
                extra_labels=image_labels,
            )
            async for event, _ in background_task_manager.poll_bgtask_event(
                uuid.UUID(resp["bgtask_id"])
            ):
                match event:
                    case BgtaskDoneEvent():
                        await reporter.update(increment=1, message="Committed image")
                        break
                    case BgtaskFailedEvent():
                        raise BackendError(extra_msg=event.message)
                    case BgtaskCancelledEvent():
                        raise BackendError(extra_msg="Operation cancelled")

            if not new_image_ref.is_local:
                # push image to registry from local agent
                image_registry = ImageRegistry(
                    name=registry_hostname,
                    url=str(registry_conf[""]),
                    username=registry_conf.get("username"),
                    password=registry_conf.get("password"),
                )
                resp = await root_ctx.registry.push_image(
                    session.main_kernel.agent,
                    new_image_ref,
                    image_registry,
                )
                async for event, _ in background_task_manager.poll_bgtask_event(
                    uuid.UUID(resp["bgtask_id"])
                ):
                    match event:
                        case BgtaskDoneEvent():
                            break
                        case BgtaskFailedEvent():
                            raise BackendError(extra_msg=event.message)
                        case BgtaskCancelledEvent():
                            raise BackendError(extra_msg="Operation cancelled")

            await reporter.update(increment=1, message="Pushed image to registry")
            # rescan updated image only
            await rescan_images(
                root_ctx.shared_config.etcd,
                root_ctx.db,
                new_image_ref.canonical,
                local=new_image_ref.is_local,
            )
            await reporter.update(increment=1, message="Completed")
        except BackendError:
            log.exception("CONVERT_SESSION_TO_IMAGE: exception")
            raise

    task_id = await background_task_manager.start(_commit_and_upload)
    return ConvertSessionToImageResponseModel(task_id=str(task_id))


@catch_unexpected(log)
async def check_agent_lost(root_ctx: RootContext, interval: float) -> None:
    try:
        now = datetime.now(tzutc())
        timeout = timedelta(seconds=root_ctx.local_config["manager"]["heartbeat-timeout"])

        async def _check_impl(r: Redis):
            async for agent_id, prev in r.hscan_iter("agent.last_seen"):
                prev = datetime.fromtimestamp(float(prev), tzutc())
                if now - prev > timeout:
                    await root_ctx.event_producer.produce_event(
                        AgentTerminatedEvent("agent-lost"), source=agent_id.decode()
                    )

        await redis_helper.execute(root_ctx.redis_live, _check_impl)
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
        tx.AliasedKey(["name", "session_name", "clientSessionToken"]) >> "session_name": t.Regexp(
            r"^(?=.{4,64}$)\w[\w.-]*\w$", re.ASCII
        ),
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
    async with root_ctx.db.begin_session() as db_sess:
        compute_session = await SessionRow.get_session(
            db_sess,
            session_name,
            owner_access_key,
            allow_stale=True,
            for_update=True,
            kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS,
        )
        if compute_session.status != SessionStatus.RUNNING:
            raise InvalidAPIParameters("Can't change name of not running session")
        compute_session.name = new_name
        for kernel in compute_session.kernels:
            kernel.session_name = new_name
        await db_sess.commit()

    return web.Response(status=204)


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
    # domain_name = None
    # if requester_access_key != owner_access_key and \
    #         not request['is_superadmin'] and request['is_admin']:
    #     domain_name = request['user']['domain_name']
    log.info(
        "DESTROY (ak:{0}/{1}, s:{2}, forced:{3}, recursive: {4})",
        requester_access_key,
        owner_access_key,
        session_name,
        params["forced"],
        params["recursive"],
    )

    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)

    if params["recursive"]:
        async with root_ctx.db.begin_readonly_session() as db_sess:
            dependent_session_ids = await find_dependent_sessions(
                session_name,
                db_sess,
                owner_access_key,
                allow_stale=True,
            )

            target_session_references: List[str | uuid.UUID] = [
                *dependent_session_ids,
                session_name,
            ]
            sessions: Iterable[SessionRow | BaseException] = await asyncio.gather(
                *[
                    SessionRow.get_session(
                        db_sess,
                        name_or_id,
                        owner_access_key,
                        kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS,
                    )
                    for name_or_id in target_session_references
                ],
                return_exceptions=True,
            )

        last_stats = await asyncio.gather(
            *[
                root_ctx.registry.destroy_session(
                    sess, forced=params["forced"], user_role=user_role
                )
                for sess in sessions
                if isinstance(sess, SessionRow)
            ],
            return_exceptions=True,
        )

        # Consider not found sessions already terminated.
        # Consider GenericForbidden error occurs with scheduled/preparing/terminating/error status session, and leave them not to be quitted.
        last_stats = [
            *filter(lambda x: not isinstance(x, SessionNotFound | GenericForbidden), last_stats)
        ]

        return web.json_response(last_stats, status=200)
    else:
        async with root_ctx.db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS,
            )
        last_stat = await root_ctx.registry.destroy_session(
            session,
            forced=params["forced"],
            user_role=user_role,
        )
        resp = {
            "stats": last_stat,
        }
        return web.json_response(resp, status=200)


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
    matches: List[Dict[str, Any]] = []
    async with root_ctx.db.begin_readonly_session() as db_sess:
        sessions = await SessionRow.match_sessions(
            db_sess,
            id_or_name_prefix,
            owner_access_key,
        )
    if sessions:
        matches.extend(
            {
                "id": str(item.id),
                "name": item.name,
                "status": item.status.name,
            }
            for item in sessions
        )
    return web.json_response(
        {
            "matches": matches,
        },
        status=200,
    )


@server_status_required(READ_ALLOWED)
@auth_required
async def get_direct_access_info(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    _, owner_access_key = await get_access_key_scopes(request)

    async with root_ctx.db.begin_session() as db_sess:
        sess = await SessionRow.get_session(
            db_sess,
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
    kernel_role: KernelRole = sess.main_kernel.role
    resp = {}
    if kernel_role == KernelRole.SYSTEM:
        public_host = sess.main_kernel.agent_row.public_host
        found_ports: dict[str, list[str]] = {}
        for sport in sess.main_kernel.service_ports:
            if sport["name"] == "sshd":
                found_ports["sshd"] = sport["host_ports"]
            elif sport["name"] == "sftpd":
                found_ports["sftpd"] = sport["host_ports"]
        resp = {
            "kernel_role": kernel_role.name,
            "public_host": public_host,
            "sshd_ports": found_ports.get("sftpd") or found_ports["sshd"],
        }
    return web.json_response(resp)


@server_status_required(READ_ALLOWED)
@auth_required
async def get_info(request: web.Request) -> web.Response:
    # NOTE: This API should be replaced with GraphQL version.
    resp = {}
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info("GET_INFO (ak:{0}/{1}, s:{2})", requester_access_key, owner_access_key, session_name)
    try:
        async with root_ctx.db.begin_session() as db_sess:
            sess = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
        await root_ctx.registry.increment_session_usage(sess)
        resp["domainName"] = sess.domain_name
        resp["groupId"] = str(sess.group_id)
        resp["userId"] = str(sess.user_uuid)
        resp["lang"] = sess.main_kernel.image  # legacy
        resp["image"] = sess.main_kernel.image
        resp["architecture"] = sess.main_kernel.architecture
        resp["registry"] = sess.main_kernel.registry
        resp["tag"] = sess.tag

        # Resource occupation
        resp["containerId"] = str(sess.main_kernel.container_id)
        resp["occupiedSlots"] = str(sess.main_kernel.occupied_slots)  # legacy
        resp["occupyingSlots"] = str(sess.occupying_slots)
        resp["requestedSlots"] = str(sess.requested_slots)
        resp["occupiedShares"] = str(
            sess.main_kernel.occupied_shares
        )  # legacy, only caculate main kernel's occupying resource
        resp["environ"] = str(sess.environ)
        resp["resourceOpts"] = str(sess.resource_opts)

        # Lifecycle
        resp["status"] = sess.status.name  # "e.g. 'SessionStatus.RUNNING' -> 'RUNNING' "
        resp["statusInfo"] = str(sess.status_info)
        resp["statusData"] = sess.status_data
        age = datetime.now(tzutc()) - sess.created_at
        resp["age"] = int(age.total_seconds() * 1000)  # age in milliseconds
        resp["creationTime"] = str(sess.created_at)
        resp["terminationTime"] = str(sess.terminated_at) if sess.terminated_at else None

        resp["numQueriesExecuted"] = sess.num_queries
        resp["lastStat"] = sess.last_stat
        resp["idleChecks"] = await root_ctx.idle_checker_host.get_idle_check_report(sess.id)

        # Resource limits collected from agent heartbeats were erased, as they were deprecated
        # TODO: factor out policy/image info as a common repository

        log.info("information retrieved: {0!r}", resp)
    except BackendError:
        log.exception("GET_INFO: exception")
        raise
    return web.json_response(resp, status=200)


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
    async with root_ctx.db.begin_session() as db_sess:
        session = await SessionRow.get_session(
            db_sess,
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS,
        )
    try:
        await root_ctx.registry.increment_session_usage(session)
        await root_ctx.registry.restart_session(session)
    except BackendError:
        log.exception("RESTART: exception")
        raise
    except Exception:
        await root_ctx.error_monitor.capture_exception(context={"user": request["user"]["uuid"]})
        log.exception("RESTART: unexpected error")
        raise web.HTTPInternalServerError
    return web.Response(status=204)


@server_status_required(READ_ALLOWED)
@auth_required
async def execute(request: web.Request) -> web.Response:
    resp = {}
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    try:
        params = await request.json(loads=json.loads)
        log.info("EXECUTE(ak:{0}/{1}, s:{2})", requester_access_key, owner_access_key, session_name)
    except json.decoder.JSONDecodeError:
        log.warning("EXECUTE: invalid/missing parameters")
        raise InvalidAPIParameters
    async with root_ctx.db.begin_readonly_session() as db_sess:
        session = await SessionRow.get_session(
            db_sess,
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
    try:
        await root_ctx.registry.increment_session_usage(session)
        api_version = request["api_version"]
        if api_version[0] == 1:
            run_id = params.get("runId", secrets.token_hex(8))
            mode = "query"
            code = params.get("code", None)
            opts = None
        elif api_version[0] >= 2:
            assert "runId" in params, "runId is missing!"
            run_id = params["runId"]  # maybe None
            assert params.get("mode"), "mode is missing or empty!"
            mode = params["mode"]
            assert mode in {
                "query",
                "batch",
                "complete",
                "continue",
                "input",
            }, "mode has an invalid value."
            if mode in {"continue", "input"}:
                assert run_id is not None, "continuation requires explicit run ID"
            code = params.get("code", None)
            opts = params.get("options", None)
        else:
            raise RuntimeError("should not reach here")
        # handle cases when some params are deliberately set to None
        if code is None:
            code = ""  # noqa
        if opts is None:
            opts = {}  # noqa
        if mode == "complete":
            # For legacy
            resp["result"] = await root_ctx.registry.get_completions(session, code, opts)
        else:
            raw_result = await root_ctx.registry.execute(
                session,
                api_version,
                run_id,
                mode,
                code,
                opts,
                flush_timeout=2.0,
            )
            if raw_result is None:
                # the kernel may have terminated from its side,
                # or there was interruption of agents.
                resp["result"] = {
                    "status": "finished",
                    "runId": run_id,
                    "exitCode": 130,
                    "options": {},
                    "files": [],
                    "console": [],
                }
                return web.json_response(resp, status=200)
            # Keep internal/public API compatilibty
            result = {
                "status": raw_result["status"],
                "runId": raw_result["runId"],
                "exitCode": raw_result.get("exitCode"),
                "options": raw_result.get("options"),
                "files": raw_result.get("files"),
            }
            if api_version[0] == 1:
                result["stdout"] = raw_result.get("stdout")
                result["stderr"] = raw_result.get("stderr")
                result["media"] = raw_result.get("media")
                result["html"] = raw_result.get("html")
            else:
                result["console"] = raw_result.get("console")
            resp["result"] = result
    except AssertionError as e:
        log.warning("EXECUTE: invalid/missing parameters: {0!r}", e)
        raise InvalidAPIParameters(extra_msg=e.args[0])
    except BackendError:
        log.exception("EXECUTE: exception")
        raise
    return web.json_response(resp, status=200)


@server_status_required(READ_ALLOWED)
@auth_required
async def interrupt(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info("INTERRUPT(ak:{0}/{1}, s:{2})", requester_access_key, owner_access_key, session_name)
    async with root_ctx.db.begin_readonly_session() as db_sess:
        session = await SessionRow.get_session(
            db_sess,
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
    try:
        await root_ctx.registry.increment_session_usage(session)
        await root_ctx.registry.interrupt_session(session)
    except BackendError:
        log.exception("INTERRUPT: exception")
        raise
    return web.Response(status=204)


@server_status_required(READ_ALLOWED)
@auth_required
async def complete(request: web.Request) -> web.Response:
    resp = {
        "result": {
            "status": "finished",
            "completions": [],
        },
    }
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    try:
        params = await request.json(loads=json.loads)
        log.info(
            "COMPLETE(ak:{0}/{1}, s:{2})", requester_access_key, owner_access_key, session_name
        )
    except json.decoder.JSONDecodeError:
        raise InvalidAPIParameters
    async with root_ctx.db.begin_readonly_session() as db_sess:
        session = await SessionRow.get_session(
            db_sess,
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
    try:
        code = params.get("code", "")
        opts = params.get("options", None) or {}
        await root_ctx.registry.increment_session_usage(session)
        resp["result"] = cast(
            Dict[str, Any],
            await root_ctx.registry.get_completions(session, code, opts),
        )
    except AssertionError:
        raise InvalidAPIParameters
    except BackendError:
        log.exception("COMPLETE: exception")
        raise
    return web.json_response(resp, status=200)


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
    async with root_ctx.db.begin_readonly_session() as db_sess:
        session = await SessionRow.get_session(
            db_sess,
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
    try:
        await root_ctx.registry.shutdown_service(session, service_name)
    except BackendError:
        log.exception("SHUTDOWN_SERVICE: exception")
        raise
    return web.Response(status=204)


async def find_dependent_sessions(
    root_session_name_or_id: str | uuid.UUID,
    db_session: SASession,
    access_key: AccessKey,
    *,
    allow_stale: bool = False,
) -> Set[uuid.UUID]:
    async def _find_dependent_sessions(session_id: uuid.UUID) -> Set[uuid.UUID]:
        result = await db_session.execute(
            sa.select(SessionDependencyRow).where(SessionDependencyRow.depends_on == session_id)
        )
        dependent_sessions: set[uuid.UUID] = {x.session_id for x in result.scalars()}

        recursive_dependent_sessions: List[Set[uuid.UUID]] = [
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
    return await _find_dependent_sessions(cast(uuid.UUID, root_session.id))


@aiotools.lru_cache(maxsize=100)
async def _find_dependency_sessions(
    session_name_or_id: uuid.UUID | str,
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

    assert isinstance(session_id, get_args(uuid.UUID | str))
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

    session_info: Dict[str, Union[List, str]] = {
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
    session_name_or_id: uuid.UUID | str,
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

    async with root_ctx.db.begin_readonly_session() as db_session:
        return web.json_response(
            await find_dependency_sessions(root_session_name, db_session, owner_access_key),
            status=200,
        )


@server_status_required(READ_ALLOWED)
@auth_required
async def upload_files(request: web.Request) -> web.Response:
    loop = asyncio.get_event_loop()
    reader = await request.multipart()
    root_ctx: RootContext = request.app["_root.context"]
    session_name = request.match_info["session_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request)
    log.info(
        "UPLOAD_FILE (ak:{0}/{1}, s:{2})", requester_access_key, owner_access_key, session_name
    )
    async with root_ctx.db.begin_readonly_session() as db_sess:
        session = await SessionRow.get_session(
            db_sess,
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
    try:
        await root_ctx.registry.increment_session_usage(session)
        file_count = 0
        upload_tasks = []
        async for file in aiotools.aiter(reader.next, None):
            if file_count == 20:
                raise InvalidAPIParameters("Too many files")
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
                    raise InvalidAPIParameters("Too large file")
                chunks.append(chunk)
                recv_size += chunk_size
            data = file.decode(b"".join(chunks))
            log.debug("received file: {0} ({1:,} bytes)", file.filename, recv_size)
            t = loop.create_task(root_ctx.registry.upload_file(session, file.filename, data))
            upload_tasks.append(t)
        await asyncio.gather(*upload_tasks)
    except BackendError:
        log.exception("UPLOAD_FILES: exception")
        raise
    return web.Response(status=204)


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
    async with root_ctx.db.begin_readonly_session() as db_sess:
        session = await SessionRow.get_session(
            db_sess,
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
    try:
        assert len(files) <= 5, "Too many files"
        await root_ctx.registry.increment_session_usage(session)
        # TODO: Read all download file contents. Need to fix by using chuncking, etc.
        results = await asyncio.gather(
            *map(
                functools.partial(root_ctx.registry.download_file, session),
                files,
            ),
        )
        log.debug("file(s) inside container retrieved")
    except asyncio.CancelledError:
        raise
    except BackendError:
        log.exception("DOWNLOAD_FILE: exception")
        raise
    except (ValueError, FileNotFoundError):
        raise InvalidAPIParameters("The file is not found.")
    except Exception:
        await root_ctx.error_monitor.capture_exception(context={"user": request["user"]["uuid"]})
        log.exception("DOWNLOAD_FILE: unexpected error!")
        raise InternalServerError

    with aiohttp.MultipartWriter("mixed") as mpwriter:
        headers = multidict.MultiDict({"Content-Encoding": "identity"})
        for tarbytes in results:
            mpwriter.append(tarbytes, headers)
        return web.Response(body=mpwriter, status=200)


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
    try:
        async with root_ctx.db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
        await root_ctx.registry.increment_session_usage(session)
        result = await root_ctx.registry.download_single(session, owner_access_key, file)
    except asyncio.CancelledError:
        raise
    except BackendError:
        log.exception("DOWNLOAD_SINGLE: exception")
        raise
    except (ValueError, FileNotFoundError):
        raise InvalidAPIParameters("The file is not found.")
    except Exception:
        await root_ctx.error_monitor.capture_exception(context={"user": request["user"]["uuid"]})
        log.exception("DOWNLOAD_SINGLE: unexpected error!")
        raise InternalServerError
    return web.Response(body=result, status=200)


@server_status_required(READ_ALLOWED)
@auth_required
async def list_files(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    try:
        session_name = request.match_info["session_name"]
        requester_access_key, owner_access_key = await get_access_key_scopes(request)
        params = await request.json(loads=json.loads)
        path = params.get("path", ".")
        log.info(
            "LIST_FILES (ak:{0}/{1}, s:{2}, path:{3})",
            requester_access_key,
            owner_access_key,
            session_name,
            path,
        )
        async with root_ctx.db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
    except (asyncio.TimeoutError, AssertionError, json.decoder.JSONDecodeError) as e:
        log.warning("LIST_FILES: invalid/missing parameters, {0!r}", e)
        raise InvalidAPIParameters(extra_msg=str(e.args[0]))
    resp: MutableMapping[str, Any] = {}
    try:
        await root_ctx.registry.increment_session_usage(session)
        result = await root_ctx.registry.list_files(session, path)
        resp.update(result)
        log.debug("container file list for {0} retrieved", path)
    except asyncio.CancelledError:
        raise
    except BackendError:
        log.exception("LIST_FILES: exception")
        raise
    except Exception:
        await root_ctx.error_monitor.capture_exception(context={"user": request["user"]["uuid"]})
        log.exception("LIST_FILES: unexpected error!")
        raise InternalServerError
    return web.json_response(resp, status=200)


class ContainerLogRequestModel(BaseModel):
    owner_access_key: str | None = Field(
        validation_alias=AliasChoices("owner_access_key", "ownerAccessKey"),
        default=None,
    )
    kernel_id: uuid.UUID | None = Field(
        validation_alias=AliasChoices("kernel_id", "kernelId"),
        description="Target kernel to get container logs.",
        default=None,
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
    kernel_id = KernelId(params.kernel_id) if params.kernel_id is not None else None
    log.info(
        "GET_CONTAINER_LOG (ak:{}/{}, s:{}, k:{})",
        requester_access_key,
        owner_access_key,
        session_name,
        kernel_id,
    )
    resp = {"result": {"logs": ""}}
    async with root_ctx.db.begin_readonly_session() as db_sess:
        compute_session = await SessionRow.get_session(
            db_sess,
            session_name,
            owner_access_key,
            allow_stale=True,
            kernel_loading_strategy=(
                KernelLoadingStrategy.MAIN_KERNEL_ONLY
                if kernel_id is None
                else KernelLoadingStrategy.ALL_KERNELS
            ),
        )

        if compute_session.status in DEAD_SESSION_STATUSES:
            if kernel_id is not None:
                # Get logs from the specific kernel
                kernel_row = compute_session.get_kernel_by_id(kernel_id)
                kernel_log = kernel_row.container_log
            else:
                # Get logs from the main kernel
                kernel_log = compute_session.main_kernel.container_log
            if kernel_log is not None:
                # Get logs from database record
                log.debug("returning log from database record")
                resp["result"]["logs"] = kernel_log.decode("utf-8")
                return web.json_response(resp, status=200)

    try:
        registry = root_ctx.registry
        await registry.increment_session_usage(compute_session)
        resp["result"]["logs"] = await registry.get_logs_from_agent(
            session=compute_session, kernel_id=kernel_id
        )
        log.debug("returning log from agent")
    except BackendError:
        log.exception(
            "GET_CONTAINER_LOG(ak:{}/{}, kernel_id: {}, s:{}): unexpected error",
            requester_access_key,
            owner_access_key,
            kernel_id,
            session_name,
        )
        raise
    return web.json_response(resp, status=200)


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
    kernel_id_str = params["kernel_id"].hex
    async with root_ctx.db.begin_readonly() as conn:
        matched_vfolders = await query_accessible_vfolders(
            conn,
            user_uuid,
            user_role=user_role,
            domain_name=domain_name,
            allowed_vfolder_types=["user"],
            extra_vf_conds=(vfolders.c.name == ".logs"),
        )
        if not matched_vfolders:
            raise ObjectNotFound(
                extra_data={"vfolder_name": ".logs"},
                object_name="vfolder",
            )
        log_vfolder = matched_vfolders[0]

    proxy_name, volume_name = root_ctx.storage_manager.split_host(log_vfolder["host"])
    response = web.StreamResponse(status=200)
    response.headers[hdrs.CONTENT_TYPE] = "text/plain"
    prepared = False
    try:
        async with root_ctx.storage_manager.request(
            log_vfolder["host"],
            "POST",
            "folder/file/fetch",
            json={
                "volume": volume_name,
                "vfid": str(VFolderID.from_row(log_vfolder)),
                "relpath": str(
                    PurePosixPath("task")
                    / kernel_id_str[:2]
                    / kernel_id_str[2:4]
                    / f"{kernel_id_str[4:]}.log",
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
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
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
    cors.add(app.router.add_route("GET", "/{session_name}/abusing-report", get_abusing_report))
    cors.add(app.router.add_route("GET", "/{session_name}/dependency-graph", get_dependency_graph))
    return app, []

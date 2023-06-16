from __future__ import annotations

import datetime as dt
import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, MutableMapping, Tuple

import aiohttp_cors
import attrs
import sqlalchemy as sa
import trafaret as t
from aiohttp import web

from ai.backend.common import redis_helper
from ai.backend.common import validators as tx
from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.events import AbstractEvent, EmptyEventArgs, EventHandler
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import AgentId, LogSeverity, RedisConnectionInfo

from ..defs import REDIS_LIVE_DB, LockID
from ..models import UserRole, error_logs, users
from ..models.domain import query_domain_user
from ..models.project import query_project_user_where_user_is_admin
from .auth import auth_required
from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, Iterable, WebMiddleware
from .utils import check_api_params, get_access_key_scopes

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class DoLogCleanupEvent(EmptyEventArgs, AbstractEvent):
    name = "do_log_cleanup"


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(
    t.Dict(
        {
            t.Key("severity"): tx.Enum(LogSeverity),
            t.Key("source"): t.String,
            t.Key("message"): t.String,
            t.Key("context_lang"): t.String,
            t.Key("context_env"): tx.JSONString,
            t.Key("request_url", default=None): t.Null | t.String,
            t.Key("request_status", default=None): t.Null | t.Int,
            t.Key("traceback", default=None): t.Null | t.String,
        },
    )
)
async def append(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    params["domain"] = request["user"]["domain_name"]
    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    requester_uuid = request["user"]["uuid"]
    log.info(
        "CREATE (ak:{0}/{1})",
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else "*",
    )

    async with root_ctx.db.begin() as conn:
        resp = {
            "success": True,
        }
        query = error_logs.insert().values(
            {
                "severity": params["severity"],
                "source": params["source"],
                "user": requester_uuid,
                "message": params["message"],
                "context_lang": params["context_lang"],
                "context_env": params["context_env"],
                "request_url": params["request_url"],
                "request_status": params["request_status"],
                "traceback": params["traceback"],
            }
        )
        result = await conn.execute(query)
        assert result.rowcount == 1
    return web.json_response(resp)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict(
        {
            t.Key("mark_read", default=False): t.ToBool(),
            t.Key("page_size", default=20): t.ToInt(lt=101),
            t.Key("page_no", default=1): t.ToInt(),
        }
    ),
)
async def list_logs(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    resp: MutableMapping[str, Any] = {"logs": []}
    domain_name = request["user"]["domain_name"]
    user_role = request["user"]["role"]
    user_uuid = request["user"]["uuid"]

    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    log.info(
        "LIST (ak:{0}/{1})",
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else "*",
    )
    is_admin = True
    select_from = error_logs
    condition = None
    if request["is_superadmin"]:
        pass
    elif user_role == UserRole.DOMAIN_ADMIN or user_role in ("domain-admin", "admin"):
        select_from = sa.join(error_logs, users, error_logs.c.user == users.c.uuid)
        condition = users.c.domain_name == domain_name
    else:
        # normal user or project admins
        projects_user_ids = await query_project_user_where_user_is_admin(root_ctx.db, user_uuid)
        if projects_user_ids:
            is_admin = True
            condition = error_logs.c.user.in_([*projects_user_ids, user_uuid])
        else:
            is_admin = False
            condition = (error_logs.c.user == user_uuid) & (~error_logs.c.is_cleared)
    select_query = (
        sa.select([error_logs])
        .select_from(select_from)
        .order_by(sa.desc(error_logs.c.created_at))
        .limit(params["page_size"])
    )
    if params["page_no"] > 1:
        select_query = select_query.offset((params["page_no"] - 1) * params["page_size"])
    count_query = sa.select([sa.func.count()]).select_from(select_from)
    if condition is not None:
        select_query = select_query.where(condition)
        count_query = count_query.where(condition)

    async with root_ctx.db.begin() as conn:
        result = await conn.execute(select_query)
        for row in result:
            result_item = {
                "log_id": str(row["id"]),
                "created_at": datetime.timestamp(row["created_at"]),
                "severity": row["severity"],
                "source": row["source"],
                "user": row["user"],
                "is_read": row["is_read"],
                "message": row["message"],
                "context_lang": row["context_lang"],
                "context_env": row["context_env"],
                "request_url": row["request_url"],
                "request_status": row["request_status"],
                "traceback": row["traceback"],
            }
            if result_item["user"] is not None:
                result_item["user"] = str(result_item["user"])
            if is_admin:
                result_item["is_cleared"] = row["is_cleared"]
            resp["logs"].append(result_item)
        resp["count"] = await conn.scalar(count_query)
        if params["mark_read"]:
            read_update_query = (
                sa.update(error_logs)
                .values(is_read=True)
                .where(error_logs.c.id.in_([x["log_id"] for x in resp["logs"]]))
            )
            await conn.execute(read_update_query)
        return web.json_response(resp, status=200)


@auth_required
@server_status_required(READ_ALLOWED)
async def mark_cleared(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    domain_name = request["user"]["domain_name"]
    user_role = request["user"]["role"]
    user_uuid = request["user"]["uuid"]
    log_id = uuid.UUID(request.match_info["log_id"])

    log.info("CLEAR")
    if request["is_superadmin"]:
        condition = error_logs.c.id == log_id
    elif user_role == UserRole.DOMAIN_ADMIN or user_role in ("domain-admin", "admin"):
        domain_user_ids = await query_domain_user(root_ctx.db, domain_name)
        condition = (error_logs.c.user.in_(domain_user_ids)) & (error_logs.c.id == log_id)
    else:
        # normal user or project admins
        projects_user_ids = await query_project_user_where_user_is_admin(root_ctx.db, user_uuid)
        condition = error_logs.c.user.in_([*projects_user_ids, user_uuid]) & (
            error_logs.c.id == log_id
        )
    update_query = sa.update(error_logs).values(is_cleared=True).where(condition)
    async with root_ctx.db.begin() as conn:
        result = await conn.execute(update_query)
        assert result.rowcount == 1

        return web.json_response({"success": True}, status=200)


async def log_cleanup_task(app: web.Application, src: AgentId, event: DoLogCleanupEvent) -> None:
    root_ctx: RootContext = app["_root.context"]
    etcd = root_ctx.shared_config.etcd
    raw_lifetime = await etcd.get("config/logs/error/retention")
    if raw_lifetime is None:
        raw_lifetime = "90d"
    try:
        lifetime = tx.TimeDuration().check(raw_lifetime)
    except ValueError:
        lifetime = dt.timedelta(days=90)
        log.warning(
            (
                "Failed to parse the error log retention period ({}) read from etcd; "
                "falling back to 90 days"
            ),
            raw_lifetime,
        )
    boundary = datetime.now() - lifetime
    async with root_ctx.db.begin() as conn:
        query = sa.delete(error_logs).where(error_logs.c.created_at < boundary)
        result = await conn.execute(query)
        if result.rowcount > 0:
            log.info("Cleaned up {} log(s) filed before {}", result.rowcount, boundary)


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    log_cleanup_timer: GlobalTimer
    log_cleanup_timer_redis: RedisConnectionInfo
    log_cleanup_timer_evh: EventHandler[web.Application, DoLogCleanupEvent]


async def init(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["logs.context"]
    app_ctx.log_cleanup_timer_evh = root_ctx.event_dispatcher.consume(
        DoLogCleanupEvent,
        app,
        log_cleanup_task,
    )
    app_ctx.log_cleanup_timer_redis = redis_helper.get_redis_object(
        root_ctx.shared_config.data["redis"],
        db=REDIS_LIVE_DB,
    )
    app_ctx.log_cleanup_timer = GlobalTimer(
        root_ctx.distributed_lock_factory(LockID.LOCKID_LOG_CLEANUP_TIMER, 20.0),
        root_ctx.event_producer,
        lambda: DoLogCleanupEvent(),
        20.0,
        initial_delay=17.0,
    )
    await app_ctx.log_cleanup_timer.join()


async def shutdown(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["logs.context"]
    await app_ctx.log_cleanup_timer.leave()
    root_ctx.event_dispatcher.unconsume(app_ctx.log_cleanup_timer_evh)
    await app_ctx.log_cleanup_timer_redis.close()


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["api_versions"] = (4, 5)
    app["prefix"] = "logs/error"
    app["logs.context"] = PrivateContext()
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("POST", "", append))
    cors.add(app.router.add_route("GET", "", list_logs))
    cors.add(app.router.add_route("POST", r"/{log_id}/clear", mark_cleared))

    return app, []

"""Backward-compatible shim for the session module.

All session handler logic has been migrated to:

* ``api.rest.session.handler`` — SessionHandler class
* ``api.rest.session`` — register_routes() + _make_lazy_handler()

This module keeps ``create_app()`` so that the existing ``server.py``
subapp-loading mechanism continues to work unmodified.  It also
re-exports a few names that are imported by other modules.
"""

from __future__ import annotations

import asyncio
import functools
import logging
from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

import aiohttp_cors
import aiotools
import attrs
import sqlalchemy as sa
import sqlalchemy.exc
import trafaret as t
from aiohttp import web
from aiotools import cancel_and_wait
from dateutil.tz import tzutc
from sqlalchemy.sql.expression import null, true

from ai.backend.common.events.event_types.agent.anycast import AgentTerminatedEvent
from ai.backend.common.plugin.monitor import GAUGE
from ai.backend.common.types import AccessKey, AgentId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.kernel import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    kernels,
)
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.session import SessionDependencyRow, SessionRow
from ai.backend.manager.utils import query_userinfo as _query_userinfo

from .auth import auth_required
from .manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware
from .utils import catch_unexpected, deprecated_stub, undefined

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


# ---------------------------------------------------------------------------
# Re-exported names used by other modules
# ---------------------------------------------------------------------------


class UndefChecker(t.Trafaret):
    """Kept for backward compatibility (imported by ``openapi.py``)."""

    def check_and_return(self, value: Any) -> object:
        if value == undefined:
            return value
        self._failure("Invalid Undef format", value=value)
        raise AssertionError("unreachable")  # _failure always raises


async def query_userinfo(
    request: web.Request,
    params: Any,
    conn: SAConnection,
) -> tuple[UUID, UUID, dict[str, Any]]:
    """Backward-compatible wrapper around utils.query_userinfo."""
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
        raise InvalidAPIParameters(str(e)) from e


# ---------------------------------------------------------------------------
# Dependency-graph helpers (imported by repositories/session)
# ---------------------------------------------------------------------------


from ai.backend.manager.errors.kernel import InvalidSessionData, SessionNotFound  # noqa: E402


@aiotools.lru_cache(maxsize=100)
async def _find_dependency_sessions(
    session_name_or_id: UUID | str,
    db_session: SASession,
    access_key: AccessKey,
) -> dict[str, list[Any] | str]:
    sessions = await SessionRow.match_sessions(
        db_session,
        session_name_or_id,
        access_key=access_key,
    )

    if len(sessions) < 1:
        raise SessionNotFound("session not found!")

    session_id = str(sessions[0].id)
    session_name = sessions[0].name

    if not isinstance(session_name, str):
        raise InvalidSessionData("Invalid session_name type")

    kernel_query = (
        sa.select(
            kernels.c.status,
            kernels.c.status_changed,
        )
        .select_from(kernels)
        .where(kernels.c.session_id == session_id)
    )

    dependency_result = await db_session.execute(
        sa.select(SessionDependencyRow.depends_on).where(
            SessionDependencyRow.session_id == session_id
        )
    )
    dependency_session_ids = [row[0] for row in dependency_result.fetchall()]

    kernel_query_result = (await db_session.execute(kernel_query)).first()
    if kernel_query_result is None:
        raise ValueError(f"Kernel not found for session {session_id}")

    session_info: dict[str, list[Any] | str] = {
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
) -> dict[str, list[Any] | str]:
    return await _find_dependency_sessions(session_name_or_id, db_session, access_key)


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


# ---------------------------------------------------------------------------
# Background tasks
# ---------------------------------------------------------------------------


@catch_unexpected(log)
async def check_agent_lost(root_ctx: RootContext, _interval: float) -> None:
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
async def report_stats(root_ctx: RootContext, _interval: float) -> None:
    try:
        stats_monitor = root_ctx.stats_monitor
        await stats_monitor.report_metric(
            GAUGE, "ai.backend.manager.coroutines", len(asyncio.all_tasks())
        )

        all_inst_ids = await root_ctx.registry.enumerate_instances()
        await stats_monitor.report_metric(
            GAUGE, "ai.backend.manager.agent_instances", len(all_inst_ids)
        )

        async with root_ctx.db.begin_readonly() as conn:
            query = (
                sa.select(sa.func.count())
                .select_from(kernels)
                .where(
                    (kernels.c.cluster_role == DEFAULT_ROLE)
                    & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
                )
            )
            n = await conn.scalar(query)
            await stats_monitor.report_metric(GAUGE, "ai.backend.manager.active_kernels", n)
            subquery = (
                sa.select(sa.func.count())
                .select_from(keypairs)
                .where(keypairs.c.is_active == true())
                .group_by(keypairs.c.user_id)
            )
            query = sa.select(sa.func.count()).select_from(subquery.alias())
            n = await conn.scalar(query)
            await stats_monitor.report_metric(GAUGE, "ai.backend.users.has_active_key", n)

            subquery = subquery.where(keypairs.c.last_used != null())
            query = sa.select(sa.func.count()).select_from(subquery.alias())
            n = await conn.scalar(query)
            await stats_monitor.report_metric(GAUGE, "ai.backend.users.has_used_key", n)
    except (sqlalchemy.exc.InterfaceError, ConnectionRefusedError):
        log.warning("report_stats(): error while connecting to PostgreSQL server")


# ---------------------------------------------------------------------------
# Sub-application lifecycle
# ---------------------------------------------------------------------------


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
    await cancel_and_wait(app_ctx.agent_lost_checker)
    await cancel_and_wait(app_ctx.stats_task)

    await app_ctx.webhook_ptask_group.shutdown()
    await app_ctx.database_ptask_group.shutdown()
    await app_ctx.rpc_ptask_group.shutdown()


# ---------------------------------------------------------------------------
# create_app() — backward-compatible shim
# ---------------------------------------------------------------------------


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

    # Lazy import to break circular dependency:
    # api/session.py → rest/session/ → handler.py → dto → services → repositories → api/session.py
    from .rest.session import _make_lazy_handler

    # Helper: compose middleware decorators around a lazy handler.
    def _h(method_name: str, *, status: Any = ALL_ALLOWED, auth: bool = True) -> Any:
        wrapped = _make_lazy_handler(method_name)
        if auth:
            wrapped = auth_required(wrapped)
        return server_status_required(status)(wrapped)

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)

    # --- Session creation ---
    cors.add(app.router.add_route("POST", "", _h("create_from_params")))
    cors.add(app.router.add_route("POST", "/_/create", _h("create_from_params")))
    cors.add(app.router.add_route("POST", "/_/create-from-template", _h("create_from_template")))
    cors.add(app.router.add_route("POST", "/_/create-cluster", _h("create_cluster")))

    # --- Session matching / utilities ---
    cors.add(app.router.add_route("GET", "/_/match", _h("match_sessions", status=READ_ALLOWED)))
    cors.add(app.router.add_route("POST", "/_/sync-agent-registry", _h("sync_agent_registry")))
    cors.add(
        app.router.add_route(
            "POST",
            "/_/transit-status",
            _h("check_and_transit_status"),
        )
    )

    # --- Per-session CRUD ---
    session_resource = cors.add(app.router.add_resource(r"/{session_name}"))
    cors.add(session_resource.add_route("GET", _h("get_info", status=READ_ALLOWED)))
    cors.add(session_resource.add_route("PATCH", _h("restart", status=READ_ALLOWED)))
    cors.add(session_resource.add_route("DELETE", _h("destroy", status=READ_ALLOWED)))
    cors.add(session_resource.add_route("POST", _h("execute", status=READ_ALLOWED)))

    # --- Task logs ---
    task_log_resource = cors.add(app.router.add_resource(r"/_/logs"))
    cors.add(task_log_resource.add_route("HEAD", _h("get_task_logs", status=READ_ALLOWED)))
    cors.add(task_log_resource.add_route("GET", _h("get_task_logs", status=READ_ALLOWED)))

    # --- Per-session sub-resources ---
    cors.add(
        app.router.add_route(
            "GET",
            "/{session_name}/direct-access-info",
            _h("get_direct_access_info", status=READ_ALLOWED),
        )
    )
    cors.add(
        app.router.add_route(
            "GET",
            "/{session_name}/logs",
            _h("get_container_logs", status=READ_ALLOWED),
        )
    )
    cors.add(app.router.add_route("POST", "/{session_name}/rename", _h("rename_session")))
    cors.add(
        app.router.add_route(
            "POST",
            "/{session_name}/interrupt",
            _h("interrupt", status=READ_ALLOWED),
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/{session_name}/complete",
            _h("complete", status=READ_ALLOWED),
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/{session_name}/shutdown-service",
            _h("shutdown_service", status=READ_ALLOWED),
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/{session_name}/upload",
            _h("upload_files", status=READ_ALLOWED),
        )
    )
    cors.add(
        app.router.add_route(
            "GET",
            "/{session_name}/download",
            deprecated_get_stub,
        )
    )
    cors.add(
        app.router.add_route(
            "GET",
            "/{session_name}/download_single",
            deprecated_get_stub,
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/{session_name}/download",
            _h("download_files", status=READ_ALLOWED),
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/{session_name}/download_single",
            _h("download_single", status=READ_ALLOWED),
        )
    )
    cors.add(
        app.router.add_route(
            "GET",
            "/{session_name}/files",
            _h("list_files", status=READ_ALLOWED),
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/{session_name}/start-service",
            _h("start_service", status=READ_ALLOWED),
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/{session_name}/commit",
            _h("commit_session"),
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/{session_name}/imagify",
            _h("convert_session_to_image"),
        )
    )
    cors.add(
        app.router.add_route(
            "GET",
            "/{session_name}/commit",
            _h("get_commit_status"),
        )
    )
    cors.add(
        app.router.add_route(
            "GET",
            "/{session_name}/status-history",
            _h("get_status_history", status=READ_ALLOWED),
        )
    )
    cors.add(
        app.router.add_route(
            "GET",
            "/{session_name}/abusing-report",
            _h("get_abusing_report"),
        )
    )
    cors.add(
        app.router.add_route(
            "GET",
            "/{session_name}/dependency-graph",
            _h("get_dependency_graph", status=READ_ALLOWED),
        )
    )

    return app, []

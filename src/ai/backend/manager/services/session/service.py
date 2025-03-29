import asyncio
import functools
import logging
from datetime import datetime, timedelta
from typing import Any, Mapping

import aiotools
import attrs
import sqlalchemy as sa
from dateutil.tz import tzutc
from redis.asyncio import Redis
from sqlalchemy.sql.expression import null, true

from ai.backend.common import redis_helper
from ai.backend.common.events import AgentTerminatedEvent, EventProducer
from ai.backend.common.exception import BackendError
from ai.backend.common.plugin.monitor import GAUGE, StatsPluginContext
from ai.backend.common.types import RedisConnectionInfo
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.api.utils import catch_unexpected
from ai.backend.manager.config import LocalConfig
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.models.kernel import AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES, kernels
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.session import KernelLoadingStrategy, SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.session.actions.commit_session import (
    CommitSessionAction,
    CommitSessionActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    agent_lost_checker: asyncio.Task[None]
    stats_task: asyncio.Task[None]
    database_ptask_group: aiotools.PersistentTaskGroup
    rpc_ptask_group: aiotools.PersistentTaskGroup
    webhook_ptask_group: aiotools.PersistentTaskGroup


@catch_unexpected(log)
async def check_agent_lost(
    local_config: LocalConfig,
    event_producer: EventProducer,
    redis_live: RedisConnectionInfo,
    interval: float,
) -> None:
    try:
        now = datetime.now(tzutc())
        timeout = timedelta(seconds=local_config["manager"]["heartbeat-timeout"])

        async def _check_impl(r: Redis):
            async for agent_id, prev in r.hscan_iter("agent.last_seen"):
                prev = datetime.fromtimestamp(float(prev), tzutc())
                if now - prev > timeout:
                    await event_producer.produce_event(
                        AgentTerminatedEvent("agent-lost"), source=agent_id.decode()
                    )

        await redis_helper.execute(redis_live, _check_impl)
    except asyncio.CancelledError:
        pass


@catch_unexpected(log)
async def report_stats(
    db: ExtendedAsyncSAEngine,
    stats_monitor: StatsPluginContext,
    registry: AgentRegistry,
    interval: float,
) -> None:
    try:
        stats_monitor = stats_monitor
        await stats_monitor.report_metric(
            GAUGE, "ai.backend.manager.coroutines", len(asyncio.all_tasks())
        )

        all_inst_ids = [inst_id async for inst_id in registry.enumerate_instances()]
        await stats_monitor.report_metric(
            GAUGE, "ai.backend.manager.agent_instances", len(all_inst_ids)
        )

        async with db.begin_readonly() as conn:
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
    except (sa.exc.InterfaceError, ConnectionRefusedError):
        log.warning("report_stats(): error while connecting to PostgreSQL server")


class SessionService:
    _db: ExtendedAsyncSAEngine
    _agent_registry: AgentRegistry
    _redis_live: RedisConnectionInfo
    _local_config: LocalConfig
    _stats_monitor: StatsPluginContext
    _app_ctx: PrivateContext
    _event_producer: EventProducer

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        agent_registry: AgentRegistry,
        redis_live: RedisConnectionInfo,
        local_config: LocalConfig,
        stats_monitor: StatsPluginContext,
        event_producer: EventProducer,
    ) -> None:
        self._db = db
        self._agent_registry = agent_registry
        self._redis_live = redis_live
        self._local_config = local_config
        self._stats_monitor = stats_monitor
        self._event_producer = event_producer
        self.init_app_ctx()

    def init_app_ctx(self) -> None:
        app_ctx: PrivateContext = PrivateContext()
        app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()
        app_ctx.rpc_ptask_group = aiotools.PersistentTaskGroup()
        app_ctx.webhook_ptask_group = aiotools.PersistentTaskGroup()

        # Scan ALIVE agents
        app_ctx.agent_lost_checker = aiotools.create_timer(
            functools.partial(
                check_agent_lost, self._local_config, self._event_producer, self._redis_live
            ),
            1.0,
        )
        app_ctx.agent_lost_checker.set_name("agent_lost_checker")
        app_ctx.stats_task = aiotools.create_timer(
            functools.partial(report_stats, self._db, self._stats_monitor, self._agent_registry),
            5.0,
        )
        app_ctx.stats_task.set_name("stats_task")
        self.app_ctx = app_ctx

    async def commit_session(self, action: CommitSessionAction) -> CommitSessionActionResult:
        session_name = action.session_name
        _requester_access_key, owner_access_key = (
            action.requester_access_key,
            action.owner_access_key,
        )
        filename = action.filename

        myself = asyncio.current_task()
        assert myself is not None

        try:
            async with self._db.begin_readonly_session() as db_sess:
                session = await SessionRow.get_session(
                    db_sess,
                    session_name,
                    owner_access_key,
                    kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                )

            resp: Mapping[str, Any] = await asyncio.shield(
                self._app_ctx.rpc_ptask_group.create_task(
                    self._agent_registry.commit_session_to_file(session, filename),
                ),
            )
        except BackendError:
            log.exception("COMMIT_SESSION: exception")
            raise

        return CommitSessionActionResult(
            session_row=session,
            commit_result=resp,
        )

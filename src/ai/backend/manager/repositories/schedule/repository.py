import itertools
import logging
import uuid
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import partial
from typing import TYPE_CHECKING, Optional, cast

import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import noload, selectinload
from sqlalchemy.sql.elements import ColumnElement

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ClusterMode,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.exceptions import ErrorStatusInfo
from ai.backend.manager.models import (
    PRIVATE_SESSION_TYPES,
    AgentRow,
    AgentStatus,
    DomainRow,
    EndpointRow,
    GroupRow,
    KernelRow,
    KernelStatistics,
    KernelStatus,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    RoutingRow,
    ScalingGroupOpts,
    ScalingGroupRow,
    SessionDependencyRow,
    SessionRow,
    SessionStatus,
    UserRow,
    recalc_agent_resource_occupancy,
)
from ai.backend.manager.models.endpoint import (
    EndpointAutoScalingRuleRow,
    EndpointLifecycle,
    EndpointStatistics,
)
from ai.backend.manager.models.kernel import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    USER_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    recalc_concurrency_used,
)
from ai.backend.manager.models.routing import RouteStatus
from ai.backend.manager.models.session import _build_session_fetch_query
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    sql_json_increment,
    sql_json_merge,
)
from ai.backend.manager.scheduler.types import (
    AgentAllocationContext,
    KernelAgentBinding,
    SchedulingContext,
)

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.types import SessionAllocation

from ai.backend.manager.sokovan.scheduler.selectors.selector import AgentInfo
from ai.backend.manager.sokovan.scheduler.types import (
    AllocationBatch,
    ConcurrencySnapshot,
    KernelWorkload,
    KeyPairResourcePolicy,
    PendingSessionInfo,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    ScalingGroupInfo,
    SchedulingConfig,
    SessionDependencyInfo,
    SessionDependencySnapshot,
    SessionWorkload,
    SystemSnapshot,
    UserResourcePolicy,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Layer-specific decorator for schedule repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.SCHEDULE)


@dataclass
class ConsolidatedSessionData:
    """Container for consolidated session data fetched in a single query."""

    # Session basic info
    session_id: SessionId
    access_key: AccessKey
    user_uuid: uuid.UUID
    group_id: Optional[uuid.UUID]
    domain_name: str
    status: SessionStatus
    requested_slots: ResourceSlot
    created_at: datetime

    # Policy info (optional as they come from outer joins)
    keypair_policy_name: Optional[str] = None
    keypair_total_slots: Optional[ResourceSlot] = None
    keypair_max_concurrent: Optional[int] = None
    keypair_max_sftp: Optional[int] = None
    keypair_max_pending_count: Optional[int] = None
    keypair_max_pending_slots: Optional[ResourceSlot] = None
    group_limit: Optional[ResourceSlot] = None
    domain_limit: Optional[ResourceSlot] = None


@dataclass
class PreFetchedRowMaps:
    """Container for pre-fetched database rows used during allocation."""

    agent_row_map: dict[AgentId, AgentRow]
    session_row_map: dict[SessionId, SessionRow]
    kernel_row_map: dict[uuid.UUID, KernelRow]


@dataclass
class SnapshotDatabaseData:
    """Container for all database data fetched for system snapshot."""

    total_capacity: ResourceSlot
    resource_occupancy: ResourceOccupancySnapshot
    consolidated_sessions: list[ConsolidatedSessionData]
    user_policies: dict[uuid.UUID, UserResourcePolicy]
    session_dependencies: SessionDependencySnapshot


@dataclass
class KernelAgentInfo:
    """Information about kernel agent assignment."""

    agent_id: AgentId
    agent_addr: str
    scaling_group: str


@dataclass
class PendingSessionData:
    """Data for a pending session fetched from database."""

    id: SessionId
    access_key: AccessKey
    requested_slots: ResourceSlot
    user_uuid: uuid.UUID
    group_id: uuid.UUID
    domain_name: str
    scaling_group_name: str
    priority: int
    session_type: SessionTypes
    cluster_mode: ClusterMode
    starts_at: Optional[datetime]
    is_private: bool
    kernels: list["KernelData"]  # Will be populated from JOIN


@dataclass
class KernelData:
    """Kernel data fetched from database."""

    id: uuid.UUID
    image: str
    architecture: str
    requested_slots: ResourceSlot
    agent: Optional[AgentId]


@dataclass
class AllSchedulingDatabaseData:
    """Container for ALL data fetched from database for scheduling."""

    scaling_group_row: ScalingGroupRow
    pending_sessions: list[PendingSessionData]
    agents: Optional[list[AgentRow]]
    snapshot_data: Optional[SnapshotDatabaseData]


@dataclass
class RawSchedulingData:
    """Raw data fetched from database for scheduling operations."""

    scaling_group_row: ScalingGroupRow
    pending_sessions: list[PendingSessionData]
    # Only populated if pending sessions exist:
    agents: Optional[list[AgentRow]] = None
    snapshot_data: Optional[SnapshotDatabaseData] = None
    max_container_count: Optional[int] = None


@dataclass
class SchedulingContextData:
    """Processed data ready for scheduling decisions."""

    scaling_group_info: ScalingGroupInfo
    pending_sessions: list[SessionWorkload]
    system_snapshot: SystemSnapshot
    scheduling_config: SchedulingConfig
    agents: list[AgentInfo]


class ScheduleRepository:
    _db: ExtendedAsyncSAEngine
    _valkey_stat: ValkeyStatClient
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        valkey_stat: ValkeyStatClient,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._db = db
        self._valkey_stat = valkey_stat
        self._config_provider = config_provider

    async def _get_kernel_count_per_agent_at_endpoint(
        self,
        session: SASession,
        endpoint_id: uuid.UUID,
        filter_by_statuses: Iterable[KernelStatus],
    ) -> dict[AgentId, int]:
        # Optimized loading for kernel counting - load routing with session and kernels
        routing_rows: list[RoutingRow] = (
            await session.scalars(
                sa.select(RoutingRow)
                .options(
                    selectinload(RoutingRow.session_row).options(selectinload(SessionRow.kernels))
                )
                .where(
                    RoutingRow.endpoint == endpoint_id,
                )
            )
        ).all()

        kernel_count_per_agent: dict[AgentId, int] = {}

        for routing_row in routing_rows:
            session_row: SessionRow = routing_row.session_row
            kernels: list[KernelRow] = session_row.kernels

            for kernel in kernels:
                if kernel.status in filter_by_statuses:
                    if agent_id := kernel.agent:
                        kernel_count_per_agent[agent_id] = (
                            kernel_count_per_agent.get(agent_id, 0) + 1
                        )

        return kernel_count_per_agent

    async def _list_managed_sessions(
        self,
        session: SASession,
        sgroup_name: str,
        pending_timeout: timedelta,
    ) -> tuple[list[SessionRow], list[SessionRow], list[SessionRow]]:
        managed_sessions = await SessionRow.get_sgroup_managed_sessions(session, sgroup_name)

        candidates: list[SessionRow] = []
        cancelleds: list[SessionRow] = []
        existings: list[SessionRow] = []

        now = datetime.now(tzutc())
        key_func = lambda s: (s.status.value, s.created_at)
        for status, sessions in itertools.groupby(
            sorted(managed_sessions, key=key_func),
            key=lambda s: s.status,
        ):
            if status != SessionStatus.PENDING:
                existings.extend(sessions)
                continue
            for sess in sessions:
                elapsed_pending_time = now - sess.created_at
                if pending_timeout.total_seconds() > 0 and elapsed_pending_time >= pending_timeout:
                    cancelleds.append(sess)
                else:
                    candidates.append(sess)

        return existings, candidates, cancelleds

    async def _reserve_agent(
        self,
        session: SASession,
        scaling_group: str,
        agent_id: Optional[AgentId],
        requested_slots: ResourceSlot,
        extra_conds: Optional[ColumnElement] = None,
    ) -> AgentAllocationContext:
        query = sa.select(AgentRow.occupied_slots).where(AgentRow.id == agent_id).with_for_update()
        if extra_conds is not None:
            query = query.where(extra_conds)
        current_occupied_slots = (await session.execute(query)).scalar()
        if current_occupied_slots is None:
            raise RuntimeError(f"No agent matching condition: {extra_conds}")
        update_query = (
            sa.update(AgentRow)
            .values(
                occupied_slots=(current_occupied_slots + requested_slots),
            )
            .where(AgentRow.id == agent_id)
        )
        await session.execute(update_query)
        query = sa.select(AgentRow.addr).where(AgentRow.id == agent_id)
        agent_addr = await session.scalar(query)
        assert agent_addr is not None
        return AgentAllocationContext(agent_id, agent_addr, scaling_group)

    async def _apply_cancellation(
        self,
        session: SASession,
        session_ids: list[SessionId],
        reason: str = "pending-timeout",
    ) -> None:
        now = datetime.now(tzutc())
        kernel_query = (
            sa.update(KernelRow)
            .values(
                status=KernelStatus.CANCELLED,
                status_info=reason,
                terminated_at=now,
                status_history=sql_json_merge(
                    KernelRow.status_history,
                    (),
                    {
                        KernelStatus.CANCELLED.name: now.isoformat(),
                    },
                ),
            )
            .where(KernelRow.session_id.in_(session_ids))
        )
        await session.execute(kernel_query)
        query = (
            sa.update(SessionRow)
            .values(
                status=SessionStatus.CANCELLED,
                status_info=reason,
                terminated_at=now,
                status_history=sql_json_merge(
                    SessionRow.status_history,
                    (),
                    {
                        SessionStatus.CANCELLED.name: now.isoformat(),
                    },
                ),
            )
            .where(SessionRow.id.in_(session_ids))
        )
        await session.execute(query)

    async def _rollback_predicate_mutations(
        self,
        session: SASession,
        sched_ctx: SchedulingContext,
        sess_row: SessionRow,
    ) -> None:
        await recalc_concurrency_used(session, sched_ctx.registry.valkey_stat, sess_row.access_key)

    @repository_decorator()
    async def get_schedulable_scaling_groups(self) -> list[str]:
        async with self._db.begin_readonly_session() as session:
            query = (
                sa.select(AgentRow.scaling_group)
                .where(AgentRow.status == AgentStatus.ALIVE)
                .group_by(AgentRow.scaling_group)
            )
            result = await session.execute(query)
            return [row.scaling_group for row in result.fetchall()]

    @repository_decorator()
    async def get_scaling_group_info(self, sgroup_name: str) -> tuple[str, ScalingGroupOpts]:
        async with self._db.begin_readonly_session() as session:
            result = await session.execute(
                sa.select(ScalingGroupRow.scheduler, ScalingGroupRow.scheduler_opts).where(
                    ScalingGroupRow.name == sgroup_name
                )
            )
            row = result.first()
            if row is None:
                raise ValueError(f'Scaling group "{sgroup_name}" not found!')
            return row.scheduler, row.scheduler_opts

    @repository_decorator()
    async def list_managed_sessions(
        self,
        sgroup_name: str,
        pending_timeout: timedelta,
    ) -> tuple[list[SessionRow], list[SessionRow], list[SessionRow]]:
        async with self._db.begin_readonly_session() as session:
            return await self._list_managed_sessions(session, sgroup_name, pending_timeout)

    @repository_decorator()
    async def get_endpoint_for_session(self, session_id: SessionId) -> Optional[uuid.UUID]:
        async with self._db.begin_readonly_session() as session:
            return await session.scalar(
                sa.select(RoutingRow.endpoint).where(RoutingRow.session == session_id)
            )

    @repository_decorator()
    async def get_kernel_count_per_agent_at_endpoint(
        self,
        endpoint_id: uuid.UUID,
        filter_by_statuses: Iterable[KernelStatus],
    ) -> dict[AgentId, int]:
        async with self._db.begin_readonly_session() as session:
            return await self._get_kernel_count_per_agent_at_endpoint(
                session, endpoint_id, filter_by_statuses
            )

    @repository_decorator()
    async def get_schedulable_agents_by_sgroup(self, sgroup_name: str) -> list[AgentRow]:
        async with self._db.begin_readonly_session() as session:
            from ai.backend.manager.models import list_schedulable_agents_by_sgroup

            result = await list_schedulable_agents_by_sgroup(session, sgroup_name)
            return list(result)

    @repository_decorator()
    async def get_schedulable_session_with_kernels_and_agents(
        self, session_id: SessionId
    ) -> Optional[SessionRow]:
        async with self._db.begin_readonly_session() as session:
            return await self._get_schedulable_session_with_kernels_and_agents(session, session_id)

    async def _get_schedulable_session_with_kernels_and_agents(
        self, session: SASession, session_id: SessionId
    ) -> Optional[SessionRow]:
        eager_loading_op = (selectinload(SessionRow.kernels),)
        return await SessionRow.get_session_by_id(
            session, session_id, eager_loading_op=eager_loading_op
        )

    @repository_decorator()
    async def apply_cancellation(
        self, session_ids: list[SessionId], reason: str = "pending-timeout"
    ) -> None:
        async with self._db.begin_session() as session:
            await self._apply_cancellation(session, session_ids, reason)

    @repository_decorator()
    async def update_session_predicate_failure(
        self,
        sched_ctx: SchedulingContext,
        pending_sess: SessionRow,
        status_update_data: dict,
    ) -> None:
        async with self._db.begin_session() as session:
            await self._rollback_predicate_mutations(session, sched_ctx, pending_sess)
            query = (
                sa.update(SessionRow)
                .values(
                    status_info="predicate-checks-failed",
                    status_data=sql_json_increment(
                        SessionRow.status_data,
                        ("scheduler", "retries"),
                        parent_updates=status_update_data,
                    ),
                )
                .where(SessionRow.id == pending_sess.id)
            )
            await session.execute(query)
            if pending_sess.is_private:
                await self._apply_cancellation(session, [pending_sess.id])

    @repository_decorator()
    async def update_session_status_data(
        self,
        pending_sess: SessionRow,
        status_update_data: dict,
    ) -> None:
        async with self._db.begin_session() as session:
            kernel_query = (
                sa.update(KernelRow)
                .where(KernelRow.session_id == pending_sess.id)
                .values(
                    status_data=sql_json_merge(
                        KernelRow.status_data,
                        ("scheduler",),
                        obj=status_update_data,
                    ),
                )
            )
            await session.execute(kernel_query)
            session_query = (
                sa.update(SessionRow)
                .where(SessionRow.id == pending_sess.id)
                .values(
                    status_data=sql_json_merge(
                        SessionRow.status_data,
                        ("scheduler",),
                        obj=status_update_data,
                    ),
                )
            )
            await session.execute(session_query)

    @repository_decorator()
    async def get_agent_available_slots(
        self, agent_id: AgentId
    ) -> tuple[ResourceSlot, ResourceSlot]:
        async with self._db.begin_readonly_session() as session:
            result = (
                await session.execute(
                    sa.select([AgentRow.available_slots, AgentRow.occupied_slots]).where(
                        AgentRow.id == agent_id
                    )
                )
            ).fetchall()[0]
            if result is None:
                raise RuntimeError(f"No such agent exist in DB: {agent_id}")
            return result

    @repository_decorator()
    async def reserve_agent(
        self,
        scaling_group: str,
        agent_id: Optional[AgentId],
        requested_slots: ResourceSlot,
        extra_conds: Optional[ColumnElement] = None,
    ) -> AgentAllocationContext:
        async with self._db.begin_session() as session:
            return await self._reserve_agent(
                session, scaling_group, agent_id, requested_slots, extra_conds
            )

    @repository_decorator()
    async def update_kernel_status_with_error(
        self,
        kernel_id: str,
        status_info: str,
        status_data: ErrorStatusInfo,
    ) -> None:
        async with self._db.begin_session() as session:
            query = (
                sa.update(KernelRow)
                .values(
                    status_info=status_info,
                    status_data=status_data,
                )
                .where(KernelRow.id == kernel_id)
            )
            await session.execute(query)

    @repository_decorator()
    async def finalize_multi_node_session(
        self,
        session_id: SessionId,
        sgroup_name: str,
        kernel_agent_bindings: list[KernelAgentBinding],
    ) -> None:
        kernel_agent_id_addr = {
            binding.kernel.id: (
                binding.agent_alloc_ctx.agent_id,
                binding.agent_alloc_ctx.agent_addr,
            )
            for binding in kernel_agent_bindings
        }
        agent_ids: list[AgentId] = []
        now = datetime.now(tzutc())
        async with self._db.begin_session() as db_session:
            stmt = (
                sa.select(SessionRow)
                .where(SessionRow.id == session_id)
                .options(selectinload(SessionRow.kernels))
            )

            session_row = await db_session.scalar(stmt)
            session_row = cast(SessionRow, session_row)
            for kernel_row in session_row.kernels:
                kernel_row = cast(KernelRow, kernel_row)
                kernel_row.set_status(
                    KernelStatus.SCHEDULED,
                    status_info="scheduled",
                    status_data={},
                    status_changed_at=now,
                )
                kernel_row.scaling_group = sgroup_name
                bind_agent_id, bind_agent_addr = kernel_agent_id_addr[kernel_row.id]
                if bind_agent_id is not None:
                    agent_ids.append(bind_agent_id)
                    kernel_row.agent = bind_agent_id
                    kernel_row.agent_addr = bind_agent_addr
            session_row.set_status(
                SessionStatus.SCHEDULED,
                status_info="scheduled",
                status_data={},
                status_changed_at=now,
            )
            session_row.scaling_group_name = sgroup_name
            session_row.agent_ids = agent_ids

    async def _update_session_scheduling_failure(
        self,
        sched_ctx: SchedulingContext,
        sess_ctx: SessionRow,
        error_msg: Optional[str],
    ) -> None:
        async with self._db.begin_session() as session:
            await self._rollback_predicate_mutations(session, sched_ctx, sess_ctx)
            query = (
                sa.update(SessionRow)
                .values(
                    status_info="no-available-instances",
                    status_data=sql_json_increment(
                        SessionRow.status_data,
                        ("scheduler", "retries"),
                        parent_updates={
                            "last_try": datetime.now(tzutc()).isoformat(),
                            "msg": error_msg or "",
                        },
                    ),
                )
                .where(SessionRow.id == sess_ctx.id)
            )
            await session.execute(query)

    async def _update_session_generic_failure(
        self,
        sched_ctx: SchedulingContext,
        sess_ctx: SessionRow,
        exc_data: ErrorStatusInfo,
    ) -> None:
        async with self._db.begin_session() as session:
            await self._rollback_predicate_mutations(session, sched_ctx, sess_ctx)
            query = (
                sa.update(SessionRow)
                .values(
                    status_info="scheduler-error",
                    status_data=exc_data,
                )
                .where(SessionRow.id == sess_ctx.id)
            )
            await session.execute(query)

    @repository_decorator()
    async def finalize_single_node_session(
        self,
        session_id: SessionId,
        sgroup_name: str,
        agent_alloc_ctx: AgentAllocationContext,
    ) -> None:
        agent_ids: list[AgentId] = []
        now = datetime.now(tzutc())
        async with self._db.begin_session() as db_session:
            stmt = (
                sa.select(SessionRow)
                .where(SessionRow.id == session_id)
                .options(selectinload(SessionRow.kernels))
            )

            session_row = await db_session.scalar(stmt)
            session_row = cast(SessionRow, session_row)
            if session_row is None:
                raise RuntimeError(f"Session {session_id} not found")

            for kernel in session_row.kernels:
                kernel.set_status(
                    KernelStatus.SCHEDULED,
                    status_info="scheduled",
                    status_data={},
                    status_changed_at=now,
                )
                kernel.agent = agent_alloc_ctx.agent_id
                kernel.agent_addr = agent_alloc_ctx.agent_addr
                kernel.scaling_group = sgroup_name
            session_row.set_status(
                SessionStatus.SCHEDULED,
                status_info="scheduled",
                status_data={},
                status_changed_at=now,
            )
            if agent_alloc_ctx.agent_id is not None:
                agent_ids.append(agent_alloc_ctx.agent_id)
            session_row.scaling_group_name = sgroup_name
            session_row.agent_ids = agent_ids

    @repository_decorator()
    async def update_kernel_scheduling_failure(
        self,
        sched_ctx: SchedulingContext,
        sess_ctx: SessionRow,
        kernel_id: str,
        error_msg: Optional[str],
    ) -> None:
        async with self._db.begin_session() as session:
            await self._rollback_predicate_mutations(session, sched_ctx, sess_ctx)
            query = (
                sa.update(KernelRow)
                .values(
                    status_info="no-available-instances",
                    status_data=sql_json_increment(
                        KernelRow.status_data,
                        ("scheduler", "retries"),
                        parent_updates={
                            "last_try": datetime.now(tzutc()).isoformat(),
                            "msg": error_msg or "",
                        },
                    ),
                )
                .where(KernelRow.id == kernel_id)
            )
            await session.execute(query)

    @repository_decorator()
    async def update_multinode_kernel_generic_failure(
        self,
        sched_ctx: SchedulingContext,
        sess_ctx: SessionRow,
        kernel_id: str,
        exc_data: ErrorStatusInfo,
    ) -> None:
        await self.update_session_predicate_failure(sched_ctx, sess_ctx, {})
        await self.update_kernel_status_with_error(kernel_id, "scheduler-error", exc_data)

    async def _mark_session_cancelled(
        self,
        sched_ctx: SchedulingContext,
        session: SessionRow,
        status_data: ErrorStatusInfo,
    ) -> None:
        async with self._db.begin_session() as db_session:
            affected_agents = set(k.agent for k in session.kernels)
            await self._rollback_predicate_mutations(db_session, sched_ctx, session)
            now = datetime.now(tzutc())
            update_query = (
                sa.update(KernelRow)
                .values(
                    status=KernelStatus.CANCELLED,
                    status_changed=now,
                    status_info="failed-to-start",
                    status_data=status_data,
                    terminated_at=now,
                    status_history=sql_json_merge(
                        KernelRow.status_history,
                        (),
                        {
                            KernelStatus.CANCELLED.name: now.isoformat(),
                        },
                    ),
                )
                .where(KernelRow.session_id == session.id)
            )
            await db_session.execute(update_query)
            update_sess_query = (
                sa.update(SessionRow)
                .values(
                    status=SessionStatus.CANCELLED,
                    status_info="failed-to-start",
                    status_data=status_data,
                    terminated_at=now,
                    status_history=sql_json_merge(
                        SessionRow.status_history,
                        (),
                        {
                            SessionStatus.CANCELLED.name: now.isoformat(),
                        },
                    ),
                )
                .where(SessionRow.id == session.id)
            )
            await db_session.execute(update_sess_query)
            for agent_id in affected_agents:
                await recalc_agent_resource_occupancy(db_session, agent_id)

    @repository_decorator()
    async def transit_scheduled_to_preparing(self) -> list[SessionRow]:
        async with self._db.begin_session() as session:
            return await self._transit_scheduled_to_preparing(session)

    async def _transit_scheduled_to_preparing(self, session: SASession) -> list[SessionRow]:
        now = datetime.now(timezone.utc)
        scheduled_sessions = await SessionRow.get_sessions_by_status(
            session, SessionStatus.SCHEDULED, load_kernel_image=True
        )
        for row in scheduled_sessions:
            for kernel_row in row.kernels:
                _kernel_row = cast(KernelRow, kernel_row)
                _kernel_row.set_status(KernelStatus.PREPARING, status_changed_at=now)
            row.set_status(SessionStatus.PREPARING, status_changed_at=now)
        return scheduled_sessions

    @repository_decorator()
    async def mark_sessions_and_kernels_creating(self) -> list[SessionRow]:
        async with self._db.begin_session() as session:
            now = datetime.now(timezone.utc)
            session_rows = await SessionRow.get_sessions_by_status(session, SessionStatus.PREPARED)
            for row in session_rows:
                for kernel_row in row.kernels:
                    _kernel_row = cast(KernelRow, kernel_row)
                    _kernel_row.set_status(KernelStatus.CREATING, status_changed_at=now)
                row.set_status(SessionStatus.CREATING, status_changed_at=now)
            return session_rows

    @repository_decorator()
    async def clean_zombie_routes(self) -> int:
        async with self._db.begin_session() as session:
            query = (
                sa.select(RoutingRow)
                .join(
                    RoutingRow.session_row.and_(
                        SessionRow.status.in_((SessionStatus.TERMINATED, SessionStatus.CANCELLED))
                    )
                )
                .where(RoutingRow.status.in_((RouteStatus.PROVISIONING, RouteStatus.TERMINATING)))
                .options(selectinload(RoutingRow.session_row))
            )
            result = await session.execute(query)
            zombie_routes = result.scalars().all()
            if len(zombie_routes) > 0:
                query = sa.delete(RoutingRow).where(
                    RoutingRow.id.in_([r.id for r in zombie_routes])
                )
                result = await session.execute(query)
                return result.rowcount
            return 0

    @repository_decorator()
    async def create_routing_rows(self, endpoint_create_data: list[tuple]) -> list[uuid.UUID]:
        async with self._db.begin_session() as session:
            created_routes = []
            for endpoint, expand_count in endpoint_create_data:
                for _ in range(expand_count):
                    route_id = uuid.uuid4()
                    routing_row = RoutingRow(
                        route_id,
                        endpoint.id,
                        None,
                        endpoint.session_owner,
                        endpoint.domain,
                        endpoint.project,
                    )
                    session.add(routing_row)
                    created_routes.append(route_id)
            await session.commit()
            return created_routes

    @repository_decorator()
    async def destroy_terminated_endpoints_and_routes(
        self, endpoints_to_mark_terminated: set, already_destroyed_sessions: list[SessionId]
    ) -> None:
        async with self._db.begin_session() as session:
            query = (
                sa.update(EndpointRow)
                .values({
                    "destroyed_at": sa.func.now(),
                    "lifecycle_stage": EndpointLifecycle.DESTROYED,
                })
                .where(EndpointRow.id.in_([e.id for e in endpoints_to_mark_terminated]))
            )
            await session.execute(query)
            query = sa.delete(RoutingRow).where(RoutingRow.session.in_(already_destroyed_sessions))
            await session.execute(query)

    @repository_decorator()
    async def get_container_info_for_destroyed_kernels(self, session_id: SessionId) -> dict:
        async with self._db.begin_readonly_session() as session:
            query = sa.select(KernelRow.id, KernelRow.container_id).where(
                KernelRow.session_id == session_id
            )
            rows = (await session.execute(query)).fetchall()
            return {row["id"]: row["container_id"] for row in rows}

    @repository_decorator()
    async def autoscale_endpoints(self) -> None:
        async with self._db.begin_session(commit_on_end=True) as session:
            await self._autoscale_endpoints(session)

    async def _autoscale_endpoints(self, session: SASession) -> None:
        current_datetime = datetime.now(timezone.utc)
        rules = await EndpointAutoScalingRuleRow.list(session)

        # Currently auto scaling supports two types of stat as source: kernel and endpoint
        # To fetch aggregated kernel metrics among every kernels managed by a single endpoint
        # we first need to collect every routings, and then the sessions tied to each routing,
        # and finally the child kernels of each session
        endpoints = await EndpointRow.batch_load(
            session, [rule.endpoint for rule in rules], load_routes=True
        )
        endpoint_by_id = {endpoint.id: endpoint for endpoint in endpoints}
        metric_requested_sessions: list[SessionId] = []
        metric_requested_kernels: list[KernelId] = []
        metric_requested_endpoints: list[uuid.UUID] = []

        kernel_statistics_by_id: dict[KernelId, Mapping[str, object]] = {}
        endpoint_statistics_by_id: dict[uuid.UUID, Mapping[str, object]] = {}
        kernels_by_session_id: dict[SessionId, list[KernelRow]] = defaultdict(lambda: [])

        for rule in rules:
            match rule.metric_source:
                case AutoScalingMetricSource.KERNEL:
                    metric_requested_sessions += [
                        route.session for route in endpoint_by_id[rule.endpoint].routings
                    ]
                case AutoScalingMetricSource.INFERENCE_FRAMEWORK:
                    metric_requested_endpoints.append(rule.endpoint)

        kernel_rows = await KernelRow.batch_load_by_session_id(
            session, list(metric_requested_sessions)
        )
        for kernel in kernel_rows:
            kernels_by_session_id[kernel.session_id].append(kernel)
            metric_requested_kernels.append(kernel.id)

        # To speed up and lower the pressure to the redis we must load every metrics
        # in bulk, not querying each key at once
        kernel_live_stats = await KernelStatistics.batch_load_by_kernel_impl(
            self._valkey_stat,
            cast(list[SessionId], list(metric_requested_kernels)),
        )
        endpoint_live_stats = await EndpointStatistics.batch_load_by_endpoint_impl(
            self._valkey_stat,
            cast(list[SessionId], list(metric_requested_endpoints)),
        )

        kernel_statistics_by_id = {
            kernel_id: metric
            for kernel_id, metric in zip(metric_requested_kernels, kernel_live_stats)
            if metric is not None
        }
        endpoint_statistics_by_id = {
            endpoint_id: metric
            for endpoint_id, metric in zip(metric_requested_endpoints, endpoint_live_stats)
            if metric is not None
        }

        log_skip_due_to_missing_metric = partial(
            log.warning,
            "AUTOSCALE(e:{0.endpoint}, rule:{0.id}): skipping the rule because metric {0.metric_name} does not exist",
        )

        for rule in rules:
            should_trigger = False
            match rule.metric_source:
                # Kernel metrics should be evaluated by the average of the metric across every kernels
                case AutoScalingMetricSource.KERNEL:
                    metric_aggregated_value = Decimal("0")
                    metric_found_kernel_count = 0
                    for route in endpoint_by_id[rule.endpoint].routings:
                        for kernel in kernels_by_session_id[route.session]:
                            if not kernel_statistics_by_id.get(kernel.id):
                                continue
                            live_stat = kernel_statistics_by_id[kernel.id]
                            if rule.metric_name not in live_stat:
                                continue
                            metric_found_kernel_count += 1
                            metric_value = cast(dict, live_stat[rule.metric_name])
                            metric_aggregated_value += Decimal(metric_value["pct"])
                    if metric_found_kernel_count == 0:
                        log_skip_due_to_missing_metric(rule)
                        continue
                    current_value = metric_aggregated_value / Decimal(metric_found_kernel_count)
                case AutoScalingMetricSource.INFERENCE_FRAMEWORK:
                    if not endpoint_statistics_by_id[rule.endpoint]:
                        log_skip_due_to_missing_metric(rule)
                        continue
                    live_stat = endpoint_statistics_by_id[rule.endpoint]
                    if rule.metric_name not in live_stat:
                        log_skip_due_to_missing_metric(rule)
                        continue
                    metric_value = cast(dict, live_stat[rule.metric_name])
                    current_value = Decimal(metric_value["current"]) / len(
                        endpoint_by_id[rule.endpoint].routings
                    )
                case _:
                    raise NotImplementedError

            match rule.comparator:
                case AutoScalingMetricComparator.LESS_THAN:
                    should_trigger = current_value < rule.threshold
                case AutoScalingMetricComparator.LESS_THAN_OR_EQUAL:
                    should_trigger = current_value <= rule.threshold
                case AutoScalingMetricComparator.GREATER_THAN:
                    should_trigger = current_value > rule.threshold
                case AutoScalingMetricComparator.GREATER_THAN_OR_EQUAL:
                    should_trigger = current_value >= rule.threshold

            log.debug(
                "AUTOSCALE(e:{}, rule:{}): {} {} {}: {}",
                rule.endpoint,
                rule.id,
                current_value,
                rule.comparator,
                rule.threshold,
                should_trigger,
            )
            if should_trigger:
                new_replica_count = max(0, rule.endpoint_row.replicas + rule.step_size)
                if (rule.min_replicas is not None and new_replica_count < rule.min_replicas) or (
                    rule.max_replicas is not None and new_replica_count > rule.max_replicas
                ):
                    log.info(
                        "AUTOSCALE(e:{}, rule:{}): ignored the new replica count {} ({}) [min: {}, max: {}]",
                        rule.endpoint,
                        rule.id,
                        new_replica_count,
                        rule.step_size,
                        rule.min_replicas,
                        rule.max_replicas,
                    )
                    continue
                if rule.last_triggered_at is None or rule.last_triggered_at < (
                    current_datetime - timedelta(seconds=rule.cooldown_seconds)
                ):
                    # Changes applied here will be reflected at consequent queries (at `scale_services()`)
                    # so we do not have to propagate the changes on the function level
                    rule.endpoint_row.replicas = new_replica_count
                    rule.last_triggered_at = current_datetime
                    log.info(
                        "AUTOSCALE(e:{}, rule:{}): applied the new replica count {} ({})",
                        rule.endpoint,
                        rule.id,
                        new_replica_count,
                        rule.step_size,
                    )
                else:
                    log.info(
                        "AUTOSCALE(e:{}, rule:{}): ignored the new replica count {} ({}) as the rule is on a cooldown period until {}",
                        rule.endpoint,
                        rule.id,
                        new_replica_count,
                        rule.step_size,
                        rule.last_triggered_at + timedelta(seconds=rule.cooldown_seconds),
                    )

    @repository_decorator()
    async def get_endpoints_for_scaling(self) -> list:
        async with self._db.begin_readonly_session() as session:
            endpoints = await EndpointRow.list(
                session,
                load_image=True,
                load_routes=True,
                status_filter=[EndpointLifecycle.CREATED, EndpointLifecycle.DESTROYING],
            )
            return endpoints

    @repository_decorator()
    async def get_sessions_to_destroy_for_scaling(
        self, route_sessions: list[SessionId]
    ) -> list[SessionRow]:
        async with self._db.begin_readonly_session() as session:
            return await self._get_sessions_to_destroy_for_scaling(session, route_sessions)

    async def _get_sessions_to_destroy_for_scaling(
        self, session: SASession, route_sessions: list[SessionId]
    ) -> list[SessionRow]:
        # Optimized loading for session destruction - load kernels with agent info
        kernel_loading_op = (
            noload("*"),
            selectinload(SessionRow.kernels).options(
                noload("*"),
                selectinload(KernelRow.agent_row).noload("*"),
            ),
        )
        query = _build_session_fetch_query(
            SessionRow.id.in_(route_sessions), eager_loading_op=kernel_loading_op
        )
        result = await session.execute(query)
        return result.scalars().all()

    @repository_decorator()
    async def delete_appproxy_endpoints_readonly(
        self, endpoints_to_mark_terminated: set, registry
    ) -> None:
        async with self._db.begin_readonly_session() as session:
            await self._delete_appproxy_endpoints_readonly(
                session, endpoints_to_mark_terminated, registry
            )

    async def _delete_appproxy_endpoints_readonly(
        self, session: SASession, endpoints_to_mark_terminated: set, registry
    ) -> None:
        for endpoint in endpoints_to_mark_terminated:
            try:
                await registry.delete_appproxy_endpoint(session, endpoint)
            except Exception as e:
                log.warning("failed to communicate with AppProxy endpoint: {}", str(e))

    @repository_decorator()
    async def allocate_sessions(self, allocation_batch: AllocationBatch) -> None:
        """
        Allocate resources for multiple sessions.
        Uses a single database session for all allocations.
        Pre-fetches all agent, session, and kernel data for efficient processing.
        If a session allocation fails, the error is logged but processing continues.
        Note: Failed allocations remain uncommitted while successful ones are committed.
        """
        async with self._db.begin_session() as db_session:
            # Pre-fetch all necessary data
            row_maps = await self._create_prefetched_row_maps(db_session, allocation_batch)

            for allocation in allocation_batch.allocations:
                try:
                    await self._allocate_single_session(db_session, row_maps, allocation)
                except Exception as e:
                    log.error(
                        "Failed to allocate session {}: {}",
                        allocation.session_id,
                        str(e),
                        exc_info=True,
                    )
                    # Continue with next session allocation

    async def _prefetch_agent_rows(
        self, db_session: SASession, agent_ids: set[AgentId]
    ) -> dict[AgentId, AgentRow]:
        """
        Pre-fetch all agent rows for the given agent IDs.
        Returns a dictionary mapping agent_id to AgentRow.
        """
        if not agent_ids:
            return {}

        query = sa.select(AgentRow).where(AgentRow.id.in_(agent_ids))
        result = await db_session.execute(query)
        agents = result.scalars().all()

        return {agent.id: agent for agent in agents}

    async def _prefetch_session_rows(
        self, db_session: SASession, session_ids: set[SessionId]
    ) -> dict[SessionId, SessionRow]:
        """
        Pre-fetch all session rows for the given session IDs.
        Returns a dictionary mapping session_id to SessionRow.
        """
        if not session_ids:
            return {}

        query = sa.select(SessionRow).where(SessionRow.id.in_(session_ids))
        result = await db_session.execute(query)
        sessions = result.scalars().all()

        return {session.id: session for session in sessions}

    async def _prefetch_kernel_rows(
        self, db_session: SASession, kernel_ids: set[uuid.UUID]
    ) -> dict[uuid.UUID, KernelRow]:
        """
        Pre-fetch all kernel rows for the given kernel IDs.
        Returns a dictionary mapping kernel_id to KernelRow.
        """
        if not kernel_ids:
            return {}

        query = sa.select(KernelRow).where(KernelRow.id.in_(kernel_ids))
        result = await db_session.execute(query)
        kernels = result.scalars().all()

        return {kernel.id: kernel for kernel in kernels}

    async def _create_prefetched_row_maps(
        self, db_session: SASession, allocation_batch: AllocationBatch
    ) -> PreFetchedRowMaps:
        """
        Create PreFetchedRowMaps by collecting and pre-fetching all necessary data.
        """
        # Collect all session and kernel IDs
        session_ids: set[SessionId] = set()
        kernel_ids: set[uuid.UUID] = set()

        for allocation in allocation_batch.allocations:
            session_ids.add(allocation.session_id)
            for kernel_alloc in allocation.kernel_allocations:
                kernel_ids.add(kernel_alloc.kernel_id)

        # Pre-fetch all data in bulk
        agent_row_map = await self._prefetch_agent_rows(db_session, allocation_batch.agent_ids)
        session_row_map = await self._prefetch_session_rows(db_session, session_ids)
        kernel_row_map = await self._prefetch_kernel_rows(db_session, kernel_ids)

        return PreFetchedRowMaps(
            agent_row_map=agent_row_map,
            session_row_map=session_row_map,
            kernel_row_map=kernel_row_map,
        )

    async def _get_agent_row(
        self, db_session: SASession, agent_row_map: dict[AgentId, AgentRow], agent_id: AgentId
    ) -> AgentRow:
        """
        Get agent row from pre-fetched map or fetch from database if not found.
        """
        if agent_id in agent_row_map:
            return agent_row_map[agent_id]

        # Fallback: fetch from database if not in pre-fetched data
        query = sa.select(AgentRow).where(AgentRow.id == agent_id)
        result = await db_session.execute(query)
        agent_row = result.scalar_one_or_none()

        if agent_row is None:
            raise RuntimeError(f"Agent {agent_id} not found")

        # Cache it for future use
        agent_row_map[agent_id] = agent_row
        return agent_row

    async def _get_session_row(
        self,
        db_session: SASession,
        session_row_map: dict[SessionId, SessionRow],
        session_id: SessionId,
    ) -> SessionRow:
        """
        Get session row from pre-fetched map or fetch from database if not found.
        """
        if session_id in session_row_map:
            return session_row_map[session_id]

        # Fallback: fetch from database if not in pre-fetched data
        query = sa.select(SessionRow).where(SessionRow.id == session_id)
        result = await db_session.execute(query)
        session_row = result.scalar_one_or_none()

        if session_row is None:
            raise RuntimeError(f"Session {session_id} not found")

        # Cache it for future use
        session_row_map[session_id] = session_row
        return session_row

    async def _get_kernel_row(
        self,
        db_session: SASession,
        kernel_row_map: dict[uuid.UUID, KernelRow],
        kernel_id: uuid.UUID,
    ) -> KernelRow:
        """
        Get kernel row from pre-fetched map or fetch from database if not found.
        """
        if kernel_id in kernel_row_map:
            return kernel_row_map[kernel_id]

        # Fallback: fetch from database if not in pre-fetched data
        query = sa.select(KernelRow).where(KernelRow.id == kernel_id)
        result = await db_session.execute(query)
        kernel_row = result.scalar_one_or_none()

        if kernel_row is None:
            raise RuntimeError(f"Kernel {kernel_id} not found")

        # Cache it for future use
        kernel_row_map[kernel_id] = kernel_row
        return kernel_row

    async def _allocate_single_session(
        self,
        db_session: SASession,
        row_maps: PreFetchedRowMaps,
        allocation: "SessionAllocation",
    ) -> None:
        """
        Allocate resources for a single session.
        Raises exception if any agent resource allocation fails.
        """
        # 1. Validate that all agents can accommodate the requested resources
        await self._validate_agent_resources(db_session, row_maps.agent_row_map, allocation)

        # 2. Reserve resources on agents
        await self._reserve_agent_resources(db_session, row_maps.agent_row_map, allocation)

        # 3. Update kernel information with agent assignments
        await self._update_kernels_with_agents(db_session, row_maps.kernel_row_map, allocation)

        # 4. Update session information
        await self._update_session_status(db_session, row_maps.session_row_map, allocation)

    async def _validate_agent_resources(
        self,
        db_session: SASession,
        agent_row_map: dict[AgentId, AgentRow],
        allocation: "SessionAllocation",
    ) -> None:
        """
        Validate that all agents have sufficient resources for the allocation.
        Raises RuntimeError if any agent cannot accommodate the requested resources.
        """
        # Group allocations by agent to check resources efficiently
        agent_resource_map: dict[AgentId, ResourceSlot] = {}

        for agent_alloc in allocation.agent_allocations:
            agent_id = agent_alloc.agent_id
            for slot in agent_alloc.allocated_slots:
                if agent_id not in agent_resource_map:
                    agent_resource_map[agent_id] = ResourceSlot()
                agent_resource_map[agent_id] += slot

        # Check each agent's available resources using pre-fetched data
        for agent_id, requested_slots in agent_resource_map.items():
            agent_row = await self._get_agent_row(db_session, agent_row_map, agent_id)
            available_slots = agent_row.available_slots
            occupied_slots = agent_row.occupied_slots

            # Check if agent has enough resources
            for key, requested_amount in requested_slots.items():
                available_amount = available_slots.get(key, Decimal("0"))
                occupied_amount = occupied_slots.get(key, Decimal("0"))
                remaining = available_amount - occupied_amount

                if remaining < requested_amount:
                    raise RuntimeError(
                        f"Agent {agent_id} has insufficient resources for {key}: "
                        f"requested={requested_amount}, remaining={remaining}"
                    )

    async def _reserve_agent_resources(
        self,
        db_session: SASession,
        agent_row_map: dict[AgentId, AgentRow],
        allocation: "SessionAllocation",
    ) -> None:
        """
        Reserve resources on agents by updating their occupied_slots.
        """
        # Group allocations by agent for efficient updates
        agent_updates: dict[AgentId, ResourceSlot] = {}

        for agent_alloc in allocation.agent_allocations:
            agent_id = agent_alloc.agent_id
            for slot in agent_alloc.allocated_slots:
                if agent_id not in agent_updates:
                    agent_updates[agent_id] = ResourceSlot()
                agent_updates[agent_id] += slot

        # Update each agent's occupied slots
        for agent_id, additional_slots in agent_updates.items():
            # Get agent row from pre-fetched data or database
            agent_row = await self._get_agent_row(db_session, agent_row_map, agent_id)
            current_occupied = agent_row.occupied_slots

            # Update with new occupied slots
            new_occupied = current_occupied + additional_slots
            update_query = (
                sa.update(AgentRow)
                .values(occupied_slots=new_occupied)
                .where(AgentRow.id == agent_id)
            )
            await db_session.execute(update_query)

    async def _update_kernels_with_agents(
        self,
        db_session: SASession,
        kernel_row_map: dict[uuid.UUID, KernelRow],
        allocation: "SessionAllocation",
    ) -> None:
        """
        Update kernel information with their agent assignments.
        """
        now = datetime.now(tzutc())

        # Create a mapping of kernel_id to agent info
        kernel_agent_map: dict[uuid.UUID, KernelAgentInfo] = {}

        for kernel_alloc in allocation.kernel_allocations:
            kernel_agent_map[kernel_alloc.kernel_id] = KernelAgentInfo(
                agent_id=kernel_alloc.agent_id,
                agent_addr=kernel_alloc.agent_addr,
                scaling_group=kernel_alloc.scaling_group,
            )

        # Update all kernels using pre-fetched data
        for kernel_id, agent_info in kernel_agent_map.items():
            kernel = await self._get_kernel_row(db_session, kernel_row_map, kernel_id)

            kernel.set_status(
                KernelStatus.SCHEDULED,
                status_info="scheduled",
                status_data={},
                status_changed_at=now,
            )
            kernel.agent = agent_info.agent_id
            kernel.agent_addr = agent_info.agent_addr
            kernel.scaling_group = agent_info.scaling_group

    async def _update_session_status(
        self,
        db_session: SASession,
        session_row_map: dict[SessionId, SessionRow],
        allocation: "SessionAllocation",
    ) -> None:
        """
        Update session status and metadata.
        """
        now = datetime.now(tzutc())

        # Collect unique agent IDs from kernel allocations
        agent_ids = list({
            kernel_alloc.agent_id
            for kernel_alloc in allocation.kernel_allocations
            if kernel_alloc.agent_id is not None
        })

        # Get session from pre-fetched data
        session_row = await self._get_session_row(
            db_session, session_row_map, allocation.session_id
        )

        session_row.set_status(
            SessionStatus.SCHEDULED,
            status_info="scheduled",
            status_data={},
            status_changed_at=now,
        )
        session_row.scaling_group_name = allocation.scaling_group
        session_row.agent_ids = agent_ids

    async def _get_schedulable_agents(
        self, db_sess: SASession, scaling_group: str
    ) -> list[AgentRow]:
        """Get schedulable agents in the scaling group."""
        query = sa.select(AgentRow).where(
            (AgentRow.status == AgentStatus.ALIVE)
            & (AgentRow.scaling_group == scaling_group)
            & (AgentRow.schedulable == sa.true())
        )
        result = await db_sess.execute(query)
        return list(result.scalars().all())

    async def _get_total_capacity(self, candidate_agents: list[AgentRow]) -> ResourceSlot:
        """Get total capacity from candidate agents."""
        return sum((ag.available_slots for ag in candidate_agents), ResourceSlot())

    def _extract_resource_policies(
        self,
        data: list[ConsolidatedSessionData],
        status_filter: list[SessionStatus],
    ) -> tuple[
        dict[AccessKey, KeyPairResourcePolicy],
        dict[uuid.UUID, UserResourcePolicy],
        dict[uuid.UUID, ResourceSlot],
        dict[str, ResourceSlot],
        set[uuid.UUID],
    ]:
        """Extract resource policies from consolidated data."""
        keypair_policies: dict[AccessKey, KeyPairResourcePolicy] = {}
        group_limits: dict[uuid.UUID, ResourceSlot] = {}
        domain_limits: dict[str, ResourceSlot] = {}
        user_uuids: set[uuid.UUID] = set()

        for item in data:
            if item.status not in status_filter:
                continue

            # Collect keypair policies
            if (
                item.access_key not in keypair_policies
                and item.keypair_policy_name
                and item.keypair_total_slots is not None
                and item.keypair_max_concurrent is not None
                and item.keypair_max_sftp is not None
            ):
                keypair_policies[item.access_key] = KeyPairResourcePolicy(
                    name=item.keypair_policy_name,
                    total_resource_slots=item.keypair_total_slots,
                    max_concurrent_sessions=item.keypair_max_concurrent,
                    max_concurrent_sftp_sessions=item.keypair_max_sftp,
                    max_pending_session_count=item.keypair_max_pending_count,
                    max_pending_session_resource_slots=item.keypair_max_pending_slots,
                )

            # Collect user UUIDs for later fetch
            user_uuids.add(item.user_uuid)

            # Collect group limits
            if item.group_id and item.group_limit is not None:
                group_limits[item.group_id] = item.group_limit

            # Collect domain limits
            if item.domain_name and item.domain_limit is not None:
                domain_limits[item.domain_name] = item.domain_limit

        # Note: user_policies still need separate query due to different join path
        return keypair_policies, {}, group_limits, domain_limits, user_uuids

    def _extract_pending_sessions(
        self,
        data: list[ConsolidatedSessionData],
    ) -> PendingSessionSnapshot:
        """Extract pending sessions from consolidated data."""
        pending_by_keypair: dict[AccessKey, list[PendingSessionInfo]] = defaultdict(list)

        for item in data:
            if item.status == SessionStatus.PENDING:
                pending_by_keypair[item.access_key].append(
                    PendingSessionInfo(
                        session_id=item.session_id,
                        requested_slots=item.requested_slots,
                        creation_time=item.created_at,
                    )
                )

        return PendingSessionSnapshot(by_keypair=dict(pending_by_keypair))

    @repository_decorator()
    async def get_agents(self, scaling_group: str) -> Sequence[AgentInfo]:
        """Get all schedulable agents in the specified scaling group."""
        async with self._db.begin_readonly_session() as db_sess:
            # Get schedulable agents for the scaling group
            agent_rows = await self._get_schedulable_agents(db_sess, scaling_group)

            # Get container counts for each agent
            agent_ids = [agent.id for agent in agent_rows]
            container_counts = {}
            if agent_ids:
                query = (
                    sa.select(KernelRow.agent, sa.func.count(KernelRow.id))
                    .where(
                        KernelRow.agent.in_(agent_ids),
                        KernelRow.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES),
                    )
                    .group_by(KernelRow.agent)
                )
                result = await db_sess.execute(query)
                container_counts = dict(result.fetchall())

            # Convert AgentRow objects to AgentInfo objects
            agents_info: list[AgentInfo] = []
            for agent in agent_rows:
                agents_info.append(
                    AgentInfo(
                        agent_id=agent.id,
                        agent_addr=agent.addr,
                        architecture=agent.architecture,
                        available_slots=agent.available_slots,
                        occupied_slots=agent.occupied_slots,
                        scaling_group=agent.scaling_group,
                        container_count=container_counts.get(agent.id, 0),
                    )
                )

            return agents_info

    @repository_decorator()
    async def get_scheduling_config(self, scaling_group: str) -> SchedulingConfig:
        """Get scheduling configuration for a scaling group."""
        # Get scaling group options
        _, sgroup_opts = await self.get_scaling_group_info(scaling_group)

        # Get max container count from etcd
        max_container_count: Optional[int] = None
        raw_value = await self._config_provider.legacy_etcd_config_loader.get_raw(
            "config/agent/max-container-count"
        )
        if raw_value is not None:
            max_container_count = int(raw_value)

        return SchedulingConfig(
            max_container_count_per_agent=max_container_count,
            enforce_spreading_endpoint_replica=sgroup_opts.enforce_spreading_endpoint_replica,
        )

    @repository_decorator()
    async def get_system_snapshot(self, scaling_group: str) -> SystemSnapshot:
        """Get complete system snapshot for the specified scaling group.

        Optimized version with:
        - Single consolidated query for all session data
        - Batched Redis operations for concurrency data
        - Efficient streaming and aggregation for resource occupancy
        - In-memory data transformation
        - All DB reads consolidated in single private method
        """
        async with self._db.begin_readonly_session() as db_sess:
            # Fetch ALL data from database in one method
            db_data = await self._fetch_all_snapshot_data_from_db(db_sess, scaling_group)

            # Process consolidated data in memory

            # Extract resource policies (filtering for active sessions)
            keypair_policies, _, group_limits, domain_limits, _ = self._extract_resource_policies(
                db_data.consolidated_sessions,
                [
                    SessionStatus.PENDING,
                    SessionStatus.SCHEDULED,
                    SessionStatus.PREPARING,
                    SessionStatus.RUNNING,
                ],
            )

            # Combine all resource policies
            resource_policy = ResourcePolicySnapshot(
                keypair_policies=keypair_policies,
                user_policies=db_data.user_policies,
                group_limits=group_limits,
                domain_limits=domain_limits,
            )

            # Extract pending sessions
            pending_sessions = self._extract_pending_sessions(db_data.consolidated_sessions)

            # Get concurrency from Redis (not DB - already optimized with batch operations)
            access_keys = set(d.access_key for d in db_data.consolidated_sessions)
            concurrency = await self._get_concurrency_snapshot(access_keys)

            return SystemSnapshot(
                total_capacity=db_data.total_capacity,
                resource_occupancy=db_data.resource_occupancy,
                resource_policy=resource_policy,
                concurrency=concurrency,
                pending_sessions=pending_sessions,
                session_dependencies=db_data.session_dependencies,
            )

    async def _fetch_all_snapshot_data_from_db(
        self, db_sess: SASession, scaling_group: str
    ) -> SnapshotDatabaseData:
        """
        Fetch ALL data from database in a single method.
        This consolidates all DB read operations for get_system_snapshot.

        Returns:
            SnapshotDatabaseData containing all fetched data
        """
        # 1. Get agent data and calculate total capacity
        agents = await self._get_schedulable_agents(db_sess, scaling_group)
        total_capacity = await self._get_total_capacity(agents)

        # 2. Get resource occupancy
        resource_occupancy = await self._get_resource_occupancy_snapshot(db_sess, scaling_group)

        # 3. Fetch consolidated session data
        consolidated_sessions = await self._fetch_consolidated_session_data(db_sess, scaling_group)
        session_ids = [d.session_id for d in consolidated_sessions]

        # 4. Extract user UUIDs for user policy fetch
        user_uuids = set(
            d.user_uuid
            for d in consolidated_sessions
            if d.status
            in [
                SessionStatus.PENDING,
                SessionStatus.SCHEDULED,
                SessionStatus.PREPARING,
                SessionStatus.RUNNING,
            ]
        )

        # 5. Fetch user policies
        user_policies: dict[uuid.UUID, UserResourcePolicy] = {}
        if user_uuids:
            user_policy_query = (
                sa.select(
                    UserRow.uuid,
                    KeyPairResourcePolicyRow.name,
                    KeyPairResourcePolicyRow.total_resource_slots,
                )
                .select_from(UserRow)
                .join(KeyPairRow, UserRow.main_access_key == KeyPairRow.access_key)
                .join(
                    KeyPairResourcePolicyRow,
                    KeyPairRow.resource_policy == KeyPairResourcePolicyRow.name,
                )
                .where(UserRow.uuid.in_(user_uuids))
            )

            async for row in await db_sess.stream(user_policy_query):
                user_policies[row.uuid] = UserResourcePolicy(
                    name=row.name,
                    total_resource_slots=row.total_resource_slots,
                )

        # 6. Fetch session dependencies
        dependencies_map = await self._fetch_session_dependencies_optimized(db_sess, session_ids)
        session_dependencies = SessionDependencySnapshot(by_session=dependencies_map)

        return SnapshotDatabaseData(
            total_capacity=total_capacity,
            resource_occupancy=resource_occupancy,
            consolidated_sessions=consolidated_sessions,
            user_policies=user_policies,
            session_dependencies=session_dependencies,
        )

    @repository_decorator()
    async def _fetch_consolidated_session_data(
        self, db_sess: SASession, scaling_group: str
    ) -> list[ConsolidatedSessionData]:
        """
        Fetch all session-related data in a single query.
        This consolidates what was previously done in:
        - _get_resource_policy_snapshot
        - _get_pending_session_snapshot
        - _get_session_dependency_snapshot (partial)
        """
        comprehensive_query = (
            sa.select(
                # Session basic info
                SessionRow.id,
                SessionRow.access_key,
                SessionRow.user_uuid,
                SessionRow.group_id,
                SessionRow.domain_name,
                SessionRow.status,
                SessionRow.requested_slots,
                SessionRow.created_at,
                # Keypair policy columns
                KeyPairResourcePolicyRow.name.label("kp_policy_name"),
                KeyPairResourcePolicyRow.total_resource_slots.label("kp_total_slots"),
                KeyPairResourcePolicyRow.max_concurrent_sessions.label("kp_max_concurrent"),
                KeyPairResourcePolicyRow.max_concurrent_sftp_sessions.label("kp_max_sftp"),
                KeyPairResourcePolicyRow.max_pending_session_count.label("kp_max_pending"),
                KeyPairResourcePolicyRow.max_pending_session_resource_slots.label(
                    "kp_max_pending_slots"
                ),
                # Group and domain limits
                GroupRow.total_resource_slots.label("group_limit"),
                DomainRow.total_resource_slots.label("domain_limit"),
            )
            .select_from(SessionRow)
            .outerjoin(KeyPairRow, SessionRow.access_key == KeyPairRow.access_key)
            .outerjoin(
                KeyPairResourcePolicyRow,
                KeyPairRow.resource_policy == KeyPairResourcePolicyRow.name,
            )
            .outerjoin(GroupRow, SessionRow.group_id == GroupRow.id)
            .outerjoin(DomainRow, SessionRow.domain_name == DomainRow.name)
            .where(SessionRow.scaling_group_name == scaling_group)
            # Include all statuses - filter in memory for different uses
        )

        result = []
        async for row in await db_sess.stream(comprehensive_query):
            result.append(
                ConsolidatedSessionData(
                    session_id=row.id,
                    access_key=row.access_key,
                    user_uuid=row.user_uuid,
                    group_id=row.group_id,
                    domain_name=row.domain_name,
                    status=row.status,
                    requested_slots=row.requested_slots,
                    created_at=row.created_at,
                    keypair_policy_name=row.kp_policy_name,
                    keypair_total_slots=row.kp_total_slots,
                    keypair_max_concurrent=row.kp_max_concurrent,
                    keypair_max_sftp=row.kp_max_sftp,
                    keypair_max_pending_count=row.kp_max_pending,
                    keypair_max_pending_slots=row.kp_max_pending_slots,
                    group_limit=row.group_limit,
                    domain_limit=row.domain_limit,
                )
            )
        return result

    async def _fetch_session_dependencies_optimized(
        self, db_sess: SASession, session_ids: list[SessionId]
    ) -> dict[SessionId, list[SessionDependencyInfo]]:
        """
        Fetch all session dependencies in a single query.
        Eliminates the N+1 pattern from the original implementation.
        """
        if not session_ids:
            return {}

        dependency_query = (
            sa.select(
                SessionDependencyRow.session_id,
                SessionDependencyRow.depends_on,
                SessionRow.name,
                SessionRow.status,
                SessionRow.result,
            )
            .select_from(SessionDependencyRow)
            .join(SessionRow, SessionDependencyRow.depends_on == SessionRow.id)
            .where(SessionDependencyRow.session_id.in_(session_ids))
        )

        dependencies_by_session: dict[SessionId, list[SessionDependencyInfo]] = defaultdict(list)
        async for row in await db_sess.stream(dependency_query):
            dependencies_by_session[row.session_id].append(
                SessionDependencyInfo(
                    depends_on=row.depends_on,
                    dependency_name=row.name,
                    dependency_status=row.status,
                    dependency_result=row.result,
                )
            )

        return dict(dependencies_by_session)

    async def _get_resource_occupancy_snapshot(
        self, db_sess: SASession, scaling_group: str
    ) -> ResourceOccupancySnapshot:
        """Get resource occupancy snapshot by collecting kernel occupancy data in the scaling group.

        Optimized version that fetches all data in a single query and uses
        defaultdict for more efficient aggregation.
        """
        kernel_query = sa.select(
            KernelRow.access_key,
            KernelRow.user_uuid,
            KernelRow.group_id,
            KernelRow.domain_name,
            KernelRow.occupied_slots,
        ).where(
            (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
            & (KernelRow.session_type.not_in(PRIVATE_SESSION_TYPES))
            & (KernelRow.scaling_group == scaling_group)
        )

        # Use defaultdict for more efficient accumulation
        occupancy_by_keypair: dict[AccessKey, ResourceSlot] = defaultdict(ResourceSlot)
        occupancy_by_user: dict[uuid.UUID, ResourceSlot] = defaultdict(ResourceSlot)
        occupancy_by_group: dict[uuid.UUID, ResourceSlot] = defaultdict(ResourceSlot)
        occupancy_by_domain: dict[str, ResourceSlot] = defaultdict(ResourceSlot)

        # Stream results for memory efficiency with large datasets
        async for row in await db_sess.stream(kernel_query):
            # Single pass accumulation - no need to check for key existence
            occupancy_by_keypair[row.access_key] += row.occupied_slots
            occupancy_by_user[row.user_uuid] += row.occupied_slots
            occupancy_by_group[row.group_id] += row.occupied_slots
            occupancy_by_domain[row.domain_name] += row.occupied_slots

        return ResourceOccupancySnapshot(
            by_keypair=dict(occupancy_by_keypair),
            by_user=dict(occupancy_by_user),
            by_group=dict(occupancy_by_group),
            by_domain=dict(occupancy_by_domain),
        )

    async def _get_concurrency_snapshot(self, access_keys: set[AccessKey]) -> ConcurrencySnapshot:
        """Get concurrency snapshot from Valkey/Redis with batched operations."""
        if not access_keys:
            return ConcurrencySnapshot(
                sessions_by_keypair={},
                sftp_sessions_by_keypair={},
            )

        # Prepare all keys for batch retrieval
        access_key_list = list(access_keys)
        regular_keys = [f"keypair.concurrency_used.{ak}" for ak in access_key_list]
        sftp_keys = [f"keypair.sftp_concurrency_used.{ak}" for ak in access_key_list]
        all_keys = regular_keys + sftp_keys

        # Batch get all values in a single operation
        results = await self._valkey_stat._get_multiple_keys(all_keys)

        # Process results
        sessions_by_keypair: dict[AccessKey, int] = {}
        sftp_sessions_by_keypair: dict[AccessKey, int] = {}

        for i, ak in enumerate(access_key_list):
            # Regular concurrency
            regular_result = results[i] if i < len(results) else None
            sessions_by_keypair[ak] = int(regular_result.decode()) if regular_result else 0

            # SFTP concurrency
            sftp_idx = len(access_key_list) + i
            sftp_result = results[sftp_idx] if sftp_idx < len(results) else None
            sftp_sessions_by_keypair[ak] = int(sftp_result.decode()) if sftp_result else 0

        return ConcurrencySnapshot(
            sessions_by_keypair=sessions_by_keypair,
            sftp_sessions_by_keypair=sftp_sessions_by_keypair,
        )

    async def _fetch_raw_scheduling_data(
        self, db_sess: SASession, scaling_group: str
    ) -> Optional[RawSchedulingData]:
        """
        Fetch all raw data needed for scheduling.
        ALL database queries happen in _fetch_all_scheduling_database_data.
        """
        all_data = await self._fetch_all_scheduling_database_data(db_sess, scaling_group)
        if all_data is None:
            return None
        if not all_data.pending_sessions:
            return RawSchedulingData(
                scaling_group_row=all_data.scaling_group_row, pending_sessions=[]
            )

        return RawSchedulingData(
            scaling_group_row=all_data.scaling_group_row,
            pending_sessions=all_data.pending_sessions,
            agents=all_data.agents,
            snapshot_data=all_data.snapshot_data,
            max_container_count=None,  # Will be set from etcd later
        )

    @repository_decorator()
    async def _fetch_all_scheduling_database_data(
        self, db_sess: SASession, scaling_group: str
    ) -> Optional[AllSchedulingDatabaseData]:
        """
        Execute ALL database queries in a single method.
        This is the ONLY method that should execute database queries for scheduling.
        """
        # 1. Get scaling group info
        sg_result = await db_sess.execute(
            sa.select(ScalingGroupRow).where(ScalingGroupRow.name == scaling_group)
        )
        scaling_group_row = sg_result.scalar_one_or_none()
        if not scaling_group_row:
            return None

        # 2. Get pending sessions with kernels using single JOIN query
        pending_sessions = await self._fetch_pending_sessions_join(
            db_sess, scaling_group, scaling_group_row.scheduler_opts.pending_timeout
        )

        # Early exit if no pending sessions
        if not pending_sessions:
            return AllSchedulingDatabaseData(
                scaling_group_row=scaling_group_row,
                pending_sessions=[],
                agents=None,
                snapshot_data=None,
            )

        # 3. Get agents
        agents_result = await db_sess.execute(
            sa.select(AgentRow).where(
                (AgentRow.status == AgentStatus.ALIVE)
                & (AgentRow.scaling_group == scaling_group)
                & (AgentRow.schedulable == sa.true())
            )
        )
        agents = list(agents_result.scalars().all())

        # 4. Get snapshot data (this will contain multiple queries but all in this method)
        total_capacity = sum((ag.available_slots for ag in agents), ResourceSlot())

        # Get resource occupancy
        occupancy_result = await db_sess.execute(
            sa.select(
                KernelRow.access_key,
                KernelRow.user_uuid,
                KernelRow.group_id,
                KernelRow.domain_name,
                KernelRow.occupied_slots,
            ).where(
                (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                & (KernelRow.session_type.not_in(PRIVATE_SESSION_TYPES))
                & (KernelRow.scaling_group == scaling_group)
            )
        )

        # Process occupancy data
        occupancy_by_keypair: dict[AccessKey, ResourceSlot] = defaultdict(ResourceSlot)
        occupancy_by_user: dict[uuid.UUID, ResourceSlot] = defaultdict(ResourceSlot)
        occupancy_by_group: dict[uuid.UUID, ResourceSlot] = defaultdict(ResourceSlot)
        occupancy_by_domain: dict[str, ResourceSlot] = defaultdict(ResourceSlot)

        for row in occupancy_result:
            occupancy_by_keypair[row.access_key] += row.occupied_slots
            occupancy_by_user[row.user_uuid] += row.occupied_slots
            occupancy_by_group[row.group_id] += row.occupied_slots
            occupancy_by_domain[row.domain_name] += row.occupied_slots

        resource_occupancy = ResourceOccupancySnapshot(
            by_keypair=dict(occupancy_by_keypair),
            by_user=dict(occupancy_by_user),
            by_group=dict(occupancy_by_group),
            by_domain=dict(occupancy_by_domain),
        )

        # Get consolidated session data for policies
        consolidated_sessions = await self._fetch_consolidated_session_data(db_sess, scaling_group)

        # Get user policies
        user_uuids = {s.user_uuid for s in pending_sessions}
        user_policies: dict[uuid.UUID, UserResourcePolicy] = {}
        if user_uuids:
            user_policy_result = await db_sess.execute(
                sa.select(
                    UserRow.uuid,
                    KeyPairResourcePolicyRow.name,
                    KeyPairResourcePolicyRow.total_resource_slots,
                )
                .select_from(UserRow)
                .join(KeyPairRow, UserRow.main_access_key == KeyPairRow.access_key)
                .join(
                    KeyPairResourcePolicyRow,
                    KeyPairRow.resource_policy == KeyPairResourcePolicyRow.name,
                )
                .where(UserRow.uuid.in_(user_uuids))
            )
            for row in user_policy_result:
                user_policies[row.uuid] = UserResourcePolicy(
                    name=row.name,
                    total_resource_slots=row.total_resource_slots,
                )

        # Get session dependencies
        session_ids = [s.id for s in pending_sessions]
        dependencies_map = await self._fetch_session_dependencies_optimized(db_sess, session_ids)

        snapshot_data = SnapshotDatabaseData(
            total_capacity=total_capacity,
            resource_occupancy=resource_occupancy,
            consolidated_sessions=consolidated_sessions,
            user_policies=user_policies,
            session_dependencies=SessionDependencySnapshot(by_session=dependencies_map),
        )

        return AllSchedulingDatabaseData(
            scaling_group_row=scaling_group_row,
            pending_sessions=pending_sessions,
            agents=agents,
            snapshot_data=snapshot_data,
        )

    @repository_decorator()
    async def _fetch_pending_sessions_join(
        self, db_sess: SASession, scaling_group: str, pending_timeout: timedelta
    ) -> list[PendingSessionData]:
        """
        Fetch pending sessions with kernels using single JOIN query.
        Returns strongly-typed PendingSessionData objects.
        """
        now = datetime.now(tzutc())

        # Single JOIN query for sessions and kernels
        query = (
            sa.select(
                # Session columns
                SessionRow.id,
                SessionRow.access_key,
                SessionRow.requested_slots,
                SessionRow.user_uuid,
                SessionRow.group_id,
                SessionRow.domain_name,
                SessionRow.scaling_group_name,
                SessionRow.priority,
                SessionRow.session_type,
                SessionRow.cluster_mode,
                SessionRow.starts_at,
                # Kernel columns
                KernelRow.id.label("kernel_id"),
                KernelRow.image.label("kernel_image"),
                KernelRow.architecture.label("kernel_arch"),
                KernelRow.requested_slots.label("kernel_slots"),
                KernelRow.agent.label("kernel_agent"),
            )
            .select_from(SessionRow)
            .outerjoin(KernelRow, SessionRow.id == KernelRow.session_id)
            .where(
                (SessionRow.scaling_group_name == scaling_group)
                & (SessionRow.status == SessionStatus.PENDING)
            )
        )

        # Apply timeout filter
        if pending_timeout.total_seconds() > 0:
            timeout_cutoff = now - pending_timeout
            query = query.where(SessionRow.created_at >= timeout_cutoff)

        result = await db_sess.execute(query)

        # Process results into strongly-typed objects
        sessions_map: dict[SessionId, PendingSessionData] = {}

        for row in result:
            session_id = row.id

            # Create or get session
            if session_id not in sessions_map:
                sessions_map[session_id] = PendingSessionData(
                    id=session_id,
                    access_key=row.access_key,
                    requested_slots=row.requested_slots,
                    user_uuid=row.user_uuid,
                    group_id=row.group_id,
                    domain_name=row.domain_name,
                    scaling_group_name=row.scaling_group_name,
                    priority=row.priority,
                    session_type=row.session_type,
                    cluster_mode=row.cluster_mode,
                    starts_at=row.starts_at,
                    is_private=row.session_type in PRIVATE_SESSION_TYPES,
                    kernels=[],
                )

            # Add kernel if present
            if row.kernel_id:
                kernel = KernelData(
                    id=row.kernel_id,
                    image=row.kernel_image,
                    architecture=row.kernel_arch,
                    requested_slots=row.kernel_slots,
                    agent=row.kernel_agent,
                )
                sessions_map[session_id].kernels.append(kernel)

        return list(sessions_map.values())

    def _transform_to_scheduling_context(
        self, raw_data: RawSchedulingData
    ) -> SchedulingContextData:
        """
        Transform raw DB data to domain objects.
        No DB connection needed - pure in-memory transformation.
        """
        # 1. Transform scaling group info
        scaling_group_info = self._create_scaling_group_info(raw_data.scaling_group_row)

        # 2. Transform pending sessions to workloads
        pending_workloads = self._transform_sessions_to_workloads(raw_data.pending_sessions)

        # 3. Transform agents to AgentInfo
        agent_infos = self._transform_agents_to_info(raw_data.agents)

        # 4. Build scheduling config
        scheduling_config = self._create_scheduling_config(
            raw_data.scaling_group_row, raw_data.max_container_count
        )

        # 5. Transform system snapshot
        system_snapshot = self._create_system_snapshot(raw_data.snapshot_data)

        return SchedulingContextData(
            scaling_group_info=scaling_group_info,
            pending_sessions=pending_workloads,
            system_snapshot=system_snapshot,
            scheduling_config=scheduling_config,
            agents=agent_infos,
        )

    def _create_scaling_group_info(self, scaling_group_row: ScalingGroupRow) -> ScalingGroupInfo:
        """Create ScalingGroupInfo from database row."""
        return ScalingGroupInfo(
            scheduler_name=scaling_group_row.scheduler,
            agent_selection_strategy=scaling_group_row.scheduler_opts.agent_selection_strategy,
            pending_timeout=scaling_group_row.scheduler_opts.pending_timeout,
        )

    def _transform_sessions_to_workloads(
        self, sessions: list[PendingSessionData]
    ) -> list[SessionWorkload]:
        """Transform pending session data to workload objects."""
        workloads: list[SessionWorkload] = []
        for session in sessions:
            # Create kernel workloads
            kernel_workloads = [
                KernelWorkload(
                    kernel_id=kernel.id,
                    image=kernel.image,
                    architecture=kernel.architecture,
                    requested_slots=kernel.requested_slots,
                )
                for kernel in session.kernels
            ]

            # Create session workload
            workload = SessionWorkload(
                session_id=session.id,
                access_key=session.access_key,
                requested_slots=session.requested_slots,
                user_uuid=session.user_uuid,
                group_id=session.group_id,
                domain_name=session.domain_name,
                scaling_group=session.scaling_group_name,
                priority=session.priority,
                session_type=session.session_type,
                cluster_mode=session.cluster_mode,
                starts_at=session.starts_at,
                is_private=session.is_private,
                kernels=kernel_workloads,
                designated_agent=session.kernels[0].agent if session.kernels else None,
            )
            workloads.append(workload)
        return workloads

    def _transform_agents_to_info(self, agents: Optional[list[AgentRow]]) -> list[AgentInfo]:
        """Transform agent rows to AgentInfo objects."""
        agent_infos: list[AgentInfo] = []
        if agents:
            for agent in agents:
                agent_info = AgentInfo(
                    agent_id=agent.id,
                    agent_addr=agent.addr,
                    architecture=agent.architecture,
                    available_slots=agent.available_slots,
                    occupied_slots=agent.occupied_slots,
                    scaling_group=agent.scaling_group,
                    container_count=0,  # Will be calculated during scheduling
                )
                agent_infos.append(agent_info)
        return agent_infos

    def _create_scheduling_config(
        self, scaling_group_row: ScalingGroupRow, max_container_count: Optional[int]
    ) -> SchedulingConfig:
        """Create scheduling configuration."""
        return SchedulingConfig(
            max_container_count_per_agent=max_container_count,
            enforce_spreading_endpoint_replica=scaling_group_row.scheduler_opts.enforce_spreading_endpoint_replica,
        )

    def _create_system_snapshot(
        self, snapshot_data: Optional[SnapshotDatabaseData]
    ) -> SystemSnapshot:
        """Create system snapshot from raw snapshot data."""
        if snapshot_data:
            # Extract resource policies
            keypair_policies, _, group_limits, domain_limits, _ = self._extract_resource_policies(
                snapshot_data.consolidated_sessions,
                [
                    SessionStatus.PENDING,
                    SessionStatus.SCHEDULED,
                    SessionStatus.PREPARING,
                    SessionStatus.RUNNING,
                ],
            )

            resource_policy = ResourcePolicySnapshot(
                keypair_policies=keypair_policies,
                user_policies=snapshot_data.user_policies,
                group_limits=group_limits,
                domain_limits=domain_limits,
            )

            # Extract pending sessions
            pending_sessions = self._extract_pending_sessions(snapshot_data.consolidated_sessions)

            system_snapshot = SystemSnapshot(
                total_capacity=snapshot_data.total_capacity,
                resource_occupancy=snapshot_data.resource_occupancy,
                resource_policy=resource_policy,
                concurrency=ConcurrencySnapshot(
                    sessions_by_keypair={},  # Will be populated from Redis if needed
                    sftp_sessions_by_keypair={},
                ),
                pending_sessions=pending_sessions,
                session_dependencies=snapshot_data.session_dependencies,
            )
        else:
            # Create empty snapshot if no data
            system_snapshot = SystemSnapshot(
                total_capacity=ResourceSlot(),
                resource_occupancy=ResourceOccupancySnapshot(
                    by_keypair={}, by_user={}, by_group={}, by_domain={}
                ),
                resource_policy=ResourcePolicySnapshot(
                    keypair_policies={}, user_policies={}, group_limits={}, domain_limits={}
                ),
                concurrency=ConcurrencySnapshot(
                    sessions_by_keypair={}, sftp_sessions_by_keypair={}
                ),
                pending_sessions=PendingSessionSnapshot(by_keypair={}),
                session_dependencies=SessionDependencySnapshot(by_session={}),
            )

        return system_snapshot

    @repository_decorator()
    async def get_scheduling_context_data(
        self, scaling_group: str
    ) -> Optional[SchedulingContextData]:
        """
        Fetch all data needed for scheduling in ONE database session,
        then transform after closing DB connection.
        Returns None if no pending sessions exist (early exit optimization).

        This consolidates the following operations:
        - get_scaling_group_info_for_sokovan
        - get_pending_sessions
        - get_system_snapshot (only if pending sessions exist)
        - get_scheduling_config
        """
        async with self._db.begin_readonly_session() as db_sess:
            raw_data = await self._fetch_raw_scheduling_data(db_sess, scaling_group)

        if raw_data is None or not raw_data.pending_sessions:
            return None
        raw_value = await self._config_provider.legacy_etcd_config_loader.get_raw(
            "config/agent/max-container-count"
        )
        if raw_value is not None:
            raw_data.max_container_count = int(raw_value)
        return self._transform_to_scheduling_context(raw_data)

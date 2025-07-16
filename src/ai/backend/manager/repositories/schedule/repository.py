import itertools
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Iterable, Optional

import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from ai.backend.common.decorators import create_layer_aware_repository_decorator
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import AgentId, ResourceSlot, SessionId
from ai.backend.manager.models import (
    AgentRow,
    AgentStatus,
    EndpointRow,
    KernelRow,
    KernelStatus,
    RoutingRow,
    ScalingGroupOpts,
    ScalingGroupRow,
    SessionRow,
    SessionStatus,
    recalc_agent_resource_occupancy,
)
from ai.backend.manager.models.endpoint import EndpointAutoScalingRuleRow
from ai.backend.manager.models.kernel import recalc_concurrency_used
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    sql_json_increment,
    sql_json_merge,
)
from ai.backend.manager.scheduler.types import AgentAllocationContext, SchedulingContext

# Layer-specific decorator for schedule repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.SCHEDULE)


class ScheduleRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

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
    async def get_session_by_id(self, session_id: SessionId) -> Optional[SessionRow]:
        async with self._db.begin_readonly_session() as session:
            return await SessionRow.get_session_by_id(session, session_id)

    @repository_decorator()
    async def get_schedulable_session_with_kernels_and_agents(
        self, session_id: SessionId
    ) -> Optional[SessionRow]:
        async with self._db.begin_readonly_session() as session:
            return await self._get_schedulable_session_with_kernels_and_agents(session, session_id)

    async def _get_schedulable_session_with_kernels_and_agents(
        self, session: SASession, session_id: SessionId
    ) -> Optional[SessionRow]:
        from sqlalchemy.orm import noload, selectinload

        eager_loading_op = (
            noload("*"),
            selectinload(SessionRow.kernels).options(
                noload("*"),
                selectinload(KernelRow.agent_row).noload("*"),
            ),
        )
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
        status_data: Any,
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
    async def finalize_scheduled_session(
        self,
        session_id: SessionId,
        sgroup_name: str,
        kernel_agent_bindings: list,
    ) -> None:
        from datetime import datetime

        from dateutil.tz import tzutc

        from ai.backend.manager.models import KernelStatus, SessionStatus
        from ai.backend.manager.models.utils import sql_json_merge

        async with self._db.begin_session() as session:
            agent_ids = []
            now = datetime.now(tzutc())

            for binding in kernel_agent_bindings:
                kernel_query = (
                    sa.update(KernelRow)
                    .values(
                        agent=binding.agent_alloc_ctx.agent_id,
                        agent_addr=binding.agent_alloc_ctx.agent_addr,
                        scaling_group=sgroup_name,
                        status=KernelStatus.SCHEDULED,
                        status_info="scheduled",
                        status_history=sql_json_merge(
                            KernelRow.status_history,
                            (),
                            {
                                KernelStatus.SCHEDULED.name: now.isoformat(),
                            },
                        ),
                    )
                    .where(KernelRow.id == binding.kernel.id)
                )
                await session.execute(kernel_query)
                if binding.agent_alloc_ctx.agent_id is not None:
                    agent_ids.append(binding.agent_alloc_ctx.agent_id)

            session_query = (
                sa.update(SessionRow)
                .values(
                    scaling_group_name=sgroup_name,
                    agent_ids=agent_ids,
                    status=SessionStatus.SCHEDULED,
                    status_info="scheduled",
                    status_data={},
                    status_history=sql_json_merge(
                        SessionRow.status_history,
                        (),
                        {
                            SessionStatus.SCHEDULED.name: now.isoformat(),
                        },
                    ),
                )
                .where(SessionRow.id == session_id)
            )
            await session.execute(session_query)

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
        exc_data: Any,
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

    async def _finalize_single_node_session(
        self,
        session_id: SessionId,
        sgroup_name: str,
        agent_alloc_ctx: AgentAllocationContext,
    ) -> None:
        async with self._db.begin_session() as session:
            agent_ids: list[AgentId] = []
            now = datetime.now(tzutc())

            session_row = await session.get(SessionRow, session_id)
            if session_row is None:
                raise RuntimeError(f"Session {session_id} not found")

            for kernel in session_row.kernels:
                kernel_query = (
                    sa.update(KernelRow)
                    .values(
                        agent=agent_alloc_ctx.agent_id,
                        agent_addr=agent_alloc_ctx.agent_addr,
                        scaling_group=sgroup_name,
                        status=KernelStatus.SCHEDULED,
                        status_info="scheduled",
                        status_data={},
                        status_changed=now,
                        status_history=sql_json_merge(
                            KernelRow.status_history,
                            (),
                            {
                                KernelStatus.SCHEDULED.name: now.isoformat(),
                            },
                        ),
                    )
                    .where(KernelRow.id == kernel.id)
                )
                await session.execute(kernel_query)
            if agent_alloc_ctx.agent_id is not None:
                agent_ids.append(agent_alloc_ctx.agent_id)

            session_query = (
                sa.update(SessionRow)
                .values(
                    scaling_group_name=sgroup_name,
                    agent_ids=agent_ids,
                    status=SessionStatus.SCHEDULED,
                    status_info="scheduled",
                    status_data={},
                    status_history=sql_json_merge(
                        SessionRow.status_history,
                        (),
                        {
                            SessionStatus.SCHEDULED.name: now.isoformat(),
                        },
                    ),
                )
                .where(SessionRow.id == session_id)
            )
            await session.execute(session_query)

    async def _update_kernel_scheduling_failure(
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

    async def _update_multinode_kernel_generic_failure(
        self,
        sched_ctx: SchedulingContext,
        sess_ctx: SessionRow,
        kernel_id: str,
        exc_data: Any,
    ) -> None:
        await self.update_session_predicate_failure(sched_ctx, sess_ctx, {})
        await self.update_kernel_status_with_error(kernel_id, "scheduler-error", exc_data)

    async def _mark_session_cancelled(
        self,
        sched_ctx: SchedulingContext,
        session: SessionRow,
        status_data: Any,
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
        from datetime import timezone

        from sqlalchemy import cast

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
            return await self._mark_sessions_and_kernels_creating(session)

    async def _mark_sessions_and_kernels_creating(self, session: SASession) -> list[SessionRow]:
        from datetime import timezone

        from sqlalchemy import cast

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
            return await self._clean_zombie_routes(session)

    async def _clean_zombie_routes(self, session: SASession) -> int:
        from ai.backend.manager.models import RouteStatus

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
            query = sa.delete(RoutingRow).where(RoutingRow.id.in_([r.id for r in zombie_routes]))
            result = await session.execute(query)
            return result.rowcount
        return 0

    @repository_decorator()
    async def create_routing_rows(self, endpoint_create_data: list[tuple]) -> list[uuid.UUID]:
        async with self._db.begin_session() as session:
            return await self._create_routing_rows(session, endpoint_create_data)

    async def _create_routing_rows(
        self, session: SASession, endpoint_create_data: list[tuple]
    ) -> list[uuid.UUID]:
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
            await self._destroy_terminated_endpoints_and_routes(
                session, endpoints_to_mark_terminated, already_destroyed_sessions
            )

    async def _destroy_terminated_endpoints_and_routes(
        self,
        session: SASession,
        endpoints_to_mark_terminated: set,
        already_destroyed_sessions: list[SessionId],
    ) -> None:
        from ai.backend.manager.models import EndpointLifecycle

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
            return await self._get_container_info_for_destroyed_kernels(session, session_id)

    async def _get_container_info_for_destroyed_kernels(
        self, session: SASession, session_id: SessionId
    ) -> dict:
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
        current_datetime = datetime.now(tz=UTC)
        rules = await EndpointAutoScalingRuleRow.list(session)

        # TODO: Check this implementation
        # Currently auto scaling supports two types of stat as source: kernel and endpoint
        # endpoints = await EndpointRow.batch_load(
        #     session, [rule.endpoint for rule in rules], load_routes=True
        # )
        # endpoint_by_id = {endpoint.id: endpoint for endpoint in endpoints}

        # For now, we'll just update the last_triggered_at and replicas
        # The actual metric evaluation logic should stay in the service layer
        for rule in rules:
            if rule.last_triggered_at is None or rule.last_triggered_at < (
                current_datetime - timedelta(seconds=rule.cooldown_seconds)
            ):
                # This is just a placeholder - actual logic would be moved here
                pass

    @repository_decorator()
    async def get_endpoints_for_scaling(self) -> list:
        async with self._db.begin_readonly_session() as session:
            return await self._get_endpoints_for_scaling(session)

    async def _get_endpoints_for_scaling(self, session: SASession) -> list:
        from ai.backend.manager.models import EndpointLifecycle

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
        from sqlalchemy.orm import noload, selectinload

        from ai.backend.manager.models.session import _build_session_fetch_query

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
                import logging

                from ai.backend.logging import BraceStyleAdapter

                log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.scheduler"))
                log.warning("failed to communicate with AppProxy endpoint: {}", str(e))

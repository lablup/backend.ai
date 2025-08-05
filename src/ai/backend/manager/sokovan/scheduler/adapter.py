"""Adapter to make ScheduleRepository compatible with SchedulerRepository protocol."""

from collections.abc import Sequence
from datetime import timedelta

import sqlalchemy as sa

from ai.backend.common.types import AgentSelectionStrategy
from ai.backend.manager.models import ScalingGroupRow
from ai.backend.manager.repositories.schedule.repository import ScheduleRepository
from ai.backend.manager.sokovan.scheduler.scheduler import ScalingGroupInfo
from ai.backend.manager.sokovan.scheduler.types import KernelWorkload, SessionWorkload


class ScheduleRepositoryAdapter:
    """Adapter to make ScheduleRepository implement SchedulerRepository protocol."""

    def __init__(self, schedule_repo: ScheduleRepository) -> None:
        self._repo = schedule_repo

    # Delegate existing methods
    async def get_system_snapshot(self, scaling_group: str):
        return await self._repo.get_system_snapshot(scaling_group)

    async def get_agents(self, scaling_group: str):
        return await self._repo.get_agents(scaling_group)

    async def get_scheduling_config(self, scaling_group: str):
        return await self._repo.get_scheduling_config(scaling_group)

    async def get_schedulable_scaling_groups(self) -> list[str]:
        return await self._repo.get_schedulable_scaling_groups()

    # New methods
    async def get_pending_sessions(self, scaling_group: str) -> Sequence[SessionWorkload]:
        """Get pending sessions for a scaling group as workloads."""
        async with self._repo._db.begin_readonly_session() as db_sess:
            # Get pending sessions
            pending_sessions, _, _ = await self._repo._list_managed_sessions(
                db_sess, scaling_group, timedelta(minutes=30)
            )

            # Convert to SessionWorkload objects
            workloads: list[SessionWorkload] = []
            for session in pending_sessions:
                # Get session info with kernels
                eager_session = await self._repo._get_schedulable_session_with_kernels_and_agents(
                    db_sess, session.id
                )
                if not eager_session:
                    continue

                # Get user info
                user_uuid = (
                    eager_session.user_row.uuid
                    if eager_session.user_row
                    else eager_session.user_uuid
                )

                # Create kernel workloads
                kernel_workloads = [
                    KernelWorkload(
                        kernel_id=kernel.id,
                        image=kernel.image,
                        architecture=kernel.architecture,
                        requested_slots=kernel.requested_slots,
                    )
                    for kernel in eager_session.kernels
                ]

                workload = SessionWorkload(
                    session_id=eager_session.id,
                    requested_slots=eager_session.requested_slots,
                    session_type=eager_session.session_type,
                    cluster_mode=eager_session.cluster_mode,
                    access_key=eager_session.access_key,
                    user_uuid=user_uuid,
                    group_id=eager_session.group_id,
                    domain_name=eager_session.domain_name,
                    scaling_group=scaling_group,
                    priority=eager_session.priority,
                    starts_at=eager_session.starts_at,
                    is_private=eager_session.is_private,
                    kernels=kernel_workloads,
                    designated_agent=eager_session.kernels[0].agent
                    if eager_session.kernels
                    else None,
                )
                workloads.append(workload)

            return workloads

    async def get_scaling_group_info(self, scaling_group: str) -> ScalingGroupInfo:
        """Get scaling group configuration including scheduler name and agent selection strategy."""
        async with self._repo._db.begin_readonly_session() as db_sess:
            query = sa.select(
                ScalingGroupRow.scheduler,
                ScalingGroupRow.scheduler_opts,
            ).where(ScalingGroupRow.name == scaling_group)

            result = await db_sess.execute(query)
            row = result.first()
            if not row:
                raise ValueError(f"Scaling group {scaling_group} not found")

            scheduler_opts = row.scheduler_opts or {}

            return ScalingGroupInfo(
                scheduler_name=row.scheduler,
                agent_selection_strategy=scheduler_opts.get(
                    "agent_selection_strategy", AgentSelectionStrategy.CONCENTRATED
                ),
            )

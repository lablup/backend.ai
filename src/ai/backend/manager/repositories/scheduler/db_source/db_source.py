"""Database source for schedule repository operations."""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Mapping, Optional, cast
from uuid import UUID

import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import load_only, selectinload

from ai.backend.common.docker import ImageRef
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ResourceSlot,
    SessionId,
    SessionTypes,
    SlotName,
    SlotTypes,
    VFolderMount,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models import (
    AgentRow,
    AgentStatus,
    DefaultForUnspecified,
    DomainRow,
    GroupRow,
    ImageRow,
    KernelRow,
    KernelStatus,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    ScalingGroupRow,
    SessionDependencyRow,
    SessionRow,
    SessionStatus,
    UserRow,
    query_allowed_sgroups,
)
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    sql_json_merge,
)
from ai.backend.manager.sokovan.scheduler.types import (
    AgentOccupancy,
    AllocationBatch,
    KeypairOccupancy,
    KeyPairResourcePolicy,
    ResourceOccupancySnapshot,
    SchedulingFailure,
    SessionAllocation,
    SessionDependencyInfo,
    SessionDependencySnapshot,
    UserResourcePolicy,
)

from ..types.agent import AgentMeta
from ..types.base import SchedulingSpec
from ..types.scaling_group import ScalingGroupMeta
from ..types.scheduling import SchedulingData
from ..types.session import (
    KernelData,
    MarkTerminatingResult,
    PendingSessionData,
    PendingSessions,
    SessionTerminationResult,
    SweptSessionInfo,
    TerminatingKernelData,
    TerminatingSessionData,
)
from ..types.session_creation import (
    AllowedScalingGroup,
    ImageInfo,
    ScalingGroupNetworkInfo,
    SessionCreationContext,
    SessionCreationSpec,
    SessionEnqueueData,
)
from ..types.snapshot import ResourcePolicies, SnapshotData
from .types import SessionRowCache

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _create_resource_slot_from_policy(
    total_resource_slots: Optional[ResourceSlot],
    default_for_unspecified: Optional[DefaultForUnspecified],
    known_slot_types: Mapping[SlotName, SlotTypes],
) -> ResourceSlot:
    """Create ResourceSlot from policy data."""
    resource_policy_map = {
        "total_resource_slots": total_resource_slots or ResourceSlot(),
        "default_for_unspecified": default_for_unspecified or DefaultForUnspecified.LIMITED,
    }
    return ResourceSlot.from_policy(resource_policy_map, known_slot_types)


class ScheduleDBSource:
    """
    Database source for schedule-related operations.
    Handles all database queries and updates for scheduling.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine):
        self._db = db

    async def get_scheduling_data(self, scaling_group: str, spec: SchedulingSpec) -> SchedulingData:
        """
        Fetch all scheduling data from database in a single session.
        Raises ScalingGroupNotFound if scaling group doesn't exist.
        """
        async with self._db.begin_readonly_session() as db_sess:
            # 1. Get scaling group
            scaling_group_meta = await self._fetch_scaling_group(db_sess, scaling_group)

            # 2. Get pending sessions
            pending_sessions = await self._fetch_pending_sessions(db_sess, scaling_group)
            if not pending_sessions.sessions:
                return SchedulingData(
                    scaling_group=scaling_group_meta,
                    pending_sessions=pending_sessions,
                    agents=[],
                    snapshot_data=None,
                    spec=spec,
                )

            # 3. Get agents
            agents = await self._fetch_agents(db_sess, scaling_group)

            # 4. Get snapshot data
            snapshot_data = await self._fetch_snapshot_data(
                db_sess, scaling_group, pending_sessions, spec.known_slot_types
            )

            return SchedulingData(
                scaling_group=scaling_group_meta,
                pending_sessions=pending_sessions,
                agents=agents,
                snapshot_data=snapshot_data,
                spec=spec,
            )

    async def _fetch_scaling_group(
        self, db_sess: SASession, scaling_group: str
    ) -> ScalingGroupMeta:
        """
        Fetch scaling group metadata.
        Raises ScalingGroupNotFound if scaling group doesn't exist.
        """
        sg_result = await db_sess.execute(
            sa.select(
                ScalingGroupRow.name,
                ScalingGroupRow.scheduler,
                ScalingGroupRow.scheduler_opts,
            ).where(ScalingGroupRow.name == scaling_group)
        )
        sg_row = sg_result.one_or_none()
        if not sg_row:
            raise ScalingGroupNotFound(scaling_group)

        return ScalingGroupMeta(
            name=sg_row.name,
            scheduler=sg_row.scheduler,
            scheduler_opts=sg_row.scheduler_opts,
        )

    async def _fetch_pending_sessions(
        self, db_sess: SASession, scaling_group: str
    ) -> PendingSessions:
        """Fetch pending sessions with kernels using single JOIN query."""
        query = (
            sa.select(
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
                KernelRow.id.label("kernel_id"),
                KernelRow.image.label("kernel_image"),
                KernelRow.architecture.label("kernel_arch"),
                KernelRow.requested_slots.label("kernel_slots"),
                KernelRow.agent.label("kernel_agent"),
            )
            .select_from(SessionRow)
            .outerjoin(KernelRow, SessionRow.id == KernelRow.session_id)
            .where(
                sa.and_(
                    SessionRow.scaling_group_name == scaling_group,
                    SessionRow.status == SessionStatus.PENDING,
                )
            )
        )
        result = await db_sess.execute(query)

        sessions_map: dict[SessionId, PendingSessionData] = {}
        for row in result:
            session_id = row.id
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
                    is_private=row.session_type in SessionTypes.private_types(),
                    kernels=[],
                )

            if row.kernel_id:
                kernel = KernelData(
                    id=row.kernel_id,
                    image=row.kernel_image,
                    architecture=row.kernel_arch,
                    requested_slots=row.kernel_slots,
                    agent=row.kernel_agent,
                )
                sessions_map[session_id].kernels.append(kernel)

        return PendingSessions(sessions=list(sessions_map.values()))

    async def _fetch_agents(self, db_sess: SASession, scaling_group: str) -> list[AgentMeta]:
        """Fetch schedulable agent metadata in the scaling group."""
        agents_result = await db_sess.execute(
            sa.select(
                AgentRow.id,
                AgentRow.addr,
                AgentRow.architecture,
                AgentRow.available_slots,
                AgentRow.scaling_group,
            ).where(
                sa.and_(
                    AgentRow.status == AgentStatus.ALIVE,
                    AgentRow.scaling_group == scaling_group,
                    AgentRow.schedulable == sa.true(),
                )
            )
        )

        agents = []
        for row in agents_result:
            agents.append(
                AgentMeta(
                    id=row.id,
                    addr=row.addr,
                    architecture=row.architecture,
                    available_slots=row.available_slots,
                    scaling_group=row.scaling_group,
                )
            )
        return agents

    async def _fetch_snapshot_data(
        self,
        db_sess: SASession,
        scaling_group: str,
        pending_sessions: PendingSessions,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> SnapshotData:
        """Fetch all snapshot data for system state."""
        resource_occupancy = await self._fetch_kernel_occupancy(db_sess, scaling_group)

        # Fetch resource policies for entities in pending sessions
        resource_policies = await self._fetch_resource_policies(
            db_sess,
            pending_sessions,
            known_slot_types,
        )

        # Session dependencies
        session_ids = [s.id for s in pending_sessions.sessions]
        session_dependencies = await self._fetch_session_dependencies(db_sess, session_ids)

        return SnapshotData(
            resource_occupancy=resource_occupancy,
            resource_policies=resource_policies,
            session_dependencies=SessionDependencySnapshot(by_session=session_dependencies),
        )

    async def _fetch_kernel_occupancy(
        self, db_sess: SASession, scaling_group: str
    ) -> ResourceOccupancySnapshot:
        """Fetch kernel occupancy data from active kernels and session counts."""
        # First, fetch kernel occupancy data
        occupancy_result = await db_sess.execute(
            sa.select(
                KernelRow.session_id,
                KernelRow.access_key,
                KernelRow.user_uuid,
                KernelRow.group_id,
                KernelRow.domain_name,
                KernelRow.agent,
                KernelRow.occupied_slots,
                KernelRow.session_type,
            ).where(
                sa.and_(
                    KernelRow.status.in_(KernelStatus.resource_occupied_statuses()),
                    KernelRow.scaling_group == scaling_group,
                )
            )
        )

        # Keypair occupancy with both slots and session counts
        def keypair_occupancy_factory() -> KeypairOccupancy:
            return KeypairOccupancy(
                occupied_slots=ResourceSlot(), session_count=0, sftp_session_count=0
            )

        occupancy_by_keypair: dict[AccessKey, KeypairOccupancy] = defaultdict(
            keypair_occupancy_factory
        )
        occupancy_by_user: dict[UUID, ResourceSlot] = defaultdict(ResourceSlot)
        occupancy_by_group: dict[UUID, ResourceSlot] = defaultdict(ResourceSlot)
        occupancy_by_domain: dict[str, ResourceSlot] = defaultdict(ResourceSlot)

        # Agent occupancy with both slots and container counts
        def agent_occupancy_factory() -> AgentOccupancy:
            return AgentOccupancy(occupied_slots=ResourceSlot(), container_count=0)

        occupancy_by_agent: dict[AgentId, AgentOccupancy] = defaultdict(agent_occupancy_factory)

        # Track unique sessions per keypair to count correctly
        sessions_by_keypair: dict[AccessKey, set[SessionId]] = defaultdict(set)
        sftp_sessions_by_keypair: dict[AccessKey, set[SessionId]] = defaultdict(set)

        for row in occupancy_result:
            session_type = cast(SessionTypes, row.session_type)
            # Only accumulate resource slots for non-private sessions
            if not session_type.is_private():
                occupancy_by_keypair[row.access_key].occupied_slots += row.occupied_slots
                occupancy_by_user[row.user_uuid] += row.occupied_slots
                occupancy_by_group[row.group_id] += row.occupied_slots
                occupancy_by_domain[row.domain_name] += row.occupied_slots

                # Track regular sessions
                sessions_by_keypair[row.access_key].add(row.session_id)
            else:
                # Track SFTP sessions
                sftp_sessions_by_keypair[row.access_key].add(row.session_id)

            if row.agent:
                occupancy_by_agent[row.agent].occupied_slots += row.occupied_slots
                occupancy_by_agent[row.agent].container_count += 1

        # Update session counts in keypair occupancy
        for access_key, sessions in sessions_by_keypair.items():
            occupancy_by_keypair[access_key].session_count = len(sessions)

        for access_key, sessions in sftp_sessions_by_keypair.items():
            occupancy_by_keypair[access_key].sftp_session_count = len(sessions)

        return ResourceOccupancySnapshot(
            by_keypair=occupancy_by_keypair,
            by_user=occupancy_by_user,
            by_group=occupancy_by_group,
            by_domain=occupancy_by_domain,
            by_agent=occupancy_by_agent,
        )

    async def _fetch_resource_policies(
        self,
        db_sess: SASession,
        pending_sessions: PendingSessions,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> ResourcePolicies:
        """Fetch resource policies for entities in pending sessions."""
        keypair_policies = await self._fetch_keypair_policies(
            db_sess, pending_sessions, known_slot_types
        )
        user_policies = await self._fetch_user_policies(db_sess, pending_sessions, known_slot_types)
        group_limits = await self._fetch_group_limits(db_sess, pending_sessions, known_slot_types)
        domain_limits = await self._fetch_domain_limits(db_sess, pending_sessions, known_slot_types)

        return ResourcePolicies(
            keypair_policies=keypair_policies,
            user_policies=user_policies,
            group_limits=group_limits,
            domain_limits=domain_limits,
        )

    async def _fetch_keypair_policies(
        self,
        db_sess: SASession,
        pending_sessions: PendingSessions,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> dict[AccessKey, KeyPairResourcePolicy]:
        """Fetch keypair resource policies."""
        keypair_policies: dict[AccessKey, KeyPairResourcePolicy] = {}

        if not pending_sessions.access_keys:
            return keypair_policies

        kp_policy_result = await db_sess.execute(
            sa.select(
                KeyPairRow.access_key,
                KeyPairResourcePolicyRow.name,
                KeyPairResourcePolicyRow.total_resource_slots,
                KeyPairResourcePolicyRow.default_for_unspecified,
                KeyPairResourcePolicyRow.max_concurrent_sessions,
                KeyPairResourcePolicyRow.max_concurrent_sftp_sessions,
                KeyPairResourcePolicyRow.max_pending_session_count,
                KeyPairResourcePolicyRow.max_pending_session_resource_slots,
            )
            .select_from(KeyPairRow)
            .join(
                KeyPairResourcePolicyRow,
                KeyPairRow.resource_policy == KeyPairResourcePolicyRow.name,
            )
            .where(KeyPairRow.access_key.in_(pending_sessions.access_keys))
        )

        for row in kp_policy_result:
            if row.name:
                total_resource_slots = _create_resource_slot_from_policy(
                    row.total_resource_slots,
                    row.default_for_unspecified,
                    known_slot_types,
                )

                keypair_policies[row.access_key] = KeyPairResourcePolicy(
                    name=row.name,
                    total_resource_slots=total_resource_slots,
                    max_concurrent_sessions=row.max_concurrent_sessions or 0,
                    max_concurrent_sftp_sessions=row.max_concurrent_sftp_sessions or 0,
                    max_pending_session_count=row.max_pending_session_count,
                    max_pending_session_resource_slots=row.max_pending_session_resource_slots,
                )

        return keypair_policies

    async def _fetch_group_limits(
        self,
        db_sess: SASession,
        pending_sessions: PendingSessions,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> dict[UUID, ResourceSlot]:
        """Fetch group resource limits."""
        group_limits: dict[UUID, ResourceSlot] = {}

        if not pending_sessions.group_ids:
            return group_limits

        group_result = await db_sess.execute(
            sa.select(
                GroupRow.id,
                GroupRow.total_resource_slots,
            ).where(GroupRow.id.in_(pending_sessions.group_ids))
        )

        for row in group_result:
            if row.total_resource_slots is not None:
                group_limits[row.id] = _create_resource_slot_from_policy(
                    row.total_resource_slots,
                    DefaultForUnspecified.UNLIMITED,
                    known_slot_types,
                )

        return group_limits

    async def _fetch_domain_limits(
        self,
        db_sess: SASession,
        pending_sessions: PendingSessions,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> dict[str, ResourceSlot]:
        """Fetch domain resource limits."""
        domain_limits: dict[str, ResourceSlot] = {}

        if not pending_sessions.domain_names:
            return domain_limits

        domain_result = await db_sess.execute(
            sa.select(
                DomainRow.name,
                DomainRow.total_resource_slots,
            ).where(DomainRow.name.in_(pending_sessions.domain_names))
        )

        for row in domain_result:
            if row.total_resource_slots is not None:
                domain_limits[row.name] = _create_resource_slot_from_policy(
                    row.total_resource_slots,
                    DefaultForUnspecified.UNLIMITED,
                    known_slot_types,
                )

        return domain_limits

    async def _fetch_user_policies(
        self,
        db_sess: SASession,
        pending_sessions: PendingSessions,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ) -> dict[UUID, UserResourcePolicy]:
        """Fetch user resource policies for users in pending sessions."""
        user_policies: dict[UUID, UserResourcePolicy] = {}

        if not pending_sessions.user_uuids:
            return user_policies

        user_policy_result = await db_sess.execute(
            sa.select(
                UserRow.uuid,
                KeyPairResourcePolicyRow.name,
                KeyPairResourcePolicyRow.total_resource_slots,
                KeyPairResourcePolicyRow.default_for_unspecified,
            )
            .select_from(UserRow)
            .join(KeyPairRow, UserRow.main_access_key == KeyPairRow.access_key)
            .join(
                KeyPairResourcePolicyRow,
                KeyPairRow.resource_policy == KeyPairResourcePolicyRow.name,
            )
            .where(UserRow.uuid.in_(pending_sessions.user_uuids))
        )

        for row in user_policy_result:
            if row.name:
                total_resource_slots = _create_resource_slot_from_policy(
                    row.total_resource_slots,
                    row.default_for_unspecified,
                    known_slot_types,
                )
                user_policies[row.uuid] = UserResourcePolicy(
                    name=row.name,
                    total_resource_slots=total_resource_slots,
                )

        return user_policies

    async def _fetch_session_dependencies(
        self, db_sess: SASession, session_ids: list[SessionId]
    ) -> dict[SessionId, list[SessionDependencyInfo]]:
        """Fetch session dependencies."""
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

    async def mark_sessions_terminating(
        self, session_ids: list[SessionId], reason: str = "USER_REQUESTED"
    ) -> MarkTerminatingResult:
        """
        Mark sessions and their kernels as TERMINATING.
        Uses UPDATE ... WHERE ... RETURNING for atomic status transitions.
        Returns categorized session IDs based on their current status.
        """
        now = datetime.now(tzutc())

        async with self._db.begin_session() as db_sess:
            # 1. Cancel pending sessions
            cancelled_sessions = await self._cancel_pending_sessions(
                db_sess, session_ids, reason, now
            )

            # 2. Mark resource-occupying sessions as terminating
            terminating_sessions = await self._mark_sessions_as_terminating(
                db_sess, session_ids, reason, now
            )

            # 3. Mark unprocessed sessions as skipped
            processed_ids = set(cancelled_sessions) | set(terminating_sessions)
            skipped_sessions = [sid for sid in session_ids if sid not in processed_ids]

            return MarkTerminatingResult(
                cancelled_sessions=cancelled_sessions,
                terminating_sessions=terminating_sessions,
                skipped_sessions=skipped_sessions,
            )

    async def _cancel_pending_sessions(
        self, db_sess: SASession, session_ids: list[SessionId], reason: str, now: datetime
    ) -> list[SessionId]:
        """Cancel pending sessions and their kernels."""
        # Cancel pending sessions
        cancel_stmt = (
            sa.update(SessionRow)
            .values(
                status=SessionStatus.CANCELLED,
                status_info=reason,
                terminated_at=now,
                status_history=sql_json_merge(
                    SessionRow.status_history,
                    (),
                    {SessionStatus.CANCELLED.name: now.isoformat()},
                ),
            )
            .where(
                sa.and_(SessionRow.id.in_(session_ids), SessionRow.status == SessionStatus.PENDING)
            )
            .returning(SessionRow.id)
        )
        cancelled_result = await db_sess.execute(cancel_stmt)
        cancelled_sessions = [cast(SessionId, row.id) for row in cancelled_result]

        # Cancel kernels for cancelled sessions
        if cancelled_sessions:
            await db_sess.execute(
                sa.update(KernelRow)
                .values(
                    status=KernelStatus.CANCELLED,
                    status_info=reason,
                    status_changed=now,
                    terminated_at=now,
                    status_history=sql_json_merge(
                        KernelRow.status_history,
                        (),
                        {KernelStatus.CANCELLED.name: now.isoformat()},
                    ),
                )
                .where(KernelRow.session_id.in_(cancelled_sessions))
            )

        return cancelled_sessions

    async def _mark_sessions_as_terminating(
        self, db_sess: SASession, session_ids: list[SessionId], reason: str, now: datetime
    ) -> list[SessionId]:
        """Mark resource-occupying sessions and their kernels as terminating."""
        # Mark sessions as terminating
        terminating_stmt = (
            sa.update(SessionRow)
            .values(
                status=SessionStatus.TERMINATING,
                status_info=reason,
                status_history=sql_json_merge(
                    SessionRow.status_history,
                    (),
                    {SessionStatus.TERMINATING.name: now.isoformat()},
                ),
            )
            .where(
                sa.and_(
                    SessionRow.id.in_(session_ids),
                    SessionRow.status.in_(SessionStatus.resource_occupied_statuses()),
                )
            )
            .returning(SessionRow.id)
        )
        terminating_result = await db_sess.execute(terminating_stmt)
        terminating_sessions = [cast(SessionId, row.id) for row in terminating_result]

        # Mark kernels as terminating
        if terminating_sessions:
            await db_sess.execute(
                sa.update(KernelRow)
                .values(
                    status=KernelStatus.TERMINATING,
                    status_info=reason,
                    status_history=sql_json_merge(
                        KernelRow.status_history,
                        (),
                        {KernelStatus.TERMINATING.name: now.isoformat()},
                    ),
                )
                .where(KernelRow.session_id.in_(terminating_sessions))
            )

        return terminating_sessions

    async def get_schedulable_scaling_groups(self) -> list[str]:
        """Get list of scaling groups that have schedulable agents."""
        async with self._db.begin_readonly_session() as session:
            query = (
                sa.select(AgentRow.scaling_group)
                .where(
                    sa.and_(AgentRow.status == AgentStatus.ALIVE, AgentRow.schedulable == sa.true())
                )
                .group_by(AgentRow.scaling_group)
            )
            result = await session.execute(query)
            return [row.scaling_group for row in result.fetchall()]

    async def get_terminating_sessions(self) -> list[TerminatingSessionData]:
        """Fetch all sessions with TERMINATING status."""
        async with self._db.begin_readonly_session() as session:
            query = (
                sa.select(SessionRow)
                .where(SessionRow.status == SessionStatus.TERMINATING)
                .options(
                    selectinload(SessionRow.kernels).options(
                        load_only(
                            KernelRow.id,
                            KernelRow.status,
                            KernelRow.container_id,
                            KernelRow.agent,
                            KernelRow.agent_addr,
                            KernelRow.occupied_slots,
                        )
                    )
                )
            )
            result = await session.execute(query)
            session_rows = list(result.scalars().all())

            terminating_sessions = []
            for session_row in session_rows:
                kernels = [
                    TerminatingKernelData(
                        kernel_id=str(kernel.id),
                        status=kernel.status,
                        container_id=kernel.container_id,
                        agent_id=kernel.agent,
                        agent_addr=kernel.agent_addr,
                        occupied_slots=kernel.occupied_slots,
                    )
                    for kernel in session_row.kernels
                ]

                terminating_sessions.append(
                    TerminatingSessionData(
                        session_id=session_row.id,
                        access_key=session_row.access_key,
                        creation_id=session_row.creation_id,
                        status=session_row.status,
                        status_info=session_row.status_info or "UNKNOWN",
                        session_type=session_row.session_type,
                        kernels=kernels,
                    )
                )

            return terminating_sessions

    async def get_pending_timeout_sessions(self) -> list[SweptSessionInfo]:
        """Get sessions that have exceeded their pending timeout."""
        now = datetime.now(tzutc())
        timed_out_sessions: list[SweptSessionInfo] = []

        async with self._db.begin_readonly_session() as db_sess:
            query = (
                sa.select(
                    SessionRow.id,
                    SessionRow.creation_id,
                    SessionRow.created_at,
                    SessionRow.scaling_group_name,
                    ScalingGroupRow.scheduler_opts,
                )
                .select_from(SessionRow)
                .join(ScalingGroupRow, SessionRow.scaling_group_name == ScalingGroupRow.name)
                .where(SessionRow.status == SessionStatus.PENDING)
            )

            result = await db_sess.execute(query)
            pending_sessions = result.fetchall()

            for row in pending_sessions:
                scheduler_opts = row.scheduler_opts
                if not scheduler_opts:
                    continue

                timeout = scheduler_opts.pending_timeout
                if timeout.total_seconds() <= 0:
                    continue

                elapsed_time = now - row.created_at
                if elapsed_time >= timeout:
                    timed_out_sessions.append(
                        SweptSessionInfo(
                            session_id=row.id,
                            creation_id=row.creation_id,
                        )
                    )

        return timed_out_sessions

    async def enqueue_session(
        self,
        session_data: "SessionEnqueueData",
    ) -> SessionId:
        """
        Create new session and kernel records in PENDING status.

        Args:
            session_data: Prepared session data with kernels and dependencies

        Returns:
            SessionId: The ID of the created session
        """
        async with self._db.begin_session() as db_sess:
            # Validate dependencies if any
            matched_dependency_ids = []
            if session_data.dependencies:
                for dependency_id in session_data.dependencies:
                    # Check if dependency session exists
                    query = sa.select(SessionRow.id).where(SessionRow.id == dependency_id)
                    result = await db_sess.execute(query)
                    if not result.scalar():
                        raise InvalidAPIParameters(
                            "Unknown session ID in the dependency list",
                            extra_data={"session_ref": str(dependency_id)},
                        )
                    matched_dependency_ids.append(dependency_id)

            # Create session row
            session = SessionRow(
                id=session_data.id,
                creation_id=session_data.creation_id,
                name=session_data.name,
                access_key=session_data.access_key,
                user_uuid=session_data.user_uuid,
                group_id=session_data.group_id,
                domain_name=session_data.domain_name,
                scaling_group_name=session_data.scaling_group_name,
                session_type=session_data.session_type,
                cluster_mode=session_data.cluster_mode,
                cluster_size=session_data.cluster_size,
                priority=session_data.priority,
                status=SessionStatus[session_data.status],
                status_history=session_data.status_history,
                requested_slots=session_data.requested_slots,
                occupying_slots=session_data.occupying_slots,
                vfolder_mounts=session_data.vfolder_mounts,
                environ=session_data.environ,
                tag=session_data.tag,
                starts_at=session_data.starts_at,
                batch_timeout=session_data.batch_timeout,
                callback_url=session_data.callback_url,
                images=session_data.images,
                network_type=session_data.network_type,
                network_id=session_data.network_id,
                bootstrap_script=session_data.bootstrap_script,
                use_host_network=session_data.use_host_network,
                timeout=session_data.timeout,
            )

            # Create kernel rows
            kernels = []
            for kernel in session_data.kernels:
                kernel_row = KernelRow(
                    id=kernel.id,
                    session_id=kernel.session_id,
                    session_creation_id=kernel.session_creation_id,
                    session_name=kernel.session_name,
                    session_type=kernel.session_type,
                    cluster_mode=kernel.cluster_mode,
                    cluster_size=kernel.cluster_size,
                    cluster_role=kernel.cluster_role,
                    cluster_idx=kernel.cluster_idx,
                    local_rank=kernel.local_rank,
                    cluster_hostname=kernel.cluster_hostname,
                    agent=kernel.agent,
                    scaling_group=kernel.scaling_group,
                    domain_name=kernel.domain_name,
                    group_id=kernel.group_id,
                    user_uuid=kernel.user_uuid,
                    access_key=kernel.access_key,
                    image=kernel.image,
                    architecture=kernel.architecture,
                    registry=kernel.registry,
                    tag=kernel.tag,
                    starts_at=kernel.starts_at,
                    status=KernelStatus[kernel.status],
                    status_history=kernel.status_history,
                    occupied_slots=kernel.occupied_slots,
                    requested_slots=kernel.requested_slots,
                    occupied_shares=kernel.occupied_shares,
                    resource_opts=kernel.resource_opts,
                    environ=kernel.environ,
                    bootstrap_script=kernel.bootstrap_script,
                    startup_command=kernel.startup_command,
                    internal_data=kernel.internal_data,
                    callback_url=kernel.callback_url,
                    mounts=kernel.mounts,
                    vfolder_mounts=kernel.vfolder_mounts,
                    preopen_ports=kernel.preopen_ports,
                    use_host_network=kernel.use_host_network,
                    repl_in_port=kernel.repl_in_port,
                    repl_out_port=kernel.repl_out_port,
                    stdin_port=kernel.stdin_port,
                    stdout_port=kernel.stdout_port,
                    uid=kernel.uid,
                    main_gid=kernel.main_gid,
                    gids=kernel.gids,
                )
                kernels.append(kernel_row)

            # Add session and kernels to database
            db_sess.add(session)
            db_sess.add_all(kernels)
            await db_sess.flush()

            # Add session dependencies if any
            if matched_dependency_ids:
                dependency_rows = [
                    SessionDependencyRow(
                        session_id=session_data.id,
                        depends_on=depend_id,
                    )
                    for depend_id in matched_dependency_ids
                ]
                db_sess.add_all(dependency_rows)

            await db_sess.commit()

        return session_data.id

    async def fetch_session_creation_data(
        self,
        spec: "SessionCreationSpec",
        scaling_group_name: str,
        storage_manager,
        allowed_vfolder_types: list[str],
    ) -> "SessionCreationContext":
        """
        Fetch all data needed for session creation in a single DB session.

        Args:
            spec: Session creation specification
            scaling_group_name: Name of the scaling group
            storage_manager: Storage session manager
            allowed_vfolder_types: Allowed vfolder types from config

        Returns:
            SessionCreationContext with all required data
        """
        async with self._db.begin_readonly_session() as db_sess:
            # Collect all unique image references from kernel specs
            image_refs = []
            for kernel_spec in spec.kernel_specs:
                image_ref = kernel_spec.get("image_ref")
                if image_ref and isinstance(image_ref, ImageRef):
                    if image_ref.canonical not in image_refs:
                        image_refs.append(image_ref.canonical)

            # Fetch all data using private methods that reuse the session
            network_info = await self._get_scaling_group_network_info(db_sess, scaling_group_name)
            allowed_groups = await self._query_allowed_scaling_groups(
                db_sess,
                spec.user_scope.domain_name,
                str(spec.user_scope.group_id),
                spec.access_key,
            )
            image_infos = await self._resolve_image_info(db_sess, image_refs)

            # Prepare mount-related data
            requested_mounts = spec.creation_spec.get("mounts") or []
            requested_mount_ids = spec.creation_spec.get("mount_ids") or []
            requested_mount_map = spec.creation_spec.get("mount_map") or {}
            requested_mount_id_map = spec.creation_spec.get("mount_id_map") or {}
            requested_mount_options = spec.creation_spec.get("mount_options") or {}

            combined_mounts = requested_mounts + requested_mount_ids
            combined_mount_map = {**requested_mount_map, **requested_mount_id_map}

            # Fetch vfolder mounts
            vfolder_mounts = await self._fetch_vfolder_mounts(
                db_sess,
                storage_manager,
                allowed_vfolder_types,
                spec.user_scope,
                spec.resource_policy,
                combined_mounts,
                combined_mount_map,
                requested_mount_options,
            )

            # Fetch dotfile data
            dotfile_data = await self._fetch_dotfiles(
                db_sess,
                spec.user_scope,
                spec.access_key,
                vfolder_mounts,
            )

            return SessionCreationContext(
                scaling_group_network=network_info,
                allowed_scaling_groups=allowed_groups,
                image_infos=image_infos,
                vfolder_mounts=vfolder_mounts,
                dotfile_data=dotfile_data,
            )

    async def fetch_session_creation_context(
        self,
        spec: "SessionCreationSpec",
        scaling_group_name: str,
    ) -> "SessionCreationContext":
        """
        Legacy method for backward compatibility.
        Use fetch_session_creation_data instead.
        """
        async with self._db.begin_readonly_session() as db_sess:
            # Collect all unique image references from kernel specs
            image_refs = []
            for kernel_spec in spec.kernel_specs:
                image_ref = kernel_spec.get("image_ref")
                if image_ref and isinstance(image_ref, ImageRef):
                    if image_ref.canonical not in image_refs:
                        image_refs.append(image_ref.canonical)

            # Fetch all data using private methods that reuse the session
            network_info = await self._get_scaling_group_network_info(db_sess, scaling_group_name)
            allowed_groups = await self._query_allowed_scaling_groups(
                db_sess,
                spec.user_scope.domain_name,
                str(spec.user_scope.group_id),
                spec.access_key,
            )
            image_infos = await self._resolve_image_info(db_sess, image_refs)

            return SessionCreationContext(
                scaling_group_network=network_info,
                allowed_scaling_groups=allowed_groups,
                image_infos=image_infos,
                vfolder_mounts=[],
                dotfile_data={},
            )

    async def _get_scaling_group_network_info(
        self, db_sess: SASession, scaling_group_name: str
    ) -> "ScalingGroupNetworkInfo":
        """
        Get network configuration from scaling group.

        Args:
            db_sess: Database session
            scaling_group_name: Name of the scaling group

        Returns:
            ScalingGroupNetworkInfo with network configuration
        """
        query = sa.select(
            ScalingGroupRow.use_host_network,
            ScalingGroupRow.wsproxy_addr,
        ).where(ScalingGroupRow.name == scaling_group_name)

        result = await db_sess.execute(query)
        row = result.one_or_none()

        if not row:
            raise ValueError(f"Scaling group {scaling_group_name} not found")

        return ScalingGroupNetworkInfo(
            use_host_network=row.use_host_network,
            wsproxy_addr=row.wsproxy_addr,
        )

    async def _resolve_image_info(
        self, db_sess: SASession, image_refs: list[str]
    ) -> dict[str, "ImageInfo"]:
        """
        Resolve image references to image information.

        Args:
            db_sess: Database session
            image_refs: List of image references to resolve

        Returns:
            Dictionary mapping image reference to ImageInfo
        """
        from ai.backend.manager.models.image import ImageAlias

        image_infos = {}
        for image_ref_str in image_refs:
            # Use ImageAlias which accepts just a string
            image_alias = ImageAlias(image_ref_str)
            image_row = await ImageRow.resolve(db_sess, [image_alias])
            if image_row:
                image_infos[image_ref_str] = ImageInfo(
                    canonical=image_row.canonical,
                    architecture=image_row.architecture,
                    registry=image_row.registry,
                    labels=image_row.labels,
                    resource_spec=image_row.resource_spec,
                )
        return image_infos

    async def query_allowed_scaling_groups(
        self,
        domain_name: str,
        group_id: str,
        access_key: str,
    ) -> list["AllowedScalingGroup"]:
        """
        Query allowed scaling groups for a user (public method for external use).
        """
        async with self._db.begin_readonly_session() as db_sess:
            return await self._query_allowed_scaling_groups(
                db_sess, domain_name, group_id, access_key
            )

    async def _fetch_vfolder_mounts(
        self,
        db_sess: SASession,
        storage_manager,
        allowed_vfolder_types: list[str],
        user_scope,
        resource_policy: dict[str, Any],
        combined_mounts: list[str],
        combined_mount_map: dict[str | UUID, str],
        requested_mount_options: dict[str | UUID, Any],
    ) -> list[VFolderMount]:
        """
        Fetch vfolder mounts for the session using existing DB session.
        """
        from ai.backend.manager.models import prepare_vfolder_mounts

        # Convert the async session to sync connection for legacy code
        conn = db_sess.bind

        vfolder_mounts = await prepare_vfolder_mounts(
            conn,
            storage_manager,
            allowed_vfolder_types,
            user_scope,
            resource_policy,
            combined_mounts,
            combined_mount_map,
            requested_mount_options,
        )
        return list(vfolder_mounts)

    async def _fetch_dotfiles(
        self,
        db_sess: SASession,
        user_scope,
        access_key: AccessKey,
        vfolder_mounts: list,
    ) -> dict[str, Any]:
        """
        Fetch dotfile data for the session using existing DB session.
        """
        from ai.backend.manager.models import prepare_dotfiles

        # Convert the async session to sync connection for legacy code
        conn = db_sess.bind

        dotfile_data = await prepare_dotfiles(
            conn,
            user_scope,
            access_key,
            vfolder_mounts,
        )
        return dict(dotfile_data)

    async def prepare_vfolder_mounts(
        self,
        storage_manager,
        allowed_vfolder_types: list[str],
        user_scope,
        resource_policy: dict[str, Any],
        combined_mounts: list[str],
        combined_mount_map: dict[str | UUID, str],
        requested_mount_options: dict[str | UUID, Any],
    ) -> list[VFolderMount]:
        """
        Prepare vfolder mounts for the session.
        """
        from ai.backend.manager.models import prepare_vfolder_mounts

        async with self._db.begin_readonly() as conn:
            vfolder_mounts = await prepare_vfolder_mounts(
                conn,
                storage_manager,
                allowed_vfolder_types,
                user_scope,
                resource_policy,
                combined_mounts,
                combined_mount_map,
                requested_mount_options,
            )
        return list(vfolder_mounts)

    async def prepare_dotfiles(
        self,
        user_scope,
        access_key: AccessKey,
        vfolder_mounts: list,
    ) -> dict[str, Any]:
        """
        Prepare dotfile data for the session.
        """

        from ai.backend.manager.models import prepare_dotfiles

        async with self._db.begin_readonly() as conn:
            dotfile_data = await prepare_dotfiles(
                conn,
                user_scope,
                access_key,
                vfolder_mounts,
            )
        return dict(dotfile_data)

    async def _query_allowed_scaling_groups(
        self,
        db_sess: SASession,
        domain_name: str,
        group_id: str,
        access_key: str,
    ) -> list["AllowedScalingGroup"]:
        """
        Query allowed scaling groups for the given user/group.

        Args:
            db_sess: Database session
            domain_name: Domain name
            group_id: Group ID
            access_key: Access key

        Returns:
            List of AllowedScalingGroup objects
        """
        allowed_sgroups = await query_allowed_sgroups(
            db_sess,
            domain_name,
            group_id,
            access_key,
        )

        return [
            AllowedScalingGroup(
                name=sg.name,
                is_private=sg.is_private,
            )
            for sg in allowed_sgroups
        ]

    async def allocate_sessions(self, allocation_batch: AllocationBatch) -> None:
        """
        Allocate resources for sessions in the batch.
        Updates session/kernel statuses and syncs agent occupied slots.

        This method handles:
        1. Pre-fetching all necessary session and kernel data
        2. Processing successful allocations by updating session/kernel statuses
        3. Processing scheduling failures by updating their status data
        4. Syncing agent occupied slots to AgentRow
        """
        # Collect all affected agents
        affected_agent_ids: set[AgentId] = set()

        for allocation in allocation_batch.allocations:
            for kernel_alloc in allocation.kernel_allocations:
                if kernel_alloc.agent_id:
                    affected_agent_ids.add(kernel_alloc.agent_id)

        async with self._db.begin_session() as db_sess:
            # Process successful allocations
            for allocation in allocation_batch.allocations:
                try:
                    await self._allocate_single_session(db_sess, allocation)
                except Exception as e:
                    log.error(
                        "Error allocating session {}: {}",
                        allocation.session_id,
                        e,
                    )
                    # Continue with next session allocation

            # Process scheduling failures in the same transaction
            if allocation_batch.failures:
                # Pre-fetch session rows only for failure status updates (needed for retry counts)
                failure_session_ids = {failure.session_id for failure in allocation_batch.failures}
                session_cache = await self._prefetch_session_rows(db_sess, failure_session_ids)

                for failure in allocation_batch.failures:
                    try:
                        await self._update_session_failure_status(db_sess, session_cache, failure)
                    except SessionNotFound as e:
                        log.warning(
                            "Session {} not found for failure status update: {}",
                            failure.session_id,
                            e,
                        )
                        # Continue with next failure update
                    except Exception as e:
                        log.error(
                            "Unexpected error updating failure status for session {}: {}",
                            failure.session_id,
                            e,
                        )
                        # Continue with next failure update

            # Sync agent occupied slots to AgentRow
            # This must be done within the same transaction to ensure consistency
            await self._sync_agent_occupied_slots(db_sess, affected_agent_ids)

    async def _prefetch_session_rows(
        self, db_sess: SASession, session_ids: set[SessionId]
    ) -> SessionRowCache:
        """Pre-fetch all session rows for the given session IDs."""
        if not session_ids:
            return SessionRowCache({})

        query = sa.select(SessionRow).where(SessionRow.id.in_(session_ids))
        result = await db_sess.execute(query)
        sessions = result.scalars().all()

        prefetched = {session.id: session for session in sessions}
        return SessionRowCache(prefetched)

    async def _allocate_single_session(
        self,
        db_sess: SASession,
        allocation: SessionAllocation,
    ) -> None:
        """
        Allocate resources for a single session.
        Updates session first, then its kernels.
        Only updates if session is in PENDING status.
        """
        now = datetime.now(tzutc())

        # Update session status and metadata first
        session_update_query = (
            sa.update(SessionRow)
            .where(
                sa.and_(
                    SessionRow.id == allocation.session_id,
                    SessionRow.status == SessionStatus.PENDING,
                )
            )
            .values(
                status=SessionStatus.SCHEDULED,
                status_info="scheduled",
                status_data={},
                status_history=sql_json_merge(
                    SessionRow.status_history,
                    (),
                    {SessionStatus.SCHEDULED.name: now.isoformat()},
                ),
                scaling_group_name=allocation.scaling_group,
                agent_ids=allocation.unique_agent_ids(),
            )
        )
        result = await db_sess.execute(session_update_query)

        # Check if session was actually updated
        if result.rowcount == 0:
            log.warning(
                "Session {} was not in PENDING status, skipping allocation",
                allocation.session_id,
            )
            return

        # Update kernels only if session was successfully updated
        for kernel_alloc in allocation.kernel_allocations:
            await db_sess.execute(
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.id == kernel_alloc.kernel_id,
                        KernelRow.status == KernelStatus.PENDING,
                    )
                )
                .values(
                    status=KernelStatus.SCHEDULED,
                    status_info="scheduled",
                    status_data={},
                    status_changed=now,
                    status_history=sql_json_merge(
                        KernelRow.status_history,
                        (),
                        {KernelStatus.SCHEDULED.name: now.isoformat()},
                    ),
                    agent=kernel_alloc.agent_id,
                    agent_addr=kernel_alloc.agent_addr,
                    scaling_group=kernel_alloc.scaling_group,
                )
            )

    async def _update_session_failure_status(
        self, db_sess: SASession, session_cache: SessionRowCache, failure: SchedulingFailure
    ) -> None:
        """
        Update session status for a scheduling failure.
        Increments retries count from existing status_data.
        Only updates if session is in PENDING status.
        """
        # Get existing session to retrieve current retries count
        session_row = await session_cache.get_or_fetch(db_sess, failure.session_id)

        # Get current retries count from existing status_data
        current_status_data = session_row.status_data or {}
        scheduler_data = current_status_data.get("scheduler", {})
        current_retries = scheduler_data.get("retries", 0)

        # Prepare status data using the failure's to_status_data method
        status_data = failure.to_status_data(current_retries)

        # Update session status data first
        session_query = (
            sa.update(SessionRow)
            .where(
                sa.and_(
                    SessionRow.id == failure.session_id,
                    SessionRow.status == SessionStatus.PENDING,
                )
            )
            .values(
                status_info=failure.msg,
                status_data=sql_json_merge(
                    SessionRow.status_data,
                    ("scheduler",),
                    obj=status_data,
                ),
            )
        )
        result = await db_sess.execute(session_query)

        # Check if session was actually updated
        if result.rowcount == 0:
            log.warning(
                "Session {} was not in PENDING status, skipping failure status update",
                failure.session_id,
            )
            return

        # Update kernel status data only if session was updated
        kernel_query = (
            sa.update(KernelRow)
            .where(
                sa.and_(
                    KernelRow.session_id == failure.session_id,
                    KernelRow.status == KernelStatus.PENDING,
                )
            )
            .values(
                status_data=sql_json_merge(
                    KernelRow.status_data,
                    ("scheduler",),
                    obj=status_data,
                ),
            )
        )
        await db_sess.execute(kernel_query)

    async def batch_update_terminated_status(
        self, session_results: list[SessionTerminationResult]
    ) -> None:
        """
        Batch update kernel and session statuses to TERMINATED for successful terminations.
        Syncs agent occupied slots after termination.

        :param session_results: List of session termination results with nested kernel results
        """
        if not session_results:
            return

        now = datetime.now(tzutc())

        # Collect affected agents
        affected_agent_ids: set[AgentId] = set()

        for session_result in session_results:
            for kernel in session_result.kernel_results:
                if kernel.success and kernel.agent_id:
                    affected_agent_ids.add(kernel.agent_id)

        async with self._db.begin_session() as db_sess:
            # Process each session's results
            for session_result in session_results:
                # Collect successful kernel IDs
                successful_kernel_ids = []
                for kernel in session_result.kernel_results:
                    if kernel.success:
                        successful_kernel_ids.append(kernel.kernel_id)

                # Update successful kernels to TERMINATED (only if currently TERMINATING)
                if successful_kernel_ids:
                    kernel_stmt = (
                        sa.update(KernelRow)
                        .where(
                            sa.and_(
                                KernelRow.id.in_(successful_kernel_ids),
                                KernelRow.status == KernelStatus.TERMINATING,
                            )
                        )
                        .values(
                            status=KernelStatus.TERMINATED,
                            status_info=session_result.reason,
                            status_changed=now,
                            terminated_at=now,
                            status_history=sql_json_merge(
                                KernelRow.status_history,
                                (),
                                {KernelStatus.TERMINATED.name: now.isoformat()},
                            ),
                        )
                    )
                    await db_sess.execute(kernel_stmt)

                # Update session if all kernels succeeded (only if currently TERMINATING)
                if session_result.should_terminate_session:
                    session_stmt = (
                        sa.update(SessionRow)
                        .where(
                            sa.and_(
                                SessionRow.id == session_result.session_id,
                                SessionRow.status == SessionStatus.TERMINATING,
                            )
                        )
                        .values(
                            status=SessionStatus.TERMINATED,
                            status_info=session_result.reason,
                            status_history=sql_json_merge(
                                SessionRow.status_history,
                                (),
                                {SessionStatus.TERMINATED.name: now.isoformat()},
                            ),
                            terminated_at=now,
                        )
                    )
                    await db_sess.execute(session_stmt)

            # Sync agent occupied slots to AgentRow
            # This must be done within the same transaction to ensure consistency
            await self._sync_agent_occupied_slots(db_sess, affected_agent_ids)

    async def sync_agent_occupied_slots(self, agent_ids: Optional[set[AgentId]] = None) -> None:
        """
        Public method to sync agent occupied slots to AgentRow.
        If agent_ids is None, syncs all agents.

        :param agent_ids: Optional set of agent IDs to sync, None for all agents
        """
        async with self._db.begin_session() as db_sess:
            # If no specific agents provided, get all agents
            if agent_ids is None:
                query = sa.select(AgentRow.id)
                result = await db_sess.execute(query)
                agent_ids = {row.id for row in result}

            await self._sync_agent_occupied_slots(db_sess, agent_ids)

    async def _sync_agent_occupied_slots(self, db_sess: SASession, agent_ids: set[AgentId]) -> None:
        """
        Sync agent occupied slots from kernels to AgentRow.occupied_slots.
        Calculates the sum of occupied_slots from all active kernels per agent
        and updates AgentRow accordingly.

        :param db_sess: Existing database session
        :param agent_ids: Set of agent IDs to sync
        """
        if not agent_ids:
            return

        # Get current occupied slots per agent from kernels
        agent_occupied_slots = await self._calculate_agent_occupied_slots(db_sess, agent_ids)

        # Update each agent's occupied_slots in AgentRow
        for agent_id in agent_ids:
            occupied_slots = agent_occupied_slots.get(agent_id, ResourceSlot())

            update_stmt = (
                sa.update(AgentRow)
                .where(AgentRow.id == agent_id)
                .values(occupied_slots=occupied_slots)
            )
            await db_sess.execute(update_stmt)

    async def _calculate_agent_occupied_slots(
        self, db_sess: SASession, agent_ids: set[AgentId]
    ) -> Mapping[AgentId, ResourceSlot]:
        """
        Calculate current occupied slots for the given agents from database.
        Aggregates occupied_slots in Python since it's a custom ResourceSlot type.

        :param db_sess: Existing database session
        :param agent_ids: Set of agent IDs to calculate occupied slots for
        :return: Mapping of agent IDs to their occupied ResourceSlots
        """
        if not agent_ids:
            return {}

        # Initialize all agents with empty slots
        agent_slots: dict[AgentId, ResourceSlot] = {
            agent_id: ResourceSlot() for agent_id in agent_ids
        }

        # Query all kernels' occupied slots for affected agents
        # We need to aggregate in Python since occupied_slots is a custom type (JSONB)
        query = sa.select(
            KernelRow.agent,
            KernelRow.occupied_slots,
        ).where(
            sa.and_(
                KernelRow.agent.in_(agent_ids),
                KernelRow.status.in_(KernelStatus.resource_occupied_statuses()),
            )
        )

        result = await db_sess.execute(query)

        # Aggregate occupied slots per agent in Python
        for row in result:
            if row.agent and row.occupied_slots:
                agent_slots[row.agent] += row.occupied_slots

        return agent_slots

"""Database source for schedule repository operations."""

from __future__ import annotations

import logging
from collections import defaultdict
from contextlib import asynccontextmanager as actxmgr
from datetime import datetime
from typing import Any, AsyncIterator, Mapping, Optional, cast
from uuid import UUID

import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import load_only, selectinload, sessionmaker

from ai.backend.common.docker import ImageRef
from ai.backend.common.resource.types import TotalResourceData
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
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.image import ImageNotFound
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.exceptions import ErrorStatusInfo
from ai.backend.manager.models import (
    AgentRow,
    DefaultForUnspecified,
    DomainRow,
    GroupRow,
    ImageRow,
    KernelRow,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    ScalingGroupRow,
    SessionDependencyRow,
    SessionRow,
    UserRow,
    query_allowed_sgroups,
)
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    sql_json_merge,
)
from ai.backend.manager.sokovan.scheduler.results import ScheduledSessionData
from ai.backend.manager.sokovan.scheduler.types import (
    AgentOccupancy,
    AllocationBatch,
    ImageConfigData,
    KernelBindingData,
    KernelCreationInfo,
    KernelTransitionData,
    KeypairOccupancy,
    KeyPairResourcePolicy,
    ResourceOccupancySnapshot,
    SchedulingFailure,
    SessionAllocation,
    SessionDataForPull,
    SessionDataForStart,
    SessionDependencyInfo,
    SessionDependencySnapshot,
    SessionRunningData,
    SessionsForPullWithImages,
    SessionsForStartWithImages,
    SessionTransitionData,
    UserResourcePolicy,
)

from ..types.agent import AgentMeta
from ..types.base import SchedulingSpec
from ..types.scaling_group import ScalingGroupMeta
from ..types.scheduling import SchedulingData
from ..types.session import (
    KernelData,
    KernelTerminationResult,
    MarkTerminatingResult,
    PendingSessionData,
    PendingSessions,
    SessionTerminationResult,
    SweptSessionInfo,
    TerminatingKernelData,
    TerminatingKernelWithAgentData,
    TerminatingSessionData,
)
from ..types.session_creation import (
    AllowedScalingGroup,
    ContainerUserInfo,
    ImageInfo,
    ScalingGroupNetworkInfo,
    SessionCreationContext,
    SessionCreationSpec,
    SessionEnqueueData,
)
from ..types.snapshot import ResourcePolicies, SnapshotData
from .types import KeypairConcurrencyData, SessionRowCache

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

    @actxmgr
    async def _begin_readonly_read_committed(self) -> AsyncIterator[SAConnection]:
        """
        Begin a read-only connection with READ COMMITTED isolation level.
        """
        async with self._db.connect() as conn:
            # Set isolation level to READ COMMITTED
            conn_with_isolation = await conn.execution_options(
                isolation_level="READ COMMITTED",
                postgresql_readonly=True,
            )
            async with conn_with_isolation.begin():
                yield conn_with_isolation

    @actxmgr
    async def _begin_readonly_session_read_committed(self) -> AsyncIterator[SASession]:
        """
        Begin a read-only session with READ COMMITTED isolation level.
        """
        async with self._db.connect() as conn:
            # Set isolation level to READ COMMITTED and readonly mode
            conn_with_isolation = await conn.execution_options(
                isolation_level="READ COMMITTED",
                postgresql_readonly=True,
            )
            async with conn_with_isolation.begin():
                # Configure session factory with the connection
                sess_factory = sessionmaker(
                    bind=conn_with_isolation,
                    class_=SASession,
                    expire_on_commit=False,
                )
                session = sess_factory()
                yield session

    @actxmgr
    async def _begin_session_read_committed(self) -> AsyncIterator[SASession]:
        """
        Begin a read-write session with READ COMMITTED isolation level.
        """
        async with self._db.connect() as conn:
            # Set isolation level to READ COMMITTED
            conn_with_isolation = await conn.execution_options(isolation_level="READ COMMITTED")
            async with conn_with_isolation.begin():
                # Configure session factory with the connection
                sess_factory = sessionmaker(
                    bind=conn_with_isolation,
                    class_=SASession,
                    expire_on_commit=False,
                )
                session = sess_factory()
                yield session
                await session.commit()

    async def get_scheduling_data(self, scaling_group: str, spec: SchedulingSpec) -> SchedulingData:
        """
        Fetch all scheduling data from database in a single session.
        Raises ScalingGroupNotFound if scaling group doesn't exist.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
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
                SessionRow.designated_agent_ids,
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
                    KernelRow.status == KernelStatus.PENDING,
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
                    designated_agent_ids=row.designated_agent_ids,
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
        # Fetch kernel occupancy data for both occupied (RUNNING, TERMINATING) and requested (SCHEDULED, PREPARING, etc.) statuses
        # resource_occupied_statuses: RUNNING, TERMINATING - use occupied_slots
        # resource_requested_statuses: SCHEDULED, PREPARING, PULLING, PREPARED, CREATING - use requested_slots
        all_resource_statuses = (
            KernelStatus.resource_occupied_statuses() | KernelStatus.resource_requested_statuses()
        )
        occupancy_result = await db_sess.execute(
            sa.select(
                KernelRow.session_id,
                KernelRow.access_key,
                KernelRow.user_uuid,
                KernelRow.group_id,
                KernelRow.domain_name,
                KernelRow.agent,
                KernelRow.occupied_slots,
                KernelRow.requested_slots,
                KernelRow.status,
                KernelRow.session_type,
            ).where(
                sa.and_(
                    KernelRow.status.in_(all_resource_statuses),
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
            kernel_status = cast(KernelStatus, row.status)

            # Determine which slots to use based on kernel status
            # For RUNNING/TERMINATING: use occupied_slots (actual allocated resources)
            # For SCHEDULED/PREPARING/etc: use requested_slots (estimated allocation)
            if kernel_status in KernelStatus.resource_occupied_statuses():
                slots_to_use = row.occupied_slots
            else:  # kernel_status in resource_requested_statuses
                slots_to_use = row.requested_slots

            # Only accumulate resource slots for non-private sessions
            if not session_type.is_private():
                occupancy_by_keypair[row.access_key].occupied_slots += slots_to_use
                occupancy_by_user[row.user_uuid] += slots_to_use
                occupancy_by_group[row.group_id] += slots_to_use
                occupancy_by_domain[row.domain_name] += slots_to_use

                # Track regular sessions
                sessions_by_keypair[row.access_key].add(row.session_id)
            else:
                # Track SFTP sessions
                sftp_sessions_by_keypair[row.access_key].add(row.session_id)

            if row.agent:
                occupancy_by_agent[row.agent].occupied_slots += slots_to_use
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
                    max_concurrent_sessions=row.max_concurrent_sessions
                    if row.max_concurrent_sessions and row.max_concurrent_sessions > 0
                    else None,
                    max_concurrent_sftp_sessions=row.max_concurrent_sftp_sessions
                    if row.max_concurrent_sftp_sessions and row.max_concurrent_sftp_sessions > 0
                    else None,
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

        async with self._begin_session_read_committed() as db_sess:
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
        """Mark terminatable sessions and their kernels as terminating."""
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
                    SessionRow.status.in_(SessionStatus.terminatable_statuses()),
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
                .where(
                    sa.and_(
                        KernelRow.session_id.in_(terminating_sessions),
                        KernelRow.status.in_(KernelStatus.terminatable_statuses()),
                    )
                )
            )

        return terminating_sessions

    async def get_schedulable_scaling_groups(self) -> list[str]:
        """Get list of scaling groups that have schedulable agents."""
        async with self._begin_readonly_session_read_committed() as session:
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
        async with self._begin_readonly_session_read_committed() as session:
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

    async def get_terminating_kernels_with_lost_agents(
        self,
    ) -> list[TerminatingKernelWithAgentData]:
        """
        Fetch kernels in TERMINATING state that have lost or missing agents.

        This includes kernels where:
        - agent_id is None (never assigned)
        - agent status is unavailable (LOST or TERMINATED)
        """
        async with self._begin_readonly_session_read_committed() as session:
            query = (
                sa.select(
                    KernelRow.id,
                    KernelRow.session_id,
                    KernelRow.status,
                    KernelRow.agent,
                    AgentRow.status.label("agent_status"),
                )
                .select_from(KernelRow)
                .outerjoin(AgentRow, KernelRow.agent == AgentRow.id)
                .where(
                    KernelRow.status == KernelStatus.TERMINATING,
                    sa.or_(
                        KernelRow.agent.is_(None),  # No agent assigned
                        AgentRow.status.in_(
                            AgentStatus.unavailable_statuses()
                        ),  # Agent unavailable
                    ),
                )
            )
            result = await session.execute(query)
            rows = result.fetchall()

            return [
                TerminatingKernelWithAgentData(
                    kernel_id=str(row.id),
                    session_id=row.session_id,
                    status=row.status,
                    agent_id=row.agent,
                    agent_status=str(row.agent_status) if row.agent_status else None,
                )
                for row in rows
            ]

    async def get_pending_timeout_sessions(self) -> list[SweptSessionInfo]:
        """Get sessions that have exceeded their pending timeout."""
        now = datetime.now(tzutc())
        timed_out_sessions: list[SweptSessionInfo] = []

        async with self._begin_readonly_session_read_committed() as db_sess:
            query = (
                sa.select(
                    SessionRow.id,
                    SessionRow.creation_id,
                    SessionRow.access_key,
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
                            access_key=row.access_key,
                        )
                    )

        return timed_out_sessions

    async def enqueue_session(
        self,
        session_data: SessionEnqueueData,
    ) -> SessionId:
        """
        Create new session and kernel records in PENDING status.

        Args:
            session_data: Prepared session data with kernels and dependencies

        Returns:
            SessionId: The ID of the created session
        """
        async with self._begin_session_read_committed() as db_sess:
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
                designated_agent_ids=session_data.designated_agent_list,
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
        spec: SessionCreationSpec,
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
        async with self._begin_readonly_session_read_committed() as db_sess:
            # Collect all unique image references from kernel specs
            image_refs: list[ImageRef] = []
            for kernel_spec in spec.kernel_specs:
                image_ref = kernel_spec.get("image_ref")
                if image_ref and isinstance(image_ref, ImageRef):
                    # Keep the full ImageRef object, not just the canonical string
                    if not any(ref.canonical == image_ref.canonical for ref in image_refs):
                        image_refs.append(image_ref)

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

            # Fetch user container info
            user_container_info = await self._fetch_user_container_info(
                db_sess,
                spec.user_scope.user_uuid,
            )

            return SessionCreationContext(
                scaling_group_network=network_info,
                allowed_scaling_groups=allowed_groups,
                image_infos=image_infos,
                vfolder_mounts=vfolder_mounts,
                dotfile_data=dotfile_data,
                container_user_info=user_container_info,
            )

    async def fetch_session_creation_context(
        self,
        spec: SessionCreationSpec,
        scaling_group_name: str,
    ) -> SessionCreationContext:
        """
        Legacy method for backward compatibility.
        Use fetch_session_creation_data instead.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            # Collect all unique image references from kernel specs
            image_refs: list[ImageRef] = []
            for kernel_spec in spec.kernel_specs:
                image_ref = kernel_spec.get("image_ref")
                if image_ref and isinstance(image_ref, ImageRef):
                    # Keep the full ImageRef object, not just the canonical string
                    if not any(ref.canonical == image_ref.canonical for ref in image_refs):
                        image_refs.append(image_ref)

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
                container_user_info=ContainerUserInfo(),
            )

    async def _get_scaling_group_network_info(
        self, db_sess: SASession, scaling_group_name: str
    ) -> ScalingGroupNetworkInfo:
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
        self, db_sess: SASession, image_refs: list[ImageRef]
    ) -> dict[str, "ImageInfo"]:
        """
        Resolve image references to image information.

        Args:
            db_sess: Database session
            image_refs: List of ImageRef objects to resolve

        Returns:
            Dictionary mapping image canonical reference to ImageInfo
        """
        image_infos = {}
        for image_ref in image_refs:
            # Use the ImageRef object directly
            image_row = await ImageRow.resolve(db_sess, [image_ref])
            if image_row:
                image_infos[image_ref.canonical] = ImageInfo(
                    canonical=image_row.name,  # 'name' is the canonical reference in ImageRow
                    architecture=image_row.architecture,
                    registry=image_row.registry,
                    labels=image_row.labels,
                    resource_spec=cast(dict[str, Any], image_row.resources),  # Cast to match type
                )
        return image_infos

    async def query_allowed_scaling_groups(
        self,
        domain_name: str,
        group_id: str,
        access_key: str,
    ) -> list[AllowedScalingGroup]:
        """
        Query allowed scaling groups for a user (public method for external use).
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
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

    async def _fetch_user_container_info(
        self,
        db_sess: SASession,
        user_uuid: UUID,
    ) -> ContainerUserInfo:
        """
        Fetch user container UID/GID information.
        """
        user_row: UserRow | None = await db_sess.scalar(
            sa.select(UserRow).where(UserRow.uuid == user_uuid)
        )
        if user_row is None:
            return ContainerUserInfo()
        return ContainerUserInfo(
            uid=user_row.container_uid,
            main_gid=user_row.container_main_gid,
            supplementary_gids=user_row.container_gids,
        )

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

        async with self._begin_readonly_read_committed() as conn:
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

        async with self._begin_readonly_read_committed() as conn:
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
    ) -> list[AllowedScalingGroup]:
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
            UUID(group_id),
            access_key,
        )

        return [
            AllowedScalingGroup(
                name=sg.name,
                is_private=not sg.is_public,  # Convert is_public to is_private
                scheduler_opts=sg.scheduler_opts,
            )
            for sg in allowed_sgroups
        ]

    async def allocate_sessions(
        self, allocation_batch: AllocationBatch
    ) -> list[ScheduledSessionData]:
        """
        Allocate resources for sessions in the batch.
        Updates session/kernel statuses and syncs agent occupied slots.

        This method handles:
        1. Pre-fetching all necessary session and kernel data
        2. Processing successful allocations by updating session/kernel statuses
        3. Processing scheduling failures by updating their status data
        4. Syncing agent occupied slots to AgentRow

        Returns:
            List of ScheduledSessionData for allocated sessions
        """
        # Collect all affected agents
        affected_agent_ids: set[AgentId] = set()
        scheduled_sessions: list[ScheduledSessionData] = []

        for allocation in allocation_batch.allocations:
            for kernel_alloc in allocation.kernel_allocations:
                if kernel_alloc.agent_id:
                    affected_agent_ids.add(kernel_alloc.agent_id)

        async with self._begin_session_read_committed() as db_sess:
            # First, fetch session data to get creation_id and access_key
            session_ids = {alloc.session_id for alloc in allocation_batch.allocations}
            if session_ids:
                query = sa.select(
                    SessionRow.id, SessionRow.creation_id, SessionRow.access_key
                ).where(SessionRow.id.in_(session_ids))
                result = await db_sess.execute(query)
                session_data_map = {row.id: (row.creation_id, row.access_key) for row in result}

                # Create SessionEventData for each allocated session
                for allocation in allocation_batch.allocations:
                    if session_data := session_data_map.get(allocation.session_id):
                        creation_id, access_key = session_data
                        scheduled_sessions.append(
                            ScheduledSessionData(
                                session_id=allocation.session_id,
                                creation_id=creation_id,
                                access_key=access_key,
                                reason="triggered-by-scheduler",
                            )
                        )

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

        return scheduled_sessions

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

        async with self._begin_session_read_committed() as db_sess:
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

    async def batch_update_kernels_terminated(
        self,
        kernel_results: list[KernelTerminationResult],
        reason: str,
    ) -> None:
        """
        Batch update kernel statuses to TERMINATED without updating session status.
        Used for cleanup operations where kernels need to be marked terminated
        but session state management is handled separately.

        :param kernel_results: List of kernel termination results
        :param reason: Termination reason to record in status_info
        """
        if not kernel_results:
            return

        now = datetime.now(tzutc())

        # Collect successful kernel IDs
        successful_kernel_ids = []

        for kernel in kernel_results:
            if kernel.success:
                successful_kernel_ids.append(kernel.kernel_id)

        if not successful_kernel_ids:
            return

        async with self._begin_session_read_committed() as db_sess:
            # Update successful kernels to TERMINATED (only if currently TERMINATING)
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
                    status_info=reason,
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

    async def sync_agent_occupied_slots(self, agent_ids: Optional[set[AgentId]] = None) -> None:
        """
        Public method to sync agent occupied slots to AgentRow.
        If agent_ids is None, syncs all agents.

        :param agent_ids: Optional set of agent IDs to sync, None for all agents
        """
        async with self._begin_session_read_committed() as db_sess:
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

        # Query all kernels' slots for affected agents
        # Include both resource_occupied_statuses and resource_requested_statuses
        all_resource_statuses = (
            KernelStatus.resource_occupied_statuses() | KernelStatus.resource_requested_statuses()
        )
        query = sa.select(
            KernelRow.agent,
            KernelRow.occupied_slots,
            KernelRow.requested_slots,
            KernelRow.status,
        ).where(
            sa.and_(
                KernelRow.agent.in_(agent_ids),
                KernelRow.status.in_(all_resource_statuses),
            )
        )

        result = await db_sess.execute(query)

        # Aggregate slots per agent in Python
        for row in result:
            if row.agent:
                kernel_status = cast(KernelStatus, row.status)
                # Use occupied_slots for RUNNING/TERMINATING, requested_slots for pre-running states
                if kernel_status in KernelStatus.resource_occupied_statuses():
                    slots_to_use = row.occupied_slots
                else:  # kernel_status in resource_requested_statuses
                    slots_to_use = row.requested_slots

                if slots_to_use:
                    agent_slots[row.agent] += slots_to_use

        return agent_slots

    async def update_kernel_status_pulling(self, kernel_id: UUID, reason: str) -> bool:
        """
        Update kernel status to PULLING when pulling image.
        Uses UPDATE WHERE to ensure atomic state transition.

        :param kernel_id: Kernel ID to update
        :param reason: The reason for status change
        :return: True if update was successful, False otherwise
        """
        now = datetime.now(tzutc())

        async with self._begin_session_read_committed() as db_sess:
            stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.id == kernel_id,
                        KernelRow.status == KernelStatus.SCHEDULED,
                    )
                )
                .values(
                    status=KernelStatus.PULLING,
                    status_info=reason,
                    status_changed=now,
                    status_history=sql_json_merge(
                        KernelRow.status_history,
                        (),
                        {KernelStatus.PULLING.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)
            return result.rowcount > 0

    async def update_kernel_status_creating(self, kernel_id: UUID, reason: str) -> bool:
        """
        Update kernel status to CREATING when creating container.
        Uses UPDATE WHERE to ensure atomic state transition.

        :param kernel_id: Kernel ID to update
        :param reason: The reason for status change
        :return: True if update was successful, False otherwise
        """
        now = datetime.now(tzutc())

        async with self._begin_session_read_committed() as db_sess:
            stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.id == kernel_id,
                        KernelRow.status == KernelStatus.PULLING,
                    )
                )
                .values(
                    status=KernelStatus.CREATING,
                    status_info=reason,
                    status_changed=now,
                    status_history=sql_json_merge(
                        KernelRow.status_history,
                        (),
                        {KernelStatus.CREATING.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)
            return result.rowcount > 0

    async def update_kernel_status_running(
        self, kernel_id: UUID, reason: str, creation_info: KernelCreationInfo
    ) -> bool:
        """
        Update kernel status to RUNNING when container is started.
        Uses UPDATE WHERE to ensure atomic state transition.

        :param kernel_id: Kernel ID to update
        :param reason: The reason for status change
        :param creation_info: Container creation information as dataclass
        :return: True if update was successful, False otherwise
        """
        now = datetime.now(tzutc())

        async with self._begin_session_read_committed() as db_sess:
            stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.id == kernel_id,
                        KernelRow.status == KernelStatus.CREATING,
                    )
                )
                .values(
                    status=KernelStatus.RUNNING,
                    status_info=reason,
                    status_changed=now,
                    occupied_slots=creation_info.get_resource_allocations(),
                    container_id=creation_info.container_id,
                    attached_devices=creation_info.attached_devices,
                    repl_in_port=creation_info.repl_in_port,
                    repl_out_port=creation_info.repl_out_port,
                    stdin_port=creation_info.stdin_port,
                    stdout_port=creation_info.stdout_port,
                    service_ports=creation_info.service_ports,
                    kernel_host=creation_info.kernel_host,
                    status_history=sql_json_merge(
                        KernelRow.status_history,
                        (),
                        {KernelStatus.RUNNING.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)
            return result.rowcount > 0

    async def update_kernel_status_preparing(self, kernel_id: UUID) -> bool:
        """
        Update kernel status to PREPARING.
        Uses UPDATE WHERE to ensure atomic state transition.

        :param kernel_id: Kernel ID to update
        :return: True if update was successful, False otherwise
        """
        now = datetime.now(tzutc())

        async with self._begin_session_read_committed() as db_sess:
            stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.id == kernel_id,
                        KernelRow.status == KernelStatus.SCHEDULED,
                    )
                )
                .values(
                    status=KernelStatus.PREPARING,
                    status_info="preparing",
                    status_changed=now,
                    status_history=sql_json_merge(
                        KernelRow.status_history,
                        (),
                        {KernelStatus.PREPARING.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)
            return result.rowcount > 0

    async def update_kernel_status_cancelled(self, kernel_id: UUID, reason: str) -> bool:
        """
        Update kernel status to CANCELLED.
        Uses UPDATE WHERE to ensure atomic state transition.

        :param kernel_id: Kernel ID to update
        :param reason: Cancellation reason
        :return: True if update was successful, False otherwise
        """
        now = datetime.now(tzutc())

        async with self._begin_session_read_committed() as db_sess:
            stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.id == kernel_id,
                        KernelRow.status.in_([
                            KernelStatus.PENDING,
                            KernelStatus.SCHEDULED,
                            KernelStatus.PREPARING,
                            KernelStatus.PULLING,
                            KernelStatus.CREATING,
                        ]),
                    )
                )
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
            )
            result = await db_sess.execute(stmt)
            return result.rowcount > 0

    async def update_kernel_status_terminated(
        self, kernel_id: UUID, reason: str, exit_code: Optional[int] = None
    ) -> bool:
        """
        Update kernel status to TERMINATED.
        Uses UPDATE WHERE to ensure atomic state transition.

        :param kernel_id: Kernel ID to update
        :param reason: Termination reason
        :param exit_code: Process exit code
        :return: True if update was successful, False otherwise
        """
        now = datetime.now(tzutc())

        async with self._begin_session_read_committed() as db_sess:
            stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.id == kernel_id,
                        KernelRow.status == KernelStatus.TERMINATING,
                    )
                )
                .values(
                    status=KernelStatus.TERMINATED,
                    status_info=reason,
                    status_changed=now,
                    terminated_at=now,
                    status_data=sql_json_merge(
                        KernelRow.status_data,
                        ("kernel",),
                        {"exit_code": exit_code},
                    ),
                    status_history=sql_json_merge(
                        KernelRow.status_history,
                        (),
                        {KernelStatus.TERMINATED.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)
            return result.rowcount > 0

    async def update_kernel_heartbeat(self, kernel_id: UUID) -> bool:
        """
        Update kernel last_heartbeat timestamp.
        Uses UPDATE WHERE to ensure kernel exists and is running.

        :param kernel_id: Kernel ID to update
        :return: True if update was successful, False otherwise
        """
        now = datetime.now(tzutc())

        async with self._begin_session_read_committed() as db_sess:
            stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.id == kernel_id,
                        KernelRow.status == KernelStatus.RUNNING,
                    )
                )
                .values(
                    last_heartbeat=now,
                )
            )
            result = await db_sess.execute(stmt)
            return result.rowcount > 0

    async def update_kernels_to_pulling_for_image(
        self, agent_id: AgentId, image: str, image_ref: Optional[str] = None
    ) -> int:
        """
        Update kernel status from PREPARING to PULLING for the specified image on an agent.

        :param agent_id: The agent ID where kernels should be updated
        :param image: The image name to match kernels
        :param image_ref: Optional image reference (canonical format)
        :return: Number of kernels updated
        """
        async with self._begin_session_read_committed() as db_sess:
            now = datetime.now(tzutc())
            # Use image_ref if provided (canonical format), otherwise use image
            image_to_match = image_ref if image_ref else image
            # Find kernels on this agent with this image in PREPARING state
            stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.agent == agent_id,
                        KernelRow.image == image_to_match,
                        KernelRow.status == KernelStatus.PREPARING,
                    )
                )
                .values(
                    status=KernelStatus.PULLING,
                    status_history=sql_json_merge(
                        KernelRow.status_history,
                        (),
                        {KernelStatus.PULLING.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)
            return result.rowcount

    async def update_kernels_to_prepared_for_image(
        self, agent_id: AgentId, image: str, image_ref: Optional[str] = None
    ) -> int:
        """
        Update kernel status to PREPARED for the specified image on an agent.
        Updates kernels in both PULLING and PREPARING states.

        :param agent_id: The agent ID where kernels should be updated
        :param image: The image name to match kernels
        :param image_ref: Optional image reference (canonical format)
        :return: Number of kernels updated
        """
        async with self._begin_session_read_committed() as db_sess:
            now = datetime.now(tzutc())
            # Use image_ref if provided (canonical format), otherwise use image
            image_to_match = image_ref if image_ref else image
            # Find kernels on this agent with this image in PULLING or PREPARING state
            # and update them to PREPARED
            stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.agent == agent_id,
                        KernelRow.image == image_to_match,
                        KernelRow.status.in_([
                            KernelStatus.PULLING,
                            KernelStatus.PREPARING,
                        ]),
                    )
                )
                .values(
                    status=KernelStatus.PREPARED,
                    status_history=sql_json_merge(
                        KernelRow.status_history,
                        (),
                        {KernelStatus.PREPARED.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)
            return result.rowcount

    async def cancel_kernels_for_failed_image(
        self, agent_id: AgentId, image: str, error_msg: str, image_ref: Optional[str] = None
    ) -> set[SessionId]:
        """
        Cancel kernels for an image that failed to be available on an agent.
        Returns session IDs that may need to be checked for full cancellation.

        :param agent_id: The agent ID where the image is unavailable
        :param image: The image name that failed
        :param error_msg: The error message to include in status
        :param image_ref: Optional image reference (canonical format)
        :return: Set of affected session IDs
        """
        async with self._begin_session_read_committed() as db_sess:
            now = datetime.now(tzutc())
            # Use image_ref if provided (canonical format), otherwise use image
            image_to_match = image_ref if image_ref else image
            # Find and cancel kernels on this agent with this image in PULLING or PREPARING state
            stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.agent == agent_id,
                        KernelRow.image == image_to_match,
                        KernelRow.status.in_([
                            KernelStatus.PULLING,
                            KernelStatus.PREPARING,
                        ]),
                    )
                )
                .values(
                    status=KernelStatus.CANCELLED,
                    status_info=f"Image pull failed: {error_msg}",
                    status_history=sql_json_merge(
                        KernelRow.status_history,
                        (),
                        {KernelStatus.CANCELLED.name: now.isoformat()},
                    ),
                )
                .returning(KernelRow.session_id)
            )
            result = await db_sess.execute(stmt)
            affected_session_ids = {row.session_id for row in result}
            return affected_session_ids

    async def check_and_cancel_session_if_needed(self, session_id: SessionId) -> bool:
        """
        Check if a session should be cancelled when all its kernels are cancelled.

        :param session_id: The session ID to check
        :return: True if session was cancelled, False otherwise
        """
        async with self._begin_session_read_committed() as db_sess:
            # Check if all kernels for this session are cancelled
            kernel_check = await db_sess.execute(
                sa.select(sa.func.count())
                .select_from(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.session_id == session_id,
                        KernelRow.status != KernelStatus.CANCELLED,
                    )
                )
            )
            non_cancelled_count = kernel_check.scalar()

            if non_cancelled_count == 0:
                # All kernels are cancelled, cancel the session
                now = datetime.now(tzutc())
                stmt = (
                    sa.update(SessionRow)
                    .where(
                        sa.and_(
                            SessionRow.id == session_id,
                            SessionRow.status.not_in([
                                SessionStatus.CANCELLED,
                                SessionStatus.TERMINATED,
                            ]),
                        )
                    )
                    .values(
                        status=SessionStatus.CANCELLED,
                        status_info="All kernels cancelled",
                        status_history=sql_json_merge(
                            SessionRow.status_history,
                            (),
                            {SessionStatus.CANCELLED.name: now.isoformat()},
                        ),
                    )
                )
                result = await db_sess.execute(stmt)
                return result.rowcount > 0
        return False

    async def check_available_image(
        self, image_identifier: ImageIdentifier, domain: str, user_uuid: UUID
    ) -> None:
        """
        Check if an image is available in the database for a given domain and user.
        Raises ImageNotFound if the image is not found.

        :param image_identifier: The image identifier to check
        :param domain: The domain to check within
        :param user_uuid: The user UUID to check within
        :raises ImageNotFound: If the image is not found
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            image_row = await ImageRow.resolve(db_sess, [image_identifier])
            if (
                _owner_id := image_row.labels.get("ai.backend.customized-image.owner")
            ) and _owner_id != f"user:{user_uuid}":
                raise ImageNotFound
            if not image_row.is_local:
                query = (
                    sa.select([domains.c.allowed_docker_registries])
                    .select_from(domains)
                    .where(domains.c.name == domain)
                )
                allowed_registries = await db_sess.scalar(query)
                if image_row.registry not in allowed_registries:
                    raise ImageNotFound

    async def update_sessions_to_prepared(self, session_ids: list[SessionId]) -> None:
        """
        Update sessions from PULLING or PREPARING to PREPARED state.
        """
        if not session_ids:
            return

        async with self._begin_session_read_committed() as db_sess:
            now = datetime.now(tzutc())
            stmt = (
                sa.update(SessionRow)
                .where(
                    sa.and_(
                        SessionRow.id.in_(session_ids),
                        SessionRow.status.in_([
                            SessionStatus.PULLING,
                            SessionStatus.PREPARING,
                        ]),
                    )
                )
                .values(
                    status=SessionStatus.PREPARED,
                    status_info=None,  # Clear any previous error status
                    status_history=sql_json_merge(
                        SessionRow.status_history,
                        (),
                        {SessionStatus.PREPARED.name: now.isoformat()},
                    ),
                )
            )
            await db_sess.execute(stmt)

    async def get_sessions_for_transition(
        self,
        session_statuses: list[SessionStatus],
        kernel_statuses: list[KernelStatus],
    ) -> list[SessionTransitionData]:
        """
        Get sessions ready for state transition based on current session and kernel status.

        :param session_statuses: List of current session statuses to filter by
        :param kernel_statuses: List of required kernel statuses for transition
        :return: List of sessions ready for transition with detailed information
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            # Find sessions in specified states
            stmt = (
                sa.select(SessionRow)
                .where(SessionRow.status.in_(session_statuses))
                .options(selectinload(SessionRow.kernels))
            )
            result = await db_sess.execute(stmt)
            sessions = result.scalars().all()

            ready_sessions: list[SessionTransitionData] = []
            for session in sessions:
                # Check if all kernels have the required status
                all_ready = all(kernel.status in kernel_statuses for kernel in session.kernels)
                if not all_ready or not session.kernels:
                    continue

                # Build kernel transition data
                kernel_data = [
                    KernelTransitionData(
                        kernel_id=str(kernel.id),
                        agent_id=kernel.agent,
                        agent_addr=kernel.agent_addr,
                        cluster_role=kernel.cluster_role,
                        container_id=kernel.container_id,
                        startup_command=kernel.startup_command,
                        status_info=kernel.status_info,
                        occupied_slots=kernel.occupied_slots,
                    )
                    for kernel in session.kernels
                ]

                # Build session transition data
                session_data = SessionTransitionData(
                    session_id=session.id,
                    creation_id=session.creation_id,
                    session_name=session.name,
                    network_type=session.network_type,
                    network_id=session.network_id,
                    session_type=session.session_type,
                    access_key=session.access_key,
                    cluster_mode=session.cluster_mode,
                    kernels=kernel_data,
                    batch_timeout=session.batch_timeout,
                    status_info=session.status_info,
                )

                ready_sessions.append(session_data)

            return ready_sessions

    async def get_sessions_ready_to_run(self) -> list[SessionId]:
        """
        Get sessions in CREATING state where all kernels are RUNNING.
        Returns sessions that can transition to RUNNING state.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            # Find sessions in CREATING state where ALL kernels are RUNNING
            stmt = (
                sa.select(SessionRow)
                .where(SessionRow.status == SessionStatus.CREATING)
                .options(selectinload(SessionRow.kernels))
            )
            result = await db_sess.execute(stmt)
            sessions = result.scalars().all()

            ready_session_ids: list[SessionId] = []
            for session in sessions:
                # Check if all kernels are RUNNING
                all_running = all(
                    kernel.status == KernelStatus.RUNNING for kernel in session.kernels
                )
                if all_running and session.kernels:  # Ensure there are kernels
                    ready_session_ids.append(session.id)

            return ready_session_ids

    async def update_sessions_to_running(self, sessions_data: list[SessionRunningData]) -> None:
        """
        Update sessions from CREATING to RUNNING state with occupying_slots.
        """
        if not sessions_data:
            return

        async with self._begin_session_read_committed() as db_sess:
            now = datetime.now(tzutc())

            # Update each session individually with its calculated occupying_slots
            for session_data in sessions_data:
                stmt = (
                    sa.update(SessionRow)
                    .where(
                        sa.and_(
                            SessionRow.id == session_data.session_id,
                            SessionRow.status == SessionStatus.CREATING,
                        )
                    )
                    .values(
                        status=SessionStatus.RUNNING,
                        status_info=None,  # Clear any previous error status
                        occupying_slots=session_data.occupying_slots,
                        status_history=sql_json_merge(
                            SessionRow.status_history,
                            (),
                            {SessionStatus.RUNNING.name: now.isoformat()},
                        ),
                    )
                )
                await db_sess.execute(stmt)

    async def get_sessions_ready_to_terminate(self) -> list[SessionId]:
        """
        Get sessions in TERMINATING state where all kernels are TERMINATED.
        Returns sessions that can transition to TERMINATED state.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            # Find sessions in TERMINATING state where ALL kernels are TERMINATED
            stmt = (
                sa.select(SessionRow)
                .where(SessionRow.status == SessionStatus.TERMINATING)
                .options(selectinload(SessionRow.kernels))
            )
            result = await db_sess.execute(stmt)
            sessions = result.scalars().all()

            ready_session_ids: list[SessionId] = []
            for session in sessions:
                # Check if all kernels are TERMINATED
                all_terminated = all(
                    kernel.status == KernelStatus.TERMINATED for kernel in session.kernels
                )
                if all_terminated:  # Include sessions even with no kernels
                    ready_session_ids.append(session.id)

            return ready_session_ids

    async def update_sessions_to_terminated(self, session_ids: list[SessionId]) -> None:
        """
        Update sessions from TERMINATING to TERMINATED state.
        """
        if not session_ids:
            return

        async with self._begin_session_read_committed() as db_sess:
            now = datetime.now(tzutc())
            # Update session status to TERMINATED
            stmt = (
                sa.update(SessionRow)
                .where(
                    sa.and_(
                        SessionRow.id.in_(session_ids),
                        SessionRow.status == SessionStatus.TERMINATING,
                    )
                )
                .values(
                    status=SessionStatus.TERMINATED,
                    terminated_at=now,
                    # Keep status_info if it contains termination reason, otherwise clear
                    status_history=sql_json_merge(
                        SessionRow.status_history,
                        (),
                        {SessionStatus.TERMINATED.name: now.isoformat()},
                    ),
                )
            )
            await db_sess.execute(stmt)

    async def _resolve_image_configs(
        self, db_sess: SASession, unique_images: set[ImageIdentifier]
    ) -> dict[str, ImageConfigData]:
        """
        Resolve image configurations for the given unique images.

        :param db_sess: Database session to use
        :param unique_images: Set of ImageIdentifier objects to resolve
        :return: Dictionary mapping image names to ImageConfigData
        """
        from sqlalchemy.orm import selectinload

        from ai.backend.manager.models.image import ImageRow

        if not unique_images:
            return {}

        image_configs: dict[str, ImageConfigData] = {}

        # Build conditions for all images
        # Note: KernelRow.image stores the canonical name (ImageRow.name), not ImageRow.image
        conditions = []
        for image_id in unique_images:
            conditions.append(
                sa.and_(
                    ImageRow.name == image_id.canonical,
                    ImageRow.architecture == image_id.architecture,
                )
            )

        # Query all images at once with registry info
        stmt = (
            sa.select(ImageRow)
            .where(sa.or_(*conditions))
            .options(selectinload(ImageRow.registry_row))
        )

        result = await db_sess.execute(stmt)
        image_rows = result.scalars().all()

        # Convert to ImageConfigData
        for image_row in image_rows:
            try:
                img_ref = image_row.image_ref
                registry_row = image_row.registry_row

                image_config = ImageConfigData(
                    canonical=img_ref.canonical,
                    architecture=image_row.architecture,
                    project=image_row.project,
                    is_local=image_row.is_local,
                    digest=image_row.trimmed_digest,
                    labels=dict(image_row.labels),
                    registry_name=img_ref.registry,
                    registry_url=registry_row.url,
                    registry_username=registry_row.username,
                    registry_password=registry_row.password,
                )
                # Use the canonical name as key (which is what KernelRow.image contains)
                image_configs[image_row.name] = image_config
            except Exception as e:
                log.error(f"Failed to process image {image_row.name}: {e}")
                continue

        return image_configs

    async def _get_sessions_by_statuses(
        self,
        db_sess: SASession,
        statuses: list[SessionStatus],
    ) -> list[ScheduledSessionData]:
        """
        Get sessions with specified statuses.
        Returns dataclass objects instead of SessionRow.
        """
        # Get sessions with specified statuses and their kernels
        stmt = (
            sa.select(SessionRow)
            .where(SessionRow.status.in_(statuses))
            .options(
                selectinload(SessionRow.kernels).options(
                    load_only(
                        KernelRow.id,
                        KernelRow.agent,
                        KernelRow.agent_addr,
                        KernelRow.scaling_group,
                        KernelRow.image,
                        KernelRow.architecture,
                        KernelRow.status,
                        KernelRow.status_changed,
                    )
                )
            )
        )
        result = await db_sess.execute(stmt)
        sessions = result.scalars().all()

        scheduled_sessions: list[ScheduledSessionData] = []
        for session in sessions:
            # Create kernel data list with status_changed timestamp
            kernels_data = []
            for kernel in session.kernels:
                kernel_data = KernelBindingData(
                    kernel_id=kernel.id,
                    agent_id=kernel.agent,
                    agent_addr=kernel.agent_addr,
                    scaling_group=kernel.scaling_group,
                    image=kernel.image,
                    architecture=kernel.architecture,
                    status=kernel.status,
                    status_changed=kernel.status_changed.timestamp()
                    if kernel.status_changed
                    else None,
                )
                kernels_data.append(kernel_data)

            scheduled_session = ScheduledSessionData(
                session_id=session.id,
                creation_id=session.creation_id,
                access_key=session.access_key,
                reason="triggered-by-scheduler",
            )
            scheduled_sessions.append(scheduled_session)

        return scheduled_sessions

    async def _get_scheduled_sessions(self, db_sess: SASession) -> list[ScheduledSessionData]:
        """
        Get sessions in SCHEDULED status for precondition checking.
        Returns dataclass objects instead of SessionRow.
        """
        # Get sessions with SCHEDULED status and their kernels
        stmt = (
            sa.select(SessionRow)
            .where(SessionRow.status == SessionStatus.SCHEDULED)
            .options(
                selectinload(SessionRow.kernels).options(
                    load_only(
                        KernelRow.id,
                        KernelRow.agent,
                        KernelRow.agent_addr,
                        KernelRow.scaling_group,
                        KernelRow.image,
                        KernelRow.architecture,
                    )
                ),
                load_only(
                    SessionRow.id,
                    SessionRow.creation_id,
                    SessionRow.access_key,
                    SessionRow.session_type,
                    SessionRow.name,
                ),
            )
        )
        result = await db_sess.execute(stmt)
        sessions = result.scalars().all()

        scheduled_sessions: list[ScheduledSessionData] = []
        for session in sessions:
            scheduled_sessions.append(
                ScheduledSessionData(
                    session_id=session.id,
                    creation_id=session.creation_id,
                    access_key=session.access_key,
                    reason="triggered-by-scheduler",
                )
            )

        return scheduled_sessions

    async def get_sessions_for_pull(
        self,
        session_statuses: list[SessionStatus],
        kernel_statuses: list[KernelStatus],
    ) -> SessionsForPullWithImages:
        """
        Get sessions for image pulling with specified statuses.
        Returns SessionsForPullWithImages dataclass.

        :param session_statuses: Session statuses to filter by (typically SCHEDULED, PREPARING, PULLING)
        :param kernel_statuses: Kernel statuses to filter by (typically PREPARING, PULLING)
        :return: SessionsForPullWithImages object
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            # Get sessions with minimal fields needed for pulling
            sessions_for_pull = await self._get_sessions_for_pull(
                db_sess, session_statuses, kernel_statuses
            )

            # Collect unique images to resolve
            unique_images: set[ImageIdentifier] = set()
            for session in sessions_for_pull:
                for kernel in session.kernels:
                    unique_images.add(
                        ImageIdentifier(canonical=kernel.image, architecture=kernel.architecture)
                    )

            # Resolve all images and build ImageConfigData
            image_configs = await self._resolve_image_configs(db_sess, unique_images)

            return SessionsForPullWithImages(
                sessions=sessions_for_pull, image_configs=image_configs
            )

    async def get_sessions_for_start(
        self,
        session_statuses: list[SessionStatus],
        kernel_statuses: list[KernelStatus],
    ) -> SessionsForStartWithImages:
        """
        Get sessions for starting with specified statuses.
        Returns SessionsForStartWithImages dataclass.

        :param statuses: Session statuses to filter by (typically PREPARED, CREATING)
        :return: SessionsForStartWithImages object
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            # Get sessions with all fields needed for starting
            sessions_for_start = await self._get_sessions_for_start(
                db_sess, session_statuses, kernel_statuses
            )

            # Collect unique images to resolve
            unique_images: set[ImageIdentifier] = set()
            for session in sessions_for_start:
                for kernel in session.kernels:
                    unique_images.add(
                        ImageIdentifier(canonical=kernel.image, architecture=kernel.architecture)
                    )

            # Resolve all images and build ImageConfigData
            image_configs = await self._resolve_image_configs(db_sess, unique_images)

            return SessionsForStartWithImages(
                sessions=sessions_for_start, image_configs=image_configs
            )

    async def _get_sessions_for_pull(
        self,
        db_sess: SASession,
        session_statuses: list[SessionStatus],
        kernel_statuses: list[KernelStatus],
    ) -> list[SessionDataForPull]:
        """
        Get sessions with minimal fields needed for image pulling.
        """
        # Get sessions with specified statuses AND their kernels with specified kernel statuses
        # Using outerjoin to include sessions and filter by kernel status
        stmt = (
            sa.select(
                SessionRow.id,
                SessionRow.creation_id,
                SessionRow.access_key,
                SessionRow.status,
                KernelRow.id.label("kernel_id"),
                KernelRow.agent,
                KernelRow.agent_addr,
                KernelRow.scaling_group,
                KernelRow.image,
                KernelRow.architecture,
                KernelRow.cluster_role,
                KernelRow.cluster_idx,
                KernelRow.local_rank,
                KernelRow.cluster_hostname,
                KernelRow.uid,
                KernelRow.main_gid,
                KernelRow.gids,
                KernelRow.requested_slots,
                KernelRow.resource_opts,
                KernelRow.bootstrap_script,
                KernelRow.startup_command,
                KernelRow.preopen_ports,
                KernelRow.internal_data,
                KernelRow.vfolder_mounts,
                KernelRow.status.label("kernel_status"),
                KernelRow.status_changed,
            )
            .select_from(SessionRow)
            .outerjoin(KernelRow, SessionRow.id == KernelRow.session_id)
            .where(
                sa.and_(
                    SessionRow.status.in_(session_statuses),
                    KernelRow.status.in_(kernel_statuses),
                )
            )
            .order_by(SessionRow.created_at, SessionRow.id, KernelRow.cluster_idx)
        )
        result = await db_sess.execute(stmt)
        rows = result.fetchall()

        # Convert to dataclass - group rows by session
        sessions_map: dict[SessionId, SessionDataForPull] = {}

        for row in rows:
            session_id = row.id

            # Create session if not exists
            if session_id not in sessions_map:
                sessions_map[session_id] = SessionDataForPull(
                    session_id=session_id,
                    creation_id=row.creation_id,
                    access_key=row.access_key,
                    kernels=[],
                )

            # Add kernel if exists
            if row.kernel_id:
                kernel_binding = KernelBindingData(
                    kernel_id=row.kernel_id,
                    agent_id=row.agent,
                    agent_addr=row.agent_addr,
                    scaling_group=row.scaling_group,
                    image=row.image,
                    architecture=row.architecture,
                    status=row.kernel_status,
                    status_changed=row.status_changed.timestamp() if row.status_changed else None,
                    cluster_role=row.cluster_role,
                    cluster_idx=row.cluster_idx,
                    local_rank=row.local_rank,
                    cluster_hostname=row.cluster_hostname,
                    uid=row.uid,
                    main_gid=row.main_gid,
                    gids=row.gids or [],
                    requested_slots=row.requested_slots or ResourceSlot(),
                    resource_opts=row.resource_opts or {},
                    bootstrap_script=row.bootstrap_script,
                    startup_command=row.startup_command,
                    preopen_ports=row.preopen_ports or [],
                    internal_data=row.internal_data,
                    vfolder_mounts=row.vfolder_mounts or [],
                )
                sessions_map[session_id].kernels.append(kernel_binding)

        return list(sessions_map.values())

    async def _get_sessions_for_start(
        self,
        db_sess: SASession,
        session_statuses: list[SessionStatus],
        kernel_statuses: list[KernelStatus],
    ) -> list[SessionDataForStart]:
        """
        Get sessions with all fields needed for starting.
        """
        # Get sessions with specified statuses and their kernels with specified statuses
        # Using JOIN to filter kernels by status
        stmt = (
            sa.select(
                SessionRow.id,
                SessionRow.creation_id,
                SessionRow.access_key,
                SessionRow.session_type,
                SessionRow.name,
                SessionRow.environ,
                SessionRow.cluster_mode,
                SessionRow.user_uuid,
                KernelRow.id.label("kernel_id"),
                KernelRow.agent,
                KernelRow.agent_addr,
                KernelRow.scaling_group,
                KernelRow.image,
                KernelRow.architecture,
                KernelRow.cluster_role,
                KernelRow.cluster_idx,
                KernelRow.local_rank,
                KernelRow.cluster_hostname,
                KernelRow.uid,
                KernelRow.main_gid,
                KernelRow.gids,
                KernelRow.requested_slots,
                KernelRow.resource_opts,
                KernelRow.bootstrap_script,
                KernelRow.startup_command,
                KernelRow.preopen_ports,
                KernelRow.internal_data,
                KernelRow.vfolder_mounts,
                KernelRow.status.label("kernel_status"),
                KernelRow.status_changed,
            )
            .select_from(SessionRow)
            .outerjoin(KernelRow, SessionRow.id == KernelRow.session_id)
            .where(
                sa.and_(
                    SessionRow.status.in_(session_statuses),
                    KernelRow.status.in_(kernel_statuses),
                )
            )
            .order_by(SessionRow.created_at, SessionRow.id)
        )
        result = await db_sess.execute(stmt)
        rows = result.fetchall()

        # Group rows by session
        from collections import defaultdict

        session_data: dict[SessionId, dict] = defaultdict(lambda: {"kernels": []})
        user_uuids = set()

        for row in rows:
            session_id = row.id
            if "info" not in session_data[session_id]:
                session_data[session_id]["info"] = {
                    "id": row.id,
                    "creation_id": row.creation_id,
                    "access_key": row.access_key,
                    "session_type": row.session_type,
                    "name": row.name,
                    "environ": row.environ,
                    "cluster_mode": row.cluster_mode,
                    "user_uuid": row.user_uuid,
                }
                if row.user_uuid:
                    user_uuids.add(row.user_uuid)

            if row.kernel_id:  # Only add kernel if it exists
                session_data[session_id]["kernels"].append({
                    "kernel_id": row.kernel_id,
                    "agent": row.agent,
                    "agent_addr": row.agent_addr,
                    "scaling_group": row.scaling_group,
                    "image": row.image,
                    "architecture": row.architecture,
                    "kernel_status": row.kernel_status,
                    "status_changed": row.status_changed,
                    "cluster_role": row.cluster_role,
                    "cluster_idx": row.cluster_idx,
                    "local_rank": row.local_rank,
                    "cluster_hostname": row.cluster_hostname,
                    "uid": row.uid,
                    "main_gid": row.main_gid,
                    "gids": row.gids,
                    "requested_slots": row.requested_slots,
                    "resource_opts": row.resource_opts,
                    "bootstrap_script": row.bootstrap_script,
                    "startup_command": row.startup_command,
                    "preopen_ports": row.preopen_ports,
                    "internal_data": row.internal_data,
                    "vfolder_mounts": row.vfolder_mounts,
                })

        # Load user info for sessions
        user_map = {}
        if user_uuids:
            user_query = sa.select(
                UserRow.uuid,
                UserRow.email,
                UserRow.username,
            ).where(UserRow.uuid.in_(user_uuids))
            user_result = await db_sess.execute(user_query)
            user_map = {row.uuid: row for row in user_result.fetchall()}

        # Convert to dataclass
        sessions_for_start: list[SessionDataForStart] = []
        for session_id, data in session_data.items():
            session_info = data["info"]

            # Get user info
            user_info = user_map.get(session_info["user_uuid"])
            if not user_info:
                log.warning(f"User info not found for session {session_id}")
                continue

            # Convert kernels
            kernel_bindings = [
                KernelBindingData(
                    kernel_id=k["kernel_id"],
                    agent_id=k["agent"],
                    agent_addr=k["agent_addr"],
                    scaling_group=k["scaling_group"],
                    image=k["image"],
                    architecture=k["architecture"],
                    status=k["kernel_status"],
                    status_changed=k["status_changed"].timestamp() if k["status_changed"] else None,
                    cluster_role=k["cluster_role"],
                    cluster_idx=k["cluster_idx"],
                    local_rank=k["local_rank"],
                    cluster_hostname=k["cluster_hostname"],
                    uid=k["uid"],
                    main_gid=k["main_gid"],
                    gids=k["gids"] or [],
                    requested_slots=k["requested_slots"] or ResourceSlot(),
                    resource_opts=k["resource_opts"] or {},
                    bootstrap_script=k["bootstrap_script"],
                    startup_command=k["startup_command"],
                    preopen_ports=k["preopen_ports"] or [],
                    internal_data=k["internal_data"],
                    vfolder_mounts=k["vfolder_mounts"] or [],
                )
                for k in data["kernels"]
            ]

            sessions_for_start.append(
                SessionDataForStart(
                    session_id=session_info["id"],
                    creation_id=session_info["creation_id"],
                    access_key=session_info["access_key"],
                    session_type=session_info["session_type"],
                    name=session_info["name"],
                    cluster_mode=session_info["cluster_mode"],
                    kernels=kernel_bindings,
                    environ=session_info.get("environ", {}),
                    user_uuid=session_info["user_uuid"],
                    user_email=user_info.email,
                    user_name=user_info.username,
                )
            )

        return sessions_for_start

    async def update_sessions_to_preparing(self, session_ids: list[SessionId]) -> None:
        """
        Update sessions from SCHEDULED to PREPARING status.
        Also updates kernel status to PREPARING.
        Uses UPDATE WHERE for READ COMMITTED isolation.
        """
        if not session_ids:
            return

        async with self._begin_session_read_committed() as db_sess:
            now = datetime.now(tzutc())

            # Update session status
            stmt = (
                sa.update(SessionRow)
                .where(
                    sa.and_(
                        SessionRow.id.in_(session_ids),
                        SessionRow.status == SessionStatus.SCHEDULED,
                    )
                )
                .values(
                    status=SessionStatus.PREPARING,
                    status_info=None,  # Clear any previous error status
                    status_history=sql_json_merge(
                        SessionRow.status_history,
                        (),
                        {SessionStatus.PREPARING.name: now.isoformat()},
                    ),
                )
            )
            await db_sess.execute(stmt)

            # Update kernel statuses
            kernel_stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.session_id.in_(session_ids),
                        KernelRow.status == KernelStatus.SCHEDULED,
                    )
                )
                .values(
                    status=KernelStatus.PREPARING,
                    status_changed=now,
                )
            )
            await db_sess.execute(kernel_stmt)

    async def update_sessions_and_kernels_to_creating(self, session_ids: list[SessionId]) -> None:
        """
        Update sessions and kernels from PREPARED to CREATING status.
        Uses UPDATE WHERE for READ COMMITTED isolation.
        """
        if not session_ids:
            return

        async with self._begin_session_read_committed() as db_sess:
            now = datetime.now(tzutc())

            # Update session status
            stmt = (
                sa.update(SessionRow)
                .where(
                    sa.and_(
                        SessionRow.id.in_(session_ids),
                        SessionRow.status == SessionStatus.PREPARED,
                    )
                )
                .values(
                    status=SessionStatus.CREATING,
                    status_info=None,  # Clear any previous error status
                    status_history=sql_json_merge(
                        SessionRow.status_history,
                        (),
                        {SessionStatus.CREATING.name: now.isoformat()},
                    ),
                )
            )
            await db_sess.execute(stmt)

            # Update kernel statuses
            kernel_stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.session_id.in_(session_ids),
                        KernelRow.status == KernelStatus.PREPARED,
                    )
                )
                .values(
                    status=KernelStatus.CREATING,
                    status_changed=now,
                )
            )
            await db_sess.execute(kernel_stmt)

    async def mark_session_cancelled(
        self, session_id: SessionId, error_info: ErrorStatusInfo, reason: str = "FAILED_TO_START"
    ) -> None:
        """
        Mark a session as cancelled with error information.
        Used when session fails to start.
        """
        async with self._begin_session_read_committed() as db_sess:
            now = datetime.now(tzutc())

            # Update session status
            stmt = (
                sa.update(SessionRow)
                .where(SessionRow.id == session_id)
                .values(
                    status=SessionStatus.CANCELLED,
                    status_info=reason,
                    status_data=error_info,  # Store ErrorStatusInfo as status_data in DB
                )
            )
            await db_sess.execute(stmt)

            # Update kernel statuses
            kernel_stmt = (
                sa.update(KernelRow)
                .where(KernelRow.session_id == session_id)
                .values(
                    status=KernelStatus.CANCELLED,
                    status_changed=now,
                    status_info=reason,
                )
            )
            await db_sess.execute(kernel_stmt)

    async def _increment_session_retry_count(
        self, db_sess: SASession, session_id: SessionId, max_retries: int
    ) -> bool:
        """
        Private method to increment retry count for a session.

        :param db_sess: Database session to use
        :param session_id: The session ID to update
        :param max_retries: Maximum retries before moving to PENDING
        :return: True if session should continue retrying, False if moved to PENDING
        """
        # Get current session and its retry count
        stmt = sa.select(SessionRow).where(SessionRow.id == session_id)
        result = await db_sess.execute(stmt)
        session_row = result.scalar()

        if not session_row:
            log.warning("Session {} not found for retry count update", session_id)
            return False

        # Get current retries count from existing status_data
        current_status_data = session_row.status_data or {}
        scheduler_data = current_status_data.get("scheduler", {})
        current_retries = scheduler_data.get("retries", 0)
        new_retries = current_retries + 1

        # Check if we should move to PENDING
        should_move_to_pending = new_retries >= max_retries

        if should_move_to_pending:
            # Reset retry count to 0 when moving back to PENDING
            status_data = {"retries": 0}

            # Update session to PENDING with reset retry count
            update_stmt = (
                sa.update(SessionRow)
                .where(
                    sa.and_(
                        SessionRow.id == session_id,
                        SessionRow.status.in_(SessionStatus.retriable_statuses()),
                    )
                )
                .values(
                    status=SessionStatus.PENDING,
                    status_data=sql_json_merge(
                        SessionRow.status_data,
                        ("scheduler",),
                        obj=status_data,
                    ),
                )
            )
            await db_sess.execute(update_stmt)

            # Also update kernel status to PENDING
            kernel_stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.session_id == session_id,
                        KernelRow.status.in_(KernelStatus.retriable_statuses()),
                    )
                )
                .values(
                    agent=None,
                    agent_addr=None,
                    status=KernelStatus.PENDING,
                    status_data=sql_json_merge(
                        KernelRow.status_data,
                        ("scheduler",),
                        obj=status_data,
                    ),
                )
            )
            await db_sess.execute(kernel_stmt)

            log.info(
                "Session {} exceeded max retries ({}), moved to PENDING", session_id, max_retries
            )
            return False  # Should not retry
        else:
            # Update with incremented retry count
            status_data = {"retries": new_retries}

            # Just update retry count, keep current status
            update_stmt = (
                sa.update(SessionRow)
                .where(SessionRow.id == session_id)
                .values(
                    status_data=sql_json_merge(
                        SessionRow.status_data,
                        ("scheduler",),
                        obj=status_data,
                    ),
                )
            )
            await db_sess.execute(update_stmt)

            log.debug("Session {} retry count incremented to {}", session_id, new_retries)
            return True  # Should continue retrying

    async def batch_update_stuck_session_retries(
        self, session_ids: list[SessionId], max_retries: int = 5
    ) -> list[SessionId]:
        """
        Batch update retry counts for stuck sessions.
        Sessions that exceed max_retries are moved to PENDING status.

        :param session_ids: List of session IDs to update
        :param max_retries: Maximum retries before moving to PENDING (default: 5)
        :return: List of session IDs that should continue retrying (not moved to PENDING)
        """
        sessions_to_retry: list[SessionId] = []

        async with self._begin_session_read_committed() as db_sess:
            for session_id in session_ids:
                should_retry = await self._increment_session_retry_count(
                    db_sess, session_id, max_retries
                )

                if should_retry:
                    sessions_to_retry.append(session_id)

        return sessions_to_retry

    async def update_session_error_info(
        self, session_id: SessionId, error_info: ErrorStatusInfo
    ) -> None:
        """
        Update session's status_data with error information without changing status.
        This is used when a session fails but should be retried later.

        :param session_id: The session ID to update
        :param error_info: Error information to store in status_data
        """
        async with self._begin_session_read_committed() as db_sess:
            # Update session status_data with error info
            update_stmt = (
                sa.update(SessionRow)
                .where(SessionRow.id == session_id)
                .values(
                    status_data=sql_json_merge(
                        SessionRow.status_data,
                        ("error",),
                        obj=error_info,
                    ),
                )
            )
            await db_sess.execute(update_stmt)

            # Also update kernel status_data
            kernel_stmt = (
                sa.update(KernelRow)
                .where(KernelRow.session_id == session_id)
                .values(
                    status_data=sql_json_merge(
                        KernelRow.status_data,
                        ("error",),
                        obj=error_info,
                    ),
                )
            )
            await db_sess.execute(kernel_stmt)

    async def get_container_info_for_kernels(
        self, session_id: SessionId
    ) -> dict[UUID, Optional[str]]:
        """
        Get container IDs for kernels in a session.
        Used for cleanup when session fails to start.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            stmt = sa.select(KernelRow.id, KernelRow.container_id).where(
                KernelRow.session_id == session_id
            )
            result = await db_sess.execute(stmt)
            return {row.id: row.container_id for row in result}

    async def get_keypair_concurrencies_from_db(
        self, access_key: AccessKey
    ) -> KeypairConcurrencyData:
        """
        Calculate both regular and SFTP concurrency from database with two simple queries.

        :param access_key: The access key to query
        :return: KeypairConcurrencyData with both regular and sftp counts
        """
        from ai.backend.manager.models.kernel import USER_RESOURCE_OCCUPYING_KERNEL_STATUSES
        from ai.backend.manager.models.session import PRIVATE_SESSION_TYPES

        async with self._begin_readonly_session_read_committed() as db_sess:
            # Base query for active kernels
            base_query = (
                sa.select(sa.func.count())
                .select_from(KernelRow)
                .where(
                    (KernelRow.access_key == access_key)
                    & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                )
            )

            # Query for regular sessions
            regular_query = base_query.where(KernelRow.session_type.not_in(PRIVATE_SESSION_TYPES))
            regular_result = await db_sess.execute(regular_query)
            regular_count = regular_result.scalar() or 0

            # Query for SFTP sessions
            sftp_query = base_query.where(KernelRow.session_type.in_(PRIVATE_SESSION_TYPES))
            sftp_result = await db_sess.execute(sftp_query)
            sftp_count = sftp_result.scalar() or 0

            return KeypairConcurrencyData(regular_count=regular_count, sftp_count=sftp_count)

    async def update_session_network_id(
        self,
        session_id: SessionId,
        network_id: Optional[str],
    ) -> None:
        """
        Update session's network information in the database.

        :param session_id: The session ID to update
        :param network_id: The network ID to set (or None to clear)
        """
        async with self._begin_session_read_committed() as db_sess:
            update_stmt = (
                sa.update(SessionRow)
                .where(SessionRow.id == session_id)
                .values(
                    network_id=network_id,
                )
            )
            await db_sess.execute(update_stmt)

    async def calculate_total_resource_slots(self) -> TotalResourceData:
        """
        Calculate total resource slots from all agents in the database.
        Uses AgentRow.available_slots for capable slots and kernel-based calculation for occupied slots.

        :return: TotalResourceData with total used, free, and capable slots
        """
        async with self._begin_session_read_committed() as db_sess:
            # Get all active agent IDs and their available slots
            agent_stmt = sa.select(
                AgentRow.id,
                AgentRow.available_slots,
            ).where(
                sa.and_(AgentRow.status == AgentStatus.ALIVE, AgentRow.schedulable == sa.true())
            )

            agent_result = await db_sess.execute(agent_stmt)
            agent_rows = agent_result.fetchall()

            # Extract agent IDs and calculate total capacity slots
            agent_ids = set()
            total_capacity_slots = ResourceSlot()

            for agent_row in agent_rows:
                agent_ids.add(agent_row.id)
                if agent_row.available_slots:
                    total_capacity_slots += agent_row.available_slots

            # Calculate occupied slots from kernels using existing method
            agent_occupied_slots = await self._calculate_agent_occupied_slots(db_sess, agent_ids)

            # Sum up all occupied slots
            total_used_slots = ResourceSlot()
            for occupied_slots in agent_occupied_slots.values():
                total_used_slots += occupied_slots

            # Calculate free slots
            total_free_slots = total_capacity_slots - total_used_slots

            return TotalResourceData(
                total_used_slots=total_used_slots,
                total_free_slots=total_free_slots,
                total_capacity_slots=total_capacity_slots,
            )

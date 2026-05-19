"""Database source for schedule repository operations."""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import AsyncIterator, Mapping, Sequence
from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

if TYPE_CHECKING:
    from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
    from ai.backend.manager.data.session.draft import SessionSpecDraft
    from ai.backend.manager.data.session.spec import SessionSpec

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import load_only, selectinload

from ai.backend.common import msgpack
from ai.backend.common.data.permission.types import (
    RBACElementType,
)
from ai.backend.common.docker import ImageRef
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.resource.types import TotalResourceData
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionTypes,
    SlotName,
    SlotQuantity,
    SlotTypes,
    VFolderMount,
    VFolderMountOptions,
    VFolderMountRequest,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.dotfile.types import DotfileBundle, DotfileEntry, SSHKeypair
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.kernel.types import KernelListResult, KernelStatus
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.data.session.types import SchedulingResult, SessionInfo, SessionStatus
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.errors.image import ImageNotFound
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.errors.resource_slot import AgentResourceCapacityExceeded
from ai.backend.manager.exceptions import ErrorStatusInfo
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow, domains, query_domain_dotfiles
from ai.backend.manager.models.group import GroupRow, query_group_dotfiles
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import (
    USER_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    KernelRow,
)
from ai.backend.manager.models.kernel.conditions import KernelConditions
from ai.backend.manager.models.keypair import KeyPairRow, keypairs
from ai.backend.manager.models.resource_policy import (
    DefaultForUnspecified,
    KeyPairResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow, query_allowed_sgroups
from ai.backend.manager.models.scheduling_history.row import SessionSchedulingHistoryRow
from ai.backend.manager.models.session import (
    PRIVATE_SESSION_TYPES,
    SessionDependencyRow,
    SessionRow,
)
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    sql_json_merge,
)
from ai.backend.manager.models.vfolder import prepare_vfolder_mounts
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    execute_batch_querier,
)
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    RBACBulkEntityCreator,
    RBACEntityCreator,
    execute_rbac_bulk_entity_creator,
    execute_rbac_entity_creator,
)
from ai.backend.manager.repositories.base.updater import BatchUpdater, execute_batch_updater
from ai.backend.manager.repositories.resource_slot.types import (
    accumulate_to_quantities,
    resource_slot_to_quantities,
)
from ai.backend.manager.repositories.scheduler.creators import (
    KernelRowFromSpec,
    SessionRowFromSpec,
)
from ai.backend.manager.repositories.scheduler.options import ImageConditions
from ai.backend.manager.repositories.scheduler.types.agent import AgentMeta
from ai.backend.manager.repositories.scheduler.types.base import SchedulingSpec
from ai.backend.manager.repositories.scheduler.types.results import (
    ScheduledSessionData,
)
from ai.backend.manager.repositories.scheduler.types.scaling_group import ScalingGroupMeta
from ai.backend.manager.repositories.scheduler.types.scheduling import SchedulingData
from ai.backend.manager.repositories.scheduler.types.search import (
    SessionWithKernelsAndUserSearchResult,
    SessionWithKernelsSearchResult,
)
from ai.backend.manager.repositories.scheduler.types.session import (
    KernelData,
    MarkTerminatingResult,
    PendingSessionData,
    PendingSessions,
    SweptSessionInfo,
    TerminatingKernelData,
    TerminatingKernelWithAgentData,
    TerminatingSessionData,
)
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    ContainerUserInfo,
    ImageInfo,
    ScalingGroupNetworkInfo,
    SessionSpecContextFetch,
)
from ai.backend.manager.repositories.scheduler.types.snapshot import ResourcePolicies, SnapshotData
from ai.backend.manager.repositories.scheduling_history import (
    SessionSchedulingHistoryCreatorSpec,
)
from ai.backend.manager.sokovan.data import (
    AgentOccupancy,
    AllocationBatch,
    ImageConfigData,
    KernelBindingData,
    KernelCreationInfo,
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
    SessionWithKernels,
    UserResourcePolicy,
)
from ai.backend.manager.types import UserScope

from .types import KeypairConcurrencyData, SessionRowCache

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _create_resource_slot_from_policy(
    total_resource_slots: ResourceSlot | None,
    default_for_unspecified: DefaultForUnspecified | None,
    known_slot_types: Mapping[SlotName, SlotTypes],
) -> ResourceSlot:
    """Create ResourceSlot from policy data."""
    resource_policy_map = {
        "total_resource_slots": total_resource_slots or ResourceSlot(),
        "default_for_unspecified": default_for_unspecified or DefaultForUnspecified.LIMITED,
    }
    return ResourceSlot.from_policy(resource_policy_map, cast(Mapping[str, Any], known_slot_types))


@dataclass(frozen=True)
class _ScalingGroupWithSlotInventory:
    """Scaling group bundled with the slot inventory served by its agents.

    ``active_slot_types`` maps each slot name served by a non-terminated
    agent in this scaling group to its registered :class:`SlotTypes`
    unit. The validator chain consults this map both for membership
    (reject requests for slots the RG does not provide) and for unit
    metadata (humanize values during error formatting).
    """

    sg_row: ScalingGroupRow
    active_slot_types: Mapping[SlotName, SlotTypes]


class ScheduleDBSource:
    """
    Database source for schedule-related operations.
    Handles all database queries and updates for scheduling.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
    ) -> None:
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
                sess_factory = async_sessionmaker(
                    bind=conn_with_isolation,
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
                sess_factory = async_sessionmaker(
                    bind=conn_with_isolation,
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

    async def _fetch_scaling_group_with_slot_inventory(
        self,
        db_sess: SASession,
        name: str,
    ) -> _ScalingGroupWithSlotInventory:
        """Load a scaling group together with its per-RG slot inventory.

        Eager-loads ``agents`` -> ``agent_resource_rows`` -> ``slot_type_row``
        via ``selectinload``, filters out TERMINATED agents, and projects
        the remaining rows into ``{slot_name: SlotTypes}``. The ``AgentRow``
        instances themselves are not exposed — callers only see the SG row
        and the derived inventory.

        Raises:
            ScalingGroupNotFound: when the scaling group does not exist.
        """
        sg_row = (
            await db_sess.scalars(
                sa.select(ScalingGroupRow)
                .options(
                    selectinload(ScalingGroupRow.agents)
                    .selectinload(AgentRow.agent_resource_rows)
                    .selectinload(AgentResourceRow.slot_type_row)
                )
                .where(ScalingGroupRow.name == name)
            )
        ).one_or_none()
        if sg_row is None:
            raise ScalingGroupNotFound(f"Resource group {name} not found")
        active_slot_types: dict[SlotName, SlotTypes] = {
            SlotName(ar.slot_name): SlotTypes(ar.slot_type_row.slot_type)
            for agent in sg_row.agents
            if agent.status != AgentStatus.TERMINATED
            for ar in agent.agent_resource_rows
        }
        return _ScalingGroupWithSlotInventory(
            sg_row=sg_row,
            active_slot_types=active_slot_types,
        )

    async def _fetch_required_slot_names(self, db_sess: SASession) -> frozenset[SlotName]:
        stmt = sa.select(ResourceSlotTypeRow.slot_name).where(
            ResourceSlotTypeRow.required.is_(True)
        )
        rows = (await db_sess.execute(stmt)).scalars().all()
        return frozenset(SlotName(slot_name) for slot_name in rows)

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
        """
        Fetch pending sessions with kernels using single JOIN query.
        The result is sorted by session creation time (oldest first).
        """
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
                SessionRow.is_preemptible,
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
            .order_by(SessionRow.created_at.asc())
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
                    is_preemptible=row.is_preemptible,
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
        """Fetch kernel occupancy data from normalized resource_allocations table."""
        ra = ResourceAllocationRow.__table__
        k = KernelRow.__table__
        rst = ResourceSlotTypeRow.__table__
        all_resource_statuses = (
            KernelStatus.resource_occupied_statuses() | KernelStatus.resource_requested_statuses()
        )
        effective_amount = sa.func.coalesce(ra.c.used, ra.c.requested)
        occ_stmt = (
            sa.select(
                k.c.session_id,
                k.c.access_key,
                k.c.user_uuid,
                k.c.group_id,
                k.c.domain_name,
                k.c.agent,
                k.c.status,
                k.c.session_type,
                ra.c.slot_name,
                effective_amount.label("effective_amount"),
                rst.c.rank,
            )
            .select_from(
                ra.join(k, ra.c.kernel_id == k.c.id).join(rst, ra.c.slot_name == rst.c.slot_name)
            )
            .where(
                k.c.scaling_group == scaling_group,
                k.c.status.in_(all_resource_statuses),
                ra.c.free_at.is_(None),
            )
        )
        occupancy_rows = (await db_sess.execute(occ_stmt)).all()

        # Build rank_map for ordering
        rank_map: dict[str, int] = {}

        # Dict-based accumulators
        _keypair_accum: dict[AccessKey, dict[str, Decimal]] = defaultdict(dict)
        _user_accum: dict[UUID, dict[str, Decimal]] = defaultdict(dict)
        _group_accum: dict[UUID, dict[str, Decimal]] = defaultdict(dict)
        _domain_accum: dict[str, dict[str, Decimal]] = defaultdict(dict)
        _agent_accum: dict[AgentId, dict[str, Decimal]] = defaultdict(dict)

        # Track unique sessions per keypair to count correctly
        sessions_by_keypair: dict[AccessKey, set[SessionId]] = defaultdict(set)
        sftp_sessions_by_keypair: dict[AccessKey, set[SessionId]] = defaultdict(set)

        # Track unique kernels per agent for container count
        kernels_by_agent: dict[AgentId, set[tuple[SessionId, str]]] = defaultdict(set)

        def _accum_add(accum: dict[str, Decimal], slot_name: str, amount: Decimal) -> None:
            accum[slot_name] = accum.get(slot_name, Decimal(0)) + amount

        for row in occupancy_rows:
            rank_map[row.slot_name] = row.rank
            session_type = SessionTypes(row.session_type)

            # Only accumulate resource slots for non-private sessions
            if not session_type.is_private():
                _accum_add(_keypair_accum[row.access_key], row.slot_name, row.effective_amount)
                _accum_add(_user_accum[row.user_uuid], row.slot_name, row.effective_amount)
                _accum_add(_group_accum[row.group_id], row.slot_name, row.effective_amount)
                _accum_add(_domain_accum[row.domain_name], row.slot_name, row.effective_amount)

                # Track regular sessions
                sessions_by_keypair[row.access_key].add(row.session_id)
            else:
                # Track SFTP sessions
                sftp_sessions_by_keypair[row.access_key].add(row.session_id)

            if row.agent:
                _accum_add(_agent_accum[row.agent], row.slot_name, row.effective_amount)
                kernels_by_agent[row.agent].add((row.session_id, row.slot_name))

        # Convert to list[SlotQuantity]
        occupancy_by_keypair: dict[AccessKey, KeypairOccupancy] = {}
        for ak, accum in _keypair_accum.items():
            occupancy_by_keypair[ak] = KeypairOccupancy(
                occupied_slots=accumulate_to_quantities(accum, rank_map),
                session_count=len(sessions_by_keypair.get(ak, set())),
                sftp_session_count=len(sftp_sessions_by_keypair.get(ak, set())),
            )

        # Ensure keypairs with only SFTP sessions still appear
        for ak in sftp_sessions_by_keypair:
            if ak not in occupancy_by_keypair:
                occupancy_by_keypair[ak] = KeypairOccupancy(
                    occupied_slots=[],
                    session_count=0,
                    sftp_session_count=len(sftp_sessions_by_keypair[ak]),
                )

        occupancy_by_user = {
            uid: accumulate_to_quantities(acc, rank_map) for uid, acc in _user_accum.items()
        }
        occupancy_by_group = {
            gid: accumulate_to_quantities(acc, rank_map) for gid, acc in _group_accum.items()
        }
        occupancy_by_domain = {
            dn: accumulate_to_quantities(acc, rank_map) for dn, acc in _domain_accum.items()
        }

        occupancy_by_agent: dict[AgentId, AgentOccupancy] = {}
        for agent_id, accum in _agent_accum.items():
            unique_sessions = {sid for sid, _ in kernels_by_agent.get(agent_id, set())}
            occupancy_by_agent[agent_id] = AgentOccupancy(
                occupied_slots=accumulate_to_quantities(accum, rank_map),
                container_count=len(unique_sessions),
            )

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
        self,
        session_ids: list[SessionId],
        reason: str = "USER_REQUESTED",
        *,
        forced: bool = False,
    ) -> MarkTerminatingResult:
        """
        Mark sessions and their kernels as TERMINATING (or directly TERMINATED when forced).
        Uses UPDATE ... WHERE ... RETURNING for atomic status transitions.
        Returns categorized session IDs based on their current status.
        """
        async with self._begin_session_read_committed() as db_sess:
            now = await self._get_db_now_in_session(db_sess)
            # 1. Cancel pending sessions
            cancelled_sessions = await self._cancel_pending_sessions(
                db_sess, session_ids, reason, now
            )

            if forced:
                # 2a. Force-terminate: set sessions directly to TERMINATED
                force_terminated_sessions = await self._mark_sessions_as_force_terminated(
                    db_sess, session_ids, reason, now
                )
                terminating_sessions: list[SessionId] = []
            else:
                # 2b. Normal: mark sessions as TERMINATING
                force_terminated_sessions = []
                terminating_sessions = await self._mark_sessions_as_terminating(
                    db_sess, session_ids, reason, now
                )

            # 3. Mark unprocessed sessions as skipped
            processed_ids = (
                set(cancelled_sessions) | set(terminating_sessions) | set(force_terminated_sessions)
            )
            skipped_sessions = [sid for sid in session_ids if sid not in processed_ids]

            return MarkTerminatingResult(
                cancelled_sessions=cancelled_sessions,
                terminating_sessions=terminating_sessions,
                force_terminated_sessions=force_terminated_sessions,
                skipped_sessions=skipped_sessions,
            )

    async def _free_kernel_allocations(
        self,
        db_sess: SASession,
        kernel_ids: Sequence[UUID],
        now: datetime,
    ) -> None:
        """Set ``free_at`` on the given kernels' active allocations. Only sets
        ``free_at`` and does not adjust ``agent_resources.used`` -- callers
        whose source statuses can include RUNNING/TERMINATING must use
        ``update_kernel_status_terminated`` instead. Idempotent.
        """
        if not kernel_ids:
            return
        await db_sess.execute(
            sa.update(ResourceAllocationRow)
            .where(
                ResourceAllocationRow.kernel_id.in_(kernel_ids),
                ResourceAllocationRow.free_at.is_(None),
            )
            .values(free_at=now)
        )

    async def _cancel_pending_sessions(
        self, db_sess: SASession, session_ids: list[SessionId], reason: str, now: datetime
    ) -> list[SessionId]:
        """Cancel PENDING sessions and their kernels, and free the kernels'
        ``resource_allocations`` rows in the same transaction.
        """
        cancel_stmt = (
            sa.update(SessionRow)
            .values(
                status=SessionStatus.CANCELLED,
                status_info=reason,
                terminated_at=now,
                status_history=sql_json_merge(
                    SessionRow.__table__.c.status_history,
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

        if cancelled_sessions:
            kernel_update_result = await db_sess.execute(
                sa.update(KernelRow)
                .values(
                    status=KernelStatus.CANCELLED,
                    status_info=reason,
                    status_changed=now,
                    terminated_at=now,
                    status_history=sql_json_merge(
                        KernelRow.__table__.c.status_history,
                        (),
                        {KernelStatus.CANCELLED.name: now.isoformat()},
                    ),
                )
                .where(KernelRow.session_id.in_(cancelled_sessions))
                .returning(KernelRow.id)
            )
            cancelled_kernel_ids = [row.id for row in kernel_update_result]
            await self._free_kernel_allocations(db_sess, cancelled_kernel_ids, now)

        return cancelled_sessions

    async def _mark_sessions_as_terminating(
        self, db_sess: SASession, session_ids: list[SessionId], reason: str, now: datetime
    ) -> list[SessionId]:
        """Mark terminatable sessions and their kernels as terminating."""
        # Capture from_statuses before update
        status_query = sa.select(SessionRow.id, SessionRow.status).where(
            sa.and_(
                SessionRow.id.in_(session_ids),
                SessionRow.status.in_(SessionStatus.terminatable_statuses()),
            )
        )
        status_result = await db_sess.execute(status_query)
        from_statuses: dict[SessionId, SessionStatus] = {
            cast(SessionId, row.id): SessionStatus(row.status) for row in status_result
        }

        # Mark sessions as terminating
        terminating_stmt = (
            sa.update(SessionRow)
            .values(
                status=SessionStatus.TERMINATING,
                status_info=reason,
                status_history=sql_json_merge(
                    SessionRow.__table__.c.status_history,
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
                        KernelRow.__table__.c.status_history,
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

            # Record scheduling history for terminating transition
            history_specs = [
                SessionSchedulingHistoryCreatorSpec(
                    session_id=sid,
                    phase="mark_terminating",
                    result=SchedulingResult.SUCCESS,
                    message="mark_terminating success",
                    from_status=from_statuses.get(sid),
                    to_status=SessionStatus.TERMINATING,
                )
                for sid in terminating_sessions
            ]
            await self._record_scheduling_history(db_sess, BulkCreator(specs=history_specs))

        return terminating_sessions

    async def _mark_sessions_as_force_terminated(
        self, db_sess: SASession, session_ids: list[SessionId], reason: str, now: datetime
    ) -> list[SessionId]:
        """Directly mark terminatable sessions and their kernels as TERMINATED (force-terminate)."""
        now_iso = now.isoformat()
        # Capture from_statuses before update
        status_query = sa.select(SessionRow.id, SessionRow.status).where(
            sa.and_(
                SessionRow.id.in_(session_ids),
                SessionRow.status.in_(SessionStatus.force_terminatable_statuses()),
            )
        )
        status_result = await db_sess.execute(status_query)
        from_statuses: dict[SessionId, SessionStatus] = {
            cast(SessionId, row.id): SessionStatus(row.status) for row in status_result
        }
        # Mark sessions as TERMINATED directly, recording both TERMINATING and TERMINATED timestamps
        terminated_stmt = (
            sa.update(SessionRow)
            .values(
                status=SessionStatus.TERMINATED,
                status_info=reason,
                terminated_at=now,
                status_history=sql_json_merge(
                    SessionRow.__table__.c.status_history,
                    (),
                    {
                        SessionStatus.TERMINATING.name: now_iso,
                        SessionStatus.TERMINATED.name: now_iso,
                    },
                ),
            )
            .where(
                sa.and_(
                    SessionRow.id.in_(session_ids),
                    SessionRow.status.in_(SessionStatus.force_terminatable_statuses()),
                )
            )
            .returning(SessionRow.id)
        )
        terminated_result = await db_sess.execute(terminated_stmt)
        force_terminated_sessions = [cast(SessionId, row.id) for row in terminated_result]

        # Mark kernels as TERMINATED directly
        if force_terminated_sessions:
            # Fetch kernel_id and agent_id before updating status
            kernel_agent_query = sa.select(KernelRow.id, KernelRow.agent).where(
                sa.and_(
                    KernelRow.session_id.in_(force_terminated_sessions),
                    KernelRow.status.in_(KernelStatus.force_terminatable_statuses()),
                )
            )
            kernel_agent_rows = (await db_sess.execute(kernel_agent_query)).all()

            await db_sess.execute(
                sa.update(KernelRow)
                .values(
                    status=KernelStatus.TERMINATED,
                    status_info=reason,
                    status_changed=now,
                    terminated_at=now,
                    status_history=sql_json_merge(
                        KernelRow.__table__.c.status_history,
                        (),
                        {
                            KernelStatus.TERMINATING.name: now_iso,
                            KernelStatus.TERMINATED.name: now_iso,
                        },
                    ),
                )
                .where(
                    sa.and_(
                        KernelRow.session_id.in_(force_terminated_sessions),
                        KernelRow.status.in_(KernelStatus.force_terminatable_statuses()),
                    )
                )
            )

            # Free resource allocations and decrement agent_resources for each kernel
            ar = AgentResourceRow.__table__
            for kernel_id, agent_id in kernel_agent_rows:
                released = (
                    await db_sess.execute(
                        sa.update(ResourceAllocationRow)
                        .where(
                            ResourceAllocationRow.kernel_id == kernel_id,
                            ResourceAllocationRow.free_at.is_(None),
                        )
                        .values(free_at=sa.func.now())
                        .returning(ResourceAllocationRow.slot_name, ResourceAllocationRow.used)
                    )
                ).all()
                if agent_id and released:
                    for r in released:
                        if r.used is None:
                            continue
                        new_used = sa.func.greatest(ar.c.used - r.used, 0)
                        await db_sess.execute(
                            sa.update(ar)
                            .where(ar.c.agent_id == agent_id, ar.c.slot_name == r.slot_name)
                            .values(used=new_used)
                        )

            # Record scheduling history for force-terminate transition
            history_specs = [
                SessionSchedulingHistoryCreatorSpec(
                    session_id=sid,
                    phase="force_terminate",
                    result=SchedulingResult.SUCCESS,
                    message="force_terminate success",
                    from_status=from_statuses.get(sid),
                    to_status=SessionStatus.TERMINATED,
                )
                for sid in force_terminated_sessions
            ]
            await self._record_scheduling_history(db_sess, BulkCreator(specs=history_specs))

        return force_terminated_sessions

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

    async def get_all_scaling_groups(self) -> list[str]:
        """Get all defined scaling groups."""
        async with self._begin_readonly_session_read_committed() as session:
            query = sa.select(ScalingGroupRow.name)
            result = await session.execute(query)
            return [row.name for row in result.fetchall()]

    async def get_terminating_sessions_by_ids(
        self,
        session_ids: list[SessionId],
    ) -> list[TerminatingSessionData]:
        """
        Fetch terminating sessions by session IDs.

        This method is used by handlers that need detailed session data
        (TerminatingSessionData) beyond what the coordinator provides (HandlerSessionData).

        :param session_ids: List of session IDs to fetch
        :return: List of TerminatingSessionData objects with kernel details
        """
        if not session_ids:
            return []

        async with self._begin_readonly_session_read_committed() as session:
            query = (
                sa.select(SessionRow)
                .where(SessionRow.id.in_(session_ids))
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
                        kernel_id=KernelId(kernel.id),
                        status=kernel.status,
                        container_id=kernel.container_id,
                        agent_id=AgentId(kernel.agent) if kernel.agent else None,
                        agent_addr=kernel.agent_addr,
                        occupied_slots=kernel.occupied_slots,
                    )
                    for kernel in session_row.kernels
                ]

                terminating_sessions.append(
                    TerminatingSessionData(
                        session_id=session_row.id,
                        access_key=AccessKey(session_row.access_key)
                        if session_row.access_key
                        else AccessKey(""),
                        creation_id=session_row.creation_id or "",
                        status=session_row.status,
                        status_info=session_row.status_info or "UNKNOWN",
                        session_type=session_row.session_type,
                        kernels=kernels,
                    )
                )

            return terminating_sessions

    async def get_pending_timeout_sessions_by_ids(
        self,
        session_ids: list[SessionId],
    ) -> list[SweptSessionInfo]:
        """
        Get sessions that have exceeded their pending timeout from given session IDs.

        :param session_ids: Pre-filtered session IDs from Coordinator
        :return: List of sessions that have timed out
        """
        if not session_ids:
            return []

        timed_out_sessions: list[SweptSessionInfo] = []

        async with self._begin_readonly_session_read_committed() as db_sess:
            now = await self._get_db_now_in_session(db_sess)
            query = (
                sa.select(
                    SessionRow.id,
                    SessionRow.creation_id,
                    SessionRow.access_key,
                    SessionRow.created_at,
                    ScalingGroupRow.scheduler_opts,
                )
                .select_from(SessionRow)
                .join(ScalingGroupRow, SessionRow.scaling_group_name == ScalingGroupRow.name)
                .where(
                    SessionRow.id.in_(session_ids),
                    SessionRow.status == SessionStatus.PENDING,
                )
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

    async def get_terminating_kernels_with_lost_agents_by_ids(
        self,
        session_ids: list[SessionId],
    ) -> list[TerminatingKernelWithAgentData]:
        """
        Fetch kernels in TERMINATING state that have lost or missing agents
        from given session IDs.

        :param session_ids: Pre-filtered session IDs from Coordinator
        :return: List of kernels with lost agents
        """
        if not session_ids:
            return []

        async with self._begin_readonly_session_read_committed() as db_sess:
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
                    KernelRow.session_id.in_(session_ids),
                    KernelRow.status == KernelStatus.TERMINATING,
                    sa.or_(
                        KernelRow.agent.is_(None),  # No agent assigned
                        AgentRow.status.in_(
                            AgentStatus.unavailable_statuses()
                        ),  # Agent unavailable
                    ),
                )
            )
            result = await db_sess.execute(query)
            rows = result.fetchall()

            return [
                TerminatingKernelWithAgentData(
                    kernel_id=KernelId(row.id),
                    session_id=row.session_id,
                    status=row.status,
                    agent_id=row.agent,
                    agent_status=str(row.agent_status) if row.agent_status else None,
                )
                for row in rows
            ]

    async def enqueue_session_from_spec(
        self,
        spec: SessionSpec,
    ) -> SessionId:
        """Persist a finalized :class:`SessionSpec` as a pending session.

        Entry point for every caller that runs the typed draft → spec
        preparer
        chain. The writer transaction covers dependency validation,
        ``SessionRow`` / ``KernelRow`` creation, RBAC assignment,
        ``ResourceAllocationRow`` inserts, dependency rows, and the
        ``enqueue`` scheduling-history row — preserving the legacy
        atomicity envelope.

        The only DB read inside this method is an ``ImageRow`` batch
        fetch for the kernels' ``image_id``s so the historical
        ``image``/``architecture``/``registry``/``tag`` columns stay
        populated (see ``KernelRow.image`` docstring — those columns are
        active fallbacks while task #29 is pending). All other data
        comes from the spec the caller assembled upstream.
        """
        enqueue_time = datetime.now().astimezone()

        async with self._begin_session_read_committed() as db_sess:
            image_ids = {
                kernel.execution_spec.image_id
                for kernel in spec.kernel_specs
                if kernel.execution_spec.image_id is not None
            }
            image_metadata: dict[ImageID, ImageInfo] = {}
            if image_ids:
                rows = (
                    await db_sess.scalars(
                        sa.select(ImageRow).where(ImageRow.id.in_(list(image_ids)))
                    )
                ).all()
                image_metadata = {
                    ImageID(row.id): ImageInfo(
                        id=row.id,
                        canonical=row.name,
                        architecture=row.architecture,
                        registry=row.registry,
                        labels=dict(row.labels),
                        resource_spec=cast(dict[str, Any], row.resources),
                    )
                    for row in rows
                }

            for kernel in spec.kernel_specs:
                image_id = kernel.execution_spec.image_id
                if image_id is not None and image_id not in image_metadata:
                    raise ImageNotFound(
                        f"Image {image_id} referenced by kernel "
                        f"'{kernel.cluster_hostname}' is not registered.",
                    )

            # Validate dependencies — each dependency session must exist.
            matched_dependency_ids: list[SessionId] = []
            for dependency_id in spec.dependencies:
                result = await db_sess.execute(
                    sa.select(SessionRow.id).where(SessionRow.id == dependency_id)
                )
                if not result.scalar():
                    raise InvalidAPIParameters(
                        "Unknown session ID in the dependency list",
                        extra_data={"session_ref": str(dependency_id)},
                    )
                matched_dependency_ids.append(SessionId(dependency_id))

            session_creator_spec = SessionRowFromSpec(
                spec=spec,
                image_infos=image_metadata,
                enqueue_time=enqueue_time,
            )
            kernel_creator_specs: list[KernelRowFromSpec] = [
                KernelRowFromSpec(
                    spec=spec,
                    kernel_spec=kernel,
                    image_info=(
                        image_metadata.get(kernel.execution_spec.image_id)
                        if kernel.execution_spec.image_id is not None
                        else None
                    ),
                    enqueue_time=enqueue_time,
                )
                for kernel in spec.kernel_specs
            ]

            rbac_creator = RBACEntityCreator(
                spec=session_creator_spec,
                element_type=RBACElementType.SESSION,
                scope_ref=RBACElementRef(
                    element_type=RBACElementType.USER,
                    element_id=str(spec.identity.user_uuid),
                ),
                additional_scope_refs=[
                    RBACElementRef(
                        element_type=RBACElementType.PROJECT,
                        element_id=str(spec.scope.project_id),
                    )
                ],
            )
            await execute_rbac_entity_creator(db_sess, rbac_creator)

            kernel_rbac_creator = RBACBulkEntityCreator(
                specs=kernel_creator_specs,
                element_type=RBACElementType.KERNEL,
                scope_ref=RBACElementRef(
                    element_type=RBACElementType.SESSION,
                    element_id=str(spec.identity.session_id),
                ),
            )
            kernel_result = await execute_rbac_bulk_entity_creator(db_sess, kernel_rbac_creator)

            for kernel_row in kernel_result.rows:
                quantities = resource_slot_to_quantities(kernel_row.requested_slots)
                if quantities:
                    await db_sess.execute(
                        sa.insert(ResourceAllocationRow),
                        [
                            {
                                "kernel_id": kernel_row.id,
                                "slot_name": q.slot_name,
                                "requested": q.quantity,
                            }
                            for q in quantities
                        ],
                    )

            if matched_dependency_ids:
                dependency_rows = [
                    SessionDependencyRow(
                        session_id=spec.identity.session_id,
                        depends_on=depend_id,
                    )
                    for depend_id in matched_dependency_ids
                ]
                db_sess.add_all(dependency_rows)

            history_spec = SessionSchedulingHistoryCreatorSpec(
                session_id=SessionId(spec.identity.session_id),
                phase="enqueue",
                result=SchedulingResult.SUCCESS,
                message="enqueue success",
                from_status=None,
                to_status=SessionStatus.PENDING,
            )
            await self._record_scheduling_history(db_sess, BulkCreator(specs=[history_spec]))

            await db_sess.commit()

        return SessionId(spec.identity.session_id)

    async def fetch_session_spec_contexts(
        self,
        draft: SessionSpecDraft,
        *,
        storage_manager: StorageSessionManager,
        allowed_vfolder_types: list[str],
    ) -> SessionSpecContextFetch:
        """Batch-fetch every DB read the draft-based preparer and validator
        rules depend on, inside a single readonly transaction.

        Returns raw fetched data as :class:`SessionSpecContextFetch` — the
        scheduling controller converts it into its typed
        ``SessionSpecPreparationContext`` +
        ``SessionSpecValidationContext`` pair. Keeping the repository
        unaware of the controller's typed contexts breaks the import
        cycle between ``repositories.scheduler`` and the sokovan
        ``scheduling_controller`` subtree.
        """
        resource_group_name = (
            str(draft.scope.resource_group_name) if draft.scope.resource_group_name else None
        )
        access_key = draft.identity.access_key
        user_uuid = draft.identity.user_uuid
        domain_name = str(draft.scope.domain_name) if draft.scope.domain_name else None
        project_id = draft.scope.project_id

        kernel_specs = tuple(draft.options.kernel_groups or ())

        async with self._begin_readonly_session_read_committed() as db_sess:
            network_info: ScalingGroupNetworkInfo | None = None
            rg_defaults = None
            resource_group_allow_fractional = False
            known_slot_types: Mapping[SlotName, SlotTypes] = {}
            required_slot_names = await self._fetch_required_slot_names(db_sess)
            if resource_group_name:
                rg_bundle = await self._fetch_scaling_group_with_slot_inventory(
                    db_sess, resource_group_name
                )
                sg_row = rg_bundle.sg_row
                known_slot_types = rg_bundle.active_slot_types
                # Every production caller of ``enqueue_session_from_draft`` populates
                # access_key/domain_name/project_id alongside resource_group_name; this
                # branch flags the contract violation rather than letting the RG
                # access check silently degrade to fail-open.
                if access_key is None or domain_name is None or project_id is None:
                    raise InternalServerError(
                        "Unreachable: resource_group_name supplied without identity context",
                    )
                # The draft's access_key is the owner's for delegated sessions, so
                # this check enforces RG access against the owner's allowlist.
                allowed_rgs = await self._query_allowed_scaling_groups(
                    db_sess, domain_name, project_id, access_key
                )
                if resource_group_name not in {rg.name for rg in allowed_rgs}:
                    raise InvalidAPIParameters(
                        f"Resource group '{resource_group_name}' is not accessible"
                    )
                network_info = ScalingGroupNetworkInfo(
                    use_host_network=sg_row.use_host_network,
                    wsproxy_addr=sg_row.wsproxy_addr,
                )
                rg_defaults = sg_row.default_session_options
                scheduler_opts = sg_row.scheduler_opts
                resource_group_allow_fractional = bool(
                    getattr(scheduler_opts, "allow_fractional_resource_fragmentation", False)
                )

            if rg_defaults is None:
                rg_defaults = DefaultSessionOptions()

            image_ids: list[UUID] = []
            seen_ids: set[UUID] = set()
            for group in kernel_specs:
                img = group.execution_spec.image_id
                if img is None:
                    continue
                img_uuid = UUID(str(img))
                if img_uuid in seen_ids:
                    continue
                seen_ids.add(img_uuid)
                image_ids.append(img_uuid)
            image_rows: list[ImageRow] = []
            if image_ids:
                image_rows = list(
                    (
                        await db_sess.scalars(sa.select(ImageRow).where(ImageRow.id.in_(image_ids)))
                    ).all()
                )
            image_infos = {
                ImageID(row.id): ImageInfo(
                    id=row.id,
                    canonical=row.name,
                    architecture=row.architecture,
                    registry=row.registry,
                    labels=row.labels,
                    resource_spec=cast(dict[str, Any], row.resources),
                )
                for row in image_rows
            }

            user_container = (
                await self._fetch_user_container_info(db_sess, user_uuid)
                if user_uuid is not None
                else ContainerUserInfo()
            )

            keypair_policy = None
            resource_policy_dict: dict[str, Any] = {}
            if access_key is not None:
                kp_row = (
                    await db_sess.scalars(
                        sa.select(KeyPairRow)
                        .options(selectinload(KeyPairRow.resource_policy_row))
                        .where(KeyPairRow.access_key == access_key)
                    )
                ).one_or_none()
                if kp_row is not None and kp_row.resource_policy_row is not None:
                    keypair_policy = kp_row.resource_policy_row.to_dataclass()
                    resource_policy_dict = {
                        "allowed_vfolder_hosts": keypair_policy.allowed_vfolder_hosts,
                    }

            # Resolve mount requests per kernel group keyed by ``role``.
            # Each group's request list resolves to a single
            # ``VFolderMount`` tuple that every replica sharing the role
            # copies verbatim. Task #33 (role-based mount override) can
            # write distinct values per role without structural change.
            vfolder_mounts_by_role: dict[str, tuple[VFolderMount, ...]] = {}
            if domain_name is not None and user_uuid is not None:
                user_scope_for_mounts = UserScope(
                    domain_name=domain_name,
                    group_id=project_id if project_id is not None else UUID(int=0),
                    user_uuid=user_uuid,
                    user_role="user",
                )
                for group in kernel_specs:
                    per_group_requests: list[VFolderMountRequest] = []
                    for entry in group.execution_spec.mounts:
                        per_group_requests.append(
                            VFolderMountRequest(
                                ref=UUID(str(entry.vfolder_id)),
                                dst_path=entry.mount_destination,
                                options=VFolderMountOptions(
                                    permission=entry.mount_perm,
                                    subpath=entry.subpath,
                                ),
                            )
                        )
                    if not per_group_requests:
                        continue
                    vfolder_mounts_by_role[group.role] = tuple(
                        await self._fetch_vfolder_mounts(
                            db_sess,
                            storage_manager,
                            allowed_vfolder_types,
                            user_scope_for_mounts,
                            resource_policy_dict,
                            per_group_requests,
                        )
                    )

            dotfile_bundle = DotfileBundle()
            if domain_name is not None and user_uuid is not None and access_key is not None:
                user_scope_for_dotfiles = UserScope(
                    domain_name=domain_name,
                    group_id=project_id if project_id is not None else UUID(int=0),
                    user_uuid=user_uuid,
                    user_role="user",
                )
                dotfile_bundle = await self._fetch_dotfile_data(
                    db_sess, user_scope_for_dotfiles, access_key
                )

            # Active session count for concurrent-session quota check.
            active_session_count = 0
            if access_key is not None:
                active_count_result = await db_sess.execute(
                    sa.select(sa.func.count(SessionRow.id)).where(
                        SessionRow.access_key == access_key,
                        SessionRow.status.in_([
                            SessionStatus.PENDING,
                            SessionStatus.SCHEDULED,
                            SessionStatus.PREPARING,
                            SessionStatus.PULLING,
                            SessionStatus.CREATING,
                            SessionStatus.RUNNING,
                            SessionStatus.RESTARTING,
                        ]),
                    )
                )
                active_session_count = int(active_count_result.scalar_one())

        return SessionSpecContextFetch(
            resource_group_defaults=rg_defaults,
            resource_group_network=network_info,
            container_user_info=user_container,
            image_infos=image_infos,
            resource_group_allow_fractional=resource_group_allow_fractional,
            vfolder_mounts_by_role=vfolder_mounts_by_role,
            dotfile_data=dotfile_bundle,
            active_session_count=active_session_count,
            keypair_resource_policy=keypair_policy,
            known_slot_types=known_slot_types,
            required_slot_names=required_slot_names,
        )

    async def pick_default_resource_group(
        self,
        *,
        access_key: AccessKey,
        domain_name: str,
        project_id: ProjectID,
    ) -> ResourceGroupName:
        """Return the first resource group from the owner's allowlist."""
        async with self._begin_readonly_session_read_committed() as db_sess:
            allowed_rgs = await self._query_allowed_scaling_groups(
                db_sess, domain_name, project_id, access_key
            )
        if not allowed_rgs:
            raise InvalidAPIParameters("No accessible scaling group available")
        return ResourceGroupName(allowed_rgs[0].name)

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
            raise ScalingGroupNotFound(f"Scaling group {scaling_group_name} not found")

        return ScalingGroupNetworkInfo(
            use_host_network=row.use_host_network,
            wsproxy_addr=row.wsproxy_addr,
        )

    async def _resolve_image_info(
        self, db_sess: SASession, image_refs: list[ImageRef]
    ) -> dict[str, ImageInfo]:
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
                    id=image_row.id,
                    canonical=image_row.name,  # 'name' is the canonical reference in ImageRow
                    architecture=image_row.architecture,
                    registry=image_row.registry,
                    labels=image_row.labels,
                    resource_spec=cast(dict[str, Any], image_row.resources),  # Cast to match type
                )
        return image_infos

    async def _fetch_vfolder_mounts(
        self,
        db_sess: SASession,
        storage_manager: StorageSessionManager,
        allowed_vfolder_types: list[str],
        user_scope: UserScope,
        resource_policy: dict[str, Any],
        mount_requests: list[VFolderMountRequest],
    ) -> list[VFolderMount]:
        """
        Fetch vfolder mounts for the session using existing DB session.
        """
        conn = cast(SAConnection, db_sess.bind)

        vfolder_mounts = await prepare_vfolder_mounts(
            conn,
            storage_manager,
            allowed_vfolder_types,
            user_scope,
            resource_policy,
            mount_requests,
        )
        return list(vfolder_mounts)

    async def _fetch_dotfile_data(
        self,
        db_sess: SASession,
        user_scope: UserScope,
        access_key: AccessKey,
    ) -> DotfileBundle:
        """Read SSH keypair + keypair/group/domain dotfiles for a user.

        Ports the read-side of the legacy ``prepare_dotfiles`` helper
        (``models/dotfile.py`` — removed) into the repository layer so
        the query does not live in ``models/``. The conflict check
        against resolved vfolder mounts is owned by the validator rule
        :class:`DotfileVFolderConflictRule`; this method only fetches.

        Returns a typed :class:`DotfileBundle` with an ordered dotfile
        sequence (keypair > group > domain, with duplicate paths dropped
        and reversed so higher-priority entries overwrite on conflict)
        and an optional :class:`SSHKeypair`. The agent-facing JSONB dict
        is rendered by :meth:`DotfileBundle.to_internal_data` at the
        preparer boundary.
        """
        conn = cast(SAConnection, db_sess.bind)

        row = (
            await conn.execute(
                sa.select(
                    keypairs.c.ssh_public_key,
                    keypairs.c.ssh_private_key,
                    keypairs.c.dotfiles,
                ).where(keypairs.c.access_key == access_key)
            )
        ).first()
        if row is None:
            return DotfileBundle()

        keypair_dotfiles = list(msgpack.unpackb(row.dotfiles))
        ordered_entries: list[DotfileEntry] = [
            DotfileEntry(path=entry["path"], perm=entry["perm"], data=entry["data"])
            for entry in keypair_dotfiles
        ]
        ssh_keypair: SSHKeypair | None = None
        if row.ssh_public_key and row.ssh_private_key:
            ssh_keypair = SSHKeypair(
                public_key=row.ssh_public_key,
                private_key=row.ssh_private_key,
            )
        seen_paths = {entry.path for entry in ordered_entries}

        group_dotfiles, _ = await query_group_dotfiles(conn, user_scope.group_id)
        for entry in group_dotfiles:
            if entry["path"] not in seen_paths:
                ordered_entries.append(
                    DotfileEntry(path=entry["path"], perm=entry["perm"], data=entry["data"])
                )
                seen_paths.add(entry["path"])

        domain_dotfiles, _ = await query_domain_dotfiles(conn, user_scope.domain_name)
        for entry in domain_dotfiles:
            if entry["path"] not in seen_paths:
                ordered_entries.append(
                    DotfileEntry(path=entry["path"], perm=entry["perm"], data=entry["data"])
                )
                seen_paths.add(entry["path"])

        # Reverse so higher-priority entries win when agents apply
        # dotfiles in list order — matches the legacy behavior.
        ordered_entries.reverse()
        return DotfileBundle(
            dotfiles=tuple(ordered_entries),
            ssh_keypair=ssh_keypair,
        )

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
            supplementary_gids=user_row.container_gids or [],
        )

    async def prepare_vfolder_mounts(
        self,
        storage_manager: StorageSessionManager,
        allowed_vfolder_types: list[str],
        user_scope: UserScope,
        resource_policy: dict[str, Any],
        mount_requests: list[VFolderMountRequest],
    ) -> list[VFolderMount]:
        """
        Prepare vfolder mounts for the session.
        """
        async with self._begin_readonly_read_committed() as conn:
            vfolder_mounts = await prepare_vfolder_mounts(
                conn,
                storage_manager,
                allowed_vfolder_types,
                user_scope,
                resource_policy,
                mount_requests,
            )
        return list(vfolder_mounts)

    async def _query_allowed_scaling_groups(
        self,
        db_sess: SASession,
        domain_name: str,
        group_id: ProjectID,
        access_key: str,
    ) -> list[AllowedScalingGroup]:
        """
        Query allowed scaling groups for the given user/group.

        Args:
            db_sess: Database session
            domain_name: Domain name
            group_id: Project (group) ID
            access_key: Access key

        Returns:
            List of AllowedScalingGroup objects
        """
        # query_allowed_sgroups expects AsyncConnection, get it from session
        conn = await db_sess.connection()
        allowed_sgroups = await query_allowed_sgroups(
            conn,
            domain_name,
            group_id,
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
            now = await self._get_db_now_in_session(db_sess)
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
                    await self._allocate_single_session(db_sess, allocation, now)
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
        now: datetime,
    ) -> None:
        """
        Allocate resources for a single session.
        Updates session first, then its kernels.
        Only updates if session is in PENDING status.
        """

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
                    SessionRow.__table__.c.status_history,
                    (),
                    {SessionStatus.SCHEDULED.name: now.isoformat()},
                ),
                scaling_group_name=allocation.scaling_group,
                agent_ids=allocation.unique_agent_ids(),
            )
        )
        result = await db_sess.execute(session_update_query)

        # Check if session was actually updated
        if cast(CursorResult[Any], result).rowcount == 0:
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
                        KernelRow.__table__.c.status_history,
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
                    SessionRow.__table__.c.status_data,
                    ("scheduler",),
                    obj=status_data,
                ),
            )
        )
        result = await db_sess.execute(session_query)

        # Check if session was actually updated
        if cast(CursorResult[Any], result).rowcount == 0:
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
                    KernelRow.__table__.c.status_data,
                    ("scheduler",),
                    obj=status_data,
                ),
            )
        )
        await db_sess.execute(kernel_query)

    async def update_kernel_status_pulling(self, kernel_id: UUID, reason: str) -> bool:
        """
        Update kernel status to PULLING when pulling image.
        Uses UPDATE WHERE to ensure atomic state transition.

        :param kernel_id: Kernel ID to update
        :param reason: The reason for status change
        :return: True if update was successful, False otherwise
        """
        async with self._begin_session_read_committed() as db_sess:
            now = await self._get_db_now_in_session(db_sess)
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
                        KernelRow.__table__.c.status_history,
                        (),
                        {KernelStatus.PULLING.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)
            return cast(CursorResult[Any], result).rowcount > 0

    async def update_kernel_status_creating(self, kernel_id: UUID, reason: str) -> bool:
        """
        Update kernel status to CREATING when creating container.
        Uses UPDATE WHERE to ensure atomic state transition.

        :param kernel_id: Kernel ID to update
        :param reason: The reason for status change
        :return: True if update was successful, False otherwise
        """
        async with self._begin_session_read_committed() as db_sess:
            now = await self._get_db_now_in_session(db_sess)
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
                        KernelRow.__table__.c.status_history,
                        (),
                        {KernelStatus.CREATING.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)
            return cast(CursorResult[Any], result).rowcount > 0

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
        log.debug(
            "[DBSource] update_kernel_status_running called: kernel_id={}, reason={}",
            kernel_id,
            reason,
        )
        async with self._begin_session_read_committed() as db_sess:
            # Check current kernel status and fetch agent_id before update
            check_stmt = sa.select(KernelRow.status, KernelRow.starts_at, KernelRow.agent).where(
                KernelRow.id == kernel_id
            )
            check_result = await db_sess.execute(check_stmt)
            current = check_result.first()
            if current:
                log.debug(
                    "[DBSource] Kernel {} current state: status={}, starts_at={}",
                    kernel_id,
                    current.status,
                    current.starts_at,
                )
            else:
                log.debug("[DBSource] Kernel {} not found!", kernel_id)

            now = await self._get_db_now_in_session(db_sess)
            occupied_slots = creation_info.get_resource_allocations()
            stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.id == kernel_id,
                        KernelRow.status.in_([KernelStatus.PREPARED, KernelStatus.CREATING]),
                    )
                )
                .values(
                    status=KernelStatus.RUNNING,
                    status_info=reason,
                    status_changed=now,
                    starts_at=now,
                    occupied_slots=occupied_slots,
                    container_id=creation_info.container_id,
                    attached_devices=creation_info.attached_devices,
                    repl_in_port=creation_info.repl_in_port,
                    repl_out_port=creation_info.repl_out_port,
                    stdin_port=creation_info.stdin_port,
                    stdout_port=creation_info.stdout_port,
                    service_ports=creation_info.service_ports,
                    kernel_host=creation_info.kernel_host,
                    status_history=sql_json_merge(
                        KernelRow.__table__.c.status_history,
                        (),
                        {KernelStatus.RUNNING.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)
            rowcount = cast(CursorResult[Any], result).rowcount
            log.debug(
                "[DBSource] update_kernel_status_running result: kernel_id={}, rowcount={}, "
                "starts_at_to_set={}",
                kernel_id,
                rowcount,
                now,
            )
            if rowcount == 0:
                return False

            # Allocate kernel resources in the same transaction.
            # This ensures resource allocation happens atomically with the
            # kernel status transition to RUNNING, rather than waiting for
            # the session-level RUNNING transition.
            agent_id = current.agent if current else None
            await self._allocate_kernel_resources(
                db_sess, KernelId(kernel_id), agent_id, occupied_slots
            )
            return True

    async def _allocate_kernel_resources(
        self,
        db_sess: SASession,
        kernel_id: KernelId,
        agent_id: AgentId | None,
        occupied_slots: ResourceSlot,
    ) -> None:
        """Activate resource allocations and increment agent resource usage.

        Must be called within an existing DB session/transaction.
        Idempotent: rows where used_at is already set are skipped.
        No-op if agent_id is None or occupied_slots is empty.

        Raises:
            AgentResourceCapacityExceeded: If any slot would exceed agent capacity.
        """
        if not agent_id or not occupied_slots:
            return
        slots = resource_slot_to_quantities(occupied_slots)
        for s in slots:
            alloc_result = await db_sess.execute(
                sa.update(ResourceAllocationRow)
                .where(
                    ResourceAllocationRow.kernel_id == kernel_id,
                    ResourceAllocationRow.slot_name == s.slot_name,
                    ResourceAllocationRow.free_at.is_(None),
                    ResourceAllocationRow.used_at.is_(None),
                )
                .values(used=s.quantity, used_at=sa.func.now())
            )
            if cast(CursorResult[Any], alloc_result).rowcount == 0:
                continue
            new_used = AgentResourceRow.used + s.quantity
            agent_result = await db_sess.execute(
                sa.update(AgentResourceRow)
                .where(
                    AgentResourceRow.agent_id == agent_id,
                    AgentResourceRow.slot_name == s.slot_name,
                    new_used <= AgentResourceRow.capacity,
                )
                .values(used=new_used)
            )
            if cast(CursorResult[Any], agent_result).rowcount == 0:
                raise AgentResourceCapacityExceeded(
                    f"Agent {agent_id}: capacity exceeded for slot '{s.slot_name}'"
                )
        log.debug(
            "[DBSource] Allocated resources for kernel {} on agent {}",
            kernel_id,
            agent_id,
        )

    async def update_kernel_status_preparing(self, kernel_id: UUID) -> bool:
        """
        Update kernel status to PREPARING.
        Uses UPDATE WHERE to ensure atomic state transition.

        :param kernel_id: Kernel ID to update
        :return: True if update was successful, False otherwise
        """
        async with self._begin_session_read_committed() as db_sess:
            now = await self._get_db_now_in_session(db_sess)
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
                        KernelRow.__table__.c.status_history,
                        (),
                        {KernelStatus.PREPARING.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)
            return cast(CursorResult[Any], result).rowcount > 0

    async def update_kernel_status_cancelled(self, kernel_id: UUID, reason: str) -> bool:
        """
        Update kernel status to CANCELLED.
        Uses UPDATE WHERE to ensure atomic state transition.
        Also marks resource allocations as freed (PENDING~CREATING kernels have no used value).

        :param kernel_id: Kernel ID to update
        :param reason: Cancellation reason
        :return: True if update was successful, False otherwise
        """
        async with self._begin_session_read_committed() as db_sess:
            now = await self._get_db_now_in_session(db_sess)
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
                        KernelRow.__table__.c.status_history,
                        (),
                        {KernelStatus.CANCELLED.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)
            updated = cast(CursorResult[Any], result).rowcount > 0

            if updated:
                await db_sess.execute(
                    sa.update(ResourceAllocationRow)
                    .where(
                        ResourceAllocationRow.kernel_id == kernel_id,
                        ResourceAllocationRow.free_at.is_(None),
                    )
                    .values(free_at=sa.func.now())
                )
        return updated

    async def update_kernel_status_terminated(
        self, kernel_id: UUID, reason: str, exit_code: int | None = None
    ) -> bool:
        """
        Update kernel status to TERMINATED.
        Uses UPDATE WHERE to ensure atomic state transition.
        Also frees normalized resource allocations and decrements agent_resources.used.

        :param kernel_id: Kernel ID to update
        :param reason: Termination reason
        :param exit_code: Process exit code
        :return: True if update was successful, False otherwise
        """
        async with self._begin_session_read_committed() as db_sess:
            now = await self._get_db_now_in_session(db_sess)
            stmt = (
                sa.update(KernelRow)
                .where(
                    KernelRow.id == kernel_id,
                )
                .values(
                    status=KernelStatus.TERMINATED,
                    status_info=reason,
                    status_changed=now,
                    terminated_at=now,
                    status_data=sql_json_merge(
                        KernelRow.__table__.c.status_data,
                        ("kernel",),
                        {"exit_code": exit_code},
                    ),
                    status_history=sql_json_merge(
                        KernelRow.__table__.c.status_history,
                        (),
                        {KernelStatus.TERMINATED.name: now.isoformat()},
                    ),
                )
                .returning(KernelRow.agent)
            )
            result = await db_sess.execute(stmt)
            row = result.first()
            if row is None:
                return False
            agent_id: str | None = row[0]

            # Free resource allocations in the same transaction
            ar = AgentResourceRow.__table__
            released = (
                await db_sess.execute(
                    sa.update(ResourceAllocationRow)
                    .where(
                        ResourceAllocationRow.kernel_id == kernel_id,
                        ResourceAllocationRow.free_at.is_(None),
                    )
                    .values(free_at=sa.func.now())
                    .returning(ResourceAllocationRow.slot_name, ResourceAllocationRow.used)
                )
            ).all()
            if agent_id and released:
                for r in released:
                    if r.used is None:
                        continue
                    new_used = sa.func.greatest(ar.c.used - r.used, 0)
                    await db_sess.execute(
                        sa.update(ar)
                        .where(ar.c.agent_id == agent_id, ar.c.slot_name == r.slot_name)
                        .values(used=new_used)
                    )
        return True

    async def reset_kernels_to_pending_for_sessions(
        self, session_ids: list[SessionId], reason: str
    ) -> int:
        """
        Reset kernels to PENDING status for the given sessions.

        This is used when sessions exceed max retries and need to be rescheduled.
        Clears agent assignments and resets retry count in status_data.

        :param session_ids: List of session IDs whose kernels should be reset
        :param reason: The reason for the reset
        :return: The number of kernels reset
        """
        if not session_ids:
            return 0

        status_data = {"retries": 0}

        async with self._begin_session_read_committed() as db_sess:
            now = await self._get_db_now_in_session(db_sess)
            stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.session_id.in_(session_ids),
                        KernelRow.status.in_(KernelStatus.retriable_statuses()),
                    )
                )
                .values(
                    agent=None,
                    agent_addr=None,
                    status=KernelStatus.PENDING,
                    status_info=reason,
                    status_changed=now,
                    status_data=sql_json_merge(
                        KernelRow.__table__.c.status_data,
                        ("scheduler",),
                        obj=status_data,
                    ),
                    status_history=sql_json_merge(
                        KernelRow.__table__.c.status_history,
                        (),
                        {KernelStatus.PENDING.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)
            return cast(CursorResult[Any], result).rowcount

    async def get_agent_ids_for_sessions(
        self, session_ids: list[SessionId]
    ) -> dict[SessionId, list[AgentId]]:
        """
        Get agent IDs assigned to kernels for the given sessions.

        This is used before resetting kernels to PENDING to record
        which agents failed, so the scheduler can deprioritize them on retry.

        :param session_ids: List of session IDs to look up
        :return: Mapping of session ID to list of assigned agent IDs
        """
        if not session_ids:
            return {}

        async with self._begin_readonly_read_committed() as db_conn:
            stmt = sa.select(
                KernelRow.session_id,
                KernelRow.agent,
            ).where(
                sa.and_(
                    KernelRow.session_id.in_(session_ids),
                    KernelRow.agent.isnot(None),
                    KernelRow.status.in_(KernelStatus.retriable_statuses()),
                )
            )
            rows = (await db_conn.execute(stmt)).fetchall()

        result: dict[SessionId, list[AgentId]] = defaultdict(list)
        for row in rows:
            result[row.session_id].append(AgentId(row.agent))
        return dict(result)

    async def update_kernels_to_creating_for_sessions(
        self, session_ids: list[SessionId], reason: str
    ) -> int:
        """
        Update kernels to CREATING status for the given sessions.

        This is used when sessions transition from PREPARED to CREATING.
        Only updates kernels that are currently in PREPARED status.

        :param session_ids: List of session IDs whose kernels should be updated
        :param reason: The reason for the status change
        :return: The number of kernels updated
        """
        if not session_ids:
            return 0

        async with self._begin_session_read_committed() as db_sess:
            now = await self._get_db_now_in_session(db_sess)
            stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.session_id.in_(session_ids),
                        KernelRow.status == KernelStatus.PREPARED,
                    )
                )
                .values(
                    status=KernelStatus.CREATING,
                    status_info=reason,
                    status_changed=now,
                    status_history=sql_json_merge(
                        KernelRow.__table__.c.status_history,
                        (),
                        {KernelStatus.CREATING.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)
            return cast(CursorResult[Any], result).rowcount

    async def update_kernels_to_terminated(self, kernel_ids: list[str], reason: str) -> int:
        """
        Update multiple kernels to TERMINATED status.

        :param kernel_ids: List of kernel ID strings to update
        :param reason: Termination reason
        :return: Number of kernels updated
        """
        if not kernel_ids:
            return 0

        kernel_uuids = [UUID(kid) for kid in kernel_ids]

        async with self._begin_session_read_committed() as db_sess:
            now = await self._get_db_now_in_session(db_sess)

            # Fetch kernel_id and agent_id before updating status
            kernel_agent_query = sa.select(KernelRow.id, KernelRow.agent).where(
                KernelRow.id.in_(kernel_uuids),
            )
            kernel_agent_rows = (await db_sess.execute(kernel_agent_query)).all()

            stmt = (
                sa.update(KernelRow)
                .where(KernelRow.id.in_(kernel_uuids))
                .values(
                    status=KernelStatus.TERMINATED,
                    status_info=reason,
                    status_changed=now,
                    terminated_at=now,
                    status_history=sql_json_merge(
                        KernelRow.__table__.c.status_history,
                        (),
                        {KernelStatus.TERMINATED.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)

            # Free resource allocations and decrement agent_resources for each kernel
            ar = AgentResourceRow.__table__
            for kernel_id, agent_id in kernel_agent_rows:
                released = (
                    await db_sess.execute(
                        sa.update(ResourceAllocationRow)
                        .where(
                            ResourceAllocationRow.kernel_id == kernel_id,
                            ResourceAllocationRow.free_at.is_(None),
                        )
                        .values(free_at=sa.func.now())
                        .returning(ResourceAllocationRow.slot_name, ResourceAllocationRow.used)
                    )
                ).all()
                if agent_id and released:
                    for r in released:
                        if r.used is None:
                            continue
                        new_used = sa.func.greatest(ar.c.used - r.used, 0)
                        await db_sess.execute(
                            sa.update(ar)
                            .where(ar.c.agent_id == agent_id, ar.c.slot_name == r.slot_name)
                            .values(used=new_used)
                        )

            return cast(CursorResult[Any], result).rowcount

    async def update_kernels_to_pulling_for_image(
        self,
        agent_id: AgentId,
        image: str,
        image_ref: str | None = None,
        image_id: UUID | None = None,
    ) -> int:
        """
        Update kernel status from PREPARING to PULLING for the specified image on an agent.

        :param agent_id: The agent ID where kernels should be updated
        :param image: The image name to match kernels
        :param image_ref: Optional image reference (canonical format)
        :param image_id: Optional image UUID; when provided, matches by image_id instead of name
        :return: Number of kernels updated
        """
        async with self._begin_session_read_committed() as db_sess:
            now = await self._get_db_now_in_session(db_sess)
            # Prefer image_id (UUID) for matching when available
            if image_id is not None:
                image_condition = KernelRow.image_id == image_id
            else:
                # Use image_ref if provided (canonical format), otherwise use image
                image_to_match = image_ref if image_ref else image
                image_condition = KernelRow.image == image_to_match
            # Find kernels on this agent with this image in SCHEDULED or PREPARING state.
            # SCHEDULED is included because image pulling can start before kernel
            # transitions to PREPARING (which happens in create_kernel RPC).
            stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.agent == agent_id,
                        image_condition,
                        KernelRow.status.in_([
                            KernelStatus.SCHEDULED,
                            KernelStatus.PREPARING,
                        ]),
                    )
                )
                .values(
                    status=KernelStatus.PULLING,
                    status_history=sql_json_merge(
                        KernelRow.__table__.c.status_history,
                        (),
                        {KernelStatus.PULLING.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)
            return cast(CursorResult[Any], result).rowcount

    async def update_kernels_to_prepared_for_image(
        self,
        agent_id: AgentId,
        image: str,
        image_ref: str | None = None,
        image_id: UUID | None = None,
    ) -> int:
        """
        Update kernel status to PREPARED for the specified image on an agent.
        Updates kernels in both PULLING and PREPARING states.

        :param agent_id: The agent ID where kernels should be updated
        :param image: The image name to match kernels
        :param image_ref: Optional image reference (canonical format)
        :param image_id: Optional image UUID; when provided, matches by image_id instead of name
        :return: Number of kernels updated
        """
        async with self._begin_session_read_committed() as db_sess:
            now = await self._get_db_now_in_session(db_sess)
            # Prefer image_id (UUID) for matching when available
            if image_id is not None:
                image_condition = KernelRow.image_id == image_id
            else:
                # Use image_ref if provided (canonical format), otherwise use image
                image_to_match = image_ref if image_ref else image
                image_condition = KernelRow.image == image_to_match
            # Find kernels on this agent with this image in SCHEDULED, PULLING or PREPARING state
            # and update them to PREPARED.
            # SCHEDULED is included because when image already exists, ImagePullFinishedEvent
            # arrives before kernel transitions to PREPARING (which happens in create_kernel RPC).
            stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.agent == agent_id,
                        image_condition,
                        KernelRow.status.in_([
                            KernelStatus.SCHEDULED,
                            KernelStatus.PULLING,
                            KernelStatus.PREPARING,
                        ]),
                    )
                )
                .values(
                    status=KernelStatus.PREPARED,
                    status_history=sql_json_merge(
                        KernelRow.__table__.c.status_history,
                        (),
                        {KernelStatus.PREPARED.name: now.isoformat()},
                    ),
                )
            )
            result = await db_sess.execute(stmt)
            return cast(CursorResult[Any], result).rowcount

    async def cancel_kernels_for_failed_image(
        self,
        agent_id: AgentId,
        image: str,
        error_msg: str,
        image_ref: str | None = None,
        image_id: UUID | None = None,
    ) -> set[SessionId]:
        """Cancel SCHEDULED/PULLING/PREPARING kernels of a failed-to-pull
        image on an agent and free their ``resource_allocations`` rows in
        the same transaction. Returns affected session IDs.
        """
        async with self._begin_session_read_committed() as db_sess:
            now = await self._get_db_now_in_session(db_sess)
            # Prefer image_id (UUID) for matching when available
            if image_id is not None:
                image_condition = KernelRow.image_id == image_id
            else:
                image_to_match = image_ref if image_ref else image
                image_condition = KernelRow.image == image_to_match
            # SCHEDULED is included because image pull failure can occur
            # before the kernel transitions to PREPARING.
            stmt = (
                sa.update(KernelRow)
                .where(
                    sa.and_(
                        KernelRow.agent == agent_id,
                        image_condition,
                        KernelRow.status.in_([
                            KernelStatus.SCHEDULED,
                            KernelStatus.PULLING,
                            KernelStatus.PREPARING,
                        ]),
                    )
                )
                .values(
                    status=KernelStatus.CANCELLED,
                    status_info=f"Image pull failed: {error_msg}",
                    status_history=sql_json_merge(
                        KernelRow.__table__.c.status_history,
                        (),
                        {KernelStatus.CANCELLED.name: now.isoformat()},
                    ),
                )
                .returning(KernelRow.id, KernelRow.session_id)
            )
            result = await db_sess.execute(stmt)
            cancelled_rows = result.all()
            cancelled_kernel_ids = [row.id for row in cancelled_rows]

            await self._free_kernel_allocations(db_sess, cancelled_kernel_ids, now)

            return {row.session_id for row in cancelled_rows}

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
                now = await self._get_db_now_in_session(db_sess)
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
                            SessionRow.__table__.c.status_history,
                            (),
                            {SessionStatus.CANCELLED.name: now.isoformat()},
                        ),
                    )
                )
                result = await db_sess.execute(stmt)
                return cast(CursorResult[Any], result).rowcount > 0
        return False

    async def check_available_image(self, image_id: ImageID, domain: str, user_uuid: UUID) -> None:
        """
        Check if an image is available in the database for a given domain and user.
        Raises ImageNotFound if the image is not found.

        :param image_id: The pre-resolved image UUID to check
        :param domain: The domain to check within
        :param user_uuid: The user UUID to check within
        :raises ImageNotFound: If the image is not found
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            image_row = await db_sess.scalar(sa.select(ImageRow).where(ImageRow.id == image_id))
            if image_row is None:
                raise ImageNotFound
            if (
                _owner_id := image_row.labels.get("ai.backend.customized-image.owner")
            ) and _owner_id != f"user:{user_uuid}":
                raise ImageNotFound
            if not image_row.is_local:
                query = (
                    sa.select(domains.c.allowed_docker_registries)
                    .select_from(domains)
                    .where(domains.c.name == domain)
                )
                allowed_registries = await db_sess.scalar(query)
                if allowed_registries is None or image_row.registry not in allowed_registries:
                    raise ImageNotFound

    async def update_sessions_to_running(self, sessions_data: list[SessionRunningData]) -> None:
        """No-op after Phase 3 (BA-4308).

        Previously wrote sessions.occupying_slots JSONB.  The column is now
        deprecated — resource allocations are tracked via the normalized
        resource_allocations / agent_resources tables.
        """

    async def _resolve_image_configs(
        self, db_sess: SASession, unique_images: set[ImageIdentifier]
    ) -> dict[UUID, ImageConfigData]:
        """
        Resolve image configurations for the given unique images.

        Uses ImageConditions.by_identifiers for consistent query pattern.

        :param db_sess: Database session to use
        :param unique_images: Set of ImageIdentifier objects to resolve
        :return: Dictionary mapping image UUIDs to ImageConfigData
        """
        if not unique_images:
            return {}

        # Convert to (canonical, architecture) tuples for condition
        identifiers = [(img.canonical, img.architecture) for img in unique_images]

        # Query all images at once with registry info using ImageConditions
        condition = ImageConditions.by_identifiers(identifiers)
        stmt = sa.select(ImageRow).where(condition()).options(selectinload(ImageRow.registry_row))

        result = await db_sess.execute(stmt)
        image_rows = result.scalars().all()

        # Convert to ImageConfigData
        image_configs: dict[UUID, ImageConfigData] = {}
        for image_row in image_rows:
            try:
                img_ref = image_row.image_ref
                registry_row = image_row.registry_row

                image_config = ImageConfigData(
                    id=image_row.id,
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
                # Use the image UUID as key for reliable matching
                image_configs[image_row.id] = image_config
            except Exception as e:
                log.error("Failed to process image {}: {}", image_row.name, e)
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
                        KernelRow.image_id,
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
                    agent_id=AgentId(kernel.agent) if kernel.agent else None,
                    agent_addr=kernel.agent_addr,
                    scaling_group=kernel.scaling_group or "",
                    image=kernel.image or "",
                    image_id=kernel.image_id,
                    architecture=kernel.architecture or "",
                    status=kernel.status,
                    status_changed=kernel.status_changed.timestamp()
                    if kernel.status_changed
                    else None,
                )
                kernels_data.append(kernel_data)

            scheduled_session = ScheduledSessionData(
                session_id=session.id,
                creation_id=session.creation_id or "",
                access_key=AccessKey(session.access_key) if session.access_key else AccessKey(""),
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
                        KernelRow.image_id,
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
                    creation_id=session.creation_id or "",
                    access_key=AccessKey(session.access_key)
                    if session.access_key
                    else AccessKey(""),
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
                KernelRow.image_id,
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
                    image_id=row.image_id,
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
                SessionRow.network_type,
                SessionRow.network_id,
                KernelRow.id.label("kernel_id"),
                KernelRow.agent,
                KernelRow.agent_addr,
                KernelRow.scaling_group,
                KernelRow.image,
                KernelRow.image_id,
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
        session_data: dict[SessionId, dict[str, Any]] = defaultdict(lambda: {"kernels": []})
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
                    "network_type": row.network_type,
                    "network_id": row.network_id,
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
                    "image_id": row.image_id,
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
                log.warning("User info not found for session {}", session_id)
                continue

            # Convert kernels
            kernel_bindings = [
                KernelBindingData(
                    kernel_id=k["kernel_id"],
                    agent_id=k["agent"],
                    agent_addr=k["agent_addr"],
                    scaling_group=k["scaling_group"],
                    image=k["image"],
                    image_id=k["image_id"],
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
                    network_type=session_info["network_type"],
                    network_id=session_info["network_id"],
                )
            )

        return sessions_for_start

    async def mark_session_cancelled(
        self, session_id: SessionId, error_info: ErrorStatusInfo, reason: str = "FAILED_TO_START"
    ) -> None:
        """
        Mark a session as cancelled with error information.
        Used when session fails to start.
        """
        async with self._begin_session_read_committed() as db_sess:
            now = await self._get_db_now_in_session(db_sess)

            # Update session status with status_history
            stmt = (
                sa.update(SessionRow)
                .where(SessionRow.id == session_id)
                .values(
                    status=SessionStatus.CANCELLED,
                    status_info=reason,
                    status_data=error_info,  # Store ErrorStatusInfo as status_data in DB
                    status_history=sql_json_merge(
                        SessionRow.__table__.c.status_history,
                        (),
                        {SessionStatus.CANCELLED.name: now.isoformat()},
                    ),
                )
            )
            await db_sess.execute(stmt)

            # Update kernel statuses with status_history
            kernel_stmt = (
                sa.update(KernelRow)
                .where(KernelRow.session_id == session_id)
                .values(
                    status=KernelStatus.CANCELLED,
                    status_changed=now,
                    status_info=reason,
                    status_history=sql_json_merge(
                        KernelRow.__table__.c.status_history,
                        (),
                        {KernelStatus.CANCELLED.name: now.isoformat()},
                    ),
                )
            )
            await db_sess.execute(kernel_stmt)

            # Mark resource allocations as freed for all kernels in this session
            kernel_ids_subq = (
                sa.select(KernelRow.id).where(KernelRow.session_id == session_id).scalar_subquery()
            )
            await db_sess.execute(
                sa.update(ResourceAllocationRow)
                .where(
                    ResourceAllocationRow.kernel_id.in_(kernel_ids_subq),
                    ResourceAllocationRow.free_at.is_(None),
                )
                .values(free_at=sa.func.now())
            )

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
                        SessionRow.__table__.c.status_data,
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
                        KernelRow.__table__.c.status_data,
                        ("error",),
                        obj=error_info,
                    ),
                )
            )
            await db_sess.execute(kernel_stmt)

    async def get_container_info_for_kernels(self, session_id: SessionId) -> dict[UUID, str | None]:
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
        network_id: str | None,
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
        Calculate total resource slots from normalized agent_resources table.

        :return: TotalResourceData with total used, free, and capable slots
        """
        ar = AgentResourceRow.__table__
        ag = AgentRow.__table__

        async with self._begin_readonly_read_committed() as conn:
            stmt = (
                sa.select(
                    ar.c.slot_name,
                    sa.func.sum(ar.c.capacity).label("total_capacity"),
                    sa.func.sum(ar.c.used).label("total_used"),
                )
                .select_from(ar.join(ag, ar.c.agent_id == ag.c.id))
                .where(
                    ag.c.status == AgentStatus.ALIVE,
                    ag.c.schedulable == sa.true(),
                )
                .group_by(ar.c.slot_name)
            )
            result = await conn.execute(stmt)

            capacity: dict[str, Decimal] = {}
            used: dict[str, Decimal] = {}
            for row in result:
                capacity[row.slot_name] = row.total_capacity
                used[row.slot_name] = row.total_used

        total_capacity_slots = ResourceSlot(capacity)
        total_used_slots = ResourceSlot(used)
        total_free_slots = total_capacity_slots - total_used_slots

        return TotalResourceData(
            total_used_slots=total_used_slots,
            total_free_slots=total_free_slots,
            total_capacity_slots=total_capacity_slots,
        )

    # =========================================================================
    # Normalized resource allocation write operations
    # =========================================================================

    async def allocate_kernel_resources(
        self,
        kernel_id: UUID,
        agent_id: str,
        slots: Sequence[SlotQuantity],
    ) -> int:
        """Set used values on allocations and increment agent_resources.used.

        This method is idempotent: re-calling with the same kernel_id + slot_name
        will not double-increment agent_resources.used because only allocation rows
        where used_at IS NULL are updated.

        Returns:
            Number of slots actually allocated (0 if already allocated).

        Raises:
            AgentResourceCapacityExceeded: If any slot would exceed agent capacity.
        """
        if not slots:
            return 0
        ar = AgentResourceRow.__table__
        allocated_count = 0
        async with self._begin_session_read_committed() as db_sess:
            for s in slots:
                # Only update allocations that haven't been activated yet.
                # used_at IS NULL ensures idempotency: re-calls are no-ops.
                alloc_result = await db_sess.execute(
                    sa.update(ResourceAllocationRow)
                    .where(
                        ResourceAllocationRow.kernel_id == kernel_id,
                        ResourceAllocationRow.slot_name == s.slot_name,
                        ResourceAllocationRow.free_at.is_(None),
                        ResourceAllocationRow.used_at.is_(None),
                    )
                    .values(used=s.quantity, used_at=sa.func.now())
                )
                if cast(CursorResult[Any], alloc_result).rowcount == 0:
                    # Already allocated or no matching row — skip agent_resources update
                    continue
                new_used = ar.c.used + s.quantity
                result = await db_sess.execute(
                    sa.update(ar)
                    .where(
                        ar.c.agent_id == agent_id,
                        ar.c.slot_name == s.slot_name,
                        new_used <= ar.c.capacity,
                    )
                    .values(used=new_used)
                )
                if cast(CursorResult[Any], result).rowcount == 0:
                    raise AgentResourceCapacityExceeded(
                        f"Agent {agent_id}: capacity exceeded for slot '{s.slot_name}'"
                    )
                allocated_count += 1
            return allocated_count

    async def allocate_session_kernel_resources(
        self,
        allocations: Sequence[tuple[UUID, str, Sequence[SlotQuantity]]],
    ) -> int:
        """Allocate resources for multiple kernels in a single transaction.

        This ensures all-or-nothing semantics: if any kernel's allocation fails,
        all allocations in this batch are rolled back.

        Each individual kernel allocation is idempotent (used_at IS NULL guard).

        Args:
            allocations: List of (kernel_id, agent_id, slots) tuples.

        Returns:
            Total number of slots allocated across all kernels.

        Raises:
            AgentResourceCapacityExceeded: If any slot would exceed agent capacity.
        """
        if not allocations:
            return 0
        ar = AgentResourceRow.__table__
        total_allocated = 0
        async with self._begin_session_read_committed() as db_sess:
            for kernel_id, agent_id, slots in allocations:
                for s in slots:
                    alloc_result = await db_sess.execute(
                        sa.update(ResourceAllocationRow)
                        .where(
                            ResourceAllocationRow.kernel_id == kernel_id,
                            ResourceAllocationRow.slot_name == s.slot_name,
                            ResourceAllocationRow.free_at.is_(None),
                            ResourceAllocationRow.used_at.is_(None),
                        )
                        .values(used=s.quantity, used_at=sa.func.now())
                    )
                    if cast(CursorResult[Any], alloc_result).rowcount == 0:
                        continue
                    new_used = ar.c.used + s.quantity
                    result = await db_sess.execute(
                        sa.update(ar)
                        .where(
                            ar.c.agent_id == agent_id,
                            ar.c.slot_name == s.slot_name,
                            new_used <= ar.c.capacity,
                        )
                        .values(used=new_used)
                    )
                    if cast(CursorResult[Any], result).rowcount == 0:
                        raise AgentResourceCapacityExceeded(
                            f"Agent {agent_id}: capacity exceeded for slot '{s.slot_name}'"
                        )
                    total_allocated += 1
            return total_allocated

    async def update_running_and_allocate_resources(
        self,
        sessions_data: list[SessionRunningData],
        allocations: Sequence[tuple[UUID, str, Sequence[SlotQuantity]]],
    ) -> int:
        """Atomically update session occupying_slots AND allocate kernel resources.

        Single transaction guarantees:
        - If allocation fails, session update is also rolled back.
        - Idempotent per kernel (used_at IS NULL guard).

        Returns:
            Total number of slots allocated across all kernels.

        Raises:
            AgentResourceCapacityExceeded: If any slot would exceed agent capacity.
        """
        ar = AgentResourceRow.__table__
        total_allocated = 0
        async with self._begin_session_read_committed() as db_sess:
            # Phase 3 (BA-4308): Legacy JSONB write to sessions.occupying_slots
            # removed.  The sessions.occupying_slots column is retained for
            # historical audit but no longer written to.  Resource allocations
            # are tracked via the normalized tables below.

            # Allocate kernel resources
            for kernel_id, agent_id, slots in allocations:
                for s in slots:
                    alloc_result = await db_sess.execute(
                        sa.update(ResourceAllocationRow)
                        .where(
                            ResourceAllocationRow.kernel_id == kernel_id,
                            ResourceAllocationRow.slot_name == s.slot_name,
                            ResourceAllocationRow.free_at.is_(None),
                            ResourceAllocationRow.used_at.is_(None),
                        )
                        .values(used=s.quantity, used_at=sa.func.now())
                    )
                    if cast(CursorResult[Any], alloc_result).rowcount == 0:
                        continue
                    new_used = ar.c.used + s.quantity
                    result = await db_sess.execute(
                        sa.update(ar)
                        .where(
                            ar.c.agent_id == agent_id,
                            ar.c.slot_name == s.slot_name,
                            new_used <= ar.c.capacity,
                        )
                        .values(used=new_used)
                    )
                    if cast(CursorResult[Any], result).rowcount == 0:
                        raise AgentResourceCapacityExceeded(
                            f"Agent {agent_id}: capacity exceeded for slot '{s.slot_name}'"
                        )
                    total_allocated += 1
            return total_allocated

    async def free_kernel_resources(
        self,
        kernel_id: UUID,
        agent_id: str,
    ) -> int:
        """Set free_at on allocations and decrement agent_resources.used.

        Returns:
            Number of allocation rows freed.
        """
        ar = AgentResourceRow.__table__
        async with self._begin_session_read_committed() as db_sess:
            released = (
                await db_sess.execute(
                    sa.update(ResourceAllocationRow)
                    .where(
                        ResourceAllocationRow.kernel_id == kernel_id,
                        ResourceAllocationRow.free_at.is_(None),
                    )
                    .values(free_at=sa.func.now())
                    .returning(ResourceAllocationRow.slot_name, ResourceAllocationRow.used)
                )
            ).all()
            if not released:
                return 0
            for r in released:
                if r.used is None:
                    continue
                new_used = sa.func.greatest(ar.c.used - r.used, 0)
                await db_sess.execute(
                    sa.update(ar)
                    .where(ar.c.agent_id == agent_id, ar.c.slot_name == r.slot_name)
                    .values(used=new_used)
                )
            return len(released)

    # =========================================================================
    # Handler-specific methods for SessionLifecycleHandler pattern
    # =========================================================================

    async def fetch_sessions_for_handler(
        self,
        scaling_group: str,
        session_statuses: list[SessionStatus],
        kernel_statuses: list[KernelStatus] | None,
    ) -> list[SessionWithKernels]:
        """Fetch sessions for handler execution based on status filters.

        This method is for SessionLifecycleHandler. For SessionPromotionHandler,
        use fetch_sessions_for_promotion() which supports ALL/ANY/NOT_ANY conditions.

        Uses SessionRow.to_session_info() and KernelRow.to_kernel_info() for
        unified data representation across all handlers.

        Args:
            scaling_group: The scaling group to filter by
            session_statuses: Session statuses to include
            kernel_statuses: If non-None, include sessions that have at least one
                           kernel in these statuses (simple filtering).
                           If None, include sessions regardless of kernel status.

        Returns:
            List of SessionWithKernels containing SessionInfo and KernelInfo objects.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            stmt = (
                sa.select(SessionRow)
                .where(
                    SessionRow.scaling_group_name == scaling_group,
                    SessionRow.status.in_(session_statuses),
                )
                .options(selectinload(SessionRow.kernels))
            )
            result = await db_sess.execute(stmt)
            sessions = result.scalars().all()

            handler_sessions: list[SessionWithKernels] = []
            for session in sessions:
                # If kernel_statuses is specified (not None), check if any kernel matches
                # For ALL/ANY/NOT_ANY conditions, use fetch_sessions_for_promotion() instead
                if kernel_statuses is not None:
                    has_matching_kernel = any(
                        kernel.status in kernel_statuses for kernel in session.kernels
                    )
                    if not has_matching_kernel:
                        continue

                # Convert using Row converters
                handler_sessions.append(
                    SessionWithKernels(
                        session_info=session.to_session_info(),
                        kernel_infos=[kernel.to_kernel_info() for kernel in session.kernels],
                    )
                )

            return handler_sessions

    async def search_kernels_for_handler(
        self,
        querier: BatchQuerier,
    ) -> KernelListResult:
        """Search kernels for kernel handler execution.

        This method is for KernelLifecycleHandler. It queries kernels
        directly using BatchQuerier conditions.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.
                     Use KernelConditions for filtering.

        Returns:
            KernelListResult containing KernelInfo objects.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            stmt = sa.select(KernelRow)
            result = await execute_batch_querier(db_sess, stmt, querier)
            return KernelListResult(
                items=[row.KernelRow.to_kernel_info() for row in result.rows],
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_sessions_for_handler(
        self,
        querier: BatchQuerier,
    ) -> list[SessionInfo]:
        """Search sessions without kernel data for handlers.

        This method uses EXISTS subqueries for optimized kernel condition checking
        without loading kernel data.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            List of SessionInfo matching all conditions.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            stmt = sa.select(SessionRow)
            result = await execute_batch_querier(db_sess, stmt, querier)
            return [row.SessionRow.to_session_info() for row in result.rows]

    async def update_with_history(
        self,
        updater: BatchUpdater[SessionRow],
        bulk_creator: BulkCreator[SessionSchedulingHistoryRow],
    ) -> int:
        """Update session statuses and record history in same transaction.

        This method combines batch status update with history recording,
        ensuring both operations are atomic within a single transaction.
        Uses merge logic to prevent duplicate history records when status
        doesn't change.

        Args:
            updater: BatchUpdater containing spec and conditions for session update
            bulk_creator: BulkCreator containing specs for history records

        Returns:
            Number of sessions updated
        """
        async with self._begin_session_read_committed() as db_sess:
            # 1. Execute batch update
            update_result = await execute_batch_updater(db_sess, updater)

            # 2. Record history
            await self._record_scheduling_history(db_sess, bulk_creator)

            return update_result.updated_count

    async def create_scheduling_history(
        self,
        bulk_creator: BulkCreator[SessionSchedulingHistoryRow],
    ) -> int:
        """Create scheduling history records without status update.

        Used for recording skipped sessions where no status change occurs
        but the scheduling attempt should be recorded in history.

        Args:
            bulk_creator: BulkCreator containing specs for history records

        Returns:
            Number of history records created
        """
        if not bulk_creator.specs:
            return 0

        async with self._begin_session_read_committed() as db_sess:
            return await self._record_scheduling_history(db_sess, bulk_creator)

    async def _record_scheduling_history(
        self,
        db_sess: SASession,
        bulk_creator: BulkCreator[SessionSchedulingHistoryRow],
    ) -> int:
        """Record scheduling history with merge logic.

        Uses merge logic to prevent duplicate history records when status
        doesn't change - increments attempts count instead of creating new records.

        Args:
            db_sess: Database session
            bulk_creator: BulkCreator containing specs for history records

        Returns:
            Number of history records affected (merged + created)
        """
        # Build rows from specs
        new_rows = [spec.build_row() for spec in bulk_creator.specs]
        session_ids = [SessionId(row.session_id) for row in new_rows]

        # Get last history records for all sessions
        last_records = await self._get_last_session_histories_bulk(db_sess, session_ids)

        # Separate rows into merge and create groups
        merge_ids: list[UUID] = []
        create_rows: list[SessionSchedulingHistoryRow] = []

        for new_row in new_rows:
            last_row = last_records.get(SessionId(new_row.session_id))

            if last_row is not None and last_row.should_merge_with(new_row):
                merge_ids.append(last_row.id)
            else:
                create_rows.append(new_row)

        # Batch update attempts for merge group
        if merge_ids:
            await db_sess.execute(
                sa.update(SessionSchedulingHistoryRow)
                .where(SessionSchedulingHistoryRow.id.in_(merge_ids))
                .values(attempts=SessionSchedulingHistoryRow.attempts + 1)
            )

        # Batch insert for create group
        if create_rows:
            db_sess.add_all(create_rows)
            await db_sess.flush()

        return len(merge_ids) + len(create_rows)

    async def _get_last_session_histories_bulk(
        self,
        db_sess: SASession,
        session_ids: list[SessionId],
    ) -> dict[SessionId, SessionSchedulingHistoryRow]:
        """Get last history records for multiple sessions efficiently."""
        if not session_ids:
            return {}

        # Use DISTINCT ON to get latest record per session
        query = (
            sa.select(SessionSchedulingHistoryRow)
            .where(SessionSchedulingHistoryRow.session_id.in_(session_ids))
            .distinct(SessionSchedulingHistoryRow.session_id)
            .order_by(
                SessionSchedulingHistoryRow.session_id,
                SessionSchedulingHistoryRow.created_at.desc(),
            )
        )
        result = await db_sess.execute(query)
        rows = result.scalars().all()
        return {SessionId(row.session_id): row for row in rows}

    async def get_last_session_histories(
        self,
        session_ids: list[SessionId],
    ) -> dict[SessionId, SessionSchedulingHistoryRow]:
        """Get last history records for multiple sessions (regardless of phase).

        Returns the most recent history record for each session. The caller
        should compare history.phase with the current phase to determine
        if attempts should be used or reset to 0.

        Args:
            session_ids: List of session IDs to fetch history for

        Returns:
            Dict mapping session_id to latest history record
        """
        if not session_ids:
            return {}

        async with self._begin_readonly_session_read_committed() as db_sess:
            # Use DISTINCT ON to get latest record per session (no phase filter)
            query = (
                sa.select(SessionSchedulingHistoryRow)
                .where(SessionSchedulingHistoryRow.session_id.in_(session_ids))
                .distinct(SessionSchedulingHistoryRow.session_id)
                .order_by(
                    SessionSchedulingHistoryRow.session_id,
                    SessionSchedulingHistoryRow.created_at.desc(),
                )
            )
            result = await db_sess.execute(query)
            rows = result.scalars().all()
            return {SessionId(row.session_id): row for row in rows}

    async def get_sessions_for_pull_by_ids(
        self,
        session_ids: list[SessionId],
    ) -> SessionsForPullWithImages:
        """
        Get sessions for image pulling by session IDs.

        This method is used by handlers that need additional session data
        beyond what the coordinator provides (HandlerSessionData).

        :param session_ids: List of session IDs to fetch
        :return: SessionsForPullWithImages object with sessions and image configs
        """
        if not session_ids:
            return SessionsForPullWithImages(sessions=[], image_configs={})

        async with self._begin_readonly_session_read_committed() as db_sess:
            # Get sessions with minimal fields needed for pulling
            sessions_for_pull = await self._fetch_sessions_for_pull_by_ids(db_sess, session_ids)

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

    async def _fetch_sessions_for_pull_by_ids(
        self,
        db_sess: SASession,
        session_ids: list[SessionId],
    ) -> list[SessionDataForPull]:
        """
        Get sessions with minimal fields needed for image pulling by session IDs.
        """
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
                KernelRow.image_id,
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
            .where(SessionRow.id.in_(session_ids))
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
                    image_id=row.image_id,
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

    async def get_sessions_for_start_by_ids(
        self,
        session_ids: list[SessionId],
    ) -> SessionsForStartWithImages:
        """
        Get sessions for starting by session IDs.

        This method is used by handlers that need additional session data
        beyond what the coordinator provides (HandlerSessionData).

        :param session_ids: List of session IDs to fetch
        :return: SessionsForStartWithImages object with sessions and image configs
        """
        if not session_ids:
            return SessionsForStartWithImages(sessions=[], image_configs={})

        async with self._begin_readonly_session_read_committed() as db_sess:
            # Get sessions with all fields needed for starting
            sessions_for_start = await self._fetch_sessions_for_start_by_ids(db_sess, session_ids)

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

    async def _fetch_sessions_for_start_by_ids(
        self,
        db_sess: SASession,
        session_ids: list[SessionId],
    ) -> list[SessionDataForStart]:
        """
        Get sessions with all fields needed for starting by session IDs.
        """
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
                SessionRow.network_type,
                SessionRow.network_id,
                KernelRow.id.label("kernel_id"),
                KernelRow.agent,
                KernelRow.agent_addr,
                KernelRow.scaling_group,
                KernelRow.image,
                KernelRow.image_id,
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
            .where(SessionRow.id.in_(session_ids))
            .order_by(SessionRow.created_at, SessionRow.id, KernelRow.cluster_idx)
        )
        result = await db_sess.execute(stmt)
        rows = result.fetchall()

        # Group rows by session
        session_data: dict[SessionId, dict[str, Any]] = defaultdict(lambda: {"kernels": []})
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
                    "network_type": row.network_type,
                    "network_id": row.network_id,
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
                    "image_id": row.image_id,
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
                log.warning("User info not found for session {}", session_id)
                continue

            # Convert kernels
            kernel_bindings = [
                KernelBindingData(
                    kernel_id=k["kernel_id"],
                    agent_id=k["agent"],
                    agent_addr=k["agent_addr"],
                    scaling_group=k["scaling_group"],
                    image=k["image"],
                    image_id=k["image_id"],
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
                    network_type=session_info["network_type"],
                    network_id=session_info["network_id"],
                )
            )

        return sessions_for_start

    # ========================================================================
    # Search methods (BatchQuerier pattern)
    # ========================================================================

    async def search_sessions_with_kernels(
        self,
        querier: BatchQuerier,
    ) -> SessionWithKernelsSearchResult:
        """Search sessions with kernel data and image configs.

        Returns session data with full kernel details and resolved image configs.
        Use this when kernel binding information is needed (e.g., image pulling).

        Uses separate queries for sessions, kernels, and images to avoid
        data duplication from JOINs and improve memory efficiency.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.
                     Use NoPagination for scheduler batch operations.
                     Conditions should target SessionRow columns.

        Returns:
            SessionWithKernelsSearchResult with sessions, image_configs, and pagination info

        Example:
            querier = BatchQuerier(
                pagination=NoPagination(),
                conditions=[
                    SessionConditions.by_scaling_group("default"),
                    SessionConditions.by_statuses([SessionStatus.SCHEDULED]),
                ],
                orders=[SessionOrders.created_at()],
            )
            result = await db_source.search_sessions_with_kernels(querier)
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            # 1. Query sessions
            session_query = sa.select(
                SessionRow.id,
                SessionRow.creation_id,
                SessionRow.access_key,
                SessionRow.status,
            )
            session_result = await execute_batch_querier(db_sess, session_query, querier)

            if not session_result.rows:
                return SessionWithKernelsSearchResult(
                    sessions=[],
                    image_configs={},
                    total_count=0,
                    has_next_page=False,
                    has_previous_page=False,
                )

            # Build session map
            session_ids: list[SessionId] = []
            sessions_map: dict[SessionId, SessionDataForPull] = {}
            for row in session_result.rows:
                session_ids.append(row.id)
                sessions_map[row.id] = SessionDataForPull(
                    session_id=row.id,
                    creation_id=row.creation_id,
                    access_key=row.access_key,
                    kernels=[],
                )

            # 2. Query kernels for these sessions
            kernel_query = (
                sa.select(
                    KernelRow.id,
                    KernelRow.session_id,
                    KernelRow.agent,
                    KernelRow.agent_addr,
                    KernelRow.scaling_group,
                    KernelRow.image,
                    KernelRow.image_id,
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
                    KernelRow.status,
                    KernelRow.status_changed,
                )
                .where(KernelRow.session_id.in_(session_ids))
                .order_by(KernelRow.session_id, KernelRow.cluster_idx)
            )
            kernel_result = await db_sess.execute(kernel_query)
            kernel_rows = kernel_result.fetchall()

            # Attach kernels to sessions and collect unique images
            unique_images: set[ImageIdentifier] = set()
            for row in kernel_rows:
                session_id = row.session_id
                if session_id not in sessions_map:
                    continue

                kernel_binding = KernelBindingData(
                    kernel_id=row.id,
                    agent_id=row.agent,
                    agent_addr=row.agent_addr,
                    scaling_group=row.scaling_group,
                    image=row.image,
                    image_id=row.image_id,
                    architecture=row.architecture,
                    status=row.status,
                    status_changed=(row.status_changed.timestamp() if row.status_changed else None),
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
                unique_images.add(
                    ImageIdentifier(canonical=row.image, architecture=row.architecture)
                )

            # 3. Resolve image configs
            image_configs = await self._resolve_image_configs(db_sess, unique_images)

            sessions = list(sessions_map.values())
            return SessionWithKernelsSearchResult(
                sessions=sessions,
                image_configs=image_configs,
                total_count=session_result.total_count,
                has_next_page=session_result.has_next_page,
                has_previous_page=session_result.has_previous_page,
            )

    async def search_sessions_with_kernels_and_user(
        self,
        querier: BatchQuerier,
    ) -> SessionWithKernelsAndUserSearchResult:
        """Search sessions with kernel data, user info, and image configs.

        Returns session data with full kernel details, user information, and resolved
        image configs. Use this when starting sessions (need user email/name for session).

        Uses separate queries for sessions, kernels, users, and images to avoid
        data duplication from JOINs and improve memory efficiency.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.
                     Use NoPagination for scheduler batch operations.
                     Conditions should target SessionRow columns.

        Returns:
            SessionWithKernelsAndUserSearchResult with sessions, image_configs, and pagination info

        Example:
            querier = BatchQuerier(
                pagination=NoPagination(),
                conditions=[
                    SessionConditions.by_scaling_group("default"),
                    SessionConditions.by_statuses([SessionStatus.PREPARED]),
                ],
                orders=[SessionOrders.created_at()],
            )
            result = await db_source.search_sessions_with_kernels_and_user(querier)
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            # 1. Query sessions
            session_query = sa.select(
                SessionRow.id,
                SessionRow.creation_id,
                SessionRow.access_key,
                SessionRow.session_type,
                SessionRow.name,
                SessionRow.environ,
                SessionRow.cluster_mode,
                SessionRow.user_uuid,
                SessionRow.network_type,
                SessionRow.network_id,
            )
            session_result = await execute_batch_querier(db_sess, session_query, querier)

            if not session_result.rows:
                return SessionWithKernelsAndUserSearchResult(
                    sessions=[],
                    image_configs={},
                    total_count=0,
                    has_next_page=False,
                    has_previous_page=False,
                )

            # Build session info map and collect user UUIDs
            session_ids: list[SessionId] = []
            session_info_map: dict[SessionId, dict[str, Any]] = {}
            user_uuids: set[UUID] = set()

            for row in session_result.rows:
                session_ids.append(row.id)
                session_info_map[row.id] = {
                    "id": row.id,
                    "creation_id": row.creation_id,
                    "access_key": row.access_key,
                    "session_type": row.session_type,
                    "name": row.name,
                    "environ": row.environ,
                    "cluster_mode": row.cluster_mode,
                    "user_uuid": row.user_uuid,
                    "network_type": row.network_type,
                    "network_id": row.network_id,
                    "kernels": [],
                }
                if row.user_uuid:
                    user_uuids.add(row.user_uuid)

            # 2. Query kernels for these sessions
            kernel_query = (
                sa.select(
                    KernelRow.id,
                    KernelRow.session_id,
                    KernelRow.agent,
                    KernelRow.agent_addr,
                    KernelRow.scaling_group,
                    KernelRow.image,
                    KernelRow.image_id,
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
                    KernelRow.status,
                    KernelRow.status_changed,
                )
                .where(KernelRow.session_id.in_(session_ids))
                .order_by(KernelRow.session_id, KernelRow.cluster_idx)
            )
            kernel_result = await db_sess.execute(kernel_query)
            kernel_rows = kernel_result.fetchall()

            # Attach kernels to sessions and collect unique images
            unique_images: set[ImageIdentifier] = set()
            for row in kernel_rows:
                session_id = row.session_id
                if session_id not in session_info_map:
                    continue

                kernel_binding = KernelBindingData(
                    kernel_id=row.id,
                    agent_id=row.agent,
                    agent_addr=row.agent_addr,
                    scaling_group=row.scaling_group,
                    image=row.image,
                    image_id=row.image_id,
                    architecture=row.architecture,
                    status=row.status,
                    status_changed=(row.status_changed.timestamp() if row.status_changed else None),
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
                session_info_map[session_id]["kernels"].append(kernel_binding)
                unique_images.add(
                    ImageIdentifier(canonical=row.image, architecture=row.architecture)
                )

            # 3. Query users
            user_map: dict[UUID, Any] = {}
            if user_uuids:
                user_query = sa.select(
                    UserRow.uuid,
                    UserRow.email,
                    UserRow.username,
                ).where(UserRow.uuid.in_(user_uuids))
                user_result = await db_sess.execute(user_query)
                user_map = {row.uuid: row for row in user_result.fetchall()}

            # 4. Resolve image configs
            image_configs = await self._resolve_image_configs(db_sess, unique_images)

            # Build SessionDataForStart objects
            sessions_for_start: list[SessionDataForStart] = []
            for session_id in session_ids:
                session_info = session_info_map[session_id]
                user_info = user_map.get(session_info["user_uuid"])
                if not user_info:
                    log.warning("User info not found for session {}", session_id)
                    continue

                sessions_for_start.append(
                    SessionDataForStart(
                        session_id=session_info["id"],
                        creation_id=session_info["creation_id"],
                        access_key=session_info["access_key"],
                        session_type=session_info["session_type"],
                        name=session_info["name"],
                        cluster_mode=session_info["cluster_mode"],
                        kernels=session_info["kernels"],
                        environ=session_info.get("environ") or {},
                        user_uuid=session_info["user_uuid"],
                        user_email=user_info.email,
                        user_name=user_info.username,
                        network_type=session_info["network_type"],
                        network_id=session_info["network_id"],
                    )
                )

            return SessionWithKernelsAndUserSearchResult(
                sessions=sessions_for_start,
                image_configs=image_configs,
                total_count=session_result.total_count,
                has_next_page=session_result.has_next_page,
                has_previous_page=session_result.has_previous_page,
            )

    async def search_sessions_with_kernels_for_handler(
        self,
        querier: BatchQuerier,
    ) -> list[SessionWithKernels]:
        """Search sessions with their kernels using SessionInfo/KernelInfo for handlers.

        This method uses the unified SessionInfo and KernelInfo types,
        loading full Row objects and converting via to_session_info()/to_kernel_info().

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.
                     Conditions should target SessionRow columns.

        Returns:
            List of SessionWithKernels containing SessionInfo and KernelInfo objects.
        """
        async with self._begin_readonly_session_read_committed() as db_sess:
            # 1. Query sessions (full rows for to_session_info conversion)
            session_query = sa.select(SessionRow)
            session_result = await execute_batch_querier(db_sess, session_query, querier)

            if not session_result.rows:
                return []

            # Build session map
            session_ids: list[SessionId] = []
            sessions_map: dict[SessionId, SessionWithKernels] = {}
            for row in session_result.rows:
                session_row: SessionRow = row.SessionRow
                session_ids.append(session_row.id)
                sessions_map[session_row.id] = SessionWithKernels(
                    session_info=session_row.to_session_info(),
                    kernel_infos=[],
                )

            # 2. Query kernels for these sessions (full rows for to_kernel_info conversion)
            kernel_query = (
                sa.select(KernelRow)
                .where(KernelConditions.by_session_ids(session_ids)())
                .order_by(KernelRow.session_id, KernelRow.cluster_idx)
            )
            kernel_result = await db_sess.execute(kernel_query)
            kernel_rows = kernel_result.scalars().all()

            # Attach kernels to sessions
            for kernel_row in kernel_rows:
                session_id = kernel_row.session_id
                if session_id in sessions_map:
                    sessions_map[session_id].kernel_infos.append(kernel_row.to_kernel_info())

            return list(sessions_map.values())

    async def lower_session_priority(
        self,
        session_ids: list[SessionId],
        amount: int,
        min_priority: int,
    ) -> None:
        """
        Lower the priority of sessions by a specified amount with a floor.

        Used when sessions exceed max scheduling retries (give_up) and need to be
        deprioritized before returning to PENDING for re-scheduling.

        :param session_ids: List of session IDs to update
        :param amount: Amount to subtract from current priority
        :param min_priority: Minimum priority floor (priority will not go below this)
        """
        if not session_ids:
            return

        async with self._begin_session_read_committed() as db_sess:
            # Use GREATEST to ensure priority doesn't go below min_priority
            new_priority = sa.func.greatest(SessionRow.priority - amount, min_priority)
            update_stmt = (
                sa.update(SessionRow)
                .where(SessionRow.id.in_(session_ids))
                .values(priority=new_priority)
            )
            await db_sess.execute(update_stmt)

    async def update_kernels_last_observed_at(
        self,
        kernel_observation_times: Mapping[UUID, datetime],
    ) -> int:
        """
        Update the last_observed_at timestamp for multiple kernels.

        Used by fair share observer to record when kernels were last observed
        for resource usage tracking. Each kernel can have a different observation
        time (e.g., terminated kernels use terminated_at, running kernels use now).

        :param kernel_observation_times: Mapping of kernel ID to observation timestamp
        :return: Number of kernels updated
        """
        if not kernel_observation_times:
            return 0

        async with self._begin_session_read_committed() as db_sess:
            total_updated = 0
            # Group by observation time for efficient batch updates
            time_to_kernels: dict[datetime, list[UUID]] = {}
            for kernel_id, observed_at in kernel_observation_times.items():
                time_to_kernels.setdefault(observed_at, []).append(kernel_id)

            for observed_at, kernel_ids in time_to_kernels.items():
                update_stmt = (
                    sa.update(KernelRow)
                    .where(KernelRow.id.in_(kernel_ids))
                    .values(last_observed_at=observed_at)
                )
                result = await db_sess.execute(update_stmt)
                total_updated += cast(CursorResult[Any], result).rowcount

            return total_updated

    async def get_db_now(self) -> datetime:
        """Get the current timestamp from the database.

        Used for consistent time handling across HA environments
        where server clocks may differ.

        Returns:
            Current database timestamp with timezone
        """
        async with self._begin_readonly_read_committed() as conn:
            result = await conn.execute(sa.select(sa.func.now()))
            return result.scalar_one()

    async def _get_db_now_in_session(self, db_sess: SASession) -> datetime:
        """Get the current timestamp from the database within an existing session.

        Use this when you already have an open session to avoid creating
        a new connection.

        Args:
            db_sess: The existing database session

        Returns:
            Current database timestamp with timezone
        """
        result = await db_sess.execute(sa.select(sa.func.now()))
        return result.scalar_one()

from __future__ import annotations

import copy
import logging
import uuid
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, cast, override
from uuid import UUID

import aiotools
import msgpack
import sqlalchemy as sa
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.entity.types import EntityRef, ScopeRef, ScopeType
from ai.backend.common.data.entity.types import (
    EntityType as VirtualScopeEntityType,
)
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import SlotName, VFolderID
from ai.backend.common.utils import nmget
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.group.types import (
    GroupData,
    ProjectMemberRoleSpec,
    UnassignUserFailure,
    UnassignUsersResult,
)
from ai.backend.manager.data.permission.types import (
    EntityType,
    RBACElementRef,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as LegacyScopeType,
)
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.resource import (
    ProjectHasActiveEndpointsError,
    ProjectHasActiveKernelsError,
    ProjectHasVFoldersMountedError,
    ProjectNotFound,
)
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow
from ai.backend.manager.models.group import groups
from ai.backend.manager.models.group.row import (
    GroupRow,
)
from ai.backend.manager.models.kernel import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    LIVE_STATUS,
    RESOURCE_USAGE_KERNEL_STATUSES,
    KernelRow,
    kernels,
)
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_usage import fetch_resource_usage
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.user import UserRow, users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderDeletionInfo,
    VFolderRow,
    VFolderStatusSet,
    vfolder_status_map,
    vfolders,
)
from ai.backend.manager.repositories.base.creator import BulkCreator, Creator
from ai.backend.manager.repositories.base.pagination import NoPagination
from ai.backend.manager.repositories.base.purger import BatchPurger, execute_batch_purger
from ai.backend.manager.repositories.base.querier import (
    BatchQuerier,
    Querier,
    execute_batch_querier,
)
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    RBACEntityCreator,
)
from ai.backend.manager.repositories.base.rbac.entity_purger import (
    RBACEntityPurger,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.group.creators import (
    GroupCreatorSpec,
)
from ai.backend.manager.repositories.group.purgers import (
    GroupEndpointBatchPurgerSpec,
    GroupKernelBatchPurgerSpec,
    GroupSessionBatchPurgerSpec,
    ProjectPurgerSpec,
    SessionByIdsBatchPurgerSpec,
)
from ai.backend.manager.repositories.group.scope_binders import UserProjectEntityUnbinder
from ai.backend.manager.repositories.group.types import (
    DomainProjectSearchScope,
    GroupSearchResult,
    UserProjectSearchScope,
)
from ai.backend.manager.repositories.ops.rbac.provider import (
    EntityMembersAddition,
    EntityMembersRemoval,
    RBACOpsProvider,
    RBACWriteOps,
    ScopeCreation,
    ScopeDeletion,
    ScopeMember,
)
from ai.backend.manager.repositories.permission_controller.creators import UserRoleCreatorSpec
from ai.backend.manager.repositories.permission_controller.role_manager import (
    ScopeSystemRoleData,
)
from ai.backend.manager.repositories.vfolder.deletion import initiate_vfolder_deletion

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _project_scope(project_id: ProjectID) -> ScopeRef:
    return ScopeRef(
        scope_type=ScopeType(RBACElementType.PROJECT.value),
        scope_id=project_id,
    )


@dataclass
class ProjectUserMember(ScopeMember):
    """A user joining or leaving a project scope; ``manage_roles`` controls whether the
    membership change also grants/revokes the user's roles at the project scope."""

    user_id: uuid.UUID
    manage_roles: bool = True

    @override
    def entity_ref(self) -> EntityRef:
        return EntityRef(
            entity_type=VirtualScopeEntityType(RBACElementType.USER.value),
            entity_id=self.user_id,
        )

    @override
    def assign_role_on(self) -> UserID | None:
        return UserID(self.user_id) if self.manage_roles else None


@dataclass
class ProjectScopeCreation(ScopeCreation[GroupRow]):
    """Creates a project row under its domain, and the scope the project becomes."""

    spec: GroupCreatorSpec

    @override
    def creator(self) -> RBACEntityCreator[GroupRow]:
        return RBACEntityCreator(
            spec=self.spec,
            element_type=RBACElementType.PROJECT,
            scope_ref=RBACElementRef(
                element_type=RBACElementType.DOMAIN, element_id=self.spec.domain_name
            ),
        )

    @override
    def scope_of(self, row: GroupRow) -> ScopeRef:
        return _project_scope(ProjectID(row.id))

    @override
    def system_roles_of(self, row: GroupRow) -> Collection[ScopeSystemRoleData]:
        """A project starts with an admin role (via GroupData) and a member role
        (read-only access for project members)."""
        data = row.to_data()
        return (data, ProjectMemberRoleSpec(project_id=data.id))


class GroupDBSource:
    _db: ExtendedAsyncSAEngine
    _rbac_ops_provider: RBACOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._rbac_ops_provider = RBACOpsProvider(db)

    async def create(self, creator: Creator[GroupRow]) -> GroupData:
        """Create a new group.

        Domain/resource-policy existence and name-uniqueness are enforced by the group
        row's DB constraints, mapped to domain errors via the spec's
        integrity_error_checks.
        """
        creation = ProjectScopeCreation(spec=cast(GroupCreatorSpec, creator.spec))
        async with self._rbac_ops_provider.write_ops() as w:
            return (await w.create_scope(creation)).row.to_data()

    async def modify_validated(
        self,
        updater: Updater[GroupRow],
        user_update_mode: str | None = None,
        user_uuids: list[uuid.UUID] | None = None,
    ) -> GroupData | None:
        """Modify a group with validation."""
        group_id = cast(UUID, updater.pk_value)
        project_id = ProjectID(group_id)

        async with self._rbac_ops_provider.write_ops() as w:
            existing_group = await w.query(Querier(row_class=GroupRow, pk_value=group_id))
            if existing_group is None:
                raise ProjectNotFound(f"Group not found: {group_id}")

            if user_uuids and user_update_mode:
                if user_update_mode == "add":
                    await self._add_users_to_project(w, project_id, user_uuids)
                elif user_update_mode == "remove":
                    await w.remove_entity_members(
                        EntityMembersRemoval(
                            scope=_project_scope(project_id),
                            members=[ProjectUserMember(user_id=uid) for uid in user_uuids],
                        )
                    )

            # Update group data (returns None if no values to update)
            result = await w.update(updater)
            if result is not None:
                return result.row.to_data()

            # No group updates or only user updates were performed
            return None

    async def _users_addable_to_project(
        self,
        w: RBACWriteOps,
        project_id: ProjectID,
        user_uuids: Sequence[uuid.UUID],
    ) -> list[UserRow]:
        """Users among ``user_uuids`` that belong to the project's domain and are not
        yet members of the project."""
        project_domain_subq = (
            sa.select(GroupRow.domain_name).where(GroupRow.id == project_id).scalar_subquery()
        )
        query = (
            sa.select(UserRow)
            .outerjoin(
                AssociationScopesEntitiesRow,
                sa.and_(
                    sa.cast(UserRow.uuid, sa.String) == AssociationScopesEntitiesRow.entity_id,
                    AssociationScopesEntitiesRow.scope_type == LegacyScopeType.PROJECT,
                    AssociationScopesEntitiesRow.scope_id == str(project_id),
                    AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                ),
            )
            .where(
                UserRow.uuid.in_(user_uuids)
                & (UserRow.domain_name == project_domain_subq)
                & AssociationScopesEntitiesRow.entity_id.is_(None)
            )
        )
        result = await w.batch_query_in_global(query, BatchQuerier(pagination=NoPagination()))
        return [row.UserRow for row in result.rows]

    async def _add_users_to_project(
        self,
        w: RBACWriteOps,
        project_id: ProjectID,
        user_uuids: list[uuid.UUID],
    ) -> None:
        """Add users in the project's domain to the project, granting each new member
        the project's ``auto_assign`` roles."""
        new_user_rows = await self._users_addable_to_project(w, project_id, user_uuids)
        if not new_user_rows:
            return
        await w.add_entity_members(
            EntityMembersAddition(
                scope=_project_scope(project_id),
                members=[ProjectUserMember(user_id=row.uuid) for row in new_user_rows],
            )
        )

    async def mark_inactive(self, group_id: uuid.UUID) -> None:
        """Mark a group as inactive (soft delete)."""
        async with self._db.begin_session() as session:
            result = await session.execute(
                sa.update(groups)
                .values(
                    is_active=False,
                    integration_id=None,
                )
                .where(groups.c.id == group_id)
            )
            if cast(CursorResult[Any], result).rowcount > 0:
                return
            raise ProjectNotFound(f"Group not found: {group_id}")

    async def get_container_stats_for_period(
        self,
        start_date: datetime,
        end_date: datetime,
        valkey_stat_client: ValkeyStatClient,
        config_provider: ManagerConfigProvider,
        group_ids: Sequence[UUID] | None = None,
    ) -> list[dict[str, Any]]:
        """Get container statistics for groups within a time period."""
        async with self._db.begin_readonly() as conn:
            j = kernels.join(groups, groups.c.id == kernels.c.group_id).join(
                users, users.c.uuid == kernels.c.user_uuid
            )
            query = (
                sa.select(
                    kernels.c.id,
                    kernels.c.container_id,
                    kernels.c.session_id,
                    kernels.c.session_name,
                    kernels.c.access_key,
                    kernels.c.agent,
                    kernels.c.domain_name,
                    kernels.c.group_id,
                    kernels.c.attached_devices,
                    kernels.c.occupied_slots,
                    kernels.c.resource_opts,
                    kernels.c.vfolder_mounts,
                    kernels.c.mounts,
                    kernels.c.image,
                    kernels.c.status,
                    kernels.c.status_info,
                    kernels.c.status_changed,
                    kernels.c.last_stat,
                    kernels.c.status_history,
                    kernels.c.created_at,
                    kernels.c.terminated_at,
                    kernels.c.cluster_mode,
                    groups.c.name,
                    users.c.email,
                    users.c.full_name,
                )
                .select_from(j)
                .where(
                    # Filter sessions which existence period overlaps with requested period
                    (
                        (kernels.c.terminated_at >= start_date)
                        & (kernels.c.created_at < end_date)
                        & (kernels.c.status.in_(RESOURCE_USAGE_KERNEL_STATUSES))
                    )
                    |
                    # Or, filter running sessions which created before requested end_date
                    ((kernels.c.created_at < end_date) & (kernels.c.status.in_(LIVE_STATUS))),
                )
                .order_by(sa.asc(kernels.c.terminated_at))
            )
            if group_ids:
                query = query.where(kernels.c.group_id.in_(group_ids))
            result = await conn.execute(query)
            rows = result.fetchall()

        kernel_ids = [str(row.id) for row in rows]
        raw_stats = await valkey_stat_client.get_user_kernel_statistics_batch(kernel_ids)

        objs_per_group = {}
        local_tz = config_provider.config.system.timezone

        for row, raw_stat in zip(rows, raw_stats, strict=True):
            group_id = str(row.group_id)
            last_stat = row.last_stat
            if not last_stat:
                if raw_stat is None:
                    log.warning("stat object for {} not found on redis, skipping", str(row.id))
                    continue
                last_stat = msgpack.unpackb(raw_stat)
            nfs = None
            if row.vfolder_mounts:
                # For >=22.03, return used host directories instead of volume host, which is not so useful.
                nfs = list({str(mount.host_path) for mount in row.vfolder_mounts})
            elif row.mounts and isinstance(row.mounts[0], list):
                # For the kernel records that have legacy contents of `mounts`.
                nfs = list({mount[2] for mount in row.mounts})
            if row.terminated_at is None:
                used_time = used_days = None
            else:
                used_time = str(row.terminated_at - row.created_at)
                used_days = (
                    row.terminated_at.astimezone(local_tz).toordinal()
                    - row.created_at.astimezone(local_tz).toordinal()
                    + 1
                )
            device_type = set()
            gpu_smp_allocated = 0
            gpu_mem_allocated = 0
            if row.attached_devices and row.attached_devices.get("cuda"):
                for dev_info in row.attached_devices["cuda"]:
                    if dev_info.get("model_name"):
                        device_type.add(dev_info["model_name"])
                    gpu_smp_allocated += int(nmget(dev_info, "data.smp", 0))
                    gpu_mem_allocated += int(nmget(dev_info, "data.mem", 0))
            gpu_allocated = Decimal(0)
            for key, value in row.occupied_slots.items():
                if SlotName(key).is_accelerator():
                    gpu_allocated += value
            c_info = {
                "id": str(row.id),
                "session_id": str(row.session_id),
                "container_id": row.container_id,
                "domain_name": row.domain_name,
                "group_id": str(row.group_id),
                "group_name": row.name,
                "name": row.session_name,
                "access_key": row.access_key,
                "email": row.email,
                "full_name": row.full_name,
                "agent": row.agent,
                "cpu_allocated": float(row.occupied_slots.get("cpu", 0)),
                "cpu_used": float(nmget(last_stat, "cpu_used.current", 0)),
                "mem_allocated": int(row.occupied_slots.get("mem", 0)),
                "mem_used": int(nmget(last_stat, "mem.capacity", 0)),
                "shared_memory": int(nmget(row.resource_opts, "shmem", 0)),
                "disk_allocated": 0,  # TODO: disk quota limit
                "disk_used": int(nmget(last_stat, "io_scratch_size/stats.max", 0, "/")),
                "io_read": int(nmget(last_stat, "io_read.current", 0)),
                "io_write": int(nmget(last_stat, "io_write.current", 0)),
                "used_time": used_time,
                "used_days": used_days,
                "device_type": list(device_type),
                "smp": float(gpu_smp_allocated),
                "gpu_mem_allocated": float(gpu_mem_allocated),
                "gpu_allocated": float(gpu_allocated),
                "nfs": nfs,
                "image_id": row.image,  # TODO: image id
                "image_name": row.image,
                "created_at": str(row.created_at),
                "terminated_at": str(row.terminated_at),
                "status": row.status.name,
                "status_info": row.status_info,
                "status_changed": str(row.status_changed),
                "status_history": row.status_history or {},
                "cluster_mode": row.cluster_mode,
            }
            if group_id not in objs_per_group:
                objs_per_group[group_id] = {
                    "domain_name": row.domain_name,
                    "g_id": group_id,
                    "g_name": row.name,  # this is group's name
                    "g_cpu_allocated": c_info["cpu_allocated"],
                    "g_cpu_used": c_info["cpu_used"],
                    "g_mem_allocated": c_info["mem_allocated"],
                    "g_mem_used": c_info["mem_used"],
                    "g_shared_memory": c_info["shared_memory"],
                    "g_disk_allocated": c_info["disk_allocated"],
                    "g_disk_used": c_info["disk_used"],
                    "g_io_read": c_info["io_read"],
                    "g_io_write": c_info["io_write"],
                    "g_device_type": copy.deepcopy(c_info["device_type"]),
                    "g_smp": c_info["smp"],
                    "g_gpu_mem_allocated": c_info["gpu_mem_allocated"],
                    "g_gpu_allocated": c_info["gpu_allocated"],
                    "c_infos": [c_info],
                }
            else:
                objs_per_group[group_id]["g_cpu_allocated"] += c_info["cpu_allocated"]
                objs_per_group[group_id]["g_cpu_used"] += c_info["cpu_used"]
                objs_per_group[group_id]["g_mem_allocated"] += c_info["mem_allocated"]
                objs_per_group[group_id]["g_mem_used"] += c_info["mem_used"]
                objs_per_group[group_id]["g_shared_memory"] += c_info["shared_memory"]
                objs_per_group[group_id]["g_disk_allocated"] += c_info["disk_allocated"]
                objs_per_group[group_id]["g_disk_used"] += c_info["disk_used"]
                objs_per_group[group_id]["g_io_read"] += c_info["io_read"]
                objs_per_group[group_id]["g_io_write"] += c_info["io_write"]
                for device in c_info["device_type"]:
                    if device not in objs_per_group[group_id]["g_device_type"]:
                        g_dev_type = objs_per_group[group_id]["g_device_type"]
                        g_dev_type.append(device)
                        objs_per_group[group_id]["g_device_type"] = list(set(g_dev_type))
                objs_per_group[group_id]["g_smp"] += c_info["smp"]
                objs_per_group[group_id]["g_gpu_mem_allocated"] += c_info["gpu_mem_allocated"]
                objs_per_group[group_id]["g_gpu_allocated"] += c_info["gpu_allocated"]
                objs_per_group[group_id]["c_infos"].append(c_info)
        return list(objs_per_group.values())

    async def fetch_project_resource_usage(
        self,
        start_date: datetime,
        end_date: datetime,
        project_ids: Sequence[UUID] | None = None,
    ) -> list[KernelRow]:
        """Fetch resource usage data for projects."""
        return await fetch_resource_usage(self._db, start_date, end_date, project_ids=project_ids)

    async def purge_group(
        self,
        group_id: uuid.UUID,
        storage_manager: StorageSessionManager,
    ) -> bool:
        """Completely remove a group and all its associated data."""
        async with self._db.begin_session() as session:
            # Pre-flight checks
            if await self._check_group_vfolders_mounted_to_active_kernels(session, group_id):
                raise ProjectHasVFoldersMountedError(
                    f"error on deleting project {group_id} with vfolders mounted to active kernels"
                )

            if await self._check_group_has_active_kernels(session, group_id):
                raise ProjectHasActiveKernelsError(
                    f"error on deleting project {group_id} with active kernels"
                )

            # Delete associated resources
            await self._delete_group_endpoints(session, group_id)

            # Commit session before vfolder deletion (which uses separate transactions)
            await session.commit()

        # Delete vfolders (uses separate transaction)
        await self._delete_group_vfolders(group_id, storage_manager)

        project_id = ProjectID(group_id)
        async with self._rbac_ops_provider.write_ops() as w:
            # Delete remaining data
            await w.batch_purge(BatchPurger(spec=GroupKernelBatchPurgerSpec(group_id=group_id)))
            await w.batch_purge(BatchPurger(spec=GroupSessionBatchPurgerSpec(group_id=group_id)))

            # Finally delete the group itself as a scope: the row, its RBAC
            # entries, and its virtual scope node.
            result = await w.delete_scope(
                ScopeDeletion(
                    purger=RBACEntityPurger(
                        spec=ProjectPurgerSpec(project_id=project_id),
                    ),
                    scope=_project_scope(project_id),
                )
            )
            if result is None:
                raise ProjectNotFound("project not found")
            return True

    async def _check_group_vfolders_mounted_to_active_kernels(
        self, session: SASession, group_id: uuid.UUID
    ) -> bool:
        """Check if group has vfolders mounted to active kernels."""
        # Get group vfolder IDs
        query = sa.select(vfolders.c.id).select_from(vfolders).where(vfolders.c.group == group_id)
        result = await session.execute(query)
        rows = result.fetchall()
        group_vfolder_ids = [row.id for row in rows]

        # Check if any active kernels have these vfolders mounted
        query = (
            sa.select(kernels.c.mounts)
            .select_from(kernels)
            .where(
                (kernels.c.group_id == group_id)
                & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
            )
        )
        async for row in await session.stream(query):
            for _mount in row.mounts:
                try:
                    vfolder_id = uuid.UUID(_mount[2])
                    if vfolder_id in group_vfolder_ids:
                        return True
                except Exception:
                    log.warning("Malformed mount entry in group {}, skipping: {}", group_id, _mount)
        return False

    async def _check_group_has_active_kernels(
        self, session: SASession, group_id: uuid.UUID
    ) -> bool:
        """Check if group has active kernels."""
        query = (
            sa.select(sa.func.count())
            .select_from(kernels)
            .where(
                (kernels.c.group_id == group_id)
                & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
            )
        )
        active_kernel_count = await session.scalar(query)
        return (active_kernel_count or 0) > 0

    async def _delete_group_vfolders(
        self,
        group_id: uuid.UUID,
        storage_manager: StorageSessionManager,
    ) -> int:
        """Delete all vfolders belonging to the group."""
        target_vfs: list[VFolderDeletionInfo] = []
        async with self._db.begin_session() as session:
            query = sa.select(VFolderRow).where(
                sa.and_(
                    VFolderRow.group == group_id,
                    VFolderRow.status.in_(vfolder_status_map[VFolderStatusSet.DELETABLE]),
                )
            )
            result = await session.scalars(query)
            rows = cast(list[VFolderRow], result.fetchall())
            for vf in rows:
                target_vfs.append(
                    VFolderDeletionInfo(VFolderID.from_row(vf), vf.host, vf.unmanaged_path)
                )

        storage_ptask_group = aiotools.PersistentTaskGroup()
        await initiate_vfolder_deletion(
            self._db,
            target_vfs,
            storage_manager,
            storage_ptask_group,
        )

        return len(target_vfs)

    async def _delete_group_endpoints(self, session: SASession, group_id: uuid.UUID) -> None:
        """Delete all endpoints belonging to the group."""
        # Get all endpoints for the group to check for active ones
        endpoints = (
            await session.execute(
                sa.select(
                    EndpointRow.id,
                    sa.case(
                        (
                            EndpointRow.lifecycle_stage.in_([
                                EndpointLifecycle.CREATED,
                                EndpointLifecycle.DESTROYING,
                            ]),
                            True,
                        ),
                        else_=False,
                    ).label("is_active"),
                ).where(EndpointRow.project == group_id)
            )
        ).all()

        if len(endpoints) == 0:
            return

        # Check for active endpoints
        active_endpoints = [ep.id for ep in endpoints if ep.is_active]
        if len(active_endpoints) > 0:
            raise ProjectHasActiveEndpointsError(f"project {group_id} has active endpoints")

        # Collect session IDs first (must be done before endpoint/routing deletion
        # as the query depends on RoutingRow)
        endpoint_ids = [ep.id for ep in endpoints]
        session_id_query = sa.select(RoutingRow.session).where(
            sa.and_(
                RoutingRow.endpoint.in_(endpoint_ids),
                RoutingRow.session.is_not(None),
            )
        )
        session_ids_result = await session.scalars(session_id_query)
        session_ids = [sid for sid in session_ids_result.all() if sid is not None]

        # Delete endpoints first (routings are CASCADE deleted automatically)
        await execute_batch_purger(
            session, BatchPurger(spec=GroupEndpointBatchPurgerSpec(project_id=group_id))
        )

        # Delete sessions using the collected IDs
        if session_ids:
            await execute_batch_purger(
                session, BatchPurger(spec=SessionByIdsBatchPurgerSpec(session_ids=session_ids))
            )

    async def assign_users_to_project(
        self, project_id: UUID, user_ids: list[UUID], role_id: UUID
    ) -> list[UserData]:
        """Assign users to a project with domain validation via the RBAC member ops.

        Validates that the role exists, filters to users in the project's domain
        that are not already assigned, writes each new member's virtual-scope
        membership and scope association, and creates user-role mappings for the
        specified role.

        Returns the list of newly assigned users.
        """
        if not user_ids:
            return []

        target_project_id = ProjectID(project_id)
        async with self._rbac_ops_provider.write_ops() as w:
            # TODO: https://github.com/lablup/backend.ai/issues/10687
            role = await w.query(Querier(row_class=RoleRow, pk_value=role_id))
            if role is None:
                raise InvalidAPIParameters(f"Role not found: {role_id}")

            new_user_rows = await self._users_addable_to_project(w, target_project_id, user_ids)
            if not new_user_rows:
                return []

            await w.add_entity_members(
                EntityMembersAddition(
                    scope=_project_scope(target_project_id),
                    members=[
                        ProjectUserMember(user_id=row.uuid, manage_roles=False)
                        for row in new_user_rows
                    ],
                )
            )
            user_role_specs = [
                UserRoleCreatorSpec(user_id=row.uuid, role_id=role_id) for row in new_user_rows
            ]
            await w.bulk_create(BulkCreator(specs=user_role_specs))

            return [row.to_data() for row in new_user_rows]

    async def unassign_users_from_project(
        self, unbinder: UserProjectEntityUnbinder
    ) -> UnassignUsersResult:
        """Remove users from a project and return unassigned users and failures.

        Deletes each member's virtual-scope membership and scope association via
        the RBAC member ops. Reports which requested user IDs could not be
        unassigned and why.
        """
        async with self._rbac_ops_provider.write_ops() as w:
            requested_ids = set(unbinder.user_uuids)
            target_entity_ids = [str(uid) for uid in unbinder.user_uuids]

            # Find which requested UUIDs actually exist in the system
            existing_query = sa.select(UserRow).where(UserRow.uuid.in_(unbinder.user_uuids))
            existing_result = await w.batch_query_in_global(
                existing_query, BatchQuerier(pagination=NoPagination())
            )
            existing_ids = {row.UserRow.uuid for row in existing_result.rows}

            # Fetch users that are actually associated before removing
            actual_assoc_query = sa.select(UserRow).where(
                sa.cast(UserRow.uuid, sa.String).in_(
                    sa.select(AssociationScopesEntitiesRow.entity_id).where(
                        AssociationScopesEntitiesRow.scope_type == LegacyScopeType.PROJECT,
                        AssociationScopesEntitiesRow.scope_id == str(unbinder.project_id),
                        AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                        AssociationScopesEntitiesRow.entity_id.in_(target_entity_ids),
                    )
                )
            )
            assoc_result = await w.batch_query_in_global(
                actual_assoc_query, BatchQuerier(pagination=NoPagination())
            )
            assigned_rows = [row.UserRow for row in assoc_result.rows]
            assigned_ids = {row.uuid for row in assigned_rows}
            unassigned_users = [row.to_data() for row in assigned_rows]

            await w.remove_entity_members(
                EntityMembersRemoval(
                    scope=_project_scope(ProjectID(unbinder.project_id)),
                    members=[
                        ProjectUserMember(user_id=uid, manage_roles=False)
                        for uid in unbinder.user_uuids
                    ],
                )
            )

            # Compute failures
            failures: list[UnassignUserFailure] = []
            for uid in requested_ids - existing_ids:
                failures.append(UnassignUserFailure(user_id=uid, reason="User does not exist."))
            for uid in existing_ids - assigned_ids:
                failures.append(
                    UnassignUserFailure(user_id=uid, reason="User is not assigned to this project.")
                )

            return UnassignUsersResult(
                unassigned_users=unassigned_users,
                failures=failures,
            )

    async def bind_user_to_project(self, user_id: UserID, project_id: ProjectID) -> None:
        """Add a user to a project as a scope member (membership writes only).

        Idempotent: adding an existing member is a no-op.
        """
        async with self._rbac_ops_provider.write_ops() as w:
            await w.add_entity_members(
                EntityMembersAddition(
                    scope=_project_scope(project_id),
                    members=[ProjectUserMember(user_id=user_id, manage_roles=False)],
                )
            )

    async def unbind_user_from_project(self, user_id: UserID, project_id: ProjectID) -> None:
        """Remove a user from a project (membership writes only)."""
        async with self._rbac_ops_provider.write_ops() as w:
            await w.remove_entity_members(
                EntityMembersRemoval(
                    scope=_project_scope(project_id),
                    members=[ProjectUserMember(user_id=user_id, manage_roles=False)],
                )
            )

    async def get_project(self, project_id: UUID) -> GroupData:
        """Get a single project by UUID.

        Args:
            project_id: UUID of the project.

        Returns:
            GroupData for the project.

        Raises:
            ProjectNotFound: If project does not exist.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.execute(sa.select(GroupRow).where(GroupRow.id == project_id))
            row = result.scalar_one_or_none()
            if row is None:
                raise ProjectNotFound(f"Project {project_id} not found")
            return row.to_data()

    async def project_id_by_name_in_domain(
        self, domain_name: str, project_name: str
    ) -> ProjectID | None:
        """Resolve an active project's UUID by its domain-scoped name.

        LEGACY: Exists solely to support existing API handlers that only accept a
        group name as input (e.g. the REST v1 session/cluster template endpoints).
        New API handlers and any other new code MUST NOT use this — they should
        accept a project UUID directly.

        Returns:
            The project UUID if found, or ``None`` if no matching active project exists.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.execute(
                sa.select(GroupRow.id).where(
                    GroupRow.domain_name == domain_name,
                    GroupRow.name == project_name,
                    GroupRow.is_active.is_(True),
                )
            )
            project_id = result.scalar_one_or_none()
            if project_id is None:
                return None
            return ProjectID(project_id)

    async def search_projects(
        self,
        querier: BatchQuerier,
    ) -> GroupSearchResult:
        """Search all projects (admin only).

        Args:
            querier: Contains conditions, orders, and pagination.

        Returns:
            GroupSearchResult with items, total_count, and pagination flags.
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(GroupRow)
            result = await execute_batch_querier(db_sess, query, querier)

            items = [row.GroupRow.to_data() for row in result.rows]

            return GroupSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_projects_by_domain(
        self,
        scope: DomainProjectSearchScope,
        querier: BatchQuerier,
    ) -> GroupSearchResult:
        """Search projects within a domain.

        Args:
            scope: DomainProjectSearchScope defining the domain to search within.
            querier: Contains conditions, orders, and pagination.

        Returns:
            GroupSearchResult with items, total_count, and pagination flags.
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(GroupRow)
            result = await execute_batch_querier(db_sess, query, querier, scopes=[scope])

            items = [row.GroupRow.to_data() for row in result.rows]

            return GroupSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_projects_by_user(
        self,
        scope: UserProjectSearchScope,
        querier: BatchQuerier,
    ) -> GroupSearchResult:
        """Search projects a user is member of.

        Joins with association_scopes_entities (PROJECT/USER) to find user's
        projects. Casts GroupRow.id to String for the JOIN since ASE.scope_id
        is a non-UUID String column.

        Args:
            scope: UserProjectSearchScope defining the user to search for.
            querier: Contains conditions, orders, and pagination.

        Returns:
            GroupSearchResult with items, total_count, and pagination flags.
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = (
                sa.select(GroupRow)
                .select_from(GroupRow)
                .join(
                    AssociationScopesEntitiesRow,
                    sa.and_(
                        sa.cast(GroupRow.id, sa.String) == AssociationScopesEntitiesRow.scope_id,
                        AssociationScopesEntitiesRow.scope_type == LegacyScopeType.PROJECT,
                        AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                    ),
                )
            )
            result = await execute_batch_querier(db_sess, query, querier, scopes=[scope])

            items = [row.GroupRow.to_data() for row in result.rows]

            return GroupSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

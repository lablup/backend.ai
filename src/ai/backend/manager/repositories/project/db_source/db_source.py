from __future__ import annotations

import copy
import logging
import uuid
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any, cast
from uuid import UUID

import aiotools
import msgpack
import sqlalchemy as sa
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.types import EntityRef, ScopeRef
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.common.exception import DomainNotFound, InvalidAPIParameters
from ai.backend.common.types import ResourceSlot, SessionId, SlotName, VFolderID
from ai.backend.common.utils import nmget
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.project.types import (
    ProjectData,
    ProjectType,
    UnassignUserFailure,
    UnassignUsersResult,
)
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.resource import (
    PersonalProjectDeletionError,
    PersonalProjectMemberAdditionError,
    ProjectHasActiveEndpointsError,
    ProjectHasVFoldersMountedError,
    ProjectNotFound,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow
from ai.backend.manager.models.kernel import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    LIVE_STATUS,
    RESOURCE_USAGE_KERNEL_STATUSES,
    KernelRow,
    kernels,
)
from ai.backend.manager.models.project import groups
from ai.backend.manager.models.project.purgers import (
    ProjectEndpointPurger,
    ProjectKernelPurger,
    ProjectPurger,
    ProjectScopeAssociationPurger,
    ProjectSessionPurger,
    SessionsByIdsPurger,
)
from ai.backend.manager.models.project.row import (
    ProjectRow,
)
from ai.backend.manager.models.project.scopes import (
    DomainProjectOperationScope,
    UserProjectOperationScope,
)
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_slot.aggregates import kernel_allocated_slots_expr
from ai.backend.manager.models.resource_usage import fetch_resource_usage
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.user import UserRow, users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderDeletionInfo,
    VFolderRow,
    VFolderStatusSet,
    vfolder_status_map,
)
from ai.backend.manager.models.virtual_entity.queries import user_scope_membership_exists
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.querier import (
    BatchQuerier,
    Querier,
    execute_batch_querier,
)
from ai.backend.manager.repositories.ops.rbac.provider import (
    EntityMembersAddition,
    RBACOpsProvider,
    RBACWriteOps,
    ScopeUserMember,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.permission_controller.creators import UserRoleCreatorSpec
from ai.backend.manager.repositories.project.scope_binders import UserProjectEntityUnbinder
from ai.backend.manager.repositories.project.types import ProjectSearchResult
from ai.backend.manager.repositories.vfolder.deletion import initiate_vfolder_deletion

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ProjectDBSource:
    _db: ExtendedAsyncSAEngine
    _v2_ops: V2DBOpsProvider
    _rbac_ops_provider: RBACOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine, v2_ops_provider: V2DBOpsProvider) -> None:
        self._db = db
        self._v2_ops = v2_ops_provider
        self._rbac_ops_provider = RBACOpsProvider(db)

    async def _get_domain_id(self, w: RBACWriteOps, domain_name: str) -> DomainID:
        result = await w.batch_query_in_global(
            sa.select(DomainRow.id).where(DomainRow.name == domain_name),
            BatchQuerier(pagination=NoPagination()),
        )
        if not result.rows:
            raise DomainNotFound(f"Domain '{domain_name}' not found")
        return DomainID(result.rows[0].id)

    async def update_members(
        self,
        project_id: ProjectID,
        user_update_mode: str,
        user_ids: list[UserID],
    ) -> None:
        """Add or remove project members.

        Membership is an association row, which the v2 ops layer has no primitive for,
        so this stays on the legacy write ops.
        """
        async with self._rbac_ops_provider.write_ops() as w:
            existing_group = await w.query(Querier(row_class=ProjectRow, pk_value=project_id))
            if existing_group is None:
                raise ProjectNotFound(f"Group not found: {project_id}")
            if user_update_mode == "add":
                await self._refuse_personal_project(w, project_id)
                await self._add_users_to_project(w, project_id, user_ids)
            elif user_update_mode == "remove":
                await w.remove_bulk_members(
                    ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=project_id),
                    [EntityRef(entity_type=USER_ENTITY_TYPE, entity_id=uid) for uid in user_ids],
                )

    async def _refuse_personal_project(self, w: RBACWriteOps, project_id: ProjectID) -> None:
        """Refuse the write when the project is a personal one, which keeps its owner
        as its only member."""
        result = await w.batch_query_in_global(
            sa.select(ProjectRow.id).where(
                ProjectRow.id == project_id, ProjectRow.type == ProjectType.PERSONAL
            ),
            BatchQuerier(pagination=NoPagination()),
        )
        if result.rows:
            raise PersonalProjectMemberAdditionError(
                f"Personal project takes no members: {project_id}"
            )

    async def _users_addable_to_project(
        self,
        w: RBACWriteOps,
        project_id: ProjectID,
        user_ids: Sequence[UserID],
    ) -> list[UserRow]:
        """Users among ``user_ids`` that belong to the project's domain and are not
        yet members of the project."""
        project_domain_subq = (
            sa.select(ProjectRow.domain_name).where(ProjectRow.id == project_id).scalar_subquery()
        )
        query = sa.select(UserRow).where(
            UserRow.uuid.in_(user_ids)
            & (UserRow.domain_name == project_domain_subq)
            & ~user_scope_membership_exists(PROJECT_SCOPE_TYPE, project_id, UserRow.uuid)
        )
        result = await w.batch_query_in_global(query, BatchQuerier(pagination=NoPagination()))
        return [row.UserRow for row in result.rows]

    async def _add_users_to_project(
        self,
        w: RBACWriteOps,
        project_id: ProjectID,
        user_ids: list[UserID],
    ) -> None:
        """Add users in the project's domain to the project, granting each new member
        the project's ``auto_assign`` roles."""
        new_user_rows = await self._users_addable_to_project(w, project_id, user_ids)
        if not new_user_rows:
            return
        await w.add_bulk_members(
            EntityMembersAddition(
                scope=ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=project_id),
                members=[ScopeUserMember(user_id=UserID(row.uuid)) for row in new_user_rows],
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
                    kernel_allocated_slots_expr(kernels.c.id).label("occupied_slots"),
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
    ) -> tuple[list[KernelRow], dict[UUID, ResourceSlot]]:
        """Fetch the project's kernels with the slots they were allocated."""
        return await fetch_resource_usage(self._db, start_date, end_date, project_ids=project_ids)

    async def purge_group(
        self,
        group_id: uuid.UUID,
        storage_manager: StorageSessionManager,
    ) -> bool:
        """Completely remove a group and all its associated data."""
        project_id = ProjectID(group_id)
        async with self._db.begin_readonly_session_read_committed() as sess:
            project_type = await sess.scalar(
                sa.select(ProjectRow.type).where(ProjectRow.id == project_id)
            )
            if project_type is ProjectType.PERSONAL:
                raise PersonalProjectDeletionError(
                    f"Personal project is purged with its user: {project_id}"
                )
            if await self._project_vfolders_mounted_to_active_kernels(sess, group_id):
                raise ProjectHasVFoldersMountedError(
                    f"error on deleting project {group_id} with vfolders mounted to active kernels"
                )
            routed_session_ids = await self._routed_session_ids(sess, group_id)
            target_vfs = await self._purgable_project_vfolders(sess, group_id)

        async with self._v2_ops.write_ops() as w:
            # Deployments go first (their routings cascade), then the sessions they routed.
            await w.batch_purge_entities_in_global(ProjectEndpointPurger(project_id=project_id))
            if routed_session_ids:
                await w.batch_purge_entities_in_global(
                    SessionsByIdsPurger(session_ids=routed_session_ids)
                )
            await w.batch_purge_field_entities(
                project_id, ProjectKernelPurger(project_id=project_id)
            )
            await w.batch_purge_entities_in_global(ProjectSessionPurger(project_id=project_id))
            await w.batch_purge_field_entities(project_id, ProjectScopeAssociationPurger())
            if await w.purge_entity(ProjectPurger(project_id=project_id)) is None:
                raise ProjectNotFound("project not found")

        await self._delete_project_vfolders(target_vfs, storage_manager)
        return True

    async def _project_vfolders_mounted_to_active_kernels(
        self, sess: SASession, group_id: uuid.UUID
    ) -> bool:
        """Whether any of the project's vfolders is mounted to a kernel still running."""
        group_vfolder_ids = set(
            (await sess.scalars(sa.select(VFolderRow.id).where(VFolderRow.group == group_id))).all()
        )
        mount_lists = (
            await sess.scalars(
                sa.select(KernelRow.mounts).where(
                    KernelRow.group_id == group_id,
                    KernelRow.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES),
                )
            )
        ).all()
        for mounts in mount_lists:
            for _mount in mounts or []:
                try:
                    if uuid.UUID(_mount[2]) in group_vfolder_ids:
                        return True
                except Exception:
                    log.warning("Malformed mount entry in group {}, skipping: {}", group_id, _mount)
        return False

    async def _routed_session_ids(self, sess: SASession, group_id: uuid.UUID) -> list[SessionId]:
        """The sessions the project's deployments route to, read before the deployments go.

        Refuses while a deployment is still live.
        """
        endpoints = (
            await sess.execute(
                sa.select(EndpointRow.id, EndpointRow.lifecycle_stage).where(
                    EndpointRow.project == group_id
                )
            )
        ).all()
        if not endpoints:
            return []
        if any(
            ep.lifecycle_stage in (EndpointLifecycle.CREATED, EndpointLifecycle.DESTROYING)
            for ep in endpoints
        ):
            raise ProjectHasActiveEndpointsError(f"project {group_id} has active endpoints")
        routed = (
            await sess.scalars(
                sa.select(RoutingRow.session).where(
                    RoutingRow.endpoint.in_([ep.id for ep in endpoints]),
                    RoutingRow.session.is_not(None),
                )
            )
        ).all()
        return [SessionId(session_id) for session_id in routed if session_id is not None]

    async def _purgable_project_vfolders(
        self, sess: SASession, group_id: uuid.UUID
    ) -> list[VFolderDeletionInfo]:
        """The project's vfolders whose status allows the owner to purge them."""
        rows = (
            await sess.scalars(
                sa.select(VFolderRow).where(
                    VFolderRow.group == group_id,
                    VFolderRow.status.in_(vfolder_status_map[VFolderStatusSet.OWNER_PURGABLE]),
                )
            )
        ).all()
        return [
            VFolderDeletionInfo(VFolderID.from_row(row), row.host, row.unmanaged_path)
            for row in rows
        ]

    async def _delete_project_vfolders(
        self,
        target_vfs: list[VFolderDeletionInfo],
        storage_manager: StorageSessionManager,
    ) -> None:
        """Hand the project's purgable vfolders to the storage-side deletion."""
        if not target_vfs:
            return
        storage_ptask_group = aiotools.PersistentTaskGroup()
        await initiate_vfolder_deletion(
            self._db,
            self._v2_ops,
            target_vfs,
            storage_manager,
            storage_ptask_group,
        )

    async def assign_users_to_project(
        self, project_id: ProjectID, user_ids: list[UserID], role_id: UUID
    ) -> list[UserData]:
        """Assign users to a project with domain validation via the RBAC member ops.

        Validates that the role exists, filters to users in the project's domain
        that are not already assigned, writes each new member's virtual-entity
        membership and scope association, and creates user-role mappings for the
        specified role. Membership grants the project's ``auto_assign`` roles on
        top of that role.

        Returns the list of newly assigned users.
        """
        if not user_ids:
            return []

        async with self._rbac_ops_provider.write_ops() as w:
            await self._refuse_personal_project(w, project_id)
            # TODO: https://github.com/lablup/backend.ai/issues/10687
            role = await w.query(Querier(row_class=RoleRow, pk_value=role_id))
            if role is None:
                raise InvalidAPIParameters(f"Role not found: {role_id}")

            new_user_rows = await self._users_addable_to_project(w, project_id, user_ids)
            if not new_user_rows:
                return []

            await w.add_bulk_members(
                EntityMembersAddition(
                    scope=ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=project_id),
                    members=[ScopeUserMember(user_id=UserID(row.uuid)) for row in new_user_rows],
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

        Deletes each member's virtual-entity membership and scope association via
        the RBAC member ops. Reports which requested user IDs could not be
        unassigned and why.
        """
        async with self._rbac_ops_provider.write_ops() as w:
            requested_ids = set(unbinder.user_uuids)

            # Find which requested UUIDs actually exist in the system
            existing_query = sa.select(UserRow).where(UserRow.uuid.in_(unbinder.user_uuids))
            existing_result = await w.batch_query_in_global(
                existing_query, BatchQuerier(pagination=NoPagination())
            )
            existing_ids = {row.UserRow.uuid for row in existing_result.rows}

            # Fetch users that are actually members before removing
            actual_assoc_query = sa.select(UserRow).where(
                UserRow.uuid.in_(unbinder.user_uuids)
                & user_scope_membership_exists(
                    PROJECT_SCOPE_TYPE, ProjectID(unbinder.project_id), UserRow.uuid
                )
            )
            assoc_result = await w.batch_query_in_global(
                actual_assoc_query, BatchQuerier(pagination=NoPagination())
            )
            assigned_rows = [row.UserRow for row in assoc_result.rows]
            assigned_ids = {row.uuid for row in assigned_rows}
            unassigned_users = [row.to_data() for row in assigned_rows]

            await w.remove_bulk_members(
                ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=ProjectID(unbinder.project_id)),
                [
                    EntityRef(entity_type=USER_ENTITY_TYPE, entity_id=UserID(uid))
                    for uid in unbinder.user_uuids
                ],
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
        """Add a user to a project as a scope member, granting the project's
        ``auto_assign`` roles.

        Idempotent: adding an existing member is a no-op.
        """
        async with self._rbac_ops_provider.write_ops() as w:
            await self._refuse_personal_project(w, project_id)
            await w.add_bulk_members(
                EntityMembersAddition(
                    scope=ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=project_id),
                    members=[ScopeUserMember(user_id=user_id)],
                )
            )

    async def unbind_user_from_project(self, user_id: UserID, project_id: ProjectID) -> None:
        """Remove a user from a project (membership writes only)."""
        async with self._rbac_ops_provider.write_ops() as w:
            await w.remove_bulk_members(
                ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=project_id),
                [EntityRef(entity_type=USER_ENTITY_TYPE, entity_id=user_id)],
            )

    async def get_project(self, project_id: UUID) -> ProjectData:
        """Get a single project by UUID.

        Args:
            project_id: UUID of the project.

        Returns:
            ProjectData for the project.

        Raises:
            ProjectNotFound: If project does not exist.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.execute(sa.select(ProjectRow).where(ProjectRow.id == project_id))
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
                sa.select(ProjectRow.id).where(
                    ProjectRow.domain_name == domain_name,
                    ProjectRow.name == project_name,
                    ProjectRow.is_active.is_(True),
                )
            )
            project_id = result.scalar_one_or_none()
            if project_id is None:
                return None
            return ProjectID(project_id)

    async def search_projects(
        self,
        querier: BatchQuerier,
    ) -> ProjectSearchResult:
        """Search all projects (admin only).

        Args:
            querier: Contains conditions, orders, and pagination.

        Returns:
            ProjectSearchResult with items, total_count, and pagination flags.
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ProjectRow)
            result = await execute_batch_querier(db_sess, query, querier)

            items = [row.ProjectRow.to_data() for row in result.rows]

            return ProjectSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_projects_by_domain(
        self,
        scope: DomainProjectOperationScope,
        querier: BatchQuerier,
    ) -> ProjectSearchResult:
        """Search projects within a domain.

        Args:
            scope: DomainProjectOperationScope defining the domain to search within.
            querier: Contains conditions, orders, and pagination.

        Returns:
            ProjectSearchResult with items, total_count, and pagination flags.
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ProjectRow)
            result = await execute_batch_querier(db_sess, query, querier, scopes=[scope])

            items = [row.ProjectRow.to_data() for row in result.rows]

            return ProjectSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_projects_by_user(
        self,
        scope: UserProjectOperationScope,
        querier: BatchQuerier,
    ) -> ProjectSearchResult:
        """Search projects a user is member of.

        Membership comes from the projects' virtual entities; the scope supplies
        the membership predicate.

        Args:
            scope: UserProjectOperationScope defining the user to search for.
            querier: Contains conditions, orders, and pagination.

        Returns:
            ProjectSearchResult with items, total_count, and pagination flags.
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ProjectRow).select_from(ProjectRow)
            result = await execute_batch_querier(db_sess, query, querier, scopes=[scope])

            items = [row.ProjectRow.to_data() for row in result.rows]

            return ProjectSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

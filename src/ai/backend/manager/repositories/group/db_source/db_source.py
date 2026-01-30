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
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import SlotName, VFolderID
from ai.backend.common.utils import nmget
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.errors.resource import (
    ProjectHasActiveEndpointsError,
    ProjectHasActiveKernelsError,
    ProjectHasVFoldersMountedError,
    ProjectNotFound,
)
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow
from ai.backend.manager.models.group import GroupRow, association_groups_users, groups
from ai.backend.manager.models.kernel import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    LIVE_STATUS,
    RESOURCE_USAGE_KERNEL_STATUSES,
    KernelRow,
    kernels,
)
from ai.backend.manager.models.resource_policy import project_resource_policies
from ai.backend.manager.models.resource_usage import fetch_resource_usage
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderDeletionInfo,
    VFolderRow,
    VFolderStatusSet,
    initiate_vfolder_deletion,
    vfolder_status_map,
    vfolders,
)
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.purger import BatchPurger, execute_batch_purger
from ai.backend.manager.repositories.base.updater import Updater, execute_updater
from ai.backend.manager.repositories.group.creators import GroupCreatorSpec
from ai.backend.manager.repositories.group.purgers import (
    GroupBatchPurgerSpec,
    GroupEndpointBatchPurgerSpec,
    GroupKernelBatchPurgerSpec,
    GroupSessionBatchPurgerSpec,
    SessionByIdsBatchPurgerSpec,
)
from ai.backend.manager.repositories.permission_controller.role_manager import RoleManager

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GroupDBSource:
    _db: ExtendedAsyncSAEngine
    _role_manager: RoleManager

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._role_manager = RoleManager()

    async def create(self, creator: Creator[GroupRow]) -> GroupData:
        """Create a new group."""
        spec = cast(GroupCreatorSpec, creator.spec)
        async with self._db.begin_session() as db_session:
            # Validate domain exists
            domain_exists = await db_session.scalar(
                sa.select(sa.exists().where(domains.c.name == spec.domain_name))
            )
            if not domain_exists:
                raise InvalidAPIParameters(
                    f"Cannot create group: Domain '{spec.domain_name}' does not exist"
                )

            # Validate resource policy exists
            policy_exists = await db_session.scalar(
                sa.select(
                    sa.exists().where(project_resource_policies.c.name == spec.resource_policy)
                )
            )
            if not policy_exists:
                raise InvalidAPIParameters(
                    f"Cannot create group: Resource policy '{spec.resource_policy}' does not exist"
                )

            # Check if group already exists
            check_stmt = sa.select(GroupRow).where(
                sa.and_(
                    GroupRow.name == spec.name,
                    GroupRow.domain_name == spec.domain_name,
                )
            )
            existing_group = await db_session.scalar(check_stmt)
            if existing_group is not None:
                raise InvalidAPIParameters(
                    f"Group with name '{spec.name}' already exists in domain '{spec.domain_name}'"
                )

            # Create the group
            creator_result = await execute_creator(db_session, creator)
            row: GroupRow = creator_result.row
            data = row.to_data()
            # Create RBAC role and permissions for the group
            await self._role_manager.create_system_role(db_session, data)

            return data

    async def modify_validated(
        self,
        updater: Updater[GroupRow],
        user_update_mode: str | None = None,
        user_uuids: list[uuid.UUID] | None = None,
    ) -> GroupData | None:
        """Modify a group with validation."""
        group_id = updater.pk_value

        async with self._db.begin_session() as session:
            # First verify the group exists
            existing_group = await session.scalar(
                sa.select(groups.c.id).where(groups.c.id == group_id)
            )
            if existing_group is None:
                raise ProjectNotFound(f"Group not found: {group_id}")

            # Handle user addition/removal
            if user_uuids and user_update_mode:
                if user_update_mode == "add":
                    values = [{"user_id": uuid, "group_id": group_id} for uuid in user_uuids]
                    await session.execute(
                        sa.insert(association_groups_users).values(values),
                    )
                elif user_update_mode == "remove":
                    await session.execute(
                        sa.delete(association_groups_users).where(
                            (association_groups_users.c.user_id.in_(user_uuids))
                            & (association_groups_users.c.group_id == group_id),
                        ),
                    )

            # Update group data (execute_updater returns None if no values to update)
            result = await execute_updater(session, updater)
            if result is not None:
                return result.row.to_data()

            # No group updates or only user updates were performed
            return None

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
            if cast(CursorResult, result).rowcount > 0:
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

        async with self._db.begin_session() as session:
            # Delete remaining data
            await self._delete_group_kernels(session, group_id)
            await self._delete_group_sessions(session, group_id)

            # Finally delete the group itself
            result = await execute_batch_purger(
                session, BatchPurger(spec=GroupBatchPurgerSpec(group_id=group_id), batch_size=1)
            )

            if result.deleted_count > 0:
                return True
            raise ProjectNotFound("project not found")

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
                    pass
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

    async def _delete_group_kernels(self, session: SASession, group_id: uuid.UUID) -> int:
        """Delete all kernels belonging to the group."""
        result = await execute_batch_purger(
            session, BatchPurger(spec=GroupKernelBatchPurgerSpec(group_id=group_id))
        )
        return result.deleted_count

    async def _delete_group_sessions(self, session: SASession, group_id: uuid.UUID) -> int:
        """Delete all sessions belonging to the group."""
        result = await execute_batch_purger(
            session, BatchPurger(spec=GroupSessionBatchPurgerSpec(group_id=group_id))
        )
        return result.deleted_count

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

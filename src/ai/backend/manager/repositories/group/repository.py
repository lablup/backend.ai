import copy
import logging
import uuid
from datetime import datetime
from typing import Optional, Sequence, cast
from uuid import UUID

import msgpack
import sqlalchemy as sa

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.exception import (
    InvalidAPIParameters,
)
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.utils import nmget
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.group.types import GroupCreator, GroupData, GroupModifier
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.group import GroupRow, association_groups_users, groups
from ai.backend.manager.models.kernel import LIVE_STATUS, RESOURCE_USAGE_KERNEL_STATUSES, kernels
from ai.backend.manager.models.resource_policy import keypair_resource_policies
from ai.backend.manager.models.resource_usage import fetch_resource_usage
from ai.backend.manager.models.user import UserRole, users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, SASession

from ..permission_controller.role_manager import RoleManager

# Layer-specific decorator for group repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.GROUP)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GroupRepository:
    _db: ExtendedAsyncSAEngine
    _config_provider: ManagerConfigProvider
    _valkey_stat_client: ValkeyStatClient
    _role_manager: RoleManager

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        config_provider: ManagerConfigProvider,
        valkey_stat_client: ValkeyStatClient,
    ) -> None:
        self._db = db
        self._config_provider = config_provider
        self._valkey_stat_client = valkey_stat_client
        self._role_manager = RoleManager()

    async def _get_group_by_id(self, session: SASession, group_id: uuid.UUID) -> Optional[GroupRow]:
        """Private method to get a group by ID using an existing session."""
        result = await session.execute(sa.select(GroupRow).where(groups.c.id == group_id))
        return result.scalar_one_or_none()

    @repository_decorator()
    async def create(self, creator: GroupCreator) -> GroupData:
        """Create a new group."""
        async with self._db.begin_session() as db_session:
            # Validate domain exists
            domain_exists = await db_session.scalar(
                sa.select(sa.exists().where(domains.c.name == creator.domain_name))
            )
            if not domain_exists:
                raise InvalidAPIParameters(
                    f"Cannot create group: Domain '{creator.domain_name}' does not exist"
                )

            # Validate resource policy exists
            policy_exists = await db_session.scalar(
                sa.select(
                    sa.exists().where(keypair_resource_policies.c.name == creator.resource_policy)
                )
            )
            if not policy_exists:
                raise InvalidAPIParameters(
                    f"Cannot create group: Resource policy '{creator.resource_policy}' does not exist"
                )

            # Check if group already exists
            check_stmt = sa.select(GroupRow).where(
                sa.and_(
                    GroupRow.name == creator.name,
                    GroupRow.domain_name == creator.domain_name,
                )
            )
            existing_group = await db_session.scalar(check_stmt)
            if existing_group is not None:
                raise InvalidAPIParameters(
                    f"Group with name '{creator.name}' already exists in domain '{creator.domain_name}'"
                )

            # Create the group
            row = GroupRow.from_creator(creator)
            db_session.add(row)
            await db_session.flush()
            await db_session.refresh(row)
            data = row.to_data()
            # Create RBAC role and permissions for the group
            await self._role_manager.create_system_role(db_session, data)

            return data

    @repository_decorator()
    async def modify_validated(
        self,
        group_id: uuid.UUID,
        modifier: GroupModifier,
        user_role: UserRole,
        user_update_mode: Optional[str] = None,
        user_uuids: Optional[list[uuid.UUID]] = None,
    ) -> Optional[GroupData]:
        """Modify a group with validation."""
        data = modifier.fields_to_update()

        if user_update_mode not in (None, "add", "remove"):
            raise ValueError("invalid user_update_mode")

        if not data and user_update_mode is None:
            return None

        async with self._db.begin_session() as session:
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

            # Update group data if provided
            if data:
                update_stmt = (
                    sa.update(GroupRow)
                    .values(data)
                    .where(GroupRow.id == group_id)
                    .returning(GroupRow)
                )
                query_stmt = (
                    sa.select(GroupRow)
                    .from_statement(update_stmt)
                    .execution_options(populate_existing=True)
                )
                row = await session.scalar(query_stmt)
                row = cast(Optional[GroupRow], row)
                if row is None:
                    raise ProjectNotFound(f"Project not found: {group_id}")
                return row.to_data()

            # If only user updates were performed, return None
            return None

    @repository_decorator()
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
            if result.rowcount > 0:
                return
            raise ProjectNotFound(f"Group not found: {group_id}")

    @repository_decorator()
    async def get_container_stats_for_period(
        self,
        start_date: datetime,
        end_date: datetime,
        group_ids: Optional[Sequence[UUID]] = None,
    ) -> list[dict]:
        """Get container statistics for groups within a time period."""
        async with self._db.begin_readonly() as conn:
            j = kernels.join(groups, groups.c.id == kernels.c.group_id).join(
                users, users.c.uuid == kernels.c.user_uuid
            )
            query = (
                sa.select([
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
                ])
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

        kernel_ids = [str(row["id"]) for row in rows]
        raw_stats = await self._valkey_stat_client.get_user_kernel_statistics_batch(kernel_ids)

        objs_per_group = {}
        local_tz = self._config_provider.config.system.timezone

        for row, raw_stat in zip(rows, raw_stats):
            group_id = str(row["group_id"])
            last_stat = row["last_stat"]
            if not last_stat:
                if raw_stat is None:
                    log.warning("stat object for {} not found on redis, skipping", str(row["id"]))
                    continue
                last_stat = msgpack.unpackb(raw_stat)
            nfs = None
            if row["vfolder_mounts"]:
                # For >=22.03, return used host directories instead of volume host, which is not so useful.
                nfs = list(set([str(mount.host_path) for mount in row["vfolder_mounts"]]))
            elif row["mounts"] and isinstance(row["mounts"][0], list):
                # For the kernel records that have legacy contents of `mounts`.
                nfs = list(set([mount[2] for mount in row["mounts"]]))
            if row["terminated_at"] is None:
                used_time = used_days = None
            else:
                used_time = str(row["terminated_at"] - row["created_at"])
                used_days = (
                    row["terminated_at"].astimezone(local_tz).toordinal()
                    - row["created_at"].astimezone(local_tz).toordinal()
                    + 1
                )
            device_type = set()
            smp = 0
            gpu_mem_allocated = 0
            if row.attached_devices and row.attached_devices.get("cuda"):
                for dev_info in row.attached_devices["cuda"]:
                    if dev_info.get("model_name"):
                        device_type.add(dev_info["model_name"])
                    smp += int(nmget(dev_info, "data.smp", 0))
                    gpu_mem_allocated += int(nmget(dev_info, "data.mem", 0))
            gpu_allocated = 0
            if "cuda.devices" in row.occupied_slots:
                gpu_allocated = row.occupied_slots["cuda.devices"]
            if "cuda.shares" in row.occupied_slots:
                gpu_allocated = row.occupied_slots["cuda.shares"]
            c_info = {
                "id": str(row["id"]),
                "session_id": str(row["session_id"]),
                "container_id": row["container_id"],
                "domain_name": row["domain_name"],
                "group_id": str(row["group_id"]),
                "group_name": row["name"],
                "name": row["session_name"],
                "access_key": row["access_key"],
                "email": row["email"],
                "full_name": row["full_name"],
                "agent": row["agent"],
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
                "smp": float(smp),
                "gpu_mem_allocated": float(gpu_mem_allocated),
                "gpu_allocated": float(gpu_allocated),  # devices or shares
                "nfs": nfs,
                "image_id": row["image"],  # TODO: image id
                "image_name": row["image"],
                "created_at": str(row["created_at"]),
                "terminated_at": str(row["terminated_at"]),
                "status": row["status"].name,
                "status_info": row["status_info"],
                "status_changed": str(row["status_changed"]),
                "status_history": row["status_history"] or {},
                "cluster_mode": row["cluster_mode"],
            }
            if group_id not in objs_per_group:
                objs_per_group[group_id] = {
                    "domain_name": row["domain_name"],
                    "g_id": group_id,
                    "g_name": row["name"],  # this is group's name
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

    @repository_decorator()
    async def fetch_project_resource_usage(
        self,
        start_date: datetime,
        end_date: datetime,
        project_ids: Optional[Sequence[UUID]] = None,
    ):
        """Fetch resource usage data for projects."""
        return await fetch_resource_usage(self._db, start_date, end_date, project_ids=project_ids)

import asyncio
import copy
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Optional, Sequence, cast
from uuid import UUID

import aiotools
import msgpack
import sqlalchemy as sa
from dateutil.relativedelta import relativedelta
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline as RedisPipeline

from ai.backend.common import redis_helper
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import RedisConnectionInfo, VFolderID
from ai.backend.common.utils import nmget
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.exceptions import VFolderOperationFailed
from ai.backend.manager.models.group import association_groups_users, groups
from ai.backend.manager.models.kernel import (
    LIVE_STATUS,
    RESOURCE_USAGE_KERNEL_STATUSES,
    kernels,
)
from ai.backend.manager.models.resource_usage import (
    ProjectResourceUsage,
    fetch_resource_usage,
    parse_resource_usage_groups,
    parse_total_resource_group,
)
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, SAConnection, execute_with_retry
from ai.backend.manager.services.group.actions.create_group import (
    CreateGroupAction,
    CreateGroupActionResult,
)
from ai.backend.manager.services.group.actions.delete_group import (
    DeleteGroupAction,
    DeleteGroupActionResult,
)
from ai.backend.manager.services.group.actions.modify_group import (
    ModifyGroupAction,
    ModifyGroupActionResult,
)
from ai.backend.manager.services.group.actions.purge_group import (
    PurgeGroupAction,
    PurgeGroupActionResult,
)
from ai.backend.manager.services.group.actions.usage_per_month import (
    UsagePerMonthAction,
    UsagePerMonthActionResult,
)
from ai.backend.manager.services.group.actions.usage_per_period import (
    UsagePerPeriodAction,
    UsagePerPeriodActionResult,
)
from ai.backend.manager.services.group.types import GroupData

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class MutationResult:
    success: bool
    message: str
    data: Optional[Any]


class GroupService:
    _db: ExtendedAsyncSAEngine
    _config_provider: ManagerConfigProvider
    _redis_stat: RedisConnectionInfo
    _storage_manager: StorageSessionManager

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        storage_manager: StorageSessionManager,
        config_provider: ManagerConfigProvider,
        redis_stat: RedisConnectionInfo,
    ) -> None:
        self._db = db
        self._storage_manager = storage_manager
        self._config_provider = config_provider
        self._redis_stat = redis_stat

    async def create_group(self, action: CreateGroupAction) -> CreateGroupActionResult:
        data = action.input.fields_to_store()
        base_query = sa.insert(groups).values(data)

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                query = base_query.returning(base_query.table)
                result = await conn.execute(query)
                row = result.first()
                if result.rowcount > 0:
                    return MutationResult(
                        success=True,
                        message=f"Group {action.input.name} creation succeed",
                        data=row,
                    )
                else:
                    return MutationResult(
                        success=False, message=f"no matching {action.input.name}", data=None
                    )

        res: MutationResult = await self._db_mutation_wrapper(_do_mutate)

        return CreateGroupActionResult(data=GroupData.from_row(res.data), success=res.success)

    async def modify_group(self, action: ModifyGroupAction) -> ModifyGroupActionResult:
        data = action.modifier.fields_to_update()

        if action.user_update_mode.optional_value() not in (
            None,
            "add",
            "remove",
        ):
            raise ValueError("invalid user_update_mode")
        update_mode = action.update_mode()
        if not data and update_mode is None:
            return ModifyGroupActionResult(data=None, success=False)

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                # TODO: refactor user addition/removal in groups as separate mutations
                #       (to apply since 21.09)
                gid = action.group_id
                user_uuids = action.user_uuids.optional_value()
                if user_uuids:
                    if update_mode == "add":
                        values = [{"user_id": uuid, "group_id": gid} for uuid in user_uuids]
                        await conn.execute(
                            sa.insert(association_groups_users).values(values),
                        )
                    elif update_mode == "remove":
                        await conn.execute(
                            sa.delete(association_groups_users).where(
                                (association_groups_users.c.user_id.in_(user_uuids))
                                & (association_groups_users.c.group_id == gid),
                            ),
                        )
                if data:
                    result = await conn.execute(
                        sa.update(groups).values(data).where(groups.c.id == gid).returning(groups),
                    )
                    if result.rowcount > 0:
                        row = result.first()
                        return MutationResult(success=True, message="success", data=row)
                    return MutationResult(success=False, message=f"no such group {gid}", data=None)
                else:  # updated association_groups_users table
                    return MutationResult(success=True, message="success", data=None)

        res: MutationResult = await self._db_mutation_wrapper(_do_mutate)

        return ModifyGroupActionResult(data=GroupData.from_row(res.data), success=res.success)

    async def delete_group(self, action: DeleteGroupAction) -> DeleteGroupActionResult:
        update_query = (
            sa.update(groups)
            .values(
                is_active=False,
                integration_id=None,
            )
            .where(groups.c.id == action.group_id)
        )

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                result = await conn.execute(update_query)
                if result.rowcount > 0:
                    return MutationResult(success=True, message="success", data=None)
                return MutationResult(
                    success=False, message=f"no such group {action.group_id}", data=None
                )

        res: MutationResult = await self._db_mutation_wrapper(_do_mutate)

        return DeleteGroupActionResult(data=GroupData.from_row(res.data), success=res.success)

    async def purge_group(self, action: PurgeGroupAction) -> PurgeGroupActionResult:
        gid = action.group_id

        async def _pre_func(conn: SAConnection) -> None:
            if await self._group_vfolder_mounted_to_active_kernels(conn, gid):
                raise RuntimeError(
                    "Some of virtual folders that belong to this group "
                    "are currently mounted to active sessions. "
                    "Terminate them first to proceed removal.",
                )
            if await self._group_has_active_kernels(conn, gid):
                raise RuntimeError(
                    "Group has some active session. Terminate them first to proceed removal.",
                )
            await self._delete_vfolders(gid)
            await self._delete_kernels(conn, gid)
            await self._delete_sessions(conn, gid)

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                delete_query = sa.delete(groups).where(groups.c.id == gid)
                await _pre_func(conn)
                result = await conn.execute(delete_query)
                if result.rowcount > 0:
                    return MutationResult(
                        success=True, message=f"Group {action.group_id} deleted succeed", data=None
                    )
                else:
                    return MutationResult(
                        success=False, message=f"no matching {action.group_id}", data=None
                    )

        res: MutationResult = await self._db_mutation_wrapper(_do_mutate)

        return PurgeGroupActionResult(data=GroupData.from_row(res.data), success=res.success)

    async def _group_vfolder_mounted_to_active_kernels(
        self, db_conn: SAConnection, group_id: uuid.UUID
    ) -> bool:
        from ai.backend.manager.models import (
            AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
            kernels,
            vfolders,
        )

        query = sa.select([vfolders.c.id]).select_from(vfolders).where(vfolders.c.group == group_id)
        result = await db_conn.execute(query)
        rows = result.fetchall()
        group_vfolder_ids = [row["id"] for row in rows]
        query = (
            sa.select([kernels.c.mounts])
            .select_from(kernels)
            .where(
                (kernels.c.group_id == group_id)
                & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
            )
        )
        async for row in await db_conn.stream(query):
            for _mount in row["mounts"]:
                try:
                    vfolder_id = uuid.UUID(_mount[2])
                    if vfolder_id in group_vfolder_ids:
                        return True
                except Exception:
                    pass
        return False

    async def _group_has_active_kernels(self, db_conn: SAConnection, group_id: uuid.UUID) -> bool:
        from ai.backend.manager.models import AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES, kernels

        query = (
            sa.select([sa.func.count()])
            .select_from(kernels)
            .where(
                (kernels.c.group_id == group_id)
                & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
            )
        )
        active_kernel_count = await db_conn.scalar(query)
        return True if active_kernel_count > 0 else False

    async def _delete_vfolders(self, group_id: uuid.UUID) -> int:
        from ai.backend.manager.models import (
            VFolderDeletionInfo,
            VFolderRow,
            VFolderStatusSet,
            initiate_vfolder_deletion,
            vfolder_status_map,
        )

        target_vfs: list[VFolderDeletionInfo] = []
        async with self._db.begin_session() as db_session:
            query = sa.select(VFolderRow).where(
                sa.and_(
                    VFolderRow.group == group_id,
                    VFolderRow.status.in_(vfolder_status_map[VFolderStatusSet.DELETABLE]),
                )
            )
            result = await db_session.scalars(query)
            rows = cast(list[VFolderRow], result.fetchall())
            for vf in rows:
                target_vfs.append(
                    VFolderDeletionInfo(VFolderID.from_row(vf), vf.host, vf.unmanaged_path)
                )

        storage_ptask_group = aiotools.PersistentTaskGroup()
        try:
            await initiate_vfolder_deletion(
                self._db,
                target_vfs,
                self._storage_manager,
                storage_ptask_group,
            )
        except VFolderOperationFailed as e:
            log.error("error on deleting vfolder filesystem directory: {0}", e.extra_msg)
            raise
        deleted_count = len(target_vfs)
        if deleted_count > 0:
            log.info("deleted {0} group's virtual folders ({1})", deleted_count, group_id)
        return deleted_count

    async def _delete_kernels(self, db_conn: SAConnection, group_id: uuid.UUID) -> None:
        from ai.backend.manager.models import kernels

        query = sa.delete(kernels).where(kernels.c.group_id == group_id)
        result = await db_conn.execute(query)
        if result.rowcount > 0:
            log.info("deleted {0} group's kernels ({1})", result.rowcount, group_id)
        return result.rowcount

    async def _delete_sessions(self, db_conn: SAConnection, group_id: uuid.UUID) -> None:
        from ai.backend.manager.models.session import SessionRow

        stmt = sa.delete(SessionRow).where(SessionRow.group_id == group_id)
        await db_conn.execute(stmt)

    async def _db_mutation_wrapper(
        self, _do_mutate: Callable[[], Awaitable[MutationResult]]
    ) -> MutationResult:
        try:
            return await execute_with_retry(_do_mutate)
        except sa.exc.IntegrityError as e:
            log.warning("db_mutation_wrapper(): integrity error ({})", repr(e))
            return MutationResult(success=False, message=f"integrity error: {e}", data=None)
        except sa.exc.StatementError as e:
            log.warning(
                "db_mutation_wrapper(): statement error ({})\n{}",
                repr(e),
                e.statement or "(unknown)",
            )
            orig_exc = e.orig
            return MutationResult(success=False, message=str(orig_exc), data=None)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            raise
        except Exception:
            log.exception("db_mutation_wrapper(): other error")
            raise

    async def _get_project_stats_for_period(
        self,
        start_date: datetime,
        end_date: datetime,
        project_ids: Optional[Sequence[UUID]] = None,
    ) -> dict[UUID, ProjectResourceUsage]:
        kernels = await fetch_resource_usage(
            self._db, start_date, end_date, project_ids=project_ids
        )
        local_tz = self._config_provider.config.system.timezone
        usage_groups = await parse_resource_usage_groups(kernels, self._redis_stat, local_tz)
        total_groups, _ = parse_total_resource_group(usage_groups)
        return total_groups

    async def _get_container_stats_for_period(
        self,
        start_date: datetime,
        end_date: datetime,
        group_ids: Optional[Sequence[UUID]] = None,
    ):
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

        async def _pipe_builder(r: Redis) -> RedisPipeline:
            pipe = r.pipeline()
            for row in rows:
                await pipe.get(str(row["id"]))
            return pipe

        raw_stats = await redis_helper.execute(self._redis_stat, _pipe_builder)

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

    # group (or all the groups)
    async def usage_per_month(self, action: UsagePerMonthAction) -> UsagePerMonthActionResult:
        month = action.month
        local_tz = self._config_provider.config.system.timezone

        try:
            start_date = datetime.strptime(month, "%Y%m").replace(tzinfo=local_tz)
            end_date = start_date + relativedelta(months=+1)
        except ValueError:
            raise InvalidAPIParameters(extra_msg="Invalid date values")
        result = await self._get_container_stats_for_period(start_date, end_date, action.group_ids)
        log.debug("container list are retrieved for month {0}", month)
        return UsagePerMonthActionResult(result=result)

    # group (or all the groups)
    async def usage_per_period(self, action: UsagePerPeriodAction) -> UsagePerPeriodActionResult:
        local_tz = self._config_provider.config.system.timezone
        project_id = action.project_id

        try:
            start_date = datetime.strptime(action.start_date, "%Y%m%d").replace(tzinfo=local_tz)
            end_date = datetime.strptime(action.end_date, "%Y%m%d").replace(tzinfo=local_tz)
            end_date = end_date + timedelta(days=1)  # include sessions in end_date
            if end_date - start_date > timedelta(days=100):
                raise InvalidAPIParameters("Cannot query more than 100 days")
        except ValueError:
            raise InvalidAPIParameters(extra_msg="Invalid date values")
        if end_date <= start_date:
            raise InvalidAPIParameters(extra_msg="end_date must be later than start_date.")
        log.info(
            "USAGE_PER_MONTH (p:{}, start_date:{}, end_date:{})", project_id, start_date, end_date
        )
        project_ids = [project_id] if project_id is not None else None
        usage_map = await self._get_project_stats_for_period(
            start_date, end_date, project_ids=project_ids
        )
        result = [p_usage.to_json(child=True) for p_usage in usage_map.values()]
        log.debug("container list are retrieved from {0} to {1}", start_date, end_date)
        return UsagePerPeriodActionResult(result=result)

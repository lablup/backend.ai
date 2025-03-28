import copy
import logging
from datetime import datetime, timedelta
from typing import Optional, Sequence
from uuid import UUID

import msgpack
import sqlalchemy as sa
from dateutil.relativedelta import relativedelta
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline as RedisPipeline

from ai.backend.common import redis_helper
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import (
    RedisConnectionInfo,
)
from ai.backend.common.utils import nmget
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config import SharedConfig
from ai.backend.manager.models.group import groups
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
from ai.backend.manager.models.user import users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.group.actions.usage_per_month import (
    UsagePerMonthAction,
    UsagePerMonthActionResult,
)
from ai.backend.manager.services.group.actions.usage_per_period import (
    UsagePerPeriodAction,
    UsagePerPeriodActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GroupService:
    _db: ExtendedAsyncSAEngine
    _shared_config: SharedConfig
    _redis_stat: RedisConnectionInfo

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        redis_stat: RedisConnectionInfo,
        shared_config: SharedConfig,
    ) -> None:
        self._db = db
        self._redis_stat = redis_stat
        self._shared_config = shared_config

    async def _get_project_stats_for_period(
        self,
        start_date: datetime,
        end_date: datetime,
        project_ids: Optional[Sequence[UUID]] = None,
    ) -> dict[UUID, ProjectResourceUsage]:
        kernels = await fetch_resource_usage(
            self._db, start_date, end_date, project_ids=project_ids
        )
        local_tz = self._shared_config["system"]["timezone"]
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
        local_tz = self._shared_config["system"]["timezone"]

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

    # group (or group 전체)
    async def usage_per_month(self, action: UsagePerMonthAction) -> UsagePerMonthActionResult:
        month = action.month
        local_tz = self._shared_config["system"]["timezone"]

        try:
            start_date = datetime.strptime(month, "%Y%m").replace(tzinfo=local_tz)
            end_date = start_date + relativedelta(months=+1)
        except ValueError:
            raise InvalidAPIParameters(extra_msg="Invalid date values")
        result = await self._get_container_stats_for_period(start_date, end_date, action.group_ids)
        log.debug("container list are retrieved for month {0}", month)
        return UsagePerMonthActionResult(result=result)

    # group (or group 전체)
    async def usage_per_period(self, action: UsagePerPeriodAction) -> UsagePerPeriodActionResult:
        local_tz = self._shared_config["system"]["timezone"]
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

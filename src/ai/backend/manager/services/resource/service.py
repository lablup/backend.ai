import copy
from datetime import datetime
from decimal import Decimal
from typing import Optional, Sequence, cast
from uuid import UUID

import msgpack
import sqlalchemy as sa
from dateutil.relativedelta import relativedelta
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline as RedisPipeline
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.account_manager.exceptions import InvalidAPIParameters
from ai.backend.common import logging, redis_helper
from ai.backend.common.types import DefaultForUnspecified, RedisConnectionInfo, ResourceSlot
from ai.backend.common.utils import nmget
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config import SharedConfig
from ai.backend.manager.models.agent import AgentStatus, agents
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.group import association_groups_users, groups
from ai.backend.manager.models.kernel import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    LIVE_STATUS,
    RESOURCE_USAGE_KERNEL_STATUSES,
    KernelRow,
    kernels,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.resource_usage import (
    ProjectResourceUsage,
    fetch_resource_usage,
    parse_resource_usage_groups,
    parse_total_resource_group,
)
from ai.backend.manager.models.scaling_group import query_allowed_sgroups
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.resource.actions.check_presets import (
    CheckResourcePresetsAction,
    CheckResourcePresetsActionResult,
)
from ai.backend.manager.services.resource.actions.list_presets import (
    ListResourcePresetsAction,
    ListResourcePresetsResult,
)
from ai.backend.manager.services.resource.actions.recalculate_usage import (
    RecalculateUsageAction,
    RecalculateUsageActionResult,
)
from ai.backend.manager.services.resource.actions.usage_per_month import (
    UsagePerMonthAction,
    UsagePerMonthActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ResourceService:
    _db: ExtendedAsyncSAEngine
    _shared_config: SharedConfig
    _agent_registry: AgentRegistry
    _redis_stat: RedisConnectionInfo

    # TODO: 인자들 한 타입으로 묶을 것.
    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        agent_registry: AgentRegistry,
        redis_stat: RedisConnectionInfo,
        shared_config: SharedConfig,
    ) -> None:
        self._db = db
        self._agent_registry = agent_registry
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

    async def list_presets(self, action: ListResourcePresetsAction) -> ListResourcePresetsResult:
        # TODO: Remove this?
        await self._shared_config.get_resource_slots()

        async with self._db.begin_readonly_session() as db_session:
            query = sa.select(ResourcePresetRow)
            query_condition = ResourcePresetRow.scaling_group_name.is_(sa.null())
            scaling_group_name = action.scaling_group
            if scaling_group_name is not None:
                query_condition = sa.or_(
                    query_condition, ResourcePresetRow.scaling_group_name == scaling_group_name
                )
            query = query.where(query_condition)
            presets = []
            async for row in await db_session.stream_scalars(query):
                row = cast(ResourcePresetRow, row)
                preset_slots = row.resource_slots.normalize_slots(ignore_unknown=True)
                presets.append({
                    "id": str(row.id),
                    "name": row.name,
                    "shared_memory": str(row.shared_memory) if row.shared_memory else None,
                    "resource_slots": preset_slots.to_json(),
                })

            return ListResourcePresetsResult(presets=presets)

    async def check_presets(
        self, action: CheckResourcePresetsAction
    ) -> CheckResourcePresetsActionResult:
        access_key = action.access_key
        resource_policy = action.resource_policy
        domain_name = action.domain_name

        known_slot_types = await self._shared_config.get_resource_slots()

        async with self._db.begin_readonly() as conn:
            # Check keypair resource limit.
            keypair_limits = ResourceSlot.from_policy(resource_policy, known_slot_types)
            keypair_occupied = await self._agent_registry.get_keypair_occupancy(
                access_key, db_sess=SASession(conn)
            )
            keypair_remaining = keypair_limits - keypair_occupied

            # Check group resource limit and get group_id.
            j = sa.join(
                groups,
                association_groups_users,
                association_groups_users.c.group_id == groups.c.id,
            )
            query = (
                sa.select([groups.c.id, groups.c.total_resource_slots])
                .select_from(j)
                .where(
                    (association_groups_users.c.user_id == action.user_id)
                    & (groups.c.name == action.group)
                    & (groups.c.domain_name == domain_name),
                )
            )
            result = await conn.execute(query)
            row = result.first()
            if row is None:
                raise InvalidAPIParameters(f"Unknown project (name: {action.group})")
            group_id = row["id"]
            group_resource_slots = row["total_resource_slots"]
            if group_id is None:
                raise InvalidAPIParameters(f"Unknown project (name: {action.group})")
            group_resource_policy = {
                "total_resource_slots": group_resource_slots,
                "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
            }
            group_limits = ResourceSlot.from_policy(group_resource_policy, known_slot_types)
            group_occupied = await self._agent_registry.get_group_occupancy(
                group_id, db_sess=SASession(conn)
            )
            group_remaining = group_limits - group_occupied

            # Check domain resource limit.
            query = sa.select([domains.c.total_resource_slots]).where(domains.c.name == domain_name)
            domain_resource_slots = await conn.scalar(query)
            domain_resource_policy = {
                "total_resource_slots": domain_resource_slots,
                "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
            }
            domain_limits = ResourceSlot.from_policy(domain_resource_policy, known_slot_types)
            domain_occupied = await self._agent_registry.get_domain_occupancy(
                domain_name, db_sess=SASession(conn)
            )
            domain_remaining = domain_limits - domain_occupied

            # Take minimum remaining resources. There's no need to merge limits and occupied.
            # To keep legacy, we just merge all remaining slots into `keypair_remainig`.
            for slot in known_slot_types:
                keypair_remaining[slot] = min(
                    keypair_remaining[slot],
                    group_remaining[slot],
                    domain_remaining[slot],
                )

            # Prepare per scaling group resource.
            sgroups = await query_allowed_sgroups(conn, domain_name, group_id, access_key)
            sgroup_names = [sg.name for sg in sgroups]
            if action.scaling_group is not None:
                if action.scaling_group not in sgroup_names:
                    raise InvalidAPIParameters("Unknown scaling group")
                sgroup_names = [action.scaling_group]
            per_sgroup = {
                sgname: {
                    "using": ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()}),
                    "remaining": ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()}),
                }
                for sgname in sgroup_names
            }

            # Per scaling group resource using from resource occupying kernels.
            j = sa.join(KernelRow, SessionRow, KernelRow.session_id == SessionRow.id)
            query = (
                sa.select([KernelRow.occupied_slots, SessionRow.scaling_group_name])
                .select_from(j)
                .where(
                    (KernelRow.user_uuid == action.user_id)
                    & (KernelRow.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                    & (SessionRow.scaling_group_name.in_(sgroup_names)),
                )
            )
            async for row in await conn.stream(query):
                per_sgroup[row["scaling_group_name"]]["using"] += row["occupied_slots"]

            # Per scaling group resource remaining from agents stats.
            sgroup_remaining = ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()})
            query = (
                sa.select([
                    agents.c.available_slots,
                    agents.c.occupied_slots,
                    agents.c.scaling_group,
                ])
                .select_from(agents)
                .where(
                    (agents.c.status == AgentStatus.ALIVE)
                    & (agents.c.scaling_group.in_(sgroup_names)),
                )
            )
            agent_slots = []
            async for row in await conn.stream(query):
                remaining = row["available_slots"] - row["occupied_slots"]
                remaining += ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()})
                sgroup_remaining += remaining
                agent_slots.append(remaining)
                per_sgroup[row["scaling_group"]]["remaining"] += remaining

            # Take maximum allocatable resources per sgroup.
            for sgname, sgfields in per_sgroup.items():
                for rtype, slots in sgfields.items():
                    if rtype == "remaining":
                        for slot in known_slot_types.keys():
                            if slot in slots:
                                slots[slot] = min(keypair_remaining[slot], slots[slot])
                    per_sgroup[sgname][rtype] = slots.to_json()  # type: ignore  # it's serialization
            for slot in known_slot_types.keys():
                sgroup_remaining[slot] = min(keypair_remaining[slot], sgroup_remaining[slot])

            # Fetch all resource presets in the current scaling group.
            resource_preset_query = sa.select(ResourcePresetRow)
            query_condition = ResourcePresetRow.scaling_group_name.is_(sa.null())
            if action.scaling_group is not None:
                query_condition = sa.or_(
                    query_condition,
                    ResourcePresetRow.scaling_group_name == action.scaling_group,
                )
            resource_preset_query = resource_preset_query.where(query_condition)

            presets = []
            async for row in await SASession(conn).stream_scalars(resource_preset_query):
                # Check if there are any agent that can allocate each preset.
                row = cast(ResourcePresetRow, row)
                allocatable = False
                preset_slots = row.resource_slots.normalize_slots(ignore_unknown=True)
                for agent_slot in agent_slots:
                    if agent_slot >= preset_slots and keypair_remaining >= preset_slots:
                        allocatable = True
                        break
                presets.append({
                    "id": str(row.id),
                    "name": row.name,
                    "resource_slots": preset_slots.to_json(),
                    "shared_memory": (
                        str(row.shared_memory) if row.shared_memory is not None else None
                    ),
                    "allocatable": allocatable,
                })

            # Return group resource status as NaN if not allowed.
            group_resource_visibility = await self._shared_config.get_raw(
                "config/api/resources/group_resource_visibility"
            )
            group_resource_visibility = t.ToBool().check(group_resource_visibility)
            if not group_resource_visibility:
                group_limits = ResourceSlot({k: Decimal("NaN") for k in known_slot_types.keys()})
                group_occupied = ResourceSlot({k: Decimal("NaN") for k in known_slot_types.keys()})
                group_remaining = ResourceSlot({k: Decimal("NaN") for k in known_slot_types.keys()})

            return CheckResourcePresetsActionResult(
                presets=presets,
                keypair_limits=keypair_limits.to_json(),
                keypair_using=keypair_occupied.to_json(),
                keypair_remaining=keypair_remaining.to_json(),
                group_limits=group_limits.to_json(),
                group_using=group_occupied.to_json(),
                group_remaining=group_remaining.to_json(),
                scaling_group_remaining=sgroup_remaining.to_json(),
                scaling_groups=per_sgroup,
            )

    async def recalculate_usage(
        self, action: RecalculateUsageAction
    ) -> RecalculateUsageActionResult:
        await self._agent_registry.recalc_resource_usage()
        return RecalculateUsageActionResult()

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

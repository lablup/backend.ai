from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Optional, Sequence
from uuid import UUID

import attrs
import msgpack
import sqlalchemy as sa
from dateutil.tz.tz import tzfile
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline as RedisPipeline
from sqlalchemy.orm import joinedload, load_only

from ai.backend.common import redis_helper
from ai.backend.common.types import RedisConnectionInfo
from ai.backend.common.utils import nmget

from .group import GroupRow
from .kernel import LIVE_STATUS, RESOURCE_USAGE_KERNEL_STATUSES, KernelRow, KernelStatus
from .session import SessionRow
from .user import UserRow
from .utils import ExtendedAsyncSAEngine

__all__: Sequence[str] = (
    "ResourceGroupUnit",
    "ResourceUsage",
    "BaseResourceUsageGroup",
    "parse_resource_usage",
    "parse_resource_usage_groups",
    "fetch_resource_usage",
)


class ResourceGroupUnit(str, Enum):
    KERNEL = "kernel"
    SESSION = "session"
    PROJECT = "project"
    DOMAIN = "domain"
    TOTAL = "total"


@attrs.define(slots=True)
class ResourceUsage:
    nfs: set = attrs.field(factory=set)
    cpu_allocated: float = attrs.field(default=0.0)
    cpu_used: float = attrs.field(default=0.0)
    mem_allocated: int = attrs.field(default=0)
    mem_used: int = attrs.field(default=0)
    shared_memory: int = attrs.field(default=0)
    disk_allocated: int = attrs.field(default=0)  # TODO: disk quota limit
    disk_used: int = attrs.field(default=0)
    io_read: int = attrs.field(default=0)
    io_write: int = attrs.field(default=0)
    device_type: set = attrs.field(factory=set)
    smp: float = attrs.field(default=0.0)
    gpu_mem_allocated: float = attrs.field(default=0.0)
    gpu_allocated: float = attrs.field(default=0.0)

    agent_ids: set[str] = attrs.field(factory=set)

    def __add__(self, other: Any) -> ResourceUsage:
        if not isinstance(other, ResourceUsage):
            raise TypeError(
                "ResourceUsage should only be added to `ResourceUsage` type,"
                f" not `{type(other)}` type."
            )
        assert isinstance(other, ResourceUsage)
        self.nfs |= other.nfs  # Is this correct??
        self.device_type |= other.device_type
        self.cpu_allocated += other.cpu_allocated
        self.cpu_used += other.cpu_used
        self.mem_allocated += other.mem_allocated
        self.mem_used += other.mem_used
        self.shared_memory += other.shared_memory
        self.disk_allocated += other.disk_allocated
        self.disk_used += other.disk_used
        self.io_read += other.io_read
        self.io_write += other.io_write
        self.smp += other.smp
        self.gpu_mem_allocated += other.gpu_mem_allocated
        self.gpu_allocated += other.gpu_allocated
        self.agent_ids |= other.agent_ids
        return self

    def to_json(self) -> Mapping[str, Any]:
        return {
            "nfs": list(self.nfs),
            "cpu_allocated": self.cpu_allocated,
            "cpu_used": self.cpu_used,
            "mem_allocated": self.mem_allocated,
            "mem_used": self.mem_used,
            "shared_memory": self.shared_memory,
            "disk_allocated": self.disk_allocated,
            "disk_used": self.disk_used,
            "io_read": self.io_read,
            "io_write": self.io_write,
            "device_type": list(self.device_type),
            "smp": self.smp,
            "gpu_mem_allocated": self.gpu_mem_allocated,
            "gpu_allocated": self.gpu_allocated,
        }

    def copy(self) -> ResourceUsage:
        return attrs.evolve(self, nfs={*self.nfs}, device_type={*self.device_type})


def to_str(val: Any) -> Optional[str]:
    return str(val) if val is not None else None


@attrs.define(slots=True)
class BaseResourceUsageGroup:
    group_unit: ResourceGroupUnit
    child_usage_group: dict = attrs.field(factory=dict)

    project_row: Optional[GroupRow] = attrs.field(default=None)
    session_row: Optional[SessionRow] = attrs.field(default=None)
    kernel_row: Optional[KernelRow] = attrs.field(default=None)

    created_at: Optional[datetime] = attrs.field(default=None)
    terminated_at: Optional[datetime] = attrs.field(default=None)
    scheduled_at: Optional[str] = attrs.field(default=None)
    used_time: Optional[str] = attrs.field(default=None)
    used_days: Optional[int] = attrs.field(default=None)
    agents: Optional[set[str]] = attrs.field(default=None)

    user_id: Optional[UUID] = attrs.field(default=None)
    user_email: Optional[str] = attrs.field(default=None)
    full_name: Optional[str] = attrs.field(default=None)  # User's full_name
    access_key: Optional[UUID] = attrs.field(default=None)
    project_id: Optional[UUID] = attrs.field(default=None)
    project_name: Optional[str] = attrs.field(default=None)
    kernel_id: Optional[UUID] = attrs.field(default=None)
    container_ids: Optional[set[str]] = attrs.field(default=None)
    session_id: Optional[UUID] = attrs.field(default=None)
    session_name: Optional[str] = attrs.field(default=None)
    domain_name: Optional[str] = attrs.field(default=None)
    images: Optional[set[str]] = attrs.field(default=None)

    last_stat: Optional[Mapping[str, Any]] = attrs.field(default=None)
    extra_info: Mapping[str, Any] = attrs.field(factory=dict)

    status: Optional[str] = attrs.field(default=None)
    status_info: Optional[str] = attrs.field(default=None)
    status_history: Optional[str] = attrs.field(default=None)
    cluster_mode: Optional[str] = attrs.field(default=None)

    total_usage: ResourceUsage = attrs.field(factory=ResourceUsage)

    # def to_json(self, child: bool = False) -> dict[str, Any]:
    #     return_val = {
    #         **self.to_map(),
    #         "agents": self.total_usage.agent_ids,
    #         "group_unit": self.group_unit.value,
    #         "total_usage": self.total_usage.to_json(),
    #     }
    #     if child:
    #         belonged_infos: dict[str, list[Mapping[str, Any]]] = {}
    #         for g in self.child_usage_group.values():
    #             if g.group_unit.value not in belonged_infos:
    #                 belonged_infos[g.group_unit.value] = []
    #             belonged_infos[g.group_unit.value].append(g.to_json())
    #         return_val = {
    #             **belonged_infos,
    #             **return_val,
    #             # **{k:v for k, v in belonged_infos.items()},
    #         }
    #     return return_val

    def to_map(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at,
            "terminated_at": self.terminated_at,
            "used_time": self.used_time,
            "used_days": self.used_days,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "access_key": self.access_key,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "kernel_id": self.kernel_id,
            "container_ids": self.container_ids.copy() if self.container_ids is not None else None,
            "session_id": self.session_id,
            "session_name": self.session_name,
            "domain_name": self.domain_name,
            "last_stat": {**self.last_stat} if self.last_stat is not None else None,
            "extra_info": {**self.extra_info} if self.extra_info is not None else None,
            "full_name": self.full_name,
            "images": self.images.copy() if self.images is not None else None,
            "agents": self.agents.copy() if self.agents is not None else None,
            "status": self.status,
            "status_info": self.status_info,
            "status_history": self.status_history,
            "cluster_mode": self.cluster_mode,
            "scheduled_at": self.scheduled_at,
            "total_usage": self.total_usage.copy(),
        }

    def to_json_base(self) -> dict[str, Any]:
        return {
            "created_at": to_str(self.created_at),
            "used_time": self.used_time,
            "used_days": self.used_days,
            "user_id": to_str(self.user_id),
            "user_email": self.user_email,
            "access_key": self.access_key,
            "project_id": to_str(self.project_id),
            "project_name": self.project_name,
            "kernel_id": to_str(self.kernel_id),
            "container_ids": list(self.container_ids) if self.container_ids is not None else [],
            "session_id": to_str(self.session_id),
            "session_name": self.session_name,
            "domain_name": self.domain_name,
            "last_stat": self.last_stat,
            "extra_info": self.extra_info,
            "full_name": to_str(self.full_name),
            "images": list(self.images) if self.images is not None else [],
            "agents": list(self.agents) if self.agents is not None else [],
            "status": to_str(self.status),
            "status_info": to_str(self.status_info),
            "status_history": to_str(self.status_history),
            "cluster_mode": to_str(self.cluster_mode),
            "scheduled_at": to_str(self.scheduled_at),
            "terminated_at": to_str(self.terminated_at),
            "total_usage": self.total_usage.to_json(),
        }


@attrs.define(slots=True, kw_only=True)
class KernelResourceUsage(BaseResourceUsageGroup):
    group_unit: ResourceGroupUnit = ResourceGroupUnit.KERNEL
    # child_usage_group: dict = attrs.field(factory=dict)
    agent: str
    kernel_id: UUID
    project_row: GroupRow
    session_row: SessionRow
    kernel_row: KernelRow

    def to_json(self, child: bool = False) -> dict[str, Any]:
        return {
            **self.to_json_base(),
            "agents": list(self.agents) if self.agents is not None else [],
            "agent": self.agent,
            "group_unit": self.group_unit.value,
            "total_usage": self.total_usage.to_json(),
        }

    @classmethod
    def from_base_usage_group(cls, usage_group: BaseResourceUsageGroup) -> KernelResourceUsage:
        if usage_group.group_unit != ResourceGroupUnit.KERNEL:
            raise ValueError(
                "Unable to parse `KernelResourceUsage` from usage_group "
                "that DOES NOT have `ResourceGroupUnit.KERNEL` on group_unit field."
            )
        if (
            usage_group.project_row is None
            or usage_group.session_row is None
            or usage_group.kernel_row is None
        ):
            raise ValueError(
                "Cannot parse `KernelResourceUsage` from usage_group that have None value field"
            )
        return cls(
            project_row=usage_group.project_row,
            session_row=usage_group.session_row,
            kernel_row=usage_group.kernel_row,
            agent=usage_group.kernel_row.agent,
            **usage_group.to_map(),
        )

    def register_resource_group(
        self,
        other: BaseResourceUsageGroup,
    ) -> bool:
        return True


@attrs.define(slots=True, kw_only=True)
class SessionResourceUsage(BaseResourceUsageGroup):
    group_unit: ResourceGroupUnit = ResourceGroupUnit.SESSION
    child_usage_group: dict[UUID, KernelResourceUsage] = attrs.Factory(dict)
    session_id: UUID
    project_row: GroupRow
    session_row: SessionRow

    def to_json(self, child: bool = False) -> dict[str, Any]:
        return_val = {
            **self.to_json_base(),
            "agents": list(self.agents) if self.agents is not None else [],
            "group_unit": self.group_unit.value,
            "total_usage": self.total_usage.to_json(),
        }
        if child:
            return_val = {
                **return_val,
                "kernels": {
                    str(g.kernel_id): g.to_json(child) for g in self.child_usage_group.values()
                },
            }
        return return_val

    @classmethod
    def from_base_usage_group(cls, usage_group: BaseResourceUsageGroup) -> SessionResourceUsage:
        if usage_group.group_unit not in (ResourceGroupUnit.KERNEL, ResourceGroupUnit.SESSION):
            raise ValueError(
                "Unable to parse `SessionResourceUsage` from usage_group that DOES NOT have"
                " `ResourceGroupUnit.KERNEL` or `ResourceGroupUnit.SESSION` on group_unit field."
            )
        if usage_group.project_row is None or usage_group.session_row is None:
            raise ValueError(
                "Cannot parse `SessionResourceUsage` from usage_group that have None value field"
            )
        return cls(
            project_row=usage_group.project_row,
            session_row=usage_group.session_row,
            **{
                **usage_group.to_map(),
                "total_usage": ResourceUsage(),
            },
        )

    def register_resource_group(self, other: BaseResourceUsageGroup) -> bool:
        if other.kernel_id is None:
            return False
        if other.kernel_id in self.child_usage_group:
            return False
        self.child_usage_group[other.kernel_id] = KernelResourceUsage.from_base_usage_group(other)
        is_registered = self.child_usage_group[other.kernel_id].register_resource_group(other)
        if is_registered:
            self.total_usage += other.total_usage
            if self.images is None:
                self.images = {*(other.images or set())}
            else:
                self.images |= other.images or set()
            if self.agents is None:
                self.agents = {*(other.agents or set())}
            else:
                self.agents |= other.agents or set()
            if self.container_ids is None:
                self.container_ids = {*(other.container_ids or set())}
            else:
                self.container_ids |= other.container_ids or set()
        return is_registered


@attrs.define(slots=True, kw_only=True)
class ProjectResourceUsage(BaseResourceUsageGroup):
    group_unit: ResourceGroupUnit = ResourceGroupUnit.PROJECT
    child_usage_group: dict[UUID, SessionResourceUsage] = attrs.Factory(dict)
    project_id: UUID
    project_row: GroupRow

    def to_json(self, child: bool = False) -> dict[str, Any]:
        return_val = {
            **self.to_json_base(),
            "agents": list(self.total_usage.agent_ids),
            "group_unit": self.group_unit.value,
            "total_usage": self.total_usage.to_json(),
        }
        if child:
            return_val = {
                **return_val,
                "sessions": {
                    str(g.session_id): g.to_json(child) for g in self.child_usage_group.values()
                },
            }
        return return_val

    @classmethod
    def from_base_usage_group(cls, usage_group: BaseResourceUsageGroup) -> ProjectResourceUsage:
        if usage_group.project_row is None:
            raise ValueError(
                "Cannot parse `ProjectResourceUsage` from usage_group that have None value field"
            )
        filtered_data = {
            **usage_group.to_map(),
            "images": None,
            "full_name": None,
            "status": None,
            "status_info": None,
            "status_history": None,
            "cluster_mode": None,
            "scheduled_at": None,
            "terminated_at": None,
            "total_usage": ResourceUsage(),
        }
        return cls(
            project_row=usage_group.project_row,
            **filtered_data,
        )

    def register_resource_group(self, other: BaseResourceUsageGroup) -> bool:
        if other.session_id is None:
            return False
        if other.session_id not in self.child_usage_group:
            self.child_usage_group[other.session_id] = SessionResourceUsage.from_base_usage_group(
                other
            )
        is_registered = self.child_usage_group[other.session_id].register_resource_group(other)
        if is_registered:
            self.total_usage += other.total_usage
            if self.images is None:
                self.images = {*(other.images or set())}
            else:
                self.images |= other.images or set()
            if self.agents is None:
                self.agents = {*(other.agents or set())}
            else:
                self.agents |= other.agents or set()
            if self.container_ids is None:
                self.container_ids = {*(other.container_ids or set())}
            else:
                self.container_ids |= other.container_ids or set()
        return is_registered


# @attrs.define(slots=True, kw_only=True)
# class DomainResourceUsage(BaseResourceUsageGroup):
#     group_unit: ResourceGroupUnit = attrs.field(default=ResourceGroupUnit.DOMAIN)
#     child_usage_group: dict[UUID, ProjectResourceUsage] = attrs.Factory(dict)


def parse_total_resource_group(
    groups: Sequence[BaseResourceUsageGroup],
) -> tuple[dict[UUID, ProjectResourceUsage], ResourceUsage]:
    group_map: dict[UUID, ProjectResourceUsage] = {}
    total_usage = ResourceUsage()
    for g in groups:
        key = g.project_id
        if key is None:
            continue
        if key not in group_map:
            group_map[key] = ProjectResourceUsage.from_base_usage_group(g)
        is_registered = group_map[key].register_resource_group(g)
        if is_registered:
            total_usage += g.total_usage
    return group_map, total_usage


def parse_resource_usage(
    kernel: KernelRow,
    last_stat: Optional[Mapping[str, Any]],
) -> ResourceUsage:
    if not last_stat:
        return ResourceUsage(
            agent_ids={kernel.agent},
        )
    nfs = set()
    if kernel.vfolder_mounts:
        # For >=22.03, return used host directories instead of volume host, which is not so useful.
        nfs = set([str(mount.host_path) for mount in kernel.vfolder_mounts])
    elif kernel.mounts and isinstance(kernel.mounts[0], list):
        # For the kernel records that have legacy contents of `mounts`.
        nfs = set([mount[2] for mount in kernel.mounts])

    device_type = set()
    smp = 0
    gpu_mem_allocated = 0
    if kernel.attached_devices and "cuda" in kernel.attached_devices:
        for dev_info in kernel.attached_devices["cuda"]:
            if (model_name := dev_info.get("model_name")) is not None:
                device_type.add(model_name)
            smp += int(nmget(dev_info, "data.smp", 0))
            gpu_mem_allocated += int(nmget(dev_info, "data.mem", 0))
    gpu_allocated = 0
    if "cuda.devices" in kernel.occupied_slots:
        gpu_allocated = kernel.occupied_slots["cuda.devices"]
    if "cuda.shares" in kernel.occupied_slots:
        gpu_allocated = kernel.occupied_slots["cuda.shares"]

    return ResourceUsage(
        agent_ids={kernel.agent},
        nfs={*nfs},
        cpu_allocated=float(kernel.occupied_slots.get("cpu", 0)),
        cpu_used=float(nmget(last_stat, "cpu_used.current", 0)),
        mem_allocated=int(kernel.occupied_slots.get("mem", 0)),
        mem_used=int(nmget(last_stat, "mem.capacity", 0)),
        shared_memory=int(nmget(kernel.resource_opts, "shmem", 0)),
        disk_allocated=0,
        disk_used=int(nmget(last_stat, "io_scratch_size/stats.max", 0, "/")),
        io_read=int(nmget(last_stat, "io_read.current", 0)),
        io_write=int(nmget(last_stat, "io_write.current", 0)),
        device_type={*device_type},
        smp=float(smp),
        gpu_mem_allocated=float(gpu_mem_allocated),
        gpu_allocated=float(gpu_allocated),
    )


async def parse_resource_usage_groups(
    kernels: list[KernelRow],
    redis_stat: RedisConnectionInfo,
    local_tz: tzfile,
) -> list[BaseResourceUsageGroup]:
    stat_map = {k.id: k.last_stat for k in kernels}
    stat_empty_kerns = [k.id for k in kernels if not k.last_stat]

    async def _pipe_builder(r: Redis) -> RedisPipeline:
        pipe = r.pipeline()
        for kern_id in stat_empty_kerns:
            await pipe.get(str(kern_id))
        return pipe

    raw_stats = await redis_helper.execute(redis_stat, _pipe_builder)
    for kern_id, raw_stat in zip(stat_empty_kerns, raw_stats):
        if raw_stat is None:
            continue
        stat_map[kern_id] = msgpack.unpackb(raw_stat)

    return [
        BaseResourceUsageGroup(
            kernel_row=kern,
            project_row=kern.session.group,
            session_row=kern.session,
            created_at=kern.created_at,
            terminated_at=kern.terminated_at,
            scheduled_at=kern.status_history.get(KernelStatus.SCHEDULED.name),
            used_time=kern.used_time,
            used_days=kern.get_used_days(local_tz),
            last_stat=stat_map[kern.id],
            user_id=kern.session.user_uuid,
            user_email=kern.session.user.email,
            access_key=kern.session.access_key,
            project_id=kern.session.group.id,
            project_name=kern.session.group.name,
            kernel_id=kern.id,
            container_ids={kern.container_id},
            session_id=kern.session_id,
            session_name=kern.session.name,
            domain_name=kern.session.domain_name,
            full_name=kern.session.user.full_name,
            images={kern.image},
            agents={kern.agent},
            status=kern.status.name,
            status_history=kern.status_history,
            cluster_mode=kern.cluster_mode,
            status_info=kern.status_info,
            group_unit=ResourceGroupUnit.KERNEL,
            total_usage=parse_resource_usage(kern, stat_map[kern.id]),
        )
        for kern in kernels
    ]


SESSION_RESOURCE_SELECT_COLS = (
    SessionRow.created_at,
    SessionRow.user_uuid,
    SessionRow.name,
    SessionRow.domain_name,
    SessionRow.id,
    SessionRow.group_id,
    SessionRow.access_key,
    SessionRow.images,
    SessionRow.cluster_mode,
    SessionRow.status_history,
    SessionRow.status,
    SessionRow.status_info,
)

PROJECT_RESOURCE_SELECT_COLS = (
    GroupRow.created_at,
    GroupRow.id,
    GroupRow.name,
    GroupRow.domain_name,
)

KERNEL_RESOURCE_SELECT_COLS = (
    KernelRow.agent,
    KernelRow.created_at,
    KernelRow.terminated_at,
    KernelRow.last_stat,
    KernelRow.status_history,
    KernelRow.status,
    KernelRow.status_info,
    KernelRow.session_id,
    KernelRow.id,
    KernelRow.container_id,
    KernelRow.occupied_slots,
    KernelRow.attached_devices,
    KernelRow.vfolder_mounts,
    KernelRow.mounts,
    KernelRow.resource_opts,
    KernelRow.image,
    KernelRow.cluster_mode,
)


def _parse_query(
    kernel_cond: Optional[sa.sql.BinaryExpression] = None,
    session_cond: Optional[sa.sql.BinaryExpression] = None,
    project_cond: Optional[sa.sql.BinaryExpression] = None,
) -> sa.sql.Select:
    session_load = joinedload(KernelRow.session)
    if session_cond is not None:
        session_load = joinedload(KernelRow.session.and_(session_cond))

    project_load = joinedload(SessionRow.group)
    if project_cond is not None:
        project_load = joinedload(SessionRow.group.and_(project_cond))
    query = sa.select(KernelRow).options(
        load_only(*KERNEL_RESOURCE_SELECT_COLS),
        session_load.options(
            load_only(*SESSION_RESOURCE_SELECT_COLS),
            joinedload(SessionRow.user).options(
                load_only(UserRow.email, UserRow.username, UserRow.full_name)
            ),
            project_load.options(load_only(*PROJECT_RESOURCE_SELECT_COLS)),
        ),
    )
    if kernel_cond is not None:
        query = query.where(kernel_cond)
    return query


async def fetch_resource_usage(
    db_engine: ExtendedAsyncSAEngine,
    start_date: datetime,
    end_date: datetime,
    session_ids: Optional[Sequence[UUID]] = None,
    project_ids: Optional[Sequence[UUID]] = None,
) -> list[KernelRow]:
    project_cond = None
    if project_ids:
        project_cond = GroupRow.id.in_(project_ids)
    session_cond = None
    if session_ids:
        session_cond = SessionRow.id.in_(session_ids)
    query = _parse_query(
        kernel_cond=(
            # Filter sessions which existence period overlaps with requested period
            (
                (KernelRow.terminated_at >= start_date)
                & (KernelRow.created_at < end_date)
                & (KernelRow.status.in_(RESOURCE_USAGE_KERNEL_STATUSES))
            )
            |
            # Or, filter running sessions which created before requested end_date
            ((KernelRow.created_at < end_date) & (KernelRow.status.in_(LIVE_STATUS)))
        ),
        session_cond=session_cond,
        project_cond=project_cond,
    )
    async with db_engine.begin_readonly_session() as db_sess:
        result = await db_sess.execute(query)
        kernels = result.scalars().all()

    return kernels

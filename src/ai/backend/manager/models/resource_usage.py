from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence
from uuid import UUID

import attr
import msgpack
from dateutil.tz.tz import tzfile
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline as RedisPipeline

from ai.backend.common import redis_helper
from ai.backend.common.types import RedisConnectionInfo
from ai.backend.common.utils import nmget

if TYPE_CHECKING:
    from .kernel import KernelRow

__all__: Sequence[str] = (
    "ResourceGroupUnit",
    "ResourceUsage",
    "ResourceUsageGroup",
    "parse_resource_usage",
    "parse_resource_usage_groups",
)


class ResourceGroupUnit(str, Enum):
    CONTAINER = "container"
    SESSION = "session"
    PROJECT = "project"
    DOMAIN = "domain"


@attr.define(slots=True)
class ResourceUsage:
    # kernel_id: UUID
    # container_id: str

    # created_at: datetime
    # terminated_at: Optional[datetime]
    # used_time: Optional[str]
    # used_days: Optional[int]
    # last_stat: Optional[Mapping[str, Any]]

    nfs: set = attr.field(factory=set)
    cpu_allocated: float = attr.field(default=0.0)
    cpu_used: float = attr.field(default=0.0)
    mem_allocated: int = attr.field(default=0)
    mem_used: int = attr.field(default=0)
    shared_memory: int = attr.field(default=0)
    disk_allocated: int = attr.field(default=0)  # TODO: disk quota limit
    disk_used: int = attr.field(default=0)
    io_read: int = attr.field(default=0)
    io_write: int = attr.field(default=0)
    device_type: set = attr.field(factory=set)
    smp: float = attr.field(default=0.0)
    gpu_mem_allocated: float = attr.field(default=0.0)
    gpu_allocated: float = attr.field(default=0.0)

    agent_ids: set = attr.field(factory=set)

    def __add__(self, other: Any) -> ResourceUsage:
        if not isinstance(other, ResourceUsage):
            raise ValueError(
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
            # "kernel_id": str(self.kernel_id),
            # "container_id": self.container_id,
            # "created_at": self.created_at,
            # "terminated_at": self.terminated_at,
            # "used_time": self.used_time,
            # "used_days": self.used_days,
            # "last_stat": self.last_stat,
            "nfs": self.nfs,
            "cpu_allocated": self.cpu_allocated,
            "cpu_used": self.cpu_used,
            "mem_allocated": self.mem_allocated,
            "mem_used": self.mem_used,
            "shared_memory": self.shared_memory,
            "disk_allocated": self.disk_allocated,
            "disk_used": self.disk_used,
            "io_read": self.io_read,
            "io_write": self.io_write,
            "device_type": self.device_type,
            "smp": self.smp,
            "gpu_mem_allocated": self.gpu_mem_allocated,
            "gpu_allocated": self.gpu_allocated,
        }


@attr.define(slots=True)
class ResourceUsageGroup:
    group_unit: ResourceGroupUnit
    created_at: datetime
    terminated_at: Optional[datetime] = attr.field(default=None)
    used_time: Optional[str] = attr.field(default=None)
    used_days: Optional[int] = attr.field(default=None)

    user_id: Optional[UUID] = attr.field(default=None)
    user_email: Optional[str] = attr.field(default=None)
    access_key: Optional[UUID] = attr.field(default=None)
    project_id: Optional[UUID] = attr.field(default=None)
    project_name: Optional[str] = attr.field(default=None)
    kernel_id: Optional[UUID] = attr.field(default=None)
    container_id: Optional[UUID] = attr.field(default=None)
    session_id: Optional[UUID] = attr.field(default=None)
    session_name: Optional[str] = attr.field(default=None)
    domain_name: Optional[str] = attr.field(default=None)

    last_stat: Optional[Mapping[str, Any]] = attr.field(default=None)
    belonged_usage_groups: list[ResourceUsageGroup] = attr.field(factory=list)
    total_usage: ResourceUsage = attr.field(factory=ResourceUsage)

    def to_json(self) -> dict[str, Any]:
        # belonged_infos = defaultdict(list)
        # for g in self.belonged_usage_groups:
        #     belonged_infos[f"{g.group_unit.value}_infos"].append(g.to_json())
        return {
            "user_id": self.user_id,
            "user_email": self.user_email,
            "access_key": self.access_key,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "group_id": self.project_id,  # legacy
            "group_name": self.project_name,  # legacy
            "kernel_id": self.kernel_id,
            "container_id": self.container_id,
            "session_id": self.session_id,
            "session_name": self.session_name,
            "domain_name": self.domain_name,
            "agents": self.total_usage.agent_ids,
            "group_unit": self.group_unit.value,
            "total_usage": self.total_usage.to_json(),
            # **belonged_infos,
        }

    def validate_hierarchy(self, other: ResourceUsageGroup) -> bool:
        match self.group_unit:
            case ResourceGroupUnit.CONTAINER:
                pass
            case ResourceGroupUnit.SESSION:
                pass
            case ResourceGroupUnit.PROJECT:
                pass
            case ResourceGroupUnit.DOMAIN:
                pass
        return True

    def register_resource_group(
        self, others: list[ResourceUsageGroup], *, strict: bool = False
    ) -> ResourceUsageGroup:
        for g in others:
            if strict:
                if not self.validate_hierarchy(g):
                    continue
            self.total_usage += g.total_usage
            self.belonged_usage_groups.append(g)
        return self


def parse_resource_usage(
    kernel: KernelRow,
    last_stat: Optional[Mapping[str, Any]],
) -> ResourceUsage:
    if not last_stat:
        return ResourceUsage()
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
        nfs=nfs,
        cpu_allocated=float(kernel.occupied_slots.get("cpu", 0)),
        cpu_used=float(nmget(last_stat, "cpu_used.current", 0)),
        mem_allocated=int(kernel.occupied_slots.get("mem", 0)),
        mem_used=int(nmget(last_stat, "mem.capacity", 0)),
        shared_memory=int(nmget(kernel.resource_opts, "shmem", 0)),
        disk_allocated=0,
        disk_used=int(nmget(last_stat, "io_scratch_size/stats.max", 0, "/")),
        io_read=int(nmget(last_stat, "io_read.current", 0)),
        io_write=int(nmget(last_stat, "io_write.current", 0)),
        device_type=device_type,
        smp=float(smp),
        gpu_mem_allocated=float(gpu_mem_allocated),
        gpu_allocated=float(gpu_allocated),
    )


async def parse_resource_usage_groups(
    kernels: list[KernelRow],
    redis_stat: RedisConnectionInfo,
    local_tz: tzfile,
) -> list[ResourceUsageGroup]:
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
        ResourceUsageGroup(
            created_at=kern.created_at,
            terminated_at=kern.terminated_at,
            used_time=kern.used_time,
            used_days=kern.get_used_days(local_tz),
            last_stat=stat_map[kern.id],
            user_id=kern.session.user_uuid,
            user_email=kern.session.user.email,
            access_key=kern.session.access_key,
            project_id=kern.session.group_id,
            project_name=kern.session.group.name,
            kernel_id=kern.id,
            container_id=kern.container_id,
            session_id=kern.session_id,
            session_name=kern.session.name,
            domain_name=kern.session.domain_name,
            group_unit=ResourceGroupUnit.CONTAINER,
            total_usage=parse_resource_usage(kern, stat_map[kern.id]),
        )
        for kern in kernels
    ]

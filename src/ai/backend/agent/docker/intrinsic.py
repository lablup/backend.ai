import asyncio
import logging
import os
import platform
from concurrent.futures import ProcessPoolExecutor
from decimal import Decimal
from pathlib import Path
from typing import Any, Collection, Dict, List, Mapping, Optional, Sequence, Tuple, cast

import aiohttp
import async_timeout
import psutil
from aiodocker.docker import Docker, DockerContainer
from aiodocker.exceptions import DockerError

from ai.backend.agent.types import MountInfo
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.netns import nsenter
from ai.backend.common.types import (
    AcceleratorMetadata,
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    MetricKey,
    SlotName,
    SlotTypes,
)
from ai.backend.common.utils import current_loop, nmget

from .. import __version__  # pants: no-infer-dep
from ..alloc_map import AllocationStrategy
from ..resources import (
    AbstractAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
)
from ..stats import (
    ContainerMeasurement,
    Measurement,
    MetricTypes,
    NodeMeasurement,
    ProcessMeasurement,
    StatContext,
    StatModes,
)
from ..utils import closing_async, read_sysfs
from ..vendor.linux import libnuma
from .agent import Container
from .resources import get_resource_spec_from_container

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


# The list of pruned fstype when checking the filesystem usage statistics.
# Note that psutil's linux implementation automatically filters out "non-device" filesystems by
# checking /proc/filesystems so we don't have to put all the details virtual filesystems like
# "sockfs", "debugfs", etc.
pruned_disk_types = frozenset([
    "vfat",
    "lxcfs",
    "squashfs",
    "tmpfs",
    "iso9660",  # cdrom
])


def netstat_ns_work(ns_path: Path):
    with nsenter(ns_path):
        result = psutil.net_io_counters(pernic=True)
    return result


async def netstat_ns(ns_path: Path):
    loop = asyncio.get_running_loop()
    # Linux namespace is per-thread state. Therefore we need to ensure
    # IO is executed in the same thread where we switched the namespace.
    # Go provides runtime.LockOSThread() to do this.
    #
    # Unfortunately, CPython drops GIL while running IO and does not
    # provide any similar functionality. Therefore we execute namespace
    # dependent operation in the new process.
    with ProcessPoolExecutor(max_workers=1) as executor:
        result = await loop.run_in_executor(executor, netstat_ns_work, ns_path)
    return result


async def fetch_api_stats(container: DockerContainer) -> Optional[Dict[str, Any]]:
    short_cid = container._id[:7]
    try:
        ret = await container.stats(stream=False)  # TODO: cache
    except RuntimeError as e:
        msg = str(e.args[0]).lower()
        if "event loop is closed" in msg or "session is closed" in msg:
            return None
        raise
    except (DockerError, aiohttp.ClientError) as e:
        log.error(
            "cannot read stats (cid:{}): client error: {!r}.",
            short_cid,
            e,
        )
        return None
    else:
        entry = {"read": "0001-01-01"}
        # aiodocker 0.16 or later returns a list of dict, even when not streaming.
        match ret:
            case list() if ret:
                entry = ret[0]
            case dict() if ret:
                entry = ret
            case _:
                # The API may return an empty result upon container termination.
                log.warning(
                    "cannot read stats (cid:{}): got an empty result: {}",
                    short_cid,
                    ret,
                )
                return None
        if entry["read"].startswith("0001-01-01") or entry["preread"].startswith("0001-01-01"):
            return None
        return entry


# Pseudo-plugins for intrinsic devices (CPU and the main memory)


class CPUDevice(AbstractComputeDevice):
    pass


class CPUPlugin(AbstractComputePlugin):
    """
    Represents the CPU.
    """

    config_watch_enabled = False

    key = DeviceName("cpu")
    slot_types = [
        (SlotName("cpu"), SlotTypes.COUNT),
    ]

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    async def list_devices(self) -> Collection[CPUDevice]:
        cores = await libnuma.get_available_cores()
        overcommit_factor = int(os.environ.get("BACKEND_CPU_OVERCOMMIT_FACTOR", "1"))
        assert 1 <= overcommit_factor <= 10
        return [
            CPUDevice(
                device_id=DeviceId(str(core_idx)),
                hw_location="root",
                numa_node=libnuma.node_of_cpu(core_idx),
                memory_size=0,
                processing_units=1 * overcommit_factor,
            )
            for core_idx in sorted(cores)
        ]

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName("cpu"): Decimal(sum(dev.processing_units for dev in devices)),
        }

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, str]:
        return {
            "agent_version": __version__,
            "machine": platform.machine(),
            "os_type": platform.system(),
        }

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        _cstat = psutil.cpu_times(True)
        q = Decimal("0.000")
        total_cpu_used = cast(
            Decimal, sum((Decimal(c.user + c.system) * 1000).quantize(q) for c in _cstat)
        )
        now, raw_interval = ctx.update_timestamp("cpu-node")
        interval = Decimal(raw_interval * 1000).quantize(q)

        return [
            NodeMeasurement(
                MetricKey("cpu_util"),
                MetricTypes.UTILIZATION,
                unit_hint="msec",
                current_hook=lambda metric: metric.stats.diff,
                per_node=Measurement(total_cpu_used, interval),
                per_device={
                    DeviceId(str(idx)): Measurement(
                        (Decimal(c.user + c.system) * 1000).quantize(q),
                        interval,
                    )
                    for idx, c in enumerate(_cstat)
                },
            ),
        ]

    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        async def sysfs_impl(container_id):
            cpu_path = ctx.agent.get_cgroup_path("cpuacct", container_id)
            version = ctx.agent.docker_info["CgroupVersion"]
            try:
                match version:
                    case "1":
                        cpu_used = read_sysfs(cpu_path / "cpuacct.usage", int) / 1e6
                    case "2":
                        cpu_stats = {
                            k: v
                            for k, v in map(
                                lambda line: line.split(" "),
                                (cpu_path / "cpu.stat").read_text().splitlines(),
                            )
                        }
                        cpu_used = int(cpu_stats["usage_usec"]) / 1e3
            except IOError as e:
                log.warning(
                    "CPUPlugin: cannot read stats: sysfs unreadable for container {0}\n{1!r}",
                    container_id[:7],
                    e,
                )
                return None
            return cpu_used

        async def api_impl(container_id):
            async with closing_async(Docker()) as docker:
                container = DockerContainer(docker, id=container_id)
                try:
                    async with async_timeout.timeout(2.0):
                        ret = await fetch_api_stats(container)
                except asyncio.TimeoutError:
                    return None
                if ret is None:
                    return None
                cpu_used = nmget(ret, "cpu_stats.cpu_usage.total_usage", 0) / 1e6
                return cpu_used

        if ctx.mode == StatModes.CGROUP:
            impl = sysfs_impl
        elif ctx.mode == StatModes.DOCKER:
            impl = api_impl
        else:
            raise RuntimeError("should not reach here")

        q = Decimal("0.000")
        per_container_cpu_used = {}
        per_container_cpu_util = {}
        tasks = []
        for cid in container_ids:
            tasks.append(asyncio.create_task(impl(cid)))
        results = await asyncio.gather(*tasks)
        for cid, cpu_used in zip(container_ids, results):
            if cpu_used is None:
                continue
            per_container_cpu_used[cid] = Measurement(Decimal(cpu_used).quantize(q))
            per_container_cpu_util[cid] = Measurement(
                Decimal(cpu_used).quantize(q),
                capacity=Decimal(1000),
            )
        return [
            ContainerMeasurement(
                MetricKey("cpu_util"),
                MetricTypes.UTILIZATION,
                unit_hint="percent",
                current_hook=lambda metric: metric.stats.rate,
                stats_filter=frozenset({"avg", "max"}),
                per_container=per_container_cpu_util,
            ),
            ContainerMeasurement(
                MetricKey("cpu_used"),
                MetricTypes.ACCUMULATION,
                unit_hint="msec",
                per_container=per_container_cpu_used,
            ),
        ]

    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        async def psutil_impl(pid: int) -> Optional[Decimal]:
            try:
                p = psutil.Process(pid)
            except psutil.NoSuchProcess:
                log.warning("psutil cannot found process {0}", pid)
            else:
                cpu_times = p.cpu_times()
                cpu_used = Decimal(cpu_times.user + cpu_times.system) * 1000
                return cpu_used
            return None

        async def api_impl(cid: str, pids: List[int]) -> List[Optional[Decimal]]:
            return []

        per_process_cpu_util = {}
        per_process_cpu_used = {}
        results: List[Decimal | None] = []
        q = Decimal("0.000")
        pid_map_list = list(pid_map.items())
        match self.local_config["agent"]["docker-mode"]:
            case "linuxkit":
                api_tasks: list[asyncio.Task[list[Decimal | None]]] = []
                # group by container ID
                cid_pids_map: Dict[str, List[int]] = {}
                for pid, cid in pid_map_list:
                    if cid_pids_map.get(cid) is None:
                        cid_pids_map[cid] = []
                    cid_pids_map[cid].append(pid)
                for cid, pids in cid_pids_map.items():
                    api_tasks.append(asyncio.create_task(api_impl(cid, pids)))
                chunked_results = await asyncio.gather(*api_tasks)
                for chunk in chunked_results:
                    results.extend(chunk)
            case _:
                psutil_tasks = []
                for pid, _ in pid_map_list:
                    psutil_tasks.append(asyncio.create_task(psutil_impl(pid)))
                results = await asyncio.gather(*psutil_tasks)

        for (pid, cid), cpu_used in zip(pid_map_list, results):
            if cpu_used is None:
                continue
            per_process_cpu_util[pid] = Measurement(
                Decimal(cpu_used).quantize(q), capacity=Decimal(1000)
            )
            per_process_cpu_used[pid] = Measurement(Decimal(cpu_used).quantize(q))
        return [
            ProcessMeasurement(
                MetricKey("cpu_util"),
                MetricTypes.UTILIZATION,
                unit_hint="percent",
                current_hook=lambda metric: metric.stats.rate,
                stats_filter=frozenset({"avg", "max"}),
                per_process=per_process_cpu_util,
            ),
            ProcessMeasurement(
                MetricKey("cpu_used"),
                MetricTypes.ACCUMULATION,
                unit_hint="msec",
                per_process=per_process_cpu_used,
            ),
        ]

    async def create_alloc_map(self) -> AbstractAllocMap:
        devices = await self.list_devices()
        return DiscretePropertyAllocMap(
            device_slots={
                dev.device_id: DeviceSlotInfo(
                    SlotTypes.COUNT, SlotName("cpu"), Decimal(dev.processing_units)
                )
                for dev in devices
            },
        )

    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        # TODO: move the sysconf hook in libbaihook.so here
        return []

    async def generate_docker_args(
        self,
        docker: Docker,
        device_alloc,
    ) -> Mapping[str, Any]:
        cores = [*map(int, device_alloc["cpu"].keys())]
        sorted_core_ids = [*map(str, sorted(cores))]
        return {
            "HostConfig": {
                "Cpus": len(cores),
                "CpusetCpus": ",".join(sorted_core_ids),
                # 'CpusetMems': f'{resource_spec.numa_node}',
            },
        }

    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        assert isinstance(alloc_map, DiscretePropertyAllocMap)
        # Docker does not return the original cpuset.... :(
        # We need to read our own records.
        resource_spec = await get_resource_spec_from_container(container.backend_obj)
        if resource_spec is None:
            return
        alloc_map.apply_allocation({
            SlotName("cpu"): resource_spec.allocations[DeviceName("cpu")][SlotName("cpu")],
        })

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids = [*device_alloc[SlotName("cpu")].keys()]
        available_devices = await self.list_devices()
        attached_devices: List[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                attached_devices.append({
                    "device_id": device.device_id,
                    "model_name": "",
                    "data": {"cores": len(device_ids)},
                })
        return attached_devices

    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[str]:
        return []

    async def generate_mounts(
        self, source_path: Path, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[MountInfo]:
        return []

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "cpu",
            "description": "CPU",
            "human_readable_name": "CPU",
            "display_unit": "Core",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "cpu",
        }


class MemoryDevice(AbstractComputeDevice):
    pass


class MemoryPlugin(AbstractComputePlugin):
    """
    Represents the main memory.

    When collecting statistics, it also measures network and I/O usage
    in addition to the memory usage.
    """

    config_watch_enabled = False

    key = DeviceName("mem")
    slot_types = [
        (SlotName("mem"), SlotTypes.BYTES),
    ]

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    async def list_devices(self) -> Collection[MemoryDevice]:
        memory_size = psutil.virtual_memory().total
        overcommit_factor = int(os.environ.get("BACKEND_MEM_OVERCOMMIT_FACTOR", "1"))
        return [
            MemoryDevice(
                device_id=DeviceId("root"),
                device_name=self.key,
                hw_location="root",
                numa_node=0,  # the kernel setting will do the job.
                memory_size=overcommit_factor * memory_size,
                processing_units=0,
            ),
        ]

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName("mem"): Decimal(sum(dev.memory_size for dev in devices)),
        }

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, str]:
        return {}

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        _mstat = psutil.virtual_memory()
        total_mem_used_bytes = Decimal(_mstat.total - _mstat.available)
        total_mem_capacity_bytes = Decimal(_mstat.total)
        _nstat = psutil.net_io_counters()
        net_rx_bytes = _nstat.bytes_recv
        net_tx_bytes = _nstat.bytes_sent

        def get_disk_stat():
            total_disk_usage = Decimal(0)
            total_disk_capacity = Decimal(0)
            per_disk_stat = {}
            for disk_info in psutil.disk_partitions():
                # Skip additional filesystem types not filtered by psutil, like squashfs.
                if disk_info.fstype in pruned_disk_types:
                    continue
                # Skip transient filesystems created/destroyed by Docker.
                if disk_info.mountpoint.startswith("/proc/docker/runtime-runc/moby/"):
                    continue
                # Skip btrfs subvolumes used by Docker if configured.
                if disk_info.mountpoint == "/var/lib/docker/btrfs":
                    continue
                dstat = os.statvfs(disk_info.mountpoint)
                disk_usage = Decimal(dstat.f_frsize * (dstat.f_blocks - dstat.f_bavail))
                disk_capacity = Decimal(dstat.f_frsize * dstat.f_blocks)
                per_disk_stat[disk_info.device] = Measurement(disk_usage, disk_capacity)
                total_disk_usage += disk_usage
                total_disk_capacity += disk_capacity
            return total_disk_usage, total_disk_capacity, per_disk_stat

        loop = current_loop()
        total_disk_usage, total_disk_capacity, per_disk_stat = await loop.run_in_executor(
            None, get_disk_stat
        )
        return [
            NodeMeasurement(
                MetricKey("mem"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_node=Measurement(total_mem_used_bytes, total_mem_capacity_bytes),
                per_device={
                    DeviceId("root"): Measurement(total_mem_used_bytes, total_mem_capacity_bytes)
                },
            ),
            NodeMeasurement(
                MetricKey("disk"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                per_node=Measurement(total_disk_usage, total_disk_capacity),
                per_device=per_disk_stat,
            ),
            NodeMeasurement(
                MetricKey("net_rx"),
                MetricTypes.RATE,
                unit_hint="bps",
                current_hook=lambda metric: metric.stats.rate,
                per_node=Measurement(Decimal(net_rx_bytes)),
                per_device={DeviceId("node"): Measurement(Decimal(net_rx_bytes))},
            ),
            NodeMeasurement(
                MetricKey("net_tx"),
                MetricTypes.RATE,
                unit_hint="bps",
                current_hook=lambda metric: metric.stats.rate,
                per_node=Measurement(Decimal(net_tx_bytes)),
                per_device={DeviceId("node"): Measurement(Decimal(net_tx_bytes))},
            ),
        ]

    async def gather_container_measures(
        self, ctx: StatContext, container_ids: Sequence[str]
    ) -> Sequence[ContainerMeasurement]:
        def get_scratch_size(container_id: str) -> int:
            # Temporarily disabled as this function incurs too much delay with
            # a large number of files in scratch dirs, causing indefinite accumulation of
            # stat collector tasks and slowing down everything.
            return 0
            # for kernel_id, info in ctx.agent.kernel_registry.items():
            #     if info['container_id'] == container_id:
            #         break
            # else:
            #     return 0
            # work_dir = ctx.agent.local_config['container']['scratch-root'] / str(kernel_id) / 'work'
            # total_size = 0
            # for path in work_dir.rglob('*'):
            #     if path.is_symlink():
            #         total_size += path.lstat().st_size
            #     elif path.is_file():
            #         total_size += path.stat().st_size
            # return total_size

        async def sysfs_impl(container_id):
            mem_path = ctx.agent.get_cgroup_path("memory", container_id)
            io_path = ctx.agent.get_cgroup_path("blkio", container_id)
            version = ctx.agent.docker_info["CgroupVersion"]

            try:
                io_read_bytes = 0
                io_write_bytes = 0
                match version:
                    case "1":
                        mem_cur_bytes = read_sysfs(mem_path / "memory.usage_in_bytes", int)
                        mem_max_bytes = read_sysfs(mem_path / "memory.limit_in_bytes", int)

                        for line in (mem_path / "memory.stat").read_text().splitlines():
                            key, value = line.split(" ")
                            if key == "total_inactive_file":
                                mem_cur_bytes -= int(value)
                                break

                        # example data:
                        #   8:0 Read 13918208
                        #   8:0 Write 0
                        #   8:0 Sync 0
                        #   8:0 Async 13918208
                        #   8:0 Total 13918208
                        #   Total 13918208
                        for line in (
                            (io_path / "blkio.throttle.io_service_bytes").read_text().splitlines()
                        ):
                            if line.startswith("Total "):
                                continue
                            dev, op, nbytes = line.strip().split()
                            if op == "Read":
                                io_read_bytes += int(nbytes)
                            elif op == "Write":
                                io_write_bytes += int(nbytes)
                    case "2":
                        mem_cur_bytes = read_sysfs(mem_path / "memory.current", int)
                        mem_max_bytes = read_sysfs(mem_path / "memory.max", int)

                        for line in (mem_path / "memory.stat").read_text().splitlines():
                            key, value = line.split(" ")
                            if key == "inactive_file":
                                mem_cur_bytes -= int(value)
                                break

                        # example data:
                        # 8:16 rbytes=1459200 wbytes=314773504 rios=192 wios=353 dbytes=0 dios=0
                        # 8:0 rbytes=3387392 wbytes=176128 rios=103 wios=32 dbytes=0 dios=0
                        for line in (io_path / "io.stat").read_text().splitlines():
                            for io_stat in line.split()[1:]:
                                stat, value = io_stat.split("=")
                                if stat == "rbytes":
                                    io_read_bytes += int(value)
                                if stat == "wbytes":
                                    io_write_bytes += int(value)
            except IOError as e:
                log.warning(
                    "MemoryPlugin: cannot read stats: sysfs unreadable for container {0}\n{1!r}",
                    container_id[:7],
                    e,
                )
                return None
            async with closing_async(Docker()) as docker:
                container = DockerContainer(docker, id=container_id)
                data = await container.show()
                sandbox_key = data["NetworkSettings"]["SandboxKey"]
            net_rx_bytes = 0
            net_tx_bytes = 0
            nstat = await netstat_ns(sandbox_key)
            for name, stat in nstat.items():
                if name == "lo":
                    continue
                net_rx_bytes += stat.bytes_recv
                net_tx_bytes += stat.bytes_sent
            loop = current_loop()
            scratch_sz = await loop.run_in_executor(None, get_scratch_size, container_id)
            return (
                mem_cur_bytes,
                mem_max_bytes,
                io_read_bytes,
                io_write_bytes,
                net_rx_bytes,
                net_tx_bytes,
                scratch_sz,
            )

        async def api_impl(container_id):
            async with closing_async(Docker()) as docker:
                container = DockerContainer(docker, id=container_id)
                try:
                    async with async_timeout.timeout(2.0):
                        ret = await fetch_api_stats(container)
                except asyncio.TimeoutError:
                    return None
                if ret is None:
                    return None
                mem_cur_bytes = nmget(ret, "memory_stats.usage", 0)
                mem_total_bytes = nmget(ret, "memory_stats.limit", 0)
                io_read_bytes = 0
                io_write_bytes = 0
                for item in nmget(ret, "blkio_stats.io_service_bytes_recursive", []):
                    if item["op"] == "Read":
                        io_read_bytes += item["value"]
                    elif item["op"] == "Write":
                        io_write_bytes += item["value"]
                net_rx_bytes = 0
                net_tx_bytes = 0
                for name, stat in ret["networks"].items():
                    net_rx_bytes += stat["rx_bytes"]
                    net_tx_bytes += stat["tx_bytes"]
                loop = current_loop()
                scratch_sz = await loop.run_in_executor(None, get_scratch_size, container_id)
                return (
                    mem_cur_bytes,
                    mem_total_bytes,
                    io_read_bytes,
                    io_write_bytes,
                    net_rx_bytes,
                    net_tx_bytes,
                    scratch_sz,
                )

        if ctx.mode == StatModes.CGROUP:
            impl = sysfs_impl
        elif ctx.mode == StatModes.DOCKER:
            impl = api_impl
        else:
            raise RuntimeError("should not reach here")

        per_container_mem_used_bytes = {}
        per_container_io_read_bytes = {}
        per_container_io_write_bytes = {}
        per_container_net_rx_bytes = {}
        per_container_net_tx_bytes = {}
        per_container_io_scratch_size = {}
        tasks = []
        for cid in container_ids:
            tasks.append(asyncio.create_task(impl(cid)))
        results = await asyncio.gather(*tasks)
        for cid, result in zip(container_ids, results):
            if result is None:
                continue
            per_container_mem_used_bytes[cid] = Measurement(
                Decimal(result[0]), capacity=Decimal(result[1])
            )
            per_container_io_read_bytes[cid] = Measurement(Decimal(result[2]))
            per_container_io_write_bytes[cid] = Measurement(Decimal(result[3]))
            per_container_net_rx_bytes[cid] = Measurement(Decimal(result[4]))
            per_container_net_tx_bytes[cid] = Measurement(Decimal(result[5]))
            per_container_io_scratch_size[cid] = Measurement(Decimal(result[6]))
        return [
            ContainerMeasurement(
                MetricKey("mem"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_container=per_container_mem_used_bytes,
            ),
            ContainerMeasurement(
                MetricKey("io_read"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"rate"}),
                per_container=per_container_io_read_bytes,
            ),
            ContainerMeasurement(
                MetricKey("io_write"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"rate"}),
                per_container=per_container_io_write_bytes,
            ),
            ContainerMeasurement(
                MetricKey("net_rx"),
                MetricTypes.RATE,
                unit_hint="bps",
                current_hook=lambda metric: metric.stats.rate,
                per_container=per_container_net_rx_bytes,
            ),
            ContainerMeasurement(
                MetricKey("net_tx"),
                MetricTypes.RATE,
                unit_hint="bps",
                current_hook=lambda metric: metric.stats.rate,
                per_container=per_container_net_tx_bytes,
            ),
            ContainerMeasurement(
                MetricKey("io_scratch_size"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_container=per_container_io_scratch_size,
            ),
        ]

    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        async def psutil_impl(pid) -> Tuple[Optional[int], Optional[int], Optional[int]]:
            try:
                p = psutil.Process(pid)
            except psutil.NoSuchProcess:
                log.warning("psutil cannot found process {0}", pid)
            else:
                stats = p.as_dict(attrs=["memory_info", "io_counters"])
                mem_cur_bytes = io_read_bytes = io_write_bytes = None
                if stats["memory_info"] is not None:
                    mem_cur_bytes = stats["memory_info"].rss
                if stats["io_counters"] is not None:
                    io_read_bytes = stats["io_counters"].read_bytes
                    io_write_bytes = stats["io_counters"].write_bytes
                return mem_cur_bytes, io_read_bytes, io_write_bytes
            return None, None, None

        async def api_impl(
            cid: str, pids: List[int]
        ) -> List[Tuple[Optional[int], Optional[int], Optional[int]]]:
            return []

        per_process_mem_used_bytes = {}
        per_process_io_read_bytes = {}
        per_process_io_write_bytes = {}
        results: List[Tuple[Optional[int], Optional[int], Optional[int]]]
        pid_map_list = list(pid_map.items())
        match self.local_config["agent"]["docker-mode"]:
            case "linuxkit":
                api_tasks = []
                # group by container ID
                cid_pids_map: Dict[str, List[int]] = {}
                for pid, cid in pid_map_list:
                    if cid_pids_map.get(cid) is None:
                        cid_pids_map[cid] = []
                    cid_pids_map[cid].append(pid)
                for cid, pids in cid_pids_map.items():
                    api_tasks.append(asyncio.create_task(api_impl(cid, pids)))
                chunked_results = await asyncio.gather(*api_tasks)
                results = []
                for chunk in chunked_results:
                    results.extend(chunk)
            case _:
                psutil_tasks = []
                for pid, _ in pid_map_list:
                    psutil_tasks.append(asyncio.create_task(psutil_impl(pid)))
                results = await asyncio.gather(*psutil_tasks)

        for (pid, _), result in zip(pid_map_list, results):
            mem, io_read, io_write = result
            if mem is not None:
                per_process_mem_used_bytes[pid] = Measurement(Decimal(mem))
            if io_read is not None:
                per_process_io_read_bytes[pid] = Measurement(Decimal(io_read))
            if io_write is not None:
                per_process_io_write_bytes[pid] = Measurement(Decimal(io_write))
        return [
            ProcessMeasurement(
                MetricKey("mem"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_process=per_process_mem_used_bytes,
            ),
            ProcessMeasurement(
                MetricKey("io_read"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"rate"}),
                per_process=per_process_io_read_bytes,
            ),
            ProcessMeasurement(
                MetricKey("io_write"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"rate"}),
                per_process=per_process_io_write_bytes,
            ),
        ]

    async def create_alloc_map(self) -> AbstractAllocMap:
        devices = await self.list_devices()
        return DiscretePropertyAllocMap(
            allocation_strategy=AllocationStrategy.FILL,
            device_slots={
                dev.device_id: DeviceSlotInfo(
                    SlotTypes.BYTES, SlotName("mem"), Decimal(dev.memory_size)
                )
                for dev in devices
            },
        )

    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    async def generate_docker_args(
        self,
        docker: Docker,
        device_alloc,
    ) -> Mapping[str, Any]:
        memory = sum(device_alloc["mem"].values())
        return {
            "HostConfig": {
                "MemorySwap": int(memory),  # prevent using swap!
                "Memory": int(memory),
            },
        }

    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        assert isinstance(alloc_map, DiscretePropertyAllocMap)
        memory_limit = container.backend_obj["HostConfig"]["Memory"]
        alloc_map.apply_allocation({
            SlotName("mem"): {DeviceId("root"): memory_limit},
        })

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids = [*device_alloc[SlotName("mem")].keys()]
        available_devices = await self.list_devices()
        attached_devices: List[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                attached_devices.append({
                    "device_id": device.device_id,
                    "model_name": "",
                    "data": {},
                })
        return attached_devices

    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[str]:
        return []

    async def generate_mounts(
        self, source_path: Path, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[MountInfo]:
        return []

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "ram",
            "description": "Memory",
            "human_readable_name": "RAM",
            "display_unit": "GiB",
            "number_format": {"binary": True, "round_length": 0},
            "display_icon": "ram",
        }

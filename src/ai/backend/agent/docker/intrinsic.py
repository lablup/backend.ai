import asyncio
from decimal import Decimal
import logging
import os
from pathlib import Path
import platform
from typing import (
    cast,
    Any,
    Collection,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
)

import aiohttp
from aiodocker.docker import Docker, DockerContainer
from aiodocker.exceptions import DockerError
import async_timeout
import psutil

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.utils import current_loop, nmget
from ai.backend.common.types import (
    DeviceName, DeviceId,
    DeviceModelInfo,
    SlotName, SlotTypes,
    MetricKey,
)
from .agent import Container
from .resources import (
    get_resource_spec_from_container,
)
from .. import __version__
from ..resources import (
    AbstractAllocMap, DeviceSlotInfo,
    DiscretePropertyAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
)
from ..stats import (
    StatContext, NodeMeasurement, ContainerMeasurement,
    StatModes, MetricTypes, Measurement,
)
from ..utils import closing_async, read_sysfs
from ..vendor.linux import libnuma

log = BraceStyleAdapter(logging.getLogger(__name__))


async def fetch_api_stats(container: DockerContainer) -> Optional[Dict[str, Any]]:
    short_cid = container._id[:7]
    try:
        ret = await container.stats(stream=False)  # TODO: cache
    except RuntimeError as e:
        msg = str(e.args[0]).lower()
        if 'event loop is closed' in msg or 'session is closed' in msg:
            return None
        raise
    except (DockerError, aiohttp.ClientError) as e:
        log.error(
            'cannot read stats (cid:{}): client error: {!r}.',
            short_cid, e,
        )
        return None
    else:
        # aiodocker 0.16 or later returns a list of dict, even when not streaming.
        if isinstance(ret, list):
            if not ret:
                # The API may return an empty result upon container termination.
                return None
            ret = ret[0]
        # The API may return an invalid or empty result upon container termination.
        if ret is None or not isinstance(ret, dict):
            log.warning(
                'cannot read stats (cid:{}): got an empty result: {}',
                short_cid, ret,
            )
            return None
        if (
            ret['read'].startswith('0001-01-01') or
            ret['preread'].startswith('0001-01-01')
        ):
            return None
        return ret


# Pseudo-plugins for intrinsic devices (CPU and the main memory)

class CPUDevice(AbstractComputeDevice):
    pass


class CPUPlugin(AbstractComputePlugin):
    """
    Represents the CPU.
    """

    config_watch_enabled = False

    key = DeviceName('cpu')
    slot_types = [
        (SlotName('cpu'), SlotTypes.COUNT),
    ]

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    async def list_devices(self) -> Collection[CPUDevice]:
        cores = await libnuma.get_available_cores()
        overcommit_factor = int(os.environ.get('BACKEND_CPU_OVERCOMMIT_FACTOR', '1'))
        assert 1 <= overcommit_factor <= 10
        return [
            CPUDevice(
                device_id=DeviceId(str(core_idx)),
                hw_location='root',
                numa_node=libnuma.node_of_cpu(core_idx),
                memory_size=0,
                processing_units=1 * overcommit_factor,
            )
            for core_idx in sorted(cores)
        ]

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName('cpu'): Decimal(sum(dev.processing_units for dev in devices)),
        }

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, str]:
        return {
            'agent_version': __version__,
            'machine': platform.machine(),
            'os_type': platform.system(),
        }

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        _cstat = psutil.cpu_times(True)
        q = Decimal('0.000')
        total_cpu_used = cast(Decimal,
                              sum((Decimal(c.user + c.system) * 1000).quantize(q) for c in _cstat))
        now, raw_interval = ctx.update_timestamp('cpu-node')
        interval = Decimal(raw_interval * 1000).quantize(q)

        return [
            NodeMeasurement(
                MetricKey('cpu_util'),
                MetricTypes.UTILIZATION,
                unit_hint='msec',
                current_hook=lambda metric: metric.stats.diff,
                per_node=Measurement(total_cpu_used, interval),
                per_device={
                    DeviceId(str(idx)):
                    Measurement(
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
            cpu_prefix = f'/sys/fs/cgroup/cpuacct/docker/{container_id}/'
            try:
                cpu_used = read_sysfs(cpu_prefix + 'cpuacct.usage', int) / 1e6
            except IOError as e:
                log.warning('cannot read stats: sysfs unreadable for container {0}\n{1!r}',
                            container_id[:7], e)
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
                cpu_used = nmget(ret, 'cpu_stats.cpu_usage.total_usage', 0) / 1e6
                return cpu_used

        if ctx.mode == StatModes.CGROUP:
            impl = sysfs_impl
        elif ctx.mode == StatModes.DOCKER:
            impl = api_impl
        else:
            raise RuntimeError("should not reach here")

        q = Decimal('0.000')
        per_container_cpu_used = {}
        per_container_cpu_util = {}
        tasks = []
        for cid in container_ids:
            tasks.append(asyncio.ensure_future(impl(cid)))
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
                MetricKey('cpu_util'),
                MetricTypes.UTILIZATION,
                unit_hint='percent',
                current_hook=lambda metric: metric.stats.rate,
                stats_filter=frozenset({'avg', 'max'}),
                per_container=per_container_cpu_util,
            ),
            ContainerMeasurement(
                MetricKey('cpu_used'),
                MetricTypes.USAGE,
                unit_hint='msec',
                per_container=per_container_cpu_used,
            ),
        ]

    async def create_alloc_map(self) -> AbstractAllocMap:
        devices = await self.list_devices()
        return DiscretePropertyAllocMap(
            device_slots={
                dev.device_id:
                    DeviceSlotInfo(SlotTypes.COUNT, SlotName('cpu'), Decimal(dev.processing_units))
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
        cores = [*map(int, device_alloc['cpu'].keys())]
        sorted_core_ids = [*map(str, sorted(cores))]
        return {
            'HostConfig': {
                'CpuPeriod': 100_000,  # docker default
                'CpuQuota': int(100_000 * len(cores)),
                'Cpus': ','.join(sorted_core_ids),
                'CpusetCpus': ','.join(sorted_core_ids),
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
            SlotName('cpu'):
                resource_spec.allocations[DeviceName('cpu')][SlotName('cpu')],
        })

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName,
        Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids = [*device_alloc[SlotName('cpu')].keys()]
        available_devices = await self.list_devices()
        attached_devices: List[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                attached_devices.append({
                    'device_id': device.device_id,
                    'model_name': '',
                    'data': {'cores': len(device_ids)},
                })
        return attached_devices


class MemoryDevice(AbstractComputeDevice):
    pass


class MemoryPlugin(AbstractComputePlugin):
    """
    Represents the main memory.

    When collecting statistics, it also measures network and I/O usage
    in addition to the memory usage.
    """

    config_watch_enabled = False

    key = DeviceName('mem')
    slot_types = [
        (SlotName('mem'), SlotTypes.BYTES),
    ]

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    async def list_devices(self) -> Collection[MemoryDevice]:
        # TODO: support NUMA?
        memory_size = psutil.virtual_memory().total
        overcommit_factor = int(os.environ.get('BACKEND_MEM_OVERCOMMIT_FACTOR', '1'))
        return [MemoryDevice(
            device_id=DeviceId('root'),
            hw_location='root',
            numa_node=0,
            memory_size=overcommit_factor * memory_size,
            processing_units=0,
        )]

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName('mem'): Decimal(sum(dev.memory_size for dev in devices)),
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
            pruned_disk_types = frozenset(['squashfs', 'vfat', 'tmpfs'])
            total_disk_usage = Decimal(0)
            total_disk_capacity = Decimal(0)
            per_disk_stat = {}
            for disk_info in psutil.disk_partitions():
                if disk_info.fstype not in pruned_disk_types:
                    dstat = os.statvfs(disk_info.mountpoint)
                    disk_usage = Decimal(dstat.f_frsize * (dstat.f_blocks - dstat.f_bavail))
                    disk_capacity = Decimal(dstat.f_frsize * dstat.f_blocks)
                    per_disk_stat[disk_info.device] = Measurement(disk_usage, disk_capacity)
                    total_disk_usage += disk_usage
                    total_disk_capacity += disk_capacity
            return total_disk_usage, total_disk_capacity, per_disk_stat

        loop = current_loop()
        total_disk_usage, total_disk_capacity, per_disk_stat = \
            await loop.run_in_executor(None, get_disk_stat)
        return [
            NodeMeasurement(
                MetricKey('mem'),
                MetricTypes.USAGE,
                unit_hint='bytes',
                stats_filter=frozenset({'max'}),
                per_node=Measurement(total_mem_used_bytes, total_mem_capacity_bytes),
                per_device={DeviceId('root'):
                            Measurement(total_mem_used_bytes,
                                        total_mem_capacity_bytes)},
            ),
            NodeMeasurement(
                MetricKey('disk'),
                MetricTypes.USAGE,
                unit_hint='bytes',
                per_node=Measurement(total_disk_usage, total_disk_capacity),
                per_device=per_disk_stat,
            ),
            NodeMeasurement(
                MetricKey('net_rx'),
                MetricTypes.RATE,
                unit_hint='bps',
                current_hook=lambda metric: metric.stats.rate,
                per_node=Measurement(Decimal(net_rx_bytes)),
                per_device={DeviceId('node'): Measurement(Decimal(net_rx_bytes))},
            ),
            NodeMeasurement(
                MetricKey('net_tx'),
                MetricTypes.RATE,
                unit_hint='bps',
                current_hook=lambda metric: metric.stats.rate,
                per_node=Measurement(Decimal(net_tx_bytes)),
                per_device={DeviceId('node'): Measurement(Decimal(net_tx_bytes))},
            ),
        ]

    async def gather_container_measures(self, ctx: StatContext, container_ids: Sequence[str]) \
            -> Sequence[ContainerMeasurement]:

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
            mem_prefix = f'/sys/fs/cgroup/memory/docker/{container_id}/'
            io_prefix = f'/sys/fs/cgroup/blkio/docker/{container_id}/'
            try:
                mem_cur_bytes = read_sysfs(mem_prefix + 'memory.usage_in_bytes', int)
                io_stats = Path(io_prefix + 'blkio.throttle.io_service_bytes').read_text()
                # example data:
                #   8:0 Read 13918208
                #   8:0 Write 0
                #   8:0 Sync 0
                #   8:0 Async 13918208
                #   8:0 Total 13918208
                #   Total 13918208
                io_read_bytes = 0
                io_write_bytes = 0
                for line in io_stats.splitlines():
                    if line.startswith('Total '):
                        continue
                    dev, op, nbytes = line.strip().split()
                    if op == 'Read':
                        io_read_bytes += int(nbytes)
                    elif op == 'Write':
                        io_write_bytes += int(nbytes)
            except IOError as e:
                log.warning('cannot read stats: sysfs unreadable for container {0}\n{1!r}',
                            container_id[:7], e)
                return None
            loop = current_loop()
            scratch_sz = await loop.run_in_executor(
                None, get_scratch_size, container_id)
            return mem_cur_bytes, io_read_bytes, io_write_bytes, scratch_sz

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
                mem_cur_bytes = nmget(ret, 'memory_stats.usage', 0)
                io_read_bytes = 0
                io_write_bytes = 0
                for item in nmget(ret, 'blkio_stats.io_service_bytes_recursive', []):
                    if item['op'] == 'Read':
                        io_read_bytes += item['value']
                    elif item['op'] == 'Write':
                        io_write_bytes += item['value']
                loop = current_loop()
                scratch_sz = await loop.run_in_executor(
                    None, get_scratch_size, container_id)
                return mem_cur_bytes, io_read_bytes, io_write_bytes, scratch_sz

        if ctx.mode == StatModes.CGROUP:
            impl = sysfs_impl
        elif ctx.mode == StatModes.DOCKER:
            impl = api_impl
        else:
            raise RuntimeError("should not reach here")

        per_container_mem_used_bytes = {}
        per_container_io_read_bytes = {}
        per_container_io_write_bytes = {}
        per_container_io_scratch_size = {}
        tasks = []
        for cid in container_ids:
            tasks.append(asyncio.ensure_future(impl(cid)))
        results = await asyncio.gather(*tasks)
        for cid, result in zip(container_ids, results):
            if result is None:
                continue
            per_container_mem_used_bytes[cid] = Measurement(
                Decimal(result[0]))
            per_container_io_read_bytes[cid] = Measurement(
                Decimal(result[1]))
            per_container_io_write_bytes[cid] = Measurement(
                Decimal(result[2]))
            per_container_io_scratch_size[cid] = Measurement(
                Decimal(result[3]))
        return [
            ContainerMeasurement(
                MetricKey('mem'),
                MetricTypes.USAGE,
                unit_hint='bytes',
                stats_filter=frozenset({'max'}),
                per_container=per_container_mem_used_bytes,
            ),
            ContainerMeasurement(
                MetricKey('io_read'),
                MetricTypes.USAGE,
                unit_hint='bytes',
                stats_filter=frozenset({'rate'}),
                per_container=per_container_io_read_bytes,
            ),
            ContainerMeasurement(
                MetricKey('io_write'),
                MetricTypes.USAGE,
                unit_hint='bytes',
                stats_filter=frozenset({'rate'}),
                per_container=per_container_io_write_bytes,
            ),
            ContainerMeasurement(
                MetricKey('io_scratch_size'),
                MetricTypes.USAGE,
                unit_hint='bytes',
                stats_filter=frozenset({'max'}),
                per_container=per_container_io_scratch_size,
            ),
        ]

    async def create_alloc_map(self) -> AbstractAllocMap:
        devices = await self.list_devices()
        return DiscretePropertyAllocMap(
            device_slots={
                dev.device_id:
                    DeviceSlotInfo(SlotTypes.BYTES, SlotName('mem'), Decimal(dev.memory_size))
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
        memory = sum(device_alloc['mem'].values())
        return {
            'HostConfig': {
                'MemorySwap': int(memory),  # prevent using swap!
                'Memory': int(memory),
            },
        }

    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        assert isinstance(alloc_map, DiscretePropertyAllocMap)
        memory_limit = container.backend_obj['HostConfig']['Memory']
        alloc_map.apply_allocation({
            SlotName('mem'): {DeviceId('root'): memory_limit},
        })

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids = [*device_alloc[SlotName('mem')].keys()]
        available_devices = await self.list_devices()
        attached_devices: List[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                attached_devices.append({
                    'device_id': device.device_id,
                    'model_name': '',
                    'data': {},
                })
        return attached_devices

import asyncio
import logging
import os
import platform
from decimal import Decimal
from pathlib import Path
from typing import Any, Collection, Dict, List, Mapping, Optional, Sequence, cast

import aiohttp
from aiodocker.docker import Docker, DockerContainer
from aiodocker.exceptions import DockerError
from kubernetes_asyncio import client as K8sClient
from kubernetes_asyncio import config as K8sConfig
from kubernetes_asyncio.client.rest import ApiException as K8sApiException

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    MetricKey,
    SlotName,
    SlotTypes,
)
from ai.backend.common.utils import current_loop

from .. import __version__
from ..alloc_map import AllocationStrategy
from ..resources import (
    AbstractAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
    MountInfo,
)
from ..stats import ContainerMeasurement, Measurement, MetricTypes, NodeMeasurement, StatContext
from .agent import Container
from .resources import get_resource_spec_from_container

log = BraceStyleAdapter(logging.getLogger(__name__))


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
        # aiodocker 0.16 or later returns a list of dict, even when not streaming.
        if isinstance(ret, list):
            if not ret:
                # The API may return an empty result upon container termination.
                return None
            ret = ret[0]
        # The API may return an invalid or empty result upon container termination.
        if ret is None or not isinstance(ret, dict):
            log.warning(
                "cannot read stats (cid:{}): got an empty result: {}",
                short_cid,
                ret,
            )
            return None
        if ret["read"].startswith("0001-01-01") or ret["preread"].startswith("0001-01-01"):
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
        await K8sConfig.load_kube_config()
        core_api = K8sClient.CoreV1Api()

        nodes = (await core_api.list_node()).to_dict()["items"]
        overcommit_factor = int(os.environ.get("BACKEND_CPU_OVERCOMMIT_FACTOR", "1"))
        assert 1 <= overcommit_factor <= 10

        return [
            CPUDevice(
                device_id=DeviceId(node["metadata"]["uid"]),
                hw_location="root",
                numa_node=None,
                memory_size=0,
                processing_units=int(node["status"]["capacity"]["cpu"]) * overcommit_factor,
            )
            for i, node in zip(range(len(nodes)), nodes)
            # if 'node-role.kubernetes.io/master' not in node['metadata']['labels'].keys()
        ]

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        log.debug("available_slots: {}", devices)
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
        async def get_cpu_stat(core_api, name: str):
            try:
                raw_resp = await core_api.connect_get_node_proxy_with_path(
                    name=name, path="metrics/resource"
                )
            except K8sApiException as e:
                log.warning("kubernetes api error: {}", e)
                return None
            resp = [line for line in raw_resp.split("\n") if "#" not in line and "node_cpu" in line]
            cpu_used = resp.pop().split(" ")[1]
            return cpu_used

        await K8sConfig.load_kube_config()
        core_api = K8sClient.CoreV1Api()
        nodes = (await core_api.list_node()).to_dict()["items"]
        node_names = [node["metadata"]["name"] for node in nodes]
        tasks = []
        for name in node_names:
            tasks.append(asyncio.ensure_future(get_cpu_stat(core_api, name)))
        total_cpu_used = Decimal(0)
        q = Decimal(0.000)
        results = await asyncio.gather(*tasks)
        for cpu_used in results:
            if cpu_used is None:
                continue
            total_cpu_used += (Decimal(cpu_used) * 1000).quantize(q)
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
                    DeviceId(node["metadata"]["uid"]): Measurement(
                        (Decimal(cpu_used) * 1000).quantize(q),
                        interval,
                    )
                    for node, cpu_used in zip(nodes, results)
                    if cpu_used
                },
            ),
        ]

    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        # TODO: Implement Kubernetes-specific container metric collection

        return []

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
        # This function might be needed later to apply fine-grained tuning for
        # K8s resource allocation
        return {}

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
        alloc_map.apply_allocation(
            {
                SlotName("cpu"): resource_spec.allocations[DeviceName("cpu")][SlotName("cpu")],
            }
        )

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids = [*device_alloc[SlotName("cpu")].keys()]
        available_devices = await self.list_devices()
        attached_devices: List[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                attached_devices.append(
                    {
                        "device_id": device.device_id,
                        "model_name": "",
                        "data": {"cores": len(device_ids)},
                    }
                )
        return attached_devices

    async def generate_mounts(
        self, source_path: Path, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[MountInfo]:
        return []

    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[str]:
        return []


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
        await K8sConfig.load_kube_config()
        core_api = K8sClient.CoreV1Api()

        nodes = (await core_api.list_node()).to_dict()["items"]
        overcommit_factor = int(os.environ.get("BACKEND_MEM_OVERCOMMIT_FACTOR", "1"))
        assert 1 <= overcommit_factor <= 10
        mem = 0
        for node in nodes:
            # if 'node-role.kubernetes.io/master' in node['metadata']['labels'].keys():
            #     continue
            mem += int(node["status"]["capacity"]["memory"][:-2]) * 1024
        return [
            MemoryDevice(
                device_id=DeviceId("root"),
                device_name=self.key,
                hw_location="root",
                numa_node=0,
                memory_size=mem * overcommit_factor,
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
        async def get_memory_stat(core_api, name: str):
            try:
                raw_resp = await core_api.connect_get_node_proxy_with_path(
                    name=name, path="metrics/resource"
                )
            except K8sApiException as e:
                log.warning("kubernetes api error: {}", e)
                return None
            resp = [line for line in raw_resp.split("\n") if "#" not in line and "node_mem" in line]
            mem_used = resp.pop().split(" ")[1]
            return mem_used

        async def get_network_stat(core_api, name: str):
            try:
                raw_resp = await core_api.connect_get_node_proxy_with_path(
                    name=name, path="metrics/cadvisor"
                )
            except K8sApiException as e:
                log.warning("kubernetes api error: {}", e)
                return None
            for line in raw_resp.split("\n"):
                if "#" in line:
                    continue
                if "container_network_receive_bytes" in line:
                    net_rx = line.split(" ")[1]
                elif "container_network_transmit_bytes" in line:
                    net_tx = line.split(" ")[1]
            return net_rx, net_tx

        await K8sConfig.load_kube_config()
        core_api = K8sClient.CoreV1Api()
        nodes = (await core_api.list_node()).to_dict()["items"]
        node_names = [node["metadata"]["name"] for node in nodes]
        _mem_tasks = []
        _net_tasks = []
        q = Decimal(0.000)
        for name in node_names:
            _mem_tasks.append(asyncio.ensure_future(get_memory_stat(core_api, name)))
            _net_tasks.append(asyncio.ensure_future(get_network_stat(core_api, name)))
        mem_results = await asyncio.gather(*_mem_tasks)
        net_results = await asyncio.gather(*_net_tasks)
        total_mem_used_bytes = Decimal(0)
        net_rx_bytes = Decimal(0)
        net_tx_bytes = Decimal(0)
        for mem_used in mem_results:
            if mem_used is None:
                continue
            total_mem_used_bytes += Decimal(mem_used).quantize(q)
        for result in net_results:
            if result is None:
                continue
            net_rx_bytes += Decimal(result[0]).quantize(q)
            net_tx_bytes += Decimal(result[1]).quantize(q)
        total_mem_capacity_bytes = cast(
            Decimal,
            sum(
                (Decimal(node["status"]["capacity"]["memory"][:-2]) * 1024).quantize(q)
                for node in nodes
            ),
        )

        def get_disk_stat(nodes):
            total_disk_capacity = Decimal(0)
            total_disk_usage = Decimal(0)
            per_disk_stat = {}
            q = Decimal(0.000)
            for node in nodes:
                disk_capacity = node["status"]["capacity"]["ephemeral-storage"]
                disk_allocatable = node["status"]["allocatable"]["ephemeral-storage"]
                if disk_capacity.isdigit():
                    disk_capacity = Decimal(disk_capacity).quantize(q)
                else:
                    disk_capacity = (Decimal(disk_capacity[:-2]) * 1024).quantize(q)
                if disk_allocatable.isdigit():
                    disk_usage = disk_capacity - (Decimal(disk_allocatable)).quantize(q)
                else:
                    disk_usage = disk_capacity - (Decimal(disk_allocatable[:-2]) * 1024).quantize(q)
                per_disk_stat[node["metadata"]["uid"]] = Measurement(disk_usage, disk_capacity)
                total_disk_capacity += disk_capacity
                total_disk_usage += disk_usage
            return total_disk_usage, total_disk_capacity, per_disk_stat

        loop = current_loop()
        total_disk_usage, total_disk_capacity, per_disk_stat = await loop.run_in_executor(
            None, get_disk_stat, nodes
        )
        return [
            NodeMeasurement(
                MetricKey("mem"),
                MetricTypes.USAGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_node=Measurement(total_mem_used_bytes, total_mem_capacity_bytes),
                per_device={
                    DeviceId("root"): Measurement(total_mem_used_bytes, total_mem_capacity_bytes)
                },
            ),
            NodeMeasurement(
                MetricKey("disk"),
                MetricTypes.USAGE,
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
        # TODO: Implement Kubernetes-specific container metric collection
        return []

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
        # This function might be needed later to apply fine-grained tuning for
        # K8s resource allocation
        return {}

    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        assert isinstance(alloc_map, DiscretePropertyAllocMap)
        memory_limit = container.backend_obj["HostConfig"]["Memory"]
        alloc_map.apply_allocation(
            {
                SlotName("mem"): {DeviceId("root"): memory_limit},
            }
        )

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids = [*device_alloc[SlotName("mem")].keys()]
        available_devices = await self.list_devices()
        attached_devices: List[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                attached_devices.append(
                    {
                        "device_id": device.device_id,
                        "model_name": "",
                        "data": {},
                    }
                )
        return attached_devices

    async def generate_mounts(
        self, source_path: Path, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[MountInfo]:
        return []

    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[str]:
        return []

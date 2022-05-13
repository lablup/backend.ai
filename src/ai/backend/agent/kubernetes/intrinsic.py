from decimal import Decimal
import logging
import os
from pathlib import Path
import platform
from typing import (
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
from kubernetes_asyncio import client as K8sClient, config as K8sConfig

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    DeviceName, DeviceId,
    DeviceModelInfo,
    SlotName, SlotTypes,
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
)

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
        await K8sConfig.load_kube_config()
        core_api = K8sClient.CoreV1Api()

        nodes = (await core_api.list_node()).to_dict()['items']
        overcommit_factor = int(os.environ.get('BACKEND_CPU_OVERCOMMIT_FACTOR', '1'))
        assert 1 <= overcommit_factor <= 10

        return [
            CPUDevice(
                device_id=DeviceId(node['metadata']['uid']),
                hw_location='root',
                numa_node=None,
                memory_size=0,
                processing_units=int(node['status']['capacity']['cpu']) * overcommit_factor,
            )
            for i, node in zip(range(len(nodes)), nodes)
            # if 'node-role.kubernetes.io/master' not in node['metadata']['labels'].keys()
        ]

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        log.debug('available_slots: {}', devices)
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
        # TODO: Create our own k8s metric collector

        return []

    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        # TODO: Implement Kubernetes-specific container metric collection

        return [
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
        await K8sConfig.load_kube_config()
        core_api = K8sClient.CoreV1Api()

        nodes = (await core_api.list_node()).to_dict()['items']
        overcommit_factor = int(os.environ.get('BACKEND_MEM_OVERCOMMIT_FACTOR', '1'))
        assert 1 <= overcommit_factor <= 10
        mem = 0
        for node in nodes:
            # if 'node-role.kubernetes.io/master' in node['metadata']['labels'].keys():
            #     continue
            mem += int(node['status']['capacity']['memory'][:-2]) * 1024
        return [
            MemoryDevice(
                device_id=DeviceId('root'),
                hw_location='root',
                numa_node=0,
                memory_size=mem * overcommit_factor,
                processing_units=0,
            ),
        ]

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
        # TODO: Create our own k8s metric collector
        return []

    async def gather_container_measures(self, ctx: StatContext, container_ids: Sequence[str]) \
            -> Sequence[ContainerMeasurement]:
        # TODO: Implement Kubernetes-specific container metric collection
        return []

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
        # This function might be needed later to apply fine-grained tuning for
        # K8s resource allocation
        return {}

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

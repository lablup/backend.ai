import logging
from abc import ABCMeta, abstractmethod
from decimal import Decimal
from pathlib import Path
from pprint import pformat
from typing import (
    Any,
    Collection,
    Dict,
    Generic,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
)

import aiodocker
import pyhlml
import trafaret as t

from ai.backend.agent.resources import (
    AbstractAllocMap,
    AbstractComputePlugin,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
)

from . import __version__
from .types import AbstractGaudiDevice

try:
    from ai.backend.agent.resources import get_resource_spec_from_container  # type: ignore
except ImportError:
    from ai.backend.agent.docker.resources import get_resource_spec_from_container
from ai.backend.agent.stats import (
    ContainerMeasurement,
    Measurement,
    MetricTypes,
    NodeMeasurement,
    ProcessMeasurement,
    StatContext,
)
from ai.backend.agent.types import Container, MountInfo
from ai.backend.common import config
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    AcceleratorMetadata,
    BinarySize,
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    MetricKey,
    SlotName,
    SlotTypes,
)

__all__ = (
    "PREFIX",
    "AbstractGaudiPlugin",
)

PREFIX = "gaudi2"

_config_iv = t.Dict({
    "docker-networks": t.List(t.String),
}).allow_extra("*")


log = BraceStyleAdapter(logging.getLogger("ai.backend.accelerator.habana.gaudi2"))


TDevice = TypeVar("TDevice", bound=AbstractGaudiDevice)


class AbstractGaudiPlugin(AbstractComputePlugin, Generic[TDevice], metaclass=ABCMeta):
    config_watch_enabled = False

    key = DeviceName("gaudi")
    slot_types: Sequence[Tuple[SlotName, SlotTypes]] = (
        (SlotName("gaudi.device"), SlotTypes("count")),
    )
    exclusive_slot_types: Set[str] = {"gaudi.device"}

    device_mask: Sequence[DeviceId] = []
    enabled: bool = True

    gaudi_config: Mapping[str, Any]

    _all_devices: Optional[List[TDevice]]

    _driver_version: str

    subnet_network_map: Mapping[str, Any]

    async def init(self, context: Any = None) -> None:
        self._all_devices = None

        raw_device_mask = self.local_config.get("device_mask")
        if raw_device_mask is not None:
            self.device_mask = [
                *map(lambda dev_id: DeviceId(dev_id), raw_device_mask.split(",")),
            ]

        raw_cfg, cfg_src_path = config.read_from_file(None, "gaudi2")
        self.gaudi_config = _config_iv.check(raw_cfg)
        log.info("Read Gaudi device configs from {}", cfg_src_path)

        try:
            pyhlml.hlmlInit()
            self._driver_version = pyhlml.hlmlGetDriverVersion().decode()
            log.info("Running on Habana Driver {}", self._driver_version)
            detected_devices = await self.list_devices()
            log.info("detected devices:\n" + pformat(detected_devices))
            await self.prepare_networks()
            log.info("Gaudi acceleration is enabled.")
        except RuntimeError as e:
            log.warning("Gaudi init error: {}", e)
            log.info("Gaudi acceleration is disabled.")
            self.enabled = False

    @abstractmethod
    async def list_devices(self) -> Collection[TDevice]:
        raise NotImplementedError

    async def prepare_networks(self) -> None:
        self.subnet_network_map = {}
        docker_network_identifiers = self.gaudi_config["docker-networks"]
        network_map: Dict[str, Any] = {}
        async with aiodocker.Docker() as docker:
            networks = await docker.networks.list()
            for network in networks:
                network_map[network["Name"]] = network
                network_map[network["Id"]] = network

        for network_identifier in docker_network_identifiers:
            network_config = network_map.get(network_identifier)
            if not network_config:
                raise RuntimeError(f"Network {network_identifier} not found")

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            self.slot_types[0][0]: Decimal(len(devices)),
        }

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, Any]:
        if self.enabled:
            return {
                "gaudi_support": True,
                "driver_version": self._driver_version,
            }
        return {
            "gaudi_support": False,
        }

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        dev_count = 0
        mem_avail_total = 0
        mem_used_total = 0
        mem_stats = {}
        util_total = 0
        util_stats = {}
        if self.enabled:
            try:
                for device in await self.list_devices():
                    dev_idx = device.dev_idx
                    if dev_idx in self.device_mask:
                        continue

                    dev_count += 1
                    handle = pyhlml.hlmlDeviceGetHandleByIndex(dev_idx)
                    mem_info = pyhlml.hlmlDeviceGetMemoryInfo(handle)
                    gpu_util = pyhlml.hlmlDeviceGetUtilizationRates(handle).aip

                    mem_total = mem_info.total
                    mem_used = mem_info.used
                    mem_avail_total += int(mem_total)
                    mem_used_total += int(mem_used)
                    mem_stats[device.device_id] = Measurement(Decimal(mem_used), Decimal(mem_total))
                    util_total += gpu_util
                    util_stats[device.device_id] = Measurement(Decimal(gpu_util), Decimal(100))
            except RuntimeError as e:
                # libhip is not installed.
                # Return an empty result.
                log.exception(e)
                self.enabled = False
        return [
            NodeMeasurement(
                MetricKey(f"{self.key}_mem"),
                MetricTypes.USAGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_node=Measurement(Decimal(mem_used_total), Decimal(mem_avail_total)),
                per_device=mem_stats,
            ),
            NodeMeasurement(
                MetricKey(f"{self.key}_util"),
                MetricTypes.USAGE,
                unit_hint="percent",
                stats_filter=frozenset({"avg", "max"}),
                per_node=Measurement(Decimal(util_total), Decimal(dev_count * 100)),
                per_device=util_stats,
            ),
        ]

    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        mem_stats: Dict[str, int] = {}
        mem_sizes: Dict[str, int] = {}
        util_stats: Dict[str, Decimal] = {}
        number_of_devices_per_container: Dict[str, int] = {}
        device_stats_by_device_filename: Dict[str, Dict[str, Any]] = {}
        if self.enabled:
            try:
                for device in await self.list_devices():
                    dev_idx = device.dev_idx
                    if dev_idx in self.device_mask:
                        continue

                    handle = pyhlml.hlmlDeviceGetHandleByIndex(dev_idx)
                    mem_info = pyhlml.hlmlDeviceGetMemoryInfo(handle)
                    gpu_util = pyhlml.hlmlDeviceGetUtilizationRates(handle).aip

                    device_stats_by_device_filename[f"/dev/accel/accel{dev_idx}"] = {
                        "util": gpu_util,
                        "mem_used": mem_info.used,
                        "mem_total": mem_info.total,
                    }
            except RuntimeError as e:
                # libhip is not installed.
                # Return an empty result.
                log.exception(e)
                self.enabled = False
                return []

            for cid in container_ids:
                mem_stats[cid] = 0
                mem_sizes[cid] = 0
                util_stats[cid] = Decimal("0")
                number_of_devices_per_container[cid] = 0
                async with aiodocker.Docker() as docker:
                    container_info = await docker.containers.get(cid)
                for device in container_info["HostConfig"]["Devices"]:
                    if device["PathOnHost"] in device_stats_by_device_filename:
                        device_stat = device_stats_by_device_filename[device["PathOnHost"]]
                        mem_stats[cid] += int(device_stat["mem_used"])
                        mem_sizes[cid] += int(device_stat["mem_total"])
                        util_stats[cid] += Decimal(device_stat["util"])
                        number_of_devices_per_container[cid] += 1

        return [
            ContainerMeasurement(
                MetricKey(f"{self.key}_mem"),
                MetricTypes.USAGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_container={
                    cid: Measurement(
                        Decimal(usage),
                        Decimal(mem_sizes[cid]),
                    )
                    for cid, usage in mem_stats.items()
                },
            ),
            ContainerMeasurement(
                MetricKey(f"{self.key}_util"),
                MetricTypes.USAGE,
                unit_hint="percent",
                stats_filter=frozenset({"avg", "max"}),
                per_container={
                    cid: Measurement(
                        util,
                        Decimal(number_of_devices_per_container[cid] * 100),
                    )
                    for cid, util in util_stats.items()
                },
            ),
        ]

    async def create_alloc_map(self) -> AbstractAllocMap:
        devices = await self.list_devices()
        return DiscretePropertyAllocMap(
            device_slots={
                dev.device_id: (DeviceSlotInfo(SlotTypes.COUNT, self.slot_types[0][0], Decimal(1)))
                for dev in devices
            },
            exclusive_slot_types=self.exclusive_slot_types,
        )

    async def generate_mounts(
        self,
        source_path: Path,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> List[MountInfo]:
        return []

    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    async def generate_docker_args(
        self,
        docker: aiodocker.Docker,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, Any]:
        assigned_devices: List[str] = []
        for idx, dev in enumerate(await self.list_devices()):
            if dev.device_id in device_alloc.get(self.slot_types[0][0], {}).keys():
                assigned_devices.append(f"/dev/accel/accel{idx}")
                assigned_devices.append(f"/dev/accel/accel_controlD{idx}")

        if len(assigned_devices) == 0:
            return {}

        return {
            "HostConfig": {
                "Devices": [
                    {
                        "PathOnHost": dev,
                        "PathInContainer": dev,
                        "CgroupPermissions": "rwm",
                    }
                    for dev in assigned_devices
                ],
                "Ipc": "host",
            },
        }

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids: List[DeviceId] = []
        if self.slot_types[0][0] in device_alloc:
            device_ids.extend(device_alloc[self.slot_types[0][0]].keys())
        available_devices = await self.list_devices()
        attached_devices: List[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                proc = device.processing_units
                mem = BinarySize(device.memory_size)
                attached_devices.append({  # TODO: update common.types.DeviceModelInfo
                    "device_id": device.device_id,
                    "model_name": device.model_name,
                    "data": {
                        "smp": proc,
                        "mem": mem,
                    },
                })
        return attached_devices

    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        if not self.enabled:
            return
        resource_spec = await get_resource_spec_from_container(container.backend_obj)
        if resource_spec is None:
            return
        if hasattr(alloc_map, "apply_allocation"):
            for slot_name, _ in self.slot_types:
                alloc_map.apply_allocation({
                    slot_name: resource_spec.allocations.get(
                        self.key,
                        {},
                    ).get(
                        slot_name,
                        {
                            dev_id: Decimal(0)
                            for dev_id, dev_slot_info in alloc_map.device_slots.items()
                            if dev_slot_info.slot_name == slot_name
                        },
                    ),
                })
        else:  # older agents without lablup/backend.ai-agent#180
            alloc_map.allocations[self.slot_types[0][0]].update(
                resource_spec.allocations.get(
                    self.key,
                    {},
                ).get(
                    self.slot_types[0][0],
                    {},
                ),
            )

    async def generate_resource_data(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, str]:
        data: MutableMapping[str, str] = {}
        if not self.enabled:
            return data

        active_device_id_set: Set[DeviceId] = set()
        for slot_type, per_device_alloc in device_alloc.items():
            for dev_id, alloc in per_device_alloc.items():
                if alloc > 0:
                    active_device_id_set.add(dev_id)
        active_device_ids = sorted(active_device_id_set, key=lambda v: int(v))
        data["HABANA_GLOBAL_DEVICE_IDS"] = ",".join(
            f"{local_idx}:{global_id}" for local_idx, global_id in enumerate(active_device_ids)
        )
        return data

    async def cleanup(self) -> None:
        pyhlml.hlmlShutdown()

    async def list_additional_gids(self) -> List[int]:
        return [44, 109]

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    async def get_docker_networks(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> List[str]:
        return self.gaudi_config["docker-networks"]

    async def gather_process_measures(
        self,
        ctx: StatContext,
        pid_map: Mapping[int, str],
    ) -> Sequence[ProcessMeasurement]:
        return []

    @abstractmethod
    def get_metadata(self) -> AcceleratorMetadata:
        raise NotImplementedError

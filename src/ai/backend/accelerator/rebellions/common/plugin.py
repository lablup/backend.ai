import logging
import shutil
from abc import ABCMeta, abstractmethod
from decimal import Decimal
from pathlib import Path
from pprint import pformat
from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
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
import trafaret as t
from aiodocker import Docker

from .. import __version__
from .atom_api import ATOMAPI, ATOMDeviceStat, LibraryError
from .types import AbstractATOMDevice

try:
    from ai.backend.agent.resources import get_resource_spec_from_container  # type: ignore
except ImportError:
    from ai.backend.agent.docker.resources import get_resource_spec_from_container

from ai.backend.agent.resources import (
    AbstractAllocMap,
    AbstractComputePlugin,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
)
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
from ai.backend.common.types import (
    AcceleratorMetadata,
    BinarySize,
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    MetricKey,
    MountTypes,
    SlotName,
    SlotTypes,
)
from ai.backend.logging import BraceStyleAdapter

_atom_config_iv = t.Dict({
    "general": t.Dict({
        t.Key("rbln_stat_path"): t.Null | t.String,
        t.Key("enforce_singular_numa_affinity", default=False): t.Null | t.Bool,
    }).allow_extra("*"),
}).allow_extra("*")

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


TATOMDevice = TypeVar("TATOMDevice", bound=AbstractATOMDevice)


class AbstractATOMPlugin(AbstractComputePlugin, Generic[TATOMDevice], metaclass=ABCMeta):
    key = DeviceName("atom")
    slot_types: Sequence[Tuple[SlotName, SlotTypes]] = (
        (SlotName("atom.device"), SlotTypes("count")),
    )
    exclusive_slot_types: Set[str] = {"atom.device"}

    device_mask: Sequence[DeviceId] = []
    enabled: bool = True
    atom_config: Any

    _rbln_stat_path: str
    _all_devices: Optional[List[TATOMDevice]]

    async def init(self, context: Any = None) -> None:
        self._all_devices = None

        raw_device_mask = self.plugin_config.get("device_mask")
        if raw_device_mask is not None:
            self.device_mask = [
                *map(lambda dev_id: DeviceId(dev_id), raw_device_mask.split(",")),
            ]

        raw_cfg, cfg_src_path = config.read_from_file(None, "atom")
        self.atom_config = _atom_config_iv.check(raw_cfg)
        log.info("Read {} device configs from {}", self.key, cfg_src_path)
        _rbln_stat_path = self.atom_config["general"]["rbln_stat_path"] or shutil.which("rbln-stat")
        if _rbln_stat_path is None:
            log.error("Could not find path to rbln-stat executable.")
            log.info("{} acceleration is disabled.")
            self.enabled = False
            return
        self._rbln_stat_path = _rbln_stat_path
        try:
            detected_devices = await self.list_devices()
            log.info("detected devices:\n" + pformat(detected_devices))
            log.info("{} acceleration is enabled.", self.key)
        except ImportError:
            log.warning("could not find {} devices with VID 1eff.", self.key)
            self.enabled = False

    async def list_devices(self) -> List[TATOMDevice]:
        if self._all_devices is None:
            devices = await self._list_devices()
            self._all_devices = devices
            return devices
        else:
            return self._all_devices

    @abstractmethod
    async def _list_devices(self) -> List[TATOMDevice]:
        raise NotImplementedError

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        log.debug("available devices: {}", Decimal(len(devices)))
        return {
            self.slot_types[0][0]: Decimal(len(devices)),
        }

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, Any]:
        if self.enabled:
            return {
                "atom_support": True,
            }
        return {}

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        dev_count = 0
        mem_avail_total = 0
        mem_used_total = 0
        mem_stats = {}
        util_total = 0.0
        util_stats = {}

        stat_prefix = self.key.replace("-", "_")

        stats = await ATOMAPI.get_stats(self._rbln_stat_path)
        if self.enabled:
            for device in await self.list_devices():
                device_id = device.device_id
                pci_bus_id = device.hw_location
                try:
                    stat = [x for x in stats.devices if x.pci.bus_id == pci_bus_id].pop()
                except IndexError:
                    continue

                mem_avail_total += int(stat.memory.total)
                mem_used_total += int(stat.memory.used)
                mem_stats[device_id] = Measurement(
                    Decimal(int(stat.memory.used)),
                    Decimal(int(stat.memory.total)),
                )
                util_total += float(stat.util)
                util_stats[device_id] = Measurement(Decimal(float(stat.util)), Decimal(100))
                dev_count += 1
        return [
            NodeMeasurement(
                MetricKey(f"{stat_prefix}_mem"),
                MetricTypes.USAGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_node=Measurement(Decimal(mem_used_total), Decimal(mem_avail_total)),
                per_device=mem_stats,
            ),
            NodeMeasurement(
                MetricKey(f"{stat_prefix}_util"),
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
        stat_prefix = self.key.replace("-", "_")

        if self.enabled:
            stats = await ATOMAPI.get_stats(self._rbln_stat_path)
            device_stats_by_device_filename: Dict[str, ATOMDeviceStat] = {
                "/dev/" + device.device: device for device in stats.devices
            }
            for cid in container_ids:
                mem_stats[cid] = 0
                mem_sizes[cid] = 0
                util_stats[cid] = Decimal("0")
                number_of_devices_per_container[cid] = 0
                async with Docker() as docker:
                    container_info = await docker.containers.get(cid)
                for device in container_info["HostConfig"]["Devices"]:
                    if device["PathOnHost"] in device_stats_by_device_filename:
                        device_stat = device_stats_by_device_filename[device["PathOnHost"]]
                        mem_stats[cid] += int(device_stat.memory.used)
                        mem_sizes[cid] += int(device_stat.memory.total)
                        util_stats[cid] += Decimal(device_stat.util)
                        number_of_devices_per_container[cid] += 1
        return [
            ContainerMeasurement(
                MetricKey(f"{stat_prefix}_mem"),
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
                MetricKey(f"{stat_prefix}_util"),
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

    async def create_alloc_map(self) -> DiscretePropertyAllocMap:
        devices = await self.list_devices()
        dpam = DiscretePropertyAllocMap(
            device_slots={
                dev.device_id: DeviceSlotInfo(SlotTypes.COUNT, self.slot_types[0][0], Decimal(1))
                for dev in devices
            },
            exclusive_slot_types=self.exclusive_slot_types,
        )
        return dpam

    async def generate_mounts(
        self,
        source_path: Path,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> List[MountInfo]:
        binpath = Path("/usr/local/bin")
        if self.slot_types[0][0] in device_alloc:
            return [
                MountInfo(MountTypes.BIND, binpath / "rbln-stat", binpath / "rbln-stat"),
            ]
        else:
            return []

    @abstractmethod
    async def list_device_files(
        self,
        device: TATOMDevice,
    ) -> Iterable[str]:
        raise NotImplementedError

    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, Any]:
        assigned_devices: List[TATOMDevice] = []
        device_files: List[Path] = []
        additional_device_files = [Path("/dev/rmda")]

        numa_node_indexes: set[int] = set()
        for dev in await self._list_devices():
            if dev.device_id in device_alloc.get(self.slot_types[0][0], {}).keys():
                assert dev.numa_node is not None, "NUMA node index of accelerator cannot be null!"
                assigned_devices.append(dev)
                device_files.extend([Path(x) for x in await self.list_device_files(dev)])
                numa_node_indexes.add(dev.numa_node)
        if (
            len(numa_node_indexes) > 1
            and self.atom_config["general"]["enforce_singular_numa_affinity"]
        ):
            raise RuntimeError(f"NUMA affinity dispersed ({numa_node_indexes})!")

        try:
            group_idx = await self.group_npus(assigned_devices)
            log.debug("Created NPU Group {} with members {}", group_idx, assigned_devices)
            additional_device_files.append(Path(f"/dev/rsd{group_idx}"))
        except LibraryError as e:
            log.warning(f"Failed to create NPU Group: {str(e)}, starting kernel without NPU group")
            additional_device_files.append(Path("/dev/rsd0"))

        for filename in additional_device_files:
            try:
                filename.stat()  # check if target file exists
                device_files.append(filename)
            except FileNotFoundError:
                pass  # just skip mounting without raising error

        return {
            "HostConfig": {
                "CapAdd": ["IPC_LOCK"],
                "IpcMode": "host",
                "Ulimits": [
                    {
                        "Name": "memlock",
                        "Hard": -1,
                        "Soft": -1,
                    },
                ],
                "Sysctls": {
                    "net.ipv6.conf.all.disable_ipv6": "0",
                },
                "Devices": [
                    {
                        "PathOnHost": dev.as_posix(),
                        "PathInContainer": dev.as_posix(),
                        "CgroupPermissions": "rwm",
                    }
                    for dev in device_files
                ],
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
                        "proc": proc,
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
        active_device_ids = sorted(active_device_id_set, key=lambda v: int(v.replace("rbln", "")))
        data["ATOM_GLOBAL_DEVICE_IDS"] = ",".join(
            f"{local_idx}:{global_id}" for local_idx, global_id in enumerate(active_device_ids)
        )
        return data

    @abstractmethod
    async def group_npus(self, devices: List[TATOMDevice]) -> int:
        raise NotImplementedError

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    async def get_docker_networks(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> List[str]:
        return []

    async def gather_process_measures(
        self,
        ctx: StatContext,
        pid_map: Mapping[int, str],
    ) -> Sequence[ProcessMeasurement]:
        return []

    @abstractmethod
    def get_metadata(self) -> AcceleratorMetadata:
        raise NotImplementedError

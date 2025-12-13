import logging
from decimal import Decimal
from pathlib import Path
from pprint import pformat
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)

import aiodocker
from aiodocker import Docker

from ai.backend.accelerator.tenstorrent.utils import resolve_pci_sysfs_path

from .. import __version__
from .types import TTn300Device

try:
    from ai.backend.agent.resources import get_resource_spec_from_container  # type: ignore
except ImportError:
    from ai.backend.agent.docker.resources import get_resource_spec_from_container

from tt_smi.tt_smi_backend import TTSMIBackend
from tt_tools_common.utils_common.tools_utils import (
    PciChip,
    detect_chips_with_callback,
)

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

PREFIX = "tt-n300"
VALID_CARD_TYPE = "n300"

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class TTn300Plugin(AbstractComputePlugin):
    key = DeviceName("tt-n300")
    slot_types: Sequence[Tuple[SlotName, SlotTypes]] = (
        (SlotName("tt-n300.device"), SlotTypes("count")),
    )
    exclusive_slot_types: Set[str] = {"tt-n300.device"}

    device_mask: Sequence[DeviceId] = []
    enabled: bool = True

    _all_devices: Optional[List[TTn300Device]]

    _tt_devices: list[PciChip]
    _tt_backend: TTSMIBackend

    async def init(self, context: Any = None) -> None:
        self._all_devices = None

        raw_device_mask = self.plugin_config.get("device_mask")
        if raw_device_mask is not None:
            self.device_mask = [
                *map(lambda dev_id: DeviceId(dev_id), raw_device_mask.split(",")),
            ]

        try:
            detected_devices = await self.list_devices()
            log.info("detected devices:\n" + pformat(detected_devices))
            log.info("Tenstorrent acceleration is enabled.")
        except ImportError:
            log.warning("could not find Tenstorrent devices with VID 1eff.")
            self.enabled = False

    async def list_devices(self) -> List[TTn300Device]:
        if self._all_devices is not None:
            return self._all_devices

        devices: List[TTn300Device] = []

        tt_devices = detect_chips_with_callback(print_status=False)
        backend = TTSMIBackend(tt_devices, pretty_output=False)

        self._tt_devices = tt_devices
        self._tt_backend = backend

        # device_idx in terms of TTSMIBackend API
        for device_idx, pci_chip in enumerate(tt_devices):
            device_info = backend.get_device_info(device_idx)
            # we need to aggregate results of Left and Right so discard informations about right card by evaluating PCI Bus ID
            # right board should report 'N/A' instead of valid PCI bus ID
            if device_info["board_type"] not in VALID_CARD_TYPE or device_info["bus_id"] == "N/A":
                continue
            log.debug("Config: {}", device_info)
            pci_idx, bus, _dev_fn = device_info["bus_id"].split(":", maxsplit=3)

            pci_base_path = resolve_pci_sysfs_path(f"{pci_idx}:{bus}")
            if not pci_base_path:
                raise RuntimeError("PCI device file not found in the sysfs!")

            numa_node_idx_path = Path(pci_base_path) / "device" / "numa_node"
            numa_node_idx = int(numa_node_idx_path.read_text())
            if numa_node_idx < 0:
                numa_node_idx = 0

            device = TTn300Device(
                model_name="Tenstorrent n300",
                serial=DeviceId(device_info["board_id"]),
                device_id=DeviceId(str(device_idx)),
                device_number=int(device_idx),
                hw_location=device_info["bus_id"],
                memory_size=int(BinarySize.from_str(device_info["dram_speed"]))
                * 2,  # can't understand why but memory size information is represented by `dram_speed` key'
                processing_units=0,
                numa_node=numa_node_idx,
                tt_pci_chip=pci_chip,
                tt_device_idx=device_idx,
            )
            devices.append(device)

        self._all_devices = devices
        return self._all_devices

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
                "tt_n300_support": True,
            }
        return {}

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        stat_prefix = self.key.replace("-", "_")

        power_total = Decimal("0")
        power_stats = {}

        dev_count = 0

        if self.enabled:
            for device in await self.list_devices():
                left_stat = self._tt_backend.get_chip_telemetry(device.tt_device_idx)
                right_stat = self._tt_backend.get_chip_telemetry(device.tt_device_idx + 1)
                device_id = device.device_id

                dev_power = Decimal(left_stat["power"].strip()) + Decimal(
                    right_stat["power"].strip()
                )
                power_total += dev_power
                power_stats[device_id] = Measurement(dev_power)

                dev_count += 1
        return [
            NodeMeasurement(
                MetricKey(f"{stat_prefix}_power"),
                MetricTypes.USAGE,
                unit_hint="watts",
                stats_filter=frozenset({"max"}),
                per_node=Measurement(Decimal(power_total)),
                per_device=power_stats,
            ),
        ]

    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        power_stats: Dict[str, Decimal] = {}
        number_of_devices_per_container: Dict[str, int] = {}
        stat_prefix = self.key.replace("-", "_")

        if self.enabled:
            device_stats_by_device_filename: Dict[str, Tuple[Dict, Dict]] = {
                f"/dev/tenstorrent/{device.device_number}": (
                    self._tt_backend.get_chip_telemetry(device.tt_device_idx),
                    self._tt_backend.get_chip_telemetry(device.tt_device_idx + 1),
                )
                for device in (await self.list_devices())
            }

            for cid in container_ids:
                power_stats[cid] = Decimal("0")
                number_of_devices_per_container[cid] = 0
                async with Docker() as docker:
                    container_info = await docker.containers.get(cid)
                for device in container_info["HostConfig"]["Devices"]:
                    if device["PathOnHost"] in device_stats_by_device_filename:
                        left_stat, right_stat = device_stats_by_device_filename[
                            device["PathOnHost"]
                        ]
                        power_stats[cid] += Decimal(left_stat["power"].strip())
                        power_stats[cid] += Decimal(right_stat["power"].strip())
                        number_of_devices_per_container[cid] += 1
        return [
            ContainerMeasurement(
                MetricKey(f"{stat_prefix}_power"),
                MetricTypes.USAGE,
                unit_hint="watts",
                stats_filter=frozenset({"max"}),
                per_container={
                    cid: Measurement(
                        Decimal(usage),
                    )
                    for cid, usage in power_stats.items()
                },
            ),
        ]

    async def create_alloc_map(self) -> DiscretePropertyAllocMap:
        devices = await self.list_devices()
        dpam = DiscretePropertyAllocMap(
            device_slots={
                DeviceId(str(dev.device_id)): DeviceSlotInfo(
                    SlotTypes.COUNT, self.slot_types[0][0], Decimal(1)
                )
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
        return []

    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, Any]:
        devices: dict[str, str] = {}
        alloc_idx = 0
        for dev in await self.list_devices():
            if dev.device_id in device_alloc.get(self.slot_types[0][0], {}).keys():
                devices[f"/dev/tenstorrent/{dev.device_number}"] = f"/dev/tenstorrent/{alloc_idx}"
                alloc_idx += 1

        assigned_devices: dict[Path, Path] = {}
        for host_path, container_path in devices.items():
            try:
                Path(host_path).stat()  # check if target file exists
                assigned_devices[Path(host_path)] = Path(container_path)
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
                        "PathOnHost": (host_path.as_posix()),
                        "PathInContainer": (container_path.as_posix()),
                        "CgroupPermissions": "rwm",
                    }
                    for host_path, container_path in assigned_devices.items()
                ],
                "Mounts": [
                    {
                        "BindOptions": {},
                        "ReadOnly": False,
                        "Source": "/dev/hugepages-1G",
                        "Target": "/dev/hugepages-1G",
                        "Type": "bind",
                    }
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
        active_device_ids = sorted(active_device_id_set)
        data["TT_GLOBAL_DEVICE_IDS"] = ",".join(
            f"{local_idx}:{global_id}" for local_idx, global_id in enumerate(active_device_ids)
        )
        return data

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

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "tt-n300.device",
            "description": "Tenstorrent n300",
            "human_readable_name": "Tenstorrent n300 Device",
            "display_unit": "n300",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "npu",
        }

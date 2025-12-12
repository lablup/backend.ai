import asyncio
import ipaddress
import json
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
import trafaret as t

from ai.backend.agent.docker.resources import get_resource_spec_from_container
from ai.backend.agent.resources import (
    AbstractAllocMap,
    AbstractComputePlugin,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
    StatContext,
)
from ai.backend.agent.stats import (
    ContainerMeasurement,
    Measurement,
    MetricTypes,
    NodeMeasurement,
    ProcessMeasurement,
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
    MountTypes,
    SlotName,
    SlotTypes,
)

from . import __version__
from .exception import DockerNetworkError, NoIPUoFConfError
from .gc_api import GraphcoreAPI
from .types import IPUDevice

PREFIX = "ipu"

log = BraceStyleAdapter(logging.getLogger("ai.backend.accelerator.ipu"))


_config_iv = t.Dict({
    "ipuof-config-path": t.String,
    "docker-networks": t.List(t.String),
}).allow_extra("*")


async def exec_command(command: str, args: List[str]) -> Tuple[bytes, bytes]:
    proc = await asyncio.create_subprocess_exec(
        command, *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    return await proc.communicate()


class IPUPlugin(AbstractComputePlugin):
    key = DeviceName("ipu")
    slot_types: Sequence[Tuple[SlotName, SlotTypes]] = (
        (SlotName("ipu.device"), SlotTypes("count")),
    )
    exclusive_slot_types: Set[str] = {"ipu.device"}

    device_mask: Sequence[DeviceId] = []
    enabled: bool = True

    ipu_config: Dict[str, Any]

    _all_devices: Optional[list[IPUDevice]]
    ipuof_devices: Mapping[str, Any]
    ipuof_attributes: Mapping[str, Any]
    subnet_network_map: Mapping[ipaddress.IPv4Network, str]

    async def init(self, context: Any = None) -> None:
        self._all_devices = None
        raw_device_mask = self.plugin_config.get("device_mask")
        if raw_device_mask is not None:
            self.device_mask = [
                *map(lambda dev_id: DeviceId(dev_id), raw_device_mask.split(",")),
            ]

        raw_cfg, cfg_src_path = config.read_from_file(None, "ipu")
        self.ipu_config = _config_iv.check(raw_cfg)
        log.info("Read IPU device configs from {}", cfg_src_path)

        def _read_json():
            with open(self.ipu_config["ipuof-config-path"], "r") as fr:
                return json.loads(fr.read())

        try:
            raw_ipuof_config = await asyncio.get_running_loop().run_in_executor(None, _read_json)
            self.ipuof_devices = {
                f"{d['ip']}:{d['device_id']}": d for d in raw_ipuof_config["devices"]
            }
            self.ipuof_attributes = raw_ipuof_config["attributes"]
        except FileNotFoundError:
            log.warning("could not find IPUoF configuration file.")
            self.enabled = False
            return
        try:
            detected_devices = await self.list_devices()
            log.info("detected devices:\n" + pformat(detected_devices))
            log.info("IPU acceleration is enabled.")
        except (ImportError, NoIPUoFConfError):
            log.warning("could not find Graphcore IPUs with gc-monitor command.")
            self.enabled = False
        try:
            await self.prepare_networks()
        except DockerNetworkError as e:
            log.warning("error while preparing docker networks: " + e.args[0])
            self.enabled = False

    async def list_devices(self) -> List[IPUDevice]:
        if self._all_devices is not None:
            return self._all_devices
        graphcore_info = await GraphcoreAPI.get_monitor_info()
        devices: list[IPUDevice] = []
        for card in graphcore_info["cards"]:
            for ipu in card["ipus"]:
                device = IPUDevice(
                    device_id=DeviceId(ipu["ID"]),
                    hw_location=card["IPU-M"] + ":" + ipu["PCIe ID"],
                    memory_size=0,
                    processing_units=0,
                    numa_node=0,
                    model_name=card["Type"],
                    serial=ipu["Serial"],
                    ip=card["IPU-M"],
                )
                devices.append(device)

        self._all_devices = devices
        return self._all_devices

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {
            SlotName("ipu.device"): Decimal(len(devices)),
        }

    async def prepare_networks(self) -> None:
        self.subnet_network_map = {}
        docker_network_identifiers = self.ipu_config["docker-networks"]
        network_map: Dict[str, Any] = {}
        async with aiodocker.Docker() as docker:
            networks = await docker.networks.list()
            for network in networks:
                network_map[network["Name"]] = network
                network_map[network["Id"]] = network

        for network_identifier in docker_network_identifiers:
            network_config = network_map.get(network_identifier)
            if not network_config:
                raise DockerNetworkError(f"Network {network_identifier} not found")
            ipv4_subnet = [
                x["Subnet"] for x in network_config["IPAM"]["Config"] if ":" not in x["Subnet"]
            ]
            if len(ipv4_subnet) == 0:
                raise DockerNetworkError(f"IPv4 config not found on network {network_identifier}")
            if len(ipv4_subnet) > 1:
                raise DockerNetworkError(f"Multiple IPv4 configs on network {network_identifier}")
            ip_network = ipaddress.ip_network(ipv4_subnet[0])
            assert isinstance(ip_network, ipaddress.IPv4Network)
            self.subnet_network_map[ip_network] = network_identifier

    def get_docker_network(self, device: IPUDevice) -> str:
        for subnet, network in self.subnet_network_map.items():
            if ipaddress.ip_address(device.ip) in subnet:
                return network
        else:
            raise DockerNetworkError(f"Device {device.hw_location} not available")

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, Any]:
        if self.enabled:
            return {
                "ipu_support": True,
                "poplar_version": await GraphcoreAPI.get_poplar_version(),
            }
        return {}

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        dev_count = 0
        mem_avail_total = 0
        mem_used_total = 0
        mem_stats = {}
        util_total = 0.0
        util_stats = {}
        if self.enabled:
            for inventory_info in await GraphcoreAPI.get_inventories():
                device_id = DeviceId(inventory_info["id"])
                mem_avail_total += int(inventory_info["hexoatt total size (bytes)"]) + int(
                    inventory_info["hexopt total size (bytes)"]
                )
                mem_used_total += int(inventory_info["hexoatt active size (bytes)"]) + int(
                    inventory_info["hexopt active size (bytes)"]
                )
                mem_stats[device_id] = Measurement(
                    Decimal(
                        int(inventory_info["hexoatt active size (bytes)"])
                        + int(inventory_info["hexopt active size (bytes)"])
                    ),
                    Decimal(
                        int(inventory_info["hexoatt total size (bytes)"])
                        + int(inventory_info["hexopt total size (bytes)"])
                    ),
                )
                util_total += float(inventory_info["ipu utilisation"].replace("%", ""))
                util_stats[device_id] = Measurement(
                    Decimal(float(inventory_info["ipu utilisation"].replace("%", "")))
                )
                dev_count += 1
        return [
            NodeMeasurement(
                MetricKey("ipu_mem"),
                MetricTypes.USAGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_node=Measurement(Decimal(mem_used_total), Decimal(mem_avail_total)),
                per_device=mem_stats,
            ),
            NodeMeasurement(
                MetricKey("ipu_util"),
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
        if self.enabled:
            inventory_map: dict[DeviceId, dict[str, str]] = {
                DeviceId(i["id"]): i for i in await GraphcoreAPI.get_inventories()
            }
            devices_by_hw_id: dict[str, IPUDevice] = {
                d.hw_location: d for d in await self.list_devices()
            }
            for cid in container_ids:
                mem_stats[cid] = 0
                mem_sizes[cid] = 0
                util_stats[cid] = Decimal("0")
                number_of_devices_per_container[cid] = 0
                async with aiodocker.Docker() as docker:
                    container_info = await docker.containers.get(cid)
                for mount in container_info["HostConfig"]["Mounts"]:
                    if mount["Target"] == "/etc/ipuof.conf.d":
                        ipuof_conf_path = (
                            Path(mount["Source"]) / Path(self.ipu_config["ipuof-config-path"]).name
                        )
                        ipuof_conf = json.loads(
                            await asyncio.get_running_loop().run_in_executor(
                                None, ipuof_conf_path.read_text
                            )
                        )
                        for device in ipuof_conf["devices"]:
                            hw_location = device["ip"] + ":" + str(device["device_id"])
                            device = devices_by_hw_id[hw_location]
                            inventory_info = inventory_map[device.device_id]
                            mem_stats[cid] += int(
                                inventory_info["hexoatt active size (bytes)"]
                            ) + int(inventory_info["hexopt active size (bytes)"])
                            mem_sizes[cid] += int(
                                inventory_info["hexoatt total size (bytes)"]
                            ) + int(inventory_info["hexopt total size (bytes)"])
                            util_stats[cid] += Decimal(
                                inventory_info["ipu utilisation"].replace("%", "")
                            )
                            number_of_devices_per_container[cid] += 1
        return [
            ContainerMeasurement(
                MetricKey("ipu_mem"),
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
                MetricKey("ipu_util"),
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

    # TODO: Implement
    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        return []

    async def create_alloc_map(self) -> DiscretePropertyAllocMap:
        devices = await self.list_devices()
        dpam = DiscretePropertyAllocMap(
            device_slots={
                dev.device_id: DeviceSlotInfo(SlotTypes.COUNT, SlotName("ipu.device"), Decimal(1))
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
        devices = await self.list_devices()
        target_devices_ipuof_config = [
            self.ipuof_devices[d.hw_location]
            for d in devices
            if device_alloc.get(SlotName("ipu.device"), {}).get(d.device_id) is not None
        ]
        generated_ipuof_config = {
            "devices": target_devices_ipuof_config,
            "attributes": self.ipuof_attributes,
        }
        generated_ipuof_config_path = (
            source_path / "ipuof.conf.d" / Path(self.ipu_config["ipuof-config-path"]).name
        )

        def _write():
            generated_ipuof_config_path.parent.mkdir(parents=True)
            with open(generated_ipuof_config_path, "w") as fw:
                fw.write(json.dumps(generated_ipuof_config))

        await asyncio.get_running_loop().run_in_executor(None, _write)
        return [
            MountInfo(
                MountTypes.BIND,
                generated_ipuof_config_path.parent,
                Path("/etc/ipuof.conf.d"),
            )
        ]

    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[str]:
        devices = await self.list_devices()

        return list({
            self.get_docker_network(d)
            for d in devices
            if device_alloc.get(SlotName("ipu.device"), {}).get(d.device_id) is not None
        })

    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, Any]:
        return {
            "Env": ["IPUOF_CONFIG_PATH=/etc/ipuof.conf.d/ipuof.conf"],
            "HostConfig": {
                "CapAdd": ["IPC_LOCK"],
                "IpcMode": "host",
                "Ulimits": [{"Name": "memlock", "Hard": -1, "Soft": -1}],
                "Sysctls": {"net.ipv6.conf.all.disable_ipv6": "0"},
                "Devices": [
                    {
                        "PathOnHost": "/dev/infiniband",
                        "PathInContainer": "/dev/infiniband",
                        "CgroupPermissions": "rwm",
                    },
                ],
            },
        }

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids: List[DeviceId] = []
        if SlotName("ipu.device") in device_alloc:
            device_ids.extend(device_alloc[SlotName("ipu.device")].keys())
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
                        DeviceName("ipu"),
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
            alloc_map.allocations[SlotName("ipu.device")].update(
                resource_spec.allocations.get(
                    DeviceName("ipu"),
                    {},
                ).get(
                    SlotName("ipu.device"),
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
        data["IPU_GLOBAL_DEVICE_IDS"] = ",".join(
            f"{local_idx}:{global_id}" for local_idx, global_id in enumerate(active_device_ids)
        )
        return data

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "ipu.device",
            "description": "IPU",
            "human_readable_name": "IPU Device",
            "display_unit": "IPU",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "ipu",
        }

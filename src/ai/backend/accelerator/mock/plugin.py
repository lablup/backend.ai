from __future__ import annotations

import asyncio
import json
import logging
import random
import re
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from decimal import ROUND_DOWN, Decimal
from pathlib import Path
from pprint import pformat
from typing import (
    Any,
    Collection,
    Dict,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    cast,
)

import aiodocker
import trafaret as t

from ai.backend.agent.exception import InitializationError
from ai.backend.agent.resources import (
    AbstractAllocMap,
    AbstractComputePlugin,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
    FractionAllocMap,
)
from ai.backend.agent.types import Container, MountInfo
from ai.backend.agent.utils import update_nested_dict

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
from ai.backend.common import config
from ai.backend.common import validators as tx
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    AcceleratorMetadata,
    BinarySize,
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    HardwareMetadata,
    MetricKey,
    SlotName,
    SlotTypes,
)

from . import __version__
from .defs import AllocationModes
from .types import CUDADevice, DeviceStat, MockDevice, closing_async

__all__ = (
    "PREFIX",
    "CUDADevice",
    "MockDevice",
    "MockPlugin",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


MIN_MEM_UNIT = 512 * (2**20)  # 512 MiB
MIN_SMP_UNIT = 2
MIN_SMP_COUNT = 4  # when calculated SMP is lower than this, set this as the minimum.
# ref: TensorFlow's TF_MIN_GPU_MULTIPROCESSOR_COUNT environment variable.

PREFIX = "mock"

_format_config_iv = t.Dict({
    t.Key("human_readable_name"): t.String,
    t.Key("description"): t.String,
    t.Key("display_unit"): t.String,
    t.Key("number_format"): t.Dict({
        t.Key("binary"): t.Bool,
        t.Key("round_length"): t.Int[0:],
    }),
    t.Key("display_icon"): t.String,
}).allow_extra("*")


_mock_config_iv = t.Dict({
    t.Key("slot_name"): t.String,
    t.Key("device_plugin_name"): t.String,
    t.Key("devices"): t.List(
        t.Dict({
            t.Key("mother_uuid"): tx.UUID,
            t.Key("model_name"): t.String,
            t.Key("numa_node"): t.Int[0:],
            t.Key("subproc_count"): t.Int[1:],
            t.Key("memory_size"): tx.BinarySize,
        }).allow_extra("*")
    ),
    t.Key("attributes"): t.Dict({}).allow_extra("*"),
    t.Key("formats"): t.Dict({}).allow_extra("*"),
}).allow_extra("*")

_cuda_devices_config_iv = t.List(
    t.Dict({
        t.Key("is_mig_device"): t.ToBool,
    }).allow_extra("*")
)

_cuda_attributes_iv = t.Dict({
    t.Key("nvidia_driver", default="450.00.00"): t.String,
    t.Key("cuda_runtime", default="11.0"): t.String,
}).allow_extra("*")


class MockPlugin(AbstractComputePlugin):
    config_watch_enabled = False

    key: DeviceName
    slot_types: List[Tuple[SlotName, SlotTypes]] = []
    exclusive_slot_types: Set[str] = set()

    device_formats: Mapping[str, Mapping[str, Any]]

    enabled: bool = True
    device_mask: Sequence[DeviceId] = []
    reserved_memory: int = 64 * (2**20)  # 64 MiB (only for fractional)
    quantum_size: Decimal = Decimal("0.1")

    _all_devices: Optional[Sequence[MockDevice]] = None
    _mode: AllocationModes = AllocationModes.DISCRETE
    _unit_mem: int = 2 * (2**30)  # 2 GiB
    _unit_proc: int = 8  # number of SMPs

    nvdocker_version: Tuple[int, ...] = (0, 0, 0)
    docker_version: Tuple[int, ...] = (0, 0, 0)

    async def init(self, context: Any = None) -> None:
        # Read the mockup device config.
        raw_cfg, cfg_src_path = config.read_from_file(None, "mock-accelerator")
        self.mock_config = _mock_config_iv.check(raw_cfg)
        log.info("Read mocked device configs from {}", cfg_src_path)
        self.key = DeviceName(self.mock_config["slot_name"])
        if self.mock_config["slot_name"] == "cuda":
            _cuda_devices_config_iv.check(self.mock_config["devices"])
            _cuda_attributes_iv.check(self.mock_config["attributes"])

        # Set the allocation mode.
        mode = self.plugin_config.get("allocation_mode")
        if mode is None:
            log.warning(f'{self.key} allocation mode is not set. Using "discrete" mode.')
            self._mode = AllocationModes.DISCRETE
        else:
            try:
                self._mode = AllocationModes(mode)
            except ValueError:
                log.error("Invalid fractional mode value.")
                log.info(f"{self.key} acceleration is disabled.")
                self.enabled = False
                return

        self.device_formats = {}
        for format_name, format in self.mock_config["formats"].items():
            self.device_formats[format_name] = _format_config_iv.check(format)

        if self._mode == AllocationModes.DISCRETE:
            self.slot_types.append((f"{self.key}.device", "count"))  # type: ignore  # (only updated here)
        elif self._mode == AllocationModes.FRACTIONAL:
            self.slot_types.append((f"{self.key}.shares", "count"))  # type: ignore  # (only updated here)
        else:
            log.error("Invalid allocation mode: {}", self._mode)
            self.enabled = False
            return

        if self.key == DeviceName("cuda"):  # CUDA specific setups
            self.exclusive_slot_types = {"cuda.device:*-mig", "cuda.device", "cuda.shares"}
            # Check the docker version
            self.nvdocker_version = (2, 5, 0)  # mocked version
            try:
                proc = await asyncio.create_subprocess_exec(
                    "docker",
                    "version",
                    "-f",
                    "{{json .}}",
                    stdout=asyncio.subprocess.PIPE,
                )
                stdout, _ = await proc.communicate()
                lines = stdout.decode().splitlines()
            except FileNotFoundError:
                log.error('could not execute the "docker version" command.')
                log.warning("CUDA acceleration is disabled.")
                self.enabled = False
                return
            rx_triple_version = re.compile(r"(\d+\.\d+\.\d+)")
            docker_version_data = json.loads(lines[0])
            m = rx_triple_version.search(docker_version_data["Server"]["Version"])
            if m:
                self.docker_version = tuple(map(int, m.group(1).split(".")))
            else:
                log.error("could not detect docker version!")
                log.warning("CUDA acceleration is disabled.")
                self.enabled = False
                return
            log.info(
                "NVIDIA driver version: {} (mocked)",
                self.mock_config["attributes"]["nvidia_driver"],
            )
            log.info("nvidia-docker version (mocked): {}", self.nvdocker_version)
            log.info("docker version: {}", self.docker_version)

        # Read the configurations.
        raw_unit_mem = self.plugin_config.get("unit_mem")
        if raw_unit_mem is not None:
            unit_mem = int(raw_unit_mem)
            if unit_mem < MIN_MEM_UNIT:
                raise InitializationError(f"{self.key} plugin: too small unit_mem")
            self._unit_mem = unit_mem
        raw_unit_proc = self.plugin_config.get("unit_proc")
        if raw_unit_proc is not None:
            unit_proc = int(raw_unit_proc)
            if unit_proc < MIN_SMP_UNIT:
                raise InitializationError(f"{self.key} plugin: too small unit_proc")
            self._unit_proc = unit_proc
        raw_device_mask = self.plugin_config.get("device_mask")
        if raw_device_mask is not None:
            self.device_mask = [
                *map(lambda dev_id: DeviceId(dev_id), raw_device_mask.split(",")),
            ]
        if self._mode == AllocationModes.FRACTIONAL:
            raw_reserved_memory = self.plugin_config.get("reserved_memory")
            if raw_reserved_memory is not None:
                self.reserved_memory = int(raw_reserved_memory)
        else:
            self.reserved_memory = 0
        raw_quantum_size = self.plugin_config.get("quantum_size", "0.1")
        self.quantum_size = Decimal(raw_quantum_size)
        if self._mode == AllocationModes.FRACTIONAL:
            log.info("The fraction quantum size: {}", self.quantum_size)

        # Detect devices.
        try:
            detected_devices = await self.list_devices()
            log.info("detected devices (mocked):\n" + pformat(detected_devices))
            log.info(f"{self.key} acceleration is enabled.")
        except ImportError:
            log.warning(f"{self.key} acceleration is disabled.")
            self.enabled = False
            return

        # Update the slot types before returning so that agent would recognize MIG slots.
        await self.available_slots()

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

    async def list_devices(self) -> Collection[MockDevice]:
        if not self.enabled:
            return []
        if self._all_devices is not None:
            return self._all_devices

        device_cls: Type[MockDevice]
        all_devices = []

        for idx, dev_info in enumerate(self.mock_config["devices"]):
            init_kwargs = {
                "plugin_name": self.mock_config["device_plugin_name"],
                "device_id": DeviceId(dev_info["mother_uuid"]),
                "hw_location": f"0000:99:{idx:02d}.0",
                "mother_uuid": dev_info["mother_uuid"],
                "numa_node": dev_info["numa_node"],
                "memory_size": dev_info["memory_size"],
                "processing_units": dev_info["subproc_count"],
                "model_name": dev_info["model_name"],
            }
            match self.key:
                case "cuda":
                    init_kwargs["is_mig_device"] = dev_info["is_mig_device"]
                    if dev_info["is_mig_device"]:
                        init_kwargs["device_id"] = DeviceId(
                            f"MIG-{dev_info['mother_uuid']}/{idx}/0"
                        )
                    device_cls = CUDADevice
                case _:
                    device_cls = MockDevice

            all_devices.append(device_cls(**init_kwargs))
        self._all_devices = all_devices
        return all_devices

    def _cuda_available_slots(self, devices: List[CUDADevice]) -> MutableMapping[SlotName, Decimal]:
        slots: MutableMapping[SlotName, Decimal] = defaultdict(Decimal)
        if self._mode == AllocationModes.DISCRETE:
            slots[SlotName("cuda.device")] = Decimal(
                len([dev for dev in devices if not dev.is_mig_device])
            )
        elif self._mode == AllocationModes.FRACTIONAL:
            slots[SlotName("cuda.shares")] = Decimal(
                sum(self._get_share(dev) for dev in devices if not dev.is_mig_device)
            )
        for dev in devices:
            if not dev.is_mig_device:
                continue
            # collect MIG resource slots
            mig_slot_name = self._get_mig_slot_name(dev)
            slots[mig_slot_name] += Decimal(1)
            slot_type = (mig_slot_name, SlotTypes.UNIQUE)
            if slot_type not in self.slot_types:
                self.slot_types.append(slot_type)
        return slots

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        slots: MutableMapping[SlotName, Decimal] = defaultdict(Decimal)
        match self.key:
            case "cuda":
                slots = self._cuda_available_slots(cast(List[CUDADevice], devices))
            case _:
                if self._mode == AllocationModes.DISCRETE:
                    slots[SlotName(f"{self.key}.device")] = Decimal(len(devices))
                elif self._mode == AllocationModes.FRACTIONAL:
                    slots[SlotName(f"{self.key}.shares")] = Decimal(
                        sum(self._get_share(dev) for dev in devices)
                    )

        return slots

    @staticmethod
    def _get_mig_slot_name(dev: CUDADevice) -> SlotName:
        mig_profile = dev.model_name.split("-", maxsplit=1)[1]
        return SlotName(f"cuda.device:{mig_profile}-mig")

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, Any]:
        if self.enabled:
            return {
                f"{self.key}_support": True,
                **self.mock_config["attributes"],
            }
        return {
            f"{self.key}_support": False,
        }

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        dev_count = len(self._all_devices or [])
        mem_avail_total = 0
        mem_used_total = 0
        mem_stats = {}
        util_total = 0
        util_stats = {}
        power_usage_total = 0
        power_usage = {}
        power_max_total = 0
        temperature = {}
        if not self._all_devices:
            return []
        if self.enabled:
            for device_info in self._all_devices:
                device_id = device_info.device_id
                if device_id in self.device_mask:
                    continue
                # Randomly generate device statistics!
                mem_used = int(device_info.memory_size * random.uniform(0.2, 1.0))
                dev_stat = DeviceStat(
                    device_id=device_id,
                    mem_total=device_info.memory_size,
                    mem_used=mem_used,
                    mem_free=device_info.memory_size - mem_used,
                    mem_util=int(mem_used / device_info.memory_size * 100),
                    gpu_util=int(random.uniform(0, 100)),
                    power_usage=int(random.normalvariate(200, 50) * 1000),
                    power_max=250 * 1000,
                    core_temperature=int(random.normalvariate(90, 20)),
                )
                mem_avail_total += dev_stat.mem_total
                mem_used_total += dev_stat.mem_used
                mem_stats[device_id] = Measurement(
                    Decimal(dev_stat.mem_used), Decimal(dev_stat.mem_total)
                )
                util_total += dev_stat.gpu_util
                util_stats[device_id] = Measurement(Decimal(dev_stat.gpu_util), Decimal(100))
                power_usage_total += dev_stat.power_usage // 1000
                power_max_total += dev_stat.power_max // 1000
                power_usage[device_id] = Measurement(
                    Decimal(dev_stat.power_usage // 1000), Decimal(dev_stat.power_max // 1000)
                )
                temperature[device_id] = Measurement(
                    Decimal(dev_stat.core_temperature), Decimal(120)
                )
        avg_temperature = statistics.mean(map(lambda m: m.value, temperature.values()))
        return [
            NodeMeasurement(
                MetricKey(f"{self.key}_mem"),
                MetricTypes.GAUGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_node=Measurement(Decimal(mem_used_total), Decimal(mem_avail_total)),
                per_device=mem_stats,
            ),
            NodeMeasurement(
                MetricKey(f"{self.key}_util"),
                MetricTypes.GAUGE,
                unit_hint="percent",
                stats_filter=frozenset({"avg", "max"}),
                per_node=Measurement(Decimal(util_total), Decimal(dev_count * 100)),
                per_device=util_stats,
            ),
            NodeMeasurement(
                MetricKey(f"{self.key}_power"),
                MetricTypes.GAUGE,
                unit_hint="Watts",
                stats_filter=frozenset({"avg", "max"}),
                per_node=Measurement(Decimal(power_usage_total), Decimal(power_max_total)),
                per_device=power_usage,
            ),
            NodeMeasurement(
                MetricKey(f"{self.key}_temperature"),
                MetricTypes.GAUGE,
                unit_hint="Celsius",
                stats_filter=frozenset({"avg", "max"}),
                per_node=Measurement(
                    Decimal(avg_temperature),
                    Decimal(120),
                ),
                per_device=temperature,
            ),
        ]

    def _find_device(self, device_id: DeviceId) -> MockDevice | None:
        if self._all_devices is None:
            return None
        for device_info in self._all_devices:
            if str(device_info.device_id) == device_id:
                return device_info
        return None

    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        mem_stats: Dict[str, int] = {}
        mem_sizes: Dict[str, int] = {}
        util_stats: Dict[str, float] = {}
        device_occurrences_per_container: Dict[str, int] = defaultdict(int)
        assignment_per_container: Dict[str, Mapping[DeviceId, Decimal]] = {}
        if self.enabled:
            for cid in container_ids:
                mem_stats[cid] = 0
                mem_sizes[cid] = 0
                util_stats[cid] = 0.0
            async with closing_async(aiodocker.Docker()) as docker:
                for cid in container_ids:
                    container = docker.containers.container(cid)
                    await container.show()
                    resource_spec = await get_resource_spec_from_container(container)
                    if resource_spec is None:
                        continue
                    allocations = resource_spec.allocations.get(self.key, {})
                    for slot_name, per_dev_alloc in allocations.items():
                        assignment_per_container[cid] = per_dev_alloc
                        for device_id, alloc in per_dev_alloc.items():
                            device_info = self._find_device(device_id)
                            if device_info is None:
                                continue
                            device_mem_size = device_info.memory_size
                            device_subproc_count = device_info.processing_units
                            device_capacity = self._get_share_raw(
                                device_mem_size,
                                device_subproc_count,
                            )
                            if slot_name == SlotName(f"{self.key}.shares"):
                                if alloc > 0:
                                    util_stats[cid] += min(
                                        100.0,
                                        random.uniform(0, 100) * float(device_capacity / alloc),
                                    )
                                mem_stats[cid] = int(
                                    device_mem_size * random.uniform(0.2, 1.0) * float(alloc)
                                )
                                mem_sizes[cid] += device_mem_size * alloc
                            else:
                                util_stats[cid] += random.uniform(0, 100)
                                mem_stats[cid] = int(device_mem_size * random.uniform(0.2, 1.0))
                                mem_sizes[cid] += device_mem_size
                            device_occurrences_per_container[cid] += 1
        return [
            ContainerMeasurement(
                MetricKey(f"{self.key}_mem"),
                MetricTypes.GAUGE,
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
                MetricTypes.UTILIZATION,
                unit_hint="percent",
                stats_filter=frozenset({"avg", "max"}),
                per_container={
                    cid: Measurement(
                        Decimal(util),
                        Decimal(device_occurrences_per_container[cid] * 100),
                    )
                    for cid, util in util_stats.items()
                },
            ),
        ]

    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        return []

    async def create_alloc_map(self) -> AbstractAllocMap:
        devices = await self.list_devices()
        if self._mode == AllocationModes.DISCRETE:
            return DiscretePropertyAllocMap(
                device_slots={
                    dev.device_id: (
                        DeviceSlotInfo(SlotTypes.COUNT, SlotName(f"{self.key}.device"), Decimal(1))
                        if (not isinstance(dev, CUDADevice) or not dev.is_mig_device)
                        else DeviceSlotInfo(
                            SlotTypes.UNIQUE, self._get_mig_slot_name(dev), Decimal(1)
                        )
                    )
                    for dev in devices
                },
                exclusive_slot_types=self.exclusive_slot_types,
            )
        elif self._mode == AllocationModes.FRACTIONAL:
            # for legacy agents
            kwargs: Dict[str, Any] = {
                "quantum_size": self.quantum_size,
            }
            for kw in [*kwargs.keys()]:
                if kw not in FractionAllocMap.__init__.__annotations__:
                    kwargs.pop(kw)
            return FractionAllocMap(
                device_slots={
                    dev.device_id: (
                        DeviceSlotInfo(
                            SlotTypes.COUNT, SlotName(f"{self.key}.shares"), self._get_share(dev)
                        )
                        if (not isinstance(dev, CUDADevice) or not dev.is_mig_device)
                        else DeviceSlotInfo(
                            SlotTypes.UNIQUE, self._get_mig_slot_name(dev), Decimal(1)
                        )
                    )
                    for dev in devices
                },
                exclusive_slot_types=self.exclusive_slot_types,
                **kwargs,
            )
        else:
            raise RuntimeError("Unsupported MockDevicePlugin allocation mode!")

    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    async def generate_docker_args(
        self,
        docker: aiodocker.Docker,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, Any]:
        docker_config: Dict[str, Any] = {}
        if not self.enabled:
            return docker_config
        assigned_device_ids = []
        for slot_type, per_device_alloc in device_alloc.items():
            # now we assume that a single device cannot have multiple different slots
            for device_id, alloc in per_device_alloc.items():
                if alloc > 0:
                    assigned_device_ids.append(device_id)
        match self.key:
            case "cuda":
                if self.nvdocker_version[0] == 2:
                    update_nested_dict(
                        docker_config,
                        {
                            "Env": [
                                f"TF_MIN_GPU_MULTIPROCESSOR_COUNT={MIN_SMP_COUNT}",
                                "BACKENDAI_MOCK_CUDA_DEVICES="
                                + ",".join(map(str, assigned_device_ids)),
                                f"BACKENDAI_MOCK_CUDA_DEVICE_COUNT={len(assigned_device_ids)}",
                            ]
                        },
                    )
                else:
                    raise RuntimeError(
                        f"Unsupported nvidia-docker version: {self.nvdocker_version}"
                    )
        return docker_config

    def _get_share(self, device: MockDevice) -> Decimal:
        if isinstance(device, CUDADevice):
            assert not device.is_mig_device
        return self._get_share_raw(device.memory_size, device.processing_units)

    def _get_share_raw(self, memory_size: int, subproc_count: int) -> Decimal:
        mem_shares = memory_size / self._unit_mem
        proc_shares = subproc_count / self._unit_proc
        common_shares = min(mem_shares, proc_shares)
        quantum = Decimal(".01")
        return Decimal(common_shares).quantize(quantum, ROUND_DOWN)

    def _share_to_spec(self, share: Decimal) -> Tuple[BinarySize, int]:
        return (
            BinarySize(self._unit_mem * share),
            max(int(self._unit_proc * share), MIN_SMP_COUNT),
        )

    async def generate_resource_data(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, str]:
        data: MutableMapping[str, str] = {}
        if not self.enabled:
            return data

        is_unique = False
        active_device_id_list: List[DeviceId] = []
        for slot_type, per_device_alloc in device_alloc.items():
            if slot_type == SlotTypes.UNIQUE:
                assert len(device_alloc) == 1
                assert len(per_device_alloc) == 1
                device_id = list(per_device_alloc.keys())[0]
                active_device_id_list.append(device_id)
                is_unique = True
                break
            else:
                for dev_id, alloc in per_device_alloc.items():
                    if alloc > 0:
                        active_device_id_list.append(dev_id)

        match self.key:
            case "cuda":
                data["CUDA_GLOBAL_DEVICE_IDS"] = ",".join(
                    f"{local_idx}:{device_id}"
                    for local_idx, device_id in enumerate(active_device_id_list)
                )
                data["CUDA_RESOURCE_VIRTUALIZED"] = (
                    "0" if is_unique or self._mode == AllocationModes.DISCRETE else "1"
                )
                if self._mode == AllocationModes.FRACTIONAL:
                    mem_limits = []
                    proc_limits = []
                    # With unique slots and in the discrete allocation mode,
                    # the below will have no results and
                    # CUDA_*_LIMITS will be set to an empty string.
                    for slot_type, per_dev_alloc in device_alloc.items():
                        if slot_type == "cuda.shares":
                            for device_id, share in per_dev_alloc.items():
                                mem, proc = self._share_to_spec(share)
                                mem_limits.append((device_id, mem))
                                proc_limits.append((device_id, proc))
                    mlim_str = ",".join(f"{device_id}:{mem: }" for device_id, mem in mem_limits)
                    plim_str = ",".join(f"{device_id}:{proc}" for device_id, proc in proc_limits)
                    data["CUDA_MEMORY_LIMITS"] = mlim_str
                    data["CUDA_PROCESSOR_LIMITS"] = plim_str
                    data["CUDA_RESERVED_MEMORY"] = str(self.reserved_memory)

        return data

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
            if self._mode == AllocationModes.DISCRETE:
                alloc_map.allocations[SlotName(f"{self.key}.device")].update(
                    resource_spec.allocations.get(
                        self.key,
                        {},
                    ).get(
                        SlotName(f"{self.key}.device"),
                        {},
                    ),
                )
            elif self._mode == AllocationModes.FRACTIONAL:
                alloc_map.allocations[SlotName(f"{self.key}.shares")].update(
                    resource_spec.allocations.get(
                        self.key,
                        {},
                    ).get(
                        SlotName(f"{self.key}.shares"),
                        {},
                    ),
                )

    async def get_attached_devices(
        self,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Sequence[DeviceModelInfo]:
        device_ids: List[DeviceId] = []
        for slot_name, per_device_alloc in device_alloc.items():
            # cuda.device:* slot name dedicated for mocked MIG devices
            if slot_name.startswith("cuda.device:") or slot_name in (
                f"{self.key}.device",
                f"{self.key}.shares",
            ):
                device_ids.extend(per_device_alloc.keys())
        available_devices = await self.list_devices()
        attached_devices: List[DeviceModelInfo] = []
        for device in available_devices:
            if device.device_id in device_ids:
                if self._mode == AllocationModes.FRACTIONAL:
                    if isinstance(device, CUDADevice) and device.is_mig_device:
                        continue
                    mem, proc = self._share_to_spec(
                        device_alloc[SlotName(f"{self.key}.shares")][device.device_id],
                    )
                else:
                    proc = device.processing_units
                    mem = BinarySize(device.memory_size)
                attached_devices.append({
                    "device_id": device.device_id,
                    "model_name": device.model_name,
                    "data": {
                        "smp": proc,
                        "mem": mem,
                    },
                })
        return attached_devices

    async def get_node_hwinfo(self) -> HardwareMetadata:
        return {
            "status": "healthy",
            "status_info": None,
            "metadata": {
                "name": "Backend.AI Mocked Accelerator Node",
                "platform": "Backend.AI",
                "serial_number": "N/A",
                "version": __version__,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            },
        }

    async def get_docker_networks(
        self, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[str]:
        return []

    async def generate_mounts(
        self, source_path: Path, device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]
    ) -> List[MountInfo]:
        return []

    def get_metadata(self) -> AcceleratorMetadata:
        assert self._all_devices is not None
        format_key = ""
        if self._mode == AllocationModes.DISCRETE:
            format_key = "device"
        else:
            format_key = "shares"
        if self.key == DeviceName("cuda"):
            for device in self._all_devices:
                assert isinstance(device, CUDADevice)
                if device.is_mig_device:
                    format_key = "*-mig"
                    break

        device_format = self.device_formats[format_key]
        return {
            "slot_name": f"{self.mock_config['slot_name']}.{format_key}",
            "human_readable_name": device_format["human_readable_name"],
            "description": device_format["description"],
            "display_unit": device_format["display_unit"],
            "number_format": device_format["number_format"],
            "display_icon": device_format["display_icon"],
        }

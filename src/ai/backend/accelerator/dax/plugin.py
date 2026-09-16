import asyncio
import logging
import os
import tomllib
from collections.abc import Callable, Collection, Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from http import HTTPStatus
from pathlib import Path
from typing import Any, Final, Literal, TypedDict, override

import aiodocker
from aiodocker.exceptions import DockerError
from aiotools import closing_async
from pydantic import ValidationError

from ai.backend.accelerator.dax import __version__
from ai.backend.accelerator.dax.alloc_map import DAXAllocMap
from ai.backend.accelerator.dax.config import DAXPluginConfig, default_config_paths, load_config
from ai.backend.accelerator.dax.discovery import (
    DAXDeviceInfo,
    StatFunc,
    discover_devices,
)
from ai.backend.agent.alloc_map import AbstractAllocMap, DeviceSlotInfo
from ai.backend.agent.docker.resources import get_resource_spec_from_container
from ai.backend.agent.errors.resources import InvalidResourceArgument
from ai.backend.agent.resources import (
    AbstractComputeDevice,
    AbstractComputePlugin,
    DeviceAllocation,
)
from ai.backend.agent.stats import (
    ContainerMeasurement,
    NodeMeasurement,
    ProcessMeasurement,
    StatContext,
)
from ai.backend.agent.types import Container, MountInfo
from ai.backend.common.docker import LabelName
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import (
    AcceleratorMetadata,
    BinarySize,
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    HardwareMetadata,
    SlotName,
    SlotTypes,
)
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DAX_SLOT: Final[SlotName] = SlotName("dax.device")
DAX_PATH_PREFIX: Final[str] = "/dev/dax"
HOLDER_SCAN_TIMEOUT: Final[float] = 5.0

type HardwareStatus = Literal["healthy", "degraded", "offline", "unavailable"]
type DockerFactory = Callable[[], aiodocker.Docker]


class DAXHolder(TypedDict):
    kernel_id: str
    container_id: str


class DAXDevice(AbstractComputeDevice):
    info: DAXDeviceInfo

    def __init__(self, info: DAXDeviceInfo, device_id: DeviceId) -> None:
        super().__init__(
            device_id=device_id,
            hw_location=info.region,
            memory_size=info.size,
            processing_units=0,
            numa_node=info.numa_node if info.numa_node >= 0 else None,
            device_name=DeviceName("dax"),
        )
        self.info = info


def _device_payload(info: DAXDeviceInfo) -> dict[str, Any]:
    return {
        "id": info.device_id,
        "path": info.path,
        "size": info.size,
        "align": info.align,
        "numa_node": info.numa_node,
        "target_node": info.target_node,
        "region": info.region,
        "serials": list(info.serials),
    }


def _format_time(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _read_container_dax_paths(backend_obj: Any) -> list[str]:
    try:
        devices = backend_obj["HostConfig"]["Devices"]
    except KeyError:
        return []
    paths: list[str] = []
    for device in devices or []:
        path = device["PathInContainer"]
        if isinstance(path, str) and path.startswith(DAX_PATH_PREFIX):
            paths.append(path)
    return paths


def _device_id_at(by_path: Mapping[str, DAXDeviceInfo], path: str) -> DeviceId | None:
    info = by_path.get(path)
    return info.device_id if info is not None else None


class DAXPlugin(AbstractComputePlugin):
    config_watch_enabled = False

    key = DeviceName("dax")
    slot_types: Sequence[tuple[SlotName, SlotTypes]] = ((DAX_SLOT, SlotTypes.COUNT),)

    _config_paths: Sequence[Path]
    _stat_func: StatFunc
    _config: DAXPluginConfig
    _config_path: Path | None
    _invalid_config: str | None
    _admitted: Sequence[DAXDeviceInfo]
    _excluded: Sequence[DAXDeviceInfo]
    _devices: Sequence[DAXDevice]
    _agent_started_at: datetime | None
    _last_granted_at: dict[DeviceId, datetime]
    _grant_count: dict[DeviceId, int]
    _docker_factory: DockerFactory
    _holder_scan_timeout: float

    def __init__(
        self,
        plugin_config: Mapping[str, Any],
        local_config: Mapping[str, Any],
        *,
        config_paths: Sequence[Path] | None = None,
        stat_func: StatFunc = os.stat,
        docker_factory: DockerFactory = aiodocker.Docker,
        holder_scan_timeout: float = HOLDER_SCAN_TIMEOUT,
    ) -> None:
        super().__init__(plugin_config, local_config)
        self._config_paths = config_paths if config_paths is not None else default_config_paths()
        self._stat_func = stat_func
        self._docker_factory = docker_factory
        self._holder_scan_timeout = holder_scan_timeout
        self._config = DAXPluginConfig()
        self._config_path = None
        self._invalid_config = None
        self._admitted = ()
        self._excluded = ()
        self._devices = ()
        self._agent_started_at = None
        self._last_granted_at = {}
        self._grant_count = {}

    @override
    async def init(self, context: Any | None = None) -> None:
        self._agent_started_at = datetime.now(UTC)
        try:
            config, config_path = await asyncio.to_thread(load_config, self._config_paths)
        except (OSError, tomllib.TOMLDecodeError, ValidationError) as e:
            self._invalid_config = str(e)
            log.error("DAX plugin config is invalid; no devices are admitted: {}", e)
            return
        self._config = config
        self._config_path = config_path
        result = await asyncio.to_thread(discover_devices, config, self._stat_func)
        self._admitted = tuple(result.admitted)
        self._excluded = tuple(result.excluded)
        self._devices = tuple(
            DAXDevice(info, info.device_id) for info in self._admitted if info.device_id is not None
        )
        log.info(
            "DAX config: {} (max_holders={}, mock={})",
            config_path,
            config.max_holders,
            config.mock,
        )
        for info in self._admitted:
            log.info("DAX device admitted: {} ({}, {} bytes)", info.name, info.device_id, info.size)
        for info in self._excluded:
            log.warning("DAX device excluded: {} ({})", info.name, info.excluded_reason)

    @override
    async def cleanup(self) -> None:
        pass

    @override
    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        pass

    @override
    def get_version(self) -> str:
        return __version__

    @override
    async def extra_info(self) -> Mapping[str, str]:
        return {}

    @override
    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": str(DAX_SLOT),
            "human_readable_name": "DAX Device",
            "description": "Linux device-DAX (CXL memory)",
            "display_unit": "DAX",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "ram",
        }

    @override
    async def list_devices(self) -> Collection[DAXDevice]:
        return self._devices

    @override
    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        return {DAX_SLOT: Decimal(len(self._devices) * self._config.max_holders)}

    @override
    async def create_alloc_map(self) -> AbstractAllocMap:
        return DAXAllocMap(
            device_slots={
                device.device_id: DeviceSlotInfo(
                    SlotTypes.COUNT, DAX_SLOT, Decimal(self._config.max_holders)
                )
                for device in self._devices
            },
        )

    def _granted_devices(self, device_alloc: DeviceAllocation) -> list[DAXDeviceInfo]:
        granted_ids = {
            device_id for device_id, amount in device_alloc.get(DAX_SLOT, {}).items() if amount > 0
        }
        admitted_ids = {info.device_id for info in self._admitted}
        unknown_ids = granted_ids - admitted_ids
        if unknown_ids:
            raise InvalidResourceArgument(f"no admitted DAX device: {sorted(unknown_ids)}")
        return [info for info in self._admitted if info.device_id in granted_ids]

    def _path_on_host(self, info: DAXDeviceInfo) -> str:
        default_path = str(self._config.dev_root / info.name)
        if self._config.mock:
            return self._config.path_on_host.get(info.name, default_path)
        return default_path

    @override
    async def generate_docker_args(
        self,
        docker: aiodocker.Docker,
        device_alloc: DeviceAllocation,
    ) -> Mapping[str, Any]:
        granted = self._granted_devices(device_alloc)
        if not granted:
            return {}
        now = datetime.now(UTC)
        for info in granted:
            if info.device_id is not None:
                self._last_granted_at[info.device_id] = now
                self._grant_count[info.device_id] = self._grant_count.get(info.device_id, 0) + 1
        return {
            "HostConfig": {
                "Devices": [
                    {
                        "PathOnHost": self._path_on_host(info),
                        "PathInContainer": info.path,
                        "CgroupPermissions": "rw",
                    }
                    for info in granted
                ],
            },
            "Env": [
                "BACKENDAI_DAX_DEVICES=" + dump_json_str([_device_payload(i) for i in granted]),
                "BACKENDAI_DAX_PATHS=" + ",".join(info.path for info in granted),
            ],
        }

    @override
    async def generate_resource_data(self, device_alloc: DeviceAllocation) -> Mapping[str, str]:
        granted = self._granted_devices(device_alloc)
        if not granted:
            return {}
        return {"DAX_DEVICES": dump_json_str([_device_payload(info) for info in granted])}

    @override
    async def get_attached_devices(
        self, device_alloc: DeviceAllocation
    ) -> Sequence[DeviceModelInfo]:
        return [
            {
                "device_id": info.device_id or info.name,
                "model_name": "device-DAX",
                "data": {"mem": BinarySize(info.size)},
            }
            for info in self._granted_devices(device_alloc)
        ]

    @override
    def get_additional_gids(self) -> list[int]:
        return sorted({info.gid for info in self._admitted if info.gid is not None})

    async def _scan_holders(self) -> dict[str, list[DAXHolder]]:
        """Map each `PathOnHost` to the Running kernel containers that mount it."""
        holders: dict[str, list[DAXHolder]] = {}
        filters = dump_json_str({"label": [LabelName.KERNEL_ID], "status": ["running"]})
        async with closing_async(self._docker_factory()) as docker:
            for container in await docker.containers.list(filters=filters):
                try:
                    info = await container.show()
                except DockerError as e:
                    if e.status == HTTPStatus.NOT_FOUND:
                        continue
                    raise
                if not info["State"]["Running"]:
                    continue
                holder: DAXHolder = {
                    "kernel_id": info["Config"]["Labels"][LabelName.KERNEL_ID],
                    "container_id": info["Id"],
                }
                devices = info["HostConfig"].get("Devices") or []
                for path in {device["PathOnHost"] for device in devices}:
                    holders.setdefault(path, []).append(holder)
        return holders

    async def _collect_holders(self) -> tuple[dict[str, list[DAXHolder]] | None, str]:
        """Return `(holders by host path, "")`, or `(None, error)` when the scan fails."""
        try:
            async with asyncio.timeout(self._holder_scan_timeout):
                return await self._scan_holders(), ""
        except TimeoutError:
            error = f"holder scan timed out after {self._holder_scan_timeout} s"
        except Exception as e:
            error = repr(e)
        log.warning("DAX holder scan failed: {}", error)
        return None, error

    @override
    async def get_node_hwinfo(self) -> HardwareMetadata:
        status: HardwareStatus
        if self._invalid_config is not None:
            status = "unavailable"
        elif self._admitted:
            status = "healthy"
        elif self._excluded:
            status = "degraded"
        else:
            status = "unavailable"
        holders_by_path, holder_scan_error = await self._collect_holders()
        devices = [
            {
                "name": info.name,
                **_device_payload(info),
                "driver": info.driver,
                "excluded_reason": info.excluded_reason,
                "last_granted_at": _format_time(
                    self._last_granted_at.get(info.device_id)
                    if info.device_id is not None
                    else None
                ),
                "grant_count": (
                    self._grant_count.get(info.device_id, 0) if info.device_id is not None else 0
                ),
                "holders": (
                    holders_by_path.get(self._path_on_host(info), [])
                    if holders_by_path is not None
                    else None
                ),
            }
            for info in (*self._admitted, *self._excluded)
        ]
        metadata = {
            "max_holders": str(self._config.max_holders),
            "agent_started_at": _format_time(self._agent_started_at) or "",
            "config_path": str(self._config_path) if self._config_path is not None else "",
            "devices": dump_json_str(devices),
            "holder_scan_error": holder_scan_error,
        }
        if self._invalid_config is not None:
            metadata["invalid_config"] = self._invalid_config
        return {
            "status": status,
            "status_info": f"{len(self._admitted)} admitted, {len(self._excluded)} excluded",
            "metadata": metadata,
        }

    @override
    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        try:
            await self._restore_from_container(container, alloc_map)
        except FileNotFoundError:
            raise
        except Exception:
            log.exception("restore_from_container(): skipped container {}", container.id)

    async def _restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        resource_spec = await get_resource_spec_from_container(container.backend_obj)
        if resource_spec is None:
            return
        recorded = resource_spec.allocations.get(self.key, {}).get(DAX_SLOT, {})
        recorded_ids = [DeviceId(device_id) for device_id, amount in recorded.items() if amount > 0]
        if not recorded_ids:
            return
        mounted_paths = _read_container_dax_paths(container.backend_obj)
        by_id = {info.device_id: info for info in self._admitted}
        by_path = {info.path: info for info in self._admitted}
        held: dict[DeviceId, Decimal] = {}
        claimed_paths: set[str] = set()
        for device_id in recorded_ids:
            info = by_id.get(device_id)
            if info is not None and info.path in mounted_paths:
                held[device_id] = Decimal(1)
                claimed_paths.add(info.path)
                continue
            log.error(
                "restore_from_container(): identity_mismatch in container {}: "
                "device {} is now at {}; mounted paths now hold {}",
                container.id,
                device_id,
                info.path if info is not None else None,
                {path: _device_id_at(by_path, path) for path in mounted_paths},
            )
            if info is not None:
                held[device_id] = Decimal(1)
        for path in mounted_paths:
            if path in claimed_paths:
                continue
            path_info = by_path.get(path)
            if path_info is not None and path_info.device_id is not None:
                held[path_info.device_id] = Decimal(1)
        alloc_map.apply_allocation({DAX_SLOT: held})

    @override
    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        return []

    @override
    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        return []

    @override
    async def gather_process_measures(
        self,
        ctx: StatContext,
        pid_map: Mapping[int, str],
    ) -> Sequence[ProcessMeasurement]:
        return []

    @override
    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    @override
    async def get_docker_networks(self, device_alloc: DeviceAllocation) -> list[str]:
        return []

    @override
    async def generate_mounts(
        self,
        source_path: Path,
        device_alloc: DeviceAllocation,
    ) -> list[MountInfo]:
        return []

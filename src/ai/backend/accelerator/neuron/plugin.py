import logging
from collections.abc import Mapping, MutableMapping, Sequence
from decimal import Decimal
from pathlib import Path
from pprint import pformat
from typing import Any

import aiodocker
from aiodocker import Docker
from aiodocker.exceptions import DockerError

from ai.backend.accelerator.neuron import __version__

from .neuron_api import NeuronAPI, NeuronDeviceInfo, NeuronToolError, resolve_neuron_ls_path
from .types import NeuronCoreDevice, make_core_device_id

try:
    from ai.backend.agent.resources import get_resource_spec_from_container  # type: ignore
except ImportError:
    from ai.backend.agent.docker.resources import get_resource_spec_from_container

from ai.backend.agent.resources import (
    AbstractAllocMap,
    AbstractComputePlugin,
    DeviceAllocation,
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
from ai.backend.logging import BraceStyleAdapter

PREFIX = "neuron"
SLOT_NAME = SlotName("neuron.core")

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


def _device_node_exists(path: Path) -> bool:
    try:
        path.stat()  # check if the device node exists
        return True
    except OSError:
        return False


class NeuronPlugin(AbstractComputePlugin):
    """
    Backend.AI compute plugin for AWS Neuron devices (Trainium / Inferentia).

    The allocation unit is the **NeuronCore**, not the Neuron device.  See
    ``README.md`` in this package for the evidence behind that choice; in short,
    ``NEURON_RT_VISIBLE_CORES`` is the runtime's own allocation primitive, every
    runtime-varying metric the driver exposes is keyed per core, and sysfs models
    cores as first-class nested objects.
    """

    key = DeviceName("neuron")
    slot_types: Sequence[tuple[SlotName, SlotTypes]] = ((SLOT_NAME, SlotTypes("count")),)
    exclusive_slot_types: set[str] = {"neuron.core"}

    device_mask: Sequence[DeviceId] = []
    enabled: bool = True

    _neuron_ls_path: str
    _all_devices: list[NeuronCoreDevice] | None
    _device_infos: list[NeuronDeviceInfo]

    async def init(self, context: Any = None) -> None:
        self._all_devices = None
        self._device_infos = []

        raw_device_mask = self.plugin_config.get("device_mask")
        if raw_device_mask is not None:
            self.device_mask = [
                *map(lambda dev_id: DeviceId(dev_id.strip()), str(raw_device_mask).split(",")),
            ]

        # `neuron-ls` is a CLI, so an absent tool raises FileNotFoundError rather
        # than ImportError.  Agents load *every* installed accelerator plugin
        # unless `allow-compute-plugins` is configured, and the plugin loader
        # calls `entrypoint.load()` with no exception handling, so letting that
        # escape would take down the agent's entire plugin load.  Resolve the
        # path up front and disable the plugin instead.
        configured_path = self.plugin_config.get("neuron_ls_path")
        neuron_ls_path = resolve_neuron_ls_path(configured_path)
        if neuron_ls_path is None:
            log.info(
                "Could not find an executable neuron-ls; Neuron acceleration is disabled. "
                "(looked at the configured path, the DLAMI default and $PATH)"
            )
            self.enabled = False
            return
        self._neuron_ls_path = neuron_ls_path

        try:
            detected_devices = await self.list_devices()
        except NeuronToolError as e:
            # The degraded host: tool installed, driver absent or exposing no
            # device.  Not an error worth failing startup over.
            log.warning("Neuron acceleration is disabled: {}", e)
            self.enabled = False
            return
        except OSError as e:
            log.warning("Neuron acceleration is disabled due to a host I/O error: {}", e)
            self.enabled = False
            return

        if not detected_devices:
            log.info("No NeuronCore detected; Neuron acceleration is disabled.")
            self.enabled = False
            return

        log.info("detected devices:\n" + pformat(detected_devices))
        log.info("Neuron acceleration is enabled ({} NeuronCores).", len(detected_devices))

    async def list_devices(self) -> list[NeuronCoreDevice]:
        if self._all_devices is not None:
            return self._all_devices
        if not self.enabled:
            return []

        device_infos = await NeuronAPI.list_devices(self._neuron_ls_path)
        devices: list[NeuronCoreDevice] = []

        for info in device_infos:
            serial = NeuronAPI.read_device_serial(info.neuron_device) or ""
            model_name = NeuronAPI.read_device_model_name(info.neuron_device) or "AWS Neuron"
            arch_type = NeuronAPI.read_device_arch_type(info.neuron_device) or ""
            # `numa_node` arrives as a *string* and is "-1" on instances that do
            # not expose NUMA topology for the device; clamp it to node 0 the way
            # the Tenstorrent plugin does for its sysfs-read value.
            numa_node = max(info.numa_node, 0)

            for core_index, global_core_id in enumerate(info.neuroncore_ids):
                device_id = make_core_device_id(global_core_id)
                if device_id in self.device_mask:
                    continue
                devices.append(
                    NeuronCoreDevice(
                        model_name=model_name,
                        serial=serial,
                        neuron_device_index=info.neuron_device,
                        core_index=core_index,
                        global_core_id=global_core_id,
                        arch_type=arch_type,
                        device_id=device_id,
                        hw_location=info.bdf,
                        # `neuron-ls` reports `memory_size` in *bare bytes* (not a
                        # human-readable string), at the device level; the cores of
                        # one device share that HBM pool.
                        memory_size=info.memory_size_per_core,
                        processing_units=1,
                        numa_node=numa_node,
                    )
                )

        self._device_infos = device_infos
        self._all_devices = devices
        return devices

    async def available_slots(self) -> Mapping[SlotName, Decimal]:
        devices = await self.list_devices()
        return {SLOT_NAME: Decimal(len(devices))}

    def get_version(self) -> str:
        return __version__

    async def extra_info(self) -> Mapping[str, str]:
        if not self.enabled:
            return {}
        info: dict[str, str] = {"neuron_support": "true"}
        if self._device_infos:
            first = self._device_infos[0]
            info["neuron_device_count"] = str(len(self._device_infos))
            info["neuron_cores_per_device"] = str(first.nc_count)
        return info

    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        """
        Report per-NeuronCore memory usage read from sysfs.

        The counters live under
        ``/sys/devices/virtual/neuron_device/neuron*/neuron_core*/stats/memory_usage/``,
        are world-readable and are populated with no workload attached, so no
        vendor daemon is needed.  ``neuron-monitor`` is deliberately not used: it
        is a streaming collector with no one-shot mode, whereas this hook is a
        per-tick pull.

        Per-core *utilization* is not reported: it requires ``neuron-monitor``
        with an attached process, which is out of scope for v1.
        """
        stat_prefix = self.key.replace("-", "_")

        mem_used_total = 0
        mem_capacity_total = 0
        mem_stats: dict[DeviceId, Measurement] = {}
        host_mem_used_total = 0
        host_mem_stats: dict[DeviceId, Measurement] = {}

        if self.enabled:
            devices = await self.list_devices()
            core_stats = await NeuronAPI.read_core_stats_batch([
                (dev.neuron_device_index, dev.core_index) for dev in devices
            ])
            for dev in devices:
                stats = core_stats[(dev.neuron_device_index, dev.core_index)]
                # `device_mem/total` in sysfs is a cumulative allocation counter,
                # not capacity (it reads 0 on an idle core), so capacity comes
                # from the neuron-ls device capacity split per core.
                capacity = dev.memory_size
                mem_used_total += stats.device_mem_present
                mem_capacity_total += capacity
                mem_stats[dev.device_id] = Measurement(
                    Decimal(stats.device_mem_present),
                    Decimal(capacity),
                )
                host_mem_used_total += stats.host_mem_present
                host_mem_stats[dev.device_id] = Measurement(Decimal(stats.host_mem_present))

        return [
            NodeMeasurement(
                MetricKey(f"{stat_prefix}_mem"),
                MetricTypes.USAGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_node=Measurement(
                    Decimal(mem_used_total),
                    Decimal(mem_capacity_total),
                ),
                per_device=mem_stats,
            ),
            NodeMeasurement(
                MetricKey(f"{stat_prefix}_host_mem"),
                MetricTypes.USAGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                # Host-side pinned memory registered by the Neuron runtime.  No
                # capacity is attached: the ceiling is host RAM, which the
                # intrinsic memory plugin already accounts for.
                per_node=Measurement(Decimal(host_mem_used_total)),
                per_device=host_mem_stats,
            ),
        ]

    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        """
        Attribute Neuron device memory to containers by their attached device nodes.

        Caveat, matching the Tenstorrent and Rebellions plugins: attribution is
        per *device node*, because that is all the Docker inspect output reveals.
        Since a device node carries all of its cores, two containers each holding
        one core of the same device are both credited with that device's usage.
        """
        stat_prefix = self.key.replace("-", "_")
        mem_stats: dict[str, int] = {}
        mem_capacities: dict[str, int] = {}

        if self.enabled:
            devices = await self.list_devices()
            core_stats = await NeuronAPI.read_core_stats_batch([
                (dev.neuron_device_index, dev.core_index) for dev in devices
            ])
            usage_by_node: dict[str, int] = {}
            capacity_by_node: dict[str, int] = {}
            for dev in devices:
                stats = core_stats[(dev.neuron_device_index, dev.core_index)]
                node_path = dev.device_node_path
                usage_by_node[node_path] = (
                    usage_by_node.get(node_path, 0) + stats.device_mem_present
                )
                capacity_by_node[node_path] = capacity_by_node.get(node_path, 0) + dev.memory_size

            for cid in container_ids:
                mem_stats[cid] = 0
                mem_capacities[cid] = 0
                try:
                    async with Docker() as docker:
                        container_info = await docker.containers.get(cid)
                except DockerError:
                    log.debug("skipping unreachable container {} in Neuron stat collection", cid)
                    continue
                for attached in container_info["HostConfig"].get("Devices") or []:
                    host_path = attached.get("PathOnHost")
                    if host_path in usage_by_node:
                        mem_stats[cid] += usage_by_node[host_path]
                        mem_capacities[cid] += capacity_by_node[host_path]

        return [
            ContainerMeasurement(
                MetricKey(f"{stat_prefix}_mem"),
                MetricTypes.USAGE,
                unit_hint="bytes",
                stats_filter=frozenset({"max"}),
                per_container={
                    cid: Measurement(Decimal(usage), Decimal(mem_capacities[cid]))
                    for cid, usage in mem_stats.items()
                },
            ),
        ]

    async def gather_process_measures(
        self,
        ctx: StatContext,
        pid_map: Mapping[int, str],
    ) -> Sequence[ProcessMeasurement]:
        # Per-process attribution requires `neuron-monitor` with an attached
        # process; `neuron-ls`'s `neuron_processes` field only lists PIDs holding
        # the driver handle, with no per-process resource figures.
        return []

    async def create_alloc_map(self) -> DiscretePropertyAllocMap:
        devices = await self.list_devices()
        return DiscretePropertyAllocMap(
            device_slots={
                dev.device_id: DeviceSlotInfo(SlotTypes.COUNT, SLOT_NAME, Decimal(1))
                for dev in devices
            },
            exclusive_slot_types=self.exclusive_slot_types,
        )

    async def get_hooks(self, distro: str, arch: str) -> Sequence[Path]:
        return []

    async def generate_mounts(
        self,
        source_path: Path,
        device_alloc: DeviceAllocation,
    ) -> list[MountInfo]:
        return []

    async def _allocated_devices(
        self,
        device_alloc: DeviceAllocation,
    ) -> list[NeuronCoreDevice]:
        allocated_ids = {
            dev_id for dev_id, alloc in device_alloc.get(SLOT_NAME, {}).items() if alloc > 0
        }
        return [dev for dev in await self.list_devices() if dev.device_id in allocated_ids]

    async def generate_docker_args(
        self,
        docker: aiodocker.docker.Docker,
        device_alloc: DeviceAllocation,
    ) -> Mapping[str, Any]:
        allocated = sorted(
            await self._allocated_devices(device_alloc),
            key=lambda dev: (dev.neuron_device_index, dev.core_index),
        )
        if not allocated:
            return {}

        # A device node carries *all* of its cores, so allocating a subset of a
        # device's cores still mounts the whole device node -- the container can
        # see sibling cores it was not allocated.  NEURON_RT_VISIBLE_CORES below
        # is what confines the runtime to the allocated ones.
        host_device_indices = sorted({dev.neuron_device_index for dev in allocated})

        # Renumber so the container always sees /dev/neuron0../dev/neuron{k-1}.
        container_index_of: dict[int, int] = {
            host_index: alloc_idx for alloc_idx, host_index in enumerate(host_device_indices)
        }

        assigned_devices: dict[str, str] = {}
        for host_index, alloc_idx in container_index_of.items():
            host_path = Path(f"/dev/neuron{host_index}")
            if not _device_node_exists(host_path):
                # Just skip mounting without raising an error, matching the
                # other NPU plugins' behaviour for hot-removed devices.
                log.warning("device node {} is missing; not mounting it", host_path)
                continue
            assigned_devices[host_path.as_posix()] = f"/dev/neuron{alloc_idx}"

        # Container-local NeuronCore indices.  The runtime numbers cores by the
        # order of the *visible* devices, so a core's container-local index is
        # (position of its device among the mounted ones) * nc_count + its index
        # within the device.
        nc_count_of = {info.neuron_device: info.nc_count for info in self._device_infos}

        def _container_local_core_index(dev: NeuronCoreDevice) -> int:
            host_index = dev.neuron_device_index
            nc_count = nc_count_of.get(host_index, 1)
            return container_index_of[host_index] * nc_count + dev.core_index

        visible_cores = sorted(_container_local_core_index(dev) for dev in allocated)

        return {
            "HostConfig": {
                # The Neuron runtime performs large pinned-memory registration,
                # which needs an unlimited memlock and IPC_LOCK, and shares its
                # IPC namespace with collectives peers.
                "CapAdd": ["IPC_LOCK"],
                "IpcMode": "host",
                "Ulimits": [{"Name": "memlock", "Hard": -1, "Soft": -1}],
                "Devices": [
                    {
                        "PathOnHost": host_path,
                        "PathInContainer": container_path,
                        "CgroupPermissions": "rwm",
                    }
                    for host_path, container_path in assigned_devices.items()
                ],
            },
            # `NEURON_RT_VISIBLE_CORES` is AWS's supported allocation primitive
            # (`NEURON_RT_NUM_CORES` is deprecated in its favour).  The agent
            # deep-merges this mapping into the container-create config and
            # *extends* the existing "Env" list rather than replacing it
            # (ai/backend/agent/utils.py:update_nested_dict, applied at
            # docker/agent.py:1206 after the agent's own Env at :1133), and the
            # same entries are written into `environ.txt`, which the in-container
            # kernel runner loads into os.environ.  The TPU plugin relies on the
            # same mechanism.
            "Env": [f"NEURON_RT_VISIBLE_CORES={','.join(map(str, visible_cores))}"],
        }

    async def generate_resource_data(
        self,
        device_alloc: DeviceAllocation,
    ) -> Mapping[str, str]:
        data: MutableMapping[str, str] = {}
        if not self.enabled:
            return data
        allocated = sorted(
            await self._allocated_devices(device_alloc),
            key=lambda dev: (dev.neuron_device_index, dev.core_index),
        )
        if not allocated:
            return data
        # local:global NeuronCore id pairs, mirroring the Tenstorrent and Furiosa
        # plugins' `*_GLOBAL_DEVICE_IDS` convention.  This lands in resource.txt
        # for the plugin's own hook libraries; the process environment is set via
        # the "Env" key of generate_docker_args instead.
        data["NEURON_GLOBAL_CORE_IDS"] = ",".join(
            f"{local_idx}:{dev.global_core_id}" for local_idx, dev in enumerate(allocated)
        )
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
                    slot_name: resource_spec.allocations.get(self.key, {}).get(
                        slot_name,
                        {
                            dev_id: Decimal(0)
                            for dev_id, dev_slot_info in alloc_map.device_slots.items()
                            if dev_slot_info.slot_name == slot_name
                        },
                    ),
                })
        else:  # older agents without lablup/backend.ai-agent#180
            alloc_map.allocations[SLOT_NAME].update(
                resource_spec.allocations.get(self.key, {}).get(SLOT_NAME, {}),
            )

    async def get_attached_devices(
        self,
        device_alloc: DeviceAllocation,
    ) -> Sequence[DeviceModelInfo]:
        attached_devices: list[DeviceModelInfo] = []
        for device in await self._allocated_devices(device_alloc):
            attached_devices.append({  # TODO: update common.types.DeviceModelInfo
                "device_id": device.device_id,
                "model_name": device.model_name,
                "data": {
                    "proc": device.processing_units,
                    "mem": BinarySize(device.memory_size),
                },
            })
        return attached_devices

    async def get_node_hwinfo(self) -> HardwareMetadata:
        if not self.enabled:
            return {
                "status": "unavailable",
                "status_info": "neuron-ls or the aws-neuronx driver is not available",
                "metadata": {},
            }
        devices = await self.list_devices()
        metadata: dict[str, str] = {
            "core_count": str(len(devices)),
            "device_count": str(len(self._device_infos)),
        }
        for info in self._device_infos:
            serial = NeuronAPI.read_device_serial(info.neuron_device)
            if serial:
                metadata[f"serial_number.neuron{info.neuron_device}"] = serial
        return {
            "status": "healthy",
            "status_info": None,
            "metadata": metadata,
        }

    async def get_docker_networks(
        self,
        device_alloc: DeviceAllocation,
    ) -> list[str]:
        return []

    def get_metadata(self) -> AcceleratorMetadata:
        return {
            "slot_name": "neuron.core",
            "description": "AWS Neuron NeuronCore",
            "human_readable_name": "AWS Neuron Core",
            "display_unit": "Core",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "aws",
        }

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        pass

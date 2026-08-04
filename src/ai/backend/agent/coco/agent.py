import asyncio
import ipaddress
import logging
import signal
import time
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, override
from uuid import UUID

from ai.backend.agent.agent import (
    ACTIVE_STATUS_SET,
    AbstractAgent,
    AbstractKernelCreationContext,
    ScanImagesResult,
)
from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.errors import (
    ContainerCreationError,
    KernelNotFoundError,
    UnsupportedResource,
)
from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.kernel_registry.writer.types import KernelRegistrySaveMetadata
from ai.backend.agent.resources import (
    AbstractComputePlugin,
    ComputerContext,
    KernelResourceSpec,
    Mount,
    known_slot_types,
)
from ai.backend.agent.types import Container, KernelOwnershipData, MountInfo, Port
from ai.backend.agent.utils import get_arch_name
from ai.backend.common.cgroup import get_cgroup_mount_point
from ai.backend.common.docker import ImageRef, LabelName
from ai.backend.common.dto.agent.response import PurgeImagesResp
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.kernel.anycast import (
    SessionChannelActivityAnycastEvent,
)
from ai.backend.common.json import dump_json_str, load_json
from ai.backend.common.types import (
    AutoPullBehavior,
    ClusterInfo,
    ClusterMode,
    ClusterSSHPortMapping,
    ContainerId,
    ContainerStatus,
    DeviceId,
    DeviceName,
    ImageConfig,
    ImageRegistry,
    KernelCreationConfig,
    KernelId,
    MountPermission,
    MountTypes,
    ResourceSlot,
    Sentinel,
    ServicePort,
    SessionId,
    SlotName,
    VFolderMount,
    current_resource_slots,
)
from ai.backend.logging import BraceStyleAdapter

from .blob import MeasuredBlobStore
from .errors import (
    AcceleratorHooksRefused,
    FolderEncryptionMissing,
    HostLogFolderRefused,
    MountPlanMissing,
    StorageBindRefused,
    UnmanagedFolderRefused,
    FractionalAcceleratorRefused,
    HostConfigReadbackRefused,
    ImageDistroUnresolved,
    ImagePushRefused,
    MultiNodeSessionRefused,
    HostPrivilegeWriteRefused,
    NetworkSetupFailed,
    RawCircuitRefused,
    ReleaseNotConfirmed,
)
from .kernel import CocoKernel
from .netns import NetworkConfig, SessionNetwork, SessionNetworkManager
from .relay import ChannelRelay, Circuit
from .resources import ALLOC_LABEL, encode_allocations, resolve_char_devices
from .runtime import AbstractRuntimeClient, NerdctlClient, RuntimeConfig
from .volumes import BlockVolume, BlockVolumeManager
from .spec import (
    GUEST_ENTRYPOINT,
    ContainerSpec,
    MountSpec,
    build_annotations,
    guest_sourced_mounts,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

GUEST_ADDR_LABEL = "ai.backend.coco.guest-addr"
SERVICE_PORTS_LABEL = "ai.backend.coco.service-ports"
RESOURCE_SPEC_LABEL = "ai.backend.coco.resource-spec"
IMAGE_LABEL = "ai.backend.coco.image"
NETWORK_ID_LABEL = "ai.backend.coco.network-id"
KERNELSPEC_LABEL = "ai.backend.coco.kernelspec"

ACTIVITY_REPORT_INTERVAL = 30.0
CHANNEL_PORT = 2010
SELF_ENCRYPTING_SERVICES = frozenset({"sshd"})


@dataclass(frozen=True)
class CocoSettings:
    runtime_class: str
    blob_annotation_key: str
    blob_store_path: Path
    containerd_namespace: str
    dns_servers: Sequence[str]
    container_start_timeout: float
    attestation_timeout: float
    relay_bind_host: str
    relay_bind_port: int
    raw_circuit_allowlist: frozenset[str]
    runtime_default_memory: int
    image_memory_allowance: int
    host_overhead_memory: int
    block_volume_root: Path
    scratch_volume_size: int
    image_store_volume_size: int


def build_settings(local_config: AgentUnifiedConfig) -> CocoSettings:
    section = local_config.confidential
    return CocoSettings(
        runtime_class=section.runtime_class,
        blob_annotation_key=section.blob_annotation_key,
        blob_store_path=section.blob_store_path,
        containerd_namespace=section.containerd_namespace,
        dns_servers=list(section.dns_servers),
        container_start_timeout=section.container_start_timeout,
        attestation_timeout=section.attestation_timeout,
        relay_bind_host=str(section.relay_bind_addr.host),
        relay_bind_port=section.relay_bind_addr.port,
        raw_circuit_allowlist=frozenset(section.raw_circuit_allowlist),
        runtime_default_memory=int(section.runtime_default_memory),
        image_memory_allowance=int(section.image_memory_allowance),
        host_overhead_memory=int(section.host_overhead_memory),
        block_volume_root=section.block_volume_root,
        scratch_volume_size=int(section.scratch_volume_size),
        image_store_volume_size=int(section.image_store_volume_size),
    )


def build_network_config(local_config: AgentUnifiedConfig) -> NetworkConfig:
    section = local_config.confidential
    denied = [ipaddress.IPv4Network(section.metadata_endpoint + "/32")]
    denied += [ipaddress.IPv4Network(cidr) for cidr in section.management_networks]
    return NetworkConfig(
        netns_dir=Path("/etc/netns"),
        subnet_pool=ipaddress.IPv4Network(section.session_subnet_pool),
        subnet_prefix=section.session_subnet_prefix,
        mtu=section.session_mtu,
        dns_servers=list(section.dns_servers),
        shim_host=str(section.broker_shim_addr.host),
        shim_port=section.broker_shim_addr.port,
        upstream_host=(
            str(section.broker_upstream_addr.host) if section.broker_upstream_addr else None
        ),
        upstream_port=(section.broker_upstream_addr.port if section.broker_upstream_addr else None),
        denied_networks=denied,
        reachability_timeout=section.broker_reachability_timeout,
    )


def _optional_uuid(raw: str | None) -> UUID | None:
    return UUID(raw) if raw else None


async def _wait_for_port(host: str, port: int, limit_seconds: float) -> None:
    deadline = asyncio.get_running_loop().time() + limit_seconds
    while True:
        try:
            async with asyncio.timeout(2.0):
                _, writer = await asyncio.open_connection(host, port)
            writer.close()
            return
        except (OSError, TimeoutError):
            if asyncio.get_running_loop().time() >= deadline:
                raise ReleaseNotConfirmed(
                    extra_msg=(
                        f"the guest at {host} did not open its runner channel on port {port}"
                        f" within {limit_seconds} seconds"
                    )
                ) from None
            await asyncio.sleep(1.0)


class CocoKernelCreationContext(AbstractKernelCreationContext[CocoKernel]):
    network: SessionNetwork | None

    def __init__(
        self,
        ownership_data: KernelOwnershipData,
        event_producer: EventProducer,
        kernel_image: ImageRef,
        kernel_config: KernelCreationConfig,
        distro: str,
        local_config: AgentUnifiedConfig,
        computers: Mapping[DeviceName, ComputerContext],
        restarting: bool = False,
        *,
        settings: CocoSettings,
        blob_store: MeasuredBlobStore,
        runtime: AbstractRuntimeClient,
        network_manager: SessionNetworkManager,
        volumes: BlockVolumeManager,
    ) -> None:
        self.volumes = volumes
        super().__init__(
            ownership_data,
            event_producer,
            kernel_image,
            kernel_config,
            distro,
            local_config,
            computers,
            restarting=restarting,
        )
        self.settings = settings
        self.blob_store = blob_store
        self.runtime = runtime
        self.network_manager = network_manager
        self.network = None
        self._container_memory = 0
        self._mounts: list[MountSpec] = []
        self._char_devices: list[Path] = []
        self._block_volumes: list[BlockVolume] = []

    @override
    async def get_extra_envs(self) -> Mapping[str, str]:
        return {}

    @override
    async def prepare_resource_spec(self) -> tuple[KernelResourceSpec, Mapping[str, Any] | None]:
        slots = ResourceSlot.from_json(self.kernel_config["resource_slots"])
        if SlotName("cpu") not in slots:
            raise UnsupportedResource("cpu slot is required")
        if SlotName("mem") not in slots:
            raise UnsupportedResource("mem slot is required")
        for slot_name, slot_value in slots.items():
            if slot_value == Decimal(0):
                continue
            if slot_name not in known_slot_types:
                raise UnsupportedResource(slot_name)
            if slot_name.endswith(".shares"):
                raise FractionalAcceleratorRefused(extra_msg=str(slot_name))
        current_resource_slots.set(known_slot_types)
        slots = slots.normalize_slots(ignore_unknown=True)
        requested_memory = int(slots[SlotName("mem")])
        self._container_memory = requested_memory + self.settings.image_memory_allowance
        slots[SlotName("mem")] = Decimal(
            self.settings.runtime_default_memory
            + self._container_memory
            + self.settings.host_overhead_memory
        )
        resource_spec = KernelResourceSpec(
            allocations={},
            slots=slots.copy(),
            mounts=[],
            scratch_disk_size=0,
        )
        return resource_spec, self.kernel_config.get("resource_opts", {})

    @override
    async def prepare_scratch(self) -> None:
        self._block_volumes = await self.volumes.provision(self.kernel_id)

    @override
    async def get_intrinsic_mounts(self) -> Sequence[Mount]:
        return []

    @property
    @override
    def repl_ports(self) -> Sequence[int]:
        return (CHANNEL_PORT,)

    @property
    @override
    def protected_services(self) -> Sequence[str]:
        return ()

    @override
    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        if ClusterMode(cluster_info["mode"]) is ClusterMode.MULTI_NODE:
            raise MultiNodeSessionRefused(extra_msg=str(self.session_id))
        self.network = await self.network_manager.create(
            self.kernel_id, self.session_id, self.kernel_config.get("cluster_idx", 0)
        )

    @override
    async def prepare_ssh(self, cluster_info: ClusterInfo) -> None:
        pass

    @override
    async def mount_vfolders(
        self, vfolders: Sequence[VFolderMount], resource_spec: KernelResourceSpec
    ) -> None:
        for vfolder in vfolders:
            if vfolder.name == ".logs":
                raise HostLogFolderRefused(extra_msg=str(vfolder.kernel_path))
            descriptor = vfolder.confidential
            if descriptor is None or not descriptor.key_path:
                raise FolderEncryptionMissing(extra_msg=f"{vfolder.name} -> {vfolder.kernel_path}")
            if not descriptor.source:
                raise UnmanagedFolderRefused(extra_msg=f"{vfolder.name} at {vfolder.host_path}")

    @override
    async def process_mounts(self, mounts: Sequence[Mount]) -> None:
        for mount in mounts:
            raise StorageBindRefused(
                extra_msg=f"{mount.type.value} {mount.source} -> {mount.target}"
            )

    @override
    async def mount_krunner(
        self, resource_spec: KernelResourceSpec, environ: MutableMapping[str, str]
    ) -> None:
        arch = get_arch_name()
        for device_name, computer_ctx in self.computers.items():
            hooks = await computer_ctx.instance.get_hooks(self.distro, arch)
            if hooks:
                raise AcceleratorHooksRefused(extra_msg=f"{device_name}: {hooks}")

    @override
    async def apply_accelerator_allocation(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        if computer.key != DeviceName("cuda"):
            return
        self._char_devices = resolve_char_devices([*device_alloc.get(SlotName("cuda.device"), {})])

    @override
    async def generate_accelerator_mounts(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> list[MountInfo]:
        return []

    @override
    def resolve_krunner_filepath(self, filename: str) -> Path:
        raise AcceleratorHooksRefused(
            extra_msg=f"the confidential path injects nothing from the host ({filename})"
        )

    @override
    def get_runner_mount(
        self,
        type: MountTypes,
        src: str | Path,
        target: str | Path,
        perm: MountPermission = MountPermission.READ_ONLY,
        opts: Mapping[str, Any] | None = None,
    ) -> Mount:
        raise AcceleratorHooksRefused(
            extra_msg=f"the confidential path injects nothing from the host ({target})"
        )

    @override
    async def prepare_container(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports: list[ServicePort],
        cluster_info: ClusterInfo,
    ) -> CocoKernel:
        return CocoKernel(
            self.ownership_data,
            self.kernel_config["network_id"],
            self.image_ref,
            self.kspec_version,
            agent_config=self.local_config.model_dump(by_alias=True),
            service_ports=service_ports,
            resource_spec=resource_spec,
            environ=environ,
            data={},
        )

    def _labels(self, kernel_obj: AbstractKernel, network: SessionNetwork) -> dict[str, str]:
        return {
            LabelName.AGENT_ID: str(self.agent_id),
            LabelName.OWNER_AGENT: str(self.agent_id),
            LabelName.KERNEL_ID: str(self.kernel_id),
            LabelName.SESSION_ID: str(self.session_id),
            LabelName.OWNER_USER: self.ownership_data.owner_user_id_to_str or "",
            LabelName.OWNER_PROJECT: self.ownership_data.owner_project_id_to_str or "",
            ALLOC_LABEL: encode_allocations(kernel_obj.resource_spec.allocations),
            RESOURCE_SPEC_LABEL: kernel_obj.resource_spec.write_to_string(),
            SERVICE_PORTS_LABEL: dump_json_str(kernel_obj.service_ports),
            GUEST_ADDR_LABEL: str(network.guest_addr),
            IMAGE_LABEL: dump_json_str({
                "canonical": self.image_ref.canonical,
                "project": self.image_ref.project,
                "registry": self.image_ref.registry,
                "architecture": self.image_ref.architecture,
            }),
            NETWORK_ID_LABEL: self.kernel_config["network_id"],
            KERNELSPEC_LABEL: str(self.kspec_version),
        }

    @override
    async def start_container(
        self,
        kernel_obj: AbstractKernel,
        cmdargs: list[str],
        resource_opts: Mapping[str, Any] | None,
        preopen_ports: list[int],
        cluster_info: ClusterInfo,
    ) -> Mapping[str, Any]:
        network = self.network
        if network is None:
            raise NetworkSetupFailed(extra_msg="apply_network did not run before start_container")
        image = self.kernel_config["image"]
        digest = await self.runtime.resolve_image(image["canonical"], image.get("digest") or "")
        blob = self.blob_store.select(digest)
        cpu_alloc = kernel_obj.resource_spec.allocations.get(DeviceName("cpu"), {})
        cpuset = ",".join(sorted(str(core) for core in cpu_alloc.get(SlotName("cpu"), {})))
        confidential = self.internal_data.get("confidential") or {}
        if self.internal_data.get("sudo_session_enabled"):
            raise HostPrivilegeWriteRefused(
                extra_msg=(
                    f"kernel {self.kernel_id} asked for a per-session root grant; under the"
                    " confidential runtime that privilege is a measured image property the guest"
                    " applies to itself, and the host writes nothing into the container"
                )
            )
        env = dict(kernel_obj.environ)
        if confidential.get("config_resource"):
            env["BACKENDAI_CC_CONFIG_URI"] = confidential["config_resource"]
        if confidential.get("secrets_resource"):
            env["BACKENDAI_CC_SECRETS_URI"] = confidential["secrets_resource"]
        if confidential.get("tunnel_resource") and confidential.get("peers_resource"):
            env["BACKENDAI_CC_TUNNEL_URI"] = confidential["tunnel_resource"]
            env["BACKENDAI_CC_PEERS_URI"] = confidential["peers_resource"]
            env["BACKENDAI_CC_TUNNEL_BASE"] = str(network.subnet[2])
        if confidential.get("channel_resource"):
            env["BACKENDAI_CC_CHANNEL_URI"] = confidential["channel_resource"]
        plan_resource = confidential.get("mount_plan_resource")
        if not plan_resource:
            raise MountPlanMissing(extra_msg=str(self.kernel_id))
        env["BACKENDAI_CC_MOUNT_PLAN_URI"] = plan_resource
        spec = ContainerSpec(
            name=f"kernel.{self.kernel_id}",
            image=self.image_ref.canonical,
            hostname=self.kernel_config["cluster_hostname"],
            command=cmdargs,
            netns_path=network.netns_path,
            runtime=self.settings.runtime_class,
            memory_bytes=self._container_memory,
            cpuset=cpuset,
            dns_servers=self.settings.dns_servers,
            entrypoint=GUEST_ENTRYPOINT,
            env=env,
            labels=self._labels(kernel_obj, network),
            annotations=build_annotations(
                self.settings.blob_annotation_key,
                blob.annotation_value,
                self.image_ref.canonical,
            ),
            devices=self._char_devices,
            block_devices=[(v.loop, v.guest_path) for v in self._block_volumes],
            mounts=[*guest_sourced_mounts(), *self._mounts],
        )
        log.info(
            "starting confidential kernel {} on {} with blob {} and devices {}",
            self.kernel_id,
            network.guest_addr,
            blob.content_address,
            [str(device) for device in self._char_devices],
        )
        container_id = await self.runtime.create(spec)
        try:
            await self.runtime.start(container_id)
            await self.runtime.wait_running(container_id, self.settings.container_start_timeout)
            await _wait_for_port(
                str(network.guest_addr), CHANNEL_PORT, self.settings.attestation_timeout
            )
        except Exception as e:
            raise ContainerCreationError(container_id, str(e)) from e
        for service_port in kernel_obj.service_ports:
            service_port["host_ports"] = tuple(service_port["container_ports"])
        return {
            "container_id": container_id,
            "kernel_host": str(network.guest_addr),
            "repl_in_port": 0,
            "repl_out_port": 0,
            "channel_port": CHANNEL_PORT,
            "channel_relay_addr": f"{self.settings.relay_bind_host}:{self.settings.relay_bind_port}",
            "channel_resource": (self.internal_data.get("confidential") or {}).get(
                "channel_resource"
            ),
            "stdin_port": 0,
            "stdout_port": 0,
            "host_ports": [],
            "domain_socket_proxies": [],
            "block_service_ports": self.internal_data.get("block_service_ports", False),
            "measured_blob": blob.content_address,
        }


class CocoAgent(AbstractAgent[CocoKernel, CocoKernelCreationContext]):
    settings: CocoSettings
    runtime: AbstractRuntimeClient
    network_manager: SessionNetworkManager
    blob_store: MeasuredBlobStore
    volumes: BlockVolumeManager
    relay: ChannelRelay
    _metering_task: asyncio.Task[None] | None

    @override
    async def __ainit__(self) -> None:
        self.settings = build_settings(self.local_config)
        self.runtime = NerdctlClient(
            RuntimeConfig(
                binary=self.local_config.confidential.nerdctl_path,
                address=self.local_config.confidential.containerd_address,
                namespace=self.settings.containerd_namespace,
            )
        )
        self.network_manager = SessionNetworkManager(build_network_config(self.local_config))
        self.blob_store = MeasuredBlobStore(self.settings.blob_store_path)
        self.volumes = BlockVolumeManager(
            self.settings.block_volume_root,
            self.settings.scratch_volume_size,
            self.settings.image_store_volume_size,
        )
        self.relay = ChannelRelay(
            self.settings.relay_bind_host, self.settings.relay_bind_port, self._resolve_circuit
        )
        await self.relay.start()
        self._metering_task = asyncio.create_task(self._report_activity())
        await super().__ainit__()

    async def _resolve_circuit(self, kernel_id: str, port: int) -> Circuit:
        kernel_obj = self.kernel_registry.get(KernelId(UUID(kernel_id)))
        if kernel_obj is None:
            raise KernelNotFoundError(f"no live kernel {kernel_id} on this agent")
        if port != CHANNEL_PORT:
            allowed = {
                sport["name"]
                for sport in kernel_obj.service_ports
                if port in sport["container_ports"]
            }
            permitted = self.settings.raw_circuit_allowlist | SELF_ENCRYPTING_SERVICES
            if not allowed or not (allowed & permitted):
                raise RawCircuitRefused(
                    extra_msg=(
                        f"port {port} on kernel {kernel_id} carries no guest-terminated scheme and"
                        f" names no self-encrypting service in {sorted(permitted)}"
                    )
                )
        return Circuit(
            guest_host=str(kernel_obj.data["kernel_host"]),
            guest_port=port,
            session_id=str(kernel_obj.session_id),
        )

    async def _report_activity(self) -> None:
        while True:
            await asyncio.sleep(ACTIVITY_REPORT_INTERVAL)
            now = time.monotonic()
            for kernel_id, flow in list(self.relay.flows.items()):
                if KernelId(UUID(kernel_id)) not in self.kernel_registry:
                    self.relay.forget(kernel_id)
                    continue
                await self.anycast_event(
                    SessionChannelActivityAnycastEvent(
                        session_id=SessionId(UUID(flow.session_id)),
                        open_circuits=flow.circuits,
                        bytes_moved=flow.bytes_in + flow.bytes_out,
                        idle_seconds=now - flow.last_activity,
                    )
                )

    @override
    async def shutdown(self, stop_signal: signal.Signals) -> None:
        if self._metering_task is not None:
            self._metering_task.cancel()
            self._metering_task = None
        await self.relay.close()
        await super().shutdown(stop_signal)

    def _rebuild_kernel(self, container: Container) -> CocoKernel | None:
        labels = container.labels
        try:
            resource_spec = KernelResourceSpec.read_from_string(labels[RESOURCE_SPEC_LABEL])
            ownership_data = KernelOwnershipData(
                kernel_id=KernelId(UUID(labels[LabelName.KERNEL_ID])),
                session_id=SessionId(UUID(labels[LabelName.SESSION_ID])),
                agent_id=self.id,
                owner_user_id=_optional_uuid(labels.get(LabelName.OWNER_USER)),
                owner_project_id=_optional_uuid(labels.get(LabelName.OWNER_PROJECT)),
            )
            guest_addr = labels[GUEST_ADDR_LABEL]
            image = load_json(labels[IMAGE_LABEL])
            kernel = CocoKernel(
                ownership_data,
                labels.get(NETWORK_ID_LABEL, ""),
                ImageRef.from_image_str(
                    image["canonical"],
                    image["project"],
                    image["registry"],
                    architecture=image["architecture"],
                ),
                int(labels.get(KERNELSPEC_LABEL, "1")),
                agent_config=self.local_config.model_dump(by_alias=True),
                service_ports=load_json(labels.get(SERVICE_PORTS_LABEL, "[]")),
                resource_spec=resource_spec,
                environ={},
                data={
                    "kernel_host": guest_addr,
                    "repl_in_port": 0,
                    "repl_out_port": 0,
                    "channel_port": CHANNEL_PORT,
                    "stdin_port": 0,
                    "stdout_port": 0,
                    "host_ports": [],
                    "domain_socket_proxies": [],
                },
            )
        except (KeyError, ValueError) as e:
            log.warning("cannot reconstruct a kernel from container {}: {}", container.id, e)
            return None
        kernel.set_container_id(container.id)
        return kernel

    @override
    async def _load_kernel_registry_from_recovery(self) -> MutableMapping[KernelId, AbstractKernel]:
        recovered: MutableMapping[KernelId, AbstractKernel] = {}
        for kernel_id, container in await self.enumerate_containers(ACTIVE_STATUS_SET):
            kernel = self._rebuild_kernel(container)
            if kernel is not None:
                recovered[kernel_id] = kernel
        log.info("recovered {} confidential kernels from container labels", len(recovered))
        return recovered

    @override
    async def _write_kernel_registry_to_recovery(
        self,
        kernel_registry: MutableMapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
    ) -> None:
        pass

    @override
    async def enumerate_containers(
        self,
        status_filter: frozenset[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> Sequence[tuple[KernelId, Container]]:
        container_ids = await self.runtime.list_ids({LabelName.OWNER_AGENT: str(self.id)})
        found: list[tuple[KernelId, Container]] = []
        for entry in await self.runtime.inspect(container_ids):
            labels = (entry.get("Config") or {}).get("Labels") or {}
            raw_kernel_id = labels.get(LabelName.KERNEL_ID)
            if not raw_kernel_id:
                continue
            raw_status = str((entry.get("State") or {}).get("Status", "")).lower()
            try:
                status = ContainerStatus(raw_status)
            except ValueError:
                status = ContainerStatus.DEAD
            if status not in status_filter:
                continue
            guest_addr = labels.get(GUEST_ADDR_LABEL, "")
            found.append((
                KernelId(UUID(raw_kernel_id)),
                Container(
                    id=ContainerId(entry["Id"]),
                    status=status,
                    image=str((entry.get("Config") or {}).get("Image", "")),
                    labels=labels,
                    ports=[
                        Port(guest_addr, CHANNEL_PORT, CHANNEL_PORT),
                    ],
                    backend_obj=entry,
                ),
            ))
        return found

    @override
    async def resolve_image_distro(self, image: ImageConfig) -> str:
        distro = image["labels"].get(LabelName.BASE_DISTRO)
        if not distro:
            raise ImageDistroUnresolved(extra_msg=image["canonical"])
        return distro

    @override
    def get_cgroup_path(self, controller: str, container_id: str) -> Path:
        mount_point = get_cgroup_mount_point(self.get_cgroup_version(), controller)
        return mount_point / self.settings.containerd_namespace / container_id

    @override
    def get_cgroup_version(self) -> str:
        return "2" if Path("/sys/fs/cgroup/cgroup.controllers").exists() else "1"

    @override
    async def extract_image_command(self, image: str) -> list[str] | None:
        return None

    @override
    async def scan_images(self) -> ScanImagesResult:
        return ScanImagesResult(scanned_images={}, removed_images={})

    @override
    async def push_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout_seconds: float | None | Sentinel = Sentinel.TOKEN,
    ) -> None:
        raise ImagePushRefused(extra_msg=image_ref.canonical)

    @override
    async def pull_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout_seconds: float | None,
    ) -> None:
        log.debug("skipping host pull of {}; the guest pulls its own image", image_ref.canonical)

    @override
    async def purge_images(self, request: PurgeImagesReq) -> PurgeImagesResp:
        return PurgeImagesResp([])

    @override
    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        return False

    @override
    async def init_kernel_context(
        self,
        ownership_data: KernelOwnershipData,
        kernel_image: ImageRef,
        kernel_config: KernelCreationConfig,
        *,
        restarting: bool = False,
        cluster_ssh_port_mapping: ClusterSSHPortMapping | None = None,
    ) -> CocoKernelCreationContext:
        distro = await self.resolve_image_distro(kernel_config["image"])
        return CocoKernelCreationContext(
            ownership_data,
            self.event_producer,
            kernel_image,
            kernel_config,
            distro,
            self.local_config,
            self.computers,
            restarting=restarting,
            settings=self.settings,
            blob_store=self.blob_store,
            runtime=self.runtime,
            network_manager=self.network_manager,
            volumes=self.volumes,
        )

    async def _session_id_of(self, kernel_id: KernelId) -> SessionId | None:
        kernel_obj = self.kernel_registry.get(kernel_id)
        if kernel_obj is not None:
            return kernel_obj.session_id
        for found_id, container in await self.enumerate_containers(
            ACTIVE_STATUS_SET | ContainerStatus.dead_set()
        ):
            if found_id == kernel_id:
                raw = container.labels.get(LabelName.SESSION_ID)
                return SessionId(UUID(raw)) if raw else None
        return None

    @override
    async def destroy_kernel(self, kernel_id: KernelId, container_id: ContainerId | None) -> None:
        if container_id is None:
            return
        await self.runtime.kill(str(container_id), "SIGINT")

    @override
    async def clean_kernel(
        self, kernel_id: KernelId, container_id: ContainerId | None, restarting: bool
    ) -> None:
        session_id = await self._session_id_of(kernel_id)
        if container_id is not None:
            await self.runtime.delete(str(container_id), force=True)
        await self.volumes.release(kernel_id)
        self.relay.forget(str(kernel_id))
        if restarting or session_id is None:
            return
        await self.network_manager.destroy(kernel_id, session_id)

    @override
    async def create_local_network(self, network_name: str) -> None:
        pass

    @override
    async def destroy_local_network(self, network_name: str) -> None:
        pass

    @override
    async def restart_kernel__load_config(self, kernel_id: KernelId, name: str) -> bytes:
        raise HostConfigReadbackRefused(extra_msg=f"{kernel_id}/{name}")

    @override
    async def restart_kernel__store_config(
        self, kernel_id: KernelId, name: str, data: bytes
    ) -> None:
        log.debug("dropping host-side kernel config {} for {}", name, kernel_id)

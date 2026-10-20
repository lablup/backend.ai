from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from decimal import Decimal
from importlib.resources import files
from pathlib import Path
from typing import Any, override

from ai.backend.agent.agent import (
    ACTIVE_STATUS_SET,
    AbstractAgent,
    AbstractKernelCreationContext,
    ScanImagesResult,
)
from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.errors import UnsupportedResource
from ai.backend.agent.errors.agent import UnsupportedBaseDistroError
from ai.backend.agent.errors.containerd import KernelVerbNotSupported
from ai.backend.agent.etcd import AgentEtcdClientView
from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.kernel_registry.writer.types import KernelRegistrySaveMetadata
from ai.backend.agent.resources import (
    AbstractComputePlugin,
    ComputerContext,
    KernelResourceSpec,
    Mount,
    known_slot_types,
)
from ai.backend.agent.types import Container, KernelOwnershipData, MountInfo
from ai.backend.common.cgroup import CgroupController
from ai.backend.common.docker import ImageRef, LabelName
from ai.backend.common.dto.agent.response import PurgeImagesResp
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import (
    AutoPullBehavior,
    ClusterInfo,
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
    SlotName,
    current_resource_slots,
)
from ai.backend.logging.structured import StructuredLogger

from .kernel import ContainerdKernel
from .profile.base import KernelLaunch, RuntimeProfile
from .profile.loader import load_runtime_profiles, select_profile
from .profile.runc import RuncProfile

log = StructuredLogger(logging.getLogger(__spec__.name))


def _kernel_slots(kernel_config: KernelCreationConfig) -> Mapping[SlotName, Decimal]:
    return {
        SlotName(k): v for k, v in ResourceSlot.from_json(kernel_config["resource_slots"]).items()
    }


class ContainerdKernelCreationContext(AbstractKernelCreationContext[ContainerdKernel]):
    _profile: RuntimeProfile
    _slots: Mapping[SlotName, Decimal]
    _mounts: list[Mount]

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
        profile: RuntimeProfile,
        slots: Mapping[SlotName, Decimal],
    ) -> None:
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
        self._profile = profile
        self._slots = slots
        self._mounts = []

    @override
    async def get_extra_envs(self) -> Mapping[str, str]:
        return {}

    @override
    async def prepare_resource_spec(
        self,
    ) -> tuple[KernelResourceSpec, Mapping[str, Any] | None]:
        if self.restarting:
            raise KernelVerbNotSupported("restart_kernel")
        slots = ResourceSlot.from_json(self.kernel_config["resource_slots"])
        # Ensure that we have intrinsic slots.
        if SlotName("cpu") not in slots:
            raise UnsupportedResource("cpu slot is required")
        if SlotName("mem") not in slots:
            raise UnsupportedResource("mem slot is required")
        # accept unknown slot type with zero values
        # but reject if they have non-zero values.
        for st, sv in slots.items():
            if st not in known_slot_types and sv != Decimal(0):
                raise UnsupportedResource(st)
        # sanitize the slots
        current_resource_slots.set(known_slot_types)
        slots = slots.normalize_slots(ignore_unknown=True)
        resource_spec = KernelResourceSpec(
            allocations={},
            slots=slots.copy(),
            mounts=[],
            scratch_disk_size=0,  # TODO: implement (#70)
        )
        resource_opts = self.kernel_config.get("resource_opts", {})
        return resource_spec, resource_opts

    # FIXME(containerd-mvp): scratch/config dirs (and the TD loop file) are not created;
    # placeholder, needs the containerd client
    @override
    async def prepare_scratch(self) -> None:
        raise KernelVerbNotSupported("prepare_scratch is not implemented yet")

    # FIXME(containerd-mvp): intrinsic mounts are not generated; placeholder, needs the
    # containerd client
    @override
    async def get_intrinsic_mounts(self) -> Sequence[Mount]:
        raise KernelVerbNotSupported("get_intrinsic_mounts is not implemented yet")

    @property
    @override
    def repl_ports(self) -> Sequence[int]:
        raise KernelVerbNotSupported("repl_ports")

    @property
    @override
    def protected_services(self) -> Sequence[str]:
        raise KernelVerbNotSupported("protected_services")

    # FIXME(containerd-mvp): the network is not applied; placeholder until netns/DNAT lands
    @override
    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        raise KernelVerbNotSupported("apply_network is not implemented yet")

    # FIXME(containerd-mvp): cluster SSH keys are not installed
    @override
    async def prepare_ssh(self, cluster_info: ClusterInfo) -> None:
        return None

    # Stored for the spec builder, which consumes the mounts once it lands.
    @override
    async def process_mounts(self, mounts: Sequence[Mount]) -> None:
        self._mounts = list(mounts)

    # FIXME(containerd-mvp): devices are not applied; placeholder until device translation lands
    @override
    async def apply_accelerator_allocation(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        raise KernelVerbNotSupported("apply_accelerator_allocation is not implemented yet")

    # FIXME(containerd-mvp): accelerator mounts are not generated; placeholder, needs device
    # translation
    @override
    async def generate_accelerator_mounts(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> list[MountInfo]:
        raise KernelVerbNotSupported("generate_accelerator_mounts is not implemented yet")

    @override
    def resolve_krunner_filepath(self, filename: str) -> Path:
        return Path(str(files("ai.backend.runner").joinpath("../" + filename))).resolve()

    @override
    def get_runner_mount(
        self,
        type: MountTypes,
        src: str | Path,
        target: str | Path,
        perm: MountPermission = MountPermission.READ_ONLY,
        opts: Mapping[str, Any] | None = None,
    ) -> Mount:
        return Mount(
            type,
            Path(src),
            Path(target),
            MountPermission(perm),
            opts=opts,
        )

    @override
    async def prepare_container(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports: list[ServicePort],
        cluster_info: ClusterInfo,
    ) -> ContainerdKernel:
        launch = KernelLaunch(
            kernel_id=self.kernel_id,
            session_id=self.session_id,
            config=self.kernel_config,
            slots=self._slots,
            # FIXME(containerd-mvp): devices, mounts and base_spec are empty until the spec
            # builder and device translation land; profiles see no host mounts or devices
            devices=(),
            mounts=(),
            trusted_storage_path=None,
            base_spec={},
        )
        launch_plan = self._profile.plan(launch)
        return ContainerdKernel(
            self.ownership_data,
            self.kernel_config["network_id"],
            self.image_ref,
            self.kspec_version,
            agent_config=self.local_config.model_dump(by_alias=True),
            resource_spec=resource_spec,
            service_ports=service_ports,
            environ=environ,
            data={},
            launch_plan=launch_plan,
        )

    # FIXME(containerd-mvp): no container is started; placeholder until the containerd client lands
    @override
    async def start_container(
        self,
        kernel_obj: AbstractKernel,
        cmdargs: list[str],
        resource_opts: Mapping[str, Any] | None,
        preopen_ports: Sequence[int],
        cluster_info: ClusterInfo,
    ) -> Mapping[str, Any]:
        raise KernelVerbNotSupported("start_container is not implemented yet")


class ContainerdAgent(
    AbstractAgent[ContainerdKernel, ContainerdKernelCreationContext],
):
    _runtime_profiles: list[RuntimeProfile]
    _profile_required_slots: frozenset[SlotName]
    _runc_profile: RuncProfile

    def __init__(
        self,
        etcd: AgentEtcdClientView,
        local_config: AgentUnifiedConfig,
        **kwargs: Any,
    ) -> None:
        # Load first: a bad profile must stop the agent before any background task starts.
        containerd_config = local_config.containerd
        runtime_profiles = load_runtime_profiles(
            containerd_config.runtime_profiles, containerd_config.profiles
        )
        super().__init__(etcd, local_config, **kwargs)
        self._runtime_profiles = runtime_profiles
        self._profile_required_slots = frozenset(
            SlotName(s) for s in containerd_config.profile_required_slots
        )
        self._runc_profile = RuncProfile(local_config.kernel_lifecycles.init_timeout_sec)

    # FIXME(containerd-mvp): kernel recovery is not supported; an agent restart destroys
    # running kernels
    @override
    async def _load_kernel_registry_from_recovery(self) -> dict[KernelId, AbstractKernel]:
        log.warning("kernel registry recovery skipped")
        return {}

    # FIXME(containerd-mvp): the kernel registry is not persisted
    @override
    async def _write_kernel_registry_to_recovery(
        self,
        kernel_registry: Mapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
    ) -> None:
        return None

    # FIXME(containerd-mvp): containers are not listed; placeholder, needs the containerd client
    @override
    async def enumerate_containers(
        self,
        status_filter: frozenset[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> Sequence[tuple[KernelId, Container]]:
        return []

    @override
    async def resolve_image_distro(self, image: ImageConfig) -> str:
        distro = image["labels"].get(LabelName.BASE_DISTRO)
        if not distro:
            raise UnsupportedBaseDistroError(
                f"image {image['canonical']} has no {LabelName.BASE_DISTRO} label"
            )
        return distro

    @override
    async def get_cgroup_path(
        self, controller: CgroupController, container_id: ContainerId
    ) -> Path:
        raise KernelVerbNotSupported("get_cgroup_path")

    @override
    def get_cgroup_version(self) -> str:
        raise KernelVerbNotSupported("get_cgroup_version")

    @override
    async def extract_image_command(self, image: str) -> list[str] | None:
        raise KernelVerbNotSupported("extract_image_command")

    # FIXME(containerd-mvp): installed images are not reported to the manager
    @override
    async def scan_images(self) -> ScanImagesResult:
        return ScanImagesResult(scanned_images={}, removed_images={})

    @override
    async def pull_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout_seconds: float | None,
    ) -> None:
        raise KernelVerbNotSupported("pull_image")

    @override
    async def push_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout_seconds: float | None | Sentinel = Sentinel.TOKEN,
    ) -> None:
        raise KernelVerbNotSupported("push_image")

    @override
    async def purge_images(self, request: PurgeImagesReq) -> PurgeImagesResp:
        raise KernelVerbNotSupported("purge_images")

    # FIXME(containerd-mvp): the host never pulls; runc images must be imported beforehand
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
    ) -> ContainerdKernelCreationContext:
        slots = _kernel_slots(kernel_config)
        profile = select_profile(
            self._runtime_profiles,
            self._profile_required_slots,
            slots,
            builtin=self._runc_profile,
        )
        log.debug(
            "runtime profile selected",
            kernel_id=str(ownership_data.kernel_id),
            profile=profile.name,
        )
        distro = await self.resolve_image_distro(kernel_config["image"])
        return ContainerdKernelCreationContext(
            ownership_data,
            self.event_producer,
            kernel_image,
            kernel_config,
            distro,
            self.local_config,
            self.computers,
            restarting=restarting,
            profile=profile,
            slots=slots,
        )

    # FIXME(containerd-mvp): no container is destroyed; placeholder, needs the containerd client
    @override
    async def destroy_kernel(
        self,
        kernel_id: KernelId,
        container_id: ContainerId | None,
    ) -> None:
        return None

    # FIXME(containerd-mvp): no container is cleaned; placeholder until the containerd client lands
    @override
    async def clean_kernel(
        self,
        kernel_id: KernelId,
        container_id: ContainerId | None,
        restarting: bool,
    ) -> None:
        return None

    @override
    async def create_local_network(self, network_name: str) -> None:
        raise KernelVerbNotSupported("create_local_network")

    @override
    async def destroy_local_network(self, network_name: str) -> None:
        raise KernelVerbNotSupported("destroy_local_network")

    @override
    async def restart_kernel__load_config(
        self,
        kernel_id: KernelId,
        name: str,
    ) -> bytes:
        raise KernelVerbNotSupported("restart_kernel__load_config")

    # FIXME(containerd-mvp): restart configs are not stored
    @override
    async def restart_kernel__store_config(
        self,
        kernel_id: KernelId,
        name: str,
        data: bytes,
    ) -> None:
        return None

"""Containerd agent backend (BEP-1055).

An independent agent backend parallel to DockerAgent, targeting containerd's native
gRPC/task model instead of the Docker daemon. This is a structural scaffold: the
container-facing operations (image scan/pull, task create/start, destroy) raise
``NotImplementedError`` pending the containerd gRPC client; the runtime-agnostic parts
(resource spec, registration, kernel context wiring) are real.

Cluster networking is provided by the BEP-1055 runtime-neutral stack
(``agent.network``): the SessionNetworkCoordinator handles per-session setup and the
ContainerNetworkProvisioner attaches each container's task PID via CNI.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import subprocess
from collections.abc import Mapping, Sequence
from decimal import Decimal
from importlib.resources import files
from pathlib import Path
from typing import Any, override

from ai.backend.agent.agent import (
    AbstractAgent,
    AbstractKernelCreationContext,
    ScanImagesResult,
)
from ai.backend.agent.errors import UnsupportedResource
from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.kernel_registry.writer.types import KernelRegistrySaveMetadata
from ai.backend.agent.network.caps import publish_vtep
from ai.backend.agent.resources import (
    AbstractComputePlugin,
    ComputerContext,
    KernelResourceSpec,
    Mount,
    known_slot_types,
)
from ai.backend.agent.types import Container, KernelOwnershipData, MountInfo
from ai.backend.common.arch import CURRENT_ARCH
from ai.backend.common.docker import ImageRef, LabelName
from ai.backend.common.dto.agent.response import PurgeImageResp, PurgeImagesResp
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.exception import ImageNotAvailable
from ai.backend.common.json import dump_json_str
from ai.backend.common.network.types import SessionNetMeta
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
from ai.backend.logging import BraceStyleAdapter

from .kernel import ContainerdKernel
from .oci import KRUNNER_ENTRYPOINT, translate_creation_config
from .session_network import (
    ContainerdSessionNetwork,
    build_containerd_session_network,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_TODO = "containerd backend: not yet implemented (requires containerd gRPC client)"


def _uplink_for_ip(host_ip: str) -> str:
    """Resolve the local interface that owns ``host_ip`` (the VTEP address).

    The vxlan device must be created on the interface carrying the node's advertised
    (VTEP) IP so the overlay rides the same L2 the agents reach each other on. Falls back
    to ``eth0`` if no interface matches (single-node / misconfiguration)."""
    import socket

    import psutil

    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET and addr.address == host_ip:
                return iface
    return "eth0"


class ContainerdKernelCreationContext(AbstractKernelCreationContext[ContainerdKernel]):
    _session_network: ContainerdSessionNetwork
    _net_meta: SessionNetMeta | None
    _container_id: str
    _session_id: str
    _oci_mounts: list[Mount]
    _scratch_dir: Path | None
    _pending_spec: Any

    def __init__(
        self,
        ownership_data: KernelOwnershipData,
        event_producer: EventProducer,
        kernel_image: ImageRef,
        kernel_config: KernelCreationConfig,
        distro: str,
        local_config: Any,
        computers: Mapping[DeviceName, ComputerContext],
        restarting: bool = False,
        *,
        session_network: ContainerdSessionNetwork,
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
        self._session_network = session_network
        self._net_meta = None
        self._container_id = str(kernel_config["kernel_id"])
        self._session_id = str(kernel_config["session_id"])
        self._oci_mounts = []
        self._pending_spec = None
        self._scratch_dir = None

    @override
    async def get_extra_envs(self) -> Mapping[str, str]:
        return {}

    @override
    async def prepare_resource_spec(
        self,
    ) -> tuple[KernelResourceSpec, Mapping[str, Any] | None]:
        slots = ResourceSlot.from_json(self.kernel_config["resource_slots"])
        if SlotName("cpu") not in slots:
            raise UnsupportedResource("cpu slot is required")
        if SlotName("mem") not in slots:
            raise UnsupportedResource("mem slot is required")
        for st, sv in slots.items():
            if st not in known_slot_types and sv != Decimal(0):
                raise UnsupportedResource(st)
        current_resource_slots.set(known_slot_types)
        slots = slots.normalize_slots(ignore_unknown=True)
        resource_spec = KernelResourceSpec(
            allocations={},
            slots=slots.copy(),
            mounts=[],
            scratch_disk_size=0,
        )
        resource_opts = self.kernel_config.get("resource_opts", {})
        return resource_spec, resource_opts

    @override
    async def prepare_scratch(self) -> None:
        # Create the per-kernel scratch dirs (config/ + work/). Full parity (tmpfs/loop
        # scratch types, dotfile cloning) is a follow-up.
        scratch_dir = (self.local_config.container.scratch_root / str(self._container_id)).resolve()
        config_dir = scratch_dir / "config"
        work_dir = scratch_dir / "work"

        def _mkdirs() -> None:
            config_dir.mkdir(parents=True, exist_ok=True)
            work_dir.mkdir(parents=True, exist_ok=True)

        await asyncio.to_thread(_mkdirs)
        self._scratch_dir = scratch_dir

    @override
    async def get_intrinsic_mounts(self) -> Sequence[Mount]:
        # The kernel runner requires the per-kernel scratch dirs: config/ (RO) at
        # /home/config and work/ (RW) at /home/work. prepare_scratch created them.
        # (lxcfs, /etc/localtime, coredump, domain-socket proxies are follow-ups.)
        scratch_dir = (self.local_config.container.scratch_root / str(self._container_id)).resolve()
        return [
            Mount(
                MountTypes.BIND,
                scratch_dir / "config",
                Path("/home/config"),
                MountPermission.READ_ONLY,
            ),
            Mount(
                MountTypes.BIND,
                scratch_dir / "work",
                Path("/home/work"),
                MountPermission.READ_WRITE,
            ),
        ]

    @property
    @override
    def repl_ports(self) -> Sequence[int]:
        return (2000, 2001)

    @property
    @override
    def protected_services(self) -> Sequence[str]:
        return ()

    @override
    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        # BEP-1055: set up this node's per-session data plane (vxlan/bridge + membership)
        # and register the per-session orchestrator. Per-container CNI attach happens in
        # start_container against the task PID. Single-node sessions without a manager-
        # provided network_config skip this.
        network_config = cluster_info.get("network_config") or {}
        if not network_config.get("backend"):
            return
        self._net_meta = await self._session_network.ensure_session(
            self._session_id, network_config
        )

    @override
    async def prepare_ssh(self, cluster_info: ClusterInfo) -> None:
        # Provision the cluster SSH material into config/ssh (mounted at /home/config/ssh)
        # for PARITY with DockerAgent: the id_cluster keypair enables passwordless
        # chief<->worker SSH that distributed workloads (MPI/torchrun/bssh) rely on, and
        # port-mapping.json carries the cluster SSH port map. This is NOT required for the
        # kernel to reach RUNNING (verified: the container's own dropbear self-generates its
        # host key and the runner does not consume id_cluster at startup) — it is the
        # multi-node cluster-session contract for user workloads. Best-effort throughout.
        if self._scratch_dir is None:
            return
        scratch_dir = self._scratch_dir
        sshkey = cluster_info.get("ssh_keypair")
        port_mapping = cluster_info.get("cluster_ssh_port_mapping")

        def _write() -> None:
            ssh_dir = scratch_dir / "config" / "ssh"
            ssh_dir.mkdir(parents=True, exist_ok=True)
            if sshkey is not None:
                priv = ssh_dir / "id_cluster"
                priv.write_text(sshkey["private_key"])
                priv.chmod(0o600)
                (ssh_dir / "id_cluster.pub").write_text(sshkey["public_key"])
            if port_mapping is not None:
                (ssh_dir / "port-mapping.json").write_text(dump_json_str(port_mapping))
            host_key = ssh_dir / "dropbear_rsa_host_key"
            if not host_key.is_file():
                dropbear = self.resolve_krunner_filepath(f"runner/dropbearmulti.{CURRENT_ARCH}.bin")
                if dropbear.exists():
                    try:
                        subprocess.run(
                            [str(dropbear), "dropbearkey", "-t", "rsa", "-s", "2048",
                             "-f", str(host_key)],
                            check=True, capture_output=True,
                        )  # fmt: skip
                        host_key.chmod(0o600)
                    except subprocess.CalledProcessError:
                        log.debug(
                            "dropbear host key generation failed; will regenerate in container"
                        )

        await asyncio.to_thread(_write)

    @override
    async def process_mounts(self, mounts: Sequence[Mount]) -> None:
        # Accumulate mounts to inject into the OCI spec at prepare_container time.
        self._oci_mounts.extend(mounts)

    @override
    async def apply_accelerator_allocation(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        # No-op for CPU/mem. GPU/accelerator device injection into the OCI spec (the
        # containerd analogue of generate_docker_args) is a follow-up.
        return

    @override
    async def generate_accelerator_mounts(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> list[MountInfo]:
        return []

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
        return Mount(type, Path(src), Path(target), MountPermission(perm), opts=opts)

    @override
    async def prepare_container(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports: list[ServicePort],
        cluster_info: ClusterInfo,
    ) -> ContainerdKernel:
        # Build (but do NOT create) the container spec + kernel object. mount_krunner
        # (inherited) has populated resource_spec.mounts with the krunner bind mounts;
        # combine with process_mounts' vfolder mounts and inject them (plus env/labels)
        # into the OCI spec. Container creation is deferred to start_container, where the
        # kernel-runner cmdargs (which the container command must exec) are available.
        all_mounts = [*resource_spec.mounts, *self._oci_mounts]
        self._pending_spec = translate_creation_config(
            self.kernel_config, environ=environ, mounts=all_mounts
        )
        return ContainerdKernel(
            self.ownership_data,
            self.kernel_config["network_id"],
            self.image_ref,
            self.kspec_version,
            agent_config=self.local_config.model_dump(by_alias=True),
            service_ports=service_ports,
            resource_spec=resource_spec,
            environ=environ,
            data={"container_id": self._container_id},
        )

    @override
    async def start_container(
        self,
        kernel_obj: AbstractKernel,
        cmdargs: list[str],
        resource_opts: Mapping[str, Any] | None,
        preopen_ports: Sequence[int],
        cluster_info: ClusterInfo,
    ) -> Mapping[str, Any]:
        # The container command = krunner entrypoint + the kernel-runner cmdargs (only known
        # here), which the entrypoint execs to launch the REPL. Create the container now,
        # then start it.
        spec = self._pending_spec
        command = [KRUNNER_ENTRYPOINT, *cmdargs]
        if self._net_meta is None:
            # single-node: plain bridge network (no BEP-1055 overlay), like Docker.
            await self._session_network.create_local_container(
                self._session_id,
                self._container_id,
                image_ref=spec.image_ref,
                command=command,
                oci_spec=spec.oci_spec,
            )
            # start on the bridge; kernel_host = container's bridge IP.
            task_pid, ip = await self._session_network.start_local_container(self._container_id)
            kernel_host = ip or "127.0.0.1"
        else:
            await self._session_network.create_container(
                self._session_id,
                self._container_id,
                image_ref=spec.image_ref,
                command=command,
                oci_spec=spec.oci_spec,
            )
            # multi-node: start + attach the CNI overlay chain; kernel_host = overlay IP.
            result = await self._session_network.start_and_attach_container(
                self._session_id,
                self._container_id,
                meta=self._net_meta,
                kernel_config=self.kernel_config,
                cluster_info=cluster_info,
            )
            task_pid = result.handle.pid
            # The agent reaches the kernel's REPL over the LOCAL interface (the host is that
            # bridge's gateway); the OVERLAY IP is only reachable between kernels, not from
            # the host, so it must NOT be used as kernel_host.
            kernel_host = result.local_ip or "127.0.0.1"
        # REPL ports are the krunner intrinsic, container-internal ports (self.repl_ports);
        # the agent connects to them directly at kernel_host (the container's bridge/overlay
        # IP), so no host-port mapping is needed (cf. DockerAgent's container_network_info
        # path). stdin/stdout ports are legacy and unused (0), matching DockerAgent.
        repl_in_port, repl_out_port = self.repl_ports
        return {
            "container_id": self._container_id,
            "task_pid": task_pid,
            "kernel_host": kernel_host,
            "repl_in_port": repl_in_port,
            "repl_out_port": repl_out_port,
            "stdin_port": 0,  # legacy
            "stdout_port": 0,  # legacy
            "host_ports": [],
            "domain_socket_proxies": [],
            "block_service_ports": False,
        }

    # mount_krunner is inherited from AbstractKernelCreationContext: it populates
    # resource_spec.mounts (via get_runner_mount) and LD_PRELOAD — runtime-agnostic. The
    # accumulated mounts are injected into the OCI spec at prepare_container time.


class ContainerdAgent(
    AbstractAgent[ContainerdKernel, ContainerdKernelCreationContext],
):
    _session_network: ContainerdSessionNetwork
    _host_ip: str

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Cluster networking is delegated to the BEP-1055 agent.network stack via a
        # (verified) facade; the kernel-creation lifecycle will drive it. The vxlan uplink
        # must be the interface carrying this node's VTEP (host_ip) — deriving it from the
        # host_ip keeps the overlay on the same L2 the agents advertise on, instead of a
        # hard-coded eth0.
        container_cfg = self.local_config.container
        self._host_ip = str(container_cfg.advertised_host or container_cfg.bind_host)
        self._session_network = build_containerd_session_network(
            self.etcd,
            agent_id=str(self.id),
            host_ip=self._host_ip,
            uplink=_uplink_for_ip(self._host_ip),
        )

    @override
    async def __ainit__(self) -> None:
        await super().__ainit__()
        # Advertise this node's VTEP so the manager can pre-seed session membership and
        # eliminate the peer-publish race for multi-node overlays (BEP-1055).
        await publish_vtep(self.etcd, str(self.id), self._host_ip)

    # execute is inherited from AbstractAgent: it delegates to kernel_obj.execute (the code
    # runner's ZMQ REPL), which is runtime-agnostic. No override needed.

    @override
    async def _load_kernel_registry_from_recovery(self) -> dict[KernelId, AbstractKernel]:
        return {}

    @override
    async def _write_kernel_registry_to_recovery(
        self,
        kernel_registry: Mapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
    ) -> None:
        pass

    @override
    def get_public_service_ports(self, service_ports: list[ServicePort]) -> list[ServicePort]:
        return []

    @override
    async def sync_container_lifecycles(self) -> None:
        return

    @override
    async def enumerate_containers(
        self,
        status_filter: frozenset[ContainerStatus] = frozenset(),
    ) -> Sequence[tuple[KernelId, Container]]:
        # Boot-safe: no live-container reconciliation yet. Enumerating kernels from
        # containerd (list_containers + the ai.backend.kernel-id label -> Container) is a
        # follow-up; returning empty keeps startup/lifecycle sync working.
        return []

    @override
    async def resolve_image_distro(self, image: ImageConfig) -> str:
        # Backend.AI kernel images carry the base-distro label; use it. (DockerAgent falls
        # back to an ldd probe for unlabeled images — a follow-up here.)
        distro = image["labels"].get(LabelName.BASE_DISTRO)
        if distro:
            return distro
        raise NotImplementedError(
            f"image {image['canonical']} lacks the {LabelName.BASE_DISTRO} label; "
            "ldd-based distro detection is not yet implemented for the containerd backend"
        )

    @override
    def get_cgroup_path(self, controller: str, container_id: str) -> Path:
        # cgroup v2 unified hierarchy with the systemd driver (nerdctl/containerd default).
        # TODO: read the actual driver/slice from containerd instead of assuming systemd v2.
        return Path("/sys/fs/cgroup") / "system.slice" / f"containerd-{container_id}.scope"

    @override
    def get_cgroup_version(self) -> str:
        return "2"

    @override
    async def extract_image_command(self, image: str) -> list[str] | None:
        return await self._session_network.image_entrypoint(image)

    @override
    async def scan_images(self) -> ScanImagesResult:
        # Boot-safe: startup calls this to populate self.images. Building InstalledImageInfo
        # from `nerdctl images` + Backend.AI image labels is a follow-up; empty lets the
        # agent boot and pull-on-demand via check_image/pull_image.
        return ScanImagesResult(scanned_images={}, removed_images={})

    @override
    async def pull_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout_seconds: float | None,
    ) -> None:
        # TODO: honor registry_conf auth + timeout_seconds; nerdctl uses its own config.
        await self._session_network.pull_image(image_ref.canonical)

    @override
    async def push_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout_seconds: float | None | Sentinel = Sentinel.TOKEN,
    ) -> None:
        if image_ref.is_local:
            return
        # TODO: honor registry_conf auth (nerdctl --creds) + timeout_seconds.
        await self._session_network.push_image(image_ref.canonical)

    @override
    async def purge_images(self, request: PurgeImagesReq) -> PurgeImagesResp:
        responses: list[PurgeImageResp] = []
        for image in request.images:
            try:
                await self._session_network.remove_image(image)
                responses.append(PurgeImageResp.success(image))
            except Exception as exc:
                responses.append(PurgeImageResp(image=image, error=str(exc)))
        return PurgeImagesResp(responses=responses)

    @override
    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        # Returns True if a pull is needed. (TODO: DIGEST freshness check needs the local
        # image id; treated as up-to-date when present for now.)
        exists = await self._session_network.image_exists(image_ref.canonical)
        if exists:
            return False
        if auto_pull in (AutoPullBehavior.DIGEST, AutoPullBehavior.TAG):
            return True
        raise ImageNotAvailable(image_ref)

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
            session_network=self._session_network,
        )

    @override
    async def destroy_kernel(
        self,
        kernel_id: KernelId,
        container_id: ContainerId | None,
    ) -> None:
        # Stop the container's task (force). Removal happens in clean_kernel.
        # NOTE: proper CNI detach needs the per-kernel EndpointPlan; tracking it across
        # destroy/clean is a follow-up (removing the container drops its netns).
        await self._session_network.kill_container(str(kernel_id), signal=signal.SIGKILL)

    @override
    async def clean_kernel(
        self,
        kernel_id: KernelId,
        container_id: ContainerId | None,
        restarting: bool,
    ) -> None:
        await self._session_network.remove_container(str(kernel_id))

    @override
    async def create_local_network(self, network_name: str) -> None:
        # Single-node multi-kernel local bridge. In BEP-1055 intra-node connectivity is
        # covered by the per-session overlay/LOCAL bridges, so this is a no-op for now.
        # TODO: a dedicated agent-local bridge for single-node cluster sessions.
        return

    @override
    async def destroy_local_network(self, network_name: str) -> None:
        return

    @override
    async def restart_kernel__load_config(
        self,
        kernel_id: KernelId,
        name: str,
    ) -> bytes:
        path = self.local_config.container.scratch_root / str(kernel_id) / "config" / name
        return await asyncio.to_thread(path.read_bytes)

    @override
    async def restart_kernel__store_config(
        self,
        kernel_id: KernelId,
        name: str,
        data: bytes,
    ) -> None:
        path = self.local_config.container.scratch_root / str(kernel_id) / "config" / name
        await asyncio.to_thread(path.write_bytes, data)

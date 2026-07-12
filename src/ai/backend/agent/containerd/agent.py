"""Containerd agent backend (BEP-1058).

An independent agent backend parallel to DockerAgent, targeting containerd's native
gRPC/task model instead of the Docker daemon. The container/image lifecycle (scan/pull/push,
create/start/destroy, resource limits, GPU/device injection, distro probe) runs over the
containerd gRPC API with no nerdctl/ctr; cluster networking is delegated to the BEP-1058
stack.

Cluster networking is provided by the BEP-1058 runtime-neutral stack
(``agent.network``): the SessionNetworkCoordinator handles per-session setup and the
ContainerNetworkProvisioner attaches each container's task PID via CNI.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import platform
import shutil
import signal
import struct
import subprocess
import sys
from collections.abc import AsyncGenerator, Mapping, Sequence
from decimal import Decimal
from importlib.resources import files
from io import StringIO
from pathlib import Path
from typing import Any, cast, override
from uuid import UUID, uuid4

import zmq
import zmq.asyncio

from ai.backend.agent.agent import (
    AbstractAgent,
    AbstractKernelCreationContext,
    ScanImagesResult,
)
from ai.backend.agent.config.unified import ContainerSandboxType, ScratchType
from ai.backend.agent.containerd.runtime.spec import _DEFAULT_CAPS, container_cgroup_fs_path
from ai.backend.agent.docker.agent import (
    LDD_GLIBC_REGEX,
    LDD_MUSL_REGEX,
    known_glibc_distros,
)
from ai.backend.agent.errors import UnsupportedResource
from ai.backend.agent.errors.resources import PortPoolExhaustedError
from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.kernel_registry.adapter import (
    KernelRecoveryDataAdapter,
    KernelRecoveryDataAdapterTarget,
)
from ai.backend.agent.kernel_registry.container.creator import (
    ContainerBasedKernelRegistryCreatorArgs,
    ContainerBasedLoaderWriterCreator,
)
from ai.backend.agent.kernel_registry.pickle.creator import (
    PickleBasedKernelRegistryCreatorArgs,
    PickleBasedLoaderWriterCreator,
)
from ai.backend.agent.kernel_registry.recovery.base_recovery import BaseKernelRegistryRecovery
from ai.backend.agent.kernel_registry.writer.types import KernelRegistrySaveMetadata
from ai.backend.agent.network.caps import publish_vtep
from ai.backend.agent.network.helper.client import HelperClient, HelperPortForwarder
from ai.backend.agent.network.port_forward import PortForwarder, PortPublisher, forwards_for
from ai.backend.agent.port_pool import PortPool
from ai.backend.agent.resources import (
    AbstractComputePlugin,
    ComputerContext,
    KernelResourceSpec,
    Mount,
    known_slot_types,
)
from ai.backend.agent.scratch import create_loop_filesystem, destroy_loop_filesystem
from ai.backend.agent.stats import StatModes
from ai.backend.agent.types import (
    AgentEventData,
    Container,
    ContainerNetns,
    KernelOwnershipData,
    LifecycleEvent,
    MountInfo,
    Port,
)
from ai.backend.agent.utils import container_pid_to_host_pid, host_pid_to_container_pid
from ai.backend.common.arch import CURRENT_ARCH
from ai.backend.common.data.image.types import InstalledImageInfo
from ai.backend.common.docker import MAX_KERNELSPEC, MIN_KERNELSPEC, ImageRef, LabelName
from ai.backend.common.dto.agent.response import PurgeImageResp, PurgeImagesResp
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.kernel import KernelLifecycleEventReason
from ai.backend.common.exception import ImageNotAvailable, InvalidImageName, InvalidImageTag
from ai.backend.common.json import dump_json_str
from ai.backend.common.network.types import NetworkBackendKind, SessionNetMeta
from ai.backend.common.types import (
    AutoPullBehavior,
    ClusterInfo,
    ClusterSSHPortMapping,
    ContainerId,
    ContainerStatus,
    DeviceId,
    DeviceName,
    ImageCanonical,
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
from .oci import (
    KERNEL_ID_LABEL,
    KRUNNER_ENTRYPOINT,
    AcceleratorSpec,
    infiniband_devices,
    translate_accelerator_args,
    translate_creation_config,
)
from .runtime.grpc import ContainerdGrpcRuntime, container_log_path
from .runtime.interface import OciRuntime, TaskEvent
from .session_network import (
    ContainerdSessionNetwork,
    build_containerd_session_network,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Grace period for a kernel to self-terminate on SIGTERM before it is SIGKILL'd (Docker's
# container.stop() default).
_KERNEL_STOP_GRACE_SECONDS = 10.0
# Bound the terminal-log persist so a huge or stuck read cannot wedge the clean event.
_LOG_COLLECTION_TIMEOUT = 60.0
# Read the finished shim log in this many bytes at a time; collect_logs re-chunks to its own size.
_LOG_READ_CHUNK = 256 * 1024


async def _read_container_log(container_id: str) -> AsyncGenerator[bytes, None]:
    """Yield the finished shim log file's bytes for collect_logs. Empty (yields nothing) when the
    task wrote no log or the file is already gone — collect_logs handles a zero-length stream."""
    path = container_log_path(container_id)

    def _read(handle: Any) -> bytes:
        data: bytes = handle.read(_LOG_READ_CHUNK)
        return data

    try:
        handle = await asyncio.to_thread(path.open, "rb")
    except FileNotFoundError:
        return
    try:
        while chunk := await asyncio.to_thread(_read, handle):
            yield chunk
    finally:
        await asyncio.to_thread(handle.close)


# Placeholder subnet for a single-node BRIDGE session; the bridge backend allocates the
# real node-local /24 per session and ignores this value (SessionNetMeta requires a subnet).
_LOCAL_SUBNET = "172.30.0.0/24"
# containerd task status -> Backend.AI ContainerStatus (anything not running/paused = exited).
_CONTAINERD_TO_STATUS = {
    "running": ContainerStatus.RUNNING,
    "paused": ContainerStatus.PAUSED,
    "pausing": ContainerStatus.PAUSED,
}


# Backend.AI arch name -> primary seccomp arch token (the archMap key to select).
_SCMP_ARCH = {"x86_64": "SCMP_ARCH_X86_64", "aarch64": "SCMP_ARCH_AARCH64"}
# Backend.AI arch name -> Go arch name. Docker's per-syscall includes/excludes gate on the Go
# arch name (e.g. "amd64", "ppc64le"), NOT the SCMP token used by archMap.
_GO_ARCH = {"x86_64": "amd64", "aarch64": "arm64"}


def _kernel_ge(min_kernel: str) -> bool:
    """True if the running host kernel is at least ``min_kernel`` (e.g. '4.8')."""

    def parse(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in v.split("-", 1)[0].split(".")[:2])

    try:
        return parse(platform.release()) >= parse(min_kernel)
    except ValueError:
        return True  # unparseable -> match Docker's default (modern kernels satisfy minKernel)


def _seccomp_rule_applies(
    sc: Mapping[str, Any], *, go_arch: str | None, caps: frozenset[str]
) -> bool:
    """Evaluate a Docker seccomp rule's includes/excludes against this container's arch,
    capability set and the host kernel — mirroring Docker's runtime evaluation. Without this we
    would unconditionally allow cap-gated syscalls (bpf, ptrace, open_by_handle_at, ...) the
    container was never granted the capability for, loosening the sandbox versus DockerAgent."""
    inc = sc.get("includes") or {}
    exc = sc.get("excludes") or {}
    if (arches := inc.get("arches")) and (go_arch is None or go_arch not in arches):
        return False
    if (arches := exc.get("arches")) and go_arch is not None and go_arch in arches:
        return False
    if (inc_caps := inc.get("caps")) and not all(c in caps for c in inc_caps):
        return False
    if (exc_caps := exc.get("caps")) and any(c in caps for c in exc_caps):
        return False
    if (mk := inc.get("minKernel")) and not _kernel_ge(mk):
        return False
    exc_min_kernel = exc.get("minKernel")
    return not (exc_min_kernel and _kernel_ge(exc_min_kernel))


def _docker_seccomp_to_oci(
    profile: Mapping[str, Any],
    *,
    arch: str = CURRENT_ARCH,
    caps: frozenset[str] = frozenset(_DEFAULT_CAPS),
) -> dict[str, Any]:
    """Convert a Docker-format seccomp profile (archMap + per-syscall includes/excludes) to the
    OCI runtime-spec linux.seccomp shape. Per-syscall includes/excludes are evaluated against the
    container's ``caps``/``arch`` and the host kernel (see _seccomp_rule_applies) so cap-gated
    syscalls stay gated — matching how Docker resolves the profile at container creation.

    Only the host arch's entry (+ its compat sub-arches) is emitted: the full archMap lists arches
    (e.g. SCMP_ARCH_LOONGARCH64) that the node's libseccomp may not know, and runc rejects the
    whole profile if any architecture token is unrecognized."""
    host_scmp = _SCMP_ARCH.get(arch)
    go_arch = _GO_ARCH.get(arch)
    architectures: list[str] = []
    for entry in profile.get("archMap") or []:
        if host_scmp is not None and entry.get("architecture") != host_scmp:
            continue
        architectures.append(entry["architecture"])
        architectures.extend(entry.get("subArchitectures") or [])
    syscalls: list[dict[str, Any]] = []
    for sc in profile.get("syscalls") or []:
        if not _seccomp_rule_applies(sc, go_arch=go_arch, caps=caps):
            continue
        oci_sc: dict[str, Any] = {"names": sc["names"], "action": sc["action"]}
        if sc.get("errnoRet") is not None:
            oci_sc["errnoRet"] = sc["errnoRet"]
        if sc.get("args"):
            oci_sc["args"] = sc["args"]
        syscalls.append(oci_sc)
    oci: dict[str, Any] = {
        "defaultAction": profile.get("defaultAction", "SCMP_ACT_ERRNO"),
        "architectures": architectures,
        "syscalls": syscalls,
    }
    if profile.get("defaultErrnoRet") is not None:
        oci["defaultErrnoRet"] = profile["defaultErrnoRet"]
    return oci


def _registry_auth(registry_conf: ImageRegistry) -> dict[str, str] | None:
    """Extract basic-auth credentials from the manager-provided registry config, if any."""
    user, password = registry_conf.get("username"), registry_conf.get("password")
    if user and password:
        return {"username": user, "password": password}
    return None


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
    _accel_spec: AcceleratorSpec
    _agent_sock_path: Path | None
    _port_pool: PortPool
    _port_forwarder: PortPublisher | None
    # (host_port, container_port) for the REPL and every service port, captured at reserve time and
    # turned into DNAT rules once the container's address is known.
    _host_port_map: list[tuple[int, int]]
    _repl_host_ports: tuple[int, ...]

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
        agent_sock_path: Path | None = None,
        port_pool: PortPool,
        port_forwarder: PortPublisher | None = None,
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
        self._agent_sock_path = agent_sock_path
        self._net_meta = None
        self._container_id = str(kernel_config["kernel_id"])
        self._session_id = str(kernel_config["session_id"])
        self._oci_mounts = []
        self._pending_spec = None
        self._scratch_dir = None
        self._accel_spec = AcceleratorSpec()
        self._port_pool = port_pool
        self._port_forwarder = port_forwarder
        self._host_port_map = []
        self._repl_host_ports = ()

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
        # Create the per-kernel scratch dirs (config/ + work/) and seed the default dotfiles.
        # (Containers run as root so no chown is needed.)
        scratch_type = self.local_config.container.scratch_type
        scratch_root = self.local_config.container.scratch_root
        scratch_dir = (scratch_root / str(self._container_id)).resolve()
        config_dir = scratch_dir / "config"
        work_dir = scratch_dir / "work"
        # HOSTFILE: back the scratch with a fixed-size loop-mounted ext4 image (per-session disk
        # quota). create_loop_filesystem makes + mounts the image at scratch_dir; config/work then
        # live inside that mount.
        if sys.platform.startswith("linux") and scratch_type == ScratchType.HOSTFILE:
            await create_loop_filesystem(
                scratch_root, self.local_config.container.scratch_size, self.kernel_id
            )

        def _prepare() -> None:
            config_dir.mkdir(parents=True, exist_ok=True)
            work_dir.mkdir(parents=True, exist_ok=True)
            self._clone_dotfiles(work_dir)

        await asyncio.to_thread(_prepare)
        self._scratch_dir = scratch_dir

    @staticmethod
    def _clone_dotfiles(work_dir: Path) -> None:
        """Seed the default shell/editor dotfiles + Jupyter branding into /home/work, matching
        DockerAgent (files packaged in ai.backend.runner)."""

        def _runner_file(name: str) -> Path:
            return Path(str(files("ai.backend.runner").joinpath(name)))

        jupyter_custom_dir = work_dir / ".jupyter" / "custom"
        jupyter_custom_dir.mkdir(parents=True, exist_ok=True)
        copies = [
            ("jupyter-custom.css", jupyter_custom_dir / "custom.css"),
            ("logo.svg", jupyter_custom_dir / "logo.svg"),
            ("roboto.ttf", jupyter_custom_dir / "roboto.ttf"),
            ("roboto-italic.ttf", jupyter_custom_dir / "roboto-italic.ttf"),
            (".bashrc", work_dir / ".bashrc"),
            (".bash_profile", work_dir / ".bash_profile"),
            (".zshrc", work_dir / ".zshrc"),
            (".vimrc", work_dir / ".vimrc"),
            (".tmux.conf", work_dir / ".tmux.conf"),
            (
                "DO_NOT_STORE_PERSISTENT_FILES_HERE.md",
                work_dir / "DO_NOT_STORE_PERSISTENT_FILES_HERE.md",
            ),
        ]
        for src_name, dst in copies:
            src = _runner_file(src_name)
            if src.exists():
                shutil.copy(src.resolve(), dst)

    @override
    async def get_intrinsic_mounts(self) -> Sequence[Mount]:
        # The kernel runner requires the per-kernel scratch dirs: config/ (RO) at
        # /home/config and work/ (RW) at /home/work. prepare_scratch created them.
        # (lxcfs, /etc/localtime, coredump, domain-socket proxies are follow-ups.)
        scratch_dir = (self.local_config.container.scratch_root / str(self._container_id)).resolve()
        mounts = [
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
        # The in-container agent socket (host<->container PID translation, jail status) for
        # libbaihook/jail, bind-mounted directly (no socat relay).
        if self._agent_sock_path is not None:
            mounts.append(
                Mount(
                    MountTypes.BIND,
                    self._agent_sock_path,
                    Path("/opt/kernel/agent.sock"),
                    MountPermission.READ_WRITE,
                )
            )
        # Timezone parity: /etc/localtime + /etc/timezone (read-only, if present on the host).
        for tzfile in (Path("/etc/localtime"), Path("/etc/timezone")):
            if tzfile.exists():
                mounts.append(Mount(MountTypes.BIND, tzfile, tzfile, MountPermission.READ_ONLY))
        # lxcfs: make cgroup-aware tools (free/nproc/top) report the container's limits, not the
        # host's — only when lxcfs is installed on the node.
        lxcfs_root = Path("/var/lib/lxcfs")
        if lxcfs_root.is_dir():
            mounts.extend(
                Mount(
                    MountTypes.BIND,
                    proc_file,
                    Path("/") / proc_file.relative_to(lxcfs_root),
                    MountPermission.READ_WRITE,
                )
                for proc_file in (lxcfs_root / "proc").iterdir()
                if proc_file.stat().st_size > 0
            )
            for rel in ("sys/devices/system/cpu", "sys/devices/system/cpu/online"):
                if (lxcfs_root / rel).exists():
                    mounts.append(
                        Mount(
                            MountTypes.BIND,
                            lxcfs_root / rel,
                            Path("/") / rel,
                            MountPermission.READ_WRITE,
                        )
                    )
        return mounts

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
        # BEP-1058: set up this node's per-session data plane and register the per-session
        # orchestrator. Per-container CNI attach happens in start_container against the task
        # PID. Multi-node sessions carry a manager-provided network_config (vxlan overlay);
        # single-node sessions have none, so synthesize a node-local BRIDGE config — the
        # same CNI attach path then applies, with no nerdctl-managed network.
        network_config = dict(cluster_info.get("network_config") or {})
        if not network_config.get("backend"):
            network_config = {"backend": str(NetworkBackendKind.BRIDGE), "subnet": _LOCAL_SUBNET}
        self._net_meta = await self._session_network.ensure_session(
            self._session_id, network_config
        )

    def _prepare_etc_hosts(self, cluster_info: ClusterInfo) -> Mount | None:
        """Write an /etc/hosts carrying every cluster peer's ``hostname -> IP`` (BEP-1058 central
        IPAM) and return a bind mount for it, so hostname-based cluster workloads (MPI/torchrun)
        resolve peers. Returns None when there is no mapping to inject — single-node bridge
        sessions use node-local IPAM with no manager-assigned addresses."""
        cluster_hosts = cluster_info.get("cluster_hosts") or {}
        if not cluster_hosts or self._scratch_dir is None:
            return None
        lines = ["127.0.0.1\tlocalhost", "::1\tlocalhost ip6-localhost ip6-loopback"]
        lines += [f"{ip}\t{hostname}" for hostname, ip in cluster_hosts.items()]
        hosts_file = self._scratch_dir / "config" / "hosts"
        hosts_file.write_text("\n".join(lines) + "\n")
        return Mount(MountTypes.BIND, hosts_file, Path("/etc/hosts"), MountPermission.READ_ONLY)

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
        # Reuse the compute plugin's per-vendor Docker args (the plugins already encode the
        # right mechanism: NVIDIA via nvidia-container-toolkit, AMD/NPUs via /dev node
        # passthrough) and translate them to runtime-neutral device/gpu/env for the containerd
        # path. The `docker` arg is unused by the plugins here (cached version / list_devices),
        # so None is safe. Accumulated across accelerators and merged at prepare_container.
        docker_args = await computer.generate_docker_args(cast(Any, None), device_alloc)
        spec = translate_accelerator_args(docker_args)
        prev = self._accel_spec
        self._accel_spec = AcceleratorSpec(
            devices=[*prev.devices, *spec.devices],
            gpu_device_ids=[*prev.gpu_device_ids, *spec.gpu_device_ids],
            env={**prev.env, **spec.env},
            # Each of cpu/mem limits comes from exactly one plugin; keep the first non-None.
            cpuset_cpus=prev.cpuset_cpus or spec.cpuset_cpus,
            cpuset_mems=prev.cpuset_mems or spec.cpuset_mems,
            memory_limit=prev.memory_limit or spec.memory_limit,
            memory_swap=prev.memory_swap or spec.memory_swap,
        )

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

    async def _write_config_files(
        self, resource_spec: KernelResourceSpec, environ: Mapping[str, str]
    ) -> None:
        """Write /home/config's environ.txt + resource.txt (+ *_base copies) that the
        in-container runner and libbaihook read (parity with the Docker backend)."""
        if self._scratch_dir is None:
            return
        config_dir = self._scratch_dir / "config"
        env_lines = [f"{k}={v}" for k, v in environ.items()]
        env_lines += [f"{k}={v}" for k, v in self._accel_spec.env.items()]
        buf = StringIO()
        resource_spec.write_to_file(buf)
        for dev_type, device_alloc in resource_spec.allocations.items():
            plugin = self.computers[dev_type].instance
            for k, v in (await plugin.generate_resource_data(device_alloc)).items():
                buf.write(f"{k}={v}\n")
        resource_txt = buf.getvalue()

        def _write() -> None:
            (config_dir / "environ.txt").write_text("\n".join(env_lines) + "\n")
            (config_dir / "resource.txt").write_text(resource_txt)
            shutil.copyfile(config_dir / "environ.txt", config_dir / "environ_base.txt")
            shutil.copyfile(config_dir / "resource.txt", config_dir / "resource_base.txt")

        await asyncio.to_thread(_write)

    def _reserve_host_ports(self, service_ports: list[ServicePort]) -> None:
        """Acquire a host port for each *service* container port, recording the pairing.

        Only services are published. The REPL is not: the agent is on this node, so it reaches the
        container's LOCAL address directly (the host is that bridge's gateway) — no host port, no
        DNAT, and no dependence on ``route_localnet`` when the agent's advertised address is a
        loopback one. Services are a different matter: an AppProxy may run on any host, so they
        must be reachable at the agent's advertised address.
        """
        needed = sum(len(sp["container_ports"]) for sp in service_ports)
        if needed > len(self._port_pool):
            raise PortPoolExhaustedError(
                f"Container ports are not sufficiently available. "
                f"(needed: {needed}, remaining: {self._port_pool.remaining()})"
            )
        self._host_port_map = []
        # No sshd special case: the manager only builds a cluster SSH port mapping for HOST-network
        # sessions, and those never reach this backend.
        for sport in service_ports:
            host_ports: list[int] = []
            for container_port in sport["container_ports"]:
                host_port = self._port_pool.acquire()
                host_ports.append(host_port)
                self._host_port_map.append((host_port, container_port))
            sport["host_ports"] = tuple(host_ports)

    @override
    async def prepare_container(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports: list[ServicePort],
        cluster_info: ClusterInfo,
    ) -> ContainerdKernel:
        # In-container config files (env + resource allocation) read by the runner/hooks.
        await self._write_config_files(resource_spec, environ)
        # containerd/runc (unlike Docker) neither synthesizes /etc/hosts nor provides cluster DNS,
        # so inject peer hostname -> IP resolution for cluster sessions.
        if (hosts_mount := self._prepare_etc_hosts(cluster_info)) is not None:
            self._oci_mounts.append(hosts_mount)
        # Build (but do NOT create) the container spec + kernel object. mount_krunner
        # (inherited) has populated resource_spec.mounts with the krunner bind mounts;
        # combine with process_mounts' vfolder mounts and inject them (plus env/labels)
        # into the OCI spec. Container creation is deferred to start_container, where the
        # kernel-runner cmdargs (which the container command must exec) are available.
        # resource_spec.mounts (krunner + accelerator) and _oci_mounts (vfolder) can carry
        # the same intrinsic bind more than once; dedupe by identity so the OCI runtime spec's mounts
        # label stays within its 4 KiB size limit (duplicates only inflate it).
        seen_mounts: set[tuple[Any, ...]] = set()
        all_mounts = []
        for m in (*resource_spec.mounts, *self._oci_mounts):
            key = (str(m.source), str(m.target), m.permission, m.type)
            if key in seen_mounts:
                continue
            seen_mounts.add(key)
            all_mounts.append(m)
        self._pending_spec = translate_creation_config(
            self.kernel_config, environ=environ, mounts=all_mounts
        )
        # Layer in accelerator wiring collected by apply_accelerator_allocation: extra env,
        # /dev node passthrough (AMD/NPU), and NVIDIA GPU IDs (nvidia-container-toolkit).
        oci_spec = self._pending_spec.oci_spec
        oci_spec["env"].update(self._accel_spec.env)
        # RDMA/InfiniBand: expose the host's HCA char devices (Docker parity — unconditional bulk
        # passthrough when the host has IB; CAP_IPC_LOCK is already granted in the runtime spec).
        # Not scheduled and not tenant-isolated; proper GPUDirect-RDMA topology is BEP-1051.
        passthrough_devices = [*self._accel_spec.devices, *infiniband_devices()]
        if passthrough_devices:
            oci_spec["devices"] = [
                {"source": d.source, "destination": d.destination, "permissions": d.permissions}
                for d in passthrough_devices
            ]
        if self._accel_spec.gpu_device_ids:
            oci_spec["gpus"] = list(self._accel_spec.gpu_device_ids)
        # cgroup resource limits (cpu pinning + memory), from the cpu/mem compute plugins.
        oci_spec["cpuset_cpus"] = self._accel_spec.cpuset_cpus
        oci_spec["cpuset_mems"] = self._accel_spec.cpuset_mems
        oci_spec["memory_limit"] = self._accel_spec.memory_limit
        oci_spec["memory_swap"] = self._accel_spec.memory_swap
        # /dev/shm sizing from the session's resource_opts (parity with Docker's ShmSize).
        shmem = (self.kernel_config.get("resource_opts") or {}).get("shmem")
        if shmem:
            oci_spec["shmem"] = int(shmem)
        # MEMORY scratch type -> in-memory (tmpfs) /tmp.
        if self.local_config.container.scratch_type == ScratchType.MEMORY:
            oci_spec["tmpfs_tmp"] = True
        # The LOCAL bridge is a node-local NAT subnet, so the container's address is private and
        # unroutable off this node — an AppProxy may run on any host. Publish each service (and the
        # REPL, which the agent itself dials at kernel_host) on a host port, DNAT'd to the container
        # once its address is known at start. Same contract as the Docker backend's PortBindings.
        self._reserve_host_ports(service_ports)
        # seccomp hardening (skip under the jail sandbox, which does its own syscall filtering).
        if self.local_config.container.sandbox_type != ContainerSandboxType.JAIL:
            seccomp_path = self.resolve_krunner_filepath("runner/default-seccomp.json")
            if seccomp_path.exists():
                oci_spec["seccomp"] = _docker_seccomp_to_oci(json.loads(seccomp_path.read_text()))
        else:
            # The jail enforces syscall policy by ptrace-tracing the container's processes, so it
            # needs CAP_SYS_PTRACE. Docker's jail path adds the same capability; without it the
            # jail's tracer cannot attach and its confinement silently degrades to nothing.
            oci_spec["extra_caps"] = ["CAP_SYS_PTRACE"]
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
            raise RuntimeError("apply_network must run before start_container (no net meta)")
        # _reserve_host_ports (in prepare_container) already took host ports from the pool. Any
        # failure here means they were never published — publish is atomic, so nothing survives in
        # iptables for clean_kernel to reclaim from — so release them right here, mirroring the
        # Docker backend's _rollback_container_creation. A published launch releases via clean_kernel
        # instead, and `published` keeps the two paths from double-releasing.
        published = False
        try:
            await self._session_network.create_container(
                self._session_id,
                self._container_id,
                image_ref=spec.image_ref,
                command=command,
                oci_spec=spec.oci_spec,
            )
            # Start + attach the CNI chain (bridge for single-node, +overlay for multi-node).
            result = await self._session_network.start_and_attach_container(
                self._session_id,
                self._container_id,
                meta=self._net_meta,
                kernel_config=self.kernel_config,
                cluster_info=cluster_info,
            )
            task_pid = result.handle.pid
            container_ip = result.local_ip
            if container_ip is None:
                raise RuntimeError("the LOCAL attachment yielded no address; cannot publish ports")
            # Publish the services on host ports. kernel_host is what the manager hands to an
            # AppProxy that may run on any host, so it must be the agent's advertised address: the
            # OVERLAY IP is reachable only between kernels, and the LOCAL IP only from this node.
            await self._publish_ports(container_ip)
            published = True
        except Exception:
            if not published:
                self._port_pool.release_many([hp for hp, _ in self._host_port_map])
            raise
        kernel_host = str(
            self.local_config.container.advertised_host or self.local_config.container.bind_host
        )
        # The REPL is agent-to-container on this node, so it is dialled at the container's own
        # address (see _reserve_host_ports). repl_host travels in the kernel's data and is what the
        # code runner connects to; kernel_host is for everyone else.
        repl_in_port, repl_out_port = self.repl_ports
        return {
            "container_id": self._container_id,
            "task_pid": task_pid,
            "kernel_host": kernel_host,
            "repl_host": container_ip,
            "repl_in_port": repl_in_port,
            "repl_out_port": repl_out_port,
            "stdin_port": 0,  # legacy
            "stdout_port": 0,  # legacy
            "host_ports": [host_port for host_port, _ in self._host_port_map],
            "domain_socket_proxies": [],
            "block_service_ports": False,
        }

    async def _publish_ports(self, container_ip: str) -> None:
        """DNAT the reserved host ports at the container.

        Under a privileged helper the publisher is a proxy: it sends only the port pairing, and the
        helper DNATs to the LOCAL address it assigned itself — `container_ip` never leaves here.
        """
        if self._port_forwarder is None:
            raise RuntimeError("no port publisher; the kernel's services would be unreachable")
        await self._port_forwarder.install(
            forwards_for(self._container_id, container_ip, self._host_port_map)
        )

    # mount_krunner is inherited from AbstractKernelCreationContext: it populates
    # resource_spec.mounts (via get_runner_mount) and LD_PRELOAD — runtime-agnostic. The
    # accumulated mounts are injected into the OCI spec at prepare_container time.


class ContainerdAgent(
    AbstractAgent[ContainerdKernel, ContainerdKernelCreationContext],
):
    _runtime: OciRuntime
    _session_network: ContainerdSessionNetwork
    _host_ip: str
    _event_monitor_task: asyncio.Task[None] | None
    _agent_sock_path: Path
    _agent_sock_task: asyncio.Task[None] | None
    _port_forwarder: PortPublisher
    _kernel_recovery: BaseKernelRegistryRecovery
    _kernel_recovery_adapter: KernelRecoveryDataAdapter

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # The container runtime is the OCI runtime interface, implemented by the native
        # containerd gRPC client (no nerdctl/ctr CLI). The agent owns it and injects it into
        # the network facade; opened in __ainit__.
        self._runtime = ContainerdGrpcRuntime(namespace="backend-ai")
        self._event_monitor_task = None
        # In-container helpers (libbaihook LD_PRELOAD hook, jail) talk back to the agent over
        # a per-agent socket for host<->container PID translation + jail status. Bind ZMQ REP
        # directly on this ipc:// UNIX socket and bind-mount it into each container as
        # /opt/kernel/agent.sock — no socat relay / TCP hop (cf. DockerAgent).
        ipc_base_path = self.local_config.agent.ipc_base_path
        self._agent_sock_path = ipc_base_path / "container" / f"agent.{self.id}.sock"
        self._agent_sock_task = None
        # Cluster networking is delegated to the BEP-1058 agent.network stack via a
        # (verified) facade; the kernel-creation lifecycle will drive it. The vxlan uplink
        # must be the interface carrying this node's VTEP (host_ip) — deriving it from the
        # host_ip keeps the overlay on the same L2 the agents advertise on, instead of a
        # hard-coded eth0.
        container_cfg = self.local_config.container
        self._host_ip = str(container_cfg.advertised_host or container_cfg.bind_host)
        # When a privileged network helper is configured, delegate all CAP_NET_ADMIN/
        # CAP_SYS_ADMIN host networking to it so this agent process needs no such privilege.
        self._session_network = build_containerd_session_network(
            self.etcd,
            agent_id=str(self.id),
            host_ip=self._host_ip,
            uplink=_uplink_for_ip(self._host_ip),
            runtime=self._runtime,
            helper_socket=self.local_config.agent.network_helper_socket,
        )
        # Host-port ingress is an iptables (CAP_NET_ADMIN) op, so only the process that owns the
        # host's networking may install it: this agent when it runs privileged, the helper when
        # privilege is separated. Either way the kernel's services get published.
        helper_socket = self.local_config.agent.network_helper_socket
        self._port_forwarder = (
            PortForwarder()
            if helper_socket is None
            else HelperPortForwarder(HelperClient(helper_socket), self._session_network.session_of)
        )
        # Restart recovery (parity with DockerAgent): the container-based loader/writer keep each
        # kernel's recovery.json in its scratch (resource.txt / environ.txt are already written at
        # creation), so a restarted agent reconstructs its live kernels from the running
        # containers instead of losing them. The containerd loader rebuilds ContainerdKernels.
        scratch_root = self.local_config.container.scratch_root
        pickle_creator = PickleBasedLoaderWriterCreator.create(
            PickleBasedKernelRegistryCreatorArgs(
                scratch_root=scratch_root,
                ipc_base_path=self.local_config.agent.ipc_base_path,
                var_base_path=self.local_config.agent.var_base_path,
                agent_class=self.agent_class,
                agent_id=self.id,
                local_instance_id=self.local_instance_id,
            ),
        )
        container_creator = ContainerBasedLoaderWriterCreator(
            ContainerBasedKernelRegistryCreatorArgs(
                scratch_root=scratch_root,
                agent=self,
                kernel_factory=lambda d: d.to_containerd_kernel(),
            )
        )
        container_loader = container_creator.create_loader()
        container_writer = container_creator.create_writer()
        self._kernel_recovery = BaseKernelRegistryRecovery(
            loader=container_loader,
            writers=[pickle_creator.create_writer(), container_writer],
        )
        self._kernel_recovery_adapter = KernelRecoveryDataAdapter(
            pickle_creator.create_loader(),
            [KernelRecoveryDataAdapterTarget(container_loader, container_writer)],
        )

    @override
    async def __ainit__(self) -> None:
        # Open the runtime BEFORE super().__ainit__(): the base initializer runs the initial
        # scan_images, which queries the containerd runtime. Open it directly (the session
        # network shares the same instance; its open() below is then a no-op).
        await self._runtime.open()
        await self._session_network.open()
        # Rebuild the session-network state (attach plans, container<->session tracking, per-session
        # coordinators) for containers that outlived the previous agent process, and reconcile the
        # durable network journals against them. Must precede the kernel-registry recovery below,
        # so a kernel is never resumed before the network it is attached to.
        await self._session_network.recover()
        # Migrate any legacy pickle-based recovery into per-scratch recovery.json before the base
        # initializer loads the registry from it (parity with DockerAgent). Needs the runtime open
        # so the container-based loader can enumerate live containers.
        await self._kernel_recovery_adapter.adapt_recovery_data()
        await super().__ainit__()
        # Real-time container-death/OOM detection via the containerd event stream (the
        # equivalent of DockerAgent.monitor_docker_events); the periodic reconciler is the
        # safety net.
        self._event_monitor_task = asyncio.create_task(self._monitor_task_events())
        self._agent_sock_task = asyncio.create_task(self._handle_agent_socket())
        # Advertise this node's VTEP so the manager can pre-seed session membership and
        # eliminate the peer-publish race for multi-node overlays (BEP-1058).
        await publish_vtep(self.etcd, str(self.id), self._host_ip)

    @override
    async def shutdown(self, stop_signal: signal.Signals) -> None:
        for task in (self._event_monitor_task, self._agent_sock_task):
            if task is not None:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        await super().shutdown(stop_signal)

    async def _handle_agent_socket(self) -> None:
        """Serve the in-container helper socket (host<->container PID translation, jail
        status) as a ZMQ REP over an ipc:// UNIX socket. Re-binds on error."""
        zmq_ctx = zmq.asyncio.Context()
        endpoint = f"ipc://{self._agent_sock_path}"
        await asyncio.to_thread(self._agent_sock_path.parent.mkdir, parents=True, exist_ok=True)
        try:
            while True:
                sock = zmq_ctx.socket(zmq.REP)
                try:
                    sock.bind(endpoint)
                    self._agent_sock_path.chmod(0o777)  # in-container (non-root) user connects
                    while True:
                        msg = await sock.recv_multipart()
                        if not msg:
                            break
                        await sock.send_multipart(await self._agent_sock_reply(msg))
                except asyncio.CancelledError:
                    raise
                except Exception:
                    log.exception("agent socket handler error; re-binding")
                finally:
                    sock.close(linger=0)
                await asyncio.sleep(1.0)
        finally:
            zmq_ctx.term()

    async def _agent_sock_reply(self, msg: list[bytes]) -> list[bytes]:
        try:
            match msg[0]:
                case b"host-pid-to-container-pid":
                    container_id = msg[1].decode()
                    host_pid = struct.unpack("i", msg[2])[0]
                    cpid = await host_pid_to_container_pid(container_id, host_pid)
                    return [struct.pack("i", 0), struct.pack("i", int(cpid))]
                case b"container-pid-to-host-pid":
                    container_id = msg[1].decode()
                    cpid = struct.unpack("i", msg[2])[0]
                    hpid = await container_pid_to_host_pid(container_id, cpid)
                    return [struct.pack("i", 0), struct.pack("i", int(hpid))]
                case b"is-jail-enabled":
                    enabled = self.local_config.container.sandbox_type == ContainerSandboxType.JAIL
                    return [struct.pack("i", 0), struct.pack("i", 1 if enabled else 0)]
                case _:
                    return [struct.pack("i", -2), b"Invalid action"]
        except Exception as e:
            log.exception("agent socket action failed")
            return [struct.pack("i", -1), str(e).encode()]

    async def _monitor_task_events(self) -> None:
        """Consume the containerd task event stream, re-subscribing on drop."""
        while True:
            try:
                async for ev in self._runtime.subscribe_task_events():
                    await self._handle_task_event(ev)
                log.info("containerd event stream ended; re-subscribing")
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("containerd event monitor failed; retrying")
            await asyncio.sleep(1.0)

    async def _handle_task_event(self, ev: TaskEvent) -> None:
        try:
            kernel_id = KernelId(UUID(ev.container_id))
        except ValueError:
            return
        kernel_obj = self.kernel_registry.get(kernel_id)
        if kernel_obj is None:
            return  # not a live kernel of ours
        session_id = kernel_obj.session_id
        match ev.kind:
            case "exit":
                reason = kernel_obj.termination_reason or KernelLifecycleEventReason.SELF_TERMINATED
                await self.inject_container_lifecycle_event(
                    kernel_id,
                    session_id,
                    LifecycleEvent.CLEAN,
                    reason,
                    container_id=ContainerId(ev.container_id),
                    exit_code=ev.exit_code,
                )
            case "oom":
                await kernel_obj.notify_event(AgentEventData(type="oom", data={}))
            case "start":
                await self.inject_container_lifecycle_event(
                    kernel_id,
                    session_id,
                    LifecycleEvent.START,
                    KernelLifecycleEventReason.NEW_CONTAINER_STARTED,
                    container_id=ContainerId(ev.container_id),
                )

    # execute is inherited from AbstractAgent: it delegates to kernel_obj.execute (the code
    # runner's ZMQ REPL), which is runtime-agnostic. No override needed.

    @override
    async def _load_kernel_registry_from_recovery(self) -> dict[KernelId, AbstractKernel]:
        return dict(await self._kernel_recovery.load_kernel_registry())

    @override
    async def _write_kernel_registry_to_recovery(
        self,
        kernel_registry: Mapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
    ) -> None:
        await self._kernel_recovery.save_kernel_registry(dict(kernel_registry), metadata)

    @override
    async def enumerate_containers(
        self,
        status_filter: frozenset[ContainerStatus] = frozenset(),
    ) -> Sequence[tuple[KernelId, Container]]:
        # Reconcile live kernels from containerd: every container carrying the kernel-id label
        # is one of ours (the containerd instance is per-node/per-agent). Lets the agent
        # recover running kernels across a restart.
        #
        # The published ports come back from the DNAT rules, which name their container. Reporting
        # them lets the base agent take them out of the port pool again — otherwise a restarted
        # agent would hand a live kernel's host port to the next one.
        published = await self._published_ports_by_container()
        result: list[tuple[KernelId, Container]] = []
        for ci in await self._runtime.list_container_infos():
            raw_kid = ci.labels.get(KERNEL_ID_LABEL)
            if not raw_kid:
                continue
            status = _CONTAINERD_TO_STATUS.get(ci.status, ContainerStatus.EXITED)
            if status_filter and status not in status_filter:
                continue
            try:
                kernel_id = KernelId(UUID(raw_kid))
            except ValueError:
                continue
            # backend_obj mimics the Docker container-inspect shape the (shared) cpu/mem compute
            # plugins read in restore_from_container: a /home/config mount whose source holds
            # resource.txt. Point it at this kernel's scratch config dir so allocation restore on
            # agent restart works without a containerd-specific restore path.
            config_source = str(
                (self.local_config.container.scratch_root / raw_kid / "config").resolve()
            )
            backend_obj = {
                "HostConfig": {"Mounts": [{"Target": "/home/config", "Source": config_source}]}
            }
            result.append((
                kernel_id,
                Container(
                    id=ContainerId(ci.id),
                    status=status,
                    image=ci.image,
                    labels=dict(ci.labels),
                    ports=published.get(ci.id, []),
                    backend_obj=backend_obj,
                ),
            ))
        return result

    async def _published_ports_by_container(self) -> dict[str, list[Port]]:
        """``{container_id: [Port(...)]}`` read back from the DNAT rules that publish them."""
        try:
            forwards = await self._port_forwarder.list_forwards()
        except Exception:
            log.exception("could not read published ports; the port pool may leak")
            return {}
        published: dict[str, list[Port]] = {}
        for forward in forwards:
            published.setdefault(forward.container_id, []).append(
                Port(forward.container_ip, forward.container_port, forward.host_port)
            )
        return published

    @override
    async def resolve_image_distro(self, image: ImageConfig) -> str:
        # Backend.AI kernel images carry the base-distro label; use it directly.
        distro = image["labels"].get(LabelName.BASE_DISTRO)
        if distro:
            return distro
        # Fallback for unlabeled images: probe the C library by running `ldd --version` in a
        # throwaway container and parsing its captured stdout (same heuristic as DockerAgent).
        return await self._probe_image_distro(image["canonical"])

    async def _probe_image_distro(self, canonical: str) -> str:
        probe_id = f"distro-probe-{uuid4().hex[:12]}"
        oci_spec: dict[str, Any] = {"env": {}, "labels": {}, "mounts": []}
        await self._runtime.create_container(
            probe_id, image_ref=canonical, command=["ldd", "--version"], oci_spec=oci_spec
        )
        try:
            # No network needed for the throwaway probe: create the task and start it directly.
            await self._runtime.create_task(probe_id)
            await self._runtime.start_task(probe_id)
            for _ in range(50):  # up to ~10s for the trivial command to exit
                if await self._runtime.container_status(probe_id) in (None, "stopped"):
                    break
                await asyncio.sleep(0.2)
            output = container_log_path(probe_id).read_text(errors="replace")
        finally:
            await self._runtime.remove_container(probe_id)
        first_line = output.splitlines()[0] if output.strip() else ""
        if m := LDD_GLIBC_REGEX.search(first_line):
            version = float(m.group(1))
            if version in known_glibc_distros:
                return known_glibc_distros[version]
            for idx, known_version in enumerate(known_glibc_distros.keys()):
                if version < known_version:
                    return list(known_glibc_distros.values())[idx - 1]
            return list(known_glibc_distros.values())[-1]
        if LDD_MUSL_REGEX.search(first_line):
            return "alpine3.8"
        raise ImageNotAvailable(f"cannot determine the C library variant of {canonical}")

    @override
    def _resolve_stat_mode(self, local_config: Any) -> StatModes:
        # Always read stats from the cgroup filesystem: there is no Docker daemon to query, so the
        # 'docker' stat mode (the config default, meaningful only for the Docker backend) would 404
        # for every containerd container. get_cgroup_path below points the collectors at the exact
        # cgroup the OCI spec created, so cgroup mode is both correct and driver-independent here.
        configured = local_config.container.stats_type
        if configured is not None and StatModes(configured.value) is StatModes.DOCKER:
            log.debug(
                "containerd backend: forcing cgroup stat mode (docker stat mode has no daemon)"
            )
        return StatModes.CGROUP

    @override
    def get_cgroup_path(self, controller: str, container_id: str) -> Path:
        # The container's cgroup path is set explicitly in the OCI spec (runtime/spec.py sets
        # ``linux.cgroupsPath`` from this same derivation), so we know exactly where it lives
        # regardless of the runtime's cgroup driver. container_id == kernel_id here (see
        # __init__), which is what the spec keys the cgroup on. cgroup v2 unified hierarchy.
        return container_cgroup_fs_path(container_id)

    @override
    def get_cgroup_version(self) -> str:
        # cgroup v2 exposes a unified hierarchy marked by /sys/fs/cgroup/cgroup.controllers.
        return "2" if Path("/sys/fs/cgroup/cgroup.controllers").exists() else "1"

    @override
    async def get_container_netns(self, container_id: str) -> ContainerNetns | None:
        # The task's netns is not pinned anywhere on disk (CNI attaches against /proc/<pid>/ns/net),
        # so once the task is gone there is no namespace left to read counters from.
        pid = await self._runtime.container_pid(container_id)
        if pid is None:
            return None
        return ContainerNetns(pid=pid, path=None)

    @override
    async def extract_image_command(self, image: str) -> list[str] | None:
        return await self._session_network.image_entrypoint(image)

    @override
    async def scan_images(self) -> ScanImagesResult:
        # List local images over the containerd Images service; the kernel-spec label lives in
        # each image's OCI config (read via Content), so list_image_infos surfaces it. Keep
        # only valid Backend.AI images whose kernel-spec is in range.
        scanned: dict[ImageCanonical, InstalledImageInfo] = {}
        for info in await self._runtime.list_image_infos():
            if not info.labels:
                continue  # not a Backend.AI kernel image (no config labels)
            try:
                ImageRef.parse_image_str(info.name, "*")
            except (InvalidImageName, InvalidImageTag):
                continue
            try:
                kernelspec = int(info.labels.get(LabelName.KERNEL_SPEC, "1"))
            except ValueError:
                continue
            if not (MIN_KERNELSPEC <= kernelspec <= MAX_KERNELSPEC):
                continue
            canonical = ImageCanonical(info.name)
            scanned[canonical] = InstalledImageInfo.from_inspect_result(
                canonical=canonical,
                inspect_result={"Id": info.digest, "Architecture": info.architecture},
            )
        removed = {c: img for c, img in self.images.items() if c not in scanned}
        return ScanImagesResult(scanned_images=scanned, removed_images=removed)

    @override
    async def pull_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout_seconds: float | None,
    ) -> None:
        # The containerd Transfer service has no per-call deadline, so bound it here: on
        # timeout wait_for cancels the transfer coroutine (parity with the Docker backend,
        # which passes timeout= to the pull). ``None`` means wait indefinitely.
        await asyncio.wait_for(
            self._session_network.pull_image(
                image_ref.canonical, auth=_registry_auth(registry_conf)
            ),
            timeout_seconds,
        )

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
        # Sentinel means "unspecified" -> no deadline (parity with the Docker backend, which
        # then omits the timeout arg). The Transfer service has no per-call deadline, so bound
        # it with wait_for; None waits indefinitely.
        timeout = None if isinstance(timeout_seconds, Sentinel) else timeout_seconds
        await asyncio.wait_for(
            self._session_network.push_image(
                image_ref.canonical, auth=_registry_auth(registry_conf)
            ),
            timeout,
        )

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
        # Returns True if a pull is needed.
        local_digest = await self._session_network.image_digest(image_ref.canonical)
        if local_digest is None:  # not present locally
            if auto_pull in (AutoPullBehavior.DIGEST, AutoPullBehavior.TAG):
                return True
            raise ImageNotAvailable(image_ref)
        # Present: for DIGEST auto-pull, re-pull when the local digest is stale.
        return auto_pull is AutoPullBehavior.DIGEST and local_digest != image_id

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
            agent_sock_path=self._agent_sock_path,
            port_pool=self.port_pool,
            port_forwarder=self._port_forwarder,
        )

    @override
    async def destroy_kernel(
        self,
        kernel_id: KernelId,
        container_id: ContainerId | None,
    ) -> None:
        # Gracefully stop the task: SIGTERM, wait for self-termination, then SIGKILL — Docker
        # parity (container.stop()), so a workload gets its grace window to flush/checkpoint
        # instead of losing data to an immediate kill. Network detach + container removal happen
        # in clean_kernel -> remove_container, which replays the attach-time EndpointPlan to
        # release the host veth / IPAM / MASQ.
        await self._session_network.stop_container(
            str(kernel_id), grace_period=_KERNEL_STOP_GRACE_SECONDS
        )

    @override
    async def clean_kernel(
        self,
        kernel_id: KernelId,
        container_id: ContainerId | None,
        restarting: bool,
    ) -> None:
        # Persist the terminated kernel's logs before anything removes them. remove_container
        # unlinks the shim log file, so a manager query for a dead kernel's logs would otherwise
        # find nothing (the Docker backend collects them the same way, from container.log). The
        # shim log is a finished file here — no follow stream — so we just read it in chunks.
        if container_id is not None and not restarting:
            try:
                async with asyncio.timeout(_LOG_COLLECTION_TIMEOUT):
                    await self.collect_logs(
                        kernel_id, str(container_id), _read_container_log(str(container_id))
                    )
            except Exception:
                log.exception("clean_kernel(k:{}): collecting container logs failed", kernel_id)
        # Withdraw the published ports before the container goes: a stale DNAT rule would send the
        # next holder of that host port's traffic at an address that no longer exists. The rules
        # are tagged with the container id, so this needs no bookkeeping of our own — and it works
        # just as well after a restart, when nothing in memory remembers the kernel. Must precede
        # remove_container, which drops the attach record the helper's session lock is keyed by.
        try:
            released = await self._port_forwarder.remove_container(str(kernel_id))
        except Exception:
            log.exception("clean_kernel(k:{}): withdrawing published ports failed", kernel_id)
        else:
            self.port_pool.release_many(released)
        await self._session_network.remove_container(str(kernel_id))
        # Tear down the scratch (skipped on restart, which reuses it). HOSTFILE must be
        # unmounted (loop image) before removal; otherwise remove the directory tree. Best-effort:
        # a teardown hiccup must not abort the clean event.
        scratch_root = self.local_config.container.scratch_root
        scratch_dir = scratch_root / str(kernel_id)
        # Skip if already gone (clean_kernel may be re-invoked) so teardown stays idempotent.
        if not restarting and scratch_dir.exists():
            scratch_type = self.local_config.container.scratch_type
            try:
                if sys.platform.startswith("linux") and scratch_type == ScratchType.HOSTFILE:
                    await destroy_loop_filesystem(scratch_root, kernel_id)
                else:
                    await asyncio.to_thread(shutil.rmtree, scratch_dir, ignore_errors=True)
            except Exception:
                log.exception("clean_kernel(k:{}): scratch teardown failed", kernel_id)

    @override
    async def create_local_network(self, network_name: str) -> None:
        # Single-node multi-kernel local bridge. In BEP-1058 intra-node connectivity is
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

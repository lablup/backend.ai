"""Containerd agent backend (BEP-1062).

An independent agent backend parallel to DockerAgent, targeting containerd's native
gRPC/task model instead of the Docker daemon. The container/image lifecycle (scan/pull/push,
create/start/destroy, resource limits, GPU/device injection, distro probe) runs over the
containerd gRPC API with no nerdctl/ctr; cluster networking is delegated to the BEP-1062
stack.

Cluster networking is provided by the BEP-1062 runtime-neutral stack
(``agent.network``): the SessionNetworkCoordinator handles per-session setup and the
ContainerNetworkProvisioner attaches each container's task PID via CNI.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import platform
import secrets
import shutil
import signal
import struct
import subprocess
import sys
from collections.abc import AsyncGenerator, Mapping, Sequence
from decimal import Decimal
from functools import partial
from importlib.resources import files
from io import StringIO
from pathlib import Path
from typing import Any, cast, override
from uuid import UUID, uuid4

import aiotools
import zmq
import zmq.asyncio

from ai.backend.agent.agent import (
    ACTIVE_STATUS_SET,
    AbstractAgent,
    AbstractKernelCreationContext,
    ScanImagesResult,
)
from ai.backend.agent.config.unified import ContainerSandboxType, ScratchType
from ai.backend.agent.containerd.apparmor import ensure_profile_loaded
from ai.backend.agent.containerd.dns import resolve_container_dns
from ai.backend.agent.containerd.logs import write_logger_launcher
from ai.backend.agent.containerd.runtime.spec import (
    _DEFAULT_CAPS,
    container_cgroup_fs_path,
    container_cgroup_parent,
)
from ai.backend.agent.errors import UnsupportedResource
from ai.backend.agent.errors.agent import ContainerCreationError
from ai.backend.agent.errors.resources import PortPoolExhaustedError, ResourceError
from ai.backend.agent.fs import create_scratch_filesystem, destroy_scratch_filesystem
from ai.backend.agent.image_distro import (
    UnknownImageLibc,
    distro_from_ldd_output,
    is_deeplearning_image,
)
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
from ai.backend.agent.network.caps import probe_caps, publish_caps, publish_vtep, withdraw_vtep
from ai.backend.agent.network.helper.client import HelperClient, HelperPortForwarder
from ai.backend.agent.network.local_subnet import cluster_host_ips
from ai.backend.agent.network.port_forward import PortForwarder, PortPublisher, forwards_for
from ai.backend.agent.network.vtep import uplink_for_ip, usable_vtep
from ai.backend.agent.port_pool import PortPool
from ai.backend.agent.proxy import DomainSocketProxy, proxy_connection
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
from ai.backend.common.cgroup import get_cgroup_mount_point
from ai.backend.common.data.image.types import InstalledImageInfo
from ai.backend.common.docker import (
    MAX_KERNELSPEC,
    MIN_KERNELSPEC,
    ImageRef,
    KernelFeatures,
    LabelName,
)
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
    ClusterMode,
    ClusterSSHPortMapping,
    ContainerId,
    ContainerStatus,
    DeviceId,
    DeviceName,
    ImageCanonical,
    ImageConfig,
    ImageRegistry,
    KernelCreationConfig,
    KernelCreationResult,
    KernelId,
    MountPermission,
    MountTypes,
    ResourceGroupType,
    ResourceSlot,
    Sentinel,
    ServicePort,
    SessionId,
    SlotName,
    current_resource_slots,
)
from ai.backend.logging import BraceStyleAdapter

from .kernel import ContainerdKernel
from .oci import (
    KERNEL_ID_LABEL,
    KRUNNER_ENTRYPOINT,
    OWNER_AGENT_LABEL,
    SESSION_ID_LABEL,
    AcceleratorSpec,
    infiniband_devices,
    translate_accelerator_args,
    translate_creation_config,
)
from .runtime.grpc import CONTAINER_LOG_ROOT, ContainerdGrpcRuntime, container_log_path
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


# tmpfs quota for the MEMORY scratch, in MiB. The Docker backend passes the same literal.
_MEMORY_SCRATCH_SIZE_MIB = 64

# The files we seed into the user's home. One list, so what we hand to the user and what we hand
# OWNERSHIP of cannot drift apart — a seeded file the chown list forgets is a file the user cannot
# write. (Same set as the Docker backend's.)
_SEEDED_DOTFILES = (
    ".bashrc",
    ".bash_profile",
    ".zshrc",
    ".vimrc",
    ".tmux.conf",
    "DO_NOT_STORE_PERSISTENT_FILES_HERE.md",
)
_JUPYTER_CUSTOM_FILES = ("custom.css", "logo.svg", "roboto.ttf", "roboto-italic.ttf")
# containerd task status -> Backend.AI ContainerStatus.
#
# CREATED must NOT collapse into EXITED: EXITED is in DEAD_STATUS_SET, and
# sync_container_lifecycles() cleans every dead container it sees. A kernel is visible to
# containerd from Containers.Create until its task is started, so mapping that window to EXITED
# makes the lifecycle sync destroy kernels that are still being created. CREATED is in neither
# ACTIVE_STATUS_SET nor DEAD_STATUS_SET, so the sync leaves it alone — same as the Docker backend,
# where dockerd reports "created" for exactly this window.
_CONTAINERD_TO_STATUS = {
    "created": ContainerStatus.CREATED,
    "running": ContainerStatus.RUNNING,
    "paused": ContainerStatus.PAUSED,
    "pausing": ContainerStatus.PAUSED,
    "stopped": ContainerStatus.EXITED,
}
# Fail-safe for a status we do not recognize (containerd's UNKNOWN, or a future task state):
# treat it as CREATED so the lifecycle sync neither reports it running nor destroys it. Reaping a
# genuinely dead container is still covered by the task-exit event and the orphan-kernel observer.
_UNRECOGNIZED_STATUS = ContainerStatus.CREATED


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
    caps: frozenset[str],
    arch: str = CURRENT_ARCH,
) -> dict[str, Any]:
    """Convert a Docker-format seccomp profile (archMap + per-syscall includes/excludes) to the
    OCI runtime-spec linux.seccomp shape. Per-syscall includes/excludes are evaluated against the
    container's ``caps``/``arch`` and the host kernel (see _seccomp_rule_applies) so cap-gated
    syscalls stay gated — matching how Docker resolves the profile at container creation.

    ``caps`` is deliberately required, with no default: it must be the set the container will
    ACTUALLY hold. Defaulting it silently resolves cap-gated syscall groups (the ptrace group,
    mlock, bpf, ...) against the wrong capability set, and the container then holds a capability
    whose syscalls seccomp still denies.

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


class ContainerdKernelCreationContext(AbstractKernelCreationContext[ContainerdKernel]):
    _session_network: ContainerdSessionNetwork
    _net_meta: SessionNetMeta | None
    _container_id: str
    _session_id: str
    _oci_mounts: list[Mount]
    domain_socket_proxies: list[DomainSocketProxy]
    _scratch_dir: Path | None
    _pending_spec: Any
    _accel_spec: AcceleratorSpec
    _agent_sock_path: Path | None
    _port_pool: PortPool
    _port_forwarder: PortPublisher | None
    # The AppArmor profile the agent loaded at startup, or None if the host cannot give us one.
    _apparmor_profile: str | None
    # (host_port, container_port) for the REPL and every service port, captured at reserve time and
    # turned into DNAT rules once the container's address is known.
    # (host_port, container_port, host_ip): the host address is where the service is published —
    # 127.0.0.1 for a protected service, the configured bind-host for an ordinary one — so a
    # protected service (e.g. a storage node's ttyd) is not exposed on every interface. None means
    # every local address (the pre-S1/S2 behaviour, kept only for the empty-bind-host default).
    _host_port_map: list[tuple[int, int, str | None]]
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
        apparmor_profile: str | None = None,
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
        self.domain_socket_proxies = []
        self._pending_spec = None
        self._scratch_dir = None
        self._accel_spec = AcceleratorSpec()
        self._port_pool = port_pool
        self._port_forwarder = port_forwarder
        self._apparmor_profile = apparmor_profile
        self._host_port_map = []
        self._repl_host_ports = ()

    @override
    async def get_extra_envs(self) -> Mapping[str, str]:
        return {}

    @override
    async def prepare_resource_spec(
        self,
    ) -> tuple[KernelResourceSpec, Mapping[str, Any] | None]:
        if self.restarting:
            # A restart must keep the allocation the kernel already has. Re-deriving it from
            # resource_slots re-runs the allocator, which may hand out a different cpuset or a
            # different accelerator device than the one the kernel's processes are pinned to.
            # resource.txt in the scratch is that allocation, written at creation.
            resource_txt = (
                self.local_config.container.scratch_root
                / str(self._container_id)
                / "config"
                / "resource.txt"
            )

            def _read() -> KernelResourceSpec:
                with resource_txt.open() as f:
                    return KernelResourceSpec.read_from_file(f)

            return await asyncio.to_thread(_read), None

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

    def _memory_tmp_dir(self) -> Path:
        """The host tmpfs bind-mounted at /tmp under the MEMORY scratch type (Docker parity)."""
        return self.local_config.container.scratch_root / f"{self._container_id}_tmp"

    @override
    async def prepare_scratch(self) -> None:
        # Create the per-kernel scratch dirs (config/ + work/) and seed the default dotfiles.
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
        elif sys.platform.startswith("linux") and scratch_type == ScratchType.MEMORY:
            # MEMORY means the scratch itself lives in RAM: mount a tmpfs over it, as the Docker
            # backend does. Backing it with a container-private tmpfs at /tmp instead — which is
            # what this used to do — left /home/work on disk (so the scratch was not in memory at
            # all) and left /tmp with the kernel's default tmpfs size of half the host's RAM,
            # unbounded by anything.
            await asyncio.to_thread(scratch_dir.mkdir, parents=True, exist_ok=True)
            await asyncio.to_thread(self._memory_tmp_dir().mkdir, parents=True, exist_ok=True)
            await create_scratch_filesystem(scratch_dir, _MEMORY_SCRATCH_SIZE_MIB)
            await create_scratch_filesystem(self._memory_tmp_dir(), _MEMORY_SCRATCH_SIZE_MIB)

        def _prepare() -> None:
            config_dir.mkdir(parents=True, exist_ok=True)
            config_dir.chmod(0o755)
            work_dir.mkdir(parents=True, exist_ok=True)
            work_dir.chmod(0o755)
            if self.restarting:
                # A restart reuses the scratch. Re-seeding would overwrite the user's own .bashrc
                # with ours, which is why the Docker backend seeds only on first creation.
                return
            self._clone_dotfiles(work_dir)
            # /home/work is the user's home, and the container's PID 1 drops to LOCAL_USER_ID
            # before it ever reaches them (runner/entrypoint.sh). A root agent writes them as
            # root, so without this the user cannot write to their own home directory: Jupyter
            # cannot save, the shell cannot write history, and the dotfiles we just seeded are
            # theirs in name only. The container cannot fix it for itself either — a recursive
            # chown inside would also take ownership of every vfolder mounted under /home/work.
            self._chown_paths_if_root([
                work_dir,
                work_dir / ".jupyter",
                work_dir / ".jupyter" / "custom",
                *(work_dir / ".jupyter" / "custom" / name for name in _JUPYTER_CUSTOM_FILES),
                *(work_dir / name for name in _SEEDED_DOTFILES),
            ])

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
            *((name, work_dir / name) for name in _SEEDED_DOTFILES),
        ]
        for src_name, dst in copies:
            src = _runner_file(src_name)
            if src.exists():
                shutil.copy(src.resolve(), dst)

    @override
    async def get_intrinsic_mounts(self) -> Sequence[Mount]:
        # The kernel runner requires the per-kernel scratch dirs: config/ (RO) at
        # /home/config and work/ (RW) at /home/work. prepare_scratch created them.

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
        # MEMORY scratch: /tmp is the host tmpfs prepare_scratch mounted, bound in — not a
        # container-private tmpfs, whose default size is half the host's RAM and which the agent
        # cannot see or reclaim. Docker binds the same directory.
        if self.local_config.container.scratch_type == ScratchType.MEMORY:
            mounts.append(
                Mount(
                    MountTypes.BIND,
                    self._memory_tmp_dir(),
                    Path("/tmp"),
                    MountPermission.READ_WRITE,
                )
            )
        # Coredumps. With debug.coredump enabled the host's core_pattern writes cores into this
        # directory, so the container has to see it at the path the pattern names — otherwise the
        # kernel cannot write the core at all and the feature is silently inert.
        if self.local_config.debug.coredump.enabled:
            mounts.append(
                Mount(
                    MountTypes.BIND,
                    self.local_config.debug.coredump.path,
                    self.local_config.debug.coredump.core_path,
                    MountPermission.READ_WRITE,
                )
            )
        # Domain-socket proxies (the image importer and other special service containers that need
        # a host socket, e.g. the docker socket). The host socket itself is never bind-mounted:
        # each one gets a per-kernel proxy socket that forwards to it, so the container talks to us
        # and we decide what reaches the host. Same construction as the Docker backend — it needs
        # no container runtime at all, which is why it ports over unchanged.
        ipc_base_path = self.local_config.agent.ipc_base_path
        for host_sock_path in self.internal_data.get("domain_socket_proxies", []):
            proxy_dir = ipc_base_path / "proxy"
            await asyncio.to_thread(partial(proxy_dir.mkdir, parents=True, exist_ok=True))
            host_proxy_path = proxy_dir / f"{secrets.token_hex(12)}.sock"
            proxy_server = await asyncio.start_unix_server(
                aiotools.apartial(proxy_connection, Path(host_sock_path)), str(host_proxy_path)
            )
            await asyncio.to_thread(host_proxy_path.chmod, 0o666)
            self.domain_socket_proxies.append(
                DomainSocketProxy(Path(host_sock_path), host_proxy_path, proxy_server)
            )
            mounts.append(
                Mount(
                    MountTypes.BIND,
                    host_proxy_path,
                    Path(host_sock_path),
                    MountPermission.READ_WRITE,
                )
            )
        # The in-container agent socket (host<->container PID translation, jail status) for
        # libbaihook/jail. The *directory* is mounted, not the socket file, and the entrypoint links
        # /opt/kernel/agent.sock to it: a bind-mounted socket file pins the inode it had at mount
        # time, and that inode dies with the agent process — so every kernel that outlived an agent
        # restart was left holding a dangling socket, and its hook and jail lost PID translation
        # with no error anywhere. Through the directory, the socket the restarted agent re-creates
        # is resolved at connect time. The directory is per agent, so a kernel cannot reach the
        # socket of another agent on the same host.
        if self._agent_sock_path is not None:
            mounts.append(
                Mount(
                    MountTypes.BIND,
                    self._agent_sock_path.parent,
                    Path("/opt/kernel/agent-sock"),
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
        # Deep-learning sample notebooks at /home/work/samples, read-only, for the images they are
        # meant for. The Docker backend mounts a named Docker volume; containerd has no volume
        # registry, so the operator names the directory (unset = no samples, which is also what a
        # Docker node without the volume gets).
        if (samples := self.local_config.container.deeplearning_samples_path) and (
            is_deeplearning_image(self.image_ref.short)
        ):
            samples_dir = Path(samples)
            if samples_dir.is_dir():
                mounts.append(
                    Mount(
                        MountTypes.BIND,
                        samples_dir,
                        Path("/home/work/samples"),
                        MountPermission.READ_ONLY,
                    )
                )
            else:
                log.warning(
                    "container.deeplearning-samples-path points at {}, which is not a directory;"
                    " the kernel starts without /home/work/samples",
                    samples_dir,
                )
        return mounts

    @property
    @override
    def repl_ports(self) -> Sequence[int]:
        return (2000, 2001)

    @property
    @override
    def protected_services(self) -> Sequence[str]:
        # On a storage resource group, ttyd is a shell into the storage node: it must not be
        # exposed like an ordinary service app. Docker makes the same distinction.
        match self.local_config.agent.scaling_group_type:
            case ResourceGroupType.STORAGE:
                return ("ttyd",)
            case _:
                return ()

    @override
    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        # BEP-1062: set up this node's per-session data plane and register the per-session
        # orchestrator. Per-container CNI attach happens in start_container against the task
        # PID. Multi-node sessions carry a manager-provided network_config (vxlan overlay);
        # single-node sessions have none, so synthesize a node-local BRIDGE config — the
        # same CNI attach path then applies, with no nerdctl-managed network.
        network_config = dict(cluster_info.get("network_config") or {})
        if not network_config.get("backend"):
            # No BEP-1062 backend in the config: either there is no cluster network at all, or the
            # manager selected a v1 driver (`mode` names it — 'overlay' is Docker Swarm and is the
            # DEFAULT inter-container driver). Only the first is ours to serve.
            #
            # A v1 driver must NOT be quietly downgraded to a node-local bridge: the kernels would
            # come up on separate per-node bridges, unable to reach each other, and nothing would
            # say so. Refuse it, and name the fix. (The manager refuses this pairing too; this is
            # the backstop for an agent talking to a manager that does not yet.)
            mode = str(network_config.get("mode") or "bridge")
            if mode != "bridge":
                raise UnsupportedResource(
                    f"the manager selected the '{mode}' cluster-network driver, which the"
                    " containerd backend cannot serve (it speaks the BEP-1062 'cni' driver)."
                    " Set the manager's network.inter-container.default-driver to 'cni'."
                )
            # SessionNetMeta requires a subnet, but a single-node BRIDGE session has no
            # cluster-wide one: the bridge backend cuts this session's block out of the node's
            # own pool and never reads this field. Name the pool, so the value is at least true.
            network_config = {
                "backend": str(NetworkBackendKind.BRIDGE),
                "subnet": str(self.local_config.container.local_subnet_layout().pool),
            }
        # The container id IS the kernel id here, and the kernel claims the session network from
        # this moment — long before its container exists — so a sibling that dies during the pull
        # cannot take the session's data plane down under it.
        self._net_meta = await self._session_network.ensure_session(
            self._session_id, self._container_id, network_config
        )

    async def _peer_host_map(
        self, cluster_info: ClusterInfo, environ: Mapping[str, str]
    ) -> tuple[dict[str, str], str | None]:
        """``(hostname -> IP, the LOCAL address to pin this kernel at)`` for a cluster session.

        The map goes into /etc/hosts and always covers *every* peer, this kernel included — a
        kernel whose own name did not resolve to its real address would bind its rendezvous server
        (torchrun/c10d, MPI OOB) at the wrong one and its peers could not reach it.

        Two sources, by cluster mode:
        - **Multi-node**: the manager pre-assigns overlay IPs and hands them down as ``cluster_hosts``
          (central IPAM). Used verbatim, and nothing is pinned: the overlay attach already puts this
          kernel at the address the manager assigned it.
        - **Single-node**: there is no central assignment — every kernel is on this node's one LOCAL
          bridge — so this agent lays the peers out deterministically in the session's LOCAL subnet
          (`cluster_host_ips`) and pins each kernel at its own address, which is what makes the map
          true rather than merely advertised. The ordered peer list is the session-wide
          BACKENDAI_CLUSTER_HOSTS (identical for every kernel), so every kernel computes the same map
          without coordinating.
        """
        if cluster_hosts := (cluster_info.get("cluster_hosts") or {}):
            return dict(cluster_hosts), None
        # Only a SINGLE_NODE session may be laid out locally, and the cluster mode is the only thing
        # that says so. An empty cluster_hosts does NOT mean single-node: a MULTI_NODE session on a
        # PERSISTENT network gets the bridge backend and no manager-assigned addresses either, and
        # laying its peers out in THIS node's /26 would hand every node a different, wrong map
        # naming addresses that exist only on its own bridge.
        if cluster_info.get("mode") is not ClusterMode.SINGLE_NODE:
            return {}, None
        peers = [h for h in (environ.get("BACKENDAI_CLUSTER_HOSTS") or "").split(",") if h]
        if len(peers) <= 1:
            return {}, None  # not a cluster (or the lone kernel): only the baseline is needed
        subnet = await self._session_network.local_subnet_of(self._session_id)
        if subnet is None:
            return {}, None  # helper mode owns the addresses; peer resolution is its to add
        mapping = cluster_host_ips(subnet, peers)
        own = environ.get("BACKENDAI_CLUSTER_HOST")
        if own not in mapping:
            # Publishing a map this kernel is not in would be worse than failing: it would take a
            # dynamic address — the first free one, which is the address the map gives peers[0] —
            # and steal it from the peer pinned there.
            raise ContainerCreationError(
                f"a kernel of session {self._session_id} is not in its own session's peer list"
                f" (BACKENDAI_CLUSTER_HOST={own!r}, BACKENDAI_CLUSTER_HOSTS={peers})"
            )
        return mapping, mapping[own]

    def _write_etc_hosts(
        self, peers: Mapping[str, str], environ: Mapping[str, str]
    ) -> Mount | None:
        """Write /etc/hosts and return a bind mount for it.

        Unconditional now, not only for cluster sessions: containerd/runc (unlike dockerd) does not
        synthesize the file at all, so without this even an ordinary kernel has no ``localhost`` and
        no entry for its own hostname — the hostname the agent set is then unresolvable. Cluster
        peers (`_peer_host_map`) are added on top, this kernel's own entry among them.
        """
        if self._scratch_dir is None:
            return None
        lines = ["127.0.0.1\tlocalhost", "::1\tlocalhost ip6-localhost ip6-loopback"]
        lines += [f"{ip}\t{hostname}" for hostname, ip in peers.items()]
        own_hostname = environ.get("BACKENDAI_CLUSTER_HOST")
        if own_hostname and own_hostname not in peers:
            # A lone kernel has no peer map, but its own name must still resolve or a
            # `gethostbyname(gethostname())` — a very common way for a process to find its own
            # address — fails outright.
            lines.append(f"127.0.1.1\t{own_hostname}")
        hosts_file = self._scratch_dir / "config" / "hosts"
        hosts_file.write_text("\n".join(lines) + "\n")
        return Mount(MountTypes.BIND, hosts_file, Path("/etc/hosts"), MountPermission.READ_ONLY)

    def _prepare_resolv_conf(self) -> Mount | None:
        """Write this kernel's /etc/resolv.conf and return a bind mount for it.

        Unconditional, unlike /etc/hosts: every container needs a resolver, not just clustered
        ones. Without this the image's own (usually absent) resolv.conf is all the container gets
        and no name resolves. See containerd/dns.py for how the nameservers are chosen.
        """
        if self._scratch_dir is None:
            return None
        resolv = resolve_container_dns(self.local_config.container.dns or ())
        resolv_file = self._scratch_dir / "config" / "resolv.conf"
        resolv_file.write_text(resolv.render())
        return Mount(
            MountTypes.BIND, resolv_file, Path("/etc/resolv.conf"), MountPermission.READ_ONLY
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
            paths_to_chown: list[Path] = []
            if sshkey is not None:
                priv = ssh_dir / "id_cluster"
                priv.write_text(sshkey["private_key"])
                priv.chmod(0o600)
                pub = ssh_dir / "id_cluster.pub"
                pub.write_text(sshkey["public_key"])
                paths_to_chown.extend([priv, pub])
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
            if host_key.is_file():
                paths_to_chown.append(host_key)
            # A root agent writes these as root, and 0600 means root-only. The user the kernel runs
            # as could then not read its own cluster key — which is the whole point of the file:
            # passwordless chief<->worker SSH for MPI/torchrun. The Docker backend chowns the same
            # three (docker/agent.py, prepare_ssh).
            self._chown_paths_if_root(paths_to_chown)

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
            # Union across plugins: two accelerators on one kernel each get what they asked for.
            cap_add=[*prev.cap_add, *(c for c in spec.cap_add if c not in prev.cap_add)],
            sysctls={**prev.sysctls, **spec.sysctls},
            rlimits=[
                *prev.rlimits,
                *(r for r in spec.rlimits if r["type"] not in {p["type"] for p in prev.rlimits}),
            ],
            additional_gids=[
                *prev.additional_gids,
                *(g for g in spec.additional_gids if g not in prev.additional_gids),
            ],
            ipc_host=prev.ipc_host or spec.ipc_host,
            seccomp_unconfined=prev.seccomp_unconfined or spec.seccomp_unconfined,
        )

    @override
    async def generate_accelerator_mounts(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> list[MountInfo]:
        """The mounts an accelerator plugin needs in the container, and the per-kernel directory it
        writes them from.

        Not every accelerator is served by the device nodes and env vars alone: the IPU plugin
        writes a per-device ``ipuof`` config into this directory and mounts it, and the Hyperaccel
        LPU plugin mounts its runtime libraries. Returning nothing here (as this used to) drops
        them silently — the kernel starts, and the device it was allocated is unusable from inside.
        """
        if self._scratch_dir is None:
            return []
        src_path = self._scratch_dir / "config" / str(computer.key)
        await asyncio.to_thread(src_path.mkdir, parents=True, exist_ok=True)
        return await computer.generate_mounts(src_path, device_alloc)

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

    async def _append_container_id_to_resource_spec(self) -> None:
        """Append ``CID=`` to resource.txt, once the container it names exists.

        This is the only place the in-container side learns its own container id, and the jail /
        libbaihook abuse reporter puts it in the report the agent then acts on (agent.py reads
        ``body["CID"]``). Appended after creation, and to resource.txt only — resource_base.txt is
        the pristine copy the runner diffs against, and the Docker backend keeps it that way too.
        """
        if self._scratch_dir is None:
            return
        resource_txt = self._scratch_dir / "config" / "resource.txt"

        def _append() -> None:
            with resource_txt.open("a") as f:
                f.write(f"CID={self._container_id}\n")

        await asyncio.to_thread(_append)

    def _chown_paths_if_root(self, paths: Sequence[Path]) -> None:
        """Hand the given scratch paths to the uid/gid the container's runner drops to.

        The container's PID 1 starts as root, but the runner switches to LOCAL_USER_ID/
        LOCAL_GROUP_ID (see AbstractAgent.create_kernel), so anything we write into the scratch as
        root — ssh keys, dotfiles, bootstrap.sh — is unwritable (and, at 0600, unreadable) by the
        user unless it is chowned here. Only possible when the agent itself runs as root.
        """
        if os.geteuid() != 0:
            return
        uid = self.get_overriding_uid()
        gid = self.get_overriding_gid()
        if uid is None and gid is None:
            if KernelFeatures.UID_MATCH not in self.kernel_features:
                return
            uid = self.local_config.container.kernel_uid
            gid = self.local_config.container.kernel_gid
        for p in paths:
            try:
                stat_result = p.stat()
            except FileNotFoundError:
                # A seeded file the runner package does not ship, or a key generation that failed:
                # the caller lists what it means to hand over, not what it managed to write.
                continue
            int_uid = int(uid) if uid is not None else stat_result.st_uid
            int_gid = int(gid) if gid is not None else stat_result.st_gid
            try:
                os.chown(p, int_uid, int_gid)
            except OSError as e:
                log.warning("failed to chown {} to {}/{}: {!r}", p, int_uid, int_gid, e)

    async def _provision_internal_data(self, resource_spec: KernelResourceSpec) -> None:
        """Materialize the manager-supplied ``internal_data`` into the scratch (Docker parity).

        Everything here lands in the scratch dirs that are bind-mounted as /home/work and
        /home/config, so it needs no container access — but without it the user's SSH login,
        dotfiles, bootstrap script and registry credentials silently never appear.
        """
        if self._scratch_dir is None:
            return
        scratch_dir = self._scratch_dir
        work_dir = scratch_dir / "work"
        config_dir = scratch_dir / "config"
        internal_data = self.internal_data
        bootstrap = self.kernel_config.get("bootstrap_script")

        def _write() -> None:
            chown_targets: list[Path] = []

            if bootstrap:
                bootstrap_path = work_dir / "bootstrap.sh"
                bootstrap_path.write_text(bootstrap)
                chown_targets.append(bootstrap_path)

            if docker_creds := internal_data.get("docker_credentials"):
                (config_dir / "docker-creds.json").write_text(dump_json_str(docker_creds))

            # Skip when the user mounted their own .ssh vfolder — theirs wins (Docker parity).
            ssh_keypair = internal_data.get("ssh_keypair")
            has_ssh_mount = any(
                str(mount.target) == "/home/work/.ssh" for mount in resource_spec.mounts
            )
            if ssh_keypair and not has_ssh_mount:
                pubkey = ssh_keypair["public_key"].encode("ascii")
                privkey = ssh_keypair["private_key"].encode("ascii")
                ssh_dir = work_dir / ".ssh"
                ssh_dir.mkdir(parents=True, exist_ok=True)
                ssh_dir.chmod(0o700)
                (ssh_dir / "authorized_keys").write_bytes(pubkey)
                (ssh_dir / "authorized_keys").chmod(0o600)
                if not (ssh_dir / "id_rsa").is_file():
                    (ssh_dir / "id_rsa").write_bytes(privkey)
                    (ssh_dir / "id_rsa").chmod(0o600)
                (work_dir / "id_container").write_bytes(privkey)
                (work_dir / "id_container").chmod(0o600)
                chown_targets += [
                    ssh_dir,
                    ssh_dir / "authorized_keys",
                    ssh_dir / "id_rsa",
                    work_dir / "id_container",
                ]

            # Higher-priority dotfiles come last so they overwrite the earlier ones.
            for dotfile in internal_data.get("dotfiles", []):
                path = dotfile["path"]
                if path.startswith("/"):
                    if path.startswith("/home/"):
                        # /home/work/... and /home/config/... are this kernel's scratch.
                        file_path = scratch_dir / "/".join(path.split("/")[2:])
                    else:
                        # An absolute path outside /home cannot be reached from the host: it lives
                        # in the image's rootfs, not in a bind mount. Docker has the same blind
                        # spot (it writes to the agent's own filesystem), so skip it loudly rather
                        # than scribbling on the host.
                        log.warning(
                            "ignoring dotfile at {}: only paths under /home are in the scratch",
                            path,
                        )
                        continue
                else:
                    file_path = work_dir / path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                content = dotfile["data"]
                if not content.endswith("\n"):
                    content += "\n"
                file_path.write_text(content)
                file_path.chmod(int(dotfile["perm"], 8))
                chown_targets.append(file_path)
                # The intermediate dirs get 0700, NOT the dotfile's own mode: a file mode like
                # 0644 on a directory clears its execute bit, so the user could not traverse into
                # it and would never reach the dotfile. 0700 keeps it private and usable.
                node = file_path.parent
                while node != work_dir and node.is_relative_to(work_dir):
                    node.chmod(0o700)
                    chown_targets.append(node)
                    node = node.parent

            self._chown_paths_if_root(chown_targets)

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
        # A protected service is bound to loopback so it cannot be reached off-node (a storage
        # node's ttyd is an interactive shell into the container); an ordinary service is bound to
        # the operator's configured bind-host, which keeps kernel service ports off any interface
        # the operator did not choose. Docker makes the same two-way distinction. bind_host defaults
        # to "" — every local address — so the ordinary case is unchanged until an operator sets it.
        protected = set(self.protected_services)
        bind_host = self.local_config.container.bind_host or None
        # No sshd special case: the manager only builds a cluster SSH port mapping for HOST-network
        # sessions, and those never reach this backend.
        for sport in service_ports:
            host_ip = "127.0.0.1" if sport["name"] in protected else bind_host
            host_ports: list[int] = []
            for container_port in sport["container_ports"]:
                host_port = self._port_pool.acquire()
                host_ports.append(host_port)
                self._host_port_map.append((host_port, container_port, host_ip))
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
        # User-facing provisioning from internal_data: ssh keypair, dotfiles, bootstrap script,
        # registry credentials.
        await self._provision_internal_data(resource_spec)
        # containerd/runc (unlike Docker) neither synthesizes /etc/hosts nor provides cluster DNS,
        # so write one (localhost + own hostname) and add peer resolution for cluster sessions.
        peers, static_ip = await self._peer_host_map(cluster_info, environ)
        if static_ip is not None:
            # Single-node cluster: pin this kernel at the address its peers expect, via the same
            # kernel_config channel the overlay uses (the bridge backend reads it at attach).
            cast(dict[str, Any], self.kernel_config)["local_static_ip"] = static_ip
        if (hosts_mount := self._write_etc_hosts(peers, environ)) is not None:
            self._oci_mounts.append(hosts_mount)
        # containerd/runc provides no resolver either (dockerd synthesizes one per container).
        if (resolv_mount := self._prepare_resolv_conf()) is not None:
            self._oci_mounts.append(resolv_mount)
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
        # The rest of the accelerator's HostConfig: capabilities, sysctls, rlimits, supplementary
        # groups and host IPC. The NPU/IPU/ROCm plugins depend on these (memlock, host IPC, the
        # device's group) and a container that starts without them fails only later, inside the
        # vendor runtime.
        extra_caps = list(self._accel_spec.cap_add)
        if self._accel_spec.sysctls:
            oci_spec["sysctls"] = dict(self._accel_spec.sysctls)
        if self._accel_spec.rlimits:
            oci_spec["rlimits"] = list(self._accel_spec.rlimits)
        if self._accel_spec.additional_gids:
            oci_spec["additional_gids"] = list(self._accel_spec.additional_gids)
        if self._accel_spec.ipc_host:
            oci_spec["ipc_host"] = True
        # /dev/shm sizing from the session's resource_opts (parity with Docker's ShmSize).
        shmem = (self.kernel_config.get("resource_opts") or {}).get("shmem")
        if shmem:
            oci_spec["shmem"] = int(shmem)
        # The LOCAL bridge is a node-local NAT subnet, so the container's address is private and
        # unroutable off this node — an AppProxy may run on any host. Publish each service (and the
        # REPL, which the agent itself dials at kernel_host) on a host port, DNAT'd to the container
        # once its address is known at start. Same contract as the Docker backend's PortBindings.
        self._reserve_host_ports(service_ports)
        # Identify the container the way the Docker backend does. These labels are the only thing
        # external tooling (the watcher, operators' `ctr`/`nerdctl ps` filters) and our own
        # restart-time scan have to go on; with just kernel-id/session-id, scan_running_kernels
        # falls back to kernelspec "1" and nothing can tell whose kernel this is.
        oci_spec["labels"] = {
            **oci_spec.get("labels", {}),
            LabelName.AGENT_ID: str(self.agent_id),
            LabelName.OWNER_AGENT: str(self.agent_id),
            LabelName.KERNEL_SPEC: str(self.kspec_version),
            LabelName.BLOCK_SERVICE_PORTS: (
                "1" if self.internal_data.get("block_service_ports", False) else "0"
            ),
            LabelName.SERVICE_PORTS: ",".join(
                f"{sp['name']}:{sp['protocol']}:{sp['container_ports'][0]}"
                for sp in service_ports
                if sp.get("container_ports")
            ),
        }
        if (owner_user := self.ownership_data.owner_user_id_to_str) is not None:
            oci_spec["labels"][LabelName.OWNER_USER] = owner_user
        if (owner_project := self.ownership_data.owner_project_id_to_str) is not None:
            oci_spec["labels"][LabelName.OWNER_PROJECT] = owner_project
        # PID 1 must reap the orphans the workload leaves behind, or they accumulate as zombies
        # until the container runs out of PIDs. The Docker backend gets this from dockerd
        # (HostConfig.Init -> its bundled tini); runc injects no init, and without this the kernel
        # runner itself is PID 1 and reaps nothing. Tell the entrypoint to run the program under
        # our own PID-1 reaper instead (runner/init.py). This mirrors HostConfig.Init and is set on
        # exactly the containers Docker sets it for: kernel containers.
        oci_spec["env"]["BACKENDAI_INIT"] = "1"
        # The container's own identity inside the cluster. Docker sets Hostname to cluster_hostname
        # (main1/sub1/...); leaving runc's default meant `hostname` reported a container-id prefix,
        # which MPI/torchrun use to identify the rank they are running as.
        oci_spec["hostname"] = self.kernel_config["cluster_hostname"]
        # Docker pins WorkingDir to /home/work rather than trusting the image's.
        oci_spec["cwd"] = "/home/work"

        # AppArmor, unless the jail sandbox is in play — the jail ptrace-traces the container's
        # processes, and Docker likewise drops to apparmor=unconfined for it.
        is_jail = self.local_config.container.sandbox_type == ContainerSandboxType.JAIL
        if not is_jail and self._apparmor_profile is not None:
            oci_spec["apparmor_profile"] = self._apparmor_profile
        if is_jail:
            # The jail enforces syscall policy by ptrace-tracing the container's processes, so it
            # needs CAP_SYS_PTRACE. Docker's jail path adds the same capability; without it the
            # jail's tracer cannot attach and its confinement silently degrades to nothing.
            extra_caps.append("CAP_SYS_PTRACE")
        if extra_caps:
            oci_spec["extra_caps"] = extra_caps
        # The capability set the container will ACTUALLY hold. The seccomp profile must be
        # resolved against this, not against the defaults: Docker's profile gates whole syscall
        # groups on a capability (the ptrace group — ptrace/process_vm_readv/kcmp/pidfd_getfd —
        # on CAP_SYS_PTRACE, mlock on CAP_IPC_LOCK, and so on). Resolving against the defaults
        # while granting extra capabilities produces the worst failure mode there is: the process
        # holds the capability, and the syscall it needs it for still returns EPERM.
        effective_caps = frozenset(_DEFAULT_CAPS) | frozenset(extra_caps)
        # seccomp hardening. Skipped under the jail sandbox (which does its own ptrace-based
        # syscall filtering) and when a compute plugin asked for seccomp=unconfined — the vendor
        # runtimes that do (ROCm, Furiosa) issue syscalls the default profile blocks.
        if not is_jail and not self._accel_spec.seccomp_unconfined:
            seccomp_path = self.resolve_krunner_filepath("runner/default-seccomp.json")
            if seccomp_path.exists():
                profile = _docker_seccomp_to_oci(
                    json.loads(seccomp_path.read_text()), caps=effective_caps
                )
                # Syscalls the compute plugins additionally need (e.g. io_uring). The Docker
                # backend appends the same list; without it they get EPERM.
                if self.additional_allowed_syscalls:
                    profile.setdefault("syscalls", []).append({
                        "names": list(self.additional_allowed_syscalls),
                        "action": "SCMP_ACT_ALLOW",
                        "args": [],
                    })
                oci_spec["seccomp"] = profile
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
            await self._append_container_id_to_resource_spec()
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
            await self._provision_sudo_session()
        except Exception:
            if not published:
                self._port_pool.release_many([hp for hp, _, _ in self._host_port_map])
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
            "host_ports": [host_port for host_port, _, _ in self._host_port_map],
            "domain_socket_proxies": self.domain_socket_proxies,
            "block_service_ports": self.internal_data.get("block_service_ports", False),
        }

    async def _provision_sudo_session(self) -> None:
        """Grant the in-container user passwordless sudo when the session asked for it.

        Must run after the task is started (Docker parity): /etc/sudoers.d lives in the image's
        rootfs, not in any bind mount, so it can only be written from inside the container. The
        exec runs as root — the container's init user — regardless of the uid the runner drops to.
        """
        if not self.internal_data.get("sudo_session_enabled", False):
            return
        result = await self._session_network.exec_in_container(
            self._container_id,
            [
                "sh",
                "-c",
                'mkdir -p /etc/sudoers.d && echo "work ALL=(ALL:ALL) NOPASSWD:ALL"'
                " > /etc/sudoers.d/01-bai-work",
            ],
            uid=0,
            gid=0,
        )
        if result.exit_code != 0:
            raise ContainerCreationError(
                container_id=self._container_id,
                message=(
                    "sudoers provision failed: "
                    f"{result.stderr.decode('utf-8', errors='replace').strip()}"
                ),
            )

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
    # The validated VTEP (see network.vtep); None when this node holds no address that can anchor
    # a vxlan tunnel, which disables multi-node overlay sessions here.
    _vtep_ip: str | None
    _event_monitor_task: asyncio.Task[None] | None
    # Where each containerd task event is handled, off the subscribe loop (see _monitor_task_events).
    _event_task_group: aiotools.PersistentTaskGroup
    _agent_sock_path: Path
    _agent_sock_task: asyncio.Task[None] | None
    _port_forwarder: PortPublisher
    _kernel_recovery: BaseKernelRegistryRecovery
    # The AppArmor profile loaded at startup, handed to every kernel we create; None when the host
    # has no AppArmor (kernels then run unconfined, as they did before).
    _apparmor_profile: str | None
    _kernel_recovery_adapter: KernelRecoveryDataAdapter

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # The container runtime is the OCI runtime interface, implemented by the native
        # containerd gRPC client (no nerdctl/ctr CLI). The agent owns it and injects it into
        # the network facade; opened in __ainit__.
        self._runtime = ContainerdGrpcRuntime(
            namespace="backend-ai",
            registry_hosts_dir=self.local_config.container.registry_hosts_dir,
        )
        self._event_monitor_task = None
        self._event_task_group = aiotools.PersistentTaskGroup()
        # In-container helpers (libbaihook LD_PRELOAD hook, jail) talk back to the agent over
        # a per-agent socket for host<->container PID translation + jail status. Bind ZMQ REP
        # directly on this ipc:// UNIX socket and bind-mount it into each container as
        # /opt/kernel/agent.sock — no socat relay / TCP hop (cf. DockerAgent).
        ipc_base_path = self.local_config.agent.ipc_base_path
        # Its own directory, because that directory is what gets mounted into every kernel (see
        # get_intrinsic_mounts): a shared one would expose every agent's socket on the host.
        self._agent_sock_path = ipc_base_path / "container" / f"agent-{self.id}" / "agent.sock"
        self._agent_sock_task = None
        # Cluster networking is delegated to the BEP-1062 agent.network stack via a
        # (verified) facade; the kernel-creation lifecycle will drive it. The vxlan uplink
        # must be the interface carrying this node's VTEP (host_ip) — deriving it from the
        # host_ip keeps the overlay on the same L2 the agents advertise on, instead of a
        # hard-coded eth0.
        container_cfg = self.local_config.container
        self._host_ip = str(container_cfg.advertised_host or container_cfg.bind_host)
        # Validated once, here: it is what peers program into their FDB, so an address this node
        # cannot be reached at must never reach a session's membership record. None disables the
        # multi-node overlay on this node (ensure_session then refuses a vxlan session outright);
        # single-node sessions never touch it.
        self._vtep_ip = usable_vtep(self._host_ip)
        # When a privileged network helper is configured, delegate all CAP_NET_ADMIN/
        # CAP_SYS_ADMIN host networking to it so this agent process needs no such privilege.
        self._session_network = build_containerd_session_network(
            self.etcd,
            agent_id=str(self.id),
            host_ip=self._host_ip,
            uplink=uplink_for_ip(self._vtep_ip or self._host_ip),
            runtime=self._runtime,
            helper_socket=self.local_config.agent.network_helper_socket,
            local_subnet_layout=container_cfg.local_subnet_layout(),
            vtep_ip=self._vtep_ip,
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
        # Advertise what this node's fabric can do, so the manager selects a data plane from facts
        # rather than from a default. Without this the capability key never exists and the whole
        # selector is inert — it silently answers "vxlan" for every session whatever the host is.
        # native_routing_ok stays conservative (False): a single-node boot probe cannot confirm the
        # fabric forwards container-IP frames, and asserting it would select a backend the agent
        # does not implement.
        try:
            await publish_caps(
                self.etcd,
                str(self.id),
                await probe_caps(uplink_for_ip(self._vtep_ip or self._host_ip)),
            )
        except Exception:
            log.exception("could not publish this agent's network capabilities")
        # Advertise this node's VTEP so the manager can pre-seed session membership and
        # eliminate the peer-publish race for multi-node overlays (BEP-1062). Only the validated
        # address is ever published; with none, say so once at startup, where an operator can act on
        # it, rather than only at the first vxlan session that ensure_session then refuses.
        if self._vtep_ip is not None:
            await publish_vtep(self.etcd, str(self.id), self._vtep_ip)
        else:
            # Retract, not merely skip: the key is durable, so an address published on an earlier
            # boot would otherwise keep being pre-seeded into peers' FDBs long after this node
            # stopped holding it.
            await withdraw_vtep(self.etcd, str(self.id))
            log.warning(
                "no usable VTEP: container.advertised-host/bind-host ({!r}) is not a routable"
                " unicast IPv4 address held by an interface of this host that is up. Single-node"
                " sessions work; a multi-node overlay (vxlan) session scheduled here will be"
                " refused until it is set.",
                self._host_ip,
            )
        # dockerd loads its docker-default profile at startup and confines every container with it;
        # containerd loads nothing. Load ours here so kernels are no less confined than under
        # Docker. None means the host cannot give us AppArmor (already logged) — kernels then run
        # unconfined, as they did before this existed.
        self._apparmor_profile = await ensure_profile_loaded()
        # Log kernels through our own writer instead of letting the shim append to a file forever.
        # containerd starts the launcher below and pipes each container's stdout/stderr into it, so
        # we own the write end exactly as dockerd's log driver does — which is what makes max-size /
        # max-file rotation possible at all. The writer is a child of the shim, so it lives with the
        # container and an agent restart cannot interrupt it.
        launcher = write_logger_launcher(
            self.local_config.agent.var_base_path / "containerd-log-writer"
        )
        self._runtime.configure_logging(
            launcher, CONTAINER_LOG_ROOT, int(self.local_config.container_logs.max_length)
        )

    @override
    async def shutdown(self, stop_signal: signal.Signals) -> None:
        for task in (self._event_monitor_task, self._agent_sock_task):
            if task is not None:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        # After the monitor is gone, so nothing new is dispatched into it.
        await self._event_task_group.shutdown()
        await super().shutdown(stop_signal)

    async def _handle_agent_socket(self) -> None:
        """Serve the in-container helper socket (host<->container PID translation, jail
        status) as a ZMQ REP over an ipc:// UNIX socket. Re-binds on error."""
        zmq_ctx = zmq.asyncio.Context()
        endpoint = f"ipc://{self._agent_sock_path}"
        await asyncio.to_thread(self._agent_sock_path.parent.mkdir, parents=True, exist_ok=True)
        # An unclean shutdown leaves the socket file behind, and an ipc:// bind onto an existing
        # path fails with EADDRINUSE — which this loop would then retry forever, silently, leaving
        # every kernel on the node without PID translation. The path is this agent's alone, so a
        # leftover can only be our own.
        await asyncio.to_thread(self._agent_sock_path.unlink, True)
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
                    # Dispatched, not awaited: handling an exit runs the CLEAN path, which can spend
                    # up to _LOG_COLLECTION_TIMEOUT persisting the kernel's logs. Awaiting it here
                    # put every other kernel's death and OOM behind that one — a node where one
                    # kernel dies badly stops noticing the others. (The Docker backend shields its
                    # handlers into a task group for the same reason.) Shielded so a cancellation of
                    # this loop at shutdown does not kill a clean that is already running.
                    await asyncio.shield(
                        self._event_task_group.create_task(self._handle_task_event(ev))
                    )
                log.info("containerd event stream ended; re-subscribing")
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("containerd event monitor failed; retrying")
            await asyncio.sleep(1.0)

    async def _session_id_of(self, container_id: str) -> SessionId | None:
        """The session a container belongs to, read off the container itself.

        The label is the only source that survives the agent forgetting the kernel — which is the
        case this exists for.
        """
        try:
            for info in await self._runtime.list_container_infos():
                if info.id != container_id:
                    continue
                if raw := info.labels.get(SESSION_ID_LABEL):
                    return SessionId(UUID(raw))
                return None
        except Exception:
            log.exception("could not resolve the session of container {}", container_id)
        return None

    async def _handle_task_event(self, ev: TaskEvent) -> None:
        try:
            kernel_id = KernelId(UUID(ev.container_id))
        except ValueError:
            return
        kernel_obj = self.kernel_registry.get(kernel_id)
        session_id = (
            kernel_obj.session_id
            if kernel_obj is not None
            # A container of ours that the registry does not know about — one that outlived a
            # restart, or whose creation failed after the container existed. Its death is exactly
            # when it can be cleaned, and dropping the event (which is what this used to do) left
            # it to the periodic reconciler, so its scratch and its ports sat allocated until then.
            # The session it belongs to is on the container itself, which is why the Docker backend
            # reads it from the label rather than from its own memory.
            else await self._session_id_of(ev.container_id)
        )
        if session_id is None:
            return  # not a container of ours
        match ev.kind:
            case "exit":
                reason = (
                    kernel_obj.termination_reason if kernel_obj is not None else None
                ) or KernelLifecycleEventReason.SELF_TERMINATED
                await self.inject_container_lifecycle_event(
                    kernel_id,
                    session_id,
                    LifecycleEvent.CLEAN,
                    reason,
                    container_id=ContainerId(ev.container_id),
                    exit_code=ev.exit_code,
                )
            case "oom":
                if kernel_obj is not None:
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
        status_filter: frozenset[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> Sequence[tuple[KernelId, Container]]:
        # Reconcile live kernels from containerd: every container carrying the kernel-id label
        # is one of ours (the containerd instance is per-node/per-agent). Lets the agent
        # recover running kernels across a restart.
        #
        # The default MUST be ACTIVE_STATUS_SET (as in the Docker backend): callers that want the
        # dead ones ask for them explicitly. reconstruct_resource_usage() enumerates with no
        # argument and restores each returned container's allocations, so defaulting to "no filter"
        # made it re-account CPU/memory/accelerators for already-exited containers.
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
            # Ours only. A containerd namespace can be shared by two agents on one host (and the
            # namespace is a config value, not a per-agent fact), and every caller of this treats
            # what it returns as its own: reconstruct_resource_usage re-accounts the allocations,
            # the lifecycle sync destroys what it cannot match to a kernel, and the port reclaim
            # takes their host ports. Without this filter each agent quietly adopts — and then
            # tears down — the other's kernels. The Docker backend has always filtered on this.
            if ci.labels.get(OWNER_AGENT_LABEL) != str(self.id):
                continue
            status = _CONTAINERD_TO_STATUS.get(ci.status, _UNRECOGNIZED_STATUS)
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
        # An unlabelled image has to be probed, which means running a throwaway container in it.
        # An image's libc never changes — the image is immutable — so probing it once per kernel
        # (which is what this did) is a container start the user waits through for an answer we
        # already had. Cache it as the Docker backend does, keyed by the image's own id.
        image_id = image["digest"].partition(":")[-1]
        if cached := await self.valkey_stat_client.get_image_distro(image_id):
            return cached
        distro = await self._probe_image_distro(image["canonical"])
        await self.valkey_stat_client.set_image_distro(image_id, distro)
        return distro

    async def _probe_image_distro(self, canonical: str) -> str:
        probe_id = f"distro-probe-{uuid4().hex[:12]}"
        oci_spec: dict[str, Any] = {"env": {}, "labels": {}, "mounts": []}
        await self._runtime.create_container(
            probe_id, image_ref=canonical, command=["ldd", "--version"], oci_spec=oci_spec
        )
        try:
            # No network needed for the throwaway probe: create the task and start it directly.
            # A one-shot probe: a couple of lines, read once, container discarded. No logger.
            await self._runtime.create_task(probe_id, use_logger=False)
            await self._runtime.start_task(probe_id)
            for _ in range(50):  # up to ~10s for the trivial command to exit
                if await self._runtime.container_status(probe_id) in (None, "stopped"):
                    break
                await asyncio.sleep(0.2)
            output = container_log_path(probe_id).read_text(errors="replace")
        finally:
            await self._runtime.remove_container(probe_id)
        first_line = output.splitlines()[0] if output.strip() else ""
        try:
            return distro_from_ldd_output(first_line)
        except UnknownImageLibc as e:
            raise ImageNotAvailable(f"cannot determine the C library variant of {canonical}") from e

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
        # The container's cgroup is set explicitly in the OCI spec (runtime/spec.py writes
        # ``linux.cgroupsPath`` from the same constants), so we know its name regardless of the
        # runtime's cgroup driver. container_id == kernel_id here, which is what the spec keys on.
        #
        # Where that name is rooted differs by hierarchy, and the controller matters on v1: the
        # unified v2 tree holds every controller at one mount point, while v1 gives each controller
        # its own. Ignoring the controller (and assuming v2) made every read on a v1 host land on a
        # path that does not exist — cpuacct/memory/blkio utilization silently absent for the life
        # of the node, and enumerate_container_pids reading an empty cgroup.procs.
        version = self.get_cgroup_version()
        if version == "2":
            return container_cgroup_fs_path(container_id)
        return get_cgroup_mount_point(version, controller) / container_cgroup_parent(container_id)

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
        # `noprune` asks to keep the untagged parent layers. containerd separates the image record
        # from its content: deleting the record leaves the layers for the content garbage
        # collector, so `sync` (wait for that GC) is the knob — the inverse of noprune.
        #
        # `force` has no counterpart and needs none: it exists in Docker because dockerd refuses to
        # delete an image a stopped container still references. containerd's image records carry no
        # such reference, so the delete always proceeds.
        async def _purge(image: str) -> PurgeImageResp:
            try:
                await self._session_network.remove_image(image, sync=not request.noprune)
                return PurgeImageResp.success(image)
            except Exception as exc:
                return PurgeImageResp(image=image, error=str(exc))

        # Concurrent, like the Docker backend: a sync delete waits for the GC of that image.
        responses = list(await asyncio.gather(*(_purge(image) for image in request.images)))
        return PurgeImagesResp(responses=responses)

    @override
    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        # Returns True if a pull is needed.
        #
        # Compare the CONFIG digest, not the manifest digest: `image_id` is what the manager
        # stored, and on Docker that is the image config's `Id`. Comparing a manifest digest
        # against it never matches, so DIGEST auto-pull re-pulled the image on every creation.
        local_digest = await self._session_network.image_config_digest(image_ref.canonical)
        if local_digest is None:  # not present locally
            if auto_pull in (AutoPullBehavior.DIGEST, AutoPullBehavior.TAG):
                return True
            raise ImageNotAvailable(image_ref)
        # Present: for DIGEST auto-pull, re-pull when the local digest is stale.
        return auto_pull is AutoPullBehavior.DIGEST and local_digest != image_id

    @override
    async def create_kernel(
        self,
        ownership_data: KernelOwnershipData,
        kernel_image: ImageRef,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        restarting: bool = False,
        throttle_sema: asyncio.Semaphore | None = None,
    ) -> KernelCreationResult:
        try:
            return await super().create_kernel(
                ownership_data,
                kernel_image,
                kernel_config,
                cluster_info,
                restarting=restarting,
                throttle_sema=throttle_sema,
            )
        except ResourceError:
            # "Kernel creation already in progress" — this call never got as far as claiming
            # anything; the claim belongs to the creation that IS in progress. Releasing it here
            # would tear the session network down under that live creation, turning a duplicate RPC
            # into a killed kernel.
            raise
        except BaseException:
            # The kernel claimed this node's session network in apply_network, long before its
            # container existed. If it dies before that container is prepared it never enters the
            # kernel registry — and a destroy for a kernel the agent has never heard of returns
            # without queueing a clean, so clean_kernel (which is what normally releases the claim)
            # never runs. Release it here, or the session's devices, LOCAL block and etcd membership
            # stay pinned for its siblings' whole lifetime and beyond, until the agent restarts.
            # BaseException, not Exception: a creation cancelled at shutdown leaks the claim just as
            # surely. (A kernel that already has a container keeps its claim — that one is released
            # by its own removal.)
            await self._session_network.release_kernel(str(ownership_data.kernel_id))
            raise

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
            apparmor_profile=self._apparmor_profile,
        )

    @override
    async def destroy_kernel(
        self,
        kernel_id: KernelId,
        container_id: ContainerId | None,
    ) -> None:
        if await self._runtime.container_status(str(kernel_id)) is None:
            # Nothing to stop: the container is already gone, but the registry still holds its
            # allocations. They are derived from the containers that exist, so re-derive them —
            # otherwise the slots this kernel held stay spoken for and the node quietly loses
            # capacity. (The Docker backend does the same when the daemon answers 404/409.)
            log.warning(
                "destroy_kernel(k:{}): the container is already gone; reconciling resources",
                kernel_id,
            )
            await self.reconstruct_resource_usage()
            return
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
        #
        # Gate on the log file still existing: clean_kernel can fire more than once for a kernel,
        # and remove_container (below) unlinks the file. collect_logs *always* emits a
        # DoSyncKernelLogs event, even for an empty read — so a second clean, after the file is
        # gone, would sync an empty log and OVERWRITE the good one the first clean persisted. (The
        # Docker backend is implicitly guarded: its second collect hits a 404 and is skipped.)
        if (
            container_id is not None
            and not restarting
            and container_log_path(str(container_id)).exists()
        ):
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
        # Shut the kernel's domain-socket proxies down. Each is a live asyncio unix server holding
        # a socket file under ipc_base_path; without this they outlive the kernel that needed them.
        kernel_obj = self.kernel_registry.get(kernel_id)
        if kernel_obj is not None:
            for proxy in kernel_obj.get("domain_socket_proxies", []):
                if proxy.proxy_server.is_serving():
                    proxy.proxy_server.close()
                    await proxy.proxy_server.wait_closed()
                with contextlib.suppress(OSError):
                    proxy.host_proxy_path.unlink()

        if self.local_config.debug.skip_container_deletion:
            # A debugging aid: keep the dead container (and its scratch) around for post-mortem
            # inspection. The Docker backend honors the same flag.
            log.info(
                "clean_kernel(k:{}): skipping container removal (debug.skip-container-deletion)",
                kernel_id,
            )
            # Still give up the claim of a kernel that never got a container: the flag is about
            # keeping containers around for inspection, not about pinning session networks that
            # have none. (A kernel that HAS a container keeps its claim, as the flag intends.)
            await self._session_network.release_kernel(str(kernel_id))
            return
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
                elif sys.platform.startswith("linux") and scratch_type == ScratchType.MEMORY:
                    # Unmount before removing: rmtree on a live tmpfs deletes the files but leaves
                    # the mount, so the RAM is never given back and the mount table grows with
                    # every kernel that ever ran here.
                    tmp_dir = scratch_root / f"{kernel_id}_tmp"
                    await destroy_scratch_filesystem(scratch_dir)
                    await destroy_scratch_filesystem(tmp_dir)
                    await asyncio.to_thread(shutil.rmtree, scratch_dir, ignore_errors=True)
                    await asyncio.to_thread(shutil.rmtree, tmp_dir, ignore_errors=True)
                else:
                    await asyncio.to_thread(shutil.rmtree, scratch_dir, ignore_errors=True)
            except Exception:
                log.exception("clean_kernel(k:{}): scratch teardown failed", kernel_id)

    @override
    async def create_local_network(self, network_name: str) -> None:
        # Single-node multi-kernel local bridge. In BEP-1062 intra-node connectivity is
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

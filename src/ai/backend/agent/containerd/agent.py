"""Containerd-backed agent and kernel-creation context.

The containerd backend drives the host's containerd over its **native
gRPC API** (Containers/Tasks/Snapshots/Images/Transfer/...) inside a
dedicated metadata namespace, so kubelet's CRI plugin cannot see or reap
the workloads. See ``ContainerdClient`` and the ``NetworkProvider``
abstraction for the runtime and networking layers respectively.

``ContainerdKernelCreationContext`` builds everything a kernel needs
*before* the container exists — scratch directories, the resource spec,
intrinsic/krunner/vfolder mounts, SSH material — none of which depends on
the container runtime. Those parts port near-verbatim from the Docker
backend. The runtime-specific steps (snapshot → container → task →
network attach) land in ``prepare_container`` / ``start_container``.
"""

from __future__ import annotations

import asyncio
import logging
import os
import secrets
import shutil
import signal
import sys
from collections.abc import Iterable, Mapping, MutableMapping, Sequence
from decimal import Decimal
from functools import partial
from importlib.resources import files
from io import StringIO
from pathlib import Path
from subprocess import CalledProcessError
from subprocess import run as subprocess_run
from typing import Any, override
from uuid import UUID

import aiotools

from ai.backend.agent.agent import (
    ACTIVE_STATUS_SET,
    AbstractAgent,
    AbstractKernelCreationContext,
    ScanImagesResult,
)
from ai.backend.agent.config.unified import (
    AgentUnifiedConfig,
    ContainerdNetworkMode,
    ScratchType,
)
from ai.backend.agent.errors.containerd import ContainerdImageError, ContainerdRpcError
from ai.backend.agent.exception import (
    ContainerCreationError,
    UnsupportedResource,
)
from ai.backend.agent.fs import create_scratch_filesystem, destroy_scratch_filesystem
from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.kernel_registry.writer.types import KernelRegistrySaveMetadata
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
from ai.backend.agent.types import (
    AgentEventData,
    Container,
    KernelOwnershipData,
    LifecycleEvent,
    MountInfo,
)
from ai.backend.agent.utils import get_arch_name
from ai.backend.common.asyncio import current_loop
from ai.backend.common.cgroup import get_cgroup_mount_point
from ai.backend.common.data.image.types import InstalledImageInfo
from ai.backend.common.docker import (
    MAX_KERNELSPEC,
    MIN_KERNELSPEC,
    ImageRef,
    KernelFeatures,
    LabelName,
)
from ai.backend.common.dto.agent.response import PurgeImagesResp
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.kernel import KernelLifecycleEventReason
from ai.backend.common.exception import (
    ConfigurationError,
    ImageNotAvailable,
    InvalidImageName,
    InvalidImageTag,
)
from ai.backend.common.json import dump_json
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
    ResourceGroupType,
    ResourceSlot,
    Sentinel,
    ServicePort,
    SlotName,
    current_resource_slots,
)
from ai.backend.logging import BraceStyleAdapter

from .client.client import ContainerdClient
from .client.generated.containerd.events import task_pb2 as events_task_pb2
from .client.generated.containerd.types.task import task_pb2
from .kernel import ContainerdKernel
from .network.base import NetworkAttachment, NetworkProvider
from .network.cilium import CiliumNetworkProvider
from .network.netns import create_netns, delete_netns
from .oci import build_oci_spec
from .preflight import run_preflight

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


# Map containerd task status enum values to the agent's ContainerStatus.
# CREATED has no exact analog — treat it as RESTARTING since it means
# "task exists but has not been started yet" (the agent's recovery flow
# treats RESTARTING as active and tries to resume).
_TASK_STATUS_MAP: Mapping[int, ContainerStatus] = {
    task_pb2.RUNNING: ContainerStatus.RUNNING,
    task_pb2.PAUSED: ContainerStatus.PAUSED,
    task_pb2.PAUSING: ContainerStatus.PAUSED,
    task_pb2.CREATED: ContainerStatus.RESTARTING,
    task_pb2.STOPPED: ContainerStatus.EXITED,
    task_pb2.UNKNOWN: ContainerStatus.DEAD,
}


def _mount_to_oci(mount: Mount) -> dict[str, Any] | None:
    """Translate an agent ``Mount`` into an OCI runtime-spec mount entry.

    Returns ``None`` for mount types the containerd backend does not
    provision (Docker named volumes); only BIND and TMPFS map cleanly.
    """
    if mount.type is MountTypes.BIND:
        options = [
            "rbind",
            "rw" if mount.permission != MountPermission.READ_ONLY else "ro",
        ]
        return {
            "destination": str(mount.target),
            "source": str(mount.source),
            "type": "bind",
            "options": options,
        }
    if mount.type is MountTypes.TMPFS:
        return {
            "destination": str(mount.target),
            "source": "tmpfs",
            "type": "tmpfs",
            "options": ["nosuid", "nodev"],
        }
    return None


class ContainerdKernelCreationContext(AbstractKernelCreationContext[ContainerdKernel]):
    """Build the per-kernel state the containerd backend needs to launch a kernel.

    The runtime-specific final steps — ``prepare_container`` and
    ``start_container`` — are filled in by a later increment; everything
    else (scratch dirs, resource spec, mounts, SSH) is runtime-agnostic.
    """

    scratch_dir: Path
    tmp_dir: Path
    config_dir: Path
    work_dir: Path
    port_pool: PortPool
    agent_sockpath: Path
    resource_lock: asyncio.Lock
    containerd_client: ContainerdClient
    network_provider: NetworkProvider
    k8s_pod_namespace: str | None
    k8s_pod_name_prefix: str
    domain_socket_proxies: list[DomainSocketProxy]
    bind_mounts: list[Mount]

    def __init__(
        self,
        ownership_data: KernelOwnershipData,
        event_producer: EventProducer,
        kernel_image: ImageRef,
        kernel_config: KernelCreationConfig,
        distro: str,
        local_config: AgentUnifiedConfig,
        computers: Mapping[DeviceName, ComputerContext],
        *,
        containerd_client: ContainerdClient,
        network_provider: NetworkProvider,
        port_pool: PortPool,
        agent_sockpath: Path,
        resource_lock: asyncio.Lock,
        k8s_pod_namespace: str | None = None,
        k8s_pod_name_prefix: str = "kernel",
        restarting: bool = False,
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
        kernel_id = ownership_data.kernel_id
        scratch_dir = (self.local_config.container.scratch_root / str(kernel_id)).resolve()
        tmp_dir = (self.local_config.container.scratch_root / f"{kernel_id}_tmp").resolve()

        self.scratch_dir = scratch_dir
        self.tmp_dir = tmp_dir
        self.config_dir = scratch_dir / "config"
        self.work_dir = scratch_dir / "work"

        self.port_pool = port_pool
        self.agent_sockpath = agent_sockpath
        self.resource_lock = resource_lock
        self.containerd_client = containerd_client
        self.network_provider = network_provider
        self.k8s_pod_namespace = k8s_pod_namespace
        self.k8s_pod_name_prefix = k8s_pod_name_prefix

        self.domain_socket_proxies = []
        self.bind_mounts = []

    def _kernel_resource_spec_read(self, filename: Path | str) -> KernelResourceSpec:
        filepath = Path(filename)
        with filepath.open() as f:
            return KernelResourceSpec.read_from_file(f)

    @override
    async def get_extra_envs(self) -> Mapping[str, str]:
        return {}

    @override
    async def prepare_resource_spec(self) -> tuple[KernelResourceSpec, Mapping[str, Any] | None]:
        loop = current_loop()
        if self.restarting:
            resource_spec = await loop.run_in_executor(
                None, self._kernel_resource_spec_read, self.config_dir / "resource.txt"
            )
            resource_opts = None
        else:
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

    def _chown_paths_if_root(self, paths: Iterable[Path], uid: int | None, gid: int | None) -> None:
        if os.geteuid() == 0:  # only possible when I am root.
            for p in paths:
                if KernelFeatures.UID_MATCH in self.kernel_features:
                    valid_uid = uid if uid is not None else self.local_config.container.kernel_uid
                    valid_gid = gid if gid is not None else self.local_config.container.kernel_gid
                else:
                    stat = p.stat()
                    valid_uid = uid if uid is not None else stat.st_uid
                    valid_gid = gid if gid is not None else stat.st_gid
                try:
                    int_uid = int(valid_uid)
                    int_gid = int(valid_gid)
                except (TypeError, ValueError):
                    log.exception(
                        "invalid uid/gid to chown: {}/{}, skip chown", valid_uid, valid_gid
                    )
                    continue
                try:
                    os.chown(p, int_uid, int_gid)
                except OSError as e:
                    log.exception(
                        "failed to chown {} to {}/{} (error: {})", p, int_uid, int_gid, repr(e)
                    )

    @override
    async def prepare_scratch(self) -> None:
        loop = current_loop()

        # Create the scratch, config, and work directories.
        scratch_type = self.local_config.container.scratch_type
        scratch_root = self.local_config.container.scratch_root
        scratch_size = self.local_config.container.scratch_size

        if sys.platform.startswith("linux") and scratch_type == ScratchType.MEMORY:
            await loop.run_in_executor(None, partial(self.tmp_dir.mkdir, exist_ok=True))
            await create_scratch_filesystem(self.scratch_dir, 64)
            await create_scratch_filesystem(self.tmp_dir, 64)
        elif sys.platform.startswith("linux") and scratch_type == ScratchType.HOSTFILE:
            await create_loop_filesystem(scratch_root, scratch_size, self.kernel_id)
        else:
            await loop.run_in_executor(None, partial(self.scratch_dir.mkdir, exist_ok=True))

        def _create_scratch_dirs() -> None:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.config_dir.chmod(0o755)
            self.work_dir.mkdir(parents=True, exist_ok=True)
            self.work_dir.chmod(0o755)

        await loop.run_in_executor(None, _create_scratch_dirs)

        if not self.restarting:
            # Since these files are bind-mounted inside a bind-mounted directory,
            # we need to touch them first to avoid their "ghost" files are created
            # as root in the host-side filesystem, which prevents deletion of scratch
            # directories when the agent is running as non-root.
            def _clone_dotfiles() -> None:
                jupyter_custom_css_path = Path(
                    str(files("ai.backend.runner").joinpath("jupyter-custom.css"))
                )
                logo_path = Path(str(files("ai.backend.runner").joinpath("logo.svg")))
                font_path = Path(str(files("ai.backend.runner").joinpath("roboto.ttf")))
                font_italic_path = Path(
                    str(files("ai.backend.runner").joinpath("roboto-italic.ttf"))
                )
                bashrc_path = Path(str(files("ai.backend.runner").joinpath(".bashrc")))
                bash_profile_path = Path(str(files("ai.backend.runner").joinpath(".bash_profile")))
                zshrc_path = Path(str(files("ai.backend.runner").joinpath(".zshrc")))
                vimrc_path = Path(str(files("ai.backend.runner").joinpath(".vimrc")))
                tmux_conf_path = Path(str(files("ai.backend.runner").joinpath(".tmux.conf")))
                persistent_files_warning_doc_path = Path(
                    str(
                        files("ai.backend.runner").joinpath("DO_NOT_STORE_PERSISTENT_FILES_HERE.md")
                    )
                )
                jupyter_custom_dir = self.work_dir / ".jupyter" / "custom"
                jupyter_custom_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy(jupyter_custom_css_path.resolve(), jupyter_custom_dir / "custom.css")
                shutil.copy(logo_path.resolve(), jupyter_custom_dir / "logo.svg")
                shutil.copy(font_path.resolve(), jupyter_custom_dir / "roboto.ttf")
                shutil.copy(font_italic_path.resolve(), jupyter_custom_dir / "roboto-italic.ttf")
                shutil.copy(bashrc_path.resolve(), self.work_dir / ".bashrc")
                shutil.copy(bash_profile_path.resolve(), self.work_dir / ".bash_profile")
                shutil.copy(zshrc_path.resolve(), self.work_dir / ".zshrc")
                shutil.copy(vimrc_path.resolve(), self.work_dir / ".vimrc")
                shutil.copy(tmux_conf_path.resolve(), self.work_dir / ".tmux.conf")
                shutil.copy(
                    persistent_files_warning_doc_path.resolve(),
                    self.work_dir / "DO_NOT_STORE_PERSISTENT_FILES_HERE.md",
                )

                def chown_scratch(uid: int | None, gid: int | None) -> None:
                    paths = [
                        self.work_dir,
                        self.work_dir / ".jupyter",
                        self.work_dir / ".jupyter" / "custom",
                        self.work_dir / ".bashrc",
                        self.work_dir / ".bash_profile",
                        self.work_dir / ".zshrc",
                        self.work_dir / ".vimrc",
                        self.work_dir / ".tmux.conf",
                        self.work_dir / "DO_NOT_STORE_PERSISTENT_FILES_HERE.md",
                    ]
                    self._chown_paths_if_root(paths, uid, gid)

                do_override = False
                if (ouid := self.get_overriding_uid()) is not None:
                    do_override = True

                if (ogid := self.get_overriding_gid()) is not None:
                    do_override = True

                if do_override:
                    chown_scratch(ouid, ogid)
                else:
                    if KernelFeatures.UID_MATCH in self.kernel_features:
                        chown_scratch(
                            self.local_config.container.kernel_uid,
                            self.local_config.container.kernel_gid,
                        )

            await loop.run_in_executor(None, _clone_dotfiles)

    @override
    async def get_intrinsic_mounts(self) -> Sequence[Mount]:
        loop = current_loop()

        # scratch/config/tmp mounts
        mounts: list[Mount] = [
            Mount(
                MountTypes.BIND, self.config_dir, Path("/home/config"), MountPermission.READ_ONLY
            ),
            Mount(MountTypes.BIND, self.work_dir, Path("/home/work"), MountPermission.READ_WRITE),
        ]
        if (
            sys.platform.startswith("linux")
            and self.local_config.container.scratch_type == ScratchType.MEMORY
        ):
            mounts.append(
                Mount(
                    MountTypes.BIND,
                    self.tmp_dir,
                    Path("/tmp"),
                    MountPermission.READ_WRITE,
                )
            )
        # /etc/localtime and /etc/timezone mounts
        if sys.platform.startswith("linux"):
            localtime_file = Path("/etc/localtime")
            timezone_file = Path("/etc/timezone")
            if localtime_file.exists():
                mounts.append(
                    Mount(
                        type=MountTypes.BIND,
                        source=localtime_file,
                        target=localtime_file,
                        permission=MountPermission.READ_ONLY,
                    )
                )
            if timezone_file.exists():
                mounts.append(
                    Mount(
                        type=MountTypes.BIND,
                        source=timezone_file,
                        target=timezone_file,
                        permission=MountPermission.READ_ONLY,
                    )
                )
        # lxcfs mounts
        lxcfs_root = Path("/var/lib/lxcfs")
        if lxcfs_root.is_dir():
            mounts.extend(
                Mount(
                    MountTypes.BIND,
                    lxcfs_proc_path,
                    "/" / lxcfs_proc_path.relative_to(lxcfs_root),
                    MountPermission.READ_WRITE,
                )
                for lxcfs_proc_path in (lxcfs_root / "proc").iterdir()
                if lxcfs_proc_path.stat().st_size > 0
            )
            mounts.extend(
                Mount(
                    MountTypes.BIND,
                    lxcfs_root / path,
                    "/" / Path(path),
                    MountPermission.READ_WRITE,
                )
                for path in [
                    "sys/devices/system/cpu",
                    "sys/devices/system/cpu/online",
                ]
                if Path(lxcfs_root / path).exists()
            )

        # debug mounts
        if self.local_config.debug.coredump.enabled:
            mounts.append(
                Mount(
                    MountTypes.BIND,
                    self.local_config.debug.coredump.path,
                    self.local_config.debug.coredump.core_path,
                    MountPermission.READ_WRITE,
                )
            )

        # agent-socket mount
        if sys.platform != "darwin":
            mounts.append(
                Mount(
                    MountTypes.BIND,
                    self.agent_sockpath,
                    Path("/opt/kernel/agent.sock"),
                    MountPermission.READ_WRITE,
                )
            )
        ipc_base_path = self.local_config.agent.ipc_base_path

        # domain-socket proxy mount
        # (used for special service containers such image importer)
        for host_sock_path in self.internal_data.get("domain_socket_proxies", []):
            await loop.run_in_executor(
                None, partial((ipc_base_path / "proxy").mkdir, parents=True, exist_ok=True)
            )
            host_proxy_path = ipc_base_path / "proxy" / f"{secrets.token_hex(12)}.sock"
            proxy_server = await asyncio.start_unix_server(
                aiotools.apartial(proxy_connection, host_sock_path), str(host_proxy_path)
            )
            await loop.run_in_executor(None, host_proxy_path.chmod, 0o666)
            self.domain_socket_proxies.append(
                DomainSocketProxy(
                    Path(host_sock_path),
                    host_proxy_path,
                    proxy_server,
                )
            )
            mounts.append(
                Mount(
                    MountTypes.BIND,
                    host_proxy_path,
                    host_sock_path,
                    MountPermission.READ_WRITE,
                )
            )

        return mounts

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

    @property
    @override
    def repl_ports(self) -> Sequence[int]:
        return (2000, 2001)

    @property
    @override
    def protected_services(self) -> Sequence[str]:
        rgtype: ResourceGroupType = self.local_config.agent.scaling_group_type
        match rgtype:
            case ResourceGroupType.COMPUTE:
                return ()
            case ResourceGroupType.STORAGE:
                return ("ttyd",)

    @override
    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        # The containerd backend attaches each kernel to its network via a
        # per-kernel netns + CNI in start_container (see NetworkProvider).
        # Multi-node cluster wiring is handled there, so there is nothing
        # to apply to a pre-creation container config here.
        del cluster_info

    @override
    async def prepare_ssh(self, cluster_info: ClusterInfo) -> None:
        sshkey = cluster_info["ssh_keypair"]

        def _write_config() -> None:
            try:
                ssh_dir = self.config_dir / "ssh"
                ssh_dir.mkdir(parents=True, exist_ok=True)
                paths_to_chown: list[Path] = []

                # Generate dropbear host key for container SSH server
                host_key_path = ssh_dir / "dropbear_rsa_host_key"
                arch = get_arch_name()
                dropbearmulti_path = self.resolve_krunner_filepath(
                    f"runner/dropbearmulti.{arch}.bin"
                )
                if not dropbearmulti_path.exists():
                    raise FileNotFoundError(
                        f"dropbearmulti binary not found at {dropbearmulti_path}"
                    )
                # If the host key already exists, we assume it's valid and skip generation.
                if not host_key_path.is_file():
                    try:
                        subprocess_run(
                            [
                                str(dropbearmulti_path),
                                "dropbearkey",
                                "-t",
                                "rsa",
                                "-s",
                                "2048",
                                "-f",
                                str(host_key_path),
                            ],
                            check=True,
                            capture_output=True,
                        )
                        host_key_path.chmod(0o600)
                    except CalledProcessError as e:
                        stderr = e.stderr.decode("utf-8", "replace") if e.stderr else ""
                        stdout = e.stdout.decode("utf-8", "replace") if e.stdout else ""
                        log.warning(
                            "dropbearkey failed. Host key will regenerate on container startup. "
                            "Return code {code}, stdout: {stdout}, stderr: {stderr}",
                            code=e.returncode,
                            stdout=stdout,
                            stderr=stderr,
                        )
                    except OSError as e:
                        log.warning(
                            "failed to execute dropbearmulti for host key generation. Host key "
                            "will regenerate on container startup: {}",
                            repr(e),
                        )
                paths_to_chown.append(host_key_path)

                # Write provided SSH keypair for cluster access if exists
                if sshkey is not None:
                    cluster_priv_key_path = ssh_dir / "id_cluster"
                    cluster_pub_key_path = ssh_dir / "id_cluster.pub"
                    cluster_priv_key_path.write_text(sshkey["private_key"])
                    cluster_pub_key_path.write_text(sshkey["public_key"])
                    cluster_priv_key_path.chmod(0o600)
                    paths_to_chown.extend([cluster_priv_key_path, cluster_pub_key_path])

                    if cluster_ssh_port_mapping := cluster_info["cluster_ssh_port_mapping"]:
                        port_mapping_json_path = ssh_dir / "port-mapping.json"
                        port_mapping_json_path.write_bytes(dump_json(cluster_ssh_port_mapping))

                # Set ownership for all created files
                ouid = self.get_overriding_uid()
                ogid = self.get_overriding_gid()
                if ouid is not None or ogid is not None:
                    self._chown_paths_if_root(paths_to_chown, ouid, ogid)
                elif KernelFeatures.UID_MATCH in self.kernel_features:
                    self._chown_paths_if_root(
                        paths_to_chown,
                        self.local_config.container.kernel_uid,
                        self.local_config.container.kernel_gid,
                    )
            except Exception:
                log.exception("error while writing SSH keys")

        await current_loop().run_in_executor(None, _write_config)

    @override
    async def process_mounts(self, mounts: Sequence[Mount]) -> None:
        # Collected here and translated into OCI spec bind mounts when the
        # container is created (start_container); containerd has no
        # equivalent of Docker's HostConfig.Mounts.
        self.bind_mounts.extend(mounts)

    @override
    async def apply_accelerator_allocation(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        # Accelerator device injection into the OCI spec is handled by a
        # later increment; the intrinsic CPU/Memory plugins need no extra
        # runtime args (their generate_docker_args returns an empty map).
        del computer, device_alloc

    @override
    async def generate_accelerator_mounts(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> list[MountInfo]:
        src_path = self.config_dir / str(computer.key)
        src_path.mkdir(exist_ok=True)
        return await computer.generate_mounts(src_path, device_alloc)

    @override
    async def prepare_container(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports: list[ServicePort],
        cluster_info: ClusterInfo,
    ) -> ContainerdKernel:
        del cluster_info  # multi-node cluster wiring is via per-kernel CNI attach.
        loop = current_loop()
        ouid = self.get_overriding_uid()
        ogid = self.get_overriding_gid()

        if not self.restarting:
            # Create bootstrap.sh into workdir if needed.
            if bootstrap := self.kernel_config.get("bootstrap_script"):

                def _write_user_bootstrap_script() -> None:
                    (self.work_dir / "bootstrap.sh").write_text(bootstrap)
                    if ouid is not None or ogid is not None:
                        self._chown_paths_if_root([self.work_dir / "bootstrap.sh"], ouid, ogid)
                    else:
                        if KernelFeatures.UID_MATCH in self.kernel_features:
                            self._chown_paths_if_root(
                                [self.work_dir / "bootstrap.sh"],
                                self.local_config.container.kernel_uid,
                                self.local_config.container.kernel_gid,
                            )

                await loop.run_in_executor(None, _write_user_bootstrap_script)

            with StringIO() as buf:
                for k, v in environ.items():
                    buf.write(f"{k}={v}\n")
                await loop.run_in_executor(
                    None,
                    (self.config_dir / "environ.txt").write_bytes,
                    buf.getvalue().encode("utf8"),
                )

            with StringIO() as buf:
                resource_spec.write_to_file(buf)
                for dev_type, device_alloc in resource_spec.allocations.items():
                    device_plugin = self.computers[dev_type].instance
                    kvpairs = await device_plugin.generate_resource_data(device_alloc)
                    for k, v in kvpairs.items():
                        buf.write(f"{k}={v}\n")
                await loop.run_in_executor(
                    None,
                    (self.config_dir / "resource.txt").write_bytes,
                    buf.getvalue().encode("utf8"),
                )

        shutil.copyfile(self.config_dir / "environ.txt", self.config_dir / "environ_base.txt")
        shutil.copyfile(self.config_dir / "resource.txt", self.config_dir / "resource_base.txt")

        # SSH keypair only if internal_data.ssh_keypair exists and
        # /home/work/.ssh has not been bind-mounted in.
        if self.internal_data.get("ssh_keypair"):
            for mount in resource_spec.mounts:
                container_path = str(mount).split(":")[1]
                if container_path == "/home/work/.ssh":
                    break
            else:
                pubkey = self.internal_data["ssh_keypair"]["public_key"].encode("ascii")
                privkey = self.internal_data["ssh_keypair"]["private_key"].encode("ascii")
                ssh_dir = self.work_dir / ".ssh"

                def _populate_ssh_config() -> None:
                    ssh_dir.mkdir(parents=True, exist_ok=True)
                    ssh_dir.chmod(0o700)
                    (ssh_dir / "authorized_keys").write_bytes(pubkey)
                    (ssh_dir / "authorized_keys").chmod(0o600)
                    if not (ssh_dir / "id_rsa").is_file():
                        (ssh_dir / "id_rsa").write_bytes(privkey)
                        (ssh_dir / "id_rsa").chmod(0o600)
                    (self.work_dir / "id_container").write_bytes(privkey)
                    (self.work_dir / "id_container").chmod(0o600)

                    def chown_idfile(uid: int | None, gid: int | None) -> None:
                        paths = [
                            ssh_dir,
                            ssh_dir / "authorized_keys",
                            ssh_dir / "id_rsa",
                            self.work_dir / "id_container",
                        ]
                        self._chown_paths_if_root(paths, uid, gid)

                    if ouid is not None or ogid is not None:
                        chown_idfile(ouid, ogid)
                    else:
                        if KernelFeatures.UID_MATCH in self.kernel_features:
                            chown_idfile(
                                self.local_config.container.kernel_uid,
                                self.local_config.container.kernel_gid,
                            )

                await loop.run_in_executor(None, _populate_ssh_config)

        # higher-priority dotfiles are stored last so they overwrite.
        for dotfile in self.internal_data.get("dotfiles", []):
            if dotfile["path"].startswith("/"):
                if dotfile["path"].startswith("/home/"):
                    path_arr = dotfile["path"].split("/")
                    file_path: Path = self.scratch_dir / "/".join(path_arr[2:])
                else:
                    file_path = Path(dotfile["path"])
            else:
                file_path = self.work_dir / dotfile["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)

            dotfile_content = dotfile["data"]
            if not dotfile_content.endswith("\n"):
                dotfile_content += "\n"
            await loop.run_in_executor(None, file_path.write_text, dotfile_content)

            tmp = Path(file_path)
            tmp_paths: list[Path] = []
            while tmp != self.work_dir:
                tmp.chmod(int(dotfile["perm"], 8))
                tmp_paths.append(tmp)
                tmp = tmp.parent
            if ouid is not None or ogid is not None:
                self._chown_paths_if_root(tmp_paths, ouid, ogid)
            else:
                if KernelFeatures.UID_MATCH in self.kernel_features:
                    self._chown_paths_if_root(
                        tmp_paths,
                        self.local_config.container.kernel_uid,
                        self.local_config.container.kernel_gid,
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
            data={},
        )

    @override
    async def start_container(
        self,
        kernel_obj: AbstractKernel,
        cmdargs: list[str],
        resource_opts: Mapping[str, Any] | None,
        preopen_ports: list[int],
        cluster_info: ClusterInfo,
    ) -> Mapping[str, Any]:
        del resource_opts, cluster_info  # reserved for future use.
        resource_spec = kernel_obj.resource_spec
        service_ports = kernel_obj.service_ports
        environ = kernel_obj.environ
        image_labels = self.kernel_config["image"]["labels"]

        # Compute the kernel's exposed-port list. With direct-netns-IP
        # repl the agent does NOT consume port_pool for the intrinsic
        # repl ports; each service port also maps 1:1 to the same
        # container port (the netns IP is reachable on the cluster
        # fabric).
        exposed_ports: list[int] = [*self.repl_ports]
        for sport in service_ports:
            exposed_ports.extend(sport["container_ports"])
            sport["host_ports"] = tuple(sport["container_ports"])

        # service-ports label mirrors the docker backend so the manager-side
        # parsing of the kernel container's labels stays uniform.
        service_ports_label: list[str] = []
        service_ports_label += image_labels.get(LabelName.SERVICE_PORTS, "").split(",")
        service_ports_label += [f"{port_no}:preopen:{port_no}" for port_no in preopen_ports]

        if self.image_ref.is_local:
            image_canonical = self.image_ref.short
        else:
            image_canonical = self.image_ref.canonical

        kernel_id_str = str(self.kernel_id)
        container_id = f"kernel-{kernel_id_str}"
        netns_name = f"bai-{kernel_id_str}"

        # Translate the bind mounts collected by process_mounts +
        # intrinsic_mounts into OCI mount entries; named volumes (a
        # Docker concept) have no containerd equivalent and are dropped.
        oci_mounts: list[dict[str, Any]] = []
        all_mounts: list[Mount] = [*resource_spec.mounts, *self.bind_mounts]
        for mount in all_mounts:
            translated = _mount_to_oci(mount)
            if translated is not None:
                oci_mounts.append(translated)

        # CFS-bandwidth + memory cgroup limits derived from the resource
        # spec; either may be left unset (no limit) if the slot is zero.
        cpu_period_us = 100_000
        cpu_slot = resource_spec.slots.get("cpu", Decimal(0))
        cpu_quota_us: int | None = int(cpu_period_us * cpu_slot) if cpu_slot > 0 else None
        mem_slot = resource_spec.slots.get("mem", Decimal(0))
        memory_limit_bytes: int | None = int(mem_slot) if mem_slot > 0 else None

        # Per-kernel container-log path. Stdout/stderr are wired to this
        # file via the task's stdio URIs so the kernel's logs are
        # retrievable from the host without needing an in-container exec.
        log_path = self.scratch_dir / "container.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.touch(exist_ok=True)
        log_uri = f"file://{log_path}"

        # Network namespace + CNI attach.
        ns_path = await create_netns(netns_name)
        attachment: NetworkAttachment | None = None
        try:
            # K8S_POD_NAMESPACE / K8S_POD_NAME piggyback on CNI_ARGS and
            # only make sense when a real Pod (or CiliumExternalWorkload
            # CRD) with that ns/name exists in the k8s API. The default
            # is OFF (containerd.network.cilium_pod_namespace=""):
            # empirically, advertising a fake ns/name made cilium-cni
            # reconcile against the missing Pod and strip our user
            # labels, leaving the endpoint stuck at reserved:init. The
            # opt-in remains for operators who set up a placeholder Pod
            # or ClusterMesh External Workload alongside their kernels.
            pod_name = (
                f"{self.k8s_pod_name_prefix}-{kernel_id_str}" if self.k8s_pod_namespace else None
            )
            attachment = await self.network_provider.attach(
                container_id,
                ns_path,
                labels={
                    LabelName.AGENT_ID: str(self.agent_id),
                    LabelName.KERNEL_ID: kernel_id_str,
                    LabelName.SESSION_ID: str(self.session_id),
                },
                k8s_pod_namespace=self.k8s_pod_namespace,
                k8s_pod_name=pod_name,
            )
            if attachment.ipv4 is None:
                raise ContainerCreationError(
                    container_id=ContainerId(container_id),
                    message="CNI attach returned no IPv4 address",
                )

            # Prepare the writable container rootfs from the image layers.
            rootfs_mounts = await self.containerd_client.prepare_image_rootfs(
                image_canonical, container_id
            )

            spec = build_oci_spec(
                container_id=container_id,
                args=["/opt/kernel/entrypoint.sh", *cmdargs],
                env=[f"{k}={v}" for k, v in environ.items()],
                cwd="/home/work",
                hostname=self.kernel_config["cluster_hostname"],
                terminal=False,
                cgroups_path=f"/backendai/{container_id}",
                netns_path=ns_path,
                bind_mounts=oci_mounts,
                cpu_period_us=cpu_period_us,
                cpu_quota_us=cpu_quota_us,
                memory_limit_bytes=memory_limit_bytes,
            )

            labels: dict[str, str] = {
                LabelName.AGENT_ID: str(self.agent_id),
                LabelName.KERNEL_ID: kernel_id_str,
                LabelName.SESSION_ID: str(self.session_id),
                LabelName.OWNER_USER: self.ownership_data.owner_user_id_to_str or "",
                LabelName.OWNER_PROJECT: self.ownership_data.owner_project_id_to_str or "",
                LabelName.OWNER_AGENT: str(self.agent_id),
                LabelName.BLOCK_SERVICE_PORTS: (
                    "1" if self.internal_data.get("block_service_ports", False) else "0"
                ),
                LabelName.SERVICE_PORTS: ",".join(label for label in service_ports_label if label),
            }
            await self.containerd_client.create_container(
                container_id,
                image=image_canonical,
                spec=spec,
                snapshot_key=container_id,
                labels=labels,
            )
            try:
                await self.containerd_client.create_task(
                    container_id,
                    rootfs=rootfs_mounts,
                    stdout=log_uri,
                    stderr=log_uri,
                )
                await self.containerd_client.start_task(container_id)
            except Exception:
                # Roll back the container metadata if the task failed to
                # start; the snapshot + netns are cleaned in the outer
                # except below.
                try:
                    await self.containerd_client.delete_container(container_id)
                except Exception:
                    log.exception("rollback: delete_container({}) failed", container_id)
                raise
        except Exception:
            if attachment is not None:
                try:
                    await self.network_provider.detach(container_id, ns_path)
                except Exception:
                    log.exception("rollback: cni detach({}) failed", container_id)
            try:
                await delete_netns(netns_name)
            except Exception:
                log.exception("rollback: delete_netns({}) failed", netns_name)
            try:
                await self.containerd_client.remove_snapshot(container_id)
            except Exception:
                # The snapshot may or may not have been prepared.
                pass
            async with self.resource_lock:
                for dev_name, device_alloc in resource_spec.allocations.items():
                    self.computers[dev_name].alloc_map.free(device_alloc)
            raise

        # Append CID + IP to resource.txt for the recovery increment to
        # reconstruct workload identity later.
        cid_record = f"CID={container_id}\nIP={attachment.ipv4}\n"
        (self.config_dir / "resource.txt").write_text(
            (self.config_dir / "resource.txt").read_text() + cid_record
        )

        kernel_obj.set_container_id(ContainerId(container_id))

        return {
            "container_id": container_id,
            "kernel_host": attachment.ipv4,
            "repl_in_port": 2000,
            "repl_out_port": 2001,
            "stdin_port": 0,
            "stdout_port": 0,
            "host_ports": tuple(exposed_ports),
            "domain_socket_proxies": self.domain_socket_proxies,
            "block_service_ports": self.internal_data.get("block_service_ports", False),
            "netns_name": netns_name,
            "netns_path": ns_path,
        }


class ContainerdAgent(AbstractAgent[ContainerdKernel, ContainerdKernelCreationContext]):
    """Containerd-backed agent driving the host containerd over its native gRPC API.

    Workloads live in a dedicated containerd metadata namespace so a
    co-located kubelet (whose CRI plugin only enumerates ``k8s.io``)
    never sees — and never reaps — Backend.AI containers.

    This class currently covers the agent lifecycle, image scanning, and
    cgroup introspection. The kernel create/destroy path
    (``init_kernel_context``, ``prepare_container`` / ``start_container``,
    ``destroy_kernel`` / ``clean_kernel``), crash recovery, and image
    push/purge are filled in by later increments, so this class is not
    yet fully instantiable.
    """

    containerd: ContainerdClient
    network_provider: NetworkProvider | None
    agent_sockpath: Path
    cgroup_version: str
    checked_invalid_images: set[str]
    monitor_events_task: asyncio.Task[None] | None

    async def __ainit__(self) -> None:
        self.checked_invalid_images = set()
        self.monitor_events_task = None
        # The host's unified-vs-legacy cgroup hierarchy; used both to read
        # per-container stats and to resolve OCI cgroupsPath.
        self.cgroup_version = "2" if Path("/sys/fs/cgroup/cgroup.controllers").exists() else "1"
        # Long-lived client to the host containerd. Connect before
        # super().__ainit__() because the base scan_images() call already
        # needs it.
        self.containerd = ContainerdClient()
        await self.containerd.connect()
        await self.containerd.ensure_namespace()
        version = await self.containerd.version()
        log.info(
            "connected to containerd {} (namespace: {!r}, cgroup v{})",
            version.version,
            self.containerd.namespace,
            self.cgroup_version,
        )
        # Fail fast on CNI / network misconfiguration before any kernel work.
        containerd_config = self.local_config.container.containerd
        if containerd_config is None:
            raise ConfigurationError({
                "ContainerdAgent.__ainit__": (
                    "container.containerd is required when agent.backend='containerd'."
                )
            })
        await run_preflight(containerd_config)
        # Build the pluggable network provider for the configured mode.
        match containerd_config.network.mode:
            case ContainerdNetworkMode.CILIUM:
                provider: NetworkProvider = CiliumNetworkProvider(
                    network_name=containerd_config.network.network_name,
                    cni_conf_dir=containerd_config.network.cni_conf_dir,
                    cni_bin_dir=containerd_config.network.cni_bin_dir,
                )
                await provider.preflight()
                self.network_provider = provider
            case _:
                # 'managed' / 'host' / 'none' provider impls are not wired
                # yet; the kernel create path will raise a clear error if
                # one is needed but absent.
                self.network_provider = None
        # The agent socket is bind-mounted into kernels for in-container
        # callbacks; the socket handler task is wired in a later increment.
        ipc_base_path = self.local_config.agent.ipc_base_path
        ipc_container_path = ipc_base_path / "container"
        ipc_container_path.mkdir(parents=True, exist_ok=True)
        self.agent_sockpath = ipc_container_path / f"agent.{self.id}.sock"
        await super().__ainit__()
        # Subscribe to containerd task events so kernel termination is
        # picked up immediately instead of waiting for the base agent's
        # sync_container_lifecycles polling sweep.
        self.monitor_events_task = asyncio.create_task(self.monitor_containerd_events())

    async def shutdown(self, stop_signal: signal.Signals) -> None:
        if self.monitor_events_task is not None:
            self.monitor_events_task.cancel()
            try:
                await self.monitor_events_task
            except (asyncio.CancelledError, ContainerdRpcError):
                pass
        try:
            await super().shutdown(stop_signal)
        finally:
            await self.containerd.close()

    @override
    async def _load_kernel_registry_from_recovery(
        self,
    ) -> MutableMapping[KernelId, AbstractKernel]:
        # Crash recovery is deferred to a later increment; on a fresh start
        # there is nothing to restore, so keep the live (empty) registry.
        return self.kernel_registry

    @override
    async def _write_kernel_registry_to_recovery(
        self,
        kernel_registry: MutableMapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
    ) -> None:
        # Registry persistence is deferred together with crash recovery.
        del kernel_registry, metadata

    @override
    def get_cgroup_path(self, controller: str, container_id: str) -> Path:
        mount_point = get_cgroup_mount_point(self.cgroup_version, controller)
        # Matches oci.build_oci_spec()'s cgroupsPath ("/backendai/<cid>"):
        # runc with the default cgroupfs driver creates the container's
        # cgroup at that path under the controller mount point.
        return mount_point / "backendai" / container_id

    @override
    def get_cgroup_version(self) -> str:
        return self.cgroup_version

    @override
    async def extract_image_command(self, image: str) -> list[str] | None:
        config_doc = await self.containerd.get_image_oci_config(image)
        config = config_doc.get("config") or {}
        command = config.get("Cmd")
        if command is None:
            return None
        if isinstance(command, str):
            return [command]
        if isinstance(command, list):
            return [str(part) for part in command]
        return None

    @override
    async def enumerate_containers(
        self,
        status_filter: frozenset[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> Sequence[tuple[KernelId, Container]]:
        # Walk this namespace's containers and report the ones owned by
        # this agent. A container's active/dead state is its task's
        # status; a container with no task at all is treated as exited
        # (probably mid-teardown). Live-kernel re-attachment after agent
        # restart still needs the kernel-registry recovery piece to be
        # implemented; this method covers the cleanup side of the loop
        # (DEAD entries are picked up by scan_running_kernels and
        # routed through clean_kernel) so stale workloads from a prior
        # crash get torn down on the next start.
        agent_id_str = str(self.id)
        results: list[tuple[KernelId, Container]] = []
        for c in await self.containerd.list_containers():
            labels = dict(c.labels)
            kernel_id_label = labels.get(LabelName.KERNEL_ID)
            if not kernel_id_label:
                continue
            if labels.get(LabelName.OWNER_AGENT) != agent_id_str:
                continue
            try:
                process = await self.containerd.get_task(c.id)
            except ContainerdRpcError as e:
                log.warning(
                    "enumerate_containers: get_task({}) failed; treating as dead: {}",
                    c.id,
                    e,
                )
                process = None
            if process is None:
                status = ContainerStatus.EXITED
            else:
                status = _TASK_STATUS_MAP.get(process.status, ContainerStatus.DEAD)
            if status not in status_filter:
                continue
            try:
                kernel_id = KernelId(UUID(kernel_id_label))
            except ValueError:
                log.warning(
                    "enumerate_containers: container {} has malformed kernel-id "
                    "label {!r}; skipping",
                    c.id,
                    kernel_id_label,
                )
                continue
            results.append((
                kernel_id,
                Container(
                    id=ContainerId(c.id),
                    status=status,
                    image=c.image,
                    labels=labels,
                    ports=[],
                    backend_obj=c,
                ),
            ))
        return results

    @override
    async def resolve_image_distro(self, image: ImageConfig) -> str:
        distro = image["labels"].get(LabelName.BASE_DISTRO)
        if distro:
            return distro
        # The docker backend probes `ldd --version` in a throwaway
        # container; that probe is deferred for the containerd backend, so
        # fall back to the base-distro label inside the image's OCI config.
        config_doc = await self.containerd.get_image_oci_config(image["canonical"])
        config_labels = (config_doc.get("config") or {}).get("Labels") or {}
        distro = config_labels.get(LabelName.BASE_DISTRO)
        if distro:
            return str(distro)
        raise ContainerdImageError(
            f"cannot determine the base distro of image {image['canonical']!r}: "
            f"the {LabelName.BASE_DISTRO} label is absent"
        )

    @override
    async def scan_images(self) -> ScanImagesResult:
        scanned_images: dict[ImageCanonical, InstalledImageInfo] = {}
        removed_images: dict[ImageCanonical, InstalledImageInfo] = {}
        for image in await self.containerd.list_images():
            repo_tag = image.name
            if repo_tag.endswith("<none>"):
                continue
            try:
                ImageRef.parse_image_str(repo_tag, "*")
            except (InvalidImageName, InvalidImageTag) as e:
                if repo_tag not in self.checked_invalid_images:
                    log.warning(
                        "Image name {} does not conform to Backend.AI's image "
                        "naming rule. This image will be ignored. Details: {}",
                        repo_tag,
                        e,
                    )
                    self.checked_invalid_images.add(repo_tag)
                continue
            try:
                config_doc = await self.containerd.get_image_oci_config(repo_tag)
            except (ContainerdRpcError, ContainerdImageError) as e:
                log.warning("could not read the OCI config of image {}: {}", repo_tag, e)
                continue
            labels = (config_doc.get("config") or {}).get("Labels") or {}
            kernelspec = int(labels.get(LabelName.KERNEL_SPEC, "1"))
            if not (MIN_KERNELSPEC <= kernelspec <= MAX_KERNELSPEC):
                continue
            inspect_result: dict[str, str] = {"Id": image.target.digest}
            if architecture := config_doc.get("architecture"):
                inspect_result["Architecture"] = str(architecture)
            scanned_images[ImageCanonical(repo_tag)] = InstalledImageInfo.from_inspect_result(
                canonical=repo_tag,
                inspect_result=inspect_result,
            )
        for added_image in scanned_images.keys() - self.images.keys():
            log.debug("found kernel image: {0}", added_image)
        for removed_image in self.images.keys() - scanned_images.keys():
            log.debug("removed kernel image: {0}", removed_image)
            removed_images[removed_image] = self.images[removed_image]
        return ScanImagesResult(
            scanned_images=scanned_images,
            removed_images=removed_images,
        )

    @override
    async def pull_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout_seconds: float | None,
    ) -> None:
        log.info("pulling image {} via the containerd Transfer service", image_ref.canonical)
        # Registries that accept Basic-Auth directly (harbor, GitLab,
        # ECR with static creds, ...) are covered by the resolver header
        # path inside ContainerdClient.pull_image. Token-exchange-only
        # registries (Docker Hub) still need the Transfer auth-callback
        # stream, which is not implemented here.
        username = registry_conf.get("username") or None
        password = registry_conf.get("password") or None
        pull = self.containerd.pull_image(
            image_ref.canonical,
            username=username,
            password=password,
        )
        if timeout_seconds is not None:
            await asyncio.wait_for(pull, timeout=timeout_seconds)
        else:
            await pull

    @override
    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        try:
            image = await self.containerd.get_image(image_ref.canonical)
        except ContainerdImageError as e:
            if auto_pull in (AutoPullBehavior.DIGEST, AutoPullBehavior.TAG):
                return True
            if auto_pull == AutoPullBehavior.NONE:
                raise ImageNotAvailable(image_ref) from e
            return False
        if auto_pull == AutoPullBehavior.DIGEST and image.target.digest != image_id:
            return True
        log.info("found the local up-to-date image for {}", image_ref.canonical)
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
        if self.network_provider is None:
            raise ConfigurationError({
                "ContainerdAgent.init_kernel_context": (
                    "no network provider was built; only 'cilium' mode is wired today."
                )
            })
        containerd_config = self.local_config.container.containerd
        if containerd_config is None:
            # __ainit__ already enforces this; the recheck just narrows
            # the optional for the type checker.
            raise ConfigurationError({
                "ContainerdAgent.init_kernel_context": (
                    "container.containerd is required when agent.backend='containerd'."
                )
            })
        distro = await self.resolve_image_distro(kernel_config["image"])
        del cluster_ssh_port_mapping  # not yet threaded through to the context.
        return ContainerdKernelCreationContext(
            ownership_data,
            self.event_producer,
            kernel_image,
            kernel_config,
            distro,
            self.local_config,
            self.computers,
            containerd_client=self.containerd,
            network_provider=self.network_provider,
            port_pool=self.port_pool,
            agent_sockpath=self.agent_sockpath,
            resource_lock=self.resource_lock,
            k8s_pod_namespace=containerd_config.network.cilium_pod_namespace,
            k8s_pod_name_prefix=containerd_config.network.cilium_pod_name_prefix,
            restarting=restarting,
        )

    @override
    async def destroy_kernel(
        self,
        kernel_id: KernelId,
        container_id: ContainerId | None,
    ) -> None:
        if container_id is None:
            return
        try:
            await self.containerd.kill_task(str(container_id))
        except ContainerdRpcError as e:
            # Already dead or task already deleted — clean_kernel does
            # the final teardown either way; treat as a soft warning.
            log.warning(
                "destroy_kernel(k:{}) kill_task failed (probably already dead): {}",
                kernel_id,
                e,
            )

    @override
    async def clean_kernel(
        self,
        kernel_id: KernelId,
        container_id: ContainerId | None,
        restarting: bool,
    ) -> None:
        kernel_obj = self.kernel_registry.get(kernel_id)
        container_id_str = str(container_id) if container_id is not None else None
        netns_name: str | None = None
        ns_path: str | None = None
        if kernel_obj is not None:
            netns_name = kernel_obj.get("netns_name")
            ns_path = kernel_obj.get("netns_path")
            for domain_socket_proxy in kernel_obj.get("domain_socket_proxies", []):
                if domain_socket_proxy.proxy_server.is_serving():
                    domain_socket_proxy.proxy_server.close()
                    await domain_socket_proxy.proxy_server.wait_closed()
                    try:
                        domain_socket_proxy.host_proxy_path.unlink()
                    except OSError:
                        pass

        if container_id_str is not None:
            # Best-effort teardown: each step is independent and we
            # continue past a failed step so a partial creation still
            # cleans up as much as possible.
            try:
                await self.containerd.delete_task(container_id_str)
            except ContainerdRpcError as e:
                log.warning("clean_kernel(k:{}) delete_task: {}", kernel_id, e)
            if not self.local_config.debug.skip_container_deletion:
                try:
                    await self.containerd.delete_container(container_id_str)
                except ContainerdRpcError as e:
                    log.warning("clean_kernel(k:{}) delete_container: {}", kernel_id, e)
                try:
                    await self.containerd.remove_snapshot(container_id_str)
                except ContainerdRpcError as e:
                    log.warning("clean_kernel(k:{}) remove_snapshot: {}", kernel_id, e)

        if (
            container_id_str is not None
            and ns_path is not None
            and self.network_provider is not None
        ):
            try:
                await self.network_provider.detach(container_id_str, ns_path)
            except Exception as e:
                log.warning("clean_kernel(k:{}) cni detach: {!r}", kernel_id, e)
        if netns_name is not None:
            try:
                await delete_netns(netns_name)
            except Exception as e:
                log.warning("clean_kernel(k:{}) delete_netns: {!r}", kernel_id, e)

        if not restarting:
            scratch_root = self.local_config.container.scratch_root
            scratch_type = self.local_config.container.scratch_type
            scratch_dir = scratch_root / str(kernel_id)
            tmp_dir = scratch_root / f"{kernel_id}_tmp"
            try:
                if sys.platform.startswith("linux") and scratch_type == ScratchType.MEMORY:
                    await destroy_scratch_filesystem(scratch_dir)
                    await destroy_scratch_filesystem(tmp_dir)
                    await asyncio.to_thread(shutil.rmtree, scratch_dir)
                    await asyncio.to_thread(shutil.rmtree, tmp_dir)
                elif sys.platform.startswith("linux") and scratch_type == ScratchType.HOSTFILE:
                    await destroy_loop_filesystem(scratch_root, kernel_id)
                else:
                    await asyncio.to_thread(shutil.rmtree, scratch_dir)
            except (CalledProcessError, FileNotFoundError):
                pass

    @override
    async def push_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout_seconds: float | None | Sentinel = Sentinel.TOKEN,
    ) -> None:
        del image_ref, registry_conf, timeout_seconds
        raise NotImplementedError("containerd image push is not implemented yet")

    @override
    async def purge_images(self, request: PurgeImagesReq) -> PurgeImagesResp:
        del request
        raise NotImplementedError("containerd image purge is not implemented yet")

    @override
    async def create_local_network(self, network_name: str) -> None:
        del network_name
        # The containerd backend uses CNI-managed networks instead of
        # a per-cluster docker bridge; there is nothing to create here.
        raise NotImplementedError("create_local_network is not supported by the containerd backend")

    @override
    async def destroy_local_network(self, network_name: str) -> None:
        del network_name
        raise NotImplementedError(
            "destroy_local_network is not supported by the containerd backend"
        )

    @override
    async def restart_kernel__load_config(
        self,
        kernel_id: KernelId,
        name: str,
    ) -> bytes:
        scratch_dir = (self.local_config.container.scratch_root / str(kernel_id)).resolve()
        config_dir = scratch_dir / "config"
        return await asyncio.to_thread((config_dir / name).read_bytes)

    @override
    async def restart_kernel__store_config(
        self,
        kernel_id: KernelId,
        name: str,
        data: bytes,
    ) -> None:
        scratch_dir = (self.local_config.container.scratch_root / str(kernel_id)).resolve()
        config_dir = scratch_dir / "config"
        await asyncio.to_thread((config_dir / name).write_bytes, data)

    async def monitor_containerd_events(self) -> None:
        """Drive CLEAN / OOM lifecycle events from containerd's event stream.

        Subscribes to ``/tasks/exit`` and ``/tasks/oom`` events scoped to
        this client's namespace. On a task exit, injects a CLEAN
        lifecycle event so the kernel is torn down immediately; on OOM,
        forwards an ``oom`` notification to the kernel so the krunner can
        surface it. The stream is reconnected with exponential backoff
        on transport errors (the underlying gRPC stream can break when
        containerd restarts).
        """
        namespace = self.containerd.namespace
        filters = [
            f"namespace=={namespace},topic==/tasks/exit",
            f"namespace=={namespace},topic==/tasks/oom",
        ]
        backoff = 1.0
        while True:
            try:
                async for envelope in self.containerd.subscribe_events(filters=filters):
                    await self._handle_containerd_event(envelope)
                # The stream ended cleanly (no exception); containerd is
                # likely restarting. Fall through to the backoff branch.
                log.warning(
                    "containerd events stream closed; reconnecting in {:.1f}s",
                    backoff,
                )
            except asyncio.CancelledError:
                return
            except ContainerdRpcError as e:
                log.warning(
                    "containerd events stream error ({}); reconnecting in {:.1f}s",
                    e,
                    backoff,
                )
            except Exception:
                log.exception(
                    "unexpected error in containerd events stream; reconnecting in {:.1f}s",
                    backoff,
                )
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30.0)

    async def _handle_containerd_event(self, envelope: Any) -> None:
        """Dispatch a single ``Events.Subscribe`` envelope.

        Filters out events whose ``container_id`` does not match the
        ``kernel-{kernel_id}`` convention from ``start_container``; the
        kernel-id is parsed back out without a containerd lookup.
        """
        topic = envelope.topic
        container_id_field: str = ""
        exit_code = 0
        if topic == "/tasks/exit":
            exit_event = events_task_pb2.TaskExit()
            envelope.event.Unpack(exit_event)
            container_id_field = exit_event.container_id
            exit_code = exit_event.exit_status
        elif topic == "/tasks/oom":
            oom_event = events_task_pb2.TaskOOM()
            envelope.event.Unpack(oom_event)
            container_id_field = oom_event.container_id
        else:
            return
        if not container_id_field.startswith("kernel-"):
            return  # not one of ours.
        kernel_id_str = container_id_field[len("kernel-") :]
        try:
            kernel_id = KernelId(UUID(kernel_id_str))
        except ValueError:
            return
        kernel_obj = self.kernel_registry.get(kernel_id)
        if kernel_obj is None:
            # The event may arrive after our own clean_kernel removed
            # the registry entry; nothing more to do here.
            return
        if topic == "/tasks/oom":
            await kernel_obj.notify_event(AgentEventData(type="oom", data={}))
            return
        reason = kernel_obj.termination_reason or KernelLifecycleEventReason.SELF_TERMINATED
        await self.inject_container_lifecycle_event(
            kernel_id,
            kernel_obj.session_id,
            LifecycleEvent.CLEAN,
            reason,
            container_id=ContainerId(container_id_field),
            exit_code=exit_code,
        )

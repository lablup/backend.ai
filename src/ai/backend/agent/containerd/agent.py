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
import sys
from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal
from functools import partial
from importlib.resources import files
from pathlib import Path
from subprocess import CalledProcessError
from subprocess import run as subprocess_run
from typing import Any, override

import aiotools

from ai.backend.agent.agent import AbstractAgent, AbstractKernelCreationContext
from ai.backend.agent.config.unified import AgentUnifiedConfig, ScratchType
from ai.backend.agent.exception import UnsupportedResource
from ai.backend.agent.fs import create_scratch_filesystem
from ai.backend.agent.port_pool import PortPool
from ai.backend.agent.proxy import DomainSocketProxy, proxy_connection
from ai.backend.agent.resources import (
    AbstractComputePlugin,
    ComputerContext,
    KernelResourceSpec,
    Mount,
    known_slot_types,
)
from ai.backend.agent.scratch import create_loop_filesystem
from ai.backend.agent.types import KernelOwnershipData, MountInfo
from ai.backend.agent.utils import get_arch_name
from ai.backend.common.asyncio import current_loop
from ai.backend.common.docker import ImageRef, KernelFeatures
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.json import dump_json
from ai.backend.common.types import (
    ClusterInfo,
    DeviceId,
    DeviceName,
    KernelCreationConfig,
    MountPermission,
    MountTypes,
    ResourceGroupType,
    ResourceSlot,
    SlotName,
    current_resource_slots,
)
from ai.backend.logging import BraceStyleAdapter

from .client.client import ContainerdClient
from .kernel import ContainerdKernel
from .network.base import NetworkProvider

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


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


class ContainerdAgent(AbstractAgent[ContainerdKernel, ContainerdKernelCreationContext]):
    """Containerd-backed agent (prototype scaffold).

    Concrete operations will be implemented over the containerd native
    gRPC API via ``ContainerdClient``. The abstract methods inherited from
    ``AbstractAgent`` are intentionally left unoverridden so the class is
    not yet instantiable; this scaffold exists to validate package wiring
    and discovery only, and is filled in by a later increment.
    """

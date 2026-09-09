from __future__ import annotations

import asyncio
import base64
import contextlib
import logging
import os
import re
import secrets
import shutil
import signal
import struct
import sys
from collections.abc import AsyncGenerator, Iterable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from functools import partial
from http import HTTPStatus
from importlib.resources import files
from io import StringIO
from pathlib import Path
from subprocess import CalledProcessError
from subprocess import run as subprocess_run
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    cast,
    override,
)
from uuid import UUID

import aiofiles
import aiohttp
import aiotools
import zmq
import zmq.asyncio
from aiodocker.docker import Docker, DockerContainer
from aiodocker.exceptions import DockerContainerError, DockerError
from aiodocker.types import PortInfo
from aiomonitor.task import preserve_termination_log
from aiotools import TaskGroup
from async_timeout import timeout
from cachetools import LRUCache
from pydantic import BaseModel, Field

from ai.backend.agent.agent import (
    ACTIVE_STATUS_SET,
    AbstractAgent,
    AbstractKernelCreationContext,
    AgentClass,
    ScanImagesResult,
)
from ai.backend.agent.config.unified import (
    AgentUnifiedConfig,
    ContainerLogDriver,
    ContainerSandboxType,
    ScratchType,
)
from ai.backend.agent.errors import (
    ContainerCreationError,
    InvalidArgumentError,
    UnsupportedResource,
)
from ai.backend.agent.errors.network import ContainerLifecycleUnavailable
from ai.backend.agent.errors.resources import PortPoolExhaustedError, ResourceError
from ai.backend.agent.etcd import AgentEtcdClientView
from ai.backend.agent.fs import create_scratch_filesystem, destroy_scratch_filesystem
from ai.backend.agent.kernel import AbstractKernel, KernelRegistry
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
from ai.backend.agent.kernel_registry.recovery.docker_recovery import (
    DockerKernelRegistryRecovery,
)
from ai.backend.agent.kernel_registry.writer.types import KernelRegistrySaveMetadata
from ai.backend.agent.network.caps import (
    probe_caps,
    publish_caps,
    publish_vtep,
    withdraw_caps,
    withdraw_vtep,
)
from ai.backend.agent.network.dns import resolve_container_dns
from ai.backend.agent.network.port_forward import (
    PortForwarder,
    PortPublisher,
    forwards_for,
)
from ai.backend.agent.network.privnet.client import PrivNetPortForwarder
from ai.backend.agent.network.session_network import SessionNetwork
from ai.backend.agent.network.vtep import uplink_for_ip, usable_vtep
from ai.backend.agent.plugin.network import (
    ContainerNetworkCapability,
    ContainerNetworkInfo,
    NetworkPluginContext,
)
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
    Port,
    VolumeInfo,
)
from ai.backend.agent.utils import (
    closing_async,
    container_pid_to_host_pid,
    get_arch_name,
    get_kernel_id_from_container,
    get_safe_ulimit,
    host_pid_to_container_pid,
    update_nested_dict,
)
from ai.backend.common.asyncio import current_loop
from ai.backend.common.cgroup import (
    CgroupController,
    get_cgroup_path_of_pid,
    get_container_main_pid,
)
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
from ai.backend.common.files import AsyncFileWriter
from ai.backend.common.json import (
    dump_json,
    dump_json_str,
    load_json,
)
from ai.backend.common.network.types import SessionNetMeta
from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext
from ai.backend.common.types import (
    AgentId,
    AutoPullBehavior,
    BinarySize,
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
from ai.backend.logging.formatter import pretty

from .gate import apply_gate, release_gate, stage_gate, wait_gated_pid
from .kernel import DockerKernel
from .session_network import (
    NO_NETWORK_MODE,
    build_docker_session_network,
    is_session_networked,
)
from .utils import PersistentServiceContainer

if TYPE_CHECKING:
    from ai.backend.common.auth import PublicKey

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

#: How often the published network capabilities are refreshed. Their readiness half is a
#: question that does not stay answered -- the privileged helper can die long after startup.
_NETWORK_IDENTITY_REFRESH_SEC = 60.0
eof_sentinel = Sentinel.TOKEN

LDD_GLIBC_REGEX = re.compile(r"^ldd \([^\)]+\) (\d+(?:\.\d+)?)[\d\.]*$")
LDD_MUSL_REGEX = re.compile(r"^musl libc .+$")

# The merged seccomp profile written next to a kernel's scratch contents.
_SECCOMP_PROFILE_FILENAME: Final[str] = "seccomp.json"
# Container runtimes disagree on the seccomp option value: some decode it as the profile
# document, others open it as a path, and neither accepts the other form. These engine
# components, as reported by the version API, are the ones that require a path.
_SECCOMP_PATH_ENGINES: Final[frozenset[str]] = frozenset({"Podman Engine"})
# Cached per container, so the capacity is the number of containers an agent may host.
_CGROUP_PATH_CACHE_SIZE: Final[int] = 2048

# Docker splits the configured total container-log size across this many files.
_CONTAINER_LOG_FILE_COUNT: Final[int] = 5
# Controllers the intrinsic plugins read, resolved together from a single inspect.
_TRACKED_CGROUP_CONTROLLERS: Final[tuple[CgroupController, ...]] = (
    CgroupController.CPUACCT,
    CgroupController.MEMORY,
    CgroupController.BLKIO,
)

known_glibc_distros: Final[dict[float, str]] = {
    2.17: "centos7.6",
    2.27: "ubuntu18.04",
    2.28: "centos8.0",
    2.31: "ubuntu20.04",
    2.34: "centos9.0",
    2.35: "ubuntu22.04",
    2.39: "ubuntu24.04",
}


class LogDriverOptions(BaseModel):
    """
    Log rotation options. The Docker API takes every value as a string,
    under kebab-case keys.
    """

    max_size: str = Field(serialization_alias="max-size")
    max_file: str = Field(serialization_alias="max-file")
    compress: str = Field(serialization_alias="compress")


class LogConfig(BaseModel):
    """
    The ``HostConfig.LogConfig`` payload of a container creation request,
    keyed in PascalCase as the Docker API expects.
    """

    type: ContainerLogDriver = Field(serialization_alias="Type")
    config: LogDriverOptions = Field(serialization_alias="Config")


def _build_log_config(local_config: AgentUnifiedConfig) -> LogConfig:
    """
    Build the ``HostConfig.LogConfig`` payload for a kernel container.

    Every supported driver keeps its own on-disk log files, so the configured
    total size is split across a fixed number of rotated files.
    """
    container_logs = local_config.container_logs
    file_size = BinarySize(container_logs.max_length // _CONTAINER_LOG_FILE_COUNT)
    return LogConfig(
        type=container_logs.driver,
        config=LogDriverOptions(
            max_size=f"{file_size:s}",
            max_file=str(_CONTAINER_LOG_FILE_COUNT),
            compress="false",
        ),
    )


def _parse_distro_from_ldd_output(log_chunks: Sequence[str]) -> str | None:
    for line in "".join(log_chunks).splitlines():
        stripped_line = line.strip()
        if m := LDD_GLIBC_REGEX.search(stripped_line):
            version = float(m.group(1))
            if version in known_glibc_distros:
                return known_glibc_distros[version]
            for idx, known_version in enumerate(known_glibc_distros.keys()):
                if version < known_version:
                    return list(known_glibc_distros.values())[max(idx - 1, 0)]
            return list(known_glibc_distros.values())[-1]
        if LDD_MUSL_REGEX.search(stripped_line):
            return "alpine3.8"
    return None


deeplearning_image_keys = {
    "tensorflow",
    "caffe",
    "keras",
    "torch",
    "mxnet",
    "theano",
}

deeplearning_sample_volume = VolumeInfo(
    "deeplearning-samples",
    "/home/work/samples",
    "ro",
)


async def get_extra_volumes(docker: Docker, lang: str) -> list[VolumeInfo]:
    avail_volumes = (await docker.volumes.list())["Volumes"]  # type: ignore[no-untyped-call]
    if not avail_volumes:
        return []
    avail_volume_names = {v["Name"] for v in avail_volumes}

    # deeplearning specialization
    # TODO: extract as config
    volume_list = []
    for k in deeplearning_image_keys:
        if k in lang:
            volume_list.append(deeplearning_sample_volume)
            break

    # Mount only actually existing volumes
    mount_list = []
    for vol in volume_list:
        if vol.name in avail_volume_names:
            mount_list.append(vol)
        else:
            log.info(
                "skipped attaching extra volume {0} to a kernel based on image {1}",
                vol.name,
                lang,
            )
    return mount_list


def container_from_docker_container(src: DockerContainer) -> Container:
    ports = []
    for private_port, host_ports in src["NetworkSettings"]["Ports"].items():
        private_port = int(private_port.split("/")[0])
        if host_ports is None:
            host_ip = "127.0.0.1"
            host_port = 0
        else:
            host_ip = host_ports[0]["HostIp"]
            host_port = int(host_ports[0]["HostPort"])
        ports.append(Port(host_ip, private_port, host_port))
    return Container(
        id=ContainerId(src.id),
        status=src["State"]["Status"],
        image=src["Config"]["Image"],
        labels=src["Config"]["Labels"],
        ports=ports,
        backend_obj=src,
    )


async def _clean_scratch(
    loop: asyncio.AbstractEventLoop,
    scratch_type: str,
    scratch_root: Path,
    kernel_id: KernelId,
) -> None:
    scratch_dir = scratch_root / str(kernel_id)
    tmp_dir = scratch_root / f"{kernel_id}_tmp"
    try:
        if sys.platform.startswith("linux") and scratch_type == "memory":
            await destroy_scratch_filesystem(scratch_dir)
            await destroy_scratch_filesystem(tmp_dir)
            await loop.run_in_executor(None, shutil.rmtree, scratch_dir)
            await loop.run_in_executor(None, shutil.rmtree, tmp_dir)
        elif sys.platform.startswith("linux") and scratch_type == "hostfile":
            await destroy_loop_filesystem(scratch_root, kernel_id)
        else:
            await loop.run_in_executor(None, shutil.rmtree, scratch_dir)
    except CalledProcessError:
        pass
    except FileNotFoundError:
        pass


def _DockerError_reduce(self: DockerError) -> tuple[type, tuple[Any, ...]]:
    return (
        type(self),
        (self.status, self.message, *self.args),
    )


def _DockerContainerError_reduce(self: DockerContainerError) -> tuple[type, tuple[Any, ...]]:
    return (
        type(self),
        (self.status, self.message, self.container_id, *self.args),
    )


@dataclass
class DockerPurgeImageReq:
    image: str
    force: bool
    noprune: bool


#: The kernel runner's control channel. Reached at the container's own address under BEP-1078,
#: so it is never DNAT'd onto the host and the agent dials these numbers, not a host pairing.
_REPL_IN_PORT: Final = 2000
_REPL_OUT_PORT: Final = 2001
_REPL_PORTS: Final = frozenset({_REPL_IN_PORT, _REPL_OUT_PORT})


def _port_publisher(
    local_config: AgentUnifiedConfig, session_network: SessionNetwork
) -> PortPublisher:
    """Who installs the host-port DNAT for a session-networked kernel.

    It is an iptables (CAP_NET_ADMIN) op, so it belongs to whoever owns the host's networking: this
    agent when it runs privileged, the privnet when privilege is separated. Doing it here under a
    privnet is not a degraded path but a failure -- the agent holds no capability and iptables
    refuses with "you must be root", which is a kernel that never reaches RUNNING. Same choice the
    containerd agent makes; see ContainerdAgent.__ainit__.
    """
    privnet_socket = local_config.agent.network_privnet_socket
    if privnet_socket is None:
        return PortForwarder()
    # The session network's own client, not a fresh one on the same socket. That object is where
    # each session's incarnation is bound, and it is what stamps every request with it; a client
    # built here carries none, so a PUBLISH or UNPUBLISH delayed across a teardown and a rebuild
    # would reach the rules of the session that replaced the one it was issued for.
    client = session_network.privnet_client
    if client is None:
        raise ContainerLifecycleUnavailable(
            "this agent is configured with a privileged network helper, but its session network"
            " holds no client for it; host port rules would be installed unfenced"
        )
    return PrivNetPortForwarder(client, session_network.session_of)


class DockerKernelCreationContext(AbstractKernelCreationContext[DockerKernel]):
    scratch_dir: Path
    tmp_dir: Path
    config_dir: Path
    work_dir: Path
    container_configs: list[Mapping[str, Any]]
    domain_socket_proxies: list[DomainSocketProxy]
    computer_docker_args: dict[str, Any]
    port_pool: PortPool
    agent_sockpath: Path
    resource_lock: asyncio.Lock
    cluster_ssh_port_mapping: ClusterSSHPortMapping | None
    gwbridge_subnet: str | None
    _seccomp_profile_as_path: bool
    #: Whether BAI builds this session's data plane (BEP-1078) instead of Docker. Decided in
    #: apply_network, read where the container is created and started: it is what puts the
    #: container behind a gate so a device can be moved into its netns before its command runs.
    _session_networked: bool
    #: The node's session half (see docker/session_network.py). Shared with the agent: sessions
    #: outlive kernels, so the per-session data plane cannot be owned by one kernel's context.
    _session_network: SessionNetwork
    #: What ensure_session settled on for this session — subnet, VNI, MTU. Needed at attach time.
    _net_meta: SessionNetMeta | None
    #: The container's node-local address, learned from the attach. Docker publishes nothing for a
    #: `NetworkMode: none` container, so this is what the host ports are DNAT'd at.
    _container_ip: str | None

    network_plugin_ctx: NetworkPluginContext

    def __init__(
        self,
        ownership_data: KernelOwnershipData,
        event_producer: EventProducer,
        kernel_image: ImageRef,
        kernel_config: KernelCreationConfig,
        distro: str,
        local_config: AgentUnifiedConfig,
        computers: Mapping[DeviceName, ComputerContext],
        port_pool: PortPool,
        agent_sockpath: Path,
        resource_lock: asyncio.Lock,
        network_plugin_ctx: NetworkPluginContext,
        session_network: SessionNetwork,
        restarting: bool = False,
        cluster_ssh_port_mapping: ClusterSSHPortMapping | None = None,
        seccomp_profile_as_path: bool = False,
        gwbridge_subnet: str | None = None,
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

        self.container_configs = []
        self.domain_socket_proxies = []
        self.computer_docker_args = {}

        self.cluster_ssh_port_mapping = cluster_ssh_port_mapping
        self._seccomp_profile_as_path = seccomp_profile_as_path
        self.gwbridge_subnet = gwbridge_subnet
        self._session_networked = False
        self._session_network = session_network
        self._net_meta = None
        self._container_ip = None

        self.network_plugin_ctx = network_plugin_ctx

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
    @override
    async def destroy_scratch(self) -> None:
        """Take back what `prepare_scratch` made, through the same path a teardown uses."""
        await _clean_scratch(
            current_loop(),
            self.local_config.container.scratch_type,
            self.local_config.container.scratch_root,
            self.kernel_id,
        )

    @override
    async def prepare_scratch(self) -> None:
        loop = current_loop()

        # Create the scratch, config, and work directories.
        scratch_type = self.local_config.container.scratch_type
        scratch_root = self.local_config.container.scratch_root
        scratch_size = self.local_config.container.scratch_size

        if sys.platform.startswith("linux") and scratch_type == "memory":
            await loop.run_in_executor(None, partial(self.tmp_dir.mkdir, exist_ok=True))
            await create_scratch_filesystem(self.scratch_dir, 64)
            await create_scratch_filesystem(self.tmp_dir, 64)
        elif sys.platform.startswith("linux") and scratch_type == "hostfile":
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

        # extra mounts
        async with closing_async(Docker()) as docker:
            extra_mount_list = await get_extra_volumes(docker, self.image_ref.short)
        for v in extra_mount_list:
            permission = MountPermission.READ_ONLY if v.mode == "ro" else MountPermission.READ_WRITE
            mounts.append(
                Mount(MountTypes.VOLUME, Path(v.name), Path(v.container_path), permission)
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
    def _gate_dir(self) -> Path:
        """Where this kernel's start gate lives.

        Under the config dir rather than the work dir: the work dir is the user's home, and the
        wrapper and its FIFO are the agent's, not theirs.
        """
        return self.config_dir / "gate"

    def _session_resolv_conf(self) -> Path:
        """The resolv.conf this kernel gets, bind-mounted over the image's."""
        return self.config_dir / "resolv.conf"

    def _write_session_resolv_conf(self, gateway: str | None = None) -> None:
        """Write the kernel's resolver list, optionally with the session resolver first.

        Rewritten in place rather than replaced: the file is bind-mounted, so glibc picks the new
        contents up on the container's next lookup.
        """
        resolv = resolve_container_dns(self.local_config.container.dns or ())
        if gateway is not None:
            resolv.nameservers = [gateway, *resolv.nameservers]
        self._session_resolv_conf().write_text(resolv.render())

    async def _point_resolv_conf_at_resolver(self) -> None:
        """Prepend the session's cluster resolver, now that the attach has created its gateway.

        Best-effort: with no gateway the upstream-only file stands, which is what a single-kernel
        session wants anyway. `ensure_cluster_dns` is the loud guard for the clustered case.
        """
        gateway = await self._session_network.local_gateway_of(
            str(self.kernel_config["session_id"])
        )
        if gateway is None:
            return
        self._write_session_resolv_conf(gateway)

    async def _publish_session_ports(
        self, cid: str, host_ports: Sequence[int], exposed_ports: Sequence[int]
    ) -> None:
        """DNAT the reserved host ports at the container's node-local address.

        This backend runs its own publisher rather than delegating to a privnet: it already drives
        a root Docker daemon, so the agent process that would delegate the privilege is the one
        that holds it.
        """
        if self._container_ip is None:
            raise ContainerCreationError(
                container_id=ContainerId(cid),
                message="no container address; the kernel's services would be unreachable",
            )
        # Services only. The repl is reached at the container's own address (see DockerKernel),
        # so publishing it would put an interactive channel into the kernel on every local
        # address for no one to use.
        forwards = [
            (hp, cp, None, "tcp")
            for hp, cp in zip(host_ports, exposed_ports, strict=True)
            if cp not in _REPL_PORTS
        ]
        if forwards:
            await _port_publisher(self.local_config, self._session_network).install(
                forwards_for(
                    cid,
                    self._container_ip,
                    forwards,
                    owner_agent_id=str(self.local_config.agent.id),
                )
            )

    async def _attach_session_network(
        self, container: DockerContainer, cid: str, cluster_info: ClusterInfo
    ) -> None:
        """Move this session's device into the gated container, then let its command run.

        The gate is released in a finally: a container parked forever is worse than one whose
        network failed, because nothing times it out and the failure has no message. The attach
        itself is atomic — it rolls back its own partial ADDs — so releasing after a failure starts
        a kernel with no network, which the caller's own error path then tears down.
        """
        if self._net_meta is None:
            raise ContainerCreationError(
                container_id=ContainerId(cid),
                message="the session network was never set up for this kernel",
            )
        try:
            task_pid = await wait_gated_pid(container, self._gate_dir)
            result = await self._session_network.attach_container(
                str(self.kernel_config["session_id"]),
                cid,
                # Docker names the container, so its id is not the kernel id the session claim was
                # made under; the tracker needs both to retire that claim.
                kernel_id=str(self.kernel_id),
                meta=self._net_meta,
                kernel_config=self.kernel_config,
                cluster_info=cluster_info,
                task_pid=task_pid,
            )
            self._container_ip = result.local_ip
            # The gateway the session resolver listens on exists only now: the attach allocated
            # the session's LOCAL block.
            await self._point_resolv_conf_at_resolver()
            if self._container_ip is None:
                raise ContainerCreationError(
                    container_id=ContainerId(cid),
                    message="the LOCAL attachment yielded no address; cannot publish ports",
                )
        finally:
            await asyncio.to_thread(release_gate, self._gate_dir)

    @override
    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        if is_session_networked(cluster_info):
            # BEP-1078: this session's data plane is BAI's, not Docker's. The container starts with
            # no network at all and the agent moves a vxlan (or node-local bridge) device into its
            # netns by PID, which is why it must also be held at a gate until that has happened.
            # Handing it to Docker's networking as well would put it on two networks, one of which
            # nothing routes.
            self._net_meta = await self._session_network.ensure_session(
                str(self.kernel_config["session_id"]),
                str(self.kernel_id),
                cluster_info["network_config"],
            )
            self.container_configs.append({
                "HostConfig": {
                    "NetworkMode": NO_NETWORK_MODE,
                    # Docker writes its own /etc/resolv.conf, and for a `none` container that file
                    # names no resolver this session can use. Bind ours over it: the upstream
                    # servers now, the session's cluster resolver prepended once the attach has
                    # created the gateway it listens on. Without that a clustered kernel cannot
                    # resolve its peers and blocks at rendezvous — with the runner up and
                    # listening, which is what makes it look like a slow start rather than a
                    # missing resolver.
                    "Binds": [f"{self._session_resolv_conf()}:/etc/resolv.conf:rw"],
                },
            })
            self._write_session_resolv_conf()
            self._session_networked = True
            return
        # FIXME: find out way to inect network ID to kernel resource spec
        match cluster_info["network_config"].get("mode"):
            case "bridge":
                self.container_configs.append({
                    "HostConfig": {
                        "NetworkMode": cluster_info["network_config"]["network_name"],
                    },
                    "NetworkingConfig": {
                        "EndpointsConfig": {
                            cluster_info["network_config"]["network_name"]: {
                                "Aliases": [self.kernel_config["cluster_hostname"]],
                            },
                        },
                    },
                })
            case mode if mode:
                try:
                    plugin = self.network_plugin_ctx.plugins[mode]
                except KeyError as e:
                    raise RuntimeError(f"Network plugin {mode} not loaded!") from e

                container_config = await plugin.join_network(
                    self.kernel_config, cluster_info, **cluster_info["network_config"]
                )
                self.container_configs.append(container_config)
                if self.gwbridge_subnet is not None:
                    self.container_configs.append({
                        "Env": [f"OMPI_MCA_btl_tcp_if_exclude=127.0.0.1/32,{self.gwbridge_subnet}"],
                    })
        if self.local_config.container.alternative_bridge is not None:
            self.container_configs.append({
                "HostConfig": {
                    "NetworkMode": self.local_config.container.alternative_bridge,
                },
            })
        # RDMA mounts
        ib_root = Path("/dev/infiniband")
        if ib_root.is_dir() and (ib_root / "uverbs0").exists():
            self.container_configs.append({
                "HostConfig": {
                    "Devices": [
                        {
                            "PathOnHost": "/dev/infiniband",
                            "PathInContainer": "/dev/infiniband",
                            "CgroupPermissions": "rwm",
                        },
                    ],
                },
            })

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
                            "dropbearkey failed. Host key will regenerate on container startup. Return code {code}, stdout: {stdout}, stderr: {stderr}",
                            code=e.returncode,
                            stdout=stdout,
                            stderr=stderr,
                        )
                    except OSError as e:
                        log.warning(
                            "failed to execute dropbearmulti for host key generation. Host key will regenerate on container startup: {}",
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
        def fix_unsupported_perm(folder_perm: MountPermission) -> MountPermission:
            if folder_perm == MountPermission.RW_DELETE:
                # TODO: enforce readable/writable but not deletable
                # (Currently docker's READ_WRITE includes DELETE)
                return MountPermission.READ_WRITE
            return folder_perm

        container_config = {
            "HostConfig": {
                "Mounts": [
                    {
                        "Target": str(mount.target),
                        "Source": str(mount.source),
                        "Type": mount.type.value,
                        "ReadOnly": (
                            fix_unsupported_perm(mount.permission) == MountPermission.READ_ONLY
                        ),
                        f"{mount.type.value.capitalize()}Options": mount.opts if mount.opts else {},
                    }
                    for mount in mounts
                ],
            },
        }
        self.container_configs.append(container_config)

    @override
    async def apply_accelerator_allocation(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        async with closing_async(Docker()) as docker:
            update_nested_dict(
                self.computer_docker_args,
                await computer.generate_docker_args(docker, device_alloc),
            )

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
    ) -> DockerKernel:
        loop = current_loop()
        ouid = self.get_overriding_uid()
        ogid = self.get_overriding_gid()

        if self.restarting:
            pass
        else:
            # Create bootstrap.sh into workdir if needed
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
                accel_envs = self.computer_docker_args.get("Env", [])
                for env in accel_envs:
                    buf.write(f"{env}\n")
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

        # TODO: refactor out dotfiles/sshkey initialization to the base agent?
        docker_creds = self.internal_data.get("docker_credentials")
        if docker_creds:
            await loop.run_in_executor(
                None,
                (self.config_dir / "docker-creds.json").write_bytes,
                dump_json(docker_creds),
            )

        # Create SSH keypair only if ssh_keypair internal_data exists and
        # /home/work/.ssh folder is not mounted.
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

        # higher priority dotfiles are stored last to support overwriting
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

        return DockerKernel(
            self.ownership_data,
            self.kernel_config["network_id"],
            self.image_ref,
            self.kspec_version,
            cluster_info["network_config"].get("mode", "bridge"),
            agent_config=self.local_config.model_dump(by_alias=True),
            service_ports=service_ports,
            resource_spec=resource_spec,
            environ=environ,
            data={},
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

    async def _apply_seccomp_profile(self, container_config: MutableMapping[str, Any]) -> None:
        default_seccomp_path = self.resolve_krunner_filepath("runner/default-seccomp.json")

        if not default_seccomp_path.exists():
            log.warning(
                "Default seccomp profile file not found in the expected path! Skipped the application of additional syscalls."
            )
            return

        async with aiofiles.open(default_seccomp_path) as fp:
            seccomp_profile = load_json(await fp.read())

        additional_allowed_syscalls = self.additional_allowed_syscalls
        additional_allowed_syscall_rule = {
            "names": additional_allowed_syscalls,
            "action": "SCMP_ACT_ALLOW",
            "args": [],
            "comment": "Additionally allowed syscalls by Backend.AI Agent",
        }
        seccomp_profile["syscalls"].append(additional_allowed_syscall_rule)

        # Some runtimes decode the option value as the profile document itself, others
        # open it as a path; neither accepts the other's form.
        if self._seccomp_profile_as_path:
            profile_path = self.scratch_dir / _SECCOMP_PROFILE_FILENAME
            async with aiofiles.open(profile_path, "w") as fp:
                await fp.write(dump_json_str(seccomp_profile))
            await current_loop().run_in_executor(None, profile_path.chmod, 0o644)
            security_opt = f"seccomp={profile_path}"
        else:
            security_opt = f"seccomp={dump_json_str(seccomp_profile)}"

        container_config["HostConfig"]["SecurityOpt"] = [security_opt]

    async def _provision_or_name_the_container(
        self,
        docker: Docker,
        container: DockerContainer,
        cid: str,
        cluster_info: ClusterInfo,
        resource_spec: KernelResourceSpec,
    ) -> None:
        """`_provision_started_container`, with every failure named by the container it happened
        to.

        The container is already up by the time any of that runs, so a failure has to carry its
        id out: a plain exception reached the agent's handler as "kernel failed" with no id,
        `destroy_kernel` had nothing to act on, and the container went on running with its kernel
        already gone from the registry.
        """
        try:
            await self._provision_started_container(
                docker, container, cid, cluster_info, resource_spec
            )
        except ContainerCreationError:
            raise
        except Exception as e:
            raise ContainerCreationError(
                container_id=cid,
                message=f"failed after the container was started: {e!r}",
            ) from e

    async def _provision_started_container(
        self,
        docker: Docker,
        container: DockerContainer,
        cid: str,
        cluster_info: ClusterInfo,
        resource_spec: KernelResourceSpec,
    ) -> None:
        """Everything done to a container that is already running.

        Kept together because they share one property: the container exists, so a failure in any
        of them has to carry its id out to whoever will destroy it. The caller turns anything
        raised here into a `ContainerCreationError` naming the container.
        """
        if self._session_networked:
            # The container is running but parked: its namespaces exist and its PID is final,
            # and its command has not started. This is the only window in which the session's
            # device can be moved in -- after the release the runner immediately binds its REPL
            # and looks its peers up, and an attach racing that surfaces as a hang at
            # rendezvous rather than as an error here.
            await self._attach_session_network(container, cid, cluster_info)

        if self.internal_data.get("sudo_session_enabled", False):
            exec = await container.exec(
                [
                    # file ownership is guaranteed to be set as root:root since command is
                    # executed on behalf of root user
                    "sh",
                    "-c",
                    'mkdir -p /etc/sudoers.d && echo "work ALL=(ALL:ALL) NOPASSWD:ALL" >'
                    " /etc/sudoers.d/01-bai-work",
                ],
                user="root",
            )
            shell_response = await exec.start(detach=True)
            if shell_response:
                raise ContainerCreationError(
                    container_id=cid,
                    message=f"sudoers provision failed: {shell_response.decode()}",
                )

        additional_network_names: set[str] = set()
        for dev_name, device_alloc in resource_spec.allocations.items():
            n = await self.computers[dev_name].instance.get_docker_networks(device_alloc)
            additional_network_names |= set(n)

        await self._attach_additional_networks(docker, container, additional_network_names)

    async def _attach_additional_networks(
        self,
        docker: Docker,
        container: DockerContainer,
        requested_networks: Iterable[str],
    ) -> None:
        """
        Connect the container to each requested network, skipping any that
        Docker has already attached (e.g. `bridge` auto-attached when
        `NetworkMode` is unset). `requested_networks` may contain network
        names or IDs per the `Resources.get_docker_networks` contract.
        """
        requested = set(requested_networks)
        if not requested:
            return
        container_info = await container.show()
        networks = {}
        if (network_settings := container_info.get("NetworkSettings")) is not None:
            if (networks_dict := network_settings.get("Networks")) is not None:
                networks = networks_dict
        already_attached = set(networks.keys()) | {
            n["NetworkID"] for n in networks.values() if n is not None and n.get("NetworkID")
        }
        for ref in requested - already_attached:
            network = await docker.networks.get(ref)
            try:
                await network.connect({"Container": container._id})
            except DockerError as e:
                # Defense against a race between container.show() and connect()
                # where Docker may attach the network in between.
                if e.status == HTTPStatus.FORBIDDEN and "already exists" in str(e.message):
                    continue
                raise

    @override
    async def start_container(
        self,
        kernel_obj: AbstractKernel,
        cmdargs: list[str],
        resource_opts: Mapping[str, Any] | None,
        preopen_ports: list[int],
        cluster_info: ClusterInfo,
    ) -> Mapping[str, Any]:
        loop = current_loop()
        resource_spec = kernel_obj.resource_spec
        service_ports = kernel_obj.service_ports
        environ = kernel_obj.environ
        image_labels = self.kernel_config["image"]["labels"]

        # PHASE 4: Run!
        container_bind_host = self.local_config.container.bind_host
        advertised_kernel_host = self.local_config.container.advertised_host
        if len(service_ports) + len(self.repl_ports) > len(self.port_pool):
            raise PortPoolExhaustedError(
                f"Container ports are not sufficiently available. "
                f"(remaining ports: {self.port_pool.remaining()})"
            )
        exposed_ports = [*self.repl_ports]
        host_ports = [self.port_pool.acquire() for _ in self.repl_ports]
        host_ips = []
        for sport in service_ports:
            exposed_ports.extend(sport["container_ports"])
            if (
                sport["name"] == "sshd"
                and self.cluster_ssh_port_mapping
                and (
                    ssh_host_port := self.cluster_ssh_port_mapping.get(
                        self.kernel_config["cluster_hostname"]
                    )
                )
            ):
                host_ports.append(ssh_host_port[1])
            else:
                hport = self.port_pool.acquire()
                host_ports.append(hport)
        protected_service_ports: set[int] = set()
        for sport in service_ports:
            if sport["name"] in self.protected_services:
                protected_service_ports.update(sport["container_ports"])
        for eport in exposed_ports:
            if eport in self.repl_ports or eport in protected_service_ports:  # always protected
                host_ips.append("127.0.0.1")
            else:
                host_ips.append(str(container_bind_host))
        if len(host_ips) != len(host_ports) or len(host_ports) != len(exposed_ports):
            raise InvalidArgumentError(
                f"Port list length mismatch: host_ips={len(host_ips)}, "
                f"host_ports={len(host_ports)}, exposed_ports={len(exposed_ports)}"
            )

        if (mode := cluster_info["network_config"].get("mode")) and mode != "bridge":
            try:
                plugin = self.network_plugin_ctx.plugins[mode]
            except KeyError as e:
                raise RuntimeError(f"Network plugin {mode} not loaded!") from e
            if ContainerNetworkCapability.GLOBAL in (await plugin.get_capabilities()):
                await plugin.prepare_port_forward(
                    kernel_obj,
                    str(container_bind_host),
                    [
                        (host_port, container_port)
                        for host_port, container_port in zip(host_ports, exposed_ports, strict=True)
                    ],
                )

        if self.image_ref.is_local:
            image = self.image_ref.short
        else:
            image = self.image_ref.canonical

        container_config: MutableMapping[str, Any] = {
            "Image": image,
            "Tty": True,
            "OpenStdin": True,
            "Privileged": False,
            "StopSignal": "SIGINT",
            "ExposedPorts": {f"{port}/tcp": {} for port in exposed_ports},
            "EntryPoint": ["/opt/kernel/entrypoint.sh"],
            "Cmd": cmdargs,
            "Env": [f"{k}={v}" for k, v in environ.items()],
            "WorkingDir": "/home/work",
            "Hostname": self.kernel_config["cluster_hostname"],
            "Labels": {
                LabelName.AGENT_ID: str(self.agent_id),
                LabelName.KERNEL_ID: str(self.kernel_id),
                LabelName.SESSION_ID: str(self.session_id),
                LabelName.OWNER_USER: self.ownership_data.owner_user_id_to_str,
                LabelName.OWNER_PROJECT: self.ownership_data.owner_project_id_to_str,
                LabelName.OWNER_AGENT: str(self.agent_id),
                LabelName.BLOCK_SERVICE_PORTS: (
                    "1" if self.internal_data.get("block_service_ports", False) else "0"
                ),
            },
            "HostConfig": {
                "Init": True,
                "PortBindings": {
                    f"{eport}/tcp": [{"HostPort": str(hport), "HostIp": hip}]
                    for eport, hport, hip in zip(exposed_ports, host_ports, host_ips, strict=True)
                },
                "PublishAllPorts": False,  # we manage port mapping manually!
                "CapAdd": [
                    "IPC_LOCK",  # for hugepages and RDMA
                    "SYS_NICE",  # for NFS based GPUDirect Storage
                ],
                "Ulimits": [
                    get_safe_ulimit("nofile", 1048576, 1048576),
                    get_safe_ulimit("memlock", -1, -1),
                ],
                "LogConfig": _build_log_config(self.local_config).model_dump(
                    mode="json", by_alias=True
                ),
            },
        }

        await self._apply_seccomp_profile(container_config)

        # merge all container configs generated during prior preparation steps
        for c in self.container_configs:
            update_nested_dict(container_config, c)
        if self.local_config.container.sandbox_type == ContainerSandboxType.JAIL:
            update_nested_dict(
                container_config,
                {
                    "HostConfig": {
                        "SecurityOpt": ["seccomp=unconfined", "apparmor=unconfined"],
                        "CapAdd": ["SYS_PTRACE"],
                    },
                },
            )

        if resource_opts and resource_opts.get("shmem"):
            shmem = int(resource_opts.get("shmem", "0"))
            # Only set ShmSize limit for tmpfs (/dev/shm).
            # Do NOT subtract shmem from Memory/MemorySwap because:
            # - shm (tmpfs) and app memory share the Memory cgroup space
            # - Pre-deducting would unnecessarily reduce available memory
            self.computer_docker_args["HostConfig"]["ShmSize"] = shmem

        service_ports_label: list[str] = []
        service_ports_label += image_labels.get(LabelName.SERVICE_PORTS, "").split(",")
        service_ports_label += [f"{port_no}:preopen:{port_no}" for port_no in preopen_ports]

        container_config["Labels"][LabelName.SERVICE_PORTS] = ",".join([
            label for label in service_ports_label if label
        ])
        update_nested_dict(container_config, self.computer_docker_args)
        kernel_name = f"kernel.{self.image_ref.name.split('/')[-1]}.{self.kernel_id}"

        # optional local override of docker config
        extra_container_opts_name = "agent-docker-container-opts.json"
        for extra_container_opts_file in [
            Path("/etc/backend.ai") / extra_container_opts_name,
            Path.home() / ".config" / "backend.ai" / extra_container_opts_name,
            Path.cwd() / extra_container_opts_name,
        ]:
            if extra_container_opts_file.is_file():
                try:
                    extra_container_opts = load_json(extra_container_opts_file.read_bytes())
                    update_nested_dict(container_config, extra_container_opts)
                except OSError:
                    pass

        # The final container config is settled down here.
        if self.local_config.debug.log_kernel_config:
            log.debug("full container config: {!r}", pretty(container_config))

        async def _rollback_container_creation(container_exists: bool = False) -> None:
            """Give back what this create took -- but only while nothing holds it.

            ``container_exists`` decides whether there is anything to give back at all, and the
            answer is all three or none. A container that exists may be running: it holds the
            devices named in its own resource spec, it holds the host ports Docker published for
            it, and its scratch is its filesystem. Reclaiming any of them while it is up hands a
            live container's GPU or port to the next create -- and `docker start` can be cancelled
            AFTER the daemon has acted on it, so "the start failed" does not mean "nothing is
            running".

            Where a container exists, all of it belongs to the kernel's teardown, which stops the
            container first and then gives the ports back and rebuilds the allocation maps from
            what is actually left. That teardown is queued by
            `AbstractAgent._unwind_failed_create`.
            """
            if container_exists:
                return
            await _clean_scratch(
                loop,
                self.local_config.container.scratch_type,
                self.local_config.container.scratch_root,
                self.kernel_id,
            )
            self.port_pool.release_many(host_ports)
            async with self.resource_lock:
                for dev_name, device_alloc in resource_spec.allocations.items():
                    self.computers[dev_name].alloc_map.free(device_alloc)

        if self._session_networked:
            # BEP-1078: the container must exist, hold a netns and a stable PID, and NOT have run
            # its command yet, so a vxlan/veth can be moved in first. Docker has no such split --
            # `docker create` reports PID 0 and no netns -- so the entrypoint becomes a wrapper
            # that parks at a FIFO after its namespaces exist. Releasing it execs the real command
            # in place, which is what keeps the PID the attach used.
            stage_gate(self._gate_dir)
            apply_gate(container_config, self._gate_dir)

        # We are all set! Create and start the container.
        async with closing_async(Docker()) as docker:
            container: DockerContainer | None = None
            try:
                container = await docker.containers.create(
                    config=container_config, name=kernel_name
                )
                if container is None:
                    raise ContainerCreationError(
                        container_id="",
                        message="Docker API returned None when creating container",
                    )
                cid = container._id
                # Recorded on the kernel object the moment the container exists, and before
                # anything else can fail. Everything from here to the end of this method can
                # raise, and the agent's handler destroys a failed kernel by the id it finds
                # here: set later, as it was, a VXLAN attach that failed left the handler with
                # nothing to destroy, `destroy_kernel` did nothing, and the container went on
                # running with its kernel already gone from the registry.
                kernel_obj.set_container_id(ContainerId(cid))
                async with AsyncFileWriter(
                    target_filename=self.config_dir / "resource.txt",
                    access_mode="a",
                ) as writer:
                    await writer.write(f"CID={cid}\n")

            except asyncio.CancelledError as e:
                if container is not None:
                    raise ContainerCreationError(
                        container_id=ContainerId(container.id),
                        message="Container creation was cancelled",
                    ) from e
                raise
            except Exception as e:
                # Oops, we have to restore the allocated resources!
                await _rollback_container_creation(container_exists=container is not None)
                if container is not None:
                    raise ContainerCreationError(
                        container_id=ContainerId(container.id),
                        message=f"Unexpected error during container creation: {e!r}",
                    ) from e
                raise

            try:
                await container.start()
            except asyncio.CancelledError as e:
                # The container exists whatever this says: `docker start` can be cancelled after
                # the daemon has acted on it, and a container that is up owns its own scratch.
                await _rollback_container_creation(container_exists=True)
                raise ContainerCreationError(
                    container_id=cid,
                    message="Container start was cancelled",
                ) from e
            except Exception as e:
                await _rollback_container_creation(container_exists=True)
                raise ContainerCreationError(
                    container_id=cid,
                    message=f"Unexpected error during container start: {e!r}",
                ) from e

            await self._provision_or_name_the_container(
                docker, container, cid, cluster_info, resource_spec
            )

            container_network_info: ContainerNetworkInfo | None = None
            if (mode := cluster_info["network_config"].get("mode")) and mode != "bridge":
                try:
                    plugin = self.network_plugin_ctx.plugins[mode]
                except KeyError as e:
                    raise RuntimeError(f"Network plugin {mode} not loaded!") from e
                if ContainerNetworkCapability.GLOBAL in (await plugin.get_capabilities()):
                    container_network_info = await plugin.expose_ports(
                        kernel_obj,
                        str(container_bind_host),
                        [
                            (host_port, container_port)
                            for host_port, container_port in zip(
                                host_ports, exposed_ports, strict=True
                            )
                        ],
                    )

            created_host_ports: tuple[int, ...]
            repl_in_port = 0
            repl_out_port = 0
            if self._session_networked:
                # Docker publishes nothing for a `NetworkMode: none` container, so the pairing the
                # agent allocated is the pairing — there is no daemon-side map to read back. The
                # ports are made reachable by DNAT at the address the attach assigned, the same way
                # the containerd backend does it.
                kernel_host = str(advertised_kernel_host or container_bind_host)
                await self._publish_session_ports(cid, host_ports, exposed_ports)
                session_ports = dict(zip(exposed_ports, host_ports, strict=True))
                # The container's own ports, not the host pairing: the repl is dialled at the
                # container's LOCAL address (see repl_host below and DockerKernel), where the
                # runner listens on 2000/2001. Handing over a host port here sends the agent's
                # ZMQ at a port nothing published -- the runner is up and answering, and the
                # creation still times out waiting for it.
                repl_in_port, repl_out_port = _REPL_IN_PORT, _REPL_OUT_PORT
                stdin_port = 0  # legacy
                stdout_port = 0  # legacy
                for sport in service_ports:
                    sport["host_ports"] = tuple(
                        session_ports[cport] for cport in sport["container_ports"]
                    )
                created_host_ports = tuple(host_ports)
            elif container_network_info:
                kernel_host = container_network_info.container_host
                port_map = container_network_info.services
                if "replin" not in port_map or "replout" not in port_map:
                    raise InvalidArgumentError("replin and replout ports are required in port_map")

                repl_in_port = port_map["replin"][2000]
                repl_out_port = port_map["replout"][2001]
                stdin_port = 0  # left for legacy
                stdout_port = 0  # left for legacy

                for sport in service_ports:
                    created_host_ports = tuple(
                        port_map[sport["name"]][cport] for cport in sport["container_ports"]
                    )
                    sport["host_ports"] = created_host_ports
            else:
                kernel_host = advertised_kernel_host or container_bind_host
                ctnr_host_port_map: MutableMapping[int, int] = {}
                stdin_port = 0
                stdout_port = 0
                for idx, port in enumerate(exposed_ports):
                    ports: list[PortInfo] | None = await container.port(port)
                    if not ports:
                        raise ContainerCreationError(
                            container_id=cid,
                            message=f"Container port {port} not found in port mapping",
                        )
                    host_port = int(ports[0]["HostPort"])
                    if host_port != host_ports[idx]:
                        await _rollback_container_creation(container_exists=True)
                        raise ContainerCreationError(
                            container_id=cid,
                            message=f"Port mapping mismatch. {host_port = }, {host_ports[idx] = }",
                        )
                    if port == 2000:  # intrinsic
                        repl_in_port = host_port
                    elif port == 2001:  # intrinsic
                        repl_out_port = host_port
                    elif port == 2002:  # legacy
                        stdin_port = host_port
                    elif port == 2003:  # legacy
                        stdout_port = host_port
                    else:
                        ctnr_host_port_map[port] = host_port
                for sport in service_ports:
                    created_host_ports = tuple(
                        ctnr_host_port_map[cport] for cport in sport["container_ports"]
                    )
                    sport["host_ports"] = created_host_ports

        if repl_in_port == 0:
            raise InvalidArgumentError("repl_in_port should have been assigned")
        if repl_out_port == 0:
            raise InvalidArgumentError("repl_out_port should have been assigned")
        return {
            "container_id": container._id,
            "kernel_host": kernel_host,
            # Under BEP-1078 the repl is not published: the agent is on this node and dials the
            # container's own address. None everywhere else, where Docker's loopback publishing is
            # what the kernel falls back to.
            "repl_host": self._container_ip if self._session_networked else None,
            "repl_in_port": repl_in_port,
            "repl_out_port": repl_out_port,
            "stdin_port": stdin_port,  # legacy
            "stdout_port": stdout_port,  # legacy
            "host_ports": host_ports,
            "domain_socket_proxies": self.domain_socket_proxies,
            "block_service_ports": self.internal_data.get("block_service_ports", False),
        }


class DockerAgent(AbstractAgent[DockerKernel, DockerKernelCreationContext]):
    docker: Docker
    docker_info: Mapping[str, Any]
    monitor_docker_task: asyncio.Task[Any]
    agent_sockpath: Path
    agent_sock_task: asyncio.Task[Any]
    docker_ptask_group: aiotools.PersistentTaskGroup
    gwbridge_subnet: str | None
    checked_invalid_images: set[str]
    _seccomp_profile_as_path: bool
    _cgroup_path_cache: LRUCache[ContainerId, dict[CgroupController, Path]]
    #: BEP-1078. The session half only — Docker keeps its own container lifecycle, so this object
    #: has a locator and no runtime and refuses lifecycle calls by name.
    _session_network: SessionNetwork
    #: The address peers program into their FDB. None means this node cannot anchor a tunnel, and
    #: ensure_session refuses a vxlan session outright rather than publishing an unreachable VTEP.
    _vtep_ip: str | None
    #: The raw configured address the VTEP was validated from, kept for the startup diagnostic.
    _host_ip: str
    #: Refreshes the published capabilities, so readiness does not go stale.
    _network_identity_task: asyncio.Task[None] | None

    network_plugin_ctx: NetworkPluginContext

    def __init__(
        self,
        etcd: AgentEtcdClientView,
        local_config: AgentUnifiedConfig,
        *,
        stats_monitor: StatsPluginContext,
        error_monitor: ErrorPluginContext,
        skip_initial_scan: bool = False,
        agent_public_key: PublicKey | None,
        kernel_registry: KernelRegistry,
        computers: Mapping[DeviceName, ComputerContext],
        slots: Mapping[SlotName, Decimal],
        agent_class: AgentClass,
    ) -> None:
        super().__init__(
            etcd,
            local_config,
            stats_monitor=stats_monitor,
            error_monitor=error_monitor,
            skip_initial_scan=skip_initial_scan,
            agent_public_key=agent_public_key,
            kernel_registry=kernel_registry,
            computers=computers,
            slots=slots,
            agent_class=agent_class,
        )
        self.checked_invalid_images = set()
        self._seccomp_profile_as_path = False
        self._cgroup_path_cache = LRUCache(maxsize=_CGROUP_PATH_CACHE_SIZE)
        pickle_loader_writer_creator = PickleBasedLoaderWriterCreator.create(
            PickleBasedKernelRegistryCreatorArgs(
                scratch_root=local_config.container.scratch_root,
                ipc_base_path=local_config.agent.ipc_base_path,
                var_base_path=local_config.agent.var_base_path,
                agent_class=self.agent_class,
                agent_id=self.id,
                local_instance_id=self.local_instance_id,
            ),
        )
        pickle_loader = pickle_loader_writer_creator.create_loader()
        pickle_writer = pickle_loader_writer_creator.create_writer()
        container_loader_writer_creator = ContainerBasedLoaderWriterCreator(
            ContainerBasedKernelRegistryCreatorArgs(
                scratch_root=local_config.container.scratch_root,
                agent=self,
            )
        )
        container_loader = container_loader_writer_creator.create_loader()
        container_writer = container_loader_writer_creator.create_writer()
        self._kernel_recovery = DockerKernelRegistryRecovery(
            loader=container_loader,
            writers=[pickle_writer, container_writer],
        )
        self._kernel_recovery_adapter = KernelRecoveryDataAdapter(
            pickle_loader,
            [KernelRecoveryDataAdapterTarget(container_loader, container_writer)],
        )

    @override
    async def __ainit__(self) -> None:
        async with closing_async(Docker()) as docker:
            docker_host = ""
            match docker.connector:
                case aiohttp.TCPConnector():
                    if docker.docker_host is None:
                        raise InvalidArgumentError("docker_host is not set for TCP connector")
                    docker_host = docker.docker_host
                case aiohttp.NamedPipeConnector() | aiohttp.UnixConnector() as connector:
                    docker_host = connector.path
                case _:
                    docker_host = "(unknown)"
            log.info("accessing the local Docker daemon via {}", docker_host)
            docker_version = await docker.version()
            engine_components = [
                name
                for component in docker_version.get("Components") or []
                if (name := component.get("Name")) is not None
            ]
            log.info(
                "running with Docker {0} with API {1} (components: {2})",
                docker_version["Version"],
                docker_version["ApiVersion"],
                ", ".join(engine_components),
            )
            self._seccomp_profile_as_path = any(
                component in _SECCOMP_PATH_ENGINES for component in engine_components
            )
            kernel_version = docker_version["KernelVersion"]
            if "linuxkit" in kernel_version:
                self.local_config.agent.docker_mode = "linuxkit"
            else:
                self.local_config.agent.docker_mode = "native"
            docker_info = await docker.system.info()
            docker_info = dict(docker_info)
            # Assume cgroup v1 if CgroupVersion key is absent
            if "CgroupVersion" not in docker_info:
                docker_info["CgroupVersion"] = "1"
            log.info(
                "Cgroup Driver: {0}, Cgroup Version: {1}",
                docker_info["CgroupDriver"],
                docker_info["CgroupVersion"],
            )
            self.docker_info = docker_info
        # BEP-1078. host_ip keeps the overlay on the L2 the agents advertise on rather than a
        # hard-coded eth0; the VTEP is validated once here because it is what peers program into
        # their FDB, and an address this node cannot be reached at must never reach a session's
        # membership record.
        container_cfg = self.local_config.container
        host_ip = str(container_cfg.advertised_host or container_cfg.bind_host)
        self._host_ip = host_ip
        self._network_identity_task = None
        self._vtep_ip = usable_vtep(host_ip)
        # The interface the data plane is BUILT on, kept because it is half of what this node
        # serves with. The vxlan device is created on this uplink for the life of the process, so
        # an address that stays valid while moving to another NIC -- a failover, a re-cabling --
        # leaves the node probing one interface and building on another.
        self._serving_uplink = uplink_for_ip(self._vtep_ip or host_ip)
        self._session_network = build_docker_session_network(
            self.etcd,
            agent_id=str(self.id),
            host_ip=host_ip,
            uplink=self._serving_uplink,
            privnet_socket=self.local_config.agent.network_privnet_socket,
            local_subnet_layout=container_cfg.local_subnet_layout(),
            agent_state_dir=self.local_config.agent.var_base_path,
            vtep_ip=self._vtep_ip,
            configured_dns=tuple(container_cfg.dns or ()),
        )
        await self._session_network.open()
        # Rebuild what a restart emptied, BEFORE anything can ask the session network a question.
        # Every field it holds is process memory, while the resources they name -- bridges, veths,
        # IPAM leases, MASQ rules, etcd members -- outlive the process. Skipping it leaves a
        # restarted agent resuming its kernels with no way to detach them, no way to tear their
        # session down (the tracker is empty, so `untrack` finds nothing and teardown never runs),
        # no reaction to peers joining or leaving, and no re-assertion of the firewall or XFRM
        # drift that accumulated while it was down.
        try:
            await self._session_network.recover()
        except Exception as e:
            self._session_network.mark_recovery_failed(str(e))
            # Not fatal to startup: an agent that cannot recover its network state can still serve
            # new sessions, and refusing to start would take the node out over sessions that are
            # already running. Loud, because everything above stays true until it is fixed.
            log.exception(
                "could not recover the session network state; restarted sessions on"
                " this node may not tear down or re-converge until they are terminated"
            )
        await self._kernel_recovery_adapter.adapt_recovery_data()
        await super().__ainit__()
        # The advert is NOT published here. Everything below can still fail, and a failure here
        # aborts the runtime before `shutdown` is ever called -- so an advert written at this
        # point would stand for the whole freshness window over an agent that never started. It
        # goes at the end, as the last thing this does, and anything that fails on the way there
        # takes it away again.
        try:
            async with Docker() as docker:
                gwbridge = await docker.networks.get("docker_gwbridge")
                gwbridge_info = await gwbridge.show()
                self.gwbridge_subnet = gwbridge_info["IPAM"]["Config"][0]["Subnet"]
        except (DockerError, KeyError, IndexError):
            self.gwbridge_subnet = None
        ipc_base_path = self.local_config.agent.ipc_base_path
        (ipc_base_path / "container").mkdir(parents=True, exist_ok=True)
        self.agent_sockpath = ipc_base_path / "container" / f"agent.{self.id}.sock"
        # Workaround for Docker Desktop for Mac's UNIX socket mount failure with virtiofs
        if sys.platform != "darwin":
            socket_relay_name = f"backendai-socket-relay.{self.id}"
            socket_relay_container = PersistentServiceContainer(
                "backendai-socket-relay:latest",
                {
                    "Cmd": [
                        f"UNIX-LISTEN:/ipc/{self.agent_sockpath.name},unlink-early,fork,mode=777",
                        f"TCP-CONNECT:127.0.0.1:{self.local_config.agent.agent_sock_port}",
                    ],
                    "HostConfig": {
                        "Mounts": [
                            {
                                "Type": "bind",
                                "Source": str(ipc_base_path / "container"),
                                "Target": "/ipc",
                            },
                        ],
                        "NetworkMode": "host",
                    },
                },
                name=socket_relay_name,
            )
            await socket_relay_container.ensure_running_latest()
        self.agent_sock_task = asyncio.create_task(self.handle_agent_socket())
        self.monitor_docker_task = asyncio.create_task(self.monitor_docker_events())
        self.docker_ptask_group = aiotools.PersistentTaskGroup()

        # For legacy accelerator plugins
        self.docker = Docker()

        self.network_plugin_ctx = NetworkPluginContext(
            self.etcd, self.local_config.model_dump(by_alias=True)
        )
        await self.network_plugin_ctx.init(
            context=self,
            allowlist=self.local_config.agent.allow_network_plugins,
            blocklist=self.local_config.agent.block_network_plugins,
        )
        # The advert is NOT published here either. It admits the node to a cluster-network
        # session, and the node cannot serve one until its RPC transport is up -- which happens
        # after every `__ainit__` has returned. `start_serving` is where it goes.

    async def _withdraw_network_identity(self) -> None:
        """Stop advertising this node, and make sure nothing puts the advert back.

        Three steps, in this order, because two is not enough. Deleting first shuts the door at
        once -- while the advert stands a manager may still place work here, and the freshness
        window would let it for ten minutes after this process is gone. But a refresh already
        running can finish its publish AFTER that delete and put a fresh advert back over a node
        that is shutting down. So the publisher is stopped and waited for, and only then is the
        advert taken away for good.
        """
        for step in ("first", "final"):
            try:
                await withdraw_caps(self.etcd, str(self.id), self._boot_id)
            except Exception:
                log.exception("could not withdraw this agent's network capabilities ({})", step)
            if step == "first" and self._network_identity_task is not None:
                self._network_identity_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._network_identity_task
                self._network_identity_task = None

    @override
    async def start_serving(self) -> None:
        """Announce the node, and only then advertise what it can serve.

        The advert is last of all: it is what admits this node to a cluster-network session, and
        until the RPC transport is up there is nothing here to take one. Published from
        `__ainit__` it stood over a process that could not yet serve, and a previous run's entry
        in the manager's own table can keep that node looking ALIVE for its own timeout.
        """
        await super().start_serving()
        await self._publish_network_identity()
        self._network_identity_task = asyncio.create_task(self._publish_network_identity_forever())

    @override
    async def stop_serving(self) -> None:
        await self._withdraw_network_identity()
        await super().stop_serving()

    async def _publish_network_identity_forever(self) -> None:
        """Keep this node's advertised capabilities honest while it runs.

        Published once at startup, they answer a question that does not stay answered: the
        privileged helper can die an hour later, and the node goes on advertising `vxlan` while
        nothing on it can build a device. The VTEP does not change, so this is about readiness.
        """
        while True:
            await asyncio.sleep(_NETWORK_IDENTITY_REFRESH_SEC)
            try:
                await self._publish_network_identity()
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("could not refresh this agent's network capabilities")

    async def _publish_network_identity(self) -> None:
        """Advertise this node's overlay identity: its capabilities and its VTEP (BEP-1078).

        The VTEP lets the manager pre-seed session membership, which is what removes the
        peer-publish race for a multi-node overlay. See `network/caps.py`.
        """
        # What this node advertises is what it can actually SERVE, and that is fixed for the life
        # of the process: the session network and the vxlan backend hold the endpoint they were
        # built with, and every session already up was built on it. So the host is asked afresh
        # each time -- an address can go while this process runs, a link drops, DHCP hands out
        # another -- but the answer only ever decides whether to keep advertising, never what to
        # advertise. Republishing a recomputed address would have said "ready" on a node whose
        # serving path refuses the session, and refreshing the cached one kept the timestamp
        # moving on an advert that had stopped being true. Both are the same mistake: the advert
        # has to be about the serving state, not about the host.
        serving = self._session_network.serving_vtep
        live = usable_vtep(self._host_ip)
        # BOTH halves of the serving identity. The address alone is not it: the same address can
        # move to another NIC and stay perfectly usable, while the vxlan device goes on being
        # created on the interface this process started with -- so the node would probe the new
        # NIC, advertise it healthy, and build the tunnel on the old one. That fails outright if
        # the old NIC is gone and blackholes silently if it is merely no longer the path.
        uplink = uplink_for_ip(live) if live is not None else None
        intact = live == serving and uplink == self._serving_uplink
        self._vtep_ip = serving if intact else None
        if not intact:
            log.warning(
                "this node's overlay identity has moved (serving {!r} on {!r}, host now holds"
                " {!r} on {!r}); withdrawing from multi-node overlay work until this agent is"
                " restarted",
                serving,
                self._serving_uplink,
                live,
                uplink,
            )
        # The VTEP key first, then the capabilities. The capability record is what ADMITS this
        # node to a session, so it is written last of everything this refresh does: anything that
        # can still fail after it has landed can leave a fresh advert standing over an agent whose
        # start never finished, and the manager has no way to tell.
        if self._vtep_ip is not None:
            await publish_vtep(self.etcd, str(self.id), self._vtep_ip, self._boot_id)
        else:
            # Retract, not merely skip: the key is durable, so an address published on an earlier
            # boot would otherwise keep being pre-seeded into peers' FDBs long after this node
            # stopped holding it -- by which time it may belong to a different host entirely.
            await withdraw_vtep(self.etcd, str(self.id), self._boot_id)
            log.warning(
                "no usable VTEP: container.advertised-host/bind-host ({!r}) is not a routable"
                " unicast IPv4 address held by an interface of this host that is up. Single-node"
                " sessions work; a multi-node overlay (vxlan) session scheduled here will be"
                " refused until it is set.",
                self._host_ip,
            )
        # A diagnostic signal for operators (e.g. VXLAN tunnel offload); best-effort, because a
        # failure to describe the uplink must not stop the agent from serving kernels.
        try:
            caps = await probe_caps(
                # The interface sessions are served on, not the one the address is on now: a probe
                # of the wrong NIC describes a path this node will not use.
                self._serving_uplink,
                privnet_socket=self.local_config.agent.network_privnet_socket,
                # Retried here rather than on a loop of its own: this already runs on a timer,
                # and the answer it publishes is exactly what the retry changes.
                recovery_problems=await self._session_network.retry_recovery_fail_close(),
            )
            await publish_caps(
                self.etcd,
                str(self.id),
                caps,
                backend=str(self.local_config.agent.backend),
                vtep_ip=self._vtep_ip,
                boot_id=self._boot_id,
            )
            for problem in caps.readiness:
                # Once at startup, where an operator can act on it -- rather than at the first
                # session scheduled here, which fails on one node with the reason buried in a
                # create-time traceback.
                log.warning("overlay readiness: {}", problem)
        except Exception:
            # An advert this node could not renew must not stand: it is what a manager reads to
            # place work here, and leaving the last one behind is how a node that has stopped
            # being able to say anything keeps being chosen.
            # Withdrawn, not raised. A node that cannot describe its uplink can still serve
            # single-node sessions, and refusing to start would take it out entirely over a
            # diagnostic. With no advert standing it is simply not admitted to a cluster-network
            # session, which is the answer that matters.
            log.exception("could not publish this agent's network capabilities; withdrawing")
            await withdraw_caps(self.etcd, str(self.id), self._boot_id)

    @override
    async def shutdown(self, stop_signal: signal.Signals) -> None:
        await self._withdraw_network_identity()
        # Stop handling agent sock.
        if self.agent_sock_task is not None:
            self.agent_sock_task.cancel()
            await self.agent_sock_task
        if self.docker_ptask_group is not None:
            await self.docker_ptask_group.shutdown()

        try:
            await super().shutdown(stop_signal)
        finally:
            # Stop docker event monitoring.
            if self.monitor_docker_task is not None:
                self.monitor_docker_task.cancel()
                await self.monitor_docker_task

        if self.docker is not None:
            await self.docker.close()
        await self._session_network.close()

    @override
    async def _load_kernel_registry_from_recovery(self) -> MutableMapping[KernelId, AbstractKernel]:
        return await self._kernel_recovery.load_kernel_registry()

    @override
    async def _write_kernel_registry_to_recovery(
        self,
        kernel_registry: MutableMapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
    ) -> None:
        await self._kernel_recovery.save_kernel_registry(kernel_registry, metadata)

    @override
    async def get_cgroup_path(
        self, controller: CgroupController, container_id: ContainerId
    ) -> Path:
        cached_paths = self._cgroup_path_cache.get(container_id)
        if cached_paths is not None and (cached_path := cached_paths.get(controller)) is not None:
            return cached_path
        # The PID is used immediately and never cached: it changes when the container
        # restarts, while the resolved cgroup path does not.
        pid = await get_container_main_pid(container_id)
        version = self.docker_info["CgroupVersion"]
        resolved = {
            each_controller: get_cgroup_path_of_pid(version, each_controller, pid)
            for each_controller in {*_TRACKED_CGROUP_CONTROLLERS, controller}
        }
        if cached_paths is None:
            self._cgroup_path_cache[container_id] = resolved
        else:
            cached_paths.update(resolved)
        return resolved[controller]

    def _invalidate_cgroup_path_cache(self, container_id: ContainerId) -> None:
        self._cgroup_path_cache.pop(container_id, None)

    @override
    def get_cgroup_version(self) -> str:
        return cast(str, self.docker_info["CgroupVersion"])

    @override
    async def extract_image_command(self, image: str) -> list[str] | None:
        async with closing_async(Docker()) as docker:
            result = await docker.images.get(image)
            command = result["Config"].get("Cmd")
            if command is None:
                return None
            if isinstance(command, str):
                return [command]

            if isinstance(command, list):
                return cast(list[str], command)
            return None

    @override
    def port_publisher(self) -> PortPublisher:
        """This backend does publish host ports, so its rules are the reclaim's to collect."""
        return _port_publisher(self.local_config, self._session_network)

    @override
    async def enumerate_containers(
        self,
        status_filter: frozenset[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> Sequence[tuple[KernelId, Container]]:
        result = []
        fetch_tasks = []
        async with closing_async(Docker()) as docker:
            for container in await docker.containers.list():

                async def _fetch_container_info(container: DockerContainer) -> None:
                    kernel_id_str: str = "(unknown)"
                    try:
                        kernel_id = await get_kernel_id_from_container(container)
                        if kernel_id is None:
                            return
                        kernel_id_str = str(kernel_id)
                        if container["State"]["Status"] in status_filter:
                            owner_id = AgentId(
                                container["Config"]["Labels"].get(LabelName.OWNER_AGENT, "")
                            )
                            if self.id == owner_id:
                                await container.show()
                                result.append(
                                    (
                                        kernel_id,
                                        container_from_docker_container(container),
                                    ),
                                )
                    except DockerError as e:
                        if e.status == HTTPStatus.NOT_FOUND:
                            log.warning(e.message)
                            return
                        raise
                    except asyncio.CancelledError:
                        pass
                    except Exception:
                        log.exception(
                            "error while fetching container information (cid:{}, k:{})",
                            container._id,
                            kernel_id_str,
                        )

                fetch_tasks.append(_fetch_container_info(container))

            await asyncio.gather(*fetch_tasks, return_exceptions=True)
        return result

    @override
    async def resolve_image_distro(self, image: ImageConfig) -> str:
        image_labels = image["labels"]
        distro = image_labels.get(LabelName.BASE_DISTRO)
        if distro:
            return distro

        async with Docker() as docker:
            image_id = image["digest"].partition(":")[-1]
            # check if distro data is available on redis cache
            cached_distro = await self.valkey_stat_client.get_image_distro(image_id)
            if cached_distro:
                return cached_distro

            image_ref = ImageRef.from_image_config(image)
            container_config: dict[str, Any] = {
                "Image": image_ref.short if image_ref.is_local else image_ref.canonical,
                "Tty": True,
                "Privileged": False,
                "AttachStdin": False,
                "AttachStdout": True,
                "AttachStderr": True,
                "HostConfig": {
                    "Init": True,
                },
                "Entrypoint": [""],
                "Cmd": ["ldd", "--version"],
            }

            container = await docker.containers.create(container_config)
            await container.start()
            await container.wait()  # wait until container finishes to prevent race condition
            container_log = await container.log(stdout=True, stderr=True, follow=False)
            await container.stop()
            await container.delete()
            log.debug("response: {}", container_log)
            distro = _parse_distro_from_ldd_output(container_log)
            if distro is None:
                raise RuntimeError("Could not determine the C library variant.")
            await self.valkey_stat_client.set_image_distro(image_id, distro)
            return distro

    @override
    async def scan_images(self) -> ScanImagesResult:
        async with closing_async(Docker()) as docker:
            all_images = await docker.images.list()
            scanned_images: dict[ImageCanonical, InstalledImageInfo] = {}
            removed_images: dict[ImageCanonical, InstalledImageInfo] = {}
            for image in all_images:
                if image["RepoTags"] is None:
                    continue
                for repo_tag in image["RepoTags"]:
                    if repo_tag.endswith("<none>"):
                        continue
                    try:
                        ImageRef.parse_image_str(repo_tag, "*")
                    except (InvalidImageName, InvalidImageTag) as e:
                        if repo_tag not in self.checked_invalid_images:
                            log.warning(
                                "Image name {} does not conform to Backend.AI's image naming rule. This image will be ignored. Details: {}",
                                repo_tag,
                                e,
                            )
                            self.checked_invalid_images.add(repo_tag)
                        continue

                    img_detail = await docker.images.inspect(repo_tag)
                    labels = (img_detail.get("Config") or {}).get("Labels")
                    if labels is None:
                        continue

                    kernelspec = int(labels.get(LabelName.KERNEL_SPEC, "1"))
                    if MIN_KERNELSPEC <= kernelspec <= MAX_KERNELSPEC:
                        scanned_images[ImageCanonical(repo_tag)] = (
                            InstalledImageInfo.from_inspect_result(
                                canonical=ImageCanonical(repo_tag),
                                inspect_result=img_detail,
                            )
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

    async def handle_agent_socket(self) -> None:
        """
        A simple request-reply socket handler for in-container processes.
        For ease of implementation in low-level languages such as C,
        it uses a simple C-friendly ZeroMQ-based multipart messaging protocol.

        The agent listens on a local TCP port and there is a socat relay
        that proxies this port via a UNIX domain socket mounted inside
        actual containers.  The reason for this is to avoid inode changes
        upon agent restarts by keeping the relay container running persistently,
        so that the mounted UNIX socket files don't get to refere a dangling pointer
        when the agent is restarted.

        Request message:
            The first part is the requested action as string,
            The second part and later are arguments.

        Reply message:
            The first part is a 32-bit integer (int in C)
                (0: success)
                (-1: generic unhandled error)
                (-2: invalid action)
            The second part and later are arguments.

        All strings are UTF-8 encoded.
        """
        terminating = False
        zmq_ctx = zmq.asyncio.Context()
        while True:
            agent_sock = zmq_ctx.socket(zmq.REP)
            try:
                agent_sock.bind(f"tcp://127.0.0.1:{self.local_config.agent.agent_sock_port}")
                while True:
                    msg = await agent_sock.recv_multipart()
                    if not msg:
                        break
                    reply: list[bytes]
                    try:
                        if msg[0] == b"host-pid-to-container-pid":
                            container_id = msg[1].decode()
                            host_pid = struct.unpack("i", msg[2])[0]
                            container_pid = await host_pid_to_container_pid(
                                container_id,
                                host_pid,
                            )
                            reply = [
                                struct.pack("i", 0),
                                struct.pack("i", container_pid),
                            ]
                        elif msg[0] == b"container-pid-to-host-pid":
                            container_id = msg[1].decode()
                            container_pid = struct.unpack("i", msg[2])[0]
                            host_pid = await container_pid_to_host_pid(container_id, container_pid)
                            reply = [
                                struct.pack("i", 0),
                                struct.pack("i", host_pid),
                            ]
                        elif msg[0] == b"is-jail-enabled":
                            reply = [
                                struct.pack("i", 0),
                                struct.pack(
                                    "i",
                                    (
                                        1
                                        if self.local_config.container.sandbox_type
                                        == ContainerSandboxType.JAIL
                                        else 0
                                    ),
                                ),
                            ]
                        else:
                            reply = [struct.pack("i", -2), b"Invalid action"]
                    except asyncio.CancelledError:
                        terminating = True
                        raise
                    except Exception as e:
                        log.exception("handle_agent_socket(): internal error")
                        reply = [struct.pack("i", -1), f"Error: {e}".encode()]
                    await agent_sock.send_multipart(reply)
            except asyncio.CancelledError:
                terminating = True
                return
            except zmq.ZMQError:
                log.exception("handle_agent_socket(): zmq error")
                raise
            finally:
                agent_sock.close()
                if not terminating:
                    log.info("handle_agent_socket(): rebinding the socket")
                else:
                    zmq_ctx.destroy()

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
        auth_config = None
        reg_user = registry_conf.get("username")
        reg_passwd = registry_conf.get("password")
        log.info("pushing image {} to registry", image_ref.canonical)
        if reg_user and reg_passwd:
            encoded_creds = base64.b64encode(f"{reg_user}:{reg_passwd}".encode()).decode("ascii")
            auth_config = {
                "auth": encoded_creds,
            }

        async with closing_async(Docker()) as docker:
            kwargs: dict[str, Any] = {"auth": auth_config}
            if timeout_seconds != Sentinel.TOKEN:
                kwargs["timeout"] = timeout_seconds
            result = await docker.images.push(image_ref.canonical, **kwargs)

            if not result:
                raise RuntimeError("Failed to push image: unexpected return value from aiodocker")
            if error := result[-1].get("error"):
                raise RuntimeError(f"Failed to push image: {error}")

    @override
    async def pull_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout_seconds: float | None,
    ) -> None:
        auth_config = None
        reg_user = registry_conf.get("username")
        reg_passwd = registry_conf.get("password")
        if reg_user and reg_passwd:
            encoded_creds = base64.b64encode(f"{reg_user}:{reg_passwd}".encode()).decode("ascii")
            auth_config = {
                "auth": encoded_creds,
            }
        log.info("pulling image {} from registry", image_ref.canonical)
        async with closing_async(Docker()) as docker:
            result = await docker.images.pull(
                image_ref.canonical, auth=auth_config, timeout=timeout_seconds
            )

            if not result:
                raise RuntimeError("Failed to pull image: unexpected return value from aiodocker")
            if error := result[-1].get("error"):
                raise RuntimeError(f"Failed to pull image: {error}")

    async def _purge_image(self, docker: Docker, request: DockerPurgeImageReq) -> PurgeImageResp:
        try:
            await docker.images.delete(request.image, force=request.force, noprune=request.noprune)
            return PurgeImageResp.success(image=request.image)
        except Exception as e:
            log.error('Failed to purge image "{}": {}', request.image, e)
            return PurgeImageResp.failure(image=request.image, error=str(e))

    @override
    async def purge_images(self, request: PurgeImagesReq) -> PurgeImagesResp:
        async with closing_async(Docker()) as docker, TaskGroup() as tg:
            tasks = [
                tg.create_task(
                    self._purge_image(
                        docker,
                        DockerPurgeImageReq(
                            image=image, force=request.force, noprune=request.noprune
                        ),
                    )
                )
                for image in request.images
            ]

        results = []
        for task in tasks:
            deleted_info = task.result()
            results.append(deleted_info)

        return PurgeImagesResp(responses=results)

    @override
    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        try:
            async with closing_async(Docker()) as docker:
                image_info = await docker.images.inspect(image_ref.canonical)
                if auto_pull == AutoPullBehavior.DIGEST:
                    if image_info["Id"] != image_id:
                        return True
            log.info("found the local up-to-date image for {}", image_ref.canonical)
        except DockerError as e:
            if e.status == HTTPStatus.NOT_FOUND:
                if auto_pull == AutoPullBehavior.DIGEST or auto_pull == AutoPullBehavior.TAG:
                    return True
                if auto_pull == AutoPullBehavior.NONE:
                    raise ImageNotAvailable(image_ref) from e
            else:
                raise
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
    ) -> DockerKernelCreationContext:
        distro = await self.resolve_image_distro(kernel_config["image"])
        return DockerKernelCreationContext(
            ownership_data,
            self.event_producer,
            kernel_image,
            kernel_config,
            distro,
            self.local_config,
            self.computers,
            self.port_pool,
            self.agent_sockpath,
            self.resource_lock,
            self.network_plugin_ctx,
            self._session_network,
            restarting=restarting,
            cluster_ssh_port_mapping=cluster_ssh_port_mapping,
            seccomp_profile_as_path=self._seccomp_profile_as_path,
            gwbridge_subnet=self.gwbridge_subnet,
        )

    @override
    async def restart_kernel__load_config(
        self,
        kernel_id: KernelId,
        name: str,
    ) -> bytes:
        loop = current_loop()
        scratch_dir = (self.local_config.container.scratch_root / str(kernel_id)).resolve()
        config_dir = scratch_dir / "config"
        return await loop.run_in_executor(
            None,
            (config_dir / name).read_bytes,
        )

    @override
    async def restart_kernel__store_config(
        self,
        kernel_id: KernelId,
        name: str,
        data: bytes,
    ) -> None:
        loop = current_loop()
        scratch_dir = (self.local_config.container.scratch_root / str(kernel_id)).resolve()
        config_dir = scratch_dir / "config"

        def _write_bytes(data: bytes) -> None:
            (config_dir / name).write_bytes(data)

        return await loop.run_in_executor(
            None,
            _write_bytes,
            data,
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
            async with closing_async(Docker()) as docker:
                container = docker.containers.container(container_id)
                # The default timeout of the docker stop API is 10 seconds
                # to kill if container does not self-terminate.
                await container.stop()
        except DockerError as e:
            if e.status == HTTPStatus.CONFLICT and "is not running" in e.message:
                # already dead
                log.warning("destroy_kernel(k:{0}) already dead", kernel_id)
                await self.reconstruct_resource_usage()
            elif e.status == HTTPStatus.NOT_FOUND:
                # missing
                log.warning(
                    "destroy_kernel(k:{0}) kernel missing, forgetting this kernel", kernel_id
                )
                await self.reconstruct_resource_usage()
            else:
                log.exception("destroy_kernel(k:{0}) kill error", kernel_id)
                await self.error_monitor.capture_exception()

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
            # would tear the session network down under that live creation.
            raise
        except BaseException:
            # The kernel claimed this node's session network in apply_network, long before its
            # container existed. If it dies before that container is prepared it never enters the
            # kernel registry — and a destroy for a kernel the agent has never heard of returns
            # without queueing a clean, so clean_kernel (which normally releases the claim) never
            # runs. BaseException, not Exception: a creation cancelled at shutdown leaks the claim
            # just as surely. (A kernel that already has a container keeps its claim — that one is
            # released by its own removal.)
            await self._session_network.release_kernel(str(ownership_data.kernel_id))
            raise

    @override
    async def clean_kernel(
        self,
        kernel_id: KernelId,
        container_id: ContainerId | None,
        restarting: bool,
    ) -> None:
        loop = current_loop()
        if container_id is not None:
            self._invalidate_cgroup_path_cache(container_id)
        async with closing_async(Docker()) as docker:
            if container_id is not None:
                container = docker.containers.container(container_id)

                async def log_iter() -> AsyncGenerator[bytes, None]:
                    it = container.log(
                        stdout=True,
                        stderr=True,
                        follow=True,
                    )
                    async with aiotools.aclosing(it):  # type: ignore[type-var]
                        async for line in it:
                            yield line.encode("utf-8")

                try:
                    with timeout(60):
                        await self.collect_logs(kernel_id, container_id, log_iter())
                except DockerError as e:
                    if e.status == HTTPStatus.NOT_FOUND:
                        log.warning(
                            "container is already cleaned or missing (k:{}, cid:{})",
                            kernel_id,
                            container_id,
                        )
                    else:
                        raise
                except TimeoutError:
                    log.warning(
                        "timeout for collecting container logs (k:{}, cid:{})",
                        kernel_id,
                        container_id,
                    )
                except Exception as e:
                    log.warning(
                        "error while collecting container logs (k:{}, cid:{})",
                        kernel_id,
                        container_id,
                        exc_info=e,
                    )

            kernel_obj = self.kernel_registry.get(kernel_id)
            if kernel_obj is not None:
                for domain_socket_proxy in kernel_obj.get("domain_socket_proxies", []):
                    if domain_socket_proxy.proxy_server.is_serving():
                        domain_socket_proxy.proxy_server.close()
                        await domain_socket_proxy.proxy_server.wait_closed()
                        try:
                            domain_socket_proxy.host_proxy_path.unlink()
                        except OSError:
                            pass

            if container_id is not None:
                # BEP-1078: before the container goes. Removing it reclaims only the container-side
                # veth via netns teardown — the host veth, the host-local IPAM address and the
                # egress MASQ rule are ours to give back, and a kernel that skips this leaks them
                # until the agent restarts. A no-op for a container this node never attached.
                # The DNAT rules the publish installed are ours to give back too: nothing else
                # reclaims them, and a host port still pointing at a dead container's address is
                # handed straight to whichever kernel draws that port next.
                try:
                    await _port_publisher(
                        self.local_config, self._session_network
                    ).remove_container(str(container_id))
                except Exception:
                    log.warning(
                        "could not remove the published ports of container {}", container_id
                    )
                await self._session_network.detach_container(str(container_id))

            if not self.local_config.debug.skip_container_deletion and container_id is not None:
                container = docker.containers.container(container_id)
                try:
                    with timeout(90):
                        await container.delete(force=True, v=True)
                except DockerError as e:
                    if (
                        e.status == HTTPStatus.CONFLICT and "already in progress" in e.message
                    ) or e.status == HTTPStatus.NOT_FOUND:
                        # The container is gone, or on its way out under another deletion. That is
                        # what this call wanted; it is not a reason to abandon the rest of the
                        # clean. Returning here skipped `_clean_scratch` below, so every kernel
                        # whose container died with its agent -- the whole of a SIGKILL restart --
                        # kept its scratch directory for good. Measured: two scratch dirs left
                        # behind per ungraceful restart, never collected by anything afterwards.
                        # Nothing below depends on the delete having happened.
                        log.debug(
                            "container already gone while cleaning (k:{}, c:{}); continuing with"
                            " the scratch",
                            kernel_id,
                            container_id,
                        )
                    else:
                        log.exception(
                            "unexpected docker error while deleting container (k:{}, c:{})",
                            kernel_id,
                            container_id,
                        )
                except TimeoutError:
                    log.warning("container deletion timeout (k:{}, c:{})", kernel_id, container_id)

            if not restarting:
                await _clean_scratch(
                    loop,
                    self.local_config.container.scratch_type,
                    self.local_config.container.scratch_root,
                    kernel_id,
                )
                if kernel_obj:
                    kernel = cast(DockerKernel, kernel_obj)
                    if kernel.network_driver != "bridge":
                        try:
                            plugin = self.network_plugin_ctx.plugins[kernel.network_driver]
                        except KeyError as e:
                            raise RuntimeError(
                                f"Network plugin {kernel.network_driver} not loaded!"
                            ) from e
                        await plugin.leave_network(kernel)

    @override
    async def create_local_network(self, network_name: str) -> None:
        async with closing_async(Docker()) as docker:
            try:
                await docker.networks.get(network_name)
            except DockerError as e:
                if e.status == HTTPStatus.NOT_FOUND:
                    await docker.networks.create({
                        "Name": network_name,
                        "Driver": "bridge",
                        "Labels": {
                            "ai.backend.cluster-network": "1",
                        },
                    })
                else:
                    raise

    @override
    async def destroy_local_network(self, network_name: str) -> None:
        async with closing_async(Docker()) as docker:
            try:
                network = await docker.networks.get(network_name)
                await network.delete()
            except DockerError as e:
                if e.status == HTTPStatus.NOT_FOUND:
                    # skip silently if already removed/missing
                    pass
                else:
                    raise

    @preserve_termination_log  # type: ignore[misc]
    async def monitor_docker_events(self) -> None:
        async def handle_action_start(
            session_id: SessionId, kernel_id: KernelId, evdata: Mapping[str, Any]
        ) -> None:
            await self.inject_container_lifecycle_event(
                kernel_id,
                session_id,
                LifecycleEvent.START,
                KernelLifecycleEventReason.NEW_CONTAINER_STARTED,
                container_id=ContainerId(evdata["Actor"]["ID"]),
            )

        async def handle_action_die(
            session_id: SessionId, kernel_id: KernelId, evdata: Mapping[str, Any]
        ) -> None:
            # When containers die, we immediately clean up them.
            reason = None
            kernel_obj = self.kernel_registry.get(kernel_id)
            if kernel_obj is not None:
                reason = kernel_obj.termination_reason
            try:
                exit_code = evdata["Actor"]["Attributes"]["exitCode"]
            except KeyError:
                exit_code = 255
            await self.inject_container_lifecycle_event(
                kernel_id,
                session_id,
                LifecycleEvent.CLEAN,
                reason or KernelLifecycleEventReason.SELF_TERMINATED,
                container_id=ContainerId(evdata["Actor"]["ID"]),
                exit_code=exit_code,
            )

        async def handle_action_oom(
            _session_id: SessionId, kernel_id: KernelId, _evdata: Mapping[str, Any]
        ) -> None:
            kernel_obj = self.kernel_registry.get(kernel_id, None)
            if kernel_obj is None:
                return
            await kernel_obj.notify_event(
                AgentEventData(
                    type="oom",
                    data={},
                )
            )

        while True:
            async with closing_async(Docker()) as docker:
                subscriber = docker.events.subscribe(create_task=True)  # type: ignore[no-untyped-call]
                try:
                    while True:
                        try:
                            # ref: https://docs.docker.com/engine/api/v1.40/#operation/SystemEvents
                            evdata = await subscriber.get()
                            if evdata is None:
                                # Break out to the outermost loop when the connection is closed
                                log.info(
                                    "monitor_docker_events(): "
                                    "restarting aiodocker event subscriber",
                                )
                                break
                            if evdata["Type"] != "container":
                                # Our interest is the container-related events
                                continue
                            container_name = evdata["Actor"]["Attributes"]["name"]
                            kernel_id = await get_kernel_id_from_container(container_name)
                            if kernel_id is None:
                                continue
                            if self.local_config.debug.log_docker_events and evdata["Action"] in (
                                "start",
                                "die",
                                "oom",
                            ):
                                log.debug(
                                    "docker-event: action={}, actor={}",
                                    evdata["Action"],
                                    evdata["Actor"],
                                )
                            session_id = SessionId(
                                UUID(evdata["Actor"]["Attributes"][LabelName.SESSION_ID])
                            )
                            match evdata["Action"]:
                                case "start":
                                    await asyncio.shield(
                                        self.docker_ptask_group.create_task(
                                            handle_action_start(session_id, kernel_id, evdata),
                                        )
                                    )
                                case "die":
                                    await asyncio.shield(
                                        self.docker_ptask_group.create_task(
                                            handle_action_die(session_id, kernel_id, evdata),
                                        )
                                    )
                                case "oom":
                                    await asyncio.shield(
                                        self.docker_ptask_group.create_task(
                                            handle_action_oom(session_id, kernel_id, evdata),
                                        )
                                    )
                        except asyncio.CancelledError:
                            # We are shutting down...
                            return
                        except Exception:
                            log.exception("monitor_docker_events(): unexpected error")
                finally:
                    await asyncio.shield(
                        self.docker_ptask_group.create_task(
                            docker.events.stop(),  # type: ignore[no-untyped-call]
                        )
                    )

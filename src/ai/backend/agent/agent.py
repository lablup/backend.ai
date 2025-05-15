from __future__ import annotations

import asyncio
import logging
import re
from abc import abstractmethod
from collections.abc import (
    Awaitable,
    Callable,
    Collection,
    Iterable,
    Mapping,
    MutableMapping,
    Sequence,
)
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Generic,
    Optional,
    TypeVar,
)

import attrs
import pkg_resources
from cachetools import LRUCache, cached

from ai.backend.agent.backends.kernel import AbstractKernel
from ai.backend.common.docker import (
    DEFAULT_KERNEL_FEATURE,
    ImageRef,
    LabelName,
)
from ai.backend.common.events.dispatcher import (
    EventProducer,
)
from ai.backend.common.types import (
    AgentId,
    ClusterInfo,
    DeviceId,
    DeviceName,
    KernelCreationConfig,
    KernelId,
    MountPermission,
    MountTypes,
    Sentinel,
    SessionId,
    SlotName,
    VFolderMount,
    aobject,
)
from ai.backend.logging import BraceStyleAdapter

from .kernel import match_distro_data
from .resources import (
    AbstractAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
    KernelResourceSpec,
    Mount,
)
from .types import (
    ContainerStatus,
    KernelOwnershipData,
    MountInfo,
)
from .utils import get_arch_name

if TYPE_CHECKING:
    pass

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_sentinel = Sentinel.TOKEN

ACTIVE_STATUS_SET = frozenset([
    ContainerStatus.RUNNING,
    ContainerStatus.RESTARTING,
    ContainerStatus.PAUSED,
])

DEAD_STATUS_SET = frozenset([
    ContainerStatus.EXITED,
    ContainerStatus.DEAD,
    ContainerStatus.REMOVING,
])

COMMIT_STATUS_EXPIRE: Final[int] = 13
EVENT_DISPATCHER_CONSUMER_GROUP: Final = "agent"

KernelObjectType = TypeVar("KernelObjectType", bound=AbstractKernel)


def update_additional_gids(environ: MutableMapping[str, str], gids: Iterable[int]) -> None:
    if not gids:
        return
    if orig_additional_gids := environ.get("ADDITIONAL_GIDS"):
        orig_add_gids = {int(gid) for gid in orig_additional_gids.split(",") if gid}
        additional_gids = orig_add_gids | set(gids)
    else:
        additional_gids = set(gids)
    environ["ADDITIONAL_GIDS"] = ",".join(map(str, additional_gids))


@dataclass
class ScannedImage:
    canonical: str
    digest: str


@dataclass
class ScanImagesResult:
    scanned_images: Mapping[str, ScannedImage]
    removed_images: Mapping[str, ScannedImage]


class AbstractKernelCreationContext(aobject, Generic[KernelObjectType]):
    kspec_version: int
    distro: str
    ownership_data: KernelOwnershipData
    kernel_id: KernelId
    session_id: SessionId
    agent_id: AgentId
    event_producer: EventProducer
    kernel_config: KernelCreationConfig
    local_config: Mapping[str, Any]
    kernel_features: frozenset[str]
    image_ref: ImageRef
    internal_data: Mapping[str, Any]
    additional_allowed_syscalls: list[str]
    restarting: bool
    cancellation_handlers: Sequence[Callable[[], Awaitable[None]]] = []
    _rx_distro = re.compile(r"\.([a-z-]+\d+\.\d+)\.")

    def __init__(
        self,
        ownership_data: KernelOwnershipData,
        event_producer: EventProducer,
        kernel_image: ImageRef,
        kernel_config: KernelCreationConfig,
        distro: str,
        local_config: Mapping[str, Any],
        computers: MutableMapping[DeviceName, ComputerContext],
        restarting: bool = False,
    ) -> None:
        self.image_labels = kernel_config["image"]["labels"]
        self.kspec_version = int(self.image_labels.get("ai.backend.kernelspec", "1"))
        self.kernel_features = frozenset(
            self.image_labels.get(LabelName.FEATURES.value, DEFAULT_KERNEL_FEATURE).split()
        )
        self.ownership_data = ownership_data
        self.session_id = ownership_data.session_id
        self.kernel_id = ownership_data.kernel_id
        self.agent_id = ownership_data.agent_id
        self.event_producer = event_producer
        self.kernel_config = kernel_config
        self.image_ref = kernel_image
        self.distro = distro
        self.internal_data = kernel_config["internal_data"] or {}
        self.computers = computers
        self.restarting = restarting
        self.local_config = local_config

    @abstractmethod
    async def get_extra_envs(self) -> Mapping[str, str]:
        return {}

    @abstractmethod
    async def prepare_resource_spec(
        self,
    ) -> tuple[KernelResourceSpec, Optional[Mapping[str, Any]]]:
        raise NotImplementedError

    @abstractmethod
    async def prepare_scratch(self) -> None:
        pass

    @abstractmethod
    async def get_intrinsic_mounts(self) -> Sequence[Mount]:
        return []

    def update_user_bootstrap_script(self, script: str) -> None:
        """
        Replace user-defined bootstrap script to an arbitrary one created by agent.
        """
        self.kernel_config["bootstrap_script"] = script

    @property
    @abstractmethod
    def repl_ports(self) -> Sequence[int]:
        """
        Return the list of intrinsic REPL ports to exclude from public mapping.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def protected_services(self) -> Sequence[str]:
        """
        Return the list of protected (intrinsic) service names to exclude from public mapping.
        """
        raise NotImplementedError

    @abstractmethod
    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        """
        Apply the given cluster network information to the deployment.
        """
        raise NotImplementedError

    @abstractmethod
    async def prepare_ssh(self, cluster_info: ClusterInfo) -> None:
        """
        Prepare container to accept SSH connection.
        Install the ssh keypair inside the kernel from cluster_info.
        """
        raise NotImplementedError

    @abstractmethod
    async def process_mounts(self, mounts: Sequence[Mount]):
        raise NotImplementedError

    @abstractmethod
    async def apply_accelerator_allocation(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def generate_accelerator_mounts(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> list[MountInfo]:
        raise NotImplementedError

    @abstractmethod
    def resolve_krunner_filepath(self, filename) -> Path:
        """
        Return matching krunner path object for given filename.
        """
        raise NotImplementedError

    @abstractmethod
    def get_runner_mount(
        self,
        type: MountTypes,
        src: str | Path,
        target: str | Path,
        perm: MountPermission = MountPermission.READ_ONLY,
        opts: Optional[Mapping[str, Any]] = None,
    ):
        """
        Return mount object to mount target krunner file/folder/volume.
        """
        raise NotImplementedError

    @abstractmethod
    async def prepare_container(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports,
        cluster_info: ClusterInfo,
    ) -> KernelObjectType:
        raise NotImplementedError

    @abstractmethod
    async def start_container(
        self,
        kernel_obj: AbstractKernel,
        cmdargs: list[str],
        resource_opts,
        preopen_ports,
        cluster_info: ClusterInfo,
    ) -> Mapping[str, Any]:
        raise NotImplementedError

    @cached(
        cache=LRUCache(maxsize=32),  # type: ignore
        key=lambda self: (
            self.image_ref,
            self.distro,
        ),
    )
    def get_krunner_info(self) -> tuple[str, str, str, str, str]:
        distro = self.distro
        matched_distro, krunner_volume = match_distro_data(
            self.local_config["container"]["krunner-volumes"], distro
        )
        matched_libc_style = "glibc"
        if distro.startswith("alpine"):
            matched_libc_style = "musl"
        krunner_pyver = "3.6"  # fallback
        if m := re.search(r"^([a-z-]+)(\d+(\.\d+)*)?$", matched_distro):
            matched_distro_pkgname = m.group(1).replace("-", "_")
            try:
                krunner_pyver = (
                    Path(
                        pkg_resources.resource_filename(
                            f"ai.backend.krunner.{matched_distro_pkgname}",
                            f"krunner-python.{matched_distro}.txt",
                        )
                    )
                    .read_text()
                    .strip()
                )
            except FileNotFoundError:
                pass
        log.debug("selected krunner: {}", matched_distro)
        log.debug("selected libc style: {}", matched_libc_style)
        log.debug("krunner volume: {}", krunner_volume)
        log.debug("krunner python: {}", krunner_pyver)
        arch = get_arch_name()
        return arch, matched_distro, matched_libc_style, krunner_volume, krunner_pyver

    async def mount_vfolders(
        self,
        vfolders: Sequence[VFolderMount],
        resource_spec: KernelResourceSpec,
    ) -> None:
        for vfolder in vfolders:
            if self.internal_data.get("prevent_vfolder_mounts", False):
                # Only allow mount of ".logs" directory to prevent expose
                # internal-only information, such as Docker credentials to user's ".docker" vfolder
                # in image importer kernels.
                if vfolder.name != ".logs":
                    continue
            mount = Mount(
                MountTypes.BIND,
                Path(vfolder.host_path),
                Path(vfolder.kernel_path),
                vfolder.mount_perm,
            )
            resource_spec.mounts.append(mount)

    async def mount_krunner(
        self,
        resource_spec: KernelResourceSpec,
        environ: MutableMapping[str, str],
    ) -> None:
        def _mount(
            type,
            src,
            dst,
        ):
            resource_spec.mounts.append(
                self.get_runner_mount(
                    type,
                    src,
                    dst,
                    MountPermission.READ_ONLY,
                ),
            )

        # Inject Backend.AI kernel runner dependencies.
        distro = self.distro

        (
            arch,
            matched_distro,
            matched_libc_style,
            krunner_volume,
            krunner_pyver,
        ) = self.get_krunner_info()
        artifact_path = Path(pkg_resources.resource_filename("ai.backend.agent", "../runner"))

        def find_artifacts(pattern: str) -> Mapping[str, str]:
            artifacts = {}
            for p in artifact_path.glob(pattern):
                m = self._rx_distro.search(p.name)
                if m is not None:
                    artifacts[m.group(1)] = p.name
            return artifacts

        def mount_versioned_binary(candidate_glob: str, target_path: str) -> None:
            candidates = find_artifacts(candidate_glob)
            _, candidate = match_distro_data(candidates, distro)
            resolved_path = self.resolve_krunner_filepath("runner/" + candidate)
            _mount(MountTypes.BIND, resolved_path, target_path)

        def mount_static_binary(filename: str, target_path: str) -> None:
            resolved_path = self.resolve_krunner_filepath("runner/" + filename)
            _mount(MountTypes.BIND, resolved_path, target_path)

        mount_static_binary(f"su-exec.{arch}.bin", "/opt/kernel/su-exec")
        mount_versioned_binary(f"libbaihook.*.{arch}.so", "/opt/kernel/libbaihook.so")
        mount_static_binary(f"dropbearmulti.{arch}.bin", "/opt/kernel/dropbearmulti")
        mount_static_binary(f"sftp-server.{arch}.bin", "/opt/kernel/sftp-server")
        mount_static_binary(f"tmux.{arch}.bin", "/opt/kernel/tmux")

        jail_path: Optional[Path]
        if self.local_config["container"]["sandbox-type"] == "jail":
            jail_candidates = find_artifacts(
                f"jail.*.{arch}.bin"
            )  # architecture check is already done when starting agent
            _, jail_candidate = match_distro_data(jail_candidates, distro)
            jail_path = self.resolve_krunner_filepath("runner/" + jail_candidate)
        else:
            jail_path = None

        dotfile_extractor_path = self.resolve_krunner_filepath("runner/extract_dotfiles.py")
        persistent_files_warning_doc_path = self.resolve_krunner_filepath(
            "runner/DO_NOT_STORE_PERSISTENT_FILES_HERE.md"
        )
        entrypoint_sh_path = self.resolve_krunner_filepath("runner/entrypoint.sh")

        fantompass_path = self.resolve_krunner_filepath("runner/fantompass.py")
        hash_phrase_path = self.resolve_krunner_filepath("runner/hash_phrase.py")
        words_json_path = self.resolve_krunner_filepath("runner/words.json")

        if matched_libc_style == "musl":
            terminfo_path = self.resolve_krunner_filepath("runner/terminfo.alpine3.8")
            _mount(MountTypes.BIND, terminfo_path, "/home/work/.terminfo")

        _mount(MountTypes.BIND, dotfile_extractor_path, "/opt/kernel/extract_dotfiles.py")
        _mount(MountTypes.BIND, entrypoint_sh_path, "/opt/kernel/entrypoint.sh")
        _mount(MountTypes.BIND, fantompass_path, "/opt/kernel/fantompass.py")
        _mount(MountTypes.BIND, hash_phrase_path, "/opt/kernel/hash_phrase.py")
        _mount(MountTypes.BIND, words_json_path, "/opt/kernel/words.json")
        if jail_path is not None:
            _mount(MountTypes.BIND, jail_path, "/opt/kernel/jail")
        _mount(
            MountTypes.BIND,
            persistent_files_warning_doc_path,
            "/home/work/DO_NOT_STORE_PERSISTENT_FILES_HERE.md",
        )

        _mount(MountTypes.VOLUME, krunner_volume, "/opt/backend.ai")
        pylib_path = f"/opt/backend.ai/lib/python{krunner_pyver}/site-packages/"
        kernel_pkg_path = self.resolve_krunner_filepath("kernel")
        helpers_pkg_path = self.resolve_krunner_filepath("helpers")
        _mount(MountTypes.BIND, kernel_pkg_path, pylib_path + "ai/backend/kernel")
        _mount(MountTypes.BIND, helpers_pkg_path, pylib_path + "ai/backend/helpers")
        environ["LD_PRELOAD"] = "/opt/kernel/libbaihook.so"

        # Inject ComputeDevice-specific env-varibles and hooks
        already_injected_hooks: set[Path] = set()
        additional_gid_set: set[int] = set()
        additional_allowed_syscalls_set: set[str] = set()

        for dev_type, device_alloc in resource_spec.allocations.items():
            computer_ctx = self.computers[dev_type]
            await self.apply_accelerator_allocation(
                computer_ctx.instance,
                device_alloc,
            )
            accelerator_mounts = await self.generate_accelerator_mounts(
                computer_ctx.instance,
                device_alloc,
            )

            additional_gids = computer_ctx.instance.get_additional_gids()
            additional_gid_set.update(additional_gids)

            additional_allowed_syscalls = computer_ctx.instance.get_additional_allowed_syscalls()
            additional_allowed_syscalls_set.update(additional_allowed_syscalls)

            for mount_info in accelerator_mounts:
                _mount(mount_info.mode, mount_info.src_path, mount_info.dst_path.as_posix())
            alloc_sum = Decimal(0)
            for dev_id, per_dev_alloc in device_alloc.items():
                alloc_sum += sum(per_dev_alloc.values())
            if alloc_sum > 0:
                hook_paths = await computer_ctx.instance.get_hooks(distro, arch)
                if hook_paths:
                    log.debug(
                        "accelerator {} provides hooks: {}",
                        type(computer_ctx.instance).__name__,
                        ", ".join(map(str, hook_paths)),
                    )
                for hook_path in map(lambda p: Path(p).absolute(), hook_paths):
                    if hook_path in already_injected_hooks:
                        continue
                    container_hook_path = f"/opt/kernel/{hook_path.name}"
                    _mount(MountTypes.BIND, hook_path, container_hook_path)
                    environ["LD_PRELOAD"] += ":" + container_hook_path
                    already_injected_hooks.add(hook_path)

        self.additional_allowed_syscalls = sorted(list(additional_allowed_syscalls_set))
        update_additional_gids(environ, additional_gids)

    def get_overriding_uid(self) -> Optional[int]:
        return None

    def get_overriding_gid(self) -> Optional[int]:
        return None

    def get_supplementary_gids(self) -> set[int]:
        return set()


KernelCreationContextType = TypeVar(
    "KernelCreationContextType", bound=AbstractKernelCreationContext
)


@attrs.define(auto_attribs=True, slots=True)
class RestartTracker:
    request_lock: asyncio.Lock
    destroy_event: asyncio.Event
    done_event: asyncio.Event


@attrs.define(auto_attribs=True, slots=True)
class ComputerContext:
    instance: AbstractComputePlugin
    devices: Collection[AbstractComputeDevice]
    alloc_map: AbstractAllocMap

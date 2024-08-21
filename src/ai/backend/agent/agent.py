from __future__ import annotations

import asyncio
import json
import logging
import os
import pickle
import re
import shutil
import signal
import sys
import textwrap
import time
import traceback
import weakref
import zlib
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from decimal import Decimal
from io import SEEK_END, BytesIO
from pathlib import Path
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Collection,
    Dict,
    Final,
    FrozenSet,
    Generic,
    List,
    Literal,
    Mapping,
    MutableMapping,
    MutableSequence,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)
from uuid import UUID

import aiotools
import attrs
import pkg_resources
import yaml
import zmq
import zmq.asyncio
from async_timeout import timeout
from cachetools import LRUCache, cached
from redis.asyncio import Redis
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
    wait_fixed,
)
from trafaret import DataError

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.bgtask import BackgroundTaskManager
from ai.backend.common.config import model_definition_iv
from ai.backend.common.defs import REDIS_STAT_DB, REDIS_STREAM_DB
from ai.backend.common.docker import MAX_KERNELSPEC, MIN_KERNELSPEC, ImageRef
from ai.backend.common.events import (
    AbstractEvent,
    AgentErrorEvent,
    AgentHeartbeatEvent,
    AgentStartedEvent,
    AgentTerminatedEvent,
    DoAgentResourceCheckEvent,
    DoSyncKernelLogsEvent,
    DoVolumeMountEvent,
    DoVolumeUnmountEvent,
    EventDispatcher,
    EventProducer,
    ExecutionCancelledEvent,
    ExecutionFinishedEvent,
    ExecutionStartedEvent,
    ExecutionTimeoutEvent,
    KernelCreatingEvent,
    KernelLifecycleEventReason,
    KernelPreparingEvent,
    KernelPullingEvent,
    KernelStartedEvent,
    KernelTerminatedEvent,
    ModelServiceStatusEvent,
    SessionFailureEvent,
    SessionSuccessEvent,
    VolumeMountableNodeType,
    VolumeMounted,
    VolumeUnmounted,
)
from ai.backend.common.events_experimental import EventDispatcher as ExperimentalEventDispatcher
from ai.backend.common.exception import VolumeMountFailed
from ai.backend.common.lock import FileLock
from ai.backend.common.logging import BraceStyleAdapter, pretty
from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext
from ai.backend.common.service_ports import parse_service_ports
from ai.backend.common.types import (
    MODEL_SERVICE_RUNTIME_PROFILES,
    AbuseReportValue,
    AcceleratorMetadata,
    AgentId,
    AutoPullBehavior,
    ClusterInfo,
    ClusterSSHPortMapping,
    CommitStatus,
    ContainerId,
    DeviceId,
    DeviceName,
    HardwareMetadata,
    ImageConfig,
    ImageRegistry,
    KernelCreationConfig,
    KernelCreationResult,
    KernelId,
    ModelServiceStatus,
    MountPermission,
    MountTypes,
    RuntimeVariant,
    Sentinel,
    ServicePort,
    ServicePortProtocols,
    SessionId,
    SessionTypes,
    SlotName,
    VFolderMount,
    VFolderUsageMode,
    aobject,
)
from ai.backend.common.utils import cancel_tasks, current_loop, mount, umount

from . import __version__ as VERSION
from . import alloc_map as alloc_map_mod
from .affinity_map import AffinityMap
from .exception import AgentError, ContainerCreationError, ResourceError
from .kernel import AbstractKernel, KernelFeatures, match_distro_data
from .resources import (
    AbstractAllocMap,
    AbstractComputeDevice,
    AbstractComputePlugin,
    KernelResourceSpec,
    Mount,
    allocate,
    known_slot_types,
)
from .stats import StatContext, StatModes
from .types import (
    Container,
    ContainerLifecycleEvent,
    ContainerStatus,
    KernelLifecycleStatus,
    LifecycleEvent,
    MountInfo,
)
from .utils import generate_local_instance_id, get_arch_name

if TYPE_CHECKING:
    from ai.backend.common.auth import PublicKey
    from ai.backend.common.etcd import AsyncEtcd

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


class AbstractKernelCreationContext(aobject, Generic[KernelObjectType]):
    kspec_version: int
    distro: str
    kernel_id: KernelId
    session_id: SessionId
    agent_id: AgentId
    event_producer: EventProducer
    kernel_config: KernelCreationConfig
    local_config: Mapping[str, Any]
    kernel_features: FrozenSet[str]
    image_ref: ImageRef
    internal_data: Mapping[str, Any]
    restarting: bool
    cancellation_handlers: Sequence[Callable[[], Awaitable[None]]] = []
    _rx_distro = re.compile(r"\.([a-z-]+\d+\.\d+)\.")

    def __init__(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        agent_id: AgentId,
        event_producer: EventProducer,
        kernel_config: KernelCreationConfig,
        distro: str,
        local_config: Mapping[str, Any],
        computers: MutableMapping[DeviceName, ComputerContext],
        restarting: bool = False,
    ) -> None:
        self.image_labels = kernel_config["image"]["labels"]
        self.kspec_version = int(self.image_labels.get("ai.backend.kernelspec", "1"))
        self.kernel_features = frozenset(
            self.image_labels.get("ai.backend.features", "uid-match").split()
        )
        self.kernel_id = kernel_id
        self.session_id = session_id
        self.agent_id = agent_id
        self.event_producer = event_producer
        self.kernel_config = kernel_config
        self.image_ref = ImageRef(
            kernel_config["image"]["canonical"],
            known_registries=[kernel_config["image"]["registry"]["name"]],
            is_local=kernel_config["image"]["is_local"],
            architecture=kernel_config["image"].get("architecture", get_arch_name()),
        )
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
    ) -> Tuple[KernelResourceSpec, Optional[Mapping[str, Any]]]:
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
    ) -> List[MountInfo]:
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
        src: Union[str, Path],
        target: Union[str, Path],
        perm: Literal["ro", "rw"] = "ro",
        opts: Mapping[str, Any] = None,
    ):
        """
        Return mount object to mount target krunner file/folder/volume.
        """
        raise NotImplementedError

    @abstractmethod
    async def spawn(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports,
    ) -> KernelObjectType:
        raise NotImplementedError

    @abstractmethod
    async def start_container(
        self,
        kernel_obj: AbstractKernel,
        cmdargs: List[str],
        resource_opts,
        preopen_ports,
    ) -> Mapping[str, Any]:
        raise NotImplementedError

    @cached(
        cache=LRUCache(maxsize=32),  # type: ignore
        key=lambda self: (
            self.image_ref,
            self.distro,
        ),
    )
    def get_krunner_info(self) -> Tuple[str, str, str, str, str]:
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
                    MountPermission("ro"),
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
        already_injected_hooks: Set[Path] = set()
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


class AbstractAgent(
    aobject, Generic[KernelObjectType, KernelCreationContextType], metaclass=ABCMeta
):
    id: AgentId
    loop: asyncio.AbstractEventLoop
    local_config: Mapping[str, Any]
    etcd: AsyncEtcd
    local_instance_id: str
    kernel_registry: MutableMapping[KernelId, AbstractKernel]
    computers: MutableMapping[DeviceName, ComputerContext]
    images: Mapping[str, str]
    port_pool: Set[int]

    redis: Redis

    restarting_kernels: MutableMapping[KernelId, RestartTracker]
    timer_tasks: MutableSequence[asyncio.Task]
    container_lifecycle_queue: asyncio.Queue[ContainerLifecycleEvent | Sentinel]

    agent_public_key: Optional[PublicKey]

    stat_ctx: StatContext
    stat_sync_sockpath: Path
    stat_sync_task: asyncio.Task

    stats_monitor: StatsPluginContext  # unused currently
    error_monitor: ErrorPluginContext  # unused in favor of produce_error_event()

    background_task_manager: BackgroundTaskManager

    _pending_creation_tasks: Dict[KernelId, Set[asyncio.Task]]
    _ongoing_exec_batch_tasks: weakref.WeakSet[asyncio.Task]
    _ongoing_destruction_tasks: weakref.WeakValueDictionary[KernelId, asyncio.Task]

    def __init__(
        self,
        etcd: AsyncEtcd,
        local_config: Mapping[str, Any],
        *,
        stats_monitor: StatsPluginContext,
        error_monitor: ErrorPluginContext,
        skip_initial_scan: bool = False,
        agent_public_key: Optional[PublicKey],
    ) -> None:
        self._skip_initial_scan = skip_initial_scan
        self.loop = current_loop()
        self.etcd = etcd
        self.local_config = local_config
        self.id = AgentId(local_config["agent"]["id"])
        self.local_instance_id = generate_local_instance_id(__file__)
        self.agent_public_key = agent_public_key
        self.kernel_registry = {}
        self.computers = {}
        self.images = {}  # repoTag -> digest
        self.restarting_kernels = {}
        self.stat_ctx = StatContext(
            self,
            mode=StatModes(local_config["container"]["stats-type"]),
        )
        self.timer_tasks = []
        self.port_pool = set(
            range(
                local_config["container"]["port-range"][0],
                local_config["container"]["port-range"][1] + 1,
            )
        )
        self.stats_monitor = stats_monitor
        self.error_monitor = error_monitor
        self._pending_creation_tasks = defaultdict(set)
        self._ongoing_exec_batch_tasks = weakref.WeakSet()
        self._ongoing_destruction_tasks = weakref.WeakValueDictionary()

    async def __ainit__(self) -> None:
        """
        An implementation of AbstractAgent would define its own ``__ainit__()`` method.
        It must call this super method in an appropriate order, only once.
        """
        self.resource_lock = asyncio.Lock()
        self.registry_lock = asyncio.Lock()
        self.container_lifecycle_queue = asyncio.Queue()

        event_dispatcher_cls: type[EventDispatcher] | type[ExperimentalEventDispatcher]
        if self.local_config["agent"].get("use-experimental-redis-event-dispatcher"):
            event_dispatcher_cls = ExperimentalEventDispatcher
        else:
            event_dispatcher_cls = EventDispatcher

        self.event_producer = await EventProducer.new(
            self.local_config["redis"],
            db=REDIS_STREAM_DB,
            log_events=self.local_config["debug"]["log-events"],
        )
        self.event_dispatcher = await event_dispatcher_cls.new(
            self.local_config["redis"],
            db=REDIS_STREAM_DB,
            log_events=self.local_config["debug"]["log-events"],
            node_id=self.local_config["agent"]["id"],
            consumer_group=EVENT_DISPATCHER_CONSUMER_GROUP,
        )
        self.redis_stream_pool = redis_helper.get_redis_object(
            self.local_config["redis"],
            name="stream",
            db=REDIS_STREAM_DB,
        )
        self.redis_stat_pool = redis_helper.get_redis_object(
            self.local_config["redis"],
            name="stat",
            db=REDIS_STAT_DB,
        )

        self.background_task_manager = BackgroundTaskManager(self.event_producer)

        alloc_map_mod.log_alloc_map = self.local_config["debug"]["log-alloc-map"]
        computers = await self.load_resources()

        all_devices: List[AbstractComputeDevice] = []
        metadatas: List[AcceleratorMetadata] = []
        for name, computer in computers.items():
            devices = await computer.list_devices()
            all_devices.extend(devices)
            alloc_map = await computer.create_alloc_map()
            self.computers[name] = ComputerContext(computer, devices, alloc_map)
            metadatas.append(computer.get_metadata())

        self.slots = await self.scan_available_resources()
        log.info("Resource slots: {!r}", self.slots)
        log.info("Slot types: {!r}", known_slot_types)
        self.timer_tasks.append(aiotools.create_timer(self.update_slots, 30.0))

        async def _pipeline(r: Redis):
            pipe = r.pipeline()
            for metadata in metadatas:
                await pipe.hset(
                    "computer.metadata",
                    metadata["slot_name"],
                    json.dumps(metadata),
                )
            return pipe

        await redis_helper.execute(self.redis_stat_pool, _pipeline)

        self.affinity_map = AffinityMap.build(all_devices)

        if not self._skip_initial_scan:
            self.images = await self.scan_images()
            self.timer_tasks.append(aiotools.create_timer(self._scan_images_wrapper, 20.0))
            await self.scan_running_kernels()

        # Prepare stat collector tasks.
        self.timer_tasks.append(aiotools.create_timer(self.collect_node_stat, 5.0))
        self.timer_tasks.append(aiotools.create_timer(self.collect_container_stat, 5.0))
        self.timer_tasks.append(aiotools.create_timer(self.collect_process_stat, 5.0))

        # Prepare heartbeats.
        heartbeat_interval = self.local_config["debug"]["heartbeat-interval"]
        self.timer_tasks.append(aiotools.create_timer(self.heartbeat, heartbeat_interval))

        # Prepare auto-cleaning of idle kernels.
        sync_container_lifecycles_config = self.local_config["agent"]["sync-container-lifecycles"]
        if sync_container_lifecycles_config["enabled"]:
            self.timer_tasks.append(
                aiotools.create_timer(
                    self.sync_container_lifecycles, sync_container_lifecycles_config["interval"]
                )
            )

        if abuse_report_path := self.local_config["agent"].get("abuse-report-path"):
            log.info(
                "Monitoring abnormal kernel activities reported by Watcher at {}", abuse_report_path
            )
            abuse_report_path.mkdir(exist_ok=True, parents=True)
            self.timer_tasks.append(aiotools.create_timer(self._cleanup_reported_kernels, 30.0))

        # Report commit status
        self.timer_tasks.append(
            aiotools.create_timer(self._report_all_kernel_commit_status_map, 7.0)
        )

        loop = current_loop()
        self.last_registry_written_time = time.monotonic()
        self.container_lifecycle_handler = loop.create_task(self.process_lifecycle_events())

        # Notify the gateway.
        await self.produce_event(AgentStartedEvent(reason="self-started"))

        # passive events
        evd = self.event_dispatcher
        evd.subscribe(DoVolumeMountEvent, self, handle_volume_mount, name="ag.volume.mount")
        evd.subscribe(DoVolumeUnmountEvent, self, handle_volume_umount, name="ag.volume.umount")

    async def shutdown(self, stop_signal: signal.Signals) -> None:
        """
        An implementation of AbstractAgent would define its own ``shutdown()`` method.
        It must call this super method in an appropriate order, only once.
        """
        await cancel_tasks(self._ongoing_exec_batch_tasks)

        async with self.registry_lock:
            # Close all pending kernel runners.
            for kernel_obj in self.kernel_registry.values():
                if kernel_obj.runner is not None:
                    await kernel_obj.runner.close()
                await kernel_obj.close()
            await self.save_last_registry(force=True)
            if stop_signal == signal.SIGTERM:
                await self.clean_all_kernels(blocking=True)

        # Stop timers.
        cancel_results = await cancel_tasks(self.timer_tasks)
        for result in cancel_results:
            if isinstance(result, Exception):
                log.error("timer cancellation error: {}", result)

        # Stop lifecycle event handler.
        await self.container_lifecycle_queue.put(_sentinel)
        await self.container_lifecycle_handler

        # Notify the gateway.
        await self.produce_event(AgentTerminatedEvent(reason="shutdown"))

        # Shut down the event dispatcher and Redis connection pools.
        await self.event_producer.close()
        await self.event_dispatcher.close()
        await self.redis_stream_pool.close()
        await self.redis_stat_pool.close()

    async def produce_event(self, event: AbstractEvent) -> None:
        """
        Send an event to the manager(s).
        """
        if self.local_config["debug"]["log-heartbeats"]:
            _log = log.debug if isinstance(event, AgentHeartbeatEvent) else log.info
        else:
            _log = (lambda *args: None) if isinstance(event, AgentHeartbeatEvent) else log.info
        if self.local_config["debug"]["log-events"]:
            _log("produce_event({0})", event)
        if isinstance(event, KernelTerminatedEvent):
            pending_creation_tasks = self._pending_creation_tasks.get(event.kernel_id, None)
            if pending_creation_tasks is not None:
                for t in set(pending_creation_tasks):
                    if not t.done() and not t.cancelled():
                        t.cancel()
                        try:
                            await t
                        except asyncio.CancelledError:
                            continue
        if isinstance(event, KernelStartedEvent) or isinstance(event, KernelTerminatedEvent):
            await self.save_last_registry()
        await self.event_producer.produce_event(event, source=str(self.id))

    async def produce_error_event(
        self,
        exc_info: Tuple[Type[BaseException], BaseException, TracebackType] = None,
    ) -> None:
        exc_type, exc, tb = sys.exc_info() if exc_info is None else exc_info
        pretty_message = "".join(traceback.format_exception_only(exc_type, exc)).strip()
        pretty_tb = "".join(traceback.format_tb(tb)).strip()
        await self.produce_event(AgentErrorEvent(pretty_message, pretty_tb))

    async def _report_all_kernel_commit_status_map(self, interval: float) -> None:
        """
        Commit statuses are managed by `lock` file.
        +- base_commit_path
        |_ subdir1 (usually user's email)
            |_ commit_file1 (named by timestamp)
            |_ commit_file2
            |_ lock
                |_ kernel_id1 (means the user is currently committing the kernel)
                |_ kernel_id2
        |_ subdir2
        """
        loop = current_loop()
        base_commit_path: Path = self.local_config["agent"]["image-commit-path"]
        commit_kernels: set[str] = set()

        def _map_commit_status() -> None:
            for subdir in base_commit_path.iterdir():
                for commit_path in subdir.glob("./**/lock/*"):
                    kern = commit_path.name
                    if kern not in commit_kernels:
                        commit_kernels.add(kern)

        await loop.run_in_executor(None, _map_commit_status)

        commit_status_script = textwrap.dedent(
            """
        local key_and_value = {}
        for i, k in pairs(KEYS) do
            key_and_value[i*2-1] = k
            key_and_value[i*2] = 'ongoing'
        end
        if next(key_and_value) ~= nil then
            redis.call('MSET', unpack(key_and_value))
            for i, k in pairs(KEYS) do
                redis.call('EXPIRE', k, ARGV[1])
            end
        end
        """
        )
        await redis_helper.execute_script(
            self.redis_stat_pool,
            "check_kernel_commit_statuses",
            commit_status_script,
            [f"kernel.{kern}.commit" for kern in commit_kernels],
            [COMMIT_STATUS_EXPIRE],
        )

    async def heartbeat(self, interval: float):
        """
        Send my status information and available kernel images to the manager(s).
        """
        res_slots = {}
        try:
            for cctx in self.computers.values():
                for slot_key, slot_type in cctx.instance.slot_types:
                    res_slots[slot_key] = (
                        slot_type,
                        str(self.slots.get(slot_key, 0)),
                    )
            if self.local_config["agent"]["advertised-rpc-addr"]:
                rpc_addr = self.local_config["agent"]["advertised-rpc-addr"]
            else:
                rpc_addr = self.local_config["agent"]["rpc-listen-addr"]
            agent_info = {
                "ip": str(rpc_addr.host),
                "region": self.local_config["agent"]["region"],
                "scaling_group": self.local_config["agent"]["scaling-group"],
                "addr": f"tcp://{rpc_addr}",
                "public_key": self.agent_public_key,
                "public_host": str(self._get_public_host()),
                "resource_slots": res_slots,
                "version": VERSION,
                "compute_plugins": {
                    key: {
                        "version": computer.instance.get_version(),
                        **(await computer.instance.extra_info()),
                    }
                    for key, computer in self.computers.items()
                },
                "images": zlib.compress(
                    msgpack.packb([(repo_tag, digest) for repo_tag, digest in self.images.items()])
                ),
                "images.opts": {"compression": "zlib"},  # compression: zlib or None
                "architecture": get_arch_name(),
                "auto_terminate_abusing_kernel": self.local_config["agent"][
                    "force-terminate-abusing-containers"
                ],
            }
            await self.produce_event(AgentHeartbeatEvent(agent_info))
        except asyncio.TimeoutError:
            log.warning("event dispatch timeout: instance_heartbeat")
        except Exception:
            log.exception("instance_heartbeat failure")
            await self.produce_error_event()

    async def collect_logs(
        self,
        kernel_id: KernelId,
        container_id: str,
        async_log_iterator: AsyncIterator[bytes],
    ) -> None:
        chunk_size = self.local_config["agent"]["container-logs"]["chunk-size"]
        log_key = f"containerlog.{container_id}"
        log_length = 0
        chunk_buffer = BytesIO()
        chunk_length = 0
        try:
            async with aiotools.aclosing(async_log_iterator):
                async for fragment in async_log_iterator:
                    fragment_length = len(fragment)
                    chunk_buffer.write(fragment)
                    chunk_length += fragment_length
                    log_length += fragment_length
                    while chunk_length >= chunk_size:
                        cb = chunk_buffer.getbuffer()
                        stored_chunk = bytes(cb[:chunk_size])
                        await redis_helper.execute(
                            self.redis_stream_pool,
                            lambda r: r.rpush(log_key, stored_chunk),
                        )
                        remaining = cb[chunk_size:]
                        chunk_length = len(remaining)
                        next_chunk_buffer = BytesIO(remaining)
                        next_chunk_buffer.seek(0, SEEK_END)
                        del remaining, cb
                        chunk_buffer.close()
                        chunk_buffer = next_chunk_buffer
            assert chunk_length < chunk_size
            if chunk_length > 0:
                await redis_helper.execute(
                    self.redis_stream_pool,
                    lambda r: r.rpush(log_key, chunk_buffer.getvalue()),
                )
        finally:
            chunk_buffer.close()
        # Keep the log for at most one hour in Redis.
        # This is just a safety measure to prevent memory leak in Redis
        # for cases when the event delivery has failed or processing
        # the log data has failed.
        await redis_helper.execute(
            self.redis_stream_pool,
            lambda r: r.expire(log_key, 3600),
        )
        await self.produce_event(DoSyncKernelLogsEvent(kernel_id, container_id))

    async def collect_node_stat(self, interval: float):
        if self.local_config["debug"]["log-stats"]:
            log.debug("collecting node statistics")
        try:
            await self.stat_ctx.collect_node_stat()
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception("unhandled exception while syncing node stats")
            await self.produce_error_event()

    async def collect_container_stat(self, interval: float):
        if self.local_config["debug"]["log-stats"]:
            log.debug("collecting container statistics")
        try:
            container_ids = []
            async with self.registry_lock:
                for kernel_id, kernel_obj in [*self.kernel_registry.items()]:
                    if (
                        not kernel_obj.stats_enabled
                        or kernel_obj.state != KernelLifecycleStatus.RUNNING
                    ):
                        continue
                    container_ids.append(kernel_obj["container_id"])
                await self.stat_ctx.collect_container_stat(container_ids)
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception("unhandled exception while syncing container stats")
            await self.produce_error_event()

    async def collect_process_stat(self, interval: float):
        if self.local_config["debug"]["log-stats"]:
            log.debug("collecting process statistics in container")
        try:
            updated_kernel_ids = []
            container_ids = []
            async with self.registry_lock:
                for kernel_id, kernel_obj in [*self.kernel_registry.items()]:
                    if (
                        not kernel_obj.stats_enabled
                        or kernel_obj.state != KernelLifecycleStatus.RUNNING
                    ):
                        continue
                    updated_kernel_ids.append(kernel_id)
                    container_ids.append(kernel_obj["container_id"])
                await self.stat_ctx.collect_per_container_process_stat(container_ids)
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception("unhandled exception while syncing process stats")
            await self.produce_error_event()

    def _get_public_host(self) -> str:
        agent_config: Mapping[str, Any] = self.local_config["agent"]
        container_config: Mapping[str, Any] = self.local_config["container"]
        return (
            agent_config.get("public-host")
            or container_config.get("advertised-host")
            or container_config["bind-host"]
        )

    async def _handle_start_event(self, ev: ContainerLifecycleEvent) -> None:
        async with self.registry_lock:
            kernel_obj = self.kernel_registry.get(ev.kernel_id)
            if kernel_obj is not None:
                kernel_obj.stats_enabled = True
                kernel_obj.state = KernelLifecycleStatus.RUNNING

    async def _handle_destroy_event(self, ev: ContainerLifecycleEvent) -> None:
        try:
            current_task = asyncio.current_task()
            assert current_task is not None
            if ev.kernel_id not in self._ongoing_destruction_tasks:
                self._ongoing_destruction_tasks[ev.kernel_id] = current_task
            async with self.registry_lock:
                kernel_obj = self.kernel_registry.get(ev.kernel_id)
                if kernel_obj is None:
                    log.warning(
                        "destroy_kernel(k:{0}, c:{1}) kernel missing (already dead?)",
                        ev.kernel_id,
                        ev.container_id,
                    )
                    if ev.container_id is None:
                        await self.reconstruct_resource_usage()
                        if not ev.suppress_events:
                            await self.produce_event(
                                KernelTerminatedEvent(
                                    ev.kernel_id,
                                    ev.session_id,
                                    reason=KernelLifecycleEventReason.ALREADY_TERMINATED,
                                ),
                            )
                        if ev.done_future is not None:
                            ev.done_future.set_result(None)
                        return
                else:
                    kernel_obj.state = KernelLifecycleStatus.TERMINATING
                    kernel_obj.stats_enabled = False
                    kernel_obj.termination_reason = ev.reason
                    if kernel_obj.runner is not None:
                        await kernel_obj.runner.close()
                    kernel_obj.clean_event = ev.done_future
                try:
                    await self.destroy_kernel(ev.kernel_id, ev.container_id)
                except Exception as e:
                    if ev.done_future is not None:
                        ev.done_future.set_exception(e)
                    raise
                finally:
                    await self.container_lifecycle_queue.put(
                        ContainerLifecycleEvent(
                            ev.kernel_id,
                            ev.session_id,
                            ev.container_id,
                            LifecycleEvent.CLEAN,
                            ev.reason,
                            suppress_events=ev.suppress_events,
                            done_future=ev.done_future,
                        ),
                    )
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception("unhandled exception while processing DESTROY event")
            await self.produce_error_event()

    async def _handle_clean_event(self, ev: ContainerLifecycleEvent) -> None:
        destruction_task = self._ongoing_destruction_tasks.get(ev.kernel_id, None)
        if destruction_task is not None and not destruction_task.done():
            # let the destruction task finish first
            await destruction_task
            del destruction_task
        async with self.registry_lock:
            try:
                kernel_obj = self.kernel_registry.get(ev.kernel_id)
                if kernel_obj is not None and kernel_obj.runner is not None:
                    await kernel_obj.runner.close()
                await self.clean_kernel(
                    ev.kernel_id,
                    ev.container_id,
                    ev.kernel_id in self.restarting_kernels,
                )
            except Exception as e:
                if ev.done_future is not None:
                    ev.done_future.set_exception(e)
                await self.produce_error_event()
            finally:
                if ev.kernel_id in self.restarting_kernels:
                    # Don't forget as we are restarting it.
                    kernel_obj = self.kernel_registry.get(ev.kernel_id, None)
                else:
                    # Forget as we are done with this kernel.
                    kernel_obj = self.kernel_registry.pop(ev.kernel_id, None)
                try:
                    if kernel_obj is not None:
                        # Restore used ports to the port pool.
                        port_range = self.local_config["container"]["port-range"]
                        # Exclude out-of-range ports, because when the agent restarts
                        # with a different port range, existing containers' host ports
                        # may not belong to the new port range.
                        if host_ports := kernel_obj.get("host_ports"):
                            restored_ports = [
                                *filter(
                                    lambda p: port_range[0] <= p <= port_range[1],
                                    host_ports,
                                )
                            ]
                            self.port_pool.update(restored_ports)
                        await kernel_obj.close()
                finally:
                    if restart_tracker := self.restarting_kernels.get(ev.kernel_id, None):
                        restart_tracker.destroy_event.set()
                    else:
                        await self.reconstruct_resource_usage()
                        if not ev.suppress_events:
                            await self.produce_event(
                                KernelTerminatedEvent(
                                    ev.kernel_id, ev.session_id, reason=ev.reason
                                ),
                            )
                    # Notify cleanup waiters after all state updates.
                    if kernel_obj is not None and kernel_obj.clean_event is not None:
                        kernel_obj.clean_event.set_result(None)
                    if ev.done_future is not None and not ev.done_future.done():
                        ev.done_future.set_result(None)

    async def process_lifecycle_events(self) -> None:
        async def lifecycle_task_exception_handler(
            exc_type: Type[Exception],
            exc_obj: Exception,
            tb: TracebackType,
        ) -> None:
            log.exception("unexpected error in lifecycle task", exc_info=exc_obj)

        async with aiotools.PersistentTaskGroup(
            exception_handler=lifecycle_task_exception_handler,
        ) as tg:
            while True:
                ev = await self.container_lifecycle_queue.get()
                if isinstance(ev, Sentinel):
                    await self.save_last_registry(force=True)
                    return
                # attrs currently does not support customizing getstate/setstate dunder methods
                # until the next release.
                if self.local_config["debug"]["log-events"]:
                    log.info(f"lifecycle event: {ev!r}")
                try:
                    if ev.event == LifecycleEvent.START:
                        tg.create_task(self._handle_start_event(ev))
                    elif ev.event == LifecycleEvent.DESTROY:
                        tg.create_task(self._handle_destroy_event(ev))
                    elif ev.event == LifecycleEvent.CLEAN:
                        tg.create_task(self._handle_clean_event(ev))
                    else:
                        log.warning("unsupported lifecycle event: {!r}", ev)
                except Exception:
                    log.exception(
                        "unexpected error in process_lifecycle_events(): {!r}, continuing...",
                        ev,
                    )
                finally:
                    self.container_lifecycle_queue.task_done()

    async def inject_container_lifecycle_event(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        event: LifecycleEvent,
        reason: KernelLifecycleEventReason,
        *,
        container_id: Optional[ContainerId] = None,
        exit_code: int = None,
        done_future: asyncio.Future = None,
        suppress_events: bool = False,
    ) -> None:
        cid: Optional[ContainerId] = None
        try:
            kernel_obj = self.kernel_registry[kernel_id]
        except KeyError:
            if event == LifecycleEvent.START:
                # When creating a new kernel, the kernel_registry is not populated yet
                # during creation of actual containers.
                # The Docker daemon may publish the container creation event before
                # returning the API and our async handlers may deliver the event earlier.
                # In such cases, it is safe to ignore the missing kernel_regisry item.
                pass
            else:
                log.warning(
                    "injecting lifecycle event (e:{}) for unknown kernel (k:{})",
                    event.name,
                    kernel_id,
                )
        else:
            assert kernel_obj is not None
            if kernel_obj.termination_reason:
                reason = kernel_obj.termination_reason
            if container_id is not None:
                if event == LifecycleEvent.START:
                    # Update the container ID (for restarted kernels).
                    # This will be overwritten by create_kernel() soon, but
                    # updating here improves consistency of kernel_id to container_id
                    # mapping earlier.
                    kernel_obj["container_id"] = container_id
                elif container_id != kernel_obj["container_id"]:
                    # This should not happen!
                    log.warning(
                        "container id mismatch for kernel_obj (k:{}, c:{}) with event (e:{}, c:{})",
                        kernel_id,
                        kernel_obj["container_id"],
                        event.name,
                        container_id,
                    )
            cid = kernel_obj.get("container_id")
        if cid is None:
            log.warning(
                "kernel has no container_id (k:{}) with event (e:{})",
                kernel_id,
                event.name,
            )
        await self.container_lifecycle_queue.put(
            ContainerLifecycleEvent(
                kernel_id,
                session_id,
                cid,
                event,
                reason,
                done_future,
                exit_code,
                suppress_events,
            ),
        )

    @abstractmethod
    async def resolve_image_distro(self, image: ImageConfig) -> str:
        raise NotImplementedError

    @abstractmethod
    async def enumerate_containers(
        self,
        status_filter: FrozenSet[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> Sequence[Tuple[KernelId, Container]]:
        """
        Enumerate the containers with the given status filter.
        """

    async def reconstruct_resource_usage(self) -> None:
        """
        Reconstruct the resource alloc maps for each compute plugin from
        ``/home/config/resource.txt`` files in the kernel containers managed by this agent.
        """
        async with self.resource_lock:
            for computer_ctx in self.computers.values():
                computer_ctx.alloc_map.clear()
            for kernel_id, container in await self.enumerate_containers():
                for computer_ctx in self.computers.values():
                    try:
                        await computer_ctx.instance.restore_from_container(
                            container,
                            computer_ctx.alloc_map,
                        )
                    except Exception:
                        log.warning(
                            "rescan_resource_usage(k:{}): "
                            "failed to read kernel resource info; "
                            "maybe already terminated",
                            kernel_id,
                        )

    async def sync_container_lifecycles(self, interval: float) -> None:
        """
        Periodically synchronize the alive/known container sets,
        for cases when we miss the container lifecycle events from the underlying implementation APIs
        due to the agent restarts or crashes.
        """
        known_kernels: Dict[KernelId, ContainerId | None] = {}
        alive_kernels: Dict[KernelId, ContainerId] = {}
        kernel_session_map: Dict[KernelId, SessionId] = {}
        own_kernels: dict[KernelId, ContainerId] = {}
        terminated_kernels: dict[KernelId, ContainerLifecycleEvent] = {}

        def _get_session_id(container: Container) -> SessionId | None:
            _session_id = container.labels.get("ai.backend.session-id")
            try:
                return SessionId(UUID(_session_id))
            except ValueError:
                log.warning(
                    f"sync_container_lifecycles() invalid session-id (cid: {container.id}, sid:{_session_id})"
                )
                return None

        log.debug("sync_container_lifecycles(): triggered")
        try:
            _containers = await self.enumerate_containers(ACTIVE_STATUS_SET | DEAD_STATUS_SET)
            async with self.registry_lock:
                try:
                    # Check if: there are dead containers
                    dead_containers = [
                        (kid, container)
                        for kid, container in _containers
                        if container.status in DEAD_STATUS_SET
                    ]
                    log.debug(
                        f"detected dead containers: {[container.id[:12] for _, container in dead_containers]}"
                    )
                    for kernel_id, container in dead_containers:
                        if kernel_id in self.restarting_kernels:
                            continue
                        log.info(
                            "detected dead container during lifeycle sync (k:{}, c:{})",
                            kernel_id,
                            container.id,
                        )
                        session_id = _get_session_id(container)
                        if session_id is None:
                            continue
                        terminated_kernels[kernel_id] = ContainerLifecycleEvent(
                            kernel_id,
                            session_id,
                            container.id,
                            LifecycleEvent.CLEAN,
                            KernelLifecycleEventReason.SELF_TERMINATED,
                        )
                    active_containers = [
                        (kid, container)
                        for kid, container in _containers
                        if container.status in ACTIVE_STATUS_SET
                    ]
                    log.debug(
                        f"detected active containers: {[container.id[:12] for _, container in active_containers]}"
                    )
                    for kernel_id, container in active_containers:
                        alive_kernels[kernel_id] = container.id
                        session_id = _get_session_id(container)
                        if session_id is None:
                            continue
                        kernel_session_map[kernel_id] = session_id
                        own_kernels[kernel_id] = container.id
                    for kernel_id, kernel_obj in self.kernel_registry.items():
                        known_kernels[kernel_id] = (
                            ContainerId(kernel_obj.container_id)
                            if kernel_obj.container_id is not None
                            else None
                        )
                        session_id = kernel_obj.session_id
                        kernel_session_map[kernel_id] = session_id
                    # Check if: kernel_registry has the container but it's gone.
                    for kernel_id in known_kernels.keys() - alive_kernels.keys():
                        kernel_obj = self.kernel_registry[kernel_id]
                        if (
                            kernel_id in self.restarting_kernels
                            or kernel_obj.state != KernelLifecycleStatus.RUNNING
                        ):
                            continue
                        log.debug(f"kernel with no container (kid: {kernel_id})")
                        terminated_kernels[kernel_id] = ContainerLifecycleEvent(
                            kernel_id,
                            kernel_session_map[kernel_id],
                            known_kernels[kernel_id],
                            LifecycleEvent.CLEAN,
                            KernelLifecycleEventReason.CONTAINER_NOT_FOUND,
                        )
                    # Check if: there are containers already deleted from my registry.
                    for kernel_id in alive_kernels.keys() - known_kernels.keys():
                        if kernel_id in self.restarting_kernels:
                            continue
                        log.debug(f"kernel not found in registry (kid:{kernel_id})")
                        terminated_kernels[kernel_id] = ContainerLifecycleEvent(
                            kernel_id,
                            kernel_session_map[kernel_id],
                            alive_kernels[kernel_id],
                            LifecycleEvent.DESTROY,
                            KernelLifecycleEventReason.TERMINATED_UNKNOWN_CONTAINER,
                        )
                finally:
                    # Enqueue the events.
                    terminated_kernel_ids = ",".join([
                        str(kid) for kid in terminated_kernels.keys()
                    ])
                    if terminated_kernel_ids:
                        log.debug(f"Terminate kernels(ids:[{terminated_kernel_ids}])")
                    for kernel_id, ev in terminated_kernels.items():
                        await self.container_lifecycle_queue.put(ev)

                    # Set container count
                    await self.set_container_count(len(own_kernels.keys()))
        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError:
            log.warning("sync_container_lifecycles() timeout, continuing")
        except Exception as e:
            log.exception(f"sync_container_lifecycles() failure, continuing (detail: {repr(e)})")
            await self.produce_error_event()

    async def set_container_count(self, container_count: int) -> None:
        await redis_helper.execute(
            self.redis_stat_pool, lambda r: r.set(f"container_count.{self.id}", container_count)
        )

    async def clean_all_kernels(self, blocking: bool = False) -> None:
        kernel_ids = [*self.kernel_registry.keys()]
        clean_events = {}
        loop = asyncio.get_running_loop()
        if blocking:
            for kernel_id in kernel_ids:
                clean_events[kernel_id] = loop.create_future()
        for kernel_id in kernel_ids:
            await self.inject_container_lifecycle_event(
                kernel_id,
                self.kernel_registry[kernel_id].session_id,
                LifecycleEvent.DESTROY,
                KernelLifecycleEventReason.AGENT_TERMINATION,
                done_future=clean_events[kernel_id] if blocking else None,
            )
        if blocking:
            waiters = [clean_events[kernel_id] for kernel_id in kernel_ids]
            await asyncio.gather(*waiters)

    @abstractmethod
    async def load_resources(
        self,
    ) -> Mapping[DeviceName, AbstractComputePlugin]:
        """
        Detect available resources attached on the system and load corresponding device plugin.
        """

    @abstractmethod
    async def scan_available_resources(
        self,
    ) -> Mapping[SlotName, Decimal]:
        """
        Scan and define the amount of available resource slots in this node.
        """

    async def update_slots(
        self,
        interval: float,
    ) -> None:
        self.slots = await self.scan_available_resources()
        log.debug("slots: {!r}", self.slots)

    async def gather_hwinfo(self) -> Mapping[str, HardwareMetadata]:
        """
        Collect the hardware metadata from the compute plugins.
        """
        hwinfo: Dict[str, HardwareMetadata] = {}
        tasks: list[Awaitable[tuple[DeviceName, Exception | HardwareMetadata]]] = []

        async def _get(
            key: DeviceName,
            plugin: AbstractComputePlugin,
        ) -> tuple[DeviceName, Exception | HardwareMetadata]:
            try:
                result = await plugin.get_node_hwinfo()
                return key, result
            except Exception as e:
                return key, e

        for device_name, plugin in self.computers.items():
            tasks.append(_get(device_name, plugin.instance))
        results = await asyncio.gather(*tasks)
        for device_name, result in results:
            match result:
                case NotImplementedError():
                    continue
                case Exception():
                    hwinfo[device_name] = {
                        "status": "unavailable",
                        "status_info": str(result),
                        "metadata": {},
                    }
                case dict():  # HardwareMetadata
                    hwinfo[device_name] = result
        return hwinfo

    async def _cleanup_reported_kernels(self, interval: float):
        # dest_path == abuse_report_path
        dest_path: Path = self.local_config["agent"]["abuse-report-path"]
        auto_terminate: bool = self.local_config["agent"].get(
            "force-terminate-abusing-containers", False
        )

        def _read(path: Path) -> str:
            with open(path, "r") as fr:
                return fr.read()

        def _rm(path: Path) -> None:
            os.remove(path)

        terminated_kernels: dict[str, ContainerLifecycleEvent] = {}
        abuse_report: dict[str, str] = {}
        try:
            async with FileLock(path=dest_path / "report.lock"):
                for reported_kernel in dest_path.glob("report.*.json"):
                    raw_body = await self.loop.run_in_executor(None, _read, reported_kernel)
                    body: dict[str, str] = json.loads(raw_body)
                    kern_id = body["ID"]
                    if auto_terminate:
                        log.debug("cleanup requested: {} ({})", body["ID"], body.get("reason"))
                        kernel_id = KernelId(UUID(body["ID"]))
                        kernel_obj = self.kernel_registry.get(kernel_id)
                        if kernel_obj is None:
                            continue
                        abuse_report[kern_id] = AbuseReportValue.CLEANING.value
                        session_id = kernel_obj.session_id
                        terminated_kernels[body["ID"]] = ContainerLifecycleEvent(
                            kernel_id,
                            session_id,
                            ContainerId(body["CID"]),
                            LifecycleEvent.DESTROY,
                            KernelLifecycleEventReason.from_value(body.get("reason"))
                            or KernelLifecycleEventReason.ANOMALY_DETECTED,
                        )
                        await self.loop.run_in_executor(None, _rm, reported_kernel)
                    else:
                        abuse_report[kern_id] = AbuseReportValue.DETECTED.value
                        log.debug(
                            "abusing container detected, skipping auto-termination: {} ({})",
                            kern_id,
                            body.get("reason"),
                        )
        except Exception:
            log.exception("error while paring abuse reports:")
        finally:
            for kid, ev in terminated_kernels.items():
                await self.container_lifecycle_queue.put(ev)

            hash_name = "abuse_report"
            abuse_report_script = textwrap.dedent(
                """
                local key = KEYS[1]
                local new_report = cjson.decode(ARGV[1])

                -- Delete dangling reports
                local all_report = redis.call('HKEYS', key)
                if all_report ~= nil and next(all_report) ~= nil then
                    for _, v in ipairs(all_report) do
                        if next(all_report) == nil or not new_report[v] then
                            redis.call('HDEL', key, v)
                        end
                    end
                end

                -- Update new reports
                if next(new_report) ~= nil then
                    for kern_id, report_val in pairs(new_report) do
                        redis.call('HSET', key, kern_id, report_val)
                    end
                end
            """
            )
            await redis_helper.execute_script(
                self.redis_stat_pool,
                "report_abusing_kernels",
                abuse_report_script,
                [hash_name],
                [json.dumps(abuse_report)],
            )

    @abstractmethod
    async def scan_images(self) -> Mapping[str, str]:
        """
        Scan the available kernel images/templates and update ``self.images``.
        This is called periodically to keep the image list up-to-date and allow
        manual image addition and deletions by admins.
        """

    async def _scan_images_wrapper(self, interval: float) -> None:
        self.images = await self.scan_images()

    @abstractmethod
    async def push_image(self, image_ref: ImageRef, registry_conf: ImageRegistry) -> None:
        """
        Push the given image to the given registry.
        """

    @abstractmethod
    async def pull_image(self, image_ref: ImageRef, registry_conf: ImageRegistry) -> None:
        """
        Pull the given image from the given registry.
        """

    @abstractmethod
    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        """
        Check the availability of the image and return a boolean flag that indicates whether
        the agent should try pulling the image from a registry.
        """
        return False

    async def scan_running_kernels(self) -> None:
        """
        Scan currently running kernels and recreate the kernel objects in
        ``self.kernel_registry`` if any missing.
        """
        ipc_base_path = self.local_config["agent"]["ipc-base-path"]
        var_base_path = self.local_config["agent"]["var-base-path"]
        last_registry_file = f"last_registry.{self.local_instance_id}.dat"
        if os.path.isfile(ipc_base_path / last_registry_file):
            shutil.move(ipc_base_path / last_registry_file, var_base_path / last_registry_file)
        try:
            with open(var_base_path / last_registry_file, "rb") as f:
                self.kernel_registry = pickle.load(f)
        except EOFError:
            log.warning(
                "Failed to load the last kernel registry: {}", (var_base_path / last_registry_file)
            )
        except FileNotFoundError:
            pass
        for kernel_obj in self.kernel_registry.values():
            kernel_obj.agent_config = self.local_config
            if kernel_obj.runner is not None:
                kernel_obj.runner.event_producer = self.event_producer
                await kernel_obj.runner.__ainit__()
        async with self.registry_lock:
            for kernel_id, container in await self.enumerate_containers(
                ACTIVE_STATUS_SET | DEAD_STATUS_SET,
            ):
                session_id = SessionId(UUID(container.labels["ai.backend.session-id"]))
                if container.status in ACTIVE_STATUS_SET:
                    kernelspec = int(container.labels.get("ai.backend.kernelspec", "1"))
                    if not (MIN_KERNELSPEC <= kernelspec <= MAX_KERNELSPEC):
                        continue
                    # Consume the port pool.
                    for p in container.ports:
                        if p.host_port is not None:
                            self.port_pool.discard(p.host_port)
                    # Restore compute resources.
                    async with self.resource_lock:
                        for computer_ctx in self.computers.values():
                            await computer_ctx.instance.restore_from_container(
                                container,
                                computer_ctx.alloc_map,
                            )
                    await self.inject_container_lifecycle_event(
                        kernel_id,
                        session_id,
                        LifecycleEvent.START,
                        KernelLifecycleEventReason.RESUMING_AGENT_OPERATION,
                        container_id=container.id,
                    )
                elif container.status in DEAD_STATUS_SET:
                    log.info(
                        "detected dead container while agent is down (k:{}, c:{})",
                        kernel_id,
                        container.id,
                    )
                    await self.inject_container_lifecycle_event(
                        kernel_id,
                        session_id,
                        LifecycleEvent.CLEAN,
                        KernelLifecycleEventReason.SELF_TERMINATED,
                        container_id=container.id,
                    )

        log.info("starting with resource allocations")
        for computer_name, computer_ctx in self.computers.items():
            log.info("{}: {!r}", computer_name, dict(computer_ctx.alloc_map.allocations))

    @abstractmethod
    async def init_kernel_context(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        kernel_config: KernelCreationConfig,
        *,
        restarting: bool = False,
        cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping] = None,
    ) -> AbstractKernelCreationContext:
        raise NotImplementedError

    async def execute_batch(
        self,
        session_id: SessionId,
        kernel_id: KernelId,
        startup_command: str,
    ) -> None:
        kernel_obj = self.kernel_registry.get(kernel_id, None)
        if kernel_obj is None:
            log.warning("execute_batch(k:{}): no such kernel", kernel_id)
            return
        log.debug("execute_batch(k:{}): executing {!r}", kernel_id, (startup_command or "")[:60])
        mode: Literal["batch", "continue"] = "batch"
        opts = {
            "exec": startup_command,
        }
        try:
            while True:
                try:
                    result = await self.execute(
                        session_id,
                        kernel_id,
                        "batch-job",  # a reserved run ID
                        mode,
                        "",
                        opts=opts,
                        flush_timeout=1.0,
                        api_version=3,
                    )
                except KeyError:
                    await self.produce_event(
                        KernelTerminatedEvent(
                            kernel_id, session_id, reason=KernelLifecycleEventReason.SELF_TERMINATED
                        ),
                    )
                    break

                if result["status"] == "finished":
                    if result["exitCode"] == 0:
                        await self.produce_event(
                            SessionSuccessEvent(
                                session_id, KernelLifecycleEventReason.TASK_DONE, 0
                            ),
                        )
                    else:
                        await self.produce_event(
                            SessionFailureEvent(
                                session_id,
                                KernelLifecycleEventReason.TASK_FAILED,
                                result["exitCode"],
                            ),
                        )
                    break
                if result["status"] == "exec-timeout":
                    await self.produce_event(
                        SessionFailureEvent(
                            session_id, KernelLifecycleEventReason.TASK_TIMEOUT, -2
                        ),
                    )
                    break
                opts = {
                    "exec": "",
                }
                mode = "continue"
        except asyncio.CancelledError:
            await self.produce_event(
                SessionFailureEvent(session_id, KernelLifecycleEventReason.TASK_CANCELLED, -2),
            )

    async def create_batch_execution_task(
        self,
        session_id: SessionId,
        kernel_id: KernelId,
        code_to_execute: str,
    ) -> None:
        self._ongoing_exec_batch_tasks.add(
            asyncio.create_task(
                self.execute_batch(session_id, kernel_id, code_to_execute),
            ),
        )

    async def create_kernel(
        self,
        session_id: SessionId,
        kernel_id: KernelId,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        restarting: bool = False,
        throttle_sema: Optional[asyncio.Semaphore] = None,
    ) -> KernelCreationResult:
        """
        Create a new kernel.
        """
        if throttle_sema is None:
            # make a local semaphore
            throttle_sema = asyncio.Semaphore(1)
        async with throttle_sema:
            if not restarting:
                await self.produce_event(
                    KernelPreparingEvent(kernel_id, session_id),
                )

            # Initialize the creation context
            if self.local_config["debug"]["log-kernel-config"]:
                log.debug("Kernel creation config: {0}", pretty(kernel_config))
            ctx = await self.init_kernel_context(
                kernel_id,
                session_id,
                kernel_config,
                restarting=restarting,
                cluster_ssh_port_mapping=cluster_info.get("cluster_ssh_port_mapping"),
            )
            environ: MutableMapping[str, str] = {**kernel_config["environ"]}

            # Inject Backend.AI-intrinsic env-variables for gosu
            if KernelFeatures.UID_MATCH in ctx.kernel_features:
                uid = self.local_config["container"]["kernel-uid"]
                gid = self.local_config["container"]["kernel-gid"]
                environ["LOCAL_USER_ID"] = str(uid)
                environ["LOCAL_GROUP_ID"] = str(gid)
            environ.update(
                await ctx.get_extra_envs(),
            )
            image_labels = kernel_config["image"]["labels"]

            agent_architecture = get_arch_name()
            if agent_architecture != ctx.image_ref.architecture:
                # disable running different architecture's image
                raise AgentError(
                    f"cannot run {ctx.image_ref.architecture} image on"
                    f" {agent_architecture} machine",
                )

            # Check if we need to pull the container image
            do_pull = (not ctx.image_ref.is_local) and await self.check_image(
                ctx.image_ref,
                kernel_config["image"]["digest"],
                AutoPullBehavior(kernel_config.get("auto_pull", "digest")),
            )
            if do_pull:
                await self.produce_event(
                    KernelPullingEvent(kernel_id, session_id, ctx.image_ref.canonical),
                )
                await self.pull_image(ctx.image_ref, kernel_config["image"]["registry"])

            if not restarting:
                await self.produce_event(
                    KernelCreatingEvent(kernel_id, session_id),
                )

            # Get the resource spec from existing kernel scratches
            # or create a new resource spec from ctx.kernel_config
            resource_spec, resource_opts = await ctx.prepare_resource_spec()
            # When creating a new kernel,
            # we need to allocate agent resources, prepare the networks,
            # adn specify the container mounts.

            # Mount backend-specific intrinsic mounts (e.g., scratch directories)
            if not restarting:
                resource_spec.mounts.extend(
                    await ctx.get_intrinsic_mounts(),
                )

            # Realize ComputeDevice (including accelerators) allocations.
            if not restarting:
                alloc_order = [
                    DeviceName(name) for name in self.local_config["resource"]["allocation-order"]
                ]
                async with self.resource_lock:
                    try:
                        allocate(
                            self.computers,
                            resource_spec,
                            alloc_order,
                            self.affinity_map,
                            self.local_config["resource"]["affinity-policy"],
                        )
                    except ResourceError:
                        await self.produce_event(DoAgentResourceCheckEvent(ctx.agent_id))
                        raise
            try:
                # Prepare scratch spaces and dotfiles inside it.
                if not restarting:
                    await ctx.prepare_scratch()

                # Prepare networking.
                await ctx.apply_network(cluster_info)
                await ctx.prepare_ssh(cluster_info)

                # Mount vfolders and krunner stuffs.
                vfolder_mounts = [VFolderMount.from_json(item) for item in kernel_config["mounts"]]
                if not restarting:
                    await ctx.mount_vfolders(vfolder_mounts, resource_spec)
                    await ctx.mount_krunner(resource_spec, environ)

                # Inject Backend.AI-intrinsic env-variables for libbaihook and gosu
                label_envs_corecount = image_labels.get("ai.backend.envs.corecount", "")
                envs_corecount = label_envs_corecount.split(",") if label_envs_corecount else []
                cpu_core_count = len(resource_spec.allocations[DeviceName("cpu")][SlotName("cpu")])
                environ.update({k: str(cpu_core_count) for k in envs_corecount if k not in environ})

                # Realize mounts.
                await ctx.process_mounts(resource_spec.mounts)

                # Get attached devices information (including model_name).
                attached_devices = {}
                for dev_name, device_alloc in resource_spec.allocations.items():
                    computer_ctx = self.computers[dev_name]
                    devices = await computer_ctx.instance.get_attached_devices(device_alloc)
                    attached_devices[dev_name] = devices

                exposed_ports = [2000, 2001]
                service_ports: List[ServicePort] = []
                port_map: Dict[str, ServicePort] = {}
                preopen_ports = ctx.kernel_config.get("preopen_ports")
                if preopen_ports is None:
                    preopen_ports = []

                service_ports.append({
                    "name": "sshd",
                    "protocol": ServicePortProtocols.TCP,
                    "container_ports": (2200,),
                    "host_ports": (None,),
                    "is_inference": False,
                })
                service_ports.append({
                    "name": "ttyd",
                    "protocol": ServicePortProtocols.HTTP,
                    "container_ports": (7681,),
                    "host_ports": (None,),
                    "is_inference": False,
                })

                model_definition: Optional[Mapping[str, Any]] = None
                # Read model config
                model_folders = [
                    folder
                    for folder in vfolder_mounts
                    if folder.usage_mode == VFolderUsageMode.MODEL
                ]

                if ctx.kernel_config["cluster_role"] in ("main", "master"):
                    for sport in parse_service_ports(
                        image_labels.get("ai.backend.service-ports", ""),
                        image_labels.get("ai.backend.endpoint-ports", ""),
                    ):
                        port_map[sport["name"]] = sport
                    for port_no in preopen_ports:
                        if port_no in (2000, 2001):
                            raise AgentError("Port 2000 and 2001 are reserved for internal use")
                        overlapping_services = [
                            s for s in service_ports if port_no in s["container_ports"]
                        ]
                        if len(overlapping_services) > 0:
                            raise AgentError(
                                f"Port {port_no} overlaps with built-in service"
                                f" {overlapping_services[0]['name']}"
                            )

                        preopen_sport: ServicePort = {
                            "name": str(port_no),
                            "protocol": ServicePortProtocols.PREOPEN,
                            "container_ports": (port_no,),
                            "host_ports": (None,),
                            "is_inference": False,
                        }
                        service_ports.append(preopen_sport)
                        for cport in preopen_sport["container_ports"]:
                            exposed_ports.append(cport)
                    for sport in port_map.values():
                        service_ports.append(sport)
                        for cport in sport["container_ports"]:
                            exposed_ports.append(cport)
                    for index, port in enumerate(ctx.kernel_config["allocated_host_ports"]):
                        service_ports.append({
                            "name": f"hostport{index+1}",
                            "protocol": ServicePortProtocols.INTERNAL,
                            "container_ports": (port,),
                            "host_ports": (port,),
                            "is_inference": False,
                        })
                        exposed_ports.append(port)
                    log.debug("exposed ports: {!r}", exposed_ports)
                if kernel_config["session_type"] == SessionTypes.INFERENCE:
                    model_definition = await self.load_model_definition(
                        RuntimeVariant(
                            (kernel_config["internal_data"] or {}).get("runtime_variant", "custom")
                        ),
                        model_folders,
                        environ,
                        service_ports,
                        kernel_config,
                    )

                runtime_type = image_labels.get("ai.backend.runtime-type", "app")
                runtime_path = image_labels.get("ai.backend.runtime-path", None)
                cmdargs: list[str] = []
                krunner_opts: list[str] = []
                if self.local_config["container"]["sandbox-type"] == "jail":
                    cmdargs += [
                        "/opt/kernel/jail",
                        # "--policy",
                        # "/etc/backend.ai/jail/policy.yml",
                        # TODO: Update default Jail policy in images
                    ]
                    if self.local_config["container"]["jail-args"]:
                        cmdargs += map(
                            lambda s: s.strip(), self.local_config["container"]["jail-args"]
                        )
                    cmdargs += ["--"]
                if self.local_config["debug"]["kernel-runner"]:
                    krunner_opts.append("--debug")
                cmdargs += [
                    "/opt/backend.ai/bin/python",
                    "-s",
                    "-m",
                    "ai.backend.kernel",
                    *krunner_opts,
                    runtime_type,
                ]
                if runtime_path is not None:
                    cmdargs.append(runtime_path)

                # Store information required for restarts.
                # NOTE: kconfig may be updated after restarts.
                resource_spec.freeze()
                await self.restart_kernel__store_config(
                    kernel_id,
                    "kconfig.dat",
                    pickle.dumps(ctx.kernel_config),
                )
                if not restarting:
                    await self.restart_kernel__store_config(
                        kernel_id,
                        "cluster.json",
                        json.dumps(cluster_info).encode("utf8"),
                    )

                if self.local_config["debug"]["log-kernel-config"]:
                    log.info(
                        "kernel starting with resource spec: \n{0}",
                        pretty(attrs.asdict(resource_spec)),
                    )
                kernel_obj: KernelObjectType = await ctx.spawn(
                    resource_spec,
                    environ,
                    service_ports,
                )
                async with self.registry_lock:
                    self.kernel_registry[kernel_id] = kernel_obj
                try:
                    container_data = await ctx.start_container(
                        kernel_obj,
                        cmdargs,
                        resource_opts,
                        preopen_ports,
                    )
                except ContainerCreationError as e:
                    msg = e.message or "unknown"
                    log.error(
                        "Kernel failed to create container. Kernel is going to be destroyed."
                        f" (k:{kernel_id}, detail:{msg})",
                    )
                    cid = e.container_id
                    async with self.registry_lock:
                        self.kernel_registry[ctx.kernel_id]["container_id"] = cid
                    await self.inject_container_lifecycle_event(
                        kernel_id,
                        session_id,
                        LifecycleEvent.DESTROY,
                        KernelLifecycleEventReason.FAILED_TO_CREATE,
                        container_id=ContainerId(cid),
                    )
                    raise AgentError(
                        f"Kernel failed to create container (k:{str(ctx.kernel_id)}, detail:{msg})"
                    )
                except Exception as e:
                    log.warning(
                        "Kernel failed to create container (k:{}). Kernel is going to be destroyed.",
                        kernel_id,
                    )
                    await self.inject_container_lifecycle_event(
                        kernel_id,
                        session_id,
                        LifecycleEvent.DESTROY,
                        KernelLifecycleEventReason.FAILED_TO_CREATE,
                    )
                    raise AgentError(
                        f"Kernel failed to create container (k:{str(kernel_id)}, detail: {str(e)})"
                    )
                async with self.registry_lock:
                    self.kernel_registry[kernel_id].data.update(container_data)
                await kernel_obj.init(self.event_producer)

                current_task = asyncio.current_task()
                assert current_task is not None
                self._pending_creation_tasks[kernel_id].add(current_task)
                try:
                    async for attempt in AsyncRetrying(
                        wait=wait_fixed(0.3),
                        stop=(stop_after_attempt(10) | stop_after_delay(60)),
                        retry=retry_if_exception_type(zmq.error.ZMQError),
                    ):
                        with attempt:
                            # Wait until bootstrap script is executed.
                            # - Main kernel runner is executed after bootstrap script, and
                            #   check_status is accessible only after kernel runner is loaded.
                            await kernel_obj.check_status()
                            # Update the service-ports metadata from the image labels
                            # with the extended template metadata from the agent and krunner.
                            live_services = await kernel_obj.get_service_apps()
                            if live_services["status"] != "failed":
                                for live_service in live_services["data"]:
                                    for service_port in service_ports:
                                        if live_service["name"] == service_port["name"]:
                                            service_port.update(live_service)
                                            break
                    if self.local_config["debug"]["log-kernel-config"]:
                        log.debug("service ports:\n{!r}", pretty(service_ports))
                except asyncio.CancelledError:
                    log.warning("cancelled waiting of container startup (k:{})", kernel_id)
                    raise
                except Exception:
                    log.exception(
                        "unexpected error while waiting container startup (k:{})", kernel_id
                    )
                    raise RuntimeError(
                        "cancelled waiting of container startup due to initialization failure",
                    )
                finally:
                    self._pending_creation_tasks[kernel_id].remove(current_task)
                    if not self._pending_creation_tasks[kernel_id]:
                        del self._pending_creation_tasks[kernel_id]

                public_service_ports: List[ServicePort] = self.get_public_service_ports(
                    service_ports
                )

                kernel_creation_info: KernelCreationResult = {
                    "id": KernelId(kernel_id),
                    "kernel_host": str(kernel_obj["kernel_host"]),
                    "repl_in_port": kernel_obj["repl_in_port"],
                    "repl_out_port": kernel_obj["repl_out_port"],
                    "stdin_port": kernel_obj["stdin_port"],  # legacy
                    "stdout_port": kernel_obj["stdout_port"],  # legacy
                    "service_ports": public_service_ports,
                    "container_id": kernel_obj["container_id"],
                    "resource_spec": attrs.asdict(resource_spec),
                    "scaling_group": kernel_config["scaling_group"],
                    "agent_addr": kernel_config["agent_addr"],
                    "attached_devices": attached_devices,
                }

                if ctx.kernel_config["cluster_role"] in ("main", "master") and model_definition:
                    for model in model_definition["models"]:
                        asyncio.create_task(
                            self.start_and_monitor_model_service_health(kernel_obj, model)
                        )

                # Finally we are done.
                await self.produce_event(
                    KernelStartedEvent(
                        kernel_id,
                        session_id,
                        creation_info={
                            **kernel_creation_info,
                            "id": str(KernelId(kernel_id)),
                            "container_id": str(kernel_obj["container_id"]),
                        },
                    ),
                )
                async with self.registry_lock:
                    kernel_obj.state = KernelLifecycleStatus.RUNNING

                # The startup command for the batch-type sessions will be executed by the manager
                # upon firing of the "session_started" event.
                return kernel_creation_info
            except Exception as e:
                await self.reconstruct_resource_usage()
                raise e

    async def start_and_monitor_model_service_health(
        self,
        kernel_obj: KernelObjectType,
        model: Any,
    ) -> None:
        log.debug("starting model service of model {}", model["name"])
        result = await kernel_obj.start_model_service(model)
        if result["status"] == "failed":
            # handle cases where krunner fails to spawn model service process
            # if everything went well then krunner itself will report the status via zmq
            await self.event_producer.produce_event(
                ModelServiceStatusEvent(
                    kernel_obj.kernel_id,
                    kernel_obj.session_id,
                    model["name"],
                    ModelServiceStatus.UNHEALTHY,
                )
            )

    async def load_model_definition(
        self,
        runtime_variant: RuntimeVariant,
        model_folders: list[VFolderMount],
        environ: MutableMapping[str, Any],
        service_ports: list[ServicePort],
        kernel_config: KernelCreationConfig,
    ) -> Any:
        image_command = await self.extract_image_command(kernel_config["image"]["canonical"])
        if runtime_variant != RuntimeVariant.CUSTOM and not image_command:
            raise AgentError(
                "image should have its own command when runtime variant is set to values other than CUSTOM!"
            )
        assert len(model_folders) > 0
        model_folder: VFolderMount = model_folders[0]

        match runtime_variant:
            case RuntimeVariant.VLLM:
                _model = {
                    "name": "vllm-model",
                    "model_path": model_folder.kernel_path.as_posix(),
                    "service": {
                        "start_command": image_command,
                        "port": MODEL_SERVICE_RUNTIME_PROFILES[RuntimeVariant.VLLM].port,
                        "health_check": {
                            "path": MODEL_SERVICE_RUNTIME_PROFILES[
                                RuntimeVariant.VLLM
                            ].health_check_endpoint,
                        },
                    },
                }
                raw_definition = {"models": [_model]}

            case RuntimeVariant.NIM:
                _model = {
                    "name": "nim-model",
                    "model_path": model_folder.kernel_path.as_posix(),
                    "service": {
                        "start_command": image_command,
                        "port": MODEL_SERVICE_RUNTIME_PROFILES[RuntimeVariant.NIM].port,
                        "health_check": {
                            "path": MODEL_SERVICE_RUNTIME_PROFILES[
                                RuntimeVariant.NIM
                            ].health_check_endpoint,
                        },
                    },
                }
                raw_definition = {"models": [_model]}

            case RuntimeVariant.CMD:
                _model = {
                    "name": "image-model",
                    "model_path": model_folder.kernel_path.as_posix(),
                    "service": {
                        "start_command": image_command,
                        "port": 8000,
                    },
                }
                raw_definition = {"models": [_model]}

            case RuntimeVariant.CUSTOM:
                if _fname := (kernel_config.get("internal_data") or {}).get(
                    "model_definition_path"
                ):
                    model_definition_candidates = [_fname]
                else:
                    model_definition_candidates = [
                        "model-definition.yaml",
                        "model-definition.yml",
                    ]

                model_definition_path = None
                for filename in model_definition_candidates:
                    if (Path(model_folder.host_path) / filename).is_file():
                        model_definition_path = Path(model_folder.host_path) / filename
                        break

                if not model_definition_path:
                    raise AgentError(
                        f"Model definition file ({" or ".join(model_definition_candidates)}) does not exist under vFolder"
                        f" {model_folder.name} (ID {model_folder.vfid})",
                    )
                try:
                    model_definition_yaml = await asyncio.get_running_loop().run_in_executor(
                        None, model_definition_path.read_text
                    )
                except FileNotFoundError as e:
                    raise AgentError(
                        "Model definition file (model-definition.yml) does not exist under"
                        f" vFolder {model_folder.name} (ID {model_folder.vfid})",
                    ) from e
                try:
                    raw_definition = yaml.load(model_definition_yaml, Loader=yaml.FullLoader)
                except yaml.error.YAMLError as e:
                    raise AgentError(f"Invalid YAML syntax: {e}") from e
        try:
            model_definition = model_definition_iv.check(raw_definition)
            assert model_definition is not None
            for model in model_definition["models"]:
                if "BACKEND_MODEL_NAME" not in environ:
                    environ["BACKEND_MODEL_NAME"] = model["name"]
                environ["BACKEND_MODEL_PATH"] = model["model_path"]
                if service := model.get("service"):
                    if service["port"] in (2000, 2001):
                        raise AgentError("Port 2000 and 2001 are reserved for internal use")
                    overlapping_services = [
                        s for s in service_ports if service["port"] in s["container_ports"]
                    ]
                    if len(overlapping_services) > 0:
                        raise AgentError(
                            f"Port {service['port']} overlaps with built-in service"
                            f" {overlapping_services[0]['name']}"
                        )
                    service_ports.append({
                        "name": f"{model['name']}-{service['port']}",
                        "protocol": ServicePortProtocols.PREOPEN,
                        "container_ports": (service["port"],),
                        "host_ports": (None,),
                        "is_inference": True,
                    })
            return model_definition
        except DataError as e:
            raise AgentError(
                "Failed to validate model definition from vFolder"
                f" {model_folder.name} (ID {model_folder.vfid})",
            ) from e

    def get_public_service_ports(self, service_ports: list[ServicePort]) -> list[ServicePort]:
        return [port for port in service_ports if port["protocol"] != ServicePortProtocols.INTERNAL]

    @abstractmethod
    async def extract_image_command(self, image_ref: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def destroy_kernel(
        self,
        kernel_id: KernelId,
        container_id: Optional[ContainerId],
    ) -> None:
        """
        Initiate destruction of the kernel.

        Things to do:
        * Send SIGTERM to the kernel's main process.
        * Send SIGKILL if it's not terminated within a few seconds.
        """

    @abstractmethod
    async def clean_kernel(
        self,
        kernel_id: KernelId,
        container_id: Optional[ContainerId],
        restarting: bool,
    ) -> None:
        """
        Clean up kernel-related book-keepers when the underlying
        implementation detects an event that the kernel has terminated.

        Things to do:
        * Call :meth:`self.collect_logs()` to store the container's console outputs.
        * Delete the underlying kernel resource (e.g., container)
        * Release host-specific resources used for the kernel (e.g., scratch spaces)

        This method is intended to be called asynchronously by the implementation-specific
        event monitoring routine.

        The ``container_id`` may be ``None`` if the container has already gone away.
        In such cases, skip container-specific cleanups.
        """

    @abstractmethod
    async def create_local_network(self, network_name: str) -> None:
        """
        Create a local bridge network for a single-node multicontainer session, where containers in the
        same agent can connect to each other using cluster hostnames without explicit port mapping.

        This is called by the manager before kernel creation.
        It may raise :exc:`NotImplementedError` and then the manager
        will cancel creation of the session.
        """

    @abstractmethod
    async def destroy_local_network(self, network_name: str) -> None:
        """
        Destroy a local bridge network used for a single-node multi-container session.

        This is called by the manager after kernel destruction.
        """

    @abstractmethod
    async def restart_kernel__load_config(
        self,
        kernel_id: KernelId,
        name: str,
    ) -> bytes:
        """
        Restore the cluster config from a previous launch of the kernel.
        """
        pass

    @abstractmethod
    async def restart_kernel__store_config(
        self,
        kernel_id: KernelId,
        name: str,
        data: bytes,
    ) -> None:
        """
        Store the cluster config to a kernel-related storage (e.g., scratch space),
        so that restarts of this kernel can reuse the configuration.
        """
        pass

    async def restart_kernel(
        self,
        session_id: SessionId,
        kernel_id: KernelId,
        updating_kernel_config: KernelCreationConfig,
    ):
        tracker = self.restarting_kernels.get(kernel_id)
        if tracker is None:
            tracker = RestartTracker(
                request_lock=asyncio.Lock(),
                destroy_event=asyncio.Event(),
                done_event=asyncio.Event(),
            )
            self.restarting_kernels[kernel_id] = tracker

        existing_kernel_config = pickle.loads(
            await self.restart_kernel__load_config(kernel_id, "kconfig.dat"),
        )
        existing_cluster_info = json.loads(
            await self.restart_kernel__load_config(kernel_id, "cluster.json"),
        )
        kernel_config = cast(
            KernelCreationConfig,
            {**existing_kernel_config, **updating_kernel_config},
        )
        async with tracker.request_lock:
            tracker.done_event.clear()
            await self.inject_container_lifecycle_event(
                kernel_id,
                session_id,
                LifecycleEvent.DESTROY,
                KernelLifecycleEventReason.RESTARTING,
            )
            try:
                with timeout(60):
                    await tracker.destroy_event.wait()
            except asyncio.TimeoutError:
                log.warning("timeout detected while restarting kernel {0}!", kernel_id)
                self.restarting_kernels.pop(kernel_id, None)
                await self.inject_container_lifecycle_event(
                    kernel_id,
                    session_id,
                    LifecycleEvent.CLEAN,
                    KernelLifecycleEventReason.RESTART_TIMEOUT,
                )
                raise
            else:
                try:
                    await self.create_kernel(
                        session_id,
                        kernel_id,
                        kernel_config,
                        existing_cluster_info,
                        restarting=True,
                    )
                    self.restarting_kernels.pop(kernel_id, None)
                except Exception:
                    # TODO: retry / cancel others?
                    log.exception(
                        "restart_kernel(s:{}, k:{}): re-creation failure", session_id, kernel_id
                    )
            tracker.done_event.set()
        kernel_obj = self.kernel_registry[kernel_id]
        return {
            "container_id": kernel_obj["container_id"],
            "repl_in_port": kernel_obj["repl_in_port"],
            "repl_out_port": kernel_obj["repl_out_port"],
            "stdin_port": kernel_obj["stdin_port"],
            "stdout_port": kernel_obj["stdout_port"],
            "service_ports": kernel_obj.service_ports,
        }

    async def execute(
        self,
        session_id: SessionId,
        kernel_id: KernelId,
        run_id: Optional[str],
        mode: Literal["query", "batch", "input", "continue"],
        text: str,
        *,
        opts: Mapping[str, Any],
        api_version: int,
        flush_timeout: float,
    ):
        # Wait for the kernel restarting if it's ongoing...
        restart_tracker = self.restarting_kernels.get(kernel_id)
        if restart_tracker is not None:
            await restart_tracker.done_event.wait()

        await self.produce_event(
            ExecutionStartedEvent(session_id),
        )
        try:
            kernel_obj = self.kernel_registry[kernel_id]
            result = await kernel_obj.execute(
                run_id, mode, text, opts=opts, flush_timeout=flush_timeout, api_version=api_version
            )
        except asyncio.CancelledError:
            await self.produce_event(
                ExecutionCancelledEvent(session_id),
            )
            raise
        except KeyError:
            # This situation is handled in the lifecycle management subsystem.
            raise RuntimeError(
                f"The container for kernel {kernel_id} is not found! "
                "(might be terminated--try it again)"
            ) from None

        if result["status"] in ("finished", "exec-timeout"):
            log.debug("_execute({0}) {1}", kernel_id, result["status"])
        if result["status"] == "finished":
            await self.produce_event(
                ExecutionFinishedEvent(session_id),
            )
        elif result["status"] == "exec-timeout":
            await self.produce_event(
                ExecutionTimeoutEvent(session_id),
            )
            await self.inject_container_lifecycle_event(
                kernel_id,
                session_id,
                LifecycleEvent.DESTROY,
                KernelLifecycleEventReason.EXEC_TIMEOUT,
            )
        return {
            **result,
            "files": [],  # kept for API backward-compatibility
        }

    async def get_completions(self, kernel_id: KernelId, text: str, opts: dict):
        return await self.kernel_registry[kernel_id].get_completions(text, opts)

    async def get_logs(self, kernel_id: KernelId):
        return await self.kernel_registry[kernel_id].get_logs()

    async def interrupt_kernel(self, kernel_id: KernelId):
        return await self.kernel_registry[kernel_id].interrupt_kernel()

    async def start_service(self, kernel_id: KernelId, service: str, opts: dict):
        return await self.kernel_registry[kernel_id].start_service(service, opts)

    async def shutdown_service(self, kernel_id: KernelId, service: str):
        try:
            kernel_obj = self.kernel_registry[kernel_id]
            if kernel_obj is not None:
                await kernel_obj.shutdown_service(service)
        except Exception:
            log.exception("unhandled exception while shutting down service app ${}", service)

    async def commit(
        self,
        reporter,
        kernel_id: KernelId,
        subdir: str,
        *,
        canonical: str | None = None,
        filename: str | None = None,
        extra_labels: dict[str, str] = {},
    ):
        return await self.kernel_registry[kernel_id].commit(
            kernel_id, subdir, canonical=canonical, filename=filename, extra_labels=extra_labels
        )

    async def get_commit_status(self, kernel_id: KernelId, subdir: str) -> CommitStatus:
        return await self.kernel_registry[kernel_id].check_duplicate_commit(kernel_id, subdir)

    async def accept_file(self, kernel_id: KernelId, filename: str, filedata):
        return await self.kernel_registry[kernel_id].accept_file(filename, filedata)

    async def download_file(self, kernel_id: KernelId, filepath: str):
        return await self.kernel_registry[kernel_id].download_file(filepath)

    async def download_single(self, kernel_id: KernelId, filepath: str):
        return await self.kernel_registry[kernel_id].download_single(filepath)

    async def list_files(self, kernel_id: KernelId, path: str):
        return await self.kernel_registry[kernel_id].list_files(path)

    async def ping_kernel(self, kernel_id: KernelId):
        return await self.kernel_registry[kernel_id].ping()

    async def save_last_registry(self, force=False) -> None:
        now = time.monotonic()
        if (not force) and (now <= self.last_registry_written_time + 60):
            return  # don't save too frequently
        var_base_path = self.local_config["agent"]["var-base-path"]
        last_registry_file = f"last_registry.{self.local_instance_id}.dat"
        try:
            with open(var_base_path / last_registry_file, "wb") as f:
                pickle.dump(self.kernel_registry, f)
            self.last_registry_written_time = now
            log.debug("saved {}", last_registry_file)
        except Exception as e:
            log.exception("unable to save {}", last_registry_file, exc_info=e)
            try:
                os.remove(var_base_path / last_registry_file)
            except FileNotFoundError:
                pass


async def handle_volume_mount(
    context: AbstractAgent,
    source: AgentId,
    event: DoVolumeMountEvent,
) -> None:
    if context.local_config["agent"]["cohabiting-storage-proxy"]:
        log.debug("Storage proxy is in the same node. Skip the volume task.")
        await context.event_producer.produce_event(
            VolumeMounted(
                str(context.id),
                VolumeMountableNodeType.AGENT,
                "",
                event.quota_scope_id,
            )
        )
        return
    mount_prefix = await context.etcd.get("volumes/_mount")
    volume_mount_prefix: str | None = context.local_config["agent"]["mount-path"]
    if volume_mount_prefix is None:
        volume_mount_prefix = "./"
    real_path = Path(volume_mount_prefix, event.dir_name)
    err_msg: str | None = None
    try:
        await mount(
            str(real_path),
            event.fs_location,
            event.fs_type,
            event.cmd_options,
            event.edit_fstab,
            event.fstab_path,
            mount_prefix,
        )
    except VolumeMountFailed as e:
        err_msg = str(e)
    await context.event_producer.produce_event(
        VolumeMounted(
            str(context.id),
            VolumeMountableNodeType.AGENT,
            str(real_path),
            event.quota_scope_id,
            err_msg,
        )
    )


async def handle_volume_umount(
    context: AbstractAgent,
    source: AgentId,
    event: DoVolumeUnmountEvent,
) -> None:
    if context.local_config["agent"]["cohabiting-storage-proxy"]:
        log.debug("Storage proxy is in the same node. Skip the volume task.")
        await context.event_producer.produce_event(
            VolumeUnmounted(
                str(context.id),
                VolumeMountableNodeType.AGENT,
                "",
                event.quota_scope_id,
            )
        )
        return
    mount_prefix = await context.etcd.get("volumes/_mount")
    timeout = await context.etcd.get("config/watcher/file-io-timeout")
    volume_mount_prefix = context.local_config["agent"]["mount-path"]
    real_path = Path(volume_mount_prefix, event.dir_name)
    err_msg: str | None = None
    try:
        did_umount = await umount(
            str(real_path),
            mount_prefix,
            event.edit_fstab,
            event.fstab_path,
            timeout_sec=float(timeout) if timeout is not None else None,
        )
    except VolumeMountFailed as e:
        err_msg = str(e)
    if not did_umount:
        log.warning(f"{real_path} does not exist. Skip umount")
    await context.event_producer.produce_event(
        VolumeUnmounted(
            str(context.id),
            VolumeMountableNodeType.AGENT,
            str(real_path),
            event.quota_scope_id,
            err_msg,
        )
    )

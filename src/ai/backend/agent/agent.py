from __future__ import annotations

from abc import ABCMeta, abstractmethod
import asyncio
from collections import defaultdict
from decimal import Decimal
from io import BytesIO, SEEK_END
import json
import logging
from pathlib import Path
import pickle
import pkg_resources
import re
import signal
import sys
import traceback
from types import TracebackType
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Collection,
    Dict,
    FrozenSet,
    Generic,
    Optional,
    List,
    Literal,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    TYPE_CHECKING,
    cast,
)
import weakref

import aioredis
import aiotools
from async_timeout import timeout
import attr
from cachetools import cached, LRUCache
import snappy
from tenacity import (
    AsyncRetrying,
    stop_after_attempt,
    stop_after_delay,
    retry_if_exception_type,
    wait_fixed,
)
import time
import zmq, zmq.asyncio

from ai.backend.common import msgpack, redis
from ai.backend.common.docker import (
    ImageRef,
    MIN_KERNELSPEC,
    MAX_KERNELSPEC,
)
from ai.backend.common.logging import BraceStyleAdapter, pretty
from ai.backend.common.types import (
    AutoPullBehavior,
    ContainerId,
    KernelId,
    SessionId,
    DeviceName,
    SlotName,
    HardwareMetadata,
    ImageRegistry,
    ClusterInfo,
    KernelCreationConfig,
    KernelCreationResult,
    MountTypes,
    MountPermission,
    Sentinel,
    ServicePortProtocols,
    VFolderMount,
    aobject,
)
from ai.backend.common.events import (
    EventProducer,
    AbstractEvent,
    AgentErrorEvent,
    AgentHeartbeatEvent,
    AgentStartedEvent,
    AgentTerminatedEvent,
    DoSyncKernelLogsEvent,
    DoSyncKernelStatsEvent,
    ExecutionCancelledEvent,
    ExecutionFinishedEvent,
    ExecutionStartedEvent,
    ExecutionTimeoutEvent,
    KernelCreatingEvent,
    KernelPreparingEvent,
    KernelPullingEvent,
    KernelStartedEvent,
    KernelTerminatedEvent,
    SessionFailureEvent,
    SessionSuccessEvent,
)
from ai.backend.common.utils import cancel_tasks, current_loop
from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext
from ai.backend.common.service_ports import parse_service_ports
from . import __version__ as VERSION
from .exception import AgentError, ResourceError
from .kernel import (
    AbstractKernel,
    KernelFeatures,
    match_distro_data,
)
from . import resources as resources_mod
from .resources import (
    AbstractComputeDevice,
    AbstractComputePlugin,
    AbstractAllocMap,
    KernelResourceSpec,
    Mount,
)
from .stats import (
    StatContext, StatModes,
)
from .types import (
    Container,
    ContainerStatus,
    ContainerLifecycleEvent,
    LifecycleEvent,
)
from .utils import (
    generate_local_instance_id,
    get_arch_name,
)

if TYPE_CHECKING:
    from ai.backend.common.etcd import AsyncEtcd

log = BraceStyleAdapter(logging.getLogger('ai.backend.agent.agent'))

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


KernelObjectType = TypeVar('KernelObjectType', bound=AbstractKernel)


class AbstractKernelCreationContext(aobject, Generic[KernelObjectType]):
    kspec_version: int
    kernel_id: KernelId
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
        kernel_config: KernelCreationConfig,
        local_config: Mapping[str, Any],
        computers: MutableMapping[str, ComputerContext],
        restarting: bool = False,
    ) -> None:
        self.image_labels = kernel_config['image']['labels']
        self.kspec_version = int(self.image_labels.get('ai.backend.kernelspec', '1'))
        self.kernel_features = frozenset(self.image_labels.get('ai.backend.features', '').split())
        self.kernel_id = kernel_id
        self.kernel_config = kernel_config
        self.image_ref = ImageRef(
            kernel_config['image']['canonical'],
            known_registries=[kernel_config['image']['registry']['name']],
            architecture=kernel_config['image'].get('architecture', get_arch_name()),
        )
        self.internal_data = kernel_config['internal_data'] or {}
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

    @abstractmethod
    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        """
        Apply the given cluster network information to the deployment.
        """
        raise NotImplementedError

    @abstractmethod
    async def install_ssh_keypair(self, cluster_info: ClusterInfo) -> None:
        """
        Install the ssh keypair inside the kernel from cluster_info.
        """
        raise NotImplementedError

    @abstractmethod
    async def process_mounts(self, mounts: Sequence[Mount]):
        raise NotImplementedError

    @abstractmethod
    async def apply_accelerator_allocation(self, computer, device_alloc) -> None:
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
        perm: Literal['ro', 'rw'] = 'ro',
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
            self.kernel_config['image']['labels'].get('ai.backend.base-distro', 'ubuntu16.04'),
        ),
    )
    def get_krunner_info(self) -> Tuple[str, str, str, str, str]:
        image_labels = self.kernel_config['image']['labels']
        distro = image_labels.get('ai.backend.base-distro', 'ubuntu16.04')
        matched_distro, krunner_volume = match_distro_data(
            self.local_config['container']['krunner-volumes'], distro)
        matched_libc_style = 'glibc'
        if distro.startswith('alpine'):
            matched_libc_style = 'musl'
        krunner_pyver = '3.6'  # fallback
        if m := re.search(r'^([a-z-]+)(\d+(\.\d+)*)?$', matched_distro):
            matched_distro_pkgname = m.group(1).replace('-', '_')
            try:
                krunner_pyver = Path(pkg_resources.resource_filename(
                    f'ai.backend.krunner.{matched_distro_pkgname}',
                    f'krunner-python.{matched_distro}.txt',
                )).read_text().strip()
            except FileNotFoundError:
                pass
        log.debug('selected krunner: {}', matched_distro)
        log.debug('selected libc style: {}', matched_libc_style)
        log.debug('krunner volume: {}', krunner_volume)
        log.debug('krunner python: {}', krunner_pyver)
        arch = get_arch_name()
        return arch, matched_distro, matched_libc_style, krunner_volume, krunner_pyver

    async def mount_vfolders(
        self,
        vfolders: Sequence[VFolderMount],
        resource_spec: KernelResourceSpec,
    ) -> None:
        for vfolder in vfolders:
            if self.internal_data.get('prevent_vfolder_mounts', False):
                # Only allow mount of ".logs" directory to prevent expose
                # internal-only information, such as Docker credentials to user's ".docker" vfolder
                # in image importer kernels.
                if vfolder.name != '.logs':
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
            type, src, dst,
        ):
            resource_spec.mounts.append(
                self.get_runner_mount(
                    type, src, dst,
                    MountPermission('ro'),
                ),
            )

        # Inject Backend.AI kernel runner dependencies.
        image_labels = self.kernel_config['image']['labels']
        distro = image_labels.get('ai.backend.base-distro', 'ubuntu16.04')

        arch, matched_distro, matched_libc_style, krunner_volume, krunner_pyver = \
            self.get_krunner_info()
        artifact_path = Path(pkg_resources.resource_filename(
            'ai.backend.agent', '../runner'))

        def find_artifacts(pattern: str) -> Mapping[str, str]:
            artifacts = {}
            for p in artifact_path.glob(pattern):
                m = self._rx_distro.search(p.name)
                if m is not None:
                    artifacts[m.group(1)] = p.name
            return artifacts

        suexec_candidates = find_artifacts(f"su-exec.*.{arch}.bin")
        _, suexec_candidate = match_distro_data(suexec_candidates, distro)
        suexec_path = self.resolve_krunner_filepath('runner/' + suexec_candidate)

        hook_candidates = find_artifacts(f"libbaihook.*.{arch}.so")
        _, hook_candidate = match_distro_data(hook_candidates, distro)
        hook_path = self.resolve_krunner_filepath('runner/' + hook_candidate)

        sftp_server_candidates = find_artifacts(f"sftp-server.*.{arch}.bin")
        _, sftp_server_candidate = match_distro_data(sftp_server_candidates, distro)
        sftp_server_path = self.resolve_krunner_filepath('runner/' + sftp_server_candidate)

        scp_candidates = find_artifacts(f"scp.*.{arch}.bin")
        _, scp_candidate = match_distro_data(scp_candidates, distro)
        scp_path = self.resolve_krunner_filepath('runner/' + scp_candidate)

        jail_path: Optional[Path]
        if self.local_config['container']['sandbox-type'] == 'jail':
            jail_candidates = find_artifacts(f"jail.*.{arch}.bin")
            _, jail_candidate = match_distro_data(jail_candidates, distro)
            jail_path = self.resolve_krunner_filepath('runner/' + jail_candidate)
        else:
            jail_path = None

        kernel_pkg_path = self.resolve_krunner_filepath('kernel')
        helpers_pkg_path = self.resolve_krunner_filepath('helpers')
        dropbear_path = self.resolve_krunner_filepath(f'runner/dropbear.{matched_libc_style}.{arch}.bin')
        dropbearconv_path = \
            self.resolve_krunner_filepath(f'runner/dropbearconvert.{matched_libc_style}.{arch}.bin')
        dropbearkey_path = \
            self.resolve_krunner_filepath(f'runner/dropbearkey.{matched_libc_style}.{arch}.bin')
        tmux_path = self.resolve_krunner_filepath(f'runner/tmux.{matched_libc_style}.{arch}.bin')
        dotfile_extractor_path = self.resolve_krunner_filepath('runner/extract_dotfiles.py')
        persistent_files_warning_doc_path = \
            self.resolve_krunner_filepath('runner/DO_NOT_STORE_PERSISTENT_FILES_HERE.md')
        entrypoint_sh_path = self.resolve_krunner_filepath('runner/entrypoint.sh')

        if matched_libc_style == 'musl':
            terminfo_path = self.resolve_krunner_filepath('runner/terminfo.alpine3.8')
            _mount(MountTypes.BIND, terminfo_path, '/home/work/.terminfo')

        _mount(MountTypes.BIND, dotfile_extractor_path, '/opt/kernel/extract_dotfiles.py')
        _mount(MountTypes.BIND, entrypoint_sh_path, '/opt/kernel/entrypoint.sh')
        _mount(MountTypes.BIND, suexec_path, '/opt/kernel/su-exec')
        if jail_path is not None:
            _mount(MountTypes.BIND, jail_path, '/opt/kernel/jail')
        _mount(MountTypes.BIND, hook_path, '/opt/kernel/libbaihook.so')
        _mount(MountTypes.BIND, dropbear_path, '/opt/kernel/dropbear')
        _mount(MountTypes.BIND, dropbearconv_path, '/opt/kernel/dropbearconvert')
        _mount(MountTypes.BIND, dropbearkey_path, '/opt/kernel/dropbearkey')
        _mount(MountTypes.BIND, tmux_path, '/opt/kernel/tmux')
        _mount(MountTypes.BIND, sftp_server_path, '/usr/libexec/sftp-server')
        _mount(MountTypes.BIND, scp_path, '/usr/bin/scp')
        _mount(MountTypes.BIND, persistent_files_warning_doc_path,
               '/home/work/DO_NOT_STORE_PERSISTENT_FILES_HERE.md')

        _mount(MountTypes.VOLUME, krunner_volume, '/opt/backend.ai')
        pylib_path = f'/opt/backend.ai/lib/python{krunner_pyver}/site-packages/'
        _mount(MountTypes.BIND, kernel_pkg_path,
                                pylib_path + 'ai/backend/kernel')
        _mount(MountTypes.BIND, helpers_pkg_path,
                                pylib_path + 'ai/backend/helpers')
        environ['LD_PRELOAD'] = '/opt/kernel/libbaihook.so'

        # Inject ComputeDevice-specific env-varibles and hooks
        already_injected_hooks: Set[Path] = set()
        for dev_type, device_alloc in resource_spec.allocations.items():
            computer_set = self.computers[dev_type]
            await self.apply_accelerator_allocation(
                computer_set.instance, device_alloc,
            )
            alloc_sum = Decimal(0)
            for dev_id, per_dev_alloc in device_alloc.items():
                alloc_sum += sum(per_dev_alloc.values())
            if alloc_sum > 0:
                hook_paths = await computer_set.instance.get_hooks(distro, arch)
                if hook_paths:
                    log.debug('accelerator {} provides hooks: {}',
                              type(computer_set.instance).__name__,
                              ', '.join(map(str, hook_paths)))
                for hook_path in map(lambda p: Path(p).absolute(), hook_paths):
                    if hook_path in already_injected_hooks:
                        continue
                    container_hook_path = f"/opt/kernel/{hook_path.name}"
                    _mount(MountTypes.BIND, hook_path, container_hook_path)
                    environ['LD_PRELOAD'] += ':' + container_hook_path
                    already_injected_hooks.add(hook_path)


KernelCreationContextType = TypeVar('KernelCreationContextType', bound=AbstractKernelCreationContext)


@attr.s(auto_attribs=True, slots=True)
class RestartTracker:
    request_lock: asyncio.Lock
    destroy_event: asyncio.Event
    done_event: asyncio.Event


@attr.s(auto_attribs=True, slots=True)
class ComputerContext:
    instance: AbstractComputePlugin
    devices: Collection[AbstractComputeDevice]
    alloc_map: AbstractAllocMap


class AbstractAgent(aobject, Generic[KernelObjectType, KernelCreationContextType], metaclass=ABCMeta):

    loop: asyncio.AbstractEventLoop
    local_config: Mapping[str, Any]
    etcd: AsyncEtcd
    local_instance_id: str
    kernel_registry: MutableMapping[KernelId, AbstractKernel]
    computers: MutableMapping[str, ComputerContext]
    images: Mapping[str, str]
    port_pool: Set[int]

    redis: aioredis.Redis
    zmq_ctx: zmq.asyncio.Context

    restarting_kernels: MutableMapping[KernelId, RestartTracker]
    terminating_kernels: Set[KernelId]
    timer_tasks: MutableSequence[asyncio.Task]
    container_lifecycle_queue: asyncio.Queue[ContainerLifecycleEvent | Sentinel]

    stat_ctx: StatContext
    stat_sync_sockpath: Path
    stat_sync_task: asyncio.Task

    stats_monitor: StatsPluginContext  # unused currently
    error_monitor: ErrorPluginContext  # unused in favor of produce_error_event()

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
    ) -> None:
        self._skip_initial_scan = skip_initial_scan
        self.loop = current_loop()
        self.etcd = etcd
        self.local_config = local_config
        self.local_instance_id = generate_local_instance_id(__file__)
        self.kernel_registry = {}
        self.computers = {}
        self.images = {}  # repoTag -> digest
        self.restarting_kernels = {}
        self.terminating_kernels = set()
        self.stat_ctx = StatContext(
            self, mode=StatModes(local_config['container']['stats-type']),
        )
        self.timer_tasks = []
        self.port_pool = set(range(
            local_config['container']['port-range'][0],
            local_config['container']['port-range'][1] + 1,
        ))
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

        self.event_producer = await EventProducer.new(
            self.local_config['redis'],
            db=4,
            log_events=self.local_config['debug']['log-events'],
        )
        self.redis_stream_pool = redis.get_redis_object(self.local_config['redis'], db=4)
        self.redis_stat_pool = redis.get_redis_object(self.local_config['redis'], db=0)

        self.zmq_ctx = zmq.asyncio.Context()

        resources_mod.log_alloc_map = self.local_config['debug']['log-alloc-map']
        computers, self.slots = await self.detect_resources()
        for name, computer in computers.items():
            devices = await computer.list_devices()
            alloc_map = await computer.create_alloc_map()
            self.computers[name] = ComputerContext(computer, devices, alloc_map)

        if not self._skip_initial_scan:
            self.images = await self.scan_images()
            self.timer_tasks.append(aiotools.create_timer(self._scan_images_wrapper, 20.0))
            await self.scan_running_kernels()

        # Prepare stat collector tasks.
        self.timer_tasks.append(aiotools.create_timer(self.collect_node_stat, 5.0))
        self.timer_tasks.append(aiotools.create_timer(self.collect_container_stat, 5.0))

        # Prepare heartbeats.
        self.timer_tasks.append(aiotools.create_timer(self.heartbeat, 3.0))

        # Prepare auto-cleaning of idle kernels.
        self.timer_tasks.append(aiotools.create_timer(self.sync_container_lifecycles, 10.0))

        loop = current_loop()
        self.last_registry_written_time = time.monotonic()
        self.container_lifecycle_handler = loop.create_task(self.process_lifecycle_events())

        # Notify the gateway.
        await self.produce_event(AgentStartedEvent(reason="self-started"))

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
            if stop_signal == signal.SIGTERM:
                await self.clean_all_kernels(blocking=True)

        # Stop timers.
        cancel_results = await cancel_tasks(self.timer_tasks)
        for result in cancel_results:
            if isinstance(result, Exception):
                log.error('timer cancellation error: {}', result)

        # Stop lifecycle event handler.
        await self.container_lifecycle_queue.put(_sentinel)
        await self.container_lifecycle_handler

        # Notify the gateway.
        await self.produce_event(AgentTerminatedEvent(reason="shutdown"))

        # Shut down the event dispatcher and Redis connection pools.
        await self.event_producer.close()
        await self.redis_stream_pool.close()
        await self.redis_stat_pool.close()

        self.zmq_ctx.term()

    async def produce_event(self, event: AbstractEvent) -> None:
        """
        Send an event to the manager(s).
        """
        if self.local_config['debug']['log-heartbeats']:
            _log = log.debug if isinstance(event, AgentHeartbeatEvent) else log.info
        else:
            _log = (lambda *args: None) if isinstance(event, AgentHeartbeatEvent) else log.info
        if self.local_config['debug']['log-events']:
            _log('produce_event({0})', event)
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
        await self.event_producer.produce_event(event, source=self.local_config['agent']['id'])

    async def produce_error_event(
        self,
        exc_info: Tuple[Type[BaseException], BaseException, TracebackType] = None,
    ) -> None:
        exc_type, exc, tb = sys.exc_info() if exc_info is None else exc_info
        pretty_message = ''.join(traceback.format_exception_only(exc_type, exc)).strip()
        pretty_tb = ''.join(traceback.format_tb(tb)).strip()
        await self.produce_event(AgentErrorEvent(pretty_message, pretty_tb))

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
            agent_info = {
                'ip': str(self.local_config['agent']['rpc-listen-addr'].host),
                'region': self.local_config['agent']['region'],
                'scaling_group': self.local_config['agent']['scaling-group'],
                'addr': f"tcp://{self.local_config['agent']['rpc-listen-addr']}",
                'resource_slots': res_slots,
                'version': VERSION,
                'compute_plugins': {
                    key: {
                        'version': computer.instance.get_version(),
                        **(await computer.instance.extra_info()),
                    }
                    for key, computer in self.computers.items()
                },
                'images': snappy.compress(msgpack.packb([
                    (repo_tag, digest) for repo_tag, digest in self.images.items()
                ])),
                'architecture': get_arch_name(),
            }
            await self.produce_event(AgentHeartbeatEvent(agent_info))
        except asyncio.TimeoutError:
            log.warning('event dispatch timeout: instance_heartbeat')
        except Exception:
            log.exception('instance_heartbeat failure')
            await self.produce_error_event()

    async def collect_logs(
        self,
        kernel_id: KernelId,
        container_id: str,
        async_log_iterator: AsyncIterator[bytes],
    ) -> None:
        chunk_size = self.local_config['agent']['container-logs']['chunk-size']
        log_key = f'containerlog.{container_id}'
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
                        await redis.execute(
                            self.redis_stream_pool,
                            lambda r: r.rpush(
                                log_key, stored_chunk),
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
                await redis.execute(
                    self.redis_stream_pool,
                    lambda r: r.rpush(
                        log_key, chunk_buffer.getvalue()),
                )
        finally:
            chunk_buffer.close()
        # Keep the log for at most one hour in Redis.
        # This is just a safety measure to prevent memory leak in Redis
        # for cases when the event delivery has failed or processing
        # the log data has failed.
        await redis.execute(
            self.redis_stream_pool,
            lambda r: r.expire(log_key, 3600),
        )
        await self.produce_event(DoSyncKernelLogsEvent(kernel_id, container_id))

    async def collect_node_stat(self, interval: float):
        if self.local_config['debug']['log-stats']:
            log.debug('collecting node statistics')
        try:
            await self.stat_ctx.collect_node_stat()
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception('unhandled exception while syncing node stats')
            await self.produce_error_event()

    async def collect_container_stat(self, interval: float):
        if self.local_config['debug']['log-stats']:
            log.debug('collecting container statistics')
        try:
            updated_kernel_ids = []
            container_ids = []
            async with self.registry_lock:
                for kernel_id, kernel_obj in [*self.kernel_registry.items()]:
                    if not kernel_obj.stats_enabled:
                        continue
                    updated_kernel_ids.append(kernel_id)
                    container_ids.append(kernel_obj['container_id'])
                await self.stat_ctx.collect_container_stat(container_ids)
            # Let the manager store the statistics in the persistent database.
            if updated_kernel_ids:
                await self.produce_event(DoSyncKernelStatsEvent(updated_kernel_ids))
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception('unhandled exception while syncing container stats')
            await self.produce_error_event()

    async def _handle_start_event(self, ev: ContainerLifecycleEvent) -> None:
        async with self.registry_lock:
            kernel_obj = self.kernel_registry.get(ev.kernel_id)
            if kernel_obj is not None:
                kernel_obj.stats_enabled = True

    async def _handle_destroy_event(self, ev: ContainerLifecycleEvent) -> None:
        try:
            current_task = asyncio.current_task()
            assert current_task is not None
            if ev.kernel_id not in self._ongoing_destruction_tasks:
                self._ongoing_destruction_tasks[ev.kernel_id] = current_task
            self.terminating_kernels.add(ev.kernel_id)
            async with self.registry_lock:
                kernel_obj = self.kernel_registry.get(ev.kernel_id)
                if kernel_obj is None:
                    log.warning('destroy_kernel(k:{0}) kernel missing (already dead?)',
                                ev.kernel_id)
                    if ev.container_id is None:
                        await self.rescan_resource_usage()
                        if not ev.suppress_events:
                            await self.produce_event(
                                KernelTerminatedEvent(ev.kernel_id, "already-terminated"),
                            )
                        if ev.done_future is not None:
                            ev.done_future.set_result(None)
                        return
                    else:
                        await self.container_lifecycle_queue.put(
                            ContainerLifecycleEvent(
                                ev.kernel_id,
                                ev.container_id,
                                LifecycleEvent.CLEAN,
                                ev.reason,
                                suppress_events=ev.suppress_events,
                                done_future=ev.done_future,
                            ),
                        )
                else:
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
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception('unhandled exception while processing DESTROY event')
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
                        port_range = self.local_config['container']['port-range']
                        # Exclude out-of-range ports, because when the agent restarts
                        # with a different port range, existing containers' host ports
                        # may not belong to the new port range.
                        restored_ports = [*filter(
                            lambda p: port_range[0] <= p <= port_range[1],
                            kernel_obj['host_ports'],
                        )]
                        self.port_pool.update(restored_ports)
                        await kernel_obj.close()
                finally:
                    self.terminating_kernels.discard(ev.kernel_id)
                    if restart_tracker := self.restarting_kernels.get(ev.kernel_id, None):
                        restart_tracker.destroy_event.set()
                    else:
                        await self.rescan_resource_usage()
                        if not ev.suppress_events:
                            await self.produce_event(
                                KernelTerminatedEvent(ev.kernel_id, ev.reason),
                            )
                    # Notify cleanup waiters after all state updates.
                    if kernel_obj is not None and kernel_obj.clean_event is not None:
                        kernel_obj.clean_event.set_result(None)
                    if ev.done_future is not None and not ev.done_future.done():
                        ev.done_future.set_result(None)

    async def process_lifecycle_events(self) -> None:

        async def lifecycle_task_exception_handler(
            exc_type: Type[Exception], exc_obj: Exception, tb: TracebackType,
        ) -> None:
            log.exception("unexpected error in lifecycle task", exc_info=exc_obj)

        async with aiotools.PersistentTaskGroup(
            exception_handler=lifecycle_task_exception_handler,
        ) as tg:
            ipc_base_path = self.local_config['agent']['ipc-base-path']
            while True:
                ev = await self.container_lifecycle_queue.get()
                now = time.monotonic()
                if now > self.last_registry_written_time + 60 or isinstance(ev, Sentinel):
                    self.last_registry_written_time = now
                    with open(ipc_base_path / f'last_registry.{self.local_instance_id}.dat', 'wb') as f:
                        pickle.dump(self.kernel_registry, f)
                    log.debug(f'saved last_registry.{self.local_instance_id}.dat')
                if isinstance(ev, Sentinel):
                    return
                # attr currently does not support customizing getstate/setstate dunder methods
                # until the next release.
                if self.local_config['debug']['log-events']:
                    log.info(f'lifecycle event: {ev!r}')
                try:
                    if ev.event == LifecycleEvent.START:
                        tg.create_task(self._handle_start_event(ev))
                    elif ev.event == LifecycleEvent.DESTROY:
                        tg.create_task(self._handle_destroy_event(ev))
                    elif ev.event == LifecycleEvent.CLEAN:
                        tg.create_task(self._handle_clean_event(ev))
                    else:
                        log.warning('unsupported lifecycle event: {!r}', ev)
                except Exception:
                    log.exception(
                        'unexpected error in process_lifecycle_events(): {!r}, continuing...', ev,
                    )
                finally:
                    self.container_lifecycle_queue.task_done()

    async def inject_container_lifecycle_event(
        self,
        kernel_id: KernelId,
        event: LifecycleEvent,
        reason: str,
        *,
        container_id: ContainerId = None,
        exit_code: int = None,
        done_future: asyncio.Future = None,
        suppress_events: bool = False,
    ) -> None:
        try:
            kernel_obj = self.kernel_registry[kernel_id]
            if kernel_obj.termination_reason:
                reason = kernel_obj.termination_reason
            if container_id is not None:
                if event == LifecycleEvent.START:
                    # Update the container ID (for restarted kernels).
                    # This will be overwritten by create_kernel() soon, but
                    # updating here improves consistency of kernel_id to container_id
                    # mapping earlier.
                    kernel_obj['container_id'] = container_id
                elif container_id != kernel_obj['container_id']:
                    # This should not happen!
                    log.warning(
                        "container id mismatch for kernel_obj (k:{}, c:{}) with event (e:{}, c:{})",
                        kernel_id, kernel_obj['container_id'],
                        event.name, container_id,
                    )
            container_id = kernel_obj['container_id']
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
                    event.name, kernel_id,
                )
        await self.container_lifecycle_queue.put(
            ContainerLifecycleEvent(
                kernel_id,
                container_id,
                event,
                reason,
                done_future,
                exit_code,
                suppress_events,
            ),
        )

    @abstractmethod
    async def enumerate_containers(
        self,
        status_filter: FrozenSet[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> Sequence[Tuple[KernelId, Container]]:
        """
        Enumerate the containers with the given status filter.
        """

    async def rescan_resource_usage(self) -> None:
        async with self.resource_lock:
            for computer_set in self.computers.values():
                computer_set.alloc_map.clear()
            for kernel_id, container in (await self.enumerate_containers()):
                for computer_set in self.computers.values():
                    try:
                        await computer_set.instance.restore_from_container(
                            container,
                            computer_set.alloc_map,
                        )
                    except Exception:
                        log.warning(
                            "rescan_resoucre_usage(k:{}): "
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
        known_kernels: Dict[KernelId, ContainerId] = {}
        alive_kernels: Dict[KernelId, ContainerId] = {}
        terminated_kernels = {}

        async with self.resource_lock:
            try:
                # Check if: there are dead containers
                for kernel_id, container in (await self.enumerate_containers(DEAD_STATUS_SET)):
                    if kernel_id in self.restarting_kernels or kernel_id in self.terminating_kernels:
                        continue
                    log.info('detected dead container during lifeycle sync (k:{}, c:{})',
                            kernel_id, container.id)
                    terminated_kernels[kernel_id] = ContainerLifecycleEvent(
                        kernel_id,
                        known_kernels[kernel_id],
                        LifecycleEvent.CLEAN,
                        'self-terminated',
                    )
                for kernel_id, container in (await self.enumerate_containers(ACTIVE_STATUS_SET)):
                    alive_kernels[kernel_id] = container.id
                for kernel_id, kernel_obj in self.kernel_registry.items():
                    known_kernels[kernel_id] = kernel_obj['container_id']
                # Check if: kernel_registry has the container but it's gone.
                for kernel_id in (known_kernels.keys() - alive_kernels.keys()):
                    if kernel_id in self.restarting_kernels or kernel_id in self.terminating_kernels:
                        continue
                    terminated_kernels[kernel_id] = ContainerLifecycleEvent(
                        kernel_id,
                        known_kernels[kernel_id],
                        LifecycleEvent.CLEAN,
                        'self-terminated',
                    )
                # Check if: there are containers not spawned by me.
                for kernel_id in (alive_kernels.keys() - known_kernels.keys()):
                    if kernel_id in self.restarting_kernels:
                        continue
                    terminated_kernels[kernel_id] = ContainerLifecycleEvent(
                        kernel_id,
                        alive_kernels[kernel_id],
                        LifecycleEvent.DESTROY,
                        'terminated-unknown-container',
                    )
            finally:
                # Enqueue the events.
                for kernel_id, ev in terminated_kernels.items():
                    await self.container_lifecycle_queue.put(ev)

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
                LifecycleEvent.DESTROY,
                'agent-termination',
                done_future=clean_events[kernel_id] if blocking else None,
            )
        if blocking:
            waiters = [clean_events[kernel_id] for kernel_id in kernel_ids]
            await asyncio.gather(*waiters)

    @abstractmethod
    async def detect_resources(self) -> Tuple[
        Mapping[DeviceName, AbstractComputePlugin],
        Mapping[SlotName, Decimal],
    ]:
        """
        Scan and define the amount of available resource slots in this node.
        """

    async def gather_hwinfo(self) -> Mapping[str, HardwareMetadata]:
        """
        Collect the hardware metadata from the compute plugins.
        """
        hwinfo: Dict[str, HardwareMetadata] = {}
        tasks = []

        async def _get(
            key: str, plugin: AbstractComputePlugin,
        ) -> Tuple[str, Union[Exception, HardwareMetadata]]:
            try:
                result = await plugin.get_node_hwinfo()
                return key, result
            except Exception as e:
                return key, e

        for key, plugin in self.computers.items():
            tasks.append(_get(key, plugin.instance))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for key, result in results:
            if isinstance(result, NotImplementedError):
                continue
            elif isinstance(result, Exception):
                hwinfo[key] = {
                    'status': "unavailable",
                    'status_info': str(result),
                    'metadata': {},
                }
            else:
                hwinfo[key] = result
        return hwinfo

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
    async def pull_image(self, image_ref: ImageRef, registry_conf: ImageRegistry) -> None:
        '''
        Pull the given image from the given registry.
        '''

    @abstractmethod
    async def check_image(self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior) -> bool:
        '''
        Check the availability of the image and return a boolean flag that indicates whether
        the agent should try pulling the image from a registry.
        '''
        return False

    async def scan_running_kernels(self) -> None:
        """
        Scan currently running kernels and recreate the kernel objects in
        ``self.kernel_registry`` if any missing.
        """
        try:
            ipc_base_path = self.local_config['agent']['ipc-base-path']
            with open(ipc_base_path / f'last_registry.{self.local_instance_id}.dat', 'rb') as f:
                self.kernel_registry = pickle.load(f)
                for kernel_obj in self.kernel_registry.values():
                    kernel_obj.agent_config = self.local_config
                    if kernel_obj.runner is not None:
                        await kernel_obj.runner.__ainit__()
        except FileNotFoundError:
            pass
        async with self.resource_lock:
            for kernel_id, container in (await self.enumerate_containers(
                ACTIVE_STATUS_SET | DEAD_STATUS_SET,
            )):
                if container.status in ACTIVE_STATUS_SET:
                    kernelspec = int(container.labels.get('ai.backend.kernelspec', '1'))
                    if not (MIN_KERNELSPEC <= kernelspec <= MAX_KERNELSPEC):
                        continue
                    # Consume the port pool.
                    for p in container.ports:
                        if p.host_port is not None:
                            self.port_pool.discard(p.host_port)
                    # Restore compute resources.
                    for computer_set in self.computers.values():
                        await computer_set.instance.restore_from_container(
                            container,
                            computer_set.alloc_map,
                        )
                    await self.inject_container_lifecycle_event(
                        kernel_id,
                        LifecycleEvent.START,
                        'resuming-agent-operation',
                        container_id=container.id,
                    )
                elif container.status in DEAD_STATUS_SET:
                    log.info('detected dead container while agent is down (k:{}, c:{})',
                             kernel_id, container.id)
                    await self.inject_container_lifecycle_event(
                        kernel_id,
                        LifecycleEvent.CLEAN,
                        'self-terminated',
                        container_id=container.id,
                    )

        log.info('starting with resource allocations')
        for computer_name, computer_ctx in self.computers.items():
            log.info('{}: {!r}',
                     computer_name,
                     dict(computer_ctx.alloc_map.allocations))

    @abstractmethod
    async def init_kernel_context(
        self,
        kernel_id: KernelId,
        kernel_config: KernelCreationConfig,
        *,
        restarting: bool = False,
    ) -> AbstractKernelCreationContext:
        raise NotImplementedError

    async def execute_batch(
        self,
        kernel_id: KernelId,
        startup_command: str,
    ) -> None:
        kernel_obj = self.kernel_registry.get(kernel_id, None)
        if kernel_obj is None:
            log.warning('execute_batch(k:{}): no such kernel', kernel_id)
            return
        log.debug('execute_batch(k:{}): executing {!r}', kernel_id, (startup_command or '')[:60])
        mode: Literal['batch', 'continue'] = 'batch'
        opts = {
            'exec': startup_command,
        }
        try:
            while True:
                try:
                    result = await self.execute(
                        kernel_id,
                        'batch-job',  # a reserved run ID
                        mode,
                        '',
                        opts=opts,
                        flush_timeout=1.0,
                        api_version=3)
                except KeyError:
                    await self.produce_event(
                        KernelTerminatedEvent(kernel_id, "self-terminated"),
                    )
                    break

                if result['status'] == 'finished':
                    if result['exitCode'] == 0:
                        await self.produce_event(
                            SessionSuccessEvent(SessionId(kernel_id), "task-done", 0),
                        )
                    else:
                        await self.produce_event(
                            SessionFailureEvent(SessionId(kernel_id), "task-failed", result['exitCode']),
                        )
                    break
                if result['status'] == 'exec-timeout':
                    await self.produce_event(
                        SessionFailureEvent(SessionId(kernel_id), "task-timeout", -2),
                    )
                    break
                opts = {
                    'exec': '',
                }
                mode = 'continue'
        except asyncio.CancelledError:
            await self.produce_event(
                SessionFailureEvent(SessionId(kernel_id), "task-cancelled", -2),
            )

    async def create_kernel(
        self,
        creation_id: str,
        session_id: SessionId,
        kernel_id: KernelId,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        restarting: bool = False,
    ) -> KernelCreationResult:
        """
        Create a new kernel.
        """

        if not restarting:
            await self.produce_event(
                KernelPreparingEvent(kernel_id, creation_id),
            )

        # Initialize the creation context
        if self.local_config['debug']['log-kernel-config']:
            log.debug('Kernel creation config: {0}', pretty(kernel_config))
        ctx = await self.init_kernel_context(
            kernel_id, kernel_config,
            restarting=restarting,
        )
        environ: MutableMapping[str, str] = {**kernel_config['environ']}

        # Inject Backend.AI-intrinsic env-variables for gosu
        if KernelFeatures.UID_MATCH in ctx.kernel_features:
            uid = self.local_config['container']['kernel-uid']
            gid = self.local_config['container']['kernel-gid']
            environ['LOCAL_USER_ID'] = str(uid)
            environ['LOCAL_GROUP_ID'] = str(gid)
        environ.update(
            await ctx.get_extra_envs(),
        )
        image_labels = kernel_config['image']['labels']

        agent_architecture = get_arch_name()
        if agent_architecture != ctx.image_ref.architecture:
            # disable running different architecture's image
            raise AgentError(
                f'cannot run {ctx.image_ref.architecture} image on {agent_architecture} machine',
            )

        # Check if we need to pull the container image
        do_pull = await self.check_image(
            ctx.image_ref,
            kernel_config['image']['digest'],
            AutoPullBehavior(kernel_config.get('auto_pull', 'digest')),
        )
        if do_pull:
            await self.produce_event(
                KernelPullingEvent(kernel_id, creation_id, ctx.image_ref.canonical),
            )
            await self.pull_image(ctx.image_ref, kernel_config['image']['registry'])

        if not restarting:
            await self.produce_event(
                KernelCreatingEvent(kernel_id, creation_id),
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
        slots = resource_spec.slots
        dev_names: Set[DeviceName] = set()
        for slot_name in slots.keys():
            dev_name = slot_name.split('.', maxsplit=1)[0]
            dev_names.add(DeviceName(dev_name))

        if not restarting:
            async with self.resource_lock:
                for dev_name in dev_names:
                    computer_set = self.computers[dev_name]
                    device_specific_slots = {
                        SlotName(slot_name): Decimal(alloc)
                        for slot_name, alloc in slots.items()
                        if slot_name.startswith(dev_name)
                    }
                    try:
                        # TODO: support allocate_evenly()
                        resource_spec.allocations[dev_name] = \
                            computer_set.alloc_map.allocate(
                                device_specific_slots,
                                context_tag=dev_name)
                    except ResourceError as e:
                        log.info(
                            "resource allocation failed ({}): {} of {}\n"
                            "(alloc map: {})",
                            type(e).__name__, device_specific_slots, dev_name,
                            dict(computer_set.alloc_map.allocations),
                        )
                        raise

        # Prepare scratch spaces and dotfiles inside it.
        if not restarting:
            await ctx.prepare_scratch()

        # Prepare networking.
        await ctx.apply_network(cluster_info)
        await ctx.install_ssh_keypair(cluster_info)

        # Mount vfolders and krunner stuffs.
        if not restarting:
            vfolder_mounts = [VFolderMount.from_json(item) for item in kernel_config['mounts']]
            await ctx.mount_vfolders(vfolder_mounts, resource_spec)
            await ctx.mount_krunner(resource_spec, environ)

        # Inject Backend.AI-intrinsic env-variables for libbaihook and gosu
        label_envs_corecount = image_labels.get('ai.backend.envs.corecount', '')
        envs_corecount = label_envs_corecount.split(',') if label_envs_corecount else []
        cpu_core_count = len(resource_spec.allocations[DeviceName('cpu')][SlotName('cpu')])
        environ.update({k: str(cpu_core_count) for k in envs_corecount if k not in environ})

        # Realize mounts.
        await ctx.process_mounts(resource_spec.mounts)

        # Get attached devices information (including model_name).
        attached_devices = {}
        for dev_name, device_alloc in resource_spec.allocations.items():
            computer_set = self.computers[dev_name]
            devices = await computer_set.instance.get_attached_devices(device_alloc)
            attached_devices[dev_name] = devices

        exposed_ports = [2000, 2001]
        service_ports = []
        port_map = {}
        preopen_ports = ctx.kernel_config.get('preopen_ports')
        if preopen_ports is None:
            preopen_ports = []

        if ctx.kernel_config['cluster_role'] in ('main', 'master'):
            for sport in parse_service_ports(image_labels.get('ai.backend.service-ports', '')):
                port_map[sport['name']] = sport
            port_map['sshd'] = {
                'name': 'sshd',
                'protocol': ServicePortProtocols('tcp'),
                'container_ports': (2200,),
                'host_ports': (None,),
            }
            port_map['ttyd'] = {
                'name': 'ttyd',
                'protocol': ServicePortProtocols('http'),
                'container_ports': (7681,),
                'host_ports': (None,),
            }
            for port_no in preopen_ports:
                sport = {
                    'name': str(port_no),
                    'protocol': ServicePortProtocols('preopen'),
                    'container_ports': (port_no,),
                    'host_ports': (None,),
                }
                service_ports.append(sport)
                for cport in sport['container_ports']:
                    exposed_ports.append(cport)
            for sport in port_map.values():
                service_ports.append(sport)
                for cport in sport['container_ports']:
                    exposed_ports.append(cport)
            log.debug('exposed ports: {!r}', exposed_ports)

        runtime_type = image_labels.get('ai.backend.runtime-type', 'python')
        runtime_path = image_labels.get('ai.backend.runtime-path', None)
        cmdargs: List[str] = []
        if self.local_config['container']['sandbox-type'] == 'jail':
            cmdargs += [
                "/opt/kernel/jail",
                "-policy", "/etc/backend.ai/jail/policy.yml",
            ]
            if self.local_config['container']['jail-args']:
                cmdargs += map(lambda s: s.strip(), self.local_config['container']['jail-args'])
        cmdargs += [
            "/opt/backend.ai/bin/python",
            "-m", "ai.backend.kernel", runtime_type,
        ]
        if runtime_path is not None:
            cmdargs.append(runtime_path)

        # Store information required for restarts.
        # NOTE: kconfig may be updated after restarts.
        resource_spec.freeze()
        await self.restart_kernel__store_config(
            kernel_id, 'kconfig.dat',
            pickle.dumps(ctx.kernel_config),
        )
        if not restarting:
            await self.restart_kernel__store_config(
                kernel_id, 'cluster.json',
                json.dumps(cluster_info).encode('utf8'),
            )

        if self.local_config['debug']['log-kernel-config']:
            log.info('kernel starting with resource spec: \n{0}',
                     pretty(attr.asdict(resource_spec)))
        kernel_obj: KernelObjectType = await ctx.spawn(
            resource_spec,
            environ,
            service_ports,
        )
        async with self.registry_lock:
            self.kernel_registry[ctx.kernel_id] = kernel_obj
        container_data = await ctx.start_container(
            kernel_obj,
            cmdargs,
            resource_opts,
            preopen_ports,
        )
        async with self.registry_lock:
            self.kernel_registry[ctx.kernel_id].data.update(container_data)
        await kernel_obj.init()

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
                    if live_services['status'] != 'failed':
                        for live_service in live_services['data']:
                            for service_port in service_ports:
                                if live_service['name'] == service_port['name']:
                                    service_port.update(live_service)
                                    break
            if self.local_config['debug']['log-kernel-config']:
                log.debug('service ports:\n{!r}', pretty(service_ports))
        except asyncio.CancelledError:
            log.warning("cancelled waiting of container startup (k:{})", kernel_id)
            raise
        except Exception:
            log.exception("unexpected error while waiting container startup (k:{})", kernel_id)
            raise RuntimeError(
                "cancelled waiting of container startup due to initialization failure",
            )
        finally:
            self._pending_creation_tasks[kernel_id].remove(current_task)
            if not self._pending_creation_tasks[kernel_id]:
                del self._pending_creation_tasks[kernel_id]

        # Finally we are done.
        await self.produce_event(
            KernelStartedEvent(kernel_id, creation_id),
        )

        if kernel_config['session_type'] == 'batch' and kernel_config['cluster_role'] == 'main':
            self._ongoing_exec_batch_tasks.add(
                asyncio.create_task(
                    self.execute_batch(kernel_id, kernel_config['startup_command'] or ""),
                ),
            )

        # The startup command for the batch-type sessions will be executed by the manager
        # upon firing of the "session_started" event.

        return {
            'id': KernelId(kernel_id),
            'kernel_host': str(kernel_obj['kernel_host']),
            'repl_in_port': kernel_obj['repl_in_port'],
            'repl_out_port': kernel_obj['repl_out_port'],
            'stdin_port': kernel_obj['stdin_port'],     # legacy
            'stdout_port': kernel_obj['stdout_port'],   # legacy
            'service_ports': service_ports,
            'container_id': kernel_obj['container_id'],
            'resource_spec': resource_spec.to_json_serializable_dict(),
            'attached_devices': attached_devices,
        }

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
    async def create_overlay_network(self, network_name: str) -> None:
        """
        Create an overlay network for a multi-node multicontainer session, where containers in different
        agents can connect to each other using cluster hostnames without explicit port mapping.

        This is called by the manager before kernel creation.
        It may raise :exc:`NotImplementedError` and then the manager
        will cancel creation of the session.
        """

    @abstractmethod
    async def destroy_overlay_network(self, network_name: str) -> None:
        """
        Destroy an overlay network.

        This is called by the manager after kernel destruction.
        """

    @abstractmethod
    async def create_local_network(self, network_name: str) -> None:
        """
        Create a local bridge network for a single-node multicontainer session, where containers in the
        same agent can connect to each other using cluster hostnames without explicit port mapping.
        Depending on the backend, this may be an alias to :meth:`create_overlay_network()`.

        This is called by the manager before kernel creation.
        It may raise :exc:`NotImplementedError` and then the manager
        will cancel creation of the session.
        """

    @abstractmethod
    async def destroy_local_network(self, network_name: str) -> None:
        """
        Destroy a local bridge network.
        Depending on the backend, this may be an alias to :meth:`destroy_overlay_network()`.

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
        creation_id: str,
        session_id: SessionId,
        kernel_id: KernelId,
        updating_kernel_config: KernelCreationConfig,
    ):
        tracker = self.restarting_kernels.get(kernel_id)
        if tracker is None:
            tracker = RestartTracker(
                request_lock=asyncio.Lock(),
                destroy_event=asyncio.Event(),
                done_event=asyncio.Event())
            self.restarting_kernels[kernel_id] = tracker

        existing_kernel_config = pickle.loads(
            await self.restart_kernel__load_config(kernel_id, 'kconfig.dat'),
        )
        existing_cluster_info = json.loads(
            await self.restart_kernel__load_config(kernel_id, 'cluster.json'),
        )
        kernel_config = cast(
            KernelCreationConfig,
            {**existing_kernel_config, **updating_kernel_config},
        )
        async with tracker.request_lock:
            tracker.done_event.clear()
            await self.inject_container_lifecycle_event(
                kernel_id,
                LifecycleEvent.DESTROY,
                'restarting',
            )
            try:
                with timeout(60):
                    await tracker.destroy_event.wait()
            except asyncio.TimeoutError:
                log.warning('timeout detected while restarting kernel {0}!',
                            kernel_id)
                self.restarting_kernels.pop(kernel_id, None)
                await self.inject_container_lifecycle_event(
                    kernel_id,
                    LifecycleEvent.CLEAN,
                    'restart-timeout',
                )
                raise
            else:
                try:
                    await self.create_kernel(
                        creation_id,
                        session_id,
                        kernel_id,
                        kernel_config,
                        existing_cluster_info,
                        restarting=True)
                    self.restarting_kernels.pop(kernel_id, None)
                except Exception:
                    # TODO: retry / cancel others?
                    log.exception('restart_kernel(s:{}, k:{}): re-creation failure',
                                  session_id, kernel_id)
            tracker.done_event.set()
        kernel_obj = self.kernel_registry[kernel_id]
        return {
            'container_id': kernel_obj['container_id'],
            'repl_in_port': kernel_obj['repl_in_port'],
            'repl_out_port': kernel_obj['repl_out_port'],
            'stdin_port': kernel_obj['stdin_port'],
            'stdout_port': kernel_obj['stdout_port'],
            'service_ports': kernel_obj.service_ports,
        }

    async def execute(
        self,
        kernel_id: KernelId,
        run_id: Optional[str],
        mode: Literal['query', 'batch', 'input', 'continue'],
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
            ExecutionStartedEvent(SessionId(kernel_id)),
        )
        try:
            kernel_obj = self.kernel_registry[kernel_id]
            result = await kernel_obj.execute(
                run_id, mode, text,
                opts=opts,
                flush_timeout=flush_timeout,
                api_version=api_version)
        except asyncio.CancelledError:
            await self.produce_event(
                ExecutionCancelledEvent(SessionId(kernel_id)),
            )
            raise
        except KeyError:
            # This situation is handled in the lifecycle management subsystem.
            raise RuntimeError(f'The container for kernel {kernel_id} is not found! '
                                '(might be terminated--try it again)') from None

        if result['status'] in ('finished', 'exec-timeout'):
            log.debug('_execute({0}) {1}', kernel_id, result['status'])
        if result['status'] == 'finished':
            await self.produce_event(
                ExecutionFinishedEvent(SessionId(kernel_id)),
            )
        elif result['status'] == 'exec-timeout':
            await self.produce_event(
                ExecutionTimeoutEvent(SessionId(kernel_id)),
            )
            await self.inject_container_lifecycle_event(
                kernel_id,
                LifecycleEvent.DESTROY,
                'exec-timeout',
            )
        return {
            **result,
            'files': [],  # kept for API backward-compatibility
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
            log.exception('unhandled exception while shutting down service app ${}', service)

    async def accept_file(self, kernel_id: KernelId, filename: str, filedata):
        return await self.kernel_registry[kernel_id].accept_file(filename, filedata)

    async def download_file(self, kernel_id: KernelId, filepath: str):
        return await self.kernel_registry[kernel_id].download_file(filepath)

    async def list_files(self, kernel_id: KernelId, path: str):
        return await self.kernel_registry[kernel_id].list_files(path)

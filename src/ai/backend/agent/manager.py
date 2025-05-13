import asyncio
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import pickle
import signal
import sys
import time
import traceback
from types import TracebackType
from typing import Any, Awaitable, Collection, Generic, Mapping, MutableMapping, Optional, TypeVar

from ai.backend.agent.alloc_map import AbstractAllocMap
from ai.backend.agent.backends.image_registry import AbstractAgentImageRegistry
from ai.backend.agent.exception import KernelAlreadyExistsError, KernelNotFoundError
from ai.backend.agent.resources import AbstractComputeDevice, AbstractComputePlugin
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.asyncio import cancel_tasks
from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.docker import ImageRef
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.agent import AgentErrorEvent, AgentHeartbeatEvent, AgentTerminatedEvent
from ai.backend.common.events.dispatcher import AbstractEvent, EventProducer
from ai.backend.common.events.kernel import KernelStartedEvent, KernelTerminatedEvent
from ai.backend.common.events.volume import DoVolumeMountEvent, DoVolumeUnmountEvent, VolumeMounted, VolumeUnmounted
from ai.backend.common.exception import VolumeMountFailed
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.types import AgentId, ClusterInfo, DeviceName, HardwareMetadata, KernelCreationConfig, KernelCreationResult, KernelId, VolumeMountableNodeType
from ai.backend.common.utils import mount, umount
from ai.backend.logging.utils import BraceStyleAdapter

from .backends.kernel import AbstractKernel, AbstractKernelFactory, KernelWrapper
from .backends.types import AbstractBackend


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class ComputerContext:
    instance: AbstractComputePlugin
    devices: Collection[AbstractComputeDevice]
    alloc_map: AbstractAllocMap


class KernelRegistry:
    _lock: asyncio.Lock
    _kernel_dict: dict[KernelId, KernelWrapper]

    def __init__(self):
        self._lock = asyncio.Lock()
        self._kernel_dict = {}
    
    async def add(self, kernel_id: KernelId, kernel_obj: KernelWrapper):
        async with self._lock:
            if kernel_id in self._kernel_dict:
                raise KernelAlreadyExistsError(f"Kernel {kernel_id} already exists.")
            self._kernel_dict[kernel_id] = kernel_obj
    
    async def remove(self, kernel_id: KernelId):
        async with self._lock:
            if kernel_id not in self._kernel_dict:
                raise KernelNotFoundError(f"Kernel {kernel_id} does not exist.")
            del self._kernel_dict[kernel_id]
    
    async def get(self, kernel_id: KernelId) -> KernelWrapper:
        async with self._lock:
            if kernel_id not in self._kernel_dict:
                raise KernelNotFoundError(f"Kernel {kernel_id} does not exist.")
            return self._kernel_dict[kernel_id]
    
    async def get_all(self) -> Mapping[KernelId, KernelWrapper]:
        async with self._lock:
            return self._kernel_dict.copy()

@dataclass
class AgentArgs:
    """
    Arguments for the Agent class.
    """
    id: AgentId
    local_config: Mapping[str, Any]
    etcd: AsyncEtcd
    backend: AbstractBackend
    image_registry: AbstractAgentImageRegistry
    kernel_factory: AbstractKernelFactory
    event_producer: EventProducer


class Agent:
    _id: AgentId
    _local_config: Mapping[str, Any]
    _etcd: AsyncEtcd
    _backend: AbstractBackend
    _image_registry: AbstractAgentImageRegistry
    _kernel_factory: AbstractKernelFactory
    _kernel_registry: KernelRegistry
    _computers: list[ComputerContext]
    _event_producer: EventProducer
    _port_pool: set[int]

    def __init__(self, args: AgentArgs):
        """
        Initialize the Agent with the given arguments.
        """
        self._id = args.id
        self._backend = args.backend
        self._kernel_factory = args.kernel_factory
        self._kernel_registry = KernelRegistry()
        self._event_producer = args.event_producer
    
    @property
    def id(self) -> AgentId:
        """
        Get the agent ID.
        """
        return self._id
    
    async def create_kernel(
        self,
        ownership_data: KernelOwnershipData,
        kernel_image: ImageRef,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        restarting: bool = False,
        throttle_sema: Optional[asyncio.Semaphore] = None,
    ) -> KernelCreationResult:
        ...
    
    async def get_kernel(
        self,
        kernel_id: KernelId,
    ) -> KernelWrapper:
        ...
    
    async def all_kernels(
        self,
    ) -> Mapping[KernelId, KernelWrapper]:
        """
        Get all kernels.
        """
        return await self._kernel_registry.get_all()
    
    async def all_computers(
        self,
    ) -> Mapping[DeviceName, ComputerContext]:
        """
        Get all kernels.
        """
        return await self._computers..get_all()
    
    @property
    def backend(self) -> AbstractBackend:
        """
        Get the backend instance.
        """
        return self._backend
    
    @property
    def image_registry(self) -> AbstractAgentImageRegistry:
        """
        Get the image registry instance.
        """
        return self._image_registry

    async def gather_hwinfo(self) -> Mapping[str, HardwareMetadata]:
        """
        Collect the hardware metadata from the compute plugins.
        """
        hwinfo: dict[str, HardwareMetadata] = {}
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

        computers = await self.all_computers()
        for device_name, plugin in computers.items():
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

    async def shutdown(self, stop_signal: signal.Signals) -> None:
        """
        An implementation of AbstractAgent would define its own ``shutdown()`` method.
        It must call this super method in an appropriate order, only once.
        """
        await cancel_tasks(self._ongoing_exec_batch_tasks)

        all_kernels = await self._kernel_registry.get_all()
        for kernel_obj in all_kernels.values():
            await kernel_obj.close()
            if stop_signal == signal.SIGTERM:
                await kernel_obj.runner.close()

        async with self.registry_lock:
            # Close all pending kernel runners.
            for kernel_obj in self.kernel_registry.values():
                if kernel_obj.runner is not None:
                    await kernel_obj.runner.close()
                await kernel_obj.close()
            await self.save_last_registry(force=True)
            if stop_signal == signal.SIGTERM:
                await self.clean_all_kernels(blocking=True)

        # Notify the gateway.
        await self.produce_event(AgentTerminatedEvent(reason="shutdown"))

        # Shut down the event dispatcher and Redis connection pools.
        await self._event_producer.close()
        await self.redis_stream_pool.close()
        await self.redis_stat_pool.close()

    async def produce_event(self, event: AbstractEvent) -> None:
        """
        Send an event to the manager(s).
        """
        if self._local_config["debug"]["log-heartbeats"]:
            _log = log.debug if isinstance(event, AgentHeartbeatEvent) else log.info
        else:
            _log = (lambda *args: None) if isinstance(event, AgentHeartbeatEvent) else log.info
        if self._local_config["debug"]["log-events"]:
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
        await self._event_producer.produce_event(event)

    async def produce_error_event(
        self,
        exc_info: Optional[tuple[type[BaseException], BaseException, TracebackType]] = None,
    ) -> None:
        exc_type, exc, tb = sys.exc_info() if exc_info is None else exc_info
        pretty_message = "".join(traceback.format_exception_only(exc_type, exc)).strip()
        pretty_tb = "".join(traceback.format_tb(tb)).strip()
        await self.produce_event(AgentErrorEvent(pretty_message, pretty_tb))

    async def save_last_registry(self, force=False) -> None:
        # TODO: Remove this method when we have a better way to restore the kernel.
        now = time.monotonic()
        if (not force) and (now <= self.last_registry_written_time + 60):
            return  # don't save too frequently
        var_base_path = self.local_config["agent"]["var-base-path"]
        last_registry_file = f"last_registry.{self.local_instance_id}.dat"
        try:
            with open(var_base_path / last_registry_file, "wb") as f:
                pickle.dump(self._kernel_registry, f)
            self.last_registry_written_time = now
            log.debug("saved {}", last_registry_file)
        except Exception as e:
            log.exception("unable to save {}", last_registry_file, exc_info=e)
            try:
                os.remove(var_base_path / last_registry_file)
            except FileNotFoundError:
                pass

    async def handle_volume_mount(
        self,
        source: AgentId,
        event: DoVolumeMountEvent,
    ) -> None:
        if self._local_config["agent"]["cohabiting-storage-proxy"]:
            log.debug("Storage proxy is in the same node. Skip the volume task.")
            await self._event_producer.produce_event(
                VolumeMounted(
                    str(self._id),
                    VolumeMountableNodeType.AGENT,
                    "",
                    event.quota_scope_id,
                )
            )
            return
        mount_prefix = await self._etcd.get("volumes/_mount")
        volume_mount_prefix: str | None = self._local_config["agent"]["mount-path"]
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
        await self._event_producer.produce_event(
            VolumeMounted(
                str(self._id),
                VolumeMountableNodeType.AGENT,
                str(real_path),
                event.quota_scope_id,
                err_msg,
            )
        )

    async def handle_volume_umount(
        self,
        source: AgentId,
        event: DoVolumeUnmountEvent,
    ) -> None:
        if self._local_config["agent"]["cohabiting-storage-proxy"]:
            log.debug("Storage proxy is in the same node. Skip the volume task.")
            await self._event_producer.produce_event(
                VolumeUnmounted(
                    str(self._id),
                    VolumeMountableNodeType.AGENT,
                    "",
                    event.quota_scope_id,
                )
            )
            return
        mount_prefix = await self._etcd.get("volumes/_mount")
        timeout = await self._etcd.get("config/watcher/file-io-timeout")
        volume_mount_prefix = self._local_config["agent"]["mount-path"]
        real_path = Path(volume_mount_prefix, event.dir_name)
        err_msg: str | None = None
        did_umount = False
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
            log.warning("{} does not exist. Skip umount", real_path)
        await self._event_producer.produce_event(
            VolumeUnmounted(
                str(self._id),
                VolumeMountableNodeType.AGENT,
                str(real_path),
                event.quota_scope_id,
                err_msg,
            )
        )

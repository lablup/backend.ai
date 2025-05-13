import asyncio
import logging
import signal
import sys
import traceback
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Awaitable, Collection, Mapping, Optional

from ai.backend.agent.alloc_map import AbstractAllocMap
from ai.backend.agent.backends.image_registry import AbstractAgentImageRegistry
from ai.backend.agent.exception import KernelAlreadyExistsError, KernelNotFoundError
from ai.backend.agent.resources import AbstractComputeDevice, AbstractComputePlugin
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.asyncio import cancel_tasks
from ai.backend.common.docker import ImageRef
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.agent import (
    AgentErrorEvent,
    AgentHeartbeatEvent,
    AgentTerminatedEvent,
)
from ai.backend.common.events.dispatcher import AbstractEvent, EventProducer
from ai.backend.common.events.kernel import KernelStartedEvent, KernelTerminatedEvent
from ai.backend.common.types import (
    AgentId,
    ClusterInfo,
    DeviceName,
    HardwareMetadata,
    KernelCreationConfig,
    KernelCreationResult,
    KernelId,
)
from ai.backend.logging.utils import BraceStyleAdapter

from .backends.backend import AbstractBackend
from .backends.kernel import KernelWrapper

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

    agent_id: AgentId
    local_config: Mapping[str, Any]
    etcd: AsyncEtcd
    backend: AbstractBackend
    image_registry: AbstractAgentImageRegistry
    event_producer: EventProducer


class Agent:
    _id: AgentId
    _local_config: Mapping[str, Any]
    _etcd: AsyncEtcd
    _backend: AbstractBackend
    _image_registry: AbstractAgentImageRegistry
    _kernel_registry: KernelRegistry
    _computers: Mapping[DeviceName, ComputerContext]
    _event_producer: EventProducer
    _port_pool: set[int]

    def __init__(self, args: AgentArgs):
        """
        Initialize the Agent with the given arguments.
        """
        self._id = args.agent_id
        self._backend = args.backend
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
    ) -> KernelCreationResult: ...

    async def get_kernel(
        self,
        kernel_id: KernelId,
    ) -> KernelWrapper:
        return await self._kernel_registry.get(kernel_id)

    async def all_kernels(
        self,
    ) -> Mapping[KernelId, KernelWrapper]:
        """
        Get all kernels.
        """
        return await self._kernel_registry.get_all()

    @property
    def computers(
        self,
    ) -> Mapping[DeviceName, ComputerContext]:
        """
        Get all computers.
        """
        return self._computers

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

    async def shutdown(self, stop_signal: signal.Signals) -> None:
        """
        An implementation of AbstractAgent would define its own ``shutdown()`` method.
        It must call this super method in an appropriate order, only once.
        """
        all_kernels = await self._kernel_registry.get_all()
        for kernel_obj in all_kernels.values():
            await kernel_obj.close(stop_signal)

        # Notify the gateway.
        await self.produce_event(AgentTerminatedEvent(reason="shutdown"))

        # Shut down the event dispatcher and Redis connection pools.
        await self._event_producer.close()

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
        await self._event_producer.produce_event(event)

    async def produce_error_event(
        self,
        exc_info: Optional[tuple[type[BaseException], BaseException, TracebackType]] = None,
    ) -> None:
        exc_type, exc, tb = sys.exc_info() if exc_info is None else exc_info
        pretty_message = "".join(traceback.format_exception_only(exc_type, exc)).strip()
        pretty_tb = "".join(traceback.format_tb(tb)).strip()
        await self.produce_event(AgentErrorEvent(pretty_message, pretty_tb))

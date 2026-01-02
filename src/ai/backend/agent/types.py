from __future__ import annotations

import asyncio
import enum
import importlib
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence, Type, TypeAlias

import attrs
from aiohttp.typedefs import Middleware

from ai.backend.common.docker import LabelName
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.events.kernel import KernelLifecycleEventReason
from ai.backend.common.types import (
    AgentId,
    ContainerId,
    ContainerStatus,
    DeviceName,
    KernelId,
    MountTypes,
    SessionId,
    SlotName,
)

if TYPE_CHECKING:
    from .agent import AbstractAgent
    from .resources import AbstractComputePlugin


class AgentBackend(enum.StrEnum):
    # The list of importable backend names under "ai.backend.agent" pkg namespace.
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    DUMMY = "dummy"


class AbstractAgentDiscovery(ABC):
    @abstractmethod
    def get_agent_cls(self) -> Type[AbstractAgent]:
        """
        Return the concrete implementation class of AbstactAgent for the backend.
        """
        raise NotImplementedError()

    @abstractmethod
    async def load_resources(
        self,
        etcd: AbstractKVStore,
        local_config: Mapping[str, Any],
    ) -> Mapping[DeviceName, AbstractComputePlugin]:
        """
        Detect and load the accelerator plugins.

        limit_cpus, limit_gpus are deprecated.
        """
        raise NotImplementedError()

    @abstractmethod
    async def scan_available_resources(
        self,
        compute_device_types: Mapping[DeviceName, AbstractComputePlugin],
    ) -> Mapping[SlotName, Decimal]:
        """
        Detect available computing resource of the system.
        """
        raise NotImplementedError()

    @abstractmethod
    async def prepare_krunner_env(self, local_config: Mapping[str, Any]) -> Mapping[str, str]:
        """
        Check if the volume "backendai-krunner.{distro}.{arch}" exists and is up-to-date.
        If not, automatically create it and update its content from the packaged pre-built krunner
        tar archives.
        """
        raise NotImplementedError()


def get_agent_discovery(backend: AgentBackend) -> AbstractAgentDiscovery:
    agent_mod = importlib.import_module(f"ai.backend.agent.{backend.value}")
    return agent_mod.get_agent_discovery()


@attrs.define(auto_attribs=True, slots=True)
class VolumeInfo:
    name: str  # volume name
    container_path: str  # in-container path as str
    mode: str  # 'rw', 'ro', 'rwm'


@attrs.define(auto_attribs=True, slots=True)
class MountInfo:
    mode: MountTypes
    src_path: Path
    dst_path: Path


@attrs.define(auto_attribs=True, slots=True)
class Port:
    host: str
    private_port: int
    host_port: int


@attrs.define(auto_attribs=True, slots=True)
class AgentEventData:
    type: str
    data: dict[str, Any]


@attrs.define(auto_attribs=True, slots=True)
class Container:
    id: ContainerId
    status: ContainerStatus
    image: str
    labels: Mapping[str, str]
    ports: Sequence[Port]
    backend_obj: Any  # used to keep the backend-specific data

    @property
    def human_readable_id(self) -> str:
        """
        Returns a human-readable version of the container ID.
        This is useful for logging and debugging purposes.
        """
        return str(self.id)[:12]

    @property
    def agent_id(self) -> AgentId:
        raw_agent_id = self.labels[LabelName.AGENT_ID]
        return AgentId(raw_agent_id)

    @property
    def kernel_id(self) -> KernelId:
        raw_kernel_id = self.labels[LabelName.KERNEL_ID]
        return KernelId(uuid.UUID(raw_kernel_id))

    @property
    def session_id(self) -> SessionId:
        raw_session_id = self.labels[LabelName.SESSION_ID]
        return SessionId(uuid.UUID(raw_session_id))


class KernelLifecycleStatus(enum.StrEnum):
    """
    The lifecycle status of `AbstractKernel` object.

    By default, the state of a newly created kernel is `PREPARING`.
    The state of a kernel changes from `PREPARING` to `RUNNING` after the kernel starts a container successfully.
    It changes from `RUNNING` to `TERMINATING` before destroy kernel.
    """

    PREPARING = enum.auto()
    RUNNING = enum.auto()
    TERMINATING = enum.auto()


class LifecycleEvent(enum.IntEnum):
    DESTROY = 0
    CLEAN = 1
    START = 2


@attrs.define(auto_attribs=True, slots=True)
class ContainerLifecycleEvent:
    kernel_id: KernelId
    session_id: SessionId
    container_id: Optional[ContainerId]
    event: LifecycleEvent
    reason: KernelLifecycleEventReason
    done_future: Optional[asyncio.Future] = None
    exit_code: Optional[int] = None
    suppress_events: bool = False

    def __str__(self):
        if self.container_id:
            cid = self.container_id[:13]
        else:
            cid = "unknown"
        return (
            "LifecycleEvent("
            f"{self.event.name}, "
            f"k:{self.kernel_id}, "
            f"c:{cid}, "
            f"reason:{self.reason!r})"
        )

    def set_done_future_result(self, result: Any):
        if self.done_future is not None:
            try:
                self.done_future.set_result(result)
            except asyncio.InvalidStateError:
                # The future is already done, ignore the error
                pass

    def set_done_future_exception(self, exception: Exception):
        if self.done_future is not None:
            try:
                self.done_future.set_exception(exception)
            except asyncio.InvalidStateError:
                # The future is already done, ignore the error
                pass


@dataclass
class KernelOwnershipData:
    kernel_id: KernelId
    session_id: SessionId
    agent_id: AgentId
    owner_user_id: Optional[uuid.UUID] = None
    owner_project_id: Optional[uuid.UUID] = None

    def __post_init__(self):
        def to_uuid(value: Optional[str | uuid.UUID]) -> Optional[uuid.UUID]:
            if value is None:
                return None
            elif isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(value)

        self.owner_user_id = to_uuid(self.owner_user_id)
        self.owner_project_id = to_uuid(self.owner_project_id)

    @property
    def owner_user_id_to_str(self) -> Optional[str]:
        return str(self.owner_user_id) if self.owner_user_id is not None else None

    @property
    def owner_project_id_to_str(self) -> Optional[str]:
        return str(self.owner_project_id) if self.owner_project_id is not None else None


WebMiddleware: TypeAlias = Middleware

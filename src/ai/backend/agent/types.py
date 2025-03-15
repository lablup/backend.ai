import asyncio
import enum
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Mapping, Optional, Sequence

import attrs
from aiohttp import web
from aiohttp.typedefs import Handler

from ai.backend.common.events import KernelLifecycleEventReason
from ai.backend.common.types import AgentId, ContainerId, KernelId, MountTypes, SessionId


class AgentBackend(enum.StrEnum):
    # The list of importable backend names under "ai.backend.agent" pkg namespace.
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    DUMMY = "dummy"


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


class ContainerStatus(enum.StrEnum):
    RUNNING = "running"
    RESTARTING = "restarting"
    PAUSED = "paused"
    EXITED = "exited"
    DEAD = "dead"
    REMOVING = "removing"


@attrs.define(auto_attribs=True, slots=True)
class Container:
    id: ContainerId
    status: ContainerStatus
    image: str
    labels: Mapping[str, str]
    ports: Sequence[Port]
    backend_obj: Any  # used to keep the backend-specific data


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


@dataclass
class KernelOwnershipData:
    kernel_id: KernelId
    session_id: SessionId
    agent_id: AgentId
    owner_user_id: Optional[uuid.UUID] = None
    owner_project_id: Optional[uuid.UUID] = None

    def __post_init__(self):
        def to_uuid(value: Optional[str]) -> Optional[uuid.UUID]:
            return uuid.UUID(value) if value is not None else None

        self.owner_user_id = to_uuid(self.owner_user_id)
        self.owner_project_id = to_uuid(self.owner_project_id)

    @property
    def owner_user_id_to_str(self) -> Optional[str]:
        return str(self.owner_user_id) if self.owner_user_id is not None else None

    @property
    def owner_project_id_to_str(self) -> Optional[str]:
        return str(self.owner_project_id) if self.owner_project_id is not None else None


WebMiddleware = Callable[
    [web.Request, Handler],
    Awaitable[web.StreamResponse],
]

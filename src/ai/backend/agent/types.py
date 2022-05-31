import asyncio
import enum
from typing import (
    Any, Optional,
    Mapping,
    Sequence,
)

import attr

from ai.backend.common.types import (
    ContainerId,
    KernelId,
)


class AgentBackend(enum.Enum):
    # The list of importable backend names under "ai.backend.agent" pkg namespace.
    DOCKER = 'docker'
    KUBERNETES = 'kubernetes'


@attr.s(auto_attribs=True, slots=True)
class VolumeInfo:
    name: str             # volume name
    container_path: str   # in-container path as str
    mode: str             # 'rw', 'ro', 'rwm'


@attr.s(auto_attribs=True, slots=True)
class Port:
    host: str
    private_port: int
    host_port: int


class ContainerStatus(str, enum.Enum):
    RUNNING = 'running'
    RESTARTING = 'restarting'
    PAUSED = 'paused'
    EXITED = 'exited'
    DEAD = 'dead'
    REMOVING = 'removing'


@attr.s(auto_attribs=True, slots=True)
class Container:
    id: ContainerId
    status: ContainerStatus
    image: str
    labels: Mapping[str, str]
    ports: Sequence[Port]
    backend_obj: Any  # used to keep the backend-specific data


class LifecycleEvent(int, enum.Enum):
    DESTROY = 0
    CLEAN = 1
    START = 2


@attr.s(auto_attribs=True, slots=True)
class ContainerLifecycleEvent:
    kernel_id: KernelId
    container_id: Optional[ContainerId]
    event: LifecycleEvent
    reason: str
    done_future: Optional[asyncio.Future] = None
    exit_code: Optional[int] = None
    suppress_events: bool = False

    def __str__(self):
        if self.container_id:
            cid = self.container_id[:13]
        else:
            cid = 'unknown'
        return (
            f"LifecycleEvent("
            f"{self.event.name}, "
            f"k:{self.kernel_id}, "
            f"c:{cid}, "
            f"reason:{self.reason!r})"
        )

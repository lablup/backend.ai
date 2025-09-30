import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Optional, Self, override

from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.events.types import (
    AbstractAnycastEvent,
    EventDomain,
)
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import (
    AgentId,
    ContainerId,
    ContainerStatus,
    KernelContainerId,
    KernelId,
)
from ai.backend.logging.types import LogLevel


class BaseAgentEvent(AbstractAnycastEvent):
    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.AGENT


@dataclass
class BaseAgentLifecycleEvent(BaseAgentEvent):
    reason: str

    @override
    def serialize(self) -> tuple:
        return (self.reason,)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(value[0])

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class AgentStartedEvent(BaseAgentLifecycleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_started"


@dataclass
class AgentTerminatedEvent(BaseAgentLifecycleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_terminated"


@dataclass
class AgentOperationEvent(BaseAgentEvent):
    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class AgentErrorEvent(AgentOperationEvent):
    message: str
    traceback: Optional[str] = None
    user: Optional[Any] = None
    context_env: Mapping[str, Any] = field(default_factory=dict)
    severity: LogLevel = LogLevel.ERROR

    @override
    def serialize(self) -> tuple:
        return (
            self.message,
            self.traceback,
            self.user,
            self.context_env,
            self.severity.value,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(
            value[0],
            value[1],
            value[2],
            value[3],
            LogLevel(value[4]),
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_error"


@dataclass
class AgentHeartbeatEvent(AgentOperationEvent):
    agent_info: AgentInfo

    @override
    def serialize(self) -> tuple:
        return (self.agent_info.model_dump(),)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(AgentInfo.model_validate(value[0]))

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_heartbeat"


@dataclass
class AgentImagesRemoveEvent(AgentOperationEvent):
    image_canonicals: list[str]

    @override
    def serialize(self) -> tuple:
        return (self.image_canonicals,)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(value[0])

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_images_remove"


@dataclass
class DoAgentResourceCheckEvent(AgentOperationEvent):
    agent_id: AgentId

    @override
    def serialize(self) -> tuple:
        return (self.agent_id,)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(
            AgentId(value[0]),
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_agent_resource_check"


@dataclass
class ContainerStatusData:
    container_id: ContainerId
    kernel_id: KernelId
    status: ContainerStatus

    def to_dict(self) -> dict[str, str]:
        return {
            "container_id": str(self.container_id),
            "kernel_id": str(self.kernel_id),
            "status": str(self.status),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Self:
        return cls(
            ContainerId(data["container_id"]),
            KernelId(uuid.UUID(data["kernel_id"])),
            ContainerStatus(data["status"]),
        )


@dataclass
class AgentStatusHeartbeat(AgentOperationEvent):
    agent_id: AgentId
    active_containers: list[ContainerStatusData]
    active_kernels: list[KernelContainerId]

    @override
    def serialize(self) -> tuple:
        return (
            self.agent_id,
            tuple(cont.to_dict() for cont in self.active_containers),
            tuple(k.serialize() for k in self.active_kernels),
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(
            AgentId(value[0]),
            [ContainerStatusData.from_dict(raw_container) for raw_container in value[1]],
            [KernelContainerId.deserialize(raw_kernel) for raw_kernel in value[2]],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_status_heartbeat"

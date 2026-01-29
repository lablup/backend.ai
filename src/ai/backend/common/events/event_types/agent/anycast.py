from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Self, override

from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.data.image.types import ScannedImage
from ai.backend.common.events.types import (
    AbstractAnycastEvent,
    EventDomain,
)
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import (
    AgentId,
    ImageCanonical,
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
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
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
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


@dataclass
class AgentErrorEvent(AgentOperationEvent):
    message: str
    traceback: str | None = None
    user: Any | None = None
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


# For compatibility with redis key made with image canonical strings
# Use AgentInstalledImagesRemoveEvent instead of this if possible
@dataclass
class AgentImagesRemoveEvent(AgentOperationEvent):
    image_canonicals: list[ImageCanonical]

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
class AgentInstalledImagesRemoveEvent(AgentOperationEvent):
    scanned_images: Mapping[ImageCanonical, ScannedImage]

    @override
    def serialize(self) -> tuple:
        result = {}
        for canonical, image in self.scanned_images.items():
            result[str(canonical)] = image.to_dict()
        return (result,)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        result = {}
        for canonical, image_data in value[0].items():
            result[ImageCanonical(canonical)] = ScannedImage.from_dict(image_data)
        return cls(result)

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_installed_images_remove"


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

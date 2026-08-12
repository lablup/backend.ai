from collections.abc import Mapping
from typing import Any, Self, override

from pydantic import Field

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


class BaseAgentLifecycleEvent(BaseAgentEvent):
    reason: str

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (self.reason,)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(reason=value[0])

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class AgentStartedEvent(BaseAgentLifecycleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_started"


class AgentTerminatedEvent(BaseAgentLifecycleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_terminated"


class AgentOperationEvent(BaseAgentEvent):
    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class AgentErrorEvent(AgentOperationEvent):
    message: str
    traceback: str | None = None
    user: Any | None = None
    context_env: Mapping[str, Any] = Field(default_factory=dict)
    severity: LogLevel = LogLevel.ERROR

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            self.message,
            self.traceback,
            self.user,
            self.context_env,
            self.severity.value,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            message=value[0],
            traceback=value[1],
            user=value[2],
            context_env=value[3],
            severity=LogLevel(value[4]),
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_error"


class AgentHeartbeatEvent(AgentOperationEvent):
    agent_info: AgentInfo

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (self.agent_info.model_dump(),)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(agent_info=AgentInfo.model_validate(value[0]))

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_heartbeat"


# For compatibility with redis key made with image canonical strings
# Use AgentInstalledImagesRemoveEvent instead of this if possible
class AgentImagesRemoveEvent(AgentOperationEvent):
    image_canonicals: list[ImageCanonical]

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (self.image_canonicals,)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(image_canonicals=value[0])

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_images_remove"


class AgentInstalledImagesRemoveEvent(AgentOperationEvent):
    scanned_images: Mapping[ImageCanonical, ScannedImage]

    @override
    def serialize(self) -> tuple[Any, ...]:
        result = {}
        for canonical, image in self.scanned_images.items():
            result[str(canonical)] = image.to_dict()
        return (result,)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        result = {}
        for canonical, image_data in value[0].items():
            result[ImageCanonical(canonical)] = ScannedImage.from_dict(image_data)
        return cls(scanned_images=result)

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_installed_images_remove"


class DoAgentResourceCheckEvent(AgentOperationEvent):
    agent_id: AgentId

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (self.agent_id,)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(agent_id=AgentId(value[0]))

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_agent_resource_check"

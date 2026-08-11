from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Self, override

from pydantic import Field

from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.data.image.types import ScannedImage
from ai.backend.common.events.payload import AnycastEventPayload
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


class AgentLifecycleEventPayload(AnycastEventPayload):
    reason: str


class AgentErrorEventPayload(AnycastEventPayload):
    message: str
    traceback: str | None = None
    user: Any | None = None
    context_env: Mapping[str, Any] = Field(default_factory=dict)
    severity: LogLevel = LogLevel.ERROR


class AgentHeartbeatEventPayload(AnycastEventPayload):
    agent_info: AgentInfo


class AgentImagesRemoveEventPayload(AnycastEventPayload):
    image_canonicals: list[ImageCanonical]


class AgentInstalledImagesRemoveEventPayload(AnycastEventPayload):
    scanned_images: Mapping[ImageCanonical, ScannedImage]


class DoAgentResourceCheckEventPayload(AnycastEventPayload):
    agent_id: AgentId


class BaseAgentEvent[TPayload: AnycastEventPayload](AbstractAnycastEvent[TPayload]):
    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.AGENT


@dataclass
class BaseAgentLifecycleEvent(BaseAgentEvent[AgentLifecycleEventPayload]):
    reason: str

    @override
    def to_payload(self) -> AgentLifecycleEventPayload:
        return AgentLifecycleEventPayload(
            reason=self.reason,
        )

    @classmethod
    @override
    def from_payload(cls, payload: AgentLifecycleEventPayload) -> Self:
        return cls(
            reason=payload.reason,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (self.reason,)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
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
class AgentOperationEvent[TPayload: AnycastEventPayload](BaseAgentEvent[TPayload]):
    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


@dataclass
class AgentErrorEvent(AgentOperationEvent[AgentErrorEventPayload]):
    message: str
    traceback: str | None = None
    user: Any | None = None
    context_env: Mapping[str, Any] = field(default_factory=dict)
    severity: LogLevel = LogLevel.ERROR

    @override
    def to_payload(self) -> AgentErrorEventPayload:
        return AgentErrorEventPayload(
            message=self.message,
            traceback=self.traceback,
            user=self.user,
            context_env=self.context_env,
            severity=self.severity,
        )

    @classmethod
    @override
    def from_payload(cls, payload: AgentErrorEventPayload) -> Self:
        return cls(
            message=payload.message,
            traceback=payload.traceback,
            user=payload.user,
            context_env=payload.context_env,
            severity=payload.severity,
        )

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
class AgentHeartbeatEvent(AgentOperationEvent[AgentHeartbeatEventPayload]):
    agent_info: AgentInfo

    @override
    def to_payload(self) -> AgentHeartbeatEventPayload:
        return AgentHeartbeatEventPayload(
            agent_info=self.agent_info,
        )

    @classmethod
    @override
    def from_payload(cls, payload: AgentHeartbeatEventPayload) -> Self:
        return cls(
            agent_info=payload.agent_info,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (self.agent_info.model_dump(),)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(AgentInfo.model_validate(value[0]))

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_heartbeat"


# For compatibility with redis key made with image canonical strings
# Use AgentInstalledImagesRemoveEvent instead of this if possible
@dataclass
class AgentImagesRemoveEvent(AgentOperationEvent[AgentImagesRemoveEventPayload]):
    image_canonicals: list[ImageCanonical]

    @override
    def to_payload(self) -> AgentImagesRemoveEventPayload:
        return AgentImagesRemoveEventPayload(
            image_canonicals=self.image_canonicals,
        )

    @classmethod
    @override
    def from_payload(cls, payload: AgentImagesRemoveEventPayload) -> Self:
        return cls(
            image_canonicals=payload.image_canonicals,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (self.image_canonicals,)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(value[0])

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_images_remove"


@dataclass
class AgentInstalledImagesRemoveEvent(AgentOperationEvent[AgentInstalledImagesRemoveEventPayload]):
    scanned_images: Mapping[ImageCanonical, ScannedImage]

    @override
    def to_payload(self) -> AgentInstalledImagesRemoveEventPayload:
        return AgentInstalledImagesRemoveEventPayload(
            scanned_images=self.scanned_images,
        )

    @classmethod
    @override
    def from_payload(cls, payload: AgentInstalledImagesRemoveEventPayload) -> Self:
        return cls(
            scanned_images=payload.scanned_images,
        )

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
        return cls(result)

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_installed_images_remove"


@dataclass
class DoAgentResourceCheckEvent(AgentOperationEvent[DoAgentResourceCheckEventPayload]):
    agent_id: AgentId

    @override
    def to_payload(self) -> DoAgentResourceCheckEventPayload:
        return DoAgentResourceCheckEventPayload(
            agent_id=self.agent_id,
        )

    @classmethod
    @override
    def from_payload(cls, payload: DoAgentResourceCheckEventPayload) -> Self:
        return cls(
            agent_id=payload.agent_id,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (self.agent_id,)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            AgentId(value[0]),
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_agent_resource_check"

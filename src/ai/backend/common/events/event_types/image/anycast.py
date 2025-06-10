from dataclasses import dataclass
from typing import Optional, Self, override

from ai.backend.common.docker import ImageRef
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import AgentId


@dataclass
class BaseImageEvent(AbstractAnycastEvent):
    image: str
    agent_id: AgentId

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.IMAGE

    @override
    def domain_id(self) -> Optional[str]:
        return self.image

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class ImagePullStartedEvent(BaseImageEvent):
    timestamp: float
    image_ref: Optional[ImageRef] = None

    @override
    def serialize(self) -> tuple:
        if self.image_ref is None:
            return (self.image, str(self.agent_id), self.timestamp)

        return (
            self.image,
            str(self.agent_id),
            self.timestamp,
            self.image_ref,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        # Backward compatibility
        if len(value) <= 3:
            return cls(
                image=value[0],
                agent_id=AgentId(value[1]),
                timestamp=value[2],
            )

        return cls(
            image=value[0],
            agent_id=AgentId(value[1]),
            timestamp=value[2],
            image_ref=value[3],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "image_pull_started"


@dataclass
class ImagePullFinishedEvent(BaseImageEvent):
    timestamp: float
    msg: Optional[str] = None
    image_ref: Optional[ImageRef] = None

    @override
    def serialize(self) -> tuple:
        return (
            self.image,
            str(self.agent_id),
            self.timestamp,
            self.msg,
            self.image_ref,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        # Backward compatibility
        if len(value) <= 4:
            return cls(
                image=value[0],
                agent_id=AgentId(value[1]),
                timestamp=value[2],
                msg=value[3],
            )

        return cls(
            image=value[0],
            agent_id=AgentId(value[1]),
            timestamp=value[2],
            msg=value[3],
            image_ref=value[4],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "image_pull_finished"


@dataclass
class ImagePullFailedEvent(BaseImageEvent):
    msg: str
    image_ref: Optional[ImageRef] = None

    @override
    def serialize(self) -> tuple:
        if self.image_ref is None:
            return (self.image, str(self.agent_id), self.msg)
        return (self.image, str(self.agent_id), self.msg, self.image_ref)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        # Backward compatibility
        if len(value) <= 3:
            return cls(
                image=value[0],
                agent_id=AgentId(value[1]),
                msg=value[2],
            )

        return cls(
            image=value[0],
            agent_id=AgentId(value[1]),
            msg=value[2],
            image_ref=value[3],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "image_pull_failed"

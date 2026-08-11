from dataclasses import dataclass
from typing import Any, Self, override

from ai.backend.common.docker import ImageRef
from ai.backend.common.events.payload import AnycastEventPayload
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import AgentId


class ImagePullStartedEventPayload(AnycastEventPayload):
    image: str
    agent_id: AgentId
    timestamp: float
    image_ref: ImageRef | None = None


class ImagePullFinishedEventPayload(AnycastEventPayload):
    image: str
    agent_id: AgentId
    timestamp: float
    msg: str | None = None
    image_ref: ImageRef | None = None


class ImagePullFailedEventPayload(AnycastEventPayload):
    image: str
    agent_id: AgentId
    msg: str
    image_ref: ImageRef | None = None


@dataclass
class BaseImageEvent[TPayload: AnycastEventPayload](AbstractAnycastEvent[TPayload]):
    image: str
    agent_id: AgentId

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.IMAGE

    @override
    def domain_id(self) -> str | None:
        return self.image

    @override
    def user_event(self) -> UserEvent | None:
        return None


@dataclass
class ImagePullStartedEvent(BaseImageEvent[ImagePullStartedEventPayload]):
    timestamp: float
    image_ref: ImageRef | None = None

    @override
    def to_payload(self) -> ImagePullStartedEventPayload:
        return ImagePullStartedEventPayload(
            image=self.image,
            agent_id=self.agent_id,
            timestamp=self.timestamp,
            image_ref=self.image_ref,
        )

    @classmethod
    @override
    def from_payload(cls, payload: ImagePullStartedEventPayload) -> Self:
        return cls(
            image=payload.image,
            agent_id=payload.agent_id,
            timestamp=payload.timestamp,
            image_ref=payload.image_ref,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
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
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
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
class ImagePullFinishedEvent(BaseImageEvent[ImagePullFinishedEventPayload]):
    timestamp: float
    msg: str | None = None
    image_ref: ImageRef | None = None

    @override
    def to_payload(self) -> ImagePullFinishedEventPayload:
        return ImagePullFinishedEventPayload(
            image=self.image,
            agent_id=self.agent_id,
            timestamp=self.timestamp,
            msg=self.msg,
            image_ref=self.image_ref,
        )

    @classmethod
    @override
    def from_payload(cls, payload: ImagePullFinishedEventPayload) -> Self:
        return cls(
            image=payload.image,
            agent_id=payload.agent_id,
            timestamp=payload.timestamp,
            msg=payload.msg,
            image_ref=payload.image_ref,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            self.image,
            str(self.agent_id),
            self.timestamp,
            self.msg,
            self.image_ref,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
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
class ImagePullFailedEvent(BaseImageEvent[ImagePullFailedEventPayload]):
    msg: str
    image_ref: ImageRef | None = None

    @override
    def to_payload(self) -> ImagePullFailedEventPayload:
        return ImagePullFailedEventPayload(
            image=self.image,
            agent_id=self.agent_id,
            msg=self.msg,
            image_ref=self.image_ref,
        )

    @classmethod
    @override
    def from_payload(cls, payload: ImagePullFailedEventPayload) -> Self:
        return cls(
            image=payload.image,
            agent_id=payload.agent_id,
            msg=payload.msg,
            image_ref=payload.image_ref,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        if self.image_ref is None:
            return (self.image, str(self.agent_id), self.msg)
        return (self.image, str(self.agent_id), self.msg, self.image_ref)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
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

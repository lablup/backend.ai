from typing import override

from ai.backend.common.docker import ImageRef
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import AgentId


class BaseImageEvent(AbstractAnycastEvent):
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


class ImagePullStartedEvent(BaseImageEvent):
    timestamp: float
    image_ref: ImageRef | None = None

    @classmethod
    @override
    def event_name(cls) -> str:
        return "image_pull_started"


class ImagePullFinishedEvent(BaseImageEvent):
    timestamp: float
    msg: str | None = None
    image_ref: ImageRef | None = None

    @classmethod
    @override
    def event_name(cls) -> str:
        return "image_pull_finished"


class ImagePullFailedEvent(BaseImageEvent):
    msg: str
    image_ref: ImageRef | None = None

    @classmethod
    @override
    def event_name(cls) -> str:
        return "image_pull_failed"

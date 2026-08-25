from collections.abc import Mapping
from typing import override

from pydantic import Field

from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.data.entity.user import UserID
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
    user: UserID | None = None
    context_env: Mapping[str, str] = Field(default_factory=dict)
    severity: LogLevel = LogLevel.ERROR

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_error"


class AgentHeartbeatEvent(AgentOperationEvent):
    agent_info: AgentInfo

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_heartbeat"


# For compatibility with redis key made with image canonical strings
# Use AgentInstalledImagesRemoveEvent instead of this if possible
class AgentImagesRemoveEvent(AgentOperationEvent):
    image_canonicals: list[ImageCanonical]

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_images_remove"


class AgentInstalledImagesRemoveEvent(AgentOperationEvent):
    scanned_images: Mapping[ImageCanonical, ScannedImage]

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_installed_images_remove"


class DoAgentResourceCheckEvent(AgentOperationEvent):
    agent_id: AgentId

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_agent_resource_check"

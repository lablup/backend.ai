from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.events.types import (
    AbstractBroadcastEvent,
    EventCacheDomain,
    EventDomain,
)
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import SessionId


class BaseSessionEvent(AbstractBroadcastEvent):
    session_id: SessionId

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SESSION

    @override
    def domain_id(self) -> str | None:
        return str(self.session_id)

    @override
    def user_event(self) -> UserEvent | None:
        return None


class DoTerminateSessionEvent(BaseSessionEvent):
    reason: KernelLifecycleEventReason

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_terminate_session"


class SessionCreationEvent(BaseSessionEvent):
    creation_id: str
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN

    @override
    def user_event(self) -> UserEvent | None:
        return None


class SessionEnqueuedBroadcastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_enqueued"


class SessionCheckingPrecondBroadcastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_checking_precondition"


class SessionCancelledBroadcastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_cancelled"


class SessionTerminationEvent(BaseSessionEvent):
    reason: str = ""

    @override
    def user_event(self) -> UserEvent | None:
        return None


class SessionTerminatingBroadcastEvent(SessionTerminationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_terminating"


class SessionTerminatedBroadcastEvent(SessionTerminationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_terminated"


class SessionResultEvent(BaseSessionEvent):
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN
    exit_code: int = -1

    @override
    def user_event(self) -> UserEvent | None:
        return None


class SessionSuccessBroadcastEvent(SessionResultEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_success"


class SessionFailureBroadcastEvent(SessionResultEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_failure"


@dataclass
class SessionSchedulingEventData:
    """Data for each session in batch scheduling event."""

    session_id: SessionId
    creation_id: str


class SchedulingBroadcastEvent(AbstractBroadcastEvent):
    """Individual scheduling event for a session status transition."""

    session_id: SessionId
    creation_id: str
    status_transition: str  # "SCHEDULED", "PREPARING", "CREATING", etc.
    reason: str  # "self-terminated", "user-requested", etc.

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SESSION

    @override
    def domain_id(self) -> str | None:
        return str(self.session_id)

    @classmethod
    @override
    def event_name(cls) -> str:
        return "scheduling"

    @override
    def user_event(self) -> UserEvent | None:
        return None

    @classmethod
    @override
    def cache_domain(cls) -> EventCacheDomain | None:
        return EventCacheDomain.SESSION_SCHEDULER

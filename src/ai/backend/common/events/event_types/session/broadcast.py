from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Self, override

from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.events.payload import BroadcastEventPayload
from ai.backend.common.events.types import (
    AbstractBroadcastEvent,
    EventCacheDomain,
    EventDomain,
)
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import SessionId


class SessionLifecycleEventPayload(BroadcastEventPayload):
    """A bare session lifecycle trigger carries no arguments."""


class SessionEventPayload(BroadcastEventPayload):
    session_id: SessionId


class TerminateSessionEventPayload(BroadcastEventPayload):
    session_id: SessionId
    reason: KernelLifecycleEventReason


class SessionCreationEventPayload(BroadcastEventPayload):
    session_id: SessionId
    creation_id: str
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN


class SessionTerminationEventPayload(BroadcastEventPayload):
    session_id: SessionId
    reason: str = ""


class SessionResultEventPayload(BroadcastEventPayload):
    session_id: SessionId
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN
    exit_code: int = -1


@dataclass
class BaseSessionEvent[TPayload: BroadcastEventPayload](AbstractBroadcastEvent[TPayload]):
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


@dataclass
class DoTerminateSessionEvent(BaseSessionEvent[TerminateSessionEventPayload]):
    reason: KernelLifecycleEventReason

    @override
    def to_payload(self) -> TerminateSessionEventPayload:
        return TerminateSessionEventPayload(
            session_id=self.session_id,
            reason=self.reason,
        )

    @classmethod
    @override
    def from_payload(cls, payload: TerminateSessionEventPayload) -> Self:
        return cls(
            session_id=payload.session_id,
            reason=payload.reason,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            str(self.session_id),
            self.reason,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            SessionId(uuid.UUID(value[0])),
            value[1],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_terminate_session"


@dataclass
class SessionCreationEvent(BaseSessionEvent[SessionCreationEventPayload]):
    creation_id: str
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN

    @override
    def to_payload(self) -> SessionCreationEventPayload:
        return SessionCreationEventPayload(
            session_id=self.session_id,
            creation_id=self.creation_id,
            reason=self.reason,
        )

    @classmethod
    @override
    def from_payload(cls, payload: SessionCreationEventPayload) -> Self:
        return cls(
            session_id=payload.session_id,
            creation_id=payload.creation_id,
            reason=payload.reason,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            str(self.session_id),
            self.creation_id,
            self.reason,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            SessionId(uuid.UUID(value[0])),
            value[1],
            value[2],
        )

    @override
    def user_event(self) -> UserEvent | None:
        return None


@dataclass
class SessionEnqueuedBroadcastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_enqueued"


@dataclass
class SessionCheckingPrecondBroadcastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_checking_precondition"


@dataclass
class SessionCancelledBroadcastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_cancelled"


@dataclass
class SessionTerminationEvent(BaseSessionEvent[SessionTerminationEventPayload]):
    reason: str = ""

    @override
    def to_payload(self) -> SessionTerminationEventPayload:
        return SessionTerminationEventPayload(
            session_id=self.session_id,
            reason=self.reason,
        )

    @classmethod
    @override
    def from_payload(cls, payload: SessionTerminationEventPayload) -> Self:
        return cls(
            session_id=payload.session_id,
            reason=payload.reason,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            str(self.session_id),
            self.reason,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            SessionId(uuid.UUID(value[0])),
            value[1],
        )

    @override
    def user_event(self) -> UserEvent | None:
        return None


@dataclass
class SessionTerminatingBroadcastEvent(SessionTerminationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_terminating"


@dataclass
class SessionTerminatedBroadcastEvent(SessionTerminationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_terminated"


@dataclass
class SessionResultEvent(BaseSessionEvent[SessionResultEventPayload]):
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN
    exit_code: int = -1

    @override
    def to_payload(self) -> SessionResultEventPayload:
        return SessionResultEventPayload(
            session_id=self.session_id,
            reason=self.reason,
            exit_code=self.exit_code,
        )

    @classmethod
    @override
    def from_payload(cls, payload: SessionResultEventPayload) -> Self:
        return cls(
            session_id=payload.session_id,
            reason=payload.reason,
            exit_code=payload.exit_code,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            str(self.session_id),
            self.reason,
            self.exit_code,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            SessionId(uuid.UUID(value[0])),
            value[1],
            value[2],
        )

    @override
    def user_event(self) -> UserEvent | None:
        return None


@dataclass
class SessionSuccessBroadcastEvent(SessionResultEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_success"


@dataclass
class SessionFailureBroadcastEvent(SessionResultEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_failure"


class SchedulingBroadcastEventPayload(BroadcastEventPayload):
    session_id: SessionId
    creation_id: str
    status_transition: str
    reason: str


@dataclass
class SessionSchedulingEventData:
    """Data for each session in batch scheduling event."""

    session_id: SessionId
    creation_id: str


@dataclass
class SchedulingBroadcastEvent(AbstractBroadcastEvent[SchedulingBroadcastEventPayload]):
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

    @override
    def to_payload(self) -> SchedulingBroadcastEventPayload:
        return SchedulingBroadcastEventPayload(
            session_id=self.session_id,
            creation_id=self.creation_id,
            status_transition=self.status_transition,
            reason=self.reason,
        )

    @classmethod
    @override
    def from_payload(cls, payload: SchedulingBroadcastEventPayload) -> Self:
        return cls(
            session_id=payload.session_id,
            creation_id=payload.creation_id,
            status_transition=payload.status_transition,
            reason=payload.reason,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            str(self.session_id),
            self.creation_id,
            self.status_transition,
            self.reason,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            session_id=SessionId(uuid.UUID(value[0])),
            creation_id=value[1],
            status_transition=value[2],
            reason=value[3],
        )

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

from __future__ import annotations

import uuid
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Self, override

from ai.backend.common.events.kernel import KernelLifecycleEventReason
from ai.backend.common.events.payload import AnycastEventPayload
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import SessionExecutionStatus, SessionId


class SessionLifecycleEventPayload(AnycastEventPayload):
    """A bare session lifecycle trigger carries no arguments."""


class SessionEventPayload(AnycastEventPayload):
    session_id: SessionId


class TerminateSessionEventPayload(AnycastEventPayload):
    session_id: SessionId
    reason: KernelLifecycleEventReason


class SessionCreationEventPayload(AnycastEventPayload):
    session_id: SessionId
    creation_id: str
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN


class SessionTerminationEventPayload(AnycastEventPayload):
    session_id: SessionId
    reason: str = ""


class SessionResultEventPayload(AnycastEventPayload):
    session_id: SessionId
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN
    exit_code: int = -1


class SessionLifecycleEvent(AbstractAnycastEvent[SessionLifecycleEventPayload]):
    @override
    def serialize(self) -> tuple[Any, ...]:
        return tuple()

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls()

    @override
    def to_payload(self) -> SessionLifecycleEventPayload:
        return SessionLifecycleEventPayload()

    @classmethod
    @override
    def from_payload(cls, payload: SessionLifecycleEventPayload) -> Self:
        return cls()

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SESSION

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


@dataclass
class BaseSessionEvent[TPayload: AnycastEventPayload](AbstractAnycastEvent[TPayload]):
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
class SessionEnqueuedAnycastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_enqueued"


@dataclass
class SessionCheckingPrecondAnycastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_checking_precondition"


@dataclass
class SessionCancelledAnycastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_cancelled"


@dataclass
class SessionStartedAnycastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_started"


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
class SessionTerminatingAnycastEvent(SessionTerminationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_terminating"


@dataclass
class SessionTerminatedAnycastEvent(SessionTerminationEvent):
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
class SessionSuccessAnycastEvent(SessionResultEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_success"


@dataclass
class SessionFailureAnycastEvent(SessionResultEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_failure"


@dataclass
class BaseSessionExecutionEvent(BaseSessionEvent[SessionEventPayload]):
    @override
    def to_payload(self) -> SessionEventPayload:
        return SessionEventPayload(
            session_id=self.session_id,
        )

    @classmethod
    @override
    def from_payload(cls, payload: SessionEventPayload) -> Self:
        return cls(
            session_id=payload.session_id,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (str(self.session_id),)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            SessionId(uuid.UUID(value[0])),
        )

    @override
    def user_event(self) -> UserEvent | None:
        return None

    @classmethod
    @abstractmethod
    def execution_status(cls) -> SessionExecutionStatus:
        raise NotImplementedError


@dataclass
class ExecutionStartedAnycastEvent(BaseSessionExecutionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_started"

    @classmethod
    @override
    def execution_status(cls) -> SessionExecutionStatus:
        return SessionExecutionStatus.STARTED


@dataclass
class ExecutionFinishedAnycastEvent(BaseSessionExecutionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_finished"

    @classmethod
    @override
    def execution_status(cls) -> SessionExecutionStatus:
        return SessionExecutionStatus.FINISHED


@dataclass
class ExecutionTimeoutAnycastEvent(BaseSessionExecutionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_timeout"

    @classmethod
    @override
    def execution_status(cls) -> SessionExecutionStatus:
        return SessionExecutionStatus.TIMEOUT


@dataclass
class ExecutionCancelledAnycastEvent(BaseSessionExecutionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_cancelled"

    @classmethod
    @override
    def execution_status(cls) -> SessionExecutionStatus:
        return SessionExecutionStatus.CANCELED

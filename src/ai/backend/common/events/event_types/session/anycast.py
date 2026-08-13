from __future__ import annotations

import uuid
from abc import abstractmethod
from typing import Any, Self, override

from ai.backend.common.events.kernel import KernelLifecycleEventReason
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import SessionExecutionStatus, SessionId


class SessionLifecycleEvent(AbstractAnycastEvent):
    @override
    def serialize(self) -> tuple[Any, ...]:
        return tuple()

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
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


class BaseSessionEvent(AbstractAnycastEvent):
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
            session_id=SessionId(uuid.UUID(value[0])),
            reason=value[1],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_terminate_session"


class SessionCreationEvent(BaseSessionEvent):
    creation_id: str
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN

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
            session_id=SessionId(uuid.UUID(value[0])),
            creation_id=value[1],
            reason=value[2],
        )

    @override
    def user_event(self) -> UserEvent | None:
        return None


class SessionEnqueuedAnycastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_enqueued"


class SessionCheckingPrecondAnycastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_checking_precondition"


class SessionCancelledAnycastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_cancelled"


class SessionStartedAnycastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_started"


class SessionTerminationEvent(BaseSessionEvent):
    reason: str = ""

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
            session_id=SessionId(uuid.UUID(value[0])),
            reason=value[1],
        )

    @override
    def user_event(self) -> UserEvent | None:
        return None


class SessionTerminatingAnycastEvent(SessionTerminationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_terminating"


class SessionTerminatedAnycastEvent(SessionTerminationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_terminated"


class SessionResultEvent(BaseSessionEvent):
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN
    exit_code: int = -1

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
            session_id=SessionId(uuid.UUID(value[0])),
            reason=value[1],
            exit_code=value[2],
        )

    @override
    def user_event(self) -> UserEvent | None:
        return None


class SessionSuccessAnycastEvent(SessionResultEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_success"


class SessionFailureAnycastEvent(SessionResultEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_failure"


class BaseSessionExecutionEvent(BaseSessionEvent):
    @override
    def serialize(self) -> tuple[Any, ...]:
        return (str(self.session_id),)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            session_id=SessionId(uuid.UUID(value[0])),
        )

    @override
    def user_event(self) -> UserEvent | None:
        return None

    @classmethod
    @abstractmethod
    def execution_status(cls) -> SessionExecutionStatus:
        raise NotImplementedError


class ExecutionStartedAnycastEvent(BaseSessionExecutionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_started"

    @classmethod
    @override
    def execution_status(cls) -> SessionExecutionStatus:
        return SessionExecutionStatus.STARTED


class ExecutionFinishedAnycastEvent(BaseSessionExecutionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_finished"

    @classmethod
    @override
    def execution_status(cls) -> SessionExecutionStatus:
        return SessionExecutionStatus.FINISHED


class ExecutionTimeoutAnycastEvent(BaseSessionExecutionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_timeout"

    @classmethod
    @override
    def execution_status(cls) -> SessionExecutionStatus:
        return SessionExecutionStatus.TIMEOUT


class ExecutionCancelledAnycastEvent(BaseSessionExecutionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_cancelled"

    @classmethod
    @override
    def execution_status(cls) -> SessionExecutionStatus:
        return SessionExecutionStatus.CANCELED

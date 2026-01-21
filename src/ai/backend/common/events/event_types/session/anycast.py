import uuid
from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional, Self, override

from ai.backend.common.events.kernel import KernelLifecycleEventReason
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import SessionExecutionStatus, SessionId


class SessionLifecycleEvent(AbstractAnycastEvent):
    @override
    def serialize(self) -> tuple:
        return tuple()

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls()

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SESSION

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class DoUpdateSessionStatusEvent(SessionLifecycleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_update_session_status"


@dataclass
class BaseSessionEvent(AbstractAnycastEvent):
    session_id: SessionId

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SESSION

    @override
    def domain_id(self) -> Optional[str]:
        return str(self.session_id)

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class DoTerminateSessionEvent(BaseSessionEvent):
    reason: KernelLifecycleEventReason

    def serialize(self) -> tuple:
        return (
            str(self.session_id),
            self.reason,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(
            SessionId(uuid.UUID(value[0])),
            value[1],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_terminate_session"


@dataclass
class SessionCreationEvent(BaseSessionEvent):
    creation_id: str
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN

    @override
    def serialize(self) -> tuple:
        return (
            str(self.session_id),
            self.creation_id,
            self.reason,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple):
        return cls(
            SessionId(uuid.UUID(value[0])),
            value[1],
            value[2],
        )

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class SessionEnqueuedAnycastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_enqueued"


@dataclass
class SessionScheduledAnycastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_scheduled"


@dataclass
class SessionCheckingPrecondAnycastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_checking_precondition"


@dataclass
class SessionPreparingAnycastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_preparing"


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
class SessionTerminationEvent(BaseSessionEvent):
    reason: str = ""

    @override
    def serialize(self) -> tuple:
        return (
            str(self.session_id),
            self.reason,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple):
        return cls(
            SessionId(uuid.UUID(value[0])),
            value[1],
        )

    @override
    def user_event(self) -> Optional[UserEvent]:
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
class SessionResultEvent(BaseSessionEvent):
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN
    exit_code: int = -1

    def serialize(self) -> tuple:
        return (
            str(self.session_id),
            self.reason,
            self.exit_code,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            SessionId(uuid.UUID(value[0])),
            value[1],
            value[2],
        )

    @override
    def user_event(self) -> Optional[UserEvent]:
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
class BaseSessionExecutionEvent(BaseSessionEvent):
    @override
    def serialize(self) -> tuple:
        return (str(self.session_id),)

    @classmethod
    @override
    def deserialize(cls, value: tuple):
        return cls(
            SessionId(uuid.UUID(value[0])),
        )

    @override
    def user_event(self) -> Optional[UserEvent]:
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
    def execution_status(cls) -> SessionExecutionStatus:
        return SessionExecutionStatus.STARTED


@dataclass
class ExecutionFinishedAnycastEvent(BaseSessionExecutionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_finished"

    @classmethod
    def execution_status(cls) -> SessionExecutionStatus:
        return SessionExecutionStatus.FINISHED


@dataclass
class ExecutionTimeoutAnycastEvent(BaseSessionExecutionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_timeout"

    @classmethod
    def execution_status(cls) -> SessionExecutionStatus:
        return SessionExecutionStatus.TIMEOUT


@dataclass
class ExecutionCancelledAnycastEvent(BaseSessionExecutionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_cancelled"

    @classmethod
    def execution_status(cls) -> SessionExecutionStatus:
        return SessionExecutionStatus.CANCELED

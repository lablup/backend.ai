import uuid
from dataclasses import dataclass
from typing import Optional, Self, override

from ai.backend.common.events.kernel import KernelLifecycleEventReason
from ai.backend.common.events.types import AbstractEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import SessionId


class SessionLifecycleEvent(AbstractEvent):
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
class BaseSessionEvent(AbstractEvent):
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
class SessionEnqueuedEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_enqueued"


@dataclass
class SessionScheduledEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_scheduled"


@dataclass
class SessionCheckingPrecondEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_checking_precondition"


@dataclass
class SessionPreparingEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_preparing"


@dataclass
class SessionCancelledEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_cancelled"


@dataclass
class SessionStartedEvent(SessionCreationEvent):
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
class SessionTerminatingEvent(SessionTerminationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_terminating"


@dataclass
class SessionTerminatedEvent(SessionTerminationEvent):
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
class SessionSuccessEvent(SessionResultEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_success"


@dataclass
class SessionFailureEvent(SessionResultEvent):
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


@dataclass
class ExecutionStartedEvent(BaseSessionExecutionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_started"


@dataclass
class ExecutionFinishedEvent(BaseSessionExecutionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_finished"


@dataclass
class ExecutionTimeoutEvent(BaseSessionExecutionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_timeout"


@dataclass
class ExecutionCancelledEvent(BaseSessionExecutionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_cancelled"

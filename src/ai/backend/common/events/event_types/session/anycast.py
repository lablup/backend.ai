from __future__ import annotations

from abc import abstractmethod
from typing import override

from ai.backend.common.events.kernel import KernelLifecycleEventReason
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import SessionExecutionStatus, SessionId


class SessionLifecycleEvent(AbstractAnycastEvent):
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

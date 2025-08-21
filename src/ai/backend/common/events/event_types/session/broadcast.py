import uuid
from dataclasses import dataclass
from typing import Optional, Self, override

from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.events.types import (
    AbstractBroadcastEvent,
    BatchBroadcastEvent,
    EventDomain,
)
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import SessionId


@dataclass
class BaseSessionEvent(AbstractBroadcastEvent):
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
class SessionEnqueuedBroadcastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_enqueued"


@dataclass
class SessionScheduledBroadcastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_scheduled"


@dataclass
class SessionCheckingPrecondBroadcastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_checking_precondition"


@dataclass
class SessionPreparingBroadcastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_preparing"


@dataclass
class SessionCancelledBroadcastEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_cancelled"


@dataclass
class SessionStartedBroadcastEvent(SessionCreationEvent):
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


@dataclass
class SessionSchedulingEventData:
    """Data for each session in batch scheduling event."""

    session_id: SessionId
    creation_id: str


@dataclass
class SchedulingBroadcastEvent(AbstractBroadcastEvent):
    """Individual scheduling event for a session status transition."""

    session_id: SessionId
    creation_id: str
    status_transition: str  # "SCHEDULED", "PREPARING", "CREATING", etc.

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SESSION

    @override
    def domain_id(self) -> Optional[str]:
        return str(self.session_id)

    @override
    def serialize(self) -> tuple:
        return (
            str(self.session_id),
            self.creation_id,
            self.status_transition,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(
            session_id=SessionId(uuid.UUID(value[0])),
            creation_id=value[1],
            status_transition=value[2],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "scheduling"

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class BatchSchedulingBroadcastEvent(BatchBroadcastEvent):
    """Batch event for multiple sessions going through scheduling stages."""

    # List of session event data
    session_events: list[SessionSchedulingEventData]
    # Session status after transition (e.g., "SCHEDULED", "PREPARING", "CREATING")
    status_transition: str

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SESSION

    @override
    def domain_id(self) -> Optional[str]:
        # For batch events, we don't have a single domain_id
        return None

    @override
    def generate_events(self) -> list[AbstractBroadcastEvent]:
        """Generate individual scheduling events for each session in the batch."""
        events: list[AbstractBroadcastEvent] = []

        # Generate a SchedulingBroadcastEvent for each session
        for session_data in self.session_events:
            events.append(
                SchedulingBroadcastEvent(
                    session_id=session_data.session_id,
                    creation_id=session_data.creation_id,
                    status_transition=self.status_transition,
                )
            )

        return events

    @override
    def serialize(self) -> tuple:
        return (
            [(str(event.session_id), event.creation_id) for event in self.session_events],
            str(self.status_transition),
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(
            session_events=[
                SessionSchedulingEventData(session_id=SessionId(uuid.UUID(sid)), creation_id=cid)
                for sid, cid in value[0]
            ],
            status_transition=value[1],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "batch_scheduling"

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None

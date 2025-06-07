import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, override

from ai.backend.common.events.types import AbstractBroadcastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import KernelId, SessionId

from .types import KernelLifecycleEventReason


@dataclass
class BaseKernelEvent(AbstractBroadcastEvent):
    kernel_id: KernelId

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.KERNEL

    @override
    def domain_id(self) -> Optional[str]:
        return str(self.kernel_id)


@dataclass
class KernelLifecycleEvent(BaseKernelEvent):
    session_id: SessionId
    reason: str = ""

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None

    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_lifecycle_event"


@dataclass
class KernelCreationEvent(KernelLifecycleEvent):
    creation_info: Mapping[str, Any] = field(default_factory=dict)

    @override
    def serialize(self) -> tuple:
        return (
            str(self.kernel_id),
            str(self.session_id),
            self.reason,
            self.creation_info,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple):
        return cls(
            kernel_id=KernelId(uuid.UUID(value[0])),
            session_id=SessionId(uuid.UUID(value[1])),
            reason=value[2],
            creation_info=value[3],
        )

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class KernelPreparingEvent(KernelCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_preparing"


@dataclass
class KernelPullingEvent(KernelCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_pulling"


@dataclass
class KernelCreatingEvent(KernelCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_creating"


class KernelStartedEvent(KernelCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_started"


class KernelCancelledEvent(KernelLifecycleEvent):
    @override
    def serialize(self) -> tuple:
        return (
            str(self.kernel_id),
            str(self.session_id),
            self.reason,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple):
        return cls(
            kernel_id=KernelId(uuid.UUID(value[0])),
            session_id=SessionId(uuid.UUID(value[1])),
            reason=value[2],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_cancelled"


@dataclass
class KernelTerminationEvent(BaseKernelEvent):
    session_id: SessionId
    reason: KernelLifecycleEventReason = KernelLifecycleEventReason.UNKNOWN
    exit_code: int = -1

    @override
    def serialize(self) -> tuple:
        return (
            str(self.kernel_id),
            str(self.session_id),
            self.reason,
            self.exit_code,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple):
        return cls(
            KernelId(uuid.UUID(value[0])),
            session_id=SessionId(uuid.UUID(value[1])),
            reason=value[2],
            exit_code=value[3],
        )

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class KernelTerminatingEvent(KernelTerminationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_terminating"


class KernelTerminatedEvent(KernelTerminationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_terminated"

import enum
import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Self, override

from ai.backend.common.events.types import AbstractEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import ContainerId, KernelId, SessionId


class KernelLifecycleEventReason(enum.StrEnum):
    AGENT_TERMINATION = "agent-termination"
    ALREADY_TERMINATED = "already-terminated"
    ANOMALY_DETECTED = "anomaly-detected"
    EXEC_TIMEOUT = "exec-timeout"
    FAILED_TO_CREATE = "failed-to-create"
    FAILED_TO_START = "failed-to-start"
    FORCE_TERMINATED = "force-terminated"
    BOOTSTRAP_TIMEOUT = "bootstrap-timeout"
    HANG_TIMEOUT = "hang-timeout"
    IDLE_TIMEOUT = "idle-timeout"
    IDLE_SESSION_LIFETIME = "idle-session-lifetime"
    IDLE_UTILIZATION = "idle-utilization"
    KILLED_BY_EVENT = "killed-by-event"
    SERVICE_SCALED_DOWN = "service-scaled-down"
    NEW_CONTAINER_STARTED = "new-container-started"
    PENDING_TIMEOUT = "pending-timeout"
    RESTARTING = "restarting"
    RESTART_TIMEOUT = "restart-timeout"
    RESUMING_AGENT_OPERATION = "resuming-agent-operation"
    SELF_TERMINATED = "self-terminated"
    TASK_FAILED = "task-failed"
    TASK_TIMEOUT = "task-timeout"
    TASK_CANCELLED = "task-cancelled"
    TASK_FINISHED = "task-finished"
    TERMINATED_UNKNOWN_CONTAINER = "terminated-unknown-container"
    UNKNOWN = "unknown"
    USER_REQUESTED = "user-requested"
    NOT_FOUND_IN_MANAGER = "not-found-in-manager"
    CONTAINER_NOT_FOUND = "container-not-found"

    @classmethod
    def from_value(cls, value: Optional[str]) -> Optional[Self]:
        if value is None:
            return None
        try:
            return cls(value)
        except ValueError:
            pass
        return None


@dataclass
class BaseKernelEvent(AbstractEvent):
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


@dataclass
class DoSyncKernelLogsEvent(BaseKernelEvent):
    container_id: str

    def serialize(self) -> tuple:
        return (
            str(self.kernel_id),
            self.container_id,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            KernelId(uuid.UUID(value[0])),
            value[1],
        )

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None

    @classmethod
    def event_name(cls) -> str:
        return "do_sync_kernel_logs"


@dataclass
class KernelHeartbeatEvent(BaseKernelEvent):
    container_id: ContainerId

    @override
    def serialize(self) -> tuple:
        return (
            str(self.kernel_id),
            str(self.container_id),
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple):
        return cls(
            kernel_id=KernelId(uuid.UUID(value[0])),
            container_id=ContainerId(str(value[1])),
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "kernel_heartbeat"

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None

from __future__ import annotations

import asyncio
import enum
import logging
import secrets
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Coroutine,
    Generic,
    Mapping,
    Optional,
    Protocol,
    Self,
    Type,
    TypedDict,
    TypeVar,
    Union,
    cast,
    override,
)

import attrs
from aiomonitor.task import preserve_termination_log
from aiotools.taskgroup import PersistentTaskGroup
from aiotools.taskgroup.types import AsyncExceptionHandler
from redis.asyncio import ConnectionPool

from ai.backend.common.docker import ImageRef
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.exception import UnreachableError
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.logging import BraceStyleAdapter, LogLevel

from .. import msgpack
from ..types import (
    AgentId,
    KernelId,
    ModelServiceStatus,
    QuotaScopeID,
    SessionId,
    VFolderID,
    VolumeMountableNodeType,
)

__all__ = (
    "AbstractEvent",
    "EventCallback",
    "EventDispatcher",
    "EventHandler",
    "EventProducer",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class EventDomain(enum.StrEnum):
    BGTASK = "bgtask"
    IMAGE = "image"
    KERNEL = "kernel"
    MODEL_SERVICE = "model_service"
    ROUTE = "route"
    SCHEDULE = "schedule"
    IDLE_CHECK = "idle_check"
    SESSION = "session"
    AGENT = "agent"
    VFOLDER = "vfolder"
    VOLUME = "volume"
    LOG = "log"


class AbstractEvent(ABC):
    @abstractmethod
    def serialize(self) -> tuple[bytes, ...]:
        """
        Return a msgpack-serializable tuple.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def deserialize(cls, value: tuple[bytes, ...]) -> Self:
        """
        Construct the event args from a tuple deserialized from msgpack.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def event_domain(self) -> EventDomain:
        """
        Return the event domain.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def event_name(cls) -> str:
        """
        Return the event name.
        """
        raise NotImplementedError

    @abstractmethod
    def domain_id(self) -> Optional[str]:
        """
        Return the domain ID.
        It's used to identify the event domain in the event hub.
        """
        raise NotImplementedError

    @abstractmethod
    def user_event(self) -> Optional[UserEvent]:
        """
        Return the event as a UserEvent.
        If user event is not supported, return None.
        """
        raise NotImplementedError


class BaseScheduleEvent(AbstractEvent):
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
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class DoScheduleEvent(BaseScheduleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_schedule"


class DoCheckPrecondEvent(BaseScheduleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_check_precond"


class DoStartSessionEvent(BaseScheduleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_start_session"


class DoScaleEvent(BaseScheduleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_scale"


class BaseIdleCheckEvent(AbstractEvent):
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
        return EventDomain.IDLE_CHECK

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class DoIdleCheckEvent(BaseIdleCheckEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_idle_check"


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


class BaseSessionEvent(AbstractEvent):
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
class DoTerminateSessionEvent(BaseSessionEvent):
    session_id: SessionId
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


class BaseAgentEvent(AbstractEvent):
    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.AGENT


@dataclass
class BaseAgentLifecycleEvent(BaseAgentEvent):
    reason: str

    @override
    def serialize(self) -> tuple:
        return (self.reason,)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(value[0])

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class AgentStartedEvent(BaseAgentLifecycleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_started"


@dataclass
class AgentTerminatedEvent(BaseAgentLifecycleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_terminated"


@dataclass
class AgentOperationEvent(BaseAgentEvent):
    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class AgentErrorEvent(AgentOperationEvent):
    message: str
    traceback: Optional[str] = None
    user: Optional[Any] = None
    context_env: Mapping[str, Any] = field(default_factory=dict)
    severity: LogLevel = LogLevel.ERROR

    @override
    def serialize(self) -> tuple:
        return (
            self.message,
            self.traceback,
            self.user,
            self.context_env,
            self.severity.value,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(
            value[0],
            value[1],
            value[2],
            value[3],
            LogLevel(value[4]),
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_error"


@dataclass
class AgentHeartbeatEvent(AgentOperationEvent):
    agent_info: Mapping[str, Any]

    @override
    def serialize(self) -> tuple:
        return (self.agent_info,)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(value[0])

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_heartbeat"


@dataclass
class AgentImagesRemoveEvent(AgentOperationEvent):
    image_canonicals: list[str]

    @override
    def serialize(self) -> tuple:
        return (self.image_canonicals,)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(value[0])

    @classmethod
    @override
    def event_name(cls) -> str:
        return "agent_images_remove"


@dataclass
class DoAgentResourceCheckEvent(AgentOperationEvent):
    agent_id: AgentId

    @override
    def serialize(self) -> tuple:
        return (self.agent_id,)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(
            AgentId(value[0]),
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_agent_resource_check"


class BaseImageEvent(AbstractEvent):
    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.IMAGE

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class ImagePullStartedEvent(BaseImageEvent):
    image: str
    agent_id: AgentId
    timestamp: float
    image_ref: Optional[ImageRef] = None

    @override
    def serialize(self) -> tuple:
        if self.image_ref is None:
            return (self.image, str(self.agent_id), self.timestamp)

        return (
            self.image,
            str(self.agent_id),
            self.timestamp,
            self.image_ref,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple):
        # Backward compatibility
        if len(value) <= 3:
            return cls(
                image=value[0],
                agent_id=AgentId(value[1]),
                timestamp=value[2],
            )

        return cls(
            image=value[0],
            agent_id=AgentId(value[1]),
            timestamp=value[2],
            image_ref=value[3],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "image_pull_started"


@dataclass
class ImagePullFinishedEvent(BaseImageEvent):
    image: str
    agent_id: AgentId
    timestamp: float
    msg: Optional[str] = None
    image_ref: Optional[ImageRef] = None

    @override
    def serialize(self) -> tuple:
        return (
            self.image,
            str(self.agent_id),
            self.timestamp,
            self.msg,
            self.image_ref,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple):
        # Backward compatibility
        if len(value) <= 4:
            return cls(
                image=value[0],
                agent_id=AgentId(value[1]),
                timestamp=value[2],
                msg=value[3],
            )

        return cls(
            image=value[0],
            agent_id=AgentId(value[1]),
            timestamp=value[2],
            msg=value[3],
            image_ref=value[4],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "image_pull_finished"


@dataclass
class ImagePullFailedEvent(BaseImageEvent):
    image: str
    agent_id: AgentId
    msg: str
    image_ref: Optional[ImageRef] = None

    @override
    def serialize(self) -> tuple:
        if self.image_ref is None:
            return (self.image, str(self.agent_id), self.msg)
        return (self.image, str(self.agent_id), self.msg, self.image_ref)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> ImagePullFailedEvent:
        # Backward compatibility
        if len(value) <= 3:
            return cls(
                image=value[0],
                agent_id=AgentId(value[1]),
                msg=value[2],
            )

        return cls(
            image=value[0],
            agent_id=AgentId(value[1]),
            msg=value[2],
            image_ref=value[3],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "image_pull_failed"


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
    def from_value(cls, value: Optional[str]) -> Optional[KernelLifecycleEventReason]:
        if value is None:
            return None
        try:
            return cls(value)
        except ValueError:
            pass
        return None


class BaseKernelEvent(AbstractEvent):
    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.KERNEL


@dataclass
class KernelLifecycleEvent(BaseKernelEvent):
    kernel_id: KernelId
    session_id: SessionId
    reason: str = ""

    @override
    def domain_id(self) -> Optional[str]:
        return str(self.kernel_id)

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
    def domain_id(self) -> Optional[str]:
        return str(self.kernel_id)

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
class ModelServiceStatusEventArgs(AbstractEvent):
    kernel_id: KernelId
    session_id: SessionId
    model_name: str
    new_status: ModelServiceStatus

    def serialize(self) -> tuple:
        return (
            str(self.kernel_id),
            str(self.session_id),
            self.model_name,
            self.new_status.value,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            kernel_id=KernelId(uuid.UUID(value[0])),
            session_id=SessionId(uuid.UUID(value[1])),
            model_name=value[2],
            new_status=ModelServiceStatus(value[3]),
        )

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.MODEL_SERVICE

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class ModelServiceStatusEvent(ModelServiceStatusEventArgs):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "model_service_status_updated"


@dataclass
class KernelTerminationEvent(BaseKernelEvent):
    kernel_id: KernelId
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
class SessionCreationEvent(AbstractEvent):
    session_id: SessionId
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


class SessionEnqueuedEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_enqueued"


class SessionScheduledEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_scheduled"


class SessionCheckingPrecondEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_checking_precondition"


class SessionPreparingEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_preparing"


class SessionCancelledEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_cancelled"


class SessionStartedEvent(SessionCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_started"


@dataclass
class SessionTerminationEvent(AbstractEvent):
    session_id: SessionId
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


class SessionTerminatingEvent(SessionTerminationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_terminating"


class SessionTerminatedEvent(SessionTerminationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_terminated"


@dataclass
class SessionResultEvent(AbstractEvent):
    session_id: SessionId
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

    @classmethod
    def event_domain(cls) -> EventDomain:
        return EventDomain.SESSION

    @override
    def domain_id(self) -> Optional[str]:
        return str(self.session_id)

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class SessionSuccessEvent(SessionResultEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_success"


class SessionFailureEvent(SessionResultEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "session_failure"


@dataclass
class RouteCreationEvent(AbstractEvent):
    route_id: uuid.UUID = attrs.field()

    def serialize(self) -> tuple:
        return (str(self.route_id),)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(uuid.UUID(value[0]))

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.ROUTE

    @override
    def domain_id(self) -> Optional[str]:
        return str(self.route_id)

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class RouteCreatedEvent(RouteCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "route_created"


@dataclass
class DoSyncKernelLogsEvent(AbstractEvent):
    kernel_id: KernelId
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

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.KERNEL

    @override
    def domain_id(self) -> Optional[str]:
        return str(self.kernel_id)

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None

    @classmethod
    def event_name(cls) -> str:
        return "do_sync_kernel_logs"


@dataclass
class GenericSessionEvent(AbstractEvent):
    session_id: SessionId = attrs.field()

    @override
    def serialize(self) -> tuple:
        return (str(self.session_id),)

    @classmethod
    @override
    def deserialize(cls, value: tuple):
        return cls(
            SessionId(uuid.UUID(value[0])),
        )

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


class ExecutionStartedEvent(GenericSessionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_started"


class ExecutionFinishedEvent(GenericSessionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_finished"


class ExecutionTimeoutEvent(GenericSessionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_timeout"


class ExecutionCancelledEvent(GenericSessionEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "execution_cancelled"


@dataclass
class BaseBgtaskEvent(AbstractEvent, ABC):
    task_id: uuid.UUID

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.BGTASK

    @override
    def domain_id(self) -> Optional[str]:
        return str(self.task_id)

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class BgtaskUpdatedEvent(BaseBgtaskEvent):
    current_progress: float
    total_progress: float
    message: Optional[str] = None

    def serialize(self) -> tuple:
        return (
            str(self.task_id),
            self.current_progress,
            self.total_progress,
            self.message,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            uuid.UUID(value[0]),
            value[1],
            value[2],
            value[3],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "bgtask_updated"


@dataclass
class BaseBgtaskDoneEvent(BaseBgtaskEvent):
    """
    Arguments for events that are triggered when the Bgtask is completed.
    """

    message: Optional[str] = None

    @override
    def serialize(self) -> tuple:
        return (
            str(self.task_id),
            self.message,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple):
        # TODO: Remove this after renaming BgtaskPartialSuccessEvent.
        if len(value) == 3:
            return BgtaskPartialSuccessEvent(
                uuid.UUID(value[0]),
                value[1],
                value[2],
            )
        return cls(
            uuid.UUID(value[0]),
            value[1],
        )


@dataclass
class BgtaskDoneEvent(BaseBgtaskDoneEvent):
    """
    Event triggered when the Bgtask is successfully completed.
    """

    @classmethod
    @override
    def event_name(cls) -> str:
        return "bgtask_done"


@dataclass
class BgtaskAlreadyDoneEvent(BaseBgtaskEvent):
    """
    Event triggered when the Bgtask is already completed.
    An event recreated based on the last status of the Bgtask.
    """

    status: str
    message: Optional[str] = None
    current: str = "0"
    total: str = "0"

    @override
    def serialize(self) -> tuple:
        raise UnreachableError("BgtaskAlreadyDoneEvent should not be serialized.")

    @classmethod
    @override
    def deserialize(cls, value: tuple):
        raise UnreachableError("BsgtaskAlreadyDoneEvent should not be deserialized.")

    @classmethod
    @override
    def event_name(cls) -> str:
        return "bgtask_already_done"


@dataclass
class BgtaskCancelledEvent(BaseBgtaskDoneEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "bgtask_cancelled"


@dataclass
class BgtaskFailedEvent(BaseBgtaskDoneEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "bgtask_failed"


@dataclass
class BgtaskPartialSuccessEvent(BaseBgtaskDoneEvent):
    errors: list[str] = field(default_factory=list)

    @override
    def serialize(self) -> tuple:
        return (
            str(self.task_id),
            self.message,
            self.errors,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple):
        return cls(
            uuid.UUID(value[0]),
            value[1],
            value[2],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "bgtask_partial_success"


class BaseVolumeEvent(AbstractEvent):
    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.VOLUME

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class DoVolumeMountEvent(BaseVolumeEvent):
    # Let storage proxies and agents find the real path of volume
    # with their mount_path or mount_prefix.
    dir_name: str
    volume_backend_name: str
    quota_scope_id: QuotaScopeID

    fs_location: str
    fs_type: str = "nfs"
    cmd_options: Optional[str] = None
    scaling_group: Optional[str] = None

    # if `edit_fstab` is False, `fstab_path` is ignored
    # if `edit_fstab` is True, `fstab_path` or "/etc/fstab" is used to edit fstab
    edit_fstab: bool = False
    fstab_path: str = "/etc/fstab"

    def serialize(self) -> tuple:
        return (
            self.dir_name,
            self.volume_backend_name,
            str(self.quota_scope_id),
            self.fs_location,
            self.fs_type,
            self.cmd_options,
            self.scaling_group,
            self.edit_fstab,
            self.fstab_path,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            dir_name=value[0],
            volume_backend_name=value[1],
            quota_scope_id=QuotaScopeID.parse(value[2]),
            fs_location=value[3],
            fs_type=value[4],
            cmd_options=value[5],
            scaling_group=value[6],
            edit_fstab=value[7],
            fstab_path=value[8],
        )

    @classmethod
    def event_name(cls) -> str:
        return "do_volume_mount"


@dataclass
class DoVolumeUnmountEvent(BaseVolumeEvent):
    # Let storage proxies and agents find the real path of volume
    # with their mount_path or mount_prefix.
    dir_name: str
    volume_backend_name: str
    quota_scope_id: QuotaScopeID
    scaling_group: Optional[str] = None

    # if `edit_fstab` is False, `fstab_path` is ignored
    # if `edit_fstab` is True, `fstab_path` or "/etc/fstab" is used to edit fstab
    edit_fstab: bool = False
    fstab_path: Optional[str] = None

    def serialize(self) -> tuple:
        return (
            self.dir_name,
            self.volume_backend_name,
            str(self.quota_scope_id),
            self.scaling_group,
            self.edit_fstab,
            self.fstab_path,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            dir_name=value[0],
            volume_backend_name=value[1],
            quota_scope_id=QuotaScopeID.parse(value[2]),
            scaling_group=value[3],
            edit_fstab=value[4],
            fstab_path=value[5],
        )

    @classmethod
    def event_name(cls) -> str:
        return "do_volume_unmount"


@dataclass
class BaseAgentVolumeMountEvent(BaseVolumeEvent):
    node_id: str
    node_type: VolumeMountableNodeType
    mount_path: str
    quota_scope_id: QuotaScopeID
    err_msg: Optional[str] = None

    def serialize(self) -> tuple:
        return (
            self.node_id,
            str(self.node_type),
            self.mount_path,
            str(self.quota_scope_id),
            self.err_msg,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            value[0],
            VolumeMountableNodeType(value[1]),
            value[2],
            QuotaScopeID.parse(value[3]),
            value[4],
        )


class VolumeMounted(BaseAgentVolumeMountEvent):
    @classmethod
    def event_name(cls) -> str:
        return "volume_mounted"


class VolumeUnmounted(BaseAgentVolumeMountEvent):
    @classmethod
    def event_name(cls) -> str:
        return "volume_unmounted"


@dataclass
class VFolderEvent(AbstractEvent):
    vfid: VFolderID

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.VFOLDER

    @override
    def domain_id(self) -> Optional[str]:
        return str(self.vfid)

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class VFolderDeletionSuccessEvent(VFolderEvent):
    def serialize(self) -> tuple:
        return (str(self.vfid),)

    @classmethod
    def deserialize(cls, value: tuple) -> Self:
        return cls(
            VFolderID.from_str(value[0]),
        )

    @classmethod
    def event_name(cls) -> str:
        return "vfolder_deletion_success"


@dataclass
class VFolderDeletionFailureEvent(VFolderEvent):
    message: str

    def serialize(self) -> tuple:
        return (
            str(self.vfid),
            self.message,
        )

    @classmethod
    def deserialize(cls, value: tuple) -> Self:
        return cls(
            VFolderID.from_str(value[0]),
            value[1],
        )

    @classmethod
    def event_name(cls) -> str:
        return "vfolder_deletion_failure"


class RedisConnectorFunc(Protocol):
    def __call__(
        self,
    ) -> ConnectionPool: ...


TEvent = TypeVar("TEvent", bound="AbstractEvent")
TEventCov = TypeVar("TEventCov", bound="AbstractEvent")
TContext = TypeVar("TContext")

EventCallback = Union[
    Callable[[TContext, AgentId, TEvent], Coroutine[Any, Any, None]],
    Callable[[TContext, AgentId, TEvent], None],
]


@attrs.define(auto_attribs=True, slots=True, frozen=True, eq=False, order=False)
class EventHandler(Generic[TContext, TEvent]):
    event_cls: Type[TEvent]
    name: str
    context: TContext
    callback: EventCallback[TContext, TEvent]
    coalescing_opts: Optional[CoalescingOptions]
    coalescing_state: CoalescingState
    args_matcher: Callable[[tuple], bool] | None


class CoalescingOptions(TypedDict):
    max_wait: float
    max_batch_size: int


@attrs.define(auto_attribs=True, slots=True)
class CoalescingState:
    batch_size: int = 0
    last_added: float = 0.0
    last_handle: asyncio.TimerHandle | None = None
    fut_sync: asyncio.Future | None = None

    def proceed(self):
        if self.fut_sync is not None and not self.fut_sync.done():
            self.fut_sync.set_result(None)

    async def rate_control(self, opts: CoalescingOptions | None) -> bool:
        if opts is None:
            return True
        loop = asyncio.get_running_loop()
        if self.fut_sync is None:
            self.fut_sync = loop.create_future()
        assert self.fut_sync is not None
        self.last_added = loop.time()
        self.batch_size += 1
        if self.batch_size >= opts["max_batch_size"]:
            assert self.last_handle is not None
            self.last_handle.cancel()
            self.fut_sync.cancel()
            self.last_handle = None
            self.last_added = 0.0
            self.batch_size = 0
            return True
        # Schedule.
        self.last_handle = loop.call_later(
            opts["max_wait"],
            self.proceed,
        )
        if self.last_added > 0 and loop.time() - self.last_added < opts["max_wait"]:
            # Cancel the previously pending task.
            self.last_handle.cancel()
            self.fut_sync.cancel()
            # Reschedule.
            self.fut_sync = loop.create_future()
            self.last_handle = loop.call_later(
                opts["max_wait"],
                self.proceed,
            )
        try:
            await self.fut_sync
        except asyncio.CancelledError:
            if self.last_handle is not None and not self.last_handle.cancelled():
                self.last_handle.cancel()
            return False
        else:
            self.fut_sync = None
            self.last_handle = None
            self.last_added = 0.0
            self.batch_size = 0
            return True


class EventObserver(Protocol):
    def observe_event_success(self, *, event_type: str, duration: float) -> None: ...

    def observe_event_failure(
        self, *, event_type: str, duration: float, exception: BaseException
    ) -> None: ...


class NopEventObserver:
    def observe_event_success(self, *, event_type: str, duration: float) -> None:
        pass

    def observe_event_failure(
        self, *, event_type: str, duration: float, exception: BaseException
    ) -> None:
        pass


class EventDispatcher:
    """
    We have two types of event handlers: consumer and subscriber.

    Consumers use the distribution pattern. Only one consumer among many manager worker processes
    receives the event.

    Consumer example: database updates upon specific events.

    Subscribers use the broadcast pattern. All subscribers in many manager worker processes
    receive the same event.

    Subscriber example: enqueuing events to the queues for event streaming API handlers
    """

    _consumers: defaultdict[str, set[EventHandler[Any, AbstractEvent]]]
    _subscribers: defaultdict[str, set[EventHandler[Any, AbstractEvent]]]
    _msg_queue: AbstractMessageQueue

    _consumer_loop_task: asyncio.Task
    _subscriber_loop_task: asyncio.Task
    _consumer_taskgroup: PersistentTaskGroup
    _subscriber_taskgroup: PersistentTaskGroup

    _log_events: bool
    _metric_observer: EventObserver

    def __init__(
        self,
        message_queue: AbstractMessageQueue,
        log_events: bool = False,
        *,
        consumer_exception_handler: AsyncExceptionHandler | None = None,
        subscriber_exception_handler: AsyncExceptionHandler | None = None,
        event_observer: EventObserver = NopEventObserver(),
    ) -> None:
        self._log_events = log_events
        self._closed = False
        self._consumers = defaultdict(set)
        self._subscribers = defaultdict(set)
        self._msg_queue = message_queue
        self._metric_observer = event_observer
        self._consumer_taskgroup = PersistentTaskGroup(
            name="consumer_taskgroup",
            exception_handler=consumer_exception_handler,
        )
        self._subscriber_taskgroup = PersistentTaskGroup(
            name="subscriber_taskgroup",
            exception_handler=subscriber_exception_handler,
        )
        self._consumer_loop_task = asyncio.create_task(self._consume_loop())
        self._subscriber_loop_task = asyncio.create_task(self._subscribe_loop())

    async def close(self) -> None:
        self._closed = True
        try:
            cancelled_tasks = []
            await self._consumer_taskgroup.shutdown()
            await self._subscriber_taskgroup.shutdown()
            if not self._consumer_loop_task.done():
                self._consumer_loop_task.cancel()
                cancelled_tasks.append(self._consumer_loop_task)
            if not self._subscriber_loop_task.done():
                self._subscriber_loop_task.cancel()
                cancelled_tasks.append(self._subscriber_loop_task)
            await asyncio.gather(*cancelled_tasks, return_exceptions=True)
        except Exception:
            log.exception("unexpected error while closing event dispatcher")

    def consume(
        self,
        event_cls: Type[TEvent],
        context: TContext,
        callback: EventCallback[TContext, TEvent],
        coalescing_opts: Optional[CoalescingOptions] = None,
        *,
        name: str | None = None,
        args_matcher: Callable[[tuple], bool] | None = None,
    ) -> EventHandler[TContext, TEvent]:
        """
        Register a callback as a consumer. When multiple callback registers as a consumer
        on a single event, only one callable among those will be called.

        args_matcher:
          Optional. A callable which accepts event argument and supplies a bool as a return value.
          When specified, EventDispatcher will only execute callback when this lambda returns True.
        """

        if name is None:
            name = f"evh-{secrets.token_urlsafe(16)}"
        handler = EventHandler(
            event_cls,
            name,
            context,
            callback,
            coalescing_opts,
            CoalescingState(),
            args_matcher,
        )
        self._consumers[event_cls.event_name()].add(cast(EventHandler[Any, AbstractEvent], handler))
        return handler

    def unconsume(
        self,
        handler: EventHandler[TContext, TEvent],
    ) -> None:
        self._consumers[handler.event_cls.event_name()].discard(
            cast(EventHandler[Any, AbstractEvent], handler)
        )

    def subscribe(
        self,
        event_cls: Type[TEvent],
        context: TContext,
        callback: EventCallback[TContext, TEvent],
        coalescing_opts: Optional[CoalescingOptions] = None,
        *,
        name: Optional[str] = None,
        override_event_name: Optional[str] = None,
        args_matcher: Optional[Callable[[tuple], bool]] = None,
    ) -> EventHandler[TContext, TEvent]:
        """
        Subscribes to given event. All handlers will be called when certain event pops up.

        args_matcher:
          Optional. A callable which accepts event argument and supplies a bool as a return value.
          When specified, EventDispatcher will only execute callback when this lambda returns True.
        """

        if name is None:
            name = f"evh-{secrets.token_urlsafe(16)}"
        handler = EventHandler(
            event_cls,
            name,
            context,
            callback,
            coalescing_opts,
            CoalescingState(),
            args_matcher,
        )
        override_event_name = override_event_name or event_cls.event_name()
        self._subscribers[override_event_name].add(cast(EventHandler[Any, AbstractEvent], handler))
        return handler

    def unsubscribe(
        self,
        handler: EventHandler[TContext, TEvent],
        *,
        override_event_name: Optional[str] = None,
    ) -> None:
        override_event_name = override_event_name or handler.event_cls.event_name()
        self._subscribers[override_event_name].discard(
            cast(EventHandler[Any, AbstractEvent], handler)
        )

    async def handle(self, evh_type: str, evh: EventHandler, source: AgentId, args: tuple) -> None:
        if evh.args_matcher and not evh.args_matcher(args):
            return
        coalescing_opts = evh.coalescing_opts
        coalescing_state = evh.coalescing_state
        cb = evh.callback
        event_cls = evh.event_cls
        if self._closed:
            return
        if await coalescing_state.rate_control(coalescing_opts):
            if self._closed:
                return
            if self._log_events:
                log.debug("DISPATCH_{}(evh:{})", evh_type, evh.name)
            if asyncio.iscoroutinefunction(cb):
                # mypy cannot catch the meaning of asyncio.iscoroutinefunction().
                await cb(evh.context, source, event_cls.deserialize(args))  # type: ignore
            else:
                cb(evh.context, source, event_cls.deserialize(args))  # type: ignore

    async def dispatch_consumers(
        self,
        event_name: str,
        source: AgentId,
        args: tuple,
    ) -> None:
        if self._log_events:
            log.debug("DISPATCH_CONSUMERS(ev:{}, ag:{})", event_name, source)
        for consumer in self._consumers[event_name].copy():
            self._consumer_taskgroup.create_task(
                self.handle("CONSUMER", consumer, source, args),
            )
            await asyncio.sleep(0)

    async def dispatch_subscribers(
        self,
        event_name: str,
        source: AgentId,
        args: tuple,
    ) -> None:
        if self._log_events:
            log.debug("DISPATCH_SUBSCRIBERS(ev:{}, ag:{})", event_name, source)
        for subscriber in self._subscribers[event_name].copy():
            self._subscriber_taskgroup.create_task(
                self.handle("SUBSCRIBER", subscriber, source, args),
            )
            await asyncio.sleep(0)

    @preserve_termination_log
    async def _consume_loop(self) -> None:
        async for msg in self._msg_queue.consume_queue():  # type: ignore
            if self._closed:
                return
            event_type = "unknown"
            start = time.perf_counter()
            try:
                decoded_event_name = msg.payload[b"name"].decode()
                if decoded_event_name and isinstance(decoded_event_name, str):
                    event_type = decoded_event_name
                await self.dispatch_consumers(
                    decoded_event_name,
                    AgentId(msg.payload[b"source"].decode()),
                    msgpack.unpackb(msg.payload[b"args"]),
                )
                await self._msg_queue.done(msg.msg_id)
                self._metric_observer.observe_event_success(
                    event_type=event_type,
                    duration=time.perf_counter() - start,
                )
            except Exception as e:
                self._metric_observer.observe_event_failure(
                    event_type=event_type,
                    duration=time.perf_counter() - start,
                    exception=e,
                )
                log.exception("EventDispatcher.consume(): unexpected-error")
            except BaseException as e:
                self._metric_observer.observe_event_failure(
                    event_type=event_type,
                    duration=time.perf_counter() - start,
                    exception=e,
                )
                raise

    @preserve_termination_log
    async def _subscribe_loop(self) -> None:
        async for msg in self._msg_queue.subscribe_queue():  # type: ignore
            if self._closed:
                return
            event_type = "unknown"
            start = time.perf_counter()
            try:
                decoded_event_name = msg.payload[b"name"].decode()
                if decoded_event_name and isinstance(decoded_event_name, str):
                    event_type = decoded_event_name
                await self.dispatch_subscribers(
                    decoded_event_name,
                    AgentId(msg.payload[b"source"].decode()),
                    msgpack.unpackb(msg.payload[b"args"]),
                )
                self._metric_observer.observe_event_success(
                    event_type=event_type,
                    duration=time.perf_counter() - start,
                )
            except Exception as e:
                self._metric_observer.observe_event_failure(
                    event_type=event_type,
                    duration=time.perf_counter() - start,
                    exception=e,
                )
                log.exception("EventDispatcher.subscribe(): unexpected-error")
            except BaseException as e:
                self._metric_observer.observe_event_failure(
                    event_type=event_type,
                    duration=time.perf_counter() - start,
                    exception=e,
                )
                raise


class EventProducer:
    _closed: bool
    _msg_queue: AbstractMessageQueue
    _log_events: bool

    def __init__(
        self,
        msg_queue: AbstractMessageQueue,
        *,
        source: AgentId,
        log_events: bool = False,
    ) -> None:
        self._closed = False
        self._msg_queue = msg_queue
        self._source_bytes = source.encode()
        self._log_events = log_events

    async def close(self) -> None:
        self._closed = True
        await self._msg_queue.close()

    async def produce_event(
        self,
        event: AbstractEvent,
        source_override: Optional[AgentId] = None,
    ) -> None:
        if self._closed:
            return
        source_bytes = self._source_bytes
        if source_override is not None:
            source_bytes = source_override.encode()

        raw_event = {
            b"name": event.event_name().encode(),
            b"source": source_bytes,
            b"args": msgpack.packb(event.serialize()),
        }
        await self._msg_queue.send(raw_event)

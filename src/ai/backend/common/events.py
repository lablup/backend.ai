from __future__ import annotations

import abc
import asyncio
import enum
import logging
import secrets
import time
import uuid
from abc import abstractmethod
from collections import defaultdict
from typing import (
    Any,
    Callable,
    ClassVar,
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
from ai.backend.common.message_queue.queue import AbstractMessageQueue, MessageId
from ai.backend.logging import BraceStyleAdapter, LogLevel

from . import msgpack
from .types import (
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


class AbstractEvent(metaclass=abc.ABCMeta):
    # derivatives should define the fields.

    name: ClassVar[str] = "undefined"

    @abc.abstractmethod
    def serialize(self) -> tuple[bytes, ...]:
        """
        Return a msgpack-serializable tuple.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def deserialize(cls, value: tuple[bytes, ...]) -> Self:
        """
        Construct the event args from a tuple deserialized from msgpack.
        """
        pass


class EmptyEventArgs:
    def serialize(self) -> tuple:
        return tuple()

    @classmethod
    def deserialize(cls, value: tuple):
        return cls()


class DoScheduleEvent(EmptyEventArgs, AbstractEvent):
    name = "do_schedule"


class DoCheckPrecondEvent(EmptyEventArgs, AbstractEvent):
    name = "do_check_precond"


class DoStartSessionEvent(EmptyEventArgs, AbstractEvent):
    name = "do_start_session"


class DoScaleEvent(EmptyEventArgs, AbstractEvent):
    name = "do_scale"


class DoIdleCheckEvent(EmptyEventArgs, AbstractEvent):
    name = "do_idle_check"


class DoUpdateSessionStatusEvent(EmptyEventArgs, AbstractEvent):
    name = "do_update_session_status"


@attrs.define(slots=True, frozen=True)
class DoTerminateSessionEvent(AbstractEvent):
    name = "do_terminate_session"

    session_id: SessionId = attrs.field()
    reason: KernelLifecycleEventReason = attrs.field()

    def serialize(self) -> tuple:
        return (
            str(self.session_id),
            self.reason,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            SessionId(uuid.UUID(value[0])),
            value[1],
        )


@attrs.define(slots=True, frozen=True)
class GenericAgentEventArgs:
    reason: str = attrs.field(default="")

    def serialize(self) -> tuple:
        return (self.reason,)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(value[0])


class AgentStartedEvent(GenericAgentEventArgs, AbstractEvent):
    name = "agent_started"


class AgentTerminatedEvent(GenericAgentEventArgs, AbstractEvent):
    name = "agent_terminated"


@attrs.define(slots=True, frozen=True)
class AgentErrorEvent(AbstractEvent):
    name = "agent_error"

    message: str = attrs.field()
    traceback: Optional[str] = attrs.field(default=None)
    user: Optional[Any] = attrs.field(default=None)
    context_env: Mapping[str, Any] = attrs.field(factory=dict)
    severity: LogLevel = attrs.field(default=LogLevel.ERROR)

    def serialize(self) -> tuple:
        return (
            self.message,
            self.traceback,
            self.user,
            self.context_env,
            self.severity.value,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            value[0],
            value[1],
            value[2],
            value[3],
            LogLevel(value[4]),
        )


@attrs.define(slots=True, frozen=True)
class AgentHeartbeatEvent(AbstractEvent):
    name = "agent_heartbeat"

    agent_info: Mapping[str, Any] = attrs.field()

    def serialize(self) -> tuple:
        return (self.agent_info,)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(value[0])


@attrs.define(slots=True, frozen=True)
class AgentImagesRemoveEvent(AbstractEvent):
    name = "agent_images_remove"
    image_canonicals: list[str] = attrs.field()

    def serialize(self) -> tuple:
        return (self.image_canonicals,)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(value[0])


@attrs.define(slots=True, frozen=True)
class DoAgentResourceCheckEvent(AbstractEvent):
    name = "do_agent_resource_check"

    agent_id: AgentId = attrs.field()

    def serialize(self) -> tuple:
        return (self.agent_id,)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            AgentId(value[0]),
        )


@attrs.define(slots=True, frozen=True)
class ImagePullStartedEvent(AbstractEvent):
    name = "image_pull_started"

    image: str = attrs.field()  # deprecated, use image_ref
    agent_id: AgentId = attrs.field()
    timestamp: float = attrs.field()
    image_ref: Optional[ImageRef] = attrs.field(default=None)

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


@attrs.define(slots=True, frozen=True)
class ImagePullFinishedEvent(AbstractEvent):
    name = "image_pull_finished"

    image: str = attrs.field()  # deprecated, use image_ref
    agent_id: AgentId = attrs.field()
    timestamp: float = attrs.field()
    msg: Optional[str] = attrs.field(default=None)
    image_ref: Optional[ImageRef] = attrs.field(default=None)

    def serialize(self) -> tuple:
        return (
            self.image,
            str(self.agent_id),
            self.timestamp,
            self.msg,
            self.image_ref,
        )

    @classmethod
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


@attrs.define(slots=True, frozen=True)
class ImagePullFailedEvent(AbstractEvent):
    name = "image_pull_failed"

    image: str = attrs.field()  # deprecated, use image_ref
    agent_id: AgentId = attrs.field()
    msg: str = attrs.field()
    image_ref: Optional[ImageRef] = attrs.field(default=None)

    def serialize(self) -> tuple:
        if self.image_ref is None:
            return (self.image, str(self.agent_id), self.msg)
        return (self.image, str(self.agent_id), self.msg, self.image_ref)

    @classmethod
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


@attrs.define(slots=True, frozen=True)
class KernelCreationEventArgs:
    kernel_id: KernelId = attrs.field()
    session_id: SessionId = attrs.field()
    reason: str = attrs.field(default="")
    creation_info: Mapping[str, Any] = attrs.field(factory=dict)

    def serialize(self) -> tuple:
        return (
            str(self.kernel_id),
            str(self.session_id),
            self.reason,
            self.creation_info,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            kernel_id=KernelId(uuid.UUID(value[0])),
            session_id=SessionId(uuid.UUID(value[1])),
            reason=value[2],
            creation_info=value[3],
        )


class KernelPreparingEvent(KernelCreationEventArgs, AbstractEvent):
    name = "kernel_preparing"


class KernelPullingEvent(KernelCreationEventArgs, AbstractEvent):
    name = "kernel_pulling"


# TODO: Remove this event
@attrs.define(auto_attribs=True, slots=True)
class KernelPullProgressEvent(AbstractEvent):
    name = "kernel_pull_progress"
    kernel_id: uuid.UUID = attrs.field()
    current_progress: float = attrs.field()
    total_progress: float = attrs.field()
    message: Optional[str] = attrs.field(default=None)

    def serialize(self) -> tuple:
        return (
            str(self.kernel_id),
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


class KernelCreatingEvent(KernelCreationEventArgs, AbstractEvent):
    name = "kernel_creating"


class KernelStartedEvent(KernelCreationEventArgs, AbstractEvent):
    name = "kernel_started"


class KernelCancelledEvent(KernelCreationEventArgs, AbstractEvent):
    name = "kernel_cancelled"


@attrs.define(slots=True, frozen=True)
class ModelServiceStatusEventArgs:
    kernel_id: KernelId = attrs.field()
    session_id: SessionId = attrs.field()
    model_name: str = attrs.field()
    new_status: ModelServiceStatus = attrs.field()

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


class ModelServiceStatusEvent(ModelServiceStatusEventArgs, AbstractEvent):
    name = "model_service_status_updated"


@attrs.define(slots=True, frozen=True)
class KernelTerminationEventArgs:
    kernel_id: KernelId = attrs.field()
    session_id: SessionId = attrs.field()
    reason: KernelLifecycleEventReason = attrs.field(default=KernelLifecycleEventReason.UNKNOWN)
    exit_code: int = attrs.field(default=-1)

    def serialize(self) -> tuple:
        return (
            str(self.kernel_id),
            str(self.session_id),
            self.reason,
            self.exit_code,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            KernelId(uuid.UUID(value[0])),
            session_id=SessionId(uuid.UUID(value[1])),
            reason=value[2],
            exit_code=value[3],
        )


class KernelTerminatingEvent(KernelTerminationEventArgs, AbstractEvent):
    name = "kernel_terminating"


class KernelTerminatedEvent(KernelTerminationEventArgs, AbstractEvent):
    name = "kernel_terminated"


@attrs.define(slots=True, frozen=True)
class SessionCreationEventArgs:
    session_id: SessionId = attrs.field()
    creation_id: str = attrs.field()
    reason: KernelLifecycleEventReason = attrs.field(default=KernelLifecycleEventReason.UNKNOWN)

    def serialize(self) -> tuple:
        return (
            str(self.session_id),
            self.creation_id,
            self.reason,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            SessionId(uuid.UUID(value[0])),
            value[1],
            value[2],
        )


class SessionEnqueuedEvent(SessionCreationEventArgs, AbstractEvent):
    name = "session_enqueued"


class SessionScheduledEvent(SessionCreationEventArgs, AbstractEvent):
    name = "session_scheduled"


class SessionCheckingPrecondEvent(SessionCreationEventArgs, AbstractEvent):
    name = "session_checking_precondition"


class SessionPreparingEvent(SessionCreationEventArgs, AbstractEvent):
    name = "session_preparing"


class SessionCancelledEvent(SessionCreationEventArgs, AbstractEvent):
    name = "session_cancelled"


class SessionStartedEvent(SessionCreationEventArgs, AbstractEvent):
    name = "session_started"


@attrs.define(slots=True, frozen=True)
class SessionTerminationEventArgs:
    session_id: SessionId = attrs.field()
    reason: str = attrs.field(default="")

    def serialize(self) -> tuple:
        return (
            str(self.session_id),
            self.reason,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            SessionId(uuid.UUID(value[0])),
            value[1],
        )


class SessionTerminatingEvent(SessionTerminationEventArgs, AbstractEvent):
    name = "session_terminating"


class SessionTerminatedEvent(SessionTerminationEventArgs, AbstractEvent):
    name = "session_terminated"


@attrs.define(slots=True, frozen=True)
class SessionResultEventArgs:
    session_id: SessionId = attrs.field()
    reason: KernelLifecycleEventReason = attrs.field(default=KernelLifecycleEventReason.UNKNOWN)
    exit_code: int = attrs.field(default=-1)

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


class SessionSuccessEvent(SessionResultEventArgs, AbstractEvent):
    name = "session_success"


class SessionFailureEvent(SessionResultEventArgs, AbstractEvent):
    name = "session_failure"


@attrs.define(slots=True, frozen=True)
class RouteCreationEventArgs:
    route_id: uuid.UUID = attrs.field()

    def serialize(self) -> tuple:
        return (str(self.route_id),)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(uuid.UUID(value[0]))


class RouteCreatedEvent(RouteCreationEventArgs, AbstractEvent):
    name = "route_created"


@attrs.define(auto_attribs=True, slots=True)
class DoSyncKernelLogsEvent(AbstractEvent):
    name = "do_sync_kernel_logs"

    kernel_id: KernelId = attrs.field()
    container_id: str = attrs.field()

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


@attrs.define(auto_attribs=True, slots=True)
class GenericSessionEventArgs(AbstractEvent):
    session_id: SessionId = attrs.field()

    def serialize(self) -> tuple:
        return (str(self.session_id),)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            SessionId(uuid.UUID(value[0])),
        )


class ExecutionStartedEvent(GenericSessionEventArgs, AbstractEvent):
    name = "execution_started"


class ExecutionFinishedEvent(GenericSessionEventArgs, AbstractEvent):
    name = "execution_finished"


class ExecutionTimeoutEvent(GenericSessionEventArgs, AbstractEvent):
    name = "execution_timeout"


class ExecutionCancelledEvent(GenericSessionEventArgs, AbstractEvent):
    name = "execution_cancelled"


class AbstractBgtaskEventType(AbstractEvent):
    @abstractmethod
    def retry_count(self) -> Optional[int]:
        raise NotImplementedError

    @abstractmethod
    def should_close(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def event_body(self, extra_data: dict) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def event_name(self, extra_data: dict) -> str:
        raise NotImplementedError


class AbstractBgtaskDoneEventType(AbstractBgtaskEventType):
    @override
    def should_close(self) -> bool:
        return True


@attrs.define(auto_attribs=True, slots=True)
class BgtaskUpdatedEvent(AbstractBgtaskEventType):
    name = "bgtask_updated"

    task_id: uuid.UUID = attrs.field()
    current_progress: float = attrs.field()
    total_progress: float = attrs.field()
    message: Optional[str] = attrs.field(default=None)

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

    @override
    def retry_count(self) -> Optional[int]:
        return 5

    @override
    def should_close(self) -> bool:
        return False

    @override
    def event_body(self, extra_data: dict) -> dict[str, Any]:
        return {
            "task_id": str(self.task_id),
            "message": self.message,
            "current_progress": self.current_progress,
            "total_progress": self.total_progress,
        }

    @override
    def event_name(self, extra_data: dict) -> str:
        return self.name


@attrs.define(auto_attribs=True, slots=True)
class BgtaskDoneEventArgs:
    """
    Arguments for events that are triggered when the Bgtask is completed.
    """

    task_id: uuid.UUID = attrs.field()
    message: Optional[str] = attrs.field(default=None)

    def serialize(self) -> tuple:
        return (
            str(self.task_id),
            self.message,
        )

    @classmethod
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


class BgtaskDoneEvent(BgtaskDoneEventArgs, AbstractBgtaskDoneEventType):
    """
    Event triggered when the Bgtask is successfully completed.
    """

    name = "bgtask_done"

    @override
    def retry_count(self) -> Optional[int]:
        return None

    @override
    def event_body(self, extra_data: dict) -> dict[str, Any]:
        return {
            "task_id": str(self.task_id),
            "message": self.message,
            **extra_data,
        }

    @override
    def event_name(self, extra_data: dict) -> str:
        if extra_data:
            return f"bgtask_{extra_data['status']}"
        return self.name


class BgtaskCancelledEvent(BgtaskDoneEventArgs, AbstractBgtaskDoneEventType):
    name = "bgtask_cancelled"

    @override
    def retry_count(self) -> Optional[int]:
        return None

    @override
    def event_body(self, extra_data: dict) -> dict[str, Any]:
        return {"task_id": str(self.task_id), "message": self.message}

    @override
    def event_name(self, extra_data):
        return self.name


class BgtaskFailedEvent(BgtaskDoneEventArgs, AbstractBgtaskDoneEventType):
    name = "bgtask_failed"

    @override
    def retry_count(self) -> Optional[int]:
        return None

    @override
    def event_body(self, extra_data: dict) -> dict[str, Any]:
        return {"task_id": str(self.task_id), "message": self.message}

    @override
    def event_name(self, extra_data: dict) -> str:
        return self.name


# TODO: Change the event name after handling the `bgtask_partial_success` event in clients such as WebUI.
# BGTASK_PARTIAL_SUCCESS_EVENT_NAME = "bgtask_partial_success"
BGTASK_PARTIAL_SUCCESS_EVENT_NAME = "bgtask_done"


@attrs.define(auto_attribs=True, slots=True)
class BgtaskPartialSuccessEvent(BgtaskDoneEventArgs, AbstractBgtaskDoneEventType):
    name = BGTASK_PARTIAL_SUCCESS_EVENT_NAME

    errors: list[str] = attrs.field(factory=list)

    def serialize(self) -> tuple:
        return (
            str(self.task_id),
            self.message,
            self.errors,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            uuid.UUID(value[0]),
            value[1],
            value[2],
        )

    @override
    def retry_count(self) -> Optional[int]:
        return None

    @override
    def event_body(self, extra_data: dict) -> dict[str, Any]:
        return {
            "task_id": str(self.task_id),
            "message": self.message,
            "errors": self.errors,
        }

    @override
    def event_name(self, extra_data: dict) -> str:
        return self.name


@attrs.define(slots=True)
class DoVolumeMountEvent(AbstractEvent):
    name = "do_volume_mount"

    # Let storage proxies and agents find the real path of volume
    # with their mount_path or mount_prefix.
    dir_name: str = attrs.field()
    volume_backend_name: str = attrs.field()
    quota_scope_id: QuotaScopeID = attrs.field()

    fs_location: str = attrs.field()
    fs_type: str = attrs.field(default="nfs")
    cmd_options: str | None = attrs.field(default=None)
    scaling_group: str | None = attrs.field(default=None)

    # if `edit_fstab` is False, `fstab_path` is ignored
    # if `edit_fstab` is True, `fstab_path` or "/etc/fstab" is used to edit fstab
    edit_fstab: bool = attrs.field(default=False)
    fstab_path: str = attrs.field(default="/etc/fstab")

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


@attrs.define(slots=True)
class DoVolumeUnmountEvent(AbstractEvent):
    name = "do_volume_unmount"

    # Let storage proxies and agents find the real path of volume
    # with their mount_path or mount_prefix.
    dir_name: str = attrs.field()
    volume_backend_name: str = attrs.field()
    quota_scope_id: QuotaScopeID = attrs.field()
    scaling_group: str | None = attrs.field(default=None)

    # if `edit_fstab` is False, `fstab_path` is ignored
    # if `edit_fstab` is True, `fstab_path` or "/etc/fstab" is used to edit fstab
    edit_fstab: bool = attrs.field(default=False)
    fstab_path: str | None = attrs.field(default=None)

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


@attrs.define(auto_attribs=True, slots=True)
class VolumeMountEventArgs(AbstractEvent):
    node_id: str = attrs.field()
    node_type: VolumeMountableNodeType = attrs.field()
    mount_path: str = attrs.field()
    quota_scope_id: QuotaScopeID = attrs.field()
    err_msg: str | None = attrs.field(default=None)

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


class VolumeMounted(VolumeMountEventArgs, AbstractEvent):
    name = "volume_mounted"


class VolumeUnmounted(VolumeMountEventArgs, AbstractEvent):
    name = "volume_unmounted"


@attrs.define(auto_attribs=True, slots=True)
class VFolderDeletionSuccessEvent(AbstractEvent):
    name = "vfolder_deletion_success"

    vfid: VFolderID

    def serialize(self) -> tuple:
        return (str(self.vfid),)

    @classmethod
    def deserialize(cls, value: tuple) -> Self:
        return cls(
            VFolderID.from_str(value[0]),
        )


@attrs.define(auto_attribs=True, slots=True)
class VFolderDeletionFailureEvent(AbstractEvent):
    name = "vfolder_deletion_failure"

    vfid: VFolderID
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


class _EventHandlerType(enum.StrEnum):
    CONSUMER = "consumer"
    SUBSCRIBER = "subscriber"


@attrs.define(auto_attribs=True, slots=True, frozen=True, eq=False, order=False)
class EventHandler(Generic[TContext, TEvent]):
    event_cls: Type[TEvent]
    name: str
    context: TContext
    callback: EventCallback[TContext, TEvent]
    handler_type: _EventHandlerType
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

    _consumer_loop_task: Optional[asyncio.Task]
    _subscriber_loop_task: Optional[asyncio.Task]
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
        self._consumer_loop_task = None
        self._subscriber_loop_task = None

    async def start(self) -> None:
        self._consumer_loop_task = asyncio.create_task(self._consume_loop())
        self._subscriber_loop_task = asyncio.create_task(self._subscribe_loop())

    async def close(self) -> None:
        self._closed = True
        try:
            cancelled_tasks = []
            await self._consumer_taskgroup.shutdown()
            await self._subscriber_taskgroup.shutdown()
            if self._consumer_loop_task is not None:
                if not self._consumer_loop_task.done():
                    self._consumer_loop_task.cancel()
                    cancelled_tasks.append(self._consumer_loop_task)
            if self._subscriber_loop_task is not None:
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
            _EventHandlerType.CONSUMER,
            coalescing_opts,
            CoalescingState(),
            args_matcher,
        )
        self._consumers[event_cls.name].add(cast(EventHandler[Any, AbstractEvent], handler))
        return handler

    def unconsume(
        self,
        handler: EventHandler[TContext, TEvent],
    ) -> None:
        self._consumers[handler.event_cls.name].discard(
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
            _EventHandlerType.SUBSCRIBER,
            coalescing_opts,
            CoalescingState(),
            args_matcher,
        )
        override_event_name = override_event_name or event_cls.name
        self._subscribers[override_event_name].add(cast(EventHandler[Any, AbstractEvent], handler))
        return handler

    def unsubscribe(
        self,
        handler: EventHandler[TContext, TEvent],
        *,
        override_event_name: Optional[str] = None,
    ) -> None:
        override_event_name = override_event_name or handler.event_cls.name
        self._subscribers[override_event_name].discard(
            cast(EventHandler[Any, AbstractEvent], handler)
        )

    async def _handle(
        self, evh: EventHandler, source: AgentId, args: tuple, msg_id: Optional[MessageId] = None
    ) -> None:
        if evh.args_matcher and not evh.args_matcher(args):
            return
        coalescing_opts = evh.coalescing_opts
        coalescing_state = evh.coalescing_state
        cb = evh.callback
        evh_type = evh.handler_type
        event_cls = evh.event_cls
        event_type: str = event_cls.name
        if self._closed:
            return
        start = time.perf_counter()
        try:
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
                if msg_id is not None:
                    await self._msg_queue.done(msg_id)
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
            log.exception(f"EventDispatcher.{evh_type}(): unexpected-error, {repr(e)}")
            raise
        except BaseException as e:
            self._metric_observer.observe_event_failure(
                event_type=event_type,
                duration=time.perf_counter() - start,
                exception=e,
            )
            raise

    async def dispatch_consumers(
        self,
        event_name: str,
        source: AgentId,
        args: tuple,
        msg_id: MessageId,
    ) -> None:
        if self._log_events:
            log.debug("DISPATCH_CONSUMERS(ev:{}, ag:{})", event_name, source)
        for consumer in self._consumers[event_name].copy():
            self._consumer_taskgroup.create_task(
                self._handle(consumer, source, args, msg_id),
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
                self._handle(subscriber, source, args),
            )
            await asyncio.sleep(0)

    @preserve_termination_log
    async def _consume_loop(self) -> None:
        async for msg in self._msg_queue.consume_queue():  # type: ignore
            if self._closed:
                return
            decoded_event_name = msg.payload[b"name"].decode()
            await self.dispatch_consumers(
                decoded_event_name,
                AgentId(msg.payload[b"source"].decode()),
                msgpack.unpackb(msg.payload[b"args"]),
                msg.msg_id,
            )

    @preserve_termination_log
    async def _subscribe_loop(self) -> None:
        async for msg in self._msg_queue.subscribe_queue():  # type: ignore
            if self._closed:
                return
            decoded_event_name = msg.payload[b"name"].decode()
            await self.dispatch_subscribers(
                decoded_event_name,
                AgentId(msg.payload[b"source"].decode()),
                msgpack.unpackb(msg.payload[b"args"]),
            )


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
            b"name": event.name.encode(),
            b"source": source_bytes,
            b"args": msgpack.packb(event.serialize()),
        }
        await self._msg_queue.send(raw_event)

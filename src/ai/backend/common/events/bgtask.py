import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, override

from ai.backend.common.bgtask.types import TaskStatus
from ai.backend.common.events.dispatcher import AbstractEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.exception import UnreachableError


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

    @abstractmethod
    def status(self) -> TaskStatus:
        raise NotImplementedError


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

    @override
    def status(self) -> TaskStatus:
        return TaskStatus.STARTED


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

    @override
    def status(self) -> TaskStatus:
        return TaskStatus.DONE


@dataclass
class BgtaskAlreadyDoneEvent(BaseBgtaskEvent):
    """
    Event triggered when the Bgtask is already completed.
    An event recreated based on the last status of the Bgtask.
    """

    task_status: TaskStatus
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

    @override
    def status(self) -> TaskStatus:
        return self.task_status


@dataclass
class BgtaskCancelledEvent(BaseBgtaskDoneEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "bgtask_cancelled"

    @override
    def status(self) -> TaskStatus:
        return TaskStatus.CANCELLED


@dataclass
class BgtaskFailedEvent(BaseBgtaskDoneEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "bgtask_failed"

    @override
    def status(self) -> TaskStatus:
        return TaskStatus.FAILED


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

    @override
    def status(self) -> TaskStatus:
        # TODO: When client side is ready, we can change this to `TaskStatus.PARTIAL_SUCCESS`
        return TaskStatus.DONE

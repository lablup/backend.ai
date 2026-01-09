import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, override

from ai.backend.common.bgtask.types import BgtaskStatus
from ai.backend.common.events.types import AbstractBroadcastEvent, EventDomain
from ai.backend.common.events.user_event.user_bgtask_event import (
    UserBgtaskCancelledEvent,
    UserBgtaskDoneEvent,
    UserBgtaskFailedEvent,
    UserBgtaskUpdatedEvent,
)
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.exception import UnreachableError
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class BaseBgtaskEvent(AbstractBroadcastEvent, ABC):
    task_id: uuid.UUID

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.BGTASK

    @override
    def domain_id(self) -> Optional[str]:
        return str(self.task_id)

    @abstractmethod
    def status(self) -> BgtaskStatus:
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
    def status(self) -> BgtaskStatus:
        return BgtaskStatus.UPDATED

    @override
    def user_event(self) -> Optional[UserEvent]:
        return UserBgtaskUpdatedEvent(
            task_id=str(self.task_id),
            message=str(self.message),
            current_progress=self.current_progress,
            total_progress=self.total_progress,
        )


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
    def status(self) -> BgtaskStatus:
        return BgtaskStatus.DONE

    @override
    def user_event(self) -> Optional[UserEvent]:
        return UserBgtaskDoneEvent(
            task_id=str(self.task_id),
            message=str(self.message),
        )


@dataclass
class BgtaskAlreadyDoneEvent(BaseBgtaskEvent):
    """
    Event triggered when the Bgtask is already completed.
    An event recreated based on the last status of the Bgtask.
    """

    task_status: BgtaskStatus
    message: Optional[str] = None
    current: str = "0"
    total: str = "0"

    @override
    def serialize(self) -> tuple:
        raise UnreachableError("BgtaskAlreadyDoneEvent should not be serialized.")

    @classmethod
    @override
    def deserialize(cls, value: tuple):
        raise UnreachableError("BgtaskAlreadyDoneEvent should not be deserialized.")

    @classmethod
    @override
    def event_name(cls) -> str:
        return "bgtask_already_done"

    @override
    def status(self) -> BgtaskStatus:
        return self.task_status

    @override
    def user_event(self) -> Optional[UserEvent]:
        match self.task_status:
            case BgtaskStatus.DONE:
                return UserBgtaskDoneEvent(
                    task_id=str(self.task_id),
                    message=str(self.message),
                )
            case BgtaskStatus.CANCELLED:
                return UserBgtaskCancelledEvent(
                    task_id=str(self.task_id),
                    message=str(self.message),
                )
            case BgtaskStatus.FAILED:
                return UserBgtaskFailedEvent(
                    task_id=str(self.task_id),
                    message=str(self.message),
                )
            case BgtaskStatus.PARTIAL_SUCCESS:
                return UserBgtaskDoneEvent(
                    task_id=str(self.task_id),
                    message=str(self.message),
                )
            case _:
                log.exception("unknown task status {}", self.task_status)
                raise UnreachableError(f"Unknown task status {self.task_status}")


@dataclass
class BgtaskCancelledEvent(BaseBgtaskDoneEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "bgtask_cancelled"

    @override
    def status(self) -> BgtaskStatus:
        return BgtaskStatus.CANCELLED

    @override
    def user_event(self) -> Optional[UserEvent]:
        return UserBgtaskCancelledEvent(
            task_id=str(self.task_id),
            message=str(self.message),
        )


@dataclass
class BgtaskFailedEvent(BaseBgtaskDoneEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "bgtask_failed"

    @override
    def status(self) -> BgtaskStatus:
        return BgtaskStatus.FAILED

    @override
    def user_event(self) -> Optional[UserEvent]:
        return UserBgtaskFailedEvent(
            task_id=str(self.task_id),
            message=str(self.message),
        )


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
    def status(self) -> BgtaskStatus:
        # TODO: When client side is ready, we can change this to `TaskStatus.PARTIAL_SUCCESS`
        return BgtaskStatus.DONE

    @override
    def user_event(self) -> Optional[UserEvent]:
        # TODO: When client side is ready, we can change this to `UserBgtaskPartialSuccessEvent`
        return UserBgtaskDoneEvent(
            task_id=str(self.task_id),
            message=str(self.message),
        )

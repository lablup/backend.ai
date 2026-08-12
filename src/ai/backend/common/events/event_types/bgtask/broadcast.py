from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any, Self, override

from pydantic import Field

from ai.backend.common.bgtask.types import BgtaskStatus
from ai.backend.common.events.types import AbstractBroadcastEvent, EventDomain
from ai.backend.common.events.user_event.user_bgtask_event import (
    UserBgtaskCancelledEvent,
    UserBgtaskDoneEvent,
    UserBgtaskFailedEvent,
    UserBgtaskUpdatedEvent,
)
from ai.backend.common.events.user_event.user_event import UserEvent


class BaseBgtaskEvent(AbstractBroadcastEvent, ABC):
    task_id: uuid.UUID

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.BGTASK

    @override
    def domain_id(self) -> str | None:
        return str(self.task_id)

    @abstractmethod
    def status(self) -> BgtaskStatus:
        raise NotImplementedError


class BgtaskUpdatedEvent(BaseBgtaskEvent):
    current_progress: float
    total_progress: float
    message: str | None = None

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            str(self.task_id),
            self.current_progress,
            self.total_progress,
            self.message,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            task_id=uuid.UUID(value[0]),
            current_progress=value[1],
            total_progress=value[2],
            message=value[3],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "bgtask_updated"

    @override
    def status(self) -> BgtaskStatus:
        return BgtaskStatus.UPDATED

    @override
    def user_event(self) -> UserEvent | None:
        return UserBgtaskUpdatedEvent(
            task_id=str(self.task_id),
            message=str(self.message),
            current_progress=self.current_progress,
            total_progress=self.total_progress,
        )


class BaseBgtaskDoneEvent(BaseBgtaskEvent):
    """
    Arguments for events that are triggered when the Bgtask is completed.
    """

    message: str | None = None

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            str(self.task_id),
            self.message,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            task_id=uuid.UUID(value[0]),
            message=value[1],
        )


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
    def user_event(self) -> UserEvent | None:
        return UserBgtaskDoneEvent(
            task_id=str(self.task_id),
            message=str(self.message),
        )


class BgtaskCancelledEvent(BaseBgtaskDoneEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "bgtask_cancelled"

    @override
    def status(self) -> BgtaskStatus:
        return BgtaskStatus.CANCELLED

    @override
    def user_event(self) -> UserEvent | None:
        return UserBgtaskCancelledEvent(
            task_id=str(self.task_id),
            message=str(self.message),
        )


class BgtaskFailedEvent(BaseBgtaskDoneEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "bgtask_failed"

    @override
    def status(self) -> BgtaskStatus:
        return BgtaskStatus.FAILED

    @override
    def user_event(self) -> UserEvent | None:
        return UserBgtaskFailedEvent(
            task_id=str(self.task_id),
            message=str(self.message),
        )


class BgtaskPartialSuccessEvent(BaseBgtaskDoneEvent):
    errors: list[str] = Field(default_factory=list)

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            str(self.task_id),
            self.message,
            self.errors,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            task_id=uuid.UUID(value[0]),
            message=value[1],
            errors=value[2],
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
    def user_event(self) -> UserEvent | None:
        # TODO: When client side is ready, we can change this to `UserBgtaskPartialSuccessEvent`
        return UserBgtaskDoneEvent(
            task_id=str(self.task_id),
            message=str(self.message),
        )

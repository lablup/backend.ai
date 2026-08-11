from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Never, Self, override

from pydantic import Field as PydanticField

from ai.backend.common.bgtask.types import BgtaskStatus
from ai.backend.common.events.payload import BroadcastEventPayload
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


class BgtaskUpdatedEventPayload(BroadcastEventPayload):
    task_id: uuid.UUID
    current_progress: float
    total_progress: float
    message: str | None = None


class BgtaskDoneEventPayload(BroadcastEventPayload):
    task_id: uuid.UUID
    message: str | None = None


class BgtaskPartialSuccessEventPayload(BroadcastEventPayload):
    task_id: uuid.UUID
    message: str | None = None
    errors: list[str] = PydanticField(default_factory=list)


class BgtaskAlreadyDoneEventPayload(BroadcastEventPayload):
    """
    Declared for completeness only. This event is reconstructed locally from the last
    known task status and never crosses the message queue.
    """

    task_id: uuid.UUID
    task_status: BgtaskStatus
    message: str | None = None
    current: str = "0"
    total: str = "0"


@dataclass
class BaseBgtaskEvent[TPayload: BroadcastEventPayload](AbstractBroadcastEvent[TPayload], ABC):
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


@dataclass
class BgtaskUpdatedEvent(BaseBgtaskEvent[BgtaskUpdatedEventPayload]):
    current_progress: float
    total_progress: float
    message: str | None = None

    @override
    def to_payload(self) -> BgtaskUpdatedEventPayload:
        return BgtaskUpdatedEventPayload(
            task_id=self.task_id,
            current_progress=self.current_progress,
            total_progress=self.total_progress,
            message=self.message,
        )

    @classmethod
    @override
    def from_payload(cls, payload: BgtaskUpdatedEventPayload) -> Self:
        return cls(
            task_id=payload.task_id,
            current_progress=payload.current_progress,
            total_progress=payload.total_progress,
            message=payload.message,
        )

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
    def user_event(self) -> UserEvent | None:
        return UserBgtaskUpdatedEvent(
            task_id=str(self.task_id),
            message=str(self.message),
            current_progress=self.current_progress,
            total_progress=self.total_progress,
        )


@dataclass
class BaseBgtaskDoneEvent[TPayload: BroadcastEventPayload](BaseBgtaskEvent[TPayload]):
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
            uuid.UUID(value[0]),
            value[1],
        )


@dataclass
class BgtaskDoneEvent(BaseBgtaskDoneEvent[BgtaskDoneEventPayload]):
    """
    Event triggered when the Bgtask is successfully completed.
    """

    @override
    def to_payload(self) -> BgtaskDoneEventPayload:
        return BgtaskDoneEventPayload(task_id=self.task_id, message=self.message)

    @classmethod
    @override
    def from_payload(cls, payload: BgtaskDoneEventPayload) -> Self:
        return cls(task_id=payload.task_id, message=payload.message)

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


@dataclass
class BgtaskAlreadyDoneEvent(BaseBgtaskEvent[BgtaskAlreadyDoneEventPayload]):
    """
    Event triggered when the Bgtask is already completed.
    An event recreated based on the last status of the Bgtask.
    """

    task_status: BgtaskStatus
    message: str | None = None
    current: str = "0"
    total: str = "0"

    @override
    def to_payload(self) -> Never:
        raise UnreachableError("BgtaskAlreadyDoneEvent should not be serialized.")

    @classmethod
    @override
    def from_payload(cls, payload: BgtaskAlreadyDoneEventPayload) -> Never:
        raise UnreachableError("BgtaskAlreadyDoneEvent should not be deserialized.")

    @override
    def serialize(self) -> tuple[Any, ...]:
        raise UnreachableError("BgtaskAlreadyDoneEvent should not be serialized.")

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Never:
        raise UnreachableError("BgtaskAlreadyDoneEvent should not be deserialized.")

    @classmethod
    @override
    def event_name(cls) -> str:
        return "bgtask_already_done"

    @override
    def status(self) -> BgtaskStatus:
        return self.task_status

    @override
    def user_event(self) -> UserEvent | None:
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
class BgtaskCancelledEvent(BaseBgtaskDoneEvent[BgtaskDoneEventPayload]):
    @override
    def to_payload(self) -> BgtaskDoneEventPayload:
        return BgtaskDoneEventPayload(task_id=self.task_id, message=self.message)

    @classmethod
    @override
    def from_payload(cls, payload: BgtaskDoneEventPayload) -> Self:
        return cls(task_id=payload.task_id, message=payload.message)

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


@dataclass
class BgtaskFailedEvent(BaseBgtaskDoneEvent[BgtaskDoneEventPayload]):
    @override
    def to_payload(self) -> BgtaskDoneEventPayload:
        return BgtaskDoneEventPayload(task_id=self.task_id, message=self.message)

    @classmethod
    @override
    def from_payload(cls, payload: BgtaskDoneEventPayload) -> Self:
        return cls(task_id=payload.task_id, message=payload.message)

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


@dataclass
class BgtaskPartialSuccessEvent(BaseBgtaskDoneEvent[BgtaskPartialSuccessEventPayload]):
    errors: list[str] = field(default_factory=list)

    @override
    def to_payload(self) -> BgtaskPartialSuccessEventPayload:
        return BgtaskPartialSuccessEventPayload(
            task_id=self.task_id,
            message=self.message,
            errors=self.errors,
        )

    @classmethod
    @override
    def from_payload(cls, payload: BgtaskPartialSuccessEventPayload) -> Self:
        return cls(
            task_id=payload.task_id,
            message=payload.message,
            errors=payload.errors,
        )

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
    def user_event(self) -> UserEvent | None:
        # TODO: When client side is ready, we can change this to `UserBgtaskPartialSuccessEvent`
        return UserBgtaskDoneEvent(
            task_id=str(self.task_id),
            message=str(self.message),
        )

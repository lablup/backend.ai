import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta

from ai.backend.manager.actions.types import OperationStatus


@dataclass
class StartedActionMessage:
    """Message indicating that an action has started."""

    action_id: uuid.UUID
    action_type: str
    entity_id: str | uuid.UUID | None
    request_id: str | None
    triggered_by: str | None
    entity_type: str
    operation_type: str
    created_at: datetime


@dataclass
class FinishedActionMessage:
    """Message indicating that an action has finished."""

    action_id: uuid.UUID
    action_type: str
    entity_id: str | uuid.UUID | None  # TODO: Make this required?
    request_id: str | None
    triggered_by: str | None
    entity_type: str
    operation_type: str
    status: OperationStatus
    description: str
    created_at: datetime
    ended_at: datetime
    duration: timedelta


class AbstractReporter(ABC):
    @abstractmethod
    async def report_started(self, message: StartedActionMessage) -> None:
        raise NotImplementedError

    @abstractmethod
    async def report_finished(self, message: FinishedActionMessage) -> None:
        raise NotImplementedError

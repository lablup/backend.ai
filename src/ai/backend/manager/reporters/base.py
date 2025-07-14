import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from ai.backend.manager.actions.types import OperationStatus


@dataclass
class StartedActionMessage:
    """Message indicating that an action has started."""

    action_id: uuid.UUID
    action_type: str
    entity_id: Optional[str | uuid.UUID]
    request_id: Optional[str]
    triggered_by: Optional[str]
    entity_type: str
    operation_type: str
    created_at: datetime


@dataclass
class FinishedActionMessage:
    """Message indicating that an action has finished."""

    action_id: uuid.UUID
    action_type: str
    entity_id: Optional[str | uuid.UUID]  # TODO: Make this required?
    request_id: Optional[str]
    triggered_by: Optional[str]
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

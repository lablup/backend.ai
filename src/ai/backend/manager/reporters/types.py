import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta

from ai.backend.manager.models.audit_log import OperationStatus


@dataclass
class StartedActionMessage:
    """Message indicating that an action has started."""

    action_id: uuid.UUID
    entity_id: str | uuid.UUID
    entity_type: str
    operation_type: str
    created_at: datetime


@dataclass
class FinishedActionMessage:
    """Message indicating that an action has finished."""

    action_id: uuid.UUID
    entity_id: str | uuid.UUID
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

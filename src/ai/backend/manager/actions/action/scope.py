import uuid
from abc import ABC, abstractmethod
from collections.abc import Collection
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, TypeVar

from ai.backend.common.exception import ErrorCode
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.data.permission.id import (
    ObjectId,
)
from ai.backend.manager.data.permission.parameters import (
    ScopeQueryParams,
)
from ai.backend.manager.errors.common import PermissionDeniedError

from .base import BaseAction


class BaseScopeAction(BaseAction, ABC):
    _accessible_entity_ids: Optional[Collection[ObjectId]] = None

    @property
    def accessible_entity_ids(self) -> Collection[ObjectId]:
        if self._accessible_entity_ids is None:
            raise PermissionDeniedError
        return self._accessible_entity_ids

    @accessible_entity_ids.setter
    def accessible_entity_ids(self, value: Collection[ObjectId]) -> None:
        self._accessible_entity_ids = value

    @abstractmethod
    def requester_user_id(self) -> uuid.UUID:
        """Return the ID of the user who initiated this action."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def scope_type(cls) -> str:
        raise NotImplementedError

    @abstractmethod
    def target_scope_id(self) -> str:
        """Return the ID of the scope this action operates on."""
        raise NotImplementedError

    def permission_query_params(self) -> ScopeQueryParams:
        return ScopeQueryParams(
            user_id=self.requester_user_id(),
            entity_type=self.entity_type(),
            operation_type=self.operation_type(),
            scope_type=self.scope_type(),
            scope_id=self.target_scope_id(),
        )


class BaseScopeActionResult(ABC):
    @abstractmethod
    def scope_id(self) -> str:
        raise NotImplementedError


TBaseScopeAction = TypeVar("TBaseScopeAction", bound=BaseScopeAction)
TBaseScopeActionResult = TypeVar("TBaseScopeActionResult", bound=BaseScopeActionResult)


@dataclass
class BaseScopeActionResultMeta:
    action_id: uuid.UUID
    scope_id: Optional[str]
    accessible_entity_ids: list[ObjectId]
    status: OperationStatus
    description: str
    started_at: datetime
    ended_at: datetime
    duration: timedelta
    error_code: Optional[ErrorCode]

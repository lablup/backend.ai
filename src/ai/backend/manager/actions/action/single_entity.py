import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, TypeVar

from ai.backend.common.exception import ErrorCode
from ai.backend.manager.actions.types import ActionSpec, OperationStatus
from ai.backend.manager.data.permission.id import (
    ObjectId,
)
from ai.backend.manager.data.permission.parameters import (
    SingleEntityQueryParams,
)
from ai.backend.manager.errors.common import PermissionDeniedError


class BaseSingleEntityAction(ABC):
    _accessible_entity_id: Optional[ObjectId] = None

    @property
    def accessible_entity_id(self) -> ObjectId:
        if self._accessible_entity_id is None:
            raise PermissionDeniedError
        return self._accessible_entity_id

    @accessible_entity_id.setter
    def accessible_entity_id(self, value: ObjectId) -> None:
        self._accessible_entity_id = value

    @classmethod
    def spec(cls) -> ActionSpec:
        return ActionSpec(
            entity_type=cls.entity_type(),
            operation_type=cls.operation_type(),
        )

    @classmethod
    @abstractmethod
    def entity_type(cls) -> str:
        raise NotImplementedError

    @abstractmethod
    def entity_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def user_id(self) -> uuid.UUID:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def operation_type(cls) -> str:
        raise NotImplementedError

    def permission_query_params(self) -> SingleEntityQueryParams:
        return SingleEntityQueryParams(
            user_id=self.user_id(),
            entity_type=self.entity_type(),
            operation_type=self.operation_type(),
            entity_id=self.entity_id(),
        )


class BaseSingleEntityActionResult(ABC):
    @abstractmethod
    def entity_id(self) -> str:
        raise NotImplementedError


TSingleEntityAction = TypeVar("TSingleEntityAction", bound=BaseSingleEntityAction)
TSingleEntityActionResult = TypeVar("TSingleEntityActionResult", bound=BaseSingleEntityActionResult)


@dataclass
class BaseSingleEntityActionResultMeta:
    action_id: uuid.UUID
    entity_id: Optional[str]
    accessible_entity_id: Optional[ObjectId]
    status: OperationStatus
    description: str
    started_at: datetime
    ended_at: datetime
    duration: timedelta
    error_code: Optional[ErrorCode]

import uuid
from abc import ABC, abstractmethod
from collections.abc import Collection
from typing import Optional, TypeVar

from ai.backend.manager.data.permission.id import (
    ObjectId,
)
from ai.backend.manager.data.permission.parameters import (
    MultipleEntityQueryParams,
)
from ai.backend.manager.errors.common import PermissionDeniedError

from .base import BaseAction


class BaseMultiEntityAction(BaseAction, ABC):
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

    @abstractmethod
    def target_entity_ids(self) -> list[str]:
        """Return the IDs of the entities this action operates on."""
        raise NotImplementedError

    def permission_query_params(self) -> MultipleEntityQueryParams:
        return MultipleEntityQueryParams(
            user_id=self.requester_user_id(),
            entity_type=self.entity_type(),
            operation_type=self.operation_type(),
            entity_ids=self.target_entity_ids(),
        )


class BaseMultiEntityActionResult(ABC):
    @abstractmethod
    def entity_ids(self) -> list[str]:
        raise NotImplementedError


TBaseMultiEntityAction = TypeVar("TBaseMultiEntityAction", bound=BaseMultiEntityAction)
TBaseMultiEntityActionResult = TypeVar(
    "TBaseMultiEntityActionResult", bound=BaseMultiEntityActionResult
)

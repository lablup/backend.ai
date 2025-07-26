from abc import ABC, abstractmethod
from typing import TypeVar

from ai.backend.manager.data.permission.parameters import (
    SingleEntityQueryParams,
)

from .base import BaseAction


class BaseSingleEntityAction(BaseAction, ABC):
    @abstractmethod
    def target_entity_id(self) -> str:
        """Return the ID of the entity this action operates on."""
        raise NotImplementedError

    def permission_query_params(self) -> SingleEntityQueryParams:
        return SingleEntityQueryParams(
            entity_type=self.entity_type(),
            operation_type=self.operation_type(),
            entity_id=self.target_entity_id(),
        )


class BaseSingleEntityActionResult(ABC):
    @abstractmethod
    def entity_id(self) -> str:
        raise NotImplementedError


TSingleEntityAction = TypeVar("TSingleEntityAction", bound=BaseSingleEntityAction)
TSingleEntityActionResult = TypeVar("TSingleEntityActionResult", bound=BaseSingleEntityActionResult)

from abc import ABC, abstractmethod
from typing import TypeVar

from ai.backend.manager.data.permission.parameters import (
    ScopeQueryParams,
)

from .base import BaseAction


class BaseScopedAction(BaseAction, ABC):
    @classmethod
    @abstractmethod
    def scope_type(cls) -> str:
        raise NotImplementedError

    @abstractmethod
    def scope_id(self) -> str:
        """Return the ID of the scope this action operates on."""
        raise NotImplementedError

    def permission_query_params(self) -> ScopeQueryParams:
        return ScopeQueryParams(
            entity_type=self.entity_type(),
            operation_type=self.operation_type(),
            scope_type=self.scope_type(),
            scope_id=self.scope_id(),
        )


class BaseScopedActionResult(ABC):
    pass


TBaseScopedAction = TypeVar("TBaseScopedAction", bound=BaseScopedAction)
TBaseScopedActionResult = TypeVar("TBaseScopedActionResult", bound=BaseScopedActionResult)

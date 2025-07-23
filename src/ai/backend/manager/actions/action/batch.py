from abc import ABC, abstractmethod
from typing import TypeVar

from ai.backend.manager.data.permission.parameters import (
    BatchQueryParams,
)

from .base import BaseAction


class BaseBatchAction(BaseAction, ABC):
    @abstractmethod
    def target_entity_ids(self) -> list[str]:
        """Return the IDs of the entities this action operates on."""
        raise NotImplementedError

    def permission_query_params(self) -> BatchQueryParams:
        return BatchQueryParams(
            entity_type=self.entity_type(),
            operation_type=self.operation_type(),
            entity_ids=self.target_entity_ids(),
        )


class BaseBatchActionResult(ABC):
    @abstractmethod
    def entity_ids(self) -> list[str]:
        raise NotImplementedError


TBaseBatchAction = TypeVar("TBaseBatchAction", bound=BaseBatchAction)
TBaseBatchActionResult = TypeVar("TBaseBatchActionResult", bound=BaseBatchActionResult)

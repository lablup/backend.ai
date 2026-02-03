from abc import abstractmethod
from typing import TypeVar, override

from ai.backend.manager.data.permission.types import OperationType

from .base import BaseAction, BaseActionResult
from .types import BatchFieldData


class BaseBatchAction(BaseAction):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def entity_ids(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def field_data(self) -> BatchFieldData | None:
        """
        Returns batch field data containing the field type and IDs when the
        action's targets exist as fields of another entity.
        Returns None if these entities are not fields.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def permission_operation_type(cls) -> OperationType:
        raise NotImplementedError


class BaseBatchActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def entity_ids(self) -> list[str]:
        raise NotImplementedError


TBatchAction = TypeVar("TBatchAction", bound=BaseBatchAction)
TBatchActionResult = TypeVar("TBatchActionResult", bound=BaseBatchActionResult)

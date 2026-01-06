from abc import abstractmethod
from collections.abc import Mapping
from typing import TypeVar, override

from ai.backend.manager.data.permission.types import EntityType, OperationType

from .base import BaseAction, BaseActionResult


class BaseBatchAction(BaseAction):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def entity_ids(self) -> list[str]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def field_type(cls) -> EntityType | None:
        """
        Returns the entity type of this action's targets when they exist as fields
        of another entity. Returns None if these entities are not fields.
        """
        raise NotImplementedError

    @abstractmethod
    def field_ids(self) -> Mapping[str, str | None]:
        """
        Returns a mapping of target entity IDs to their field entity IDs.
        The value is None if the corresponding entity is not a field.
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

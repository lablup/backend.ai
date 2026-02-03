from abc import abstractmethod
from typing import TypeVar, override

from ai.backend.common.data.permission.types import OperationType

from .base import BaseAction, BaseActionResult
from .types import FieldData


class BaseSingleEntityAction(BaseAction):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def target_entity_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def field_data(self) -> FieldData | None:
        """
        Returns field data containing the field type and ID when the action's
        target exists as a field of another entity.
        Returns None if this entity is not a field.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def permission_operation_type(cls) -> OperationType:
        raise NotImplementedError


class BaseSingleEntityActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def target_entity_id(self) -> str:
        raise NotImplementedError


TSingleEntityAction = TypeVar("TSingleEntityAction", bound=BaseSingleEntityAction)
TSingleEntityActionResult = TypeVar("TSingleEntityActionResult", bound=BaseSingleEntityActionResult)

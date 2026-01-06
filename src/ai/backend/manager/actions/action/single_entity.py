from abc import abstractmethod
from typing import TypeVar, override

from ai.backend.common.data.permission.types import EntityType, OperationType

from .base import BaseAction, BaseActionResult


class BaseSingleEntityAction(BaseAction):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def target_entity_id(self) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def field_type(cls) -> EntityType | None:
        """
        Returns the entity type of this action's target when it exists as a field
        of another entity. Returns None if this entity is not a field.
        """
        raise NotImplementedError

    @abstractmethod
    def field_id(self) -> str | None:
        """
        Returns the entity ID of this action's target when it exists as a field
        of another entity. Returns None if this entity is not a field.
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

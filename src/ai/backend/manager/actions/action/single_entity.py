from abc import abstractmethod
from typing import TypeVar, override

from ai.backend.manager.data.permission.types import RBACElementRef

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
    def target_element(self) -> RBACElementRef:
        """Return the RBAC element reference for the entity this action targets.

        Used by RBAC validators to check whether the current user has the
        required permission on this entity.

        Implementations must construct the RBACElementRef directly from their
        own fields — do not delegate to ``target_entity_id()``.
        """
        raise NotImplementedError

    @abstractmethod
    def field_data(self) -> FieldData | None:
        """
        Returns field data containing the field type and ID when the action's
        target exists as a field of another entity.
        Returns None if this entity is not a field.
        """
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

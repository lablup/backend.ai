from abc import ABC, abstractmethod

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.entity.types import EntityType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.actions.types import ActionOperationType


class BaseSingleEntityAction(ABC):
    """Base for actions that operate on a single, already-identified entity."""

    @classmethod
    @abstractmethod
    def entity_type(cls) -> EntityType:
        """Return the type of entity that this action applies to."""
        raise NotImplementedError

    @abstractmethod
    def entity_id(self) -> EntityID:
        """Return the ID of the entity that this action applies to."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def required_permission(cls) -> Permission:
        """Return the permission required to perform this action."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def operation_type(cls) -> ActionOperationType:
        """Return the operation that this action performs on the entity."""
        raise NotImplementedError

    @classmethod
    def action_type(cls) -> str:
        """Return the action-type identifier, ``"<entity_type>:<operation_type>"``."""
        return f"{cls.entity_type()}:{cls.operation_type()}"

from abc import ABC, abstractmethod

from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.actions.types import Entity


class BaseSingleEntityAction(ABC):
    """Base for actions that operate on a single, already-identified entity."""

    @abstractmethod
    def entity(self) -> Entity:
        """Return the entity that this action applies to."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def required_permission(cls) -> Permission:
        """Return the permission required to perform this action."""
        raise NotImplementedError

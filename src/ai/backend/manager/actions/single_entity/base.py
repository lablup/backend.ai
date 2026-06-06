from abc import ABC, abstractmethod

from ai.backend.common.data.permission.types import OperationType
from ai.backend.manager.actions.types import Entity


class BaseSingleEntityAction(ABC):
    """Base for actions that operate on a single, already-identified entity."""

    @abstractmethod
    def entity(self) -> Entity:
        """Return the entity that this action applies to."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def operation_type(cls) -> OperationType:
        raise NotImplementedError

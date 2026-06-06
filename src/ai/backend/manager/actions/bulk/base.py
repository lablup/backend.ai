from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.data.permission.types import OperationType
from ai.backend.manager.actions.types import Entity


class BaseBulkAction(ABC):
    """Base for actions that operate on an explicit set of entities at once."""

    @abstractmethod
    def entities(self) -> Sequence[Entity]:
        """Return the Sequence of entities that this action applies to."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def operation_type(cls) -> OperationType:
        raise NotImplementedError

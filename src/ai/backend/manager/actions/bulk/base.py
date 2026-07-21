from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.identifier.entity import EntityID


class BaseBulkAction(ABC):
    """Base for actions that operate on an explicit set of entities at once."""

    @classmethod
    @abstractmethod
    def entity_type(cls) -> EntityType:
        """Return the type of entity that this action applies to."""
        raise NotImplementedError

    @abstractmethod
    def entity_ids(self) -> Sequence[EntityID]:
        """Return the IDs of the entities that this action applies to."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def required_permission(cls) -> Permission:
        """Return the permission required to perform this action."""
        raise NotImplementedError

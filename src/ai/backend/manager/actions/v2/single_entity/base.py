from abc import ABC, abstractmethod
from typing import final

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.types import ActionOperationType


class BaseSingleEntityAction(ABC):
    """Base for actions that operate on a single, already-identified entity."""

    @classmethod
    @abstractmethod
    def operation_type(cls) -> ActionOperationType:
        """Return the operation that this action performs on the entity."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def action_name(cls) -> str:
        """Return the name recorded on audit rows: a lowercase snake_case verb phrase,
        declared rather than derived so a class rename cannot split the recorded
        history. Naming rule: services/AGENTS.md."""
        raise NotImplementedError

    @abstractmethod
    def entity_id(self) -> EntityIdentifier:
        """Return the id of the entity that this action applies to."""
        raise NotImplementedError

    @final
    def entity_type(self) -> EntityType:
        """Derived from the id, which is the only thing that knows it."""
        return self.entity_id().entity_type()

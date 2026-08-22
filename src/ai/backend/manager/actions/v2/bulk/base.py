from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType


class BaseBulkAction(ABC):
    """Base for actions that operate on an explicit set of entities at once."""

    @classmethod
    @abstractmethod
    def operation_type(cls) -> ActionOperationType:
        """Return the operation that this action performs on the entities."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def action_name(cls) -> str:
        """Return the name recorded on audit rows: a lowercase snake_case verb phrase,
        declared rather than derived so a class rename cannot split the recorded
        history. Naming rule: services/AGENTS.md."""
        raise NotImplementedError

    @abstractmethod
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        """Return the IDs of the entities that this action applies to.

        Each names its own type, so one run may reach several kinds at once.
        """
        raise NotImplementedError

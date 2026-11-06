from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.types import ActionOperationType


class BaseScopeAction(ABC):
    """Base for actions that target entities by scope rather than by identity."""

    @abstractmethod
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        """Return the Sequence of scopes that this action applies to."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def entity_type(cls) -> EntityType:
        """Return the type of entity that this action applies to."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def operation_type(cls) -> ActionOperationType:
        """Return the operation that this action performs within the scopes."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def action_name(cls) -> str:
        """Return the name recorded on audit rows: a lowercase snake_case verb phrase,
        declared rather than derived so a class rename cannot split the recorded
        history. Naming rule: services/AGENTS.md."""
        raise NotImplementedError


class GrantingScopeAction(BaseScopeAction):
    """A scope action whose run attaches entities inside the scopes as a second write:
    a role on a roster (BEP-1076)."""

    @abstractmethod
    def granted_targets(self) -> Sequence[EntityIdentifier]:
        """The entities the run grants. The caller needs the operation's permission on each."""
        raise NotImplementedError

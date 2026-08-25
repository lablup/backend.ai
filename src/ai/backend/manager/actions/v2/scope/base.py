from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.manager.actions.types import ActionOperationType


class BaseScopeAction(ABC):
    """Base for actions that target entities by scope rather than by identity."""

    @abstractmethod
    def scope_targets(self) -> Sequence[ScopeRef]:
        """Return the Sequence of scopes that this action applies to."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        """The scope types this action may be targeted at.

        Bounds what :meth:`scope_targets` returns. `global` stands for a scope type the
        caller names, which no fixed set bounds; the empty sequence is no scope at all.
        """
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

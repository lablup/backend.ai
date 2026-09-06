from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.manager.actions.types import ActionOperationType

__all__ = ("BaseRelationAction",)


class BaseRelationAction(ABC):
    """Base for actions that link two entities, or unlink them.

    Names the scopes it is about and no entity type. What it writes is a row standing
    between two entities, which is neither of them, so there is no "permission on this
    type within this scope" to ask — the permission is asked of each named scope itself.

    Deliberately not a :class:`~..scope.base.BaseScopeAction`: that shape's check reads
    the acted-on entity type at each scope, and a relation has none to read. Keeping the
    roots apart means a relation cannot flow through the path that would ask the wrong
    question.

    Design rationale: `proposals/BEP-1075-entity-relation-operations.md`.
    """

    @classmethod
    @abstractmethod
    def operation_type(cls) -> ActionOperationType:
        """Return the operation this action performs on the relation."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def action_name(cls) -> str:
        """Return the name recorded on audit rows: a lowercase snake_case verb phrase,
        declared rather than derived so a class rename cannot split the recorded
        history. Naming rule: services/AGENTS.md."""
        raise NotImplementedError

    @abstractmethod
    def scope_targets(self) -> Sequence[ScopeRef]:
        """Return the scopes this run links or unlinks.

        Every one of them has to permit the run: you must be able to touch both to put
        them in a relation.
        """
        raise NotImplementedError

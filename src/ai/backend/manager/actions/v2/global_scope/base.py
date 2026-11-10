from abc import ABC, abstractmethod

from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType


class BaseGlobalAction(ABC):
    """Base for actions on system-wide state.

    Declares no target: the `global` singleton is the scope, and what it grants on the
    action's entity type is the check.
    """

    @classmethod
    @abstractmethod
    def entity_type(cls) -> EntityType:
        """Return the type of entity that this action applies to."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def operation_type(cls) -> ActionOperationType:
        """Return the operation that this action performs."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def action_name(cls) -> str:
        """Return the name recorded on audit rows: a lowercase snake_case verb phrase,
        declared rather than derived so a class rename cannot split the recorded
        history. Naming rule: services/AGENTS.md."""
        raise NotImplementedError

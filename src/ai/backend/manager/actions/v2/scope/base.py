from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.manager.actions.types import ActionOperationType, ActionSpec


class BaseScopeAction(ABC):
    """Base for actions that target entities by scope rather than by identity."""

    @abstractmethod
    def scope_targets(self) -> Sequence[ScopeRef]:
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
    def spec(cls) -> ActionSpec:
        """Return the "entity:operation" spec keying reporter subscriptions and audit records."""
        return ActionSpec(
            entity_type=cls.entity_type(),
            operation_type=cls.operation_type(),
        )

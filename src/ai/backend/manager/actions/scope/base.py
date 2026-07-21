from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.permission.types import Permission


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
    def required_permission(cls) -> Permission:
        """Return the permission required to perform this action."""
        raise NotImplementedError

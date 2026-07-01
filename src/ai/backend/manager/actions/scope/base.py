from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.entity.types import EntityType
from ai.backend.manager.actions.types import Scope


class BaseScopeAction(ABC):
    """Base for actions that target entities by scope rather than by identity."""

    @abstractmethod
    def scope_targets(self) -> Sequence[Scope]:
        """Return the Sequence of scopes that this action applies to."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def entity_type(self) -> EntityType:
        """Return the type of entity that this action applies to."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def required_permission(cls) -> Permission:
        """Return the permission required to perform this action."""
        raise NotImplementedError

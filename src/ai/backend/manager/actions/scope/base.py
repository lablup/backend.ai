from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.data.permission.types import OperationType
from ai.backend.common.entity.types import EntityType
from ai.backend.manager.actions.types import Scope


class ScopeTarget:
    """An entity type qualified by the scope it is resolved within."""

    scope: Scope
    entity_type: EntityType


class BaseScopeAction(ABC):
    """Base for actions that target entities by scope rather than by identity."""

    @abstractmethod
    def scope_targets(self) -> Sequence[ScopeTarget]:
        """Return the Sequence of scopes that this action applies to."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def operation_type(cls) -> OperationType:
        raise NotImplementedError

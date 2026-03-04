from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseBatchAction
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult


@dataclass
class SessionAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION


@dataclass
class SessionBatchAction(BaseBatchAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION


@dataclass
class SessionScopeAction(BaseScopeAction):
    """Base class for session actions that operate within a scope (domain/project).

    Used for operations like creating or searching sessions within a specific scope.
    Subclasses must implement scope_type(), scope_id(), and target_element() methods.

    Note: Scope should typically be USER scope (user_id), not GLOBAL.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION


@dataclass
class SessionScopeActionResult(BaseScopeActionResult):
    pass

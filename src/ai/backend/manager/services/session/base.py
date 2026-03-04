from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseBatchAction
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import FieldData


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
    Each concrete class must define _scope_type and _scope_id fields for RBAC validation.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION


@dataclass
class SessionScopeActionResult(BaseScopeActionResult):
    pass


@dataclass
class SessionSingleEntityAction(BaseSingleEntityAction):
    """Base class for session actions that operate on a specific session.

    Used for operations like getting, updating, or deleting a specific session.
    Each concrete class must implement target_entity_id() and target_element()
    for RBAC validation.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION

    @override
    def field_data(self) -> FieldData | None:
        return None


@dataclass
class SessionSingleEntityActionResult(BaseSingleEntityActionResult):
    pass

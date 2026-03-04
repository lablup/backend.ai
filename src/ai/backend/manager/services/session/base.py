from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.actions.action import BaseAction, BaseBatchAction
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import FieldData
from ai.backend.manager.data.permission.types import RBACElementRef


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


@dataclass
class SessionSingleEntityAction(BaseSingleEntityAction):
    """Base class for session actions that operate on a specific session.

    Used for operations like getting, updating, or deleting a specific session.
    Subclasses must provide a session_id (resolved from session_name if needed)
    before RBAC validation.

    Note: Empty session_id is not allowed and will raise ValueError.
    """

    session_id: str | None = field(default=None, kw_only=True)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION

    @override
    def field_data(self) -> FieldData | None:
        return None

    @override
    def target_entity_id(self) -> str:
        if self.session_id is None or not self.session_id.strip():
            raise ValueError(
                f"{self.__class__.__name__}.session_id must be set to a non-empty string "
                "before RBAC validation"
            )
        return self.session_id

    @override
    def target_element(self) -> RBACElementRef:
        # Reuse target_entity_id() for validation
        return RBACElementRef(
            element_type=RBACElementType.SESSION,
            element_id=self.target_entity_id(),
        )


@dataclass
class SessionSingleEntityActionResult(BaseSingleEntityActionResult):
    pass

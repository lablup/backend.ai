from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.actions.action import BaseAction, BaseBatchAction
from ai.backend.manager.actions.action.single_entity import BaseSingleEntityAction
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
class SessionSingleEntityAction(BaseSingleEntityAction):
    """Base class for session actions that operate on a specific session.
    Subclasses must provide a session_id before RBAC validation."""

    session_id: str | None = field(default=None, kw_only=True)

    @override
    def target_entity_id(self) -> str:
        if self.session_id is None or not self.session_id.strip():
            raise ValueError(f"{self.__class__.__name__}.session_id must be set")
        return self.session_id

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.SESSION,
            element_id=self.target_entity_id(),
        )

    @override
    def field_data(self) -> FieldData | None:
        """Session is not a field, so this always returns None."""
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION

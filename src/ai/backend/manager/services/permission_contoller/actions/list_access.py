from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class ListAccessAction(RoleAction):
    user_id: UUID
    operation: str
    target_entity_type: str
    target_scope_type: str
    target_scope_id: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.target_scope_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list_access"


@dataclass
class ListAccessActionResult(BaseActionResult):
    scope_allowed_operations: dict[ScopeId, set[str]]  # Maps scope IDs to allowed operations
    object_allowed_operations: dict[ObjectId, set[str]]  # Maps object IDs to allowed operations

    @override
    def entity_id(self) -> Optional[str]:
        return None

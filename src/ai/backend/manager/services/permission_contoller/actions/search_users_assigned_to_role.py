from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.permission.role import AssignedUserListResult
from ai.backend.manager.repositories.base import Querier
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class SearchUsersAssignedToRoleAction(RoleAction):
    role_id: UUID
    querier: Querier

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.role_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_users"


@dataclass
class SearchUsersAssignedToRoleActionResult(BaseActionResult):
    users: AssignedUserListResult

    @override
    def entity_id(self) -> Optional[str]:
        return None

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.permission_controller.types import ScopedPermissionSearchScope
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class SearchScopedPermissionsAction(RoleAction):
    querier: BatchQuerier
    scope: ScopedPermissionSearchScope | None = None

    @override
    def entity_id(self) -> str | None:
        return str(self.scope.role_id) if self.scope else None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"


@dataclass
class SearchScopedPermissionsActionResult(BaseActionResult):
    items: list[PermissionData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None

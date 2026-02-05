from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.permission.permission_group import PermissionGroupData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.permission_controller.types import PermissionGroupSearchScope
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class SearchPermissionGroupsAction(RoleAction):
    querier: BatchQuerier
    scope: PermissionGroupSearchScope | None = None

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"


@dataclass
class SearchPermissionGroupsActionResult(BaseActionResult):
    items: list[PermissionGroupData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None

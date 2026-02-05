from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.permission.object_permission import ObjectPermissionData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class SearchObjectPermissionsAction(RoleAction):
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"


@dataclass
class SearchObjectPermissionsActionResult(BaseActionResult):
    items: list[ObjectPermissionData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None

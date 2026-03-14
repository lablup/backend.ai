from dataclasses import dataclass, field
from typing import override

from ai.backend.manager.actions.action import SearchActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.permission_controller.types import RoleSearchScope
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class SearchRolesAction(RoleAction):
    querier: BatchQuerier
    scope: RoleSearchScope | None = field(default=None)

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchRolesActionResult(SearchActionResult[RoleData]):
    pass

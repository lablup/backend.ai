from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.permission.role import RoleListResult
from ai.backend.manager.repositories.base import Querier
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class SearchRolesAction(RoleAction):
    querier: Querier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"


@dataclass
class SearchRolesActionResult(BaseActionResult):
    roles: RoleListResult

    @override
    def entity_id(self) -> Optional[str]:
        return None

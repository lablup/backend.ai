from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.identifier.domain import DomainID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.group.actions.base import (
    GroupScopeAction,
    GroupScopeActionResult,
)


@dataclass
class CreateGroupAction(GroupScopeAction):
    creator: Creator[GroupRow]
    _domain_name: str
    _domain_id: DomainID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self._domain_name

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, str(self._domain_id))


@dataclass
class CreateGroupActionResult(GroupScopeActionResult):
    data: GroupData | None
    _domain_name: str

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self._domain_name

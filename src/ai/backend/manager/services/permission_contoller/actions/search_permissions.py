"""Actions for reading scoped permissions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import (
    GLOBAL_ENTITY_TYPE,
    EntityIdentifier,
    EntityType,
)
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.action import SearchActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.ops.base import (
    BulkScopedSearchOpsAction,
    SearchGlobalOpsAction,
)
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.scopes import (
    AssignedUserPermissionOperationScope,
)
from ai.backend.manager.models.rbac_models.permission.searchers import PermissionSearcher
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.permission_contoller.actions.base import PermissionAction


@dataclass(frozen=True)
class GlobalSearchPermissionsAction(SearchGlobalOpsAction[PermissionRow, PermissionData]):
    """Page through every scoped permission in the installation."""

    searcher: PermissionSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GLOBAL_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_permissions"

    @override
    def to_searcher(self) -> PermissionSearcher:
        return self.searcher


@dataclass(frozen=True)
class SearchPermissionsByUserAction(BulkScopedSearchOpsAction[PermissionRow, PermissionData]):
    """Page through the permissions one user holds.

    Answered for at that user: a permission row is a field of the role granting it, and
    reading what someone may do is a read of them.
    """

    user_id: UserID
    searcher: PermissionSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_permissions_by_user"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return (self.user_id,)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (AssignedUserPermissionOperationScope(user_id=self.user_id),)

    @override
    def to_searcher(self) -> PermissionSearcher:
        return self.searcher


@dataclass
class BatchLoadPermissionsAction(PermissionAction):
    """Load the permission rows a GQL node field names, by their ids or their roles'.

    Ungated: the node the field hangs off was authorized before the loader ran, so
    there is nothing left for this read to answer for.
    """

    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class BatchLoadPermissionsActionResult(SearchActionResult[PermissionData]):
    pass

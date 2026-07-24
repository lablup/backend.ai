from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.actions.action.bulk import BaseBulkActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.app_config_fragment.actions.base import (
    AppConfigFragmentBulkAction,
    AppConfigFragmentBulkTarget,
)


@dataclass
class BatchLoadAppConfigFragmentsByIdsAction(AppConfigFragmentBulkAction):
    """Load many fragments by id at once, for the GraphQL DataLoader.

    A bulk action rather than repeated :class:`GetAppConfigFragmentAction` calls, so the bulk
    RBAC validator authorizes every requested fragment in one pass — the same gate a bulk
    update crosses. The batch is all-or-nothing: one unauthorized id denies the call, which
    is what keeps ``node(id:)`` from reporting whether a fragment the caller cannot read
    exists.
    """

    fragment_ids: Sequence[AppConfigFragmentID]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def targets(self) -> Sequence[AppConfigFragmentBulkTarget]:
        return [
            AppConfigFragmentBulkTarget(fragment_id=fragment_id)
            for fragment_id in self.fragment_ids
        ]


@dataclass
class BatchLoadAppConfigFragmentsByIdsActionResult(BaseBulkActionResult):
    """The fragments for the requested ids, in query order.

    Not partial-success: the bulk RBAC gate authorizes every requested id, so any id that
    fails it — missing or unauthorized alike — denies the whole batch with
    ``PermissionDeniedError`` rather than being dropped from the result.
    """

    items: Sequence[AppConfigFragmentData]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return [
            RBACElementRef(
                element_type=RBACElementType.APP_CONFIG_FRAGMENT, element_id=str(fragment.id)
            )
            for fragment in self.items
        ]

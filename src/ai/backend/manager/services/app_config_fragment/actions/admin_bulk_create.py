from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.bulk_types import (
    AppConfigFragmentBulkItem,
    AppConfigFragmentBulkItemError,
)
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.app_config_fragment.actions.base import AppConfigFragmentTarget


@dataclass
class AdminBulkCreateAppConfigFragmentsAction(BaseBulkAction[AppConfigFragmentTarget]):
    """Bulk-create rows. `items` carries the per-item payloads; targets
    are keyed by each item's natural key (row ids do not exist at
    action-creation time)."""

    items: list[AppConfigFragmentBulkItem] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def targets(self) -> Sequence[AppConfigFragmentTarget]:
        return [AppConfigFragmentTarget(key=item.key) for item in self.items]


@dataclass
class AdminBulkCreateAppConfigFragmentsActionResult(BaseBulkActionResult):
    created: list[AppConfigFragmentData]
    failed: list[AppConfigFragmentBulkItemError]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return [
            RBACElementRef(
                element_type=RBACElementType.APP_CONFIG,
                element_id=str(fragment.id),
            )
            for fragment in self.created
        ]

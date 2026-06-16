from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.bulk_types import (
    AppConfigFragmentBulkItemError,
    MyAppConfigFragmentBulkItem,
)
from ai.backend.manager.data.app_config_fragment.types import AppConfigData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.app_config_fragment.actions.base import MyAppConfigFragmentTarget


@dataclass
class MyBulkUpdateAppConfigFragmentsAction(BaseBulkAction[MyAppConfigFragmentTarget]):
    """Self-service bulk update — see `MyBulkCreateAppConfigFragmentsAction`."""

    items: list[MyAppConfigFragmentBulkItem] = field(default_factory=list)

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
        return ActionOperationType.UPDATE

    @override
    def targets(self) -> Sequence[MyAppConfigFragmentTarget]:
        return [MyAppConfigFragmentTarget(name=item.name) for item in self.items]


@dataclass
class MyBulkUpdateAppConfigFragmentsActionResult(BaseBulkActionResult):
    updated: list[AppConfigData]
    failed: list[AppConfigFragmentBulkItemError]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return [
            RBACElementRef(
                element_type=RBACElementType.APP_CONFIG,
                element_id=item.name,
            )
            for item in self.updated
        ]

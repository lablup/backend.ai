from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_policy.types import (
    AppConfigPolicyBulkItemError,
    AppConfigPolicyBulkUpdateItem,
    AppConfigPolicyData,
)
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.app_config_policy.actions.base import AppConfigPolicyTarget


@dataclass
class AdminBulkUpdateAppConfigPoliciesAction(BaseBulkAction[AppConfigPolicyTarget]):
    """`items` carries `(id, scope_sources)` pairs targeting existing
    policy rows. `config_name` is immutable and therefore not on the
    update payload."""

    items: list[AppConfigPolicyBulkUpdateItem] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_POLICY

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def targets(self) -> Sequence[AppConfigPolicyTarget]:
        return [AppConfigPolicyTarget(id=item.id) for item in self.items]


@dataclass
class AdminBulkUpdateAppConfigPoliciesActionResult(BaseBulkActionResult):
    updated: list[AppConfigPolicyData]
    failed: list[AppConfigPolicyBulkItemError]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return [
            RBACElementRef(
                element_type=RBACElementType.APP_CONFIG_POLICY,
                element_id=str(policy.id),
            )
            for policy in self.updated
        ]

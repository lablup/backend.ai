from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.action.types import ActionTarget
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_policy.types import (
    AppConfigPolicyBulkCreateItem,
    AppConfigPolicyBulkItemError,
    AppConfigPolicyData,
)
from ai.backend.manager.data.permission.types import RBACElementRef


@dataclass(frozen=True)
class AppConfigPolicyCreateTarget(ActionTarget):
    """Bulk-action target for a to-be-created policy, keyed by its
    `config_name` (no row id exists yet at validation time)."""

    config_name: str

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.APP_CONFIG_POLICY,
            element_id=self.config_name,
        )


@dataclass
class AdminBulkCreateAppConfigPoliciesAction(BaseBulkAction[AppConfigPolicyCreateTarget]):
    """`items` carries the per-item payloads (`config_name` + scope chain)."""

    items: list[AppConfigPolicyBulkCreateItem] = field(default_factory=list)

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
        return ActionOperationType.CREATE

    @override
    def targets(self) -> Sequence[AppConfigPolicyCreateTarget]:
        return [AppConfigPolicyCreateTarget(config_name=item.config_name) for item in self.items]


@dataclass
class AdminBulkCreateAppConfigPoliciesActionResult(BaseBulkActionResult):
    created: list[AppConfigPolicyData]
    failed: list[AppConfigPolicyBulkItemError]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return [
            RBACElementRef(
                element_type=RBACElementType.APP_CONFIG_POLICY,
                element_id=str(policy.id),
            )
            for policy in self.created
        ]

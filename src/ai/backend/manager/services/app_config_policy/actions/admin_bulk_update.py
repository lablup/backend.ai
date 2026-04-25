from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_policy.bulk_types import (
    AppConfigPolicyBulkItem,
    AppConfigPolicyBulkItemError,
)
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData


@dataclass
class AdminBulkUpdateAppConfigPoliciesAction(BaseBulkAction[AppConfigPolicyBulkItem]):
    """See `AdminBulkCreateAppConfigPoliciesAction` for the entity_ids /
    items convention."""

    items: list[AppConfigPolicyBulkItem] = field(default_factory=list)

    @override
    def typed_entity_ids(self) -> list[AppConfigPolicyBulkItem]:
        return list(self.items)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class AdminBulkUpdateAppConfigPoliciesActionResult(BaseBulkActionResult):
    updated: list[AppConfigPolicyData]
    failed: list[AppConfigPolicyBulkItemError]

    @override
    def entity_ids(self) -> list[str]:
        return [str(policy.id) for policy in self.updated]

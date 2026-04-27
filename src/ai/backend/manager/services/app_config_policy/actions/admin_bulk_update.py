from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_policy.types import (
    AppConfigPolicyBulkItemError,
    AppConfigPolicyBulkUpdateItem,
    AppConfigPolicyData,
)


@dataclass
class AdminBulkUpdateAppConfigPoliciesAction(BaseBulkAction[AppConfigPolicyBulkUpdateItem]):
    """`items` carries `(id, scope_sources)` pairs targeting existing
    policy rows. `config_name` is immutable and therefore not on the
    update payload."""

    items: list[AppConfigPolicyBulkUpdateItem] = field(default_factory=list)

    @override
    def typed_entity_ids(self) -> list[AppConfigPolicyBulkUpdateItem]:
        return list(self.items)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_POLICY

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

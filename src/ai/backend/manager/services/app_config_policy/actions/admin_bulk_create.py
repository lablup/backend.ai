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
class AdminBulkCreateAppConfigPoliciesAction(BaseBulkAction[AppConfigPolicyBulkItem]):
    """`entity_ids` carries the per-item `config_name`s; `items` carries
    the matching payloads. Construct with both: the framework's
    `BulkActionProcessor` only ever rebuilds the action via
    `entity_ids=...`, so we never observe a mismatch in practice (no
    bulk validators are wired for this action).
    """

    items: list[AppConfigPolicyBulkItem] = field(default_factory=list)

    @override
    def typed_entity_ids(self) -> list[AppConfigPolicyBulkItem]:
        return list(self.items)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_POLICY

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class AdminBulkCreateAppConfigPoliciesActionResult(BaseBulkActionResult):
    created: list[AppConfigPolicyData]
    failed: list[AppConfigPolicyBulkItemError]

    @override
    def entity_ids(self) -> list[str]:
        return [str(policy.id) for policy in self.created]

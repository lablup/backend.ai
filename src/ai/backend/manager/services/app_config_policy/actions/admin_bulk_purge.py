from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_policy.bulk_types import (
    AppConfigPolicyBulkItemError,
)


@dataclass
class AdminBulkPurgeAppConfigPoliciesAction(BaseBulkAction[str]):
    """`entity_ids` carries the `config_name`s to purge — the natural
    Policy identifier."""

    @override
    def typed_entity_ids(self) -> list[str]:
        return list(self.entity_ids)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


@dataclass
class AdminBulkPurgeAppConfigPoliciesActionResult(BaseBulkActionResult):
    purged_config_names: list[str]
    failed: list[AppConfigPolicyBulkItemError]

    @override
    def entity_ids(self) -> list[str]:
        return list(self.purged_config_names)

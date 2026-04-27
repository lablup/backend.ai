from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyBulkItemError


@dataclass
class AdminBulkPurgeAppConfigPoliciesAction(BaseBulkAction[uuid.UUID]):
    """`entity_ids` carries the row ids to purge."""

    @override
    def typed_entity_ids(self) -> list[uuid.UUID]:
        return [uuid.UUID(eid) for eid in self.entity_ids]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_POLICY

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


@dataclass
class AdminBulkPurgeAppConfigPoliciesActionResult(BaseBulkActionResult):
    purged_ids: list[uuid.UUID]
    failed: list[AppConfigPolicyBulkItemError]

    @override
    def entity_ids(self) -> list[str]:
        return [str(i) for i in self.purged_ids]

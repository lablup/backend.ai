from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_policy.bulk_types import (
    AppConfigPolicyBulkItemError,
)
from ai.backend.manager.services.app_config_policy.actions.base import AppConfigPolicyAction


@dataclass
class AdminBulkPurgeAppConfigPoliciesAction(AppConfigPolicyAction):
    config_names: list[str]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


@dataclass
class AdminBulkPurgeAppConfigPoliciesActionResult(BaseActionResult):
    purged_config_names: list[str]
    failed: list[AppConfigPolicyBulkItemError]

    @override
    def entity_id(self) -> str | None:
        return None

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_policy.bulk_types import (
    AppConfigPolicyBulkItem,
    AppConfigPolicyBulkItemError,
)
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.services.app_config_policy.actions.base import AppConfigPolicyAction


@dataclass
class AdminBulkCreateAppConfigPoliciesAction(AppConfigPolicyAction):
    items: list[AppConfigPolicyBulkItem]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class AdminBulkCreateAppConfigPoliciesActionResult(BaseActionResult):
    created: list[AppConfigPolicyData]
    failed: list[AppConfigPolicyBulkItemError]

    @override
    def entity_id(self) -> str | None:
        return None

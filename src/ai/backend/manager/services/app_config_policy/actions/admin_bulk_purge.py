from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.common.identifier.app_config_policy import AppConfigPolicyID
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyBulkItemError
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.app_config_policy.actions.base import AppConfigPolicyTarget


@dataclass
class AdminBulkPurgeAppConfigPoliciesAction(BaseBulkAction[AppConfigPolicyTarget]):
    """`ids` carries the policy row ids to purge."""

    ids: list[AppConfigPolicyID] = field(default_factory=list)

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
        return ActionOperationType.PURGE

    @override
    def targets(self) -> Sequence[AppConfigPolicyTarget]:
        return [AppConfigPolicyTarget(id=policy_id) for policy_id in self.ids]


@dataclass
class AdminBulkPurgeAppConfigPoliciesActionResult(BaseBulkActionResult):
    purged_ids: list[AppConfigPolicyID]
    failed: list[AppConfigPolicyBulkItemError]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return [
            RBACElementRef(
                element_type=RBACElementType.APP_CONFIG_POLICY,
                element_id=str(policy_id),
            )
            for policy_id in self.purged_ids
        ]

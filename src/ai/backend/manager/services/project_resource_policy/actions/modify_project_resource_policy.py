from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    PROJECT_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import UpdateGlobalOpsAction
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow
from ai.backend.manager.repositories.project_resource_policy.updaters import (
    ProjectResourcePolicyUpdater,
)


@dataclass
class ModifyProjectResourcePolicyAction(
    UpdateGlobalOpsAction[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    """Retune one project resource policy; the name stays the key."""

    updater: ProjectResourcePolicyUpdater

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_update_project_resource_policy"

    @override
    def to_updater(self) -> ProjectResourcePolicyUpdater:
        return self.updater

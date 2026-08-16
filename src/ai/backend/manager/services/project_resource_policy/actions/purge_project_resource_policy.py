from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    PROJECT_RESOURCE_POLICY_ENTITY_TYPE,
    ProjectResourcePolicyUUID,
)
from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.resource_policy.purgers import (
    ProjectResourcePolicyPurger,
)
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow


@dataclass
class PurgeProjectResourcePolicyAction(
    PurgeEntityOpsAction[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    """Remove a project resource policy.

    Purge-shaped: the table carries no lifecycle column, so deleting one has
    always been the row leaving the table."""

    name: str
    policy_id: ProjectResourcePolicyUUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_purge_project_resource_policy"

    @override
    def entity_id(self) -> EntityID:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> ProjectResourcePolicyPurger:
        return ProjectResourcePolicyPurger(name=self.name, policy_id=self.policy_id)

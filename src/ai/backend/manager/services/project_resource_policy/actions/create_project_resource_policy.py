from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    PROJECT_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.resource_policy.creators import (
    ProjectResourcePolicyCreator,
)
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow


@dataclass
class CreateProjectResourcePolicyAction(
    CreateGlobalOpsAction[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    """Register a project resource policy."""

    creator: ProjectResourcePolicyCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_create_project_resource_policy"

    @override
    def to_creator(self) -> ProjectResourcePolicyCreator:
        return self.creator

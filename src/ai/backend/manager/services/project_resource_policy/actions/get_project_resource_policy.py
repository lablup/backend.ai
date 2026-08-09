from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    PROJECT_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GetGlobalOpsAction
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow
from ai.backend.manager.repositories.project_resource_policy.queriers import (
    ProjectResourcePolicyQuerier,
)


@dataclass
class GetProjectResourcePolicyAction(
    GetGlobalOpsAction[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    """Read one project resource policy by name."""

    name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_get_project_resource_policy"

    @override
    def to_querier(self) -> ProjectResourcePolicyQuerier:
        return ProjectResourcePolicyQuerier(name=self.name)

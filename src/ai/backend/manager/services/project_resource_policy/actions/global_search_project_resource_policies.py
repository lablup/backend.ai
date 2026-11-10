from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    ProjectResourcePolicyEntityType,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow


@dataclass(frozen=True)
class GlobalSearchProjectResourcePoliciesAction(
    GlobalSearcherOpsAction[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    """Page through the project resource policy catalog."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ProjectResourcePolicyEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_project_resource_policies"

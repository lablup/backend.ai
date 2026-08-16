from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    PROJECT_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow
from ai.backend.manager.repositories.project_resource_policy.searchers import (
    ProjectResourcePolicySearcher,
)


@dataclass
class SearchProjectResourcePoliciesAction(
    SearchGlobalOpsAction[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    """Page through the project resource policy catalog."""

    searcher: ProjectResourcePolicySearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_project_resource_policies"

    @override
    def to_searcher(self) -> ProjectResourcePolicySearcher:
        return self.searcher

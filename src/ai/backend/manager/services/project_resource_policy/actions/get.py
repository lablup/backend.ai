from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import ProjectResourcePolicyUUID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.resource_policy.queriers import ProjectResourcePolicyQuerier
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow


@dataclass(frozen=True)
class GetProjectResourcePolicyAction(
    GetSingleEntityOpsAction[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    """Read one project resource policy by its id."""

    policy_id: ProjectResourcePolicyUUID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.policy_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_project_resource_policy"

    @override
    def to_querier(self) -> ProjectResourcePolicyQuerier:
        return ProjectResourcePolicyQuerier(uuid=self.policy_id)

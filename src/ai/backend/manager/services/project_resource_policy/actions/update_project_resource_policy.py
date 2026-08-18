from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    ProjectResourcePolicyUUID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow
from ai.backend.manager.models.resource_policy.updaters import (
    ProjectResourcePolicyUpdater,
)


@dataclass
class UpdateProjectResourcePolicyAction(
    UpdateSingleEntityOpsAction[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    """Retune one project resource policy.

    Takes both axes: ``policy_id`` is what the operation is answered for, while the
    updater still keys on ``name``, which is the table's primary key until the id
    replaces it.
    """

    policy_id: ProjectResourcePolicyUUID
    updater: ProjectResourcePolicyUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_project_resource_policy"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.policy_id

    @override
    def to_updater(self) -> ProjectResourcePolicyUpdater:
        return self.updater

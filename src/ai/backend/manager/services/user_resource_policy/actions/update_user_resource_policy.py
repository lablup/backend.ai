from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.resource_policy.updaters import (
    UserResourcePolicyUpdater,
)


@dataclass
class UpdateUserResourcePolicyAction(
    UpdateSingleEntityOpsAction[UserResourcePolicyRow, UserResourcePolicyData]
):
    """Retune one user resource policy.

    Takes both axes: ``policy_id`` is what the operation is answered for, while the
    updater still keys on ``name``, which is the table's primary key until the id
    replaces it.
    """

    updater: UserResourcePolicyUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_user_resource_policy"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.policy_id

    @override
    def to_updater(self) -> UserResourcePolicyUpdater:
        return self.updater

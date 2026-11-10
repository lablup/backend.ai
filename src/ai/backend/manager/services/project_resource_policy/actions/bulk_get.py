from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.resource_policy import ProjectResourcePolicyUUID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.resource_policy.queriers import BulkProjectResourcePolicyQuerier
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow


@dataclass
class BulkGetProjectResourcePoliciesAction(
    PartialBulkGetEntityOpsAction[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    """Read the project resource policies the caller named, one permission check per policy."""

    ids: Sequence[ProjectResourcePolicyUUID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_project_resource_policies"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkProjectResourcePolicyQuerier:
        return BulkProjectResourcePolicyQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])

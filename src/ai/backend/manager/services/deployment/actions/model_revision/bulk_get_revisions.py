from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.deployment.types import ModelRevisionData
from ai.backend.manager.models.deployment_revision.queriers import BulkModelRevisionQuerier
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupBulkDeploymentRevisionOwnerAction,
)


@dataclass
class BulkGetRevisionsAction(
    PartialBulkGetFieldOpsAction[
        DeploymentRevisionID, DeploymentID, DeploymentRevisionRow, ModelRevisionData
    ]
):
    """Read the revisions the caller named, answering for each one."""

    ids: Sequence[DeploymentRevisionID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_revisions"

    @override
    def field_ids(self) -> Sequence[DeploymentRevisionID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkDeploymentRevisionOwnerAction:
        return LookupBulkDeploymentRevisionOwnerAction(revision_ids=self.ids)

    @override
    def to_querier(self) -> BulkModelRevisionQuerier:
        return BulkModelRevisionQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[DeploymentRevisionID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])

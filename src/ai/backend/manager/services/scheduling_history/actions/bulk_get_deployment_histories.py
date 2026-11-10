from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_history import DeploymentHistoryID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.deployment.types import DeploymentHistoryData
from ai.backend.manager.models.scheduling_history.queriers import BulkDeploymentHistoryQuerier
from ai.backend.manager.models.scheduling_history.row import DeploymentHistoryRow
from ai.backend.manager.services.scheduling_history.actions.lookup_owner import (
    LookupBulkDeploymentHistoryOwnerAction,
)


@dataclass
class BulkGetDeploymentHistoriesAction(
    PartialBulkGetFieldOpsAction[
        DeploymentHistoryID, DeploymentID, DeploymentHistoryRow, DeploymentHistoryData
    ]
):
    """Read the deployment history rows the caller named."""

    ids: Sequence[DeploymentHistoryID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_deployment_histories"

    @override
    def field_ids(self) -> Sequence[DeploymentHistoryID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkDeploymentHistoryOwnerAction:
        return LookupBulkDeploymentHistoryOwnerAction(history_ids=self.ids)

    @override
    def to_querier(self) -> BulkDeploymentHistoryQuerier:
        return BulkDeploymentHistoryQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[DeploymentHistoryID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.models.endpoint.queriers import BulkDeploymentQuerier
from ai.backend.manager.models.endpoint.row import EndpointRow


@dataclass
class BulkGetDeploymentsAction(PartialBulkGetEntityOpsAction[EndpointRow, ModelDeploymentData]):
    """Read the deployments the caller named, answering for each id."""

    ids: Sequence[DeploymentID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_deployments"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkDeploymentQuerier:
        return BulkDeploymentQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])

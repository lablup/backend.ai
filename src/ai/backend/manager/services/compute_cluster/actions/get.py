from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.compute_cluster import ComputeClusterID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.compute_cluster.types import ComputeClusterData
from ai.backend.manager.models.compute_cluster.queriers import ComputeClusterQuerier
from ai.backend.manager.models.compute_cluster.row import ComputeClusterRow


@dataclass(frozen=True)
class GetComputeClusterAction(GetSingleEntityOpsAction[ComputeClusterRow, ComputeClusterData]):
    """Read one compute cluster."""

    id: ComputeClusterID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_compute_cluster"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id

    @override
    def to_querier(self) -> ComputeClusterQuerier:
        return ComputeClusterQuerier(compute_cluster_id=self.id)

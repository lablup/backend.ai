from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.compute_cluster import ComputeClusterID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.compute_cluster.types import ComputeClusterData
from ai.backend.manager.models.compute_cluster.queriers import BulkComputeClusterQuerier
from ai.backend.manager.models.compute_cluster.row import ComputeClusterRow


@dataclass(frozen=True)
class BulkGetComputeClustersAction(
    PartialBulkGetEntityOpsAction[ComputeClusterRow, ComputeClusterData]
):
    """Read the compute clusters the caller named, one permission check per cluster."""

    ids: Sequence[ComputeClusterID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_compute_clusters"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkComputeClusterQuerier:
        return BulkComputeClusterQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])

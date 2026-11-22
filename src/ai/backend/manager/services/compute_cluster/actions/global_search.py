from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.compute_cluster import ComputeClusterEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.compute_cluster.types import ComputeClusterData
from ai.backend.manager.models.compute_cluster.row import ComputeClusterRow

__all__ = ("GlobalSearchComputeClustersAction",)


@dataclass(frozen=True)
class GlobalSearchComputeClustersAction(
    GlobalSearcherOpsAction[ComputeClusterRow, ComputeClusterData]
):
    """Page through every registered compute cluster."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ComputeClusterEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_compute_clusters"

from __future__ import annotations

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.compute_cluster.types import ComputeClusterData
from ai.backend.manager.services.compute_cluster.actions.bulk_get import (
    BulkGetComputeClustersAction,
)
from ai.backend.manager.services.compute_cluster.actions.create import (
    CreateComputeClusterAction,
)
from ai.backend.manager.services.compute_cluster.actions.get import GetComputeClusterAction
from ai.backend.manager.services.compute_cluster.actions.global_search import (
    GlobalSearchComputeClustersAction,
)
from ai.backend.manager.services.compute_cluster.actions.purge import (
    PurgeComputeClusterAction,
)
from ai.backend.manager.services.compute_cluster.actions.update import (
    UpdateComputeClusterAction,
)
from ai.backend.manager.services.compute_cluster.service import ComputeClusterService

__all__ = ("ComputeClusterProcessors",)


class ComputeClusterProcessors:
    """Every operation is superadmin-only: a cluster is created in global alone, and no
    role preset grants anything on it."""

    get: SingleEntityActionProcessor[GetComputeClusterAction, EntityOpsResult[ComputeClusterData]]
    bulk_get_ids: PartialBulkActionProcessor[BulkGetComputeClustersAction, ComputeClusterData]
    global_search: GlobalActionProcessor[
        GlobalSearchComputeClustersAction, BatchOpsResult[ComputeClusterData]
    ]
    create: GlobalActionProcessor[
        CreateComputeClusterAction, CreatedEntityOpsResult[ComputeClusterData]
    ]
    update: SingleEntityActionProcessor[
        UpdateComputeClusterAction, EntityOpsResult[ComputeClusterData]
    ]
    purge: SingleEntityActionProcessor[
        PurgeComputeClusterAction, EntityOpsResult[ComputeClusterData]
    ]

    def __init__(
        self, group: ProcessorGroup[ComputeClusterData], service: ComputeClusterService
    ) -> None:
        self.get = group.single_get_ops(GetComputeClusterAction)
        self.bulk_get_ids = group.partial_bulk_get_ops(BulkGetComputeClustersAction)
        self.global_search = group.global_searcher_ops(GlobalSearchComputeClustersAction)
        self.create = group.global_scope(CreateComputeClusterAction, service.create)
        self.update = group.single_entity(UpdateComputeClusterAction, service.update)
        self.purge = group.entity_purge_ops(PurgeComputeClusterAction)

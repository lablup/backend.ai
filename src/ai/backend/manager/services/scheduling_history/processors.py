from __future__ import annotations

from ai.backend.common.data.entity.deployment_history import DeploymentHistoryFieldType
from ai.backend.common.data.entity.kernel_scheduling_history import (
    KernelSchedulingHistoryFieldType,
)
from ai.backend.common.data.entity.replica_group_history import ReplicaGroupHistoryFieldType
from ai.backend.common.data.entity.route_history import RouteHistoryFieldType
from ai.backend.common.data.entity.session_scheduling_history import (
    SessionSchedulingHistoryFieldType,
)
from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.v2.field.bulk_processor import PartialBulkFieldActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.data.deployment.types import (
    DeploymentHistoryData,
    ModelDeploymentData,
    ReplicaGroupHistoryData,
    RouteHistoryData,
)
from ai.backend.manager.data.kernel.types import KernelSchedulingHistoryData
from ai.backend.manager.data.session.types import SessionData, SessionSchedulingHistoryData
from ai.backend.manager.services.scheduling_history.actions.bulk_get_deployment_histories import (
    BulkGetDeploymentHistoriesAction,
)
from ai.backend.manager.services.scheduling_history.actions.bulk_get_kernel_histories import (
    BulkGetKernelHistoriesAction,
)
from ai.backend.manager.services.scheduling_history.actions.bulk_get_route_histories import (
    BulkGetRouteHistoriesAction,
)
from ai.backend.manager.services.scheduling_history.actions.bulk_get_session_histories import (
    BulkGetSessionHistoriesAction,
)
from ai.backend.manager.services.scheduling_history.actions.lookup_owner import (
    LookupBulkDeploymentHistoryOwnerAction,
    LookupBulkKernelSchedulingHistoryOwnerAction,
    LookupBulkReplicaGroupHistoryOwnerAction,
    LookupBulkRouteHistoryOwnerAction,
    LookupBulkSessionSchedulingHistoryOwnerAction,
    LookupDeploymentHistoryOwnerAction,
    LookupKernelSchedulingHistoryOwnerAction,
    LookupReplicaGroupHistoryOwnerAction,
    LookupRouteHistoryOwnerAction,
    LookupSessionSchedulingHistoryOwnerAction,
)

from .actions import (
    GlobalSearchReplicaGroupHistoryAction,
    ScopedSearchReplicaGroupHistoryAction,
    ScopedSearchReplicaGroupHistoryActionResult,
    SearchDeploymentHistoryAction,
    SearchDeploymentScopedHistoryAction,
    SearchDeploymentScopedHistoryActionResult,
    SearchKernelHistoryAction,
    SearchKernelScopedHistoryAction,
    SearchKernelScopedHistoryActionResult,
    SearchRouteHistoryAction,
    SearchRouteScopedHistoryAction,
    SearchRouteScopedHistoryActionResult,
    SearchSessionHistoryAction,
    SearchSessionScopedHistoryAction,
    SearchSessionScopedHistoryActionResult,
)
from .service import SchedulingHistoryService


class SchedulingHistoryProcessors:
    """Processor package for scheduling history operations."""

    # What the DataLoaders read: checked per session or deployment the row belongs to.
    bulk_get_session_histories: PartialBulkFieldActionProcessor[
        BulkGetSessionHistoriesAction, SessionSchedulingHistoryData
    ]
    bulk_get_kernel_histories: PartialBulkFieldActionProcessor[
        BulkGetKernelHistoriesAction, KernelSchedulingHistoryData
    ]
    bulk_get_deployment_histories: PartialBulkFieldActionProcessor[
        BulkGetDeploymentHistoriesAction, DeploymentHistoryData
    ]
    bulk_get_route_histories: PartialBulkFieldActionProcessor[
        BulkGetRouteHistoriesAction, RouteHistoryData
    ]

    # Admin processors
    search_session_history: GlobalActionProcessor[
        SearchSessionHistoryAction, BatchOpsResult[SessionSchedulingHistoryData]
    ]
    search_kernel_history: GlobalActionProcessor[
        SearchKernelHistoryAction, BatchOpsResult[KernelSchedulingHistoryData]
    ]
    search_deployment_history: GlobalActionProcessor[
        SearchDeploymentHistoryAction, BatchOpsResult[DeploymentHistoryData]
    ]
    global_search_replica_group_history: GlobalActionProcessor[
        GlobalSearchReplicaGroupHistoryAction, BatchOpsResult[ReplicaGroupHistoryData]
    ]
    search_route_history: GlobalActionProcessor[
        SearchRouteHistoryAction, BatchOpsResult[RouteHistoryData]
    ]

    # Scoped processors (added in 26.2.0)
    search_session_scoped_history: ScopeActionProcessor[
        SearchSessionScopedHistoryAction, SearchSessionScopedHistoryActionResult
    ]
    search_kernel_scoped_history: ScopeActionProcessor[
        SearchKernelScopedHistoryAction, SearchKernelScopedHistoryActionResult
    ]
    search_deployment_scoped_history: ScopeActionProcessor[
        SearchDeploymentScopedHistoryAction, SearchDeploymentScopedHistoryActionResult
    ]
    scoped_search_replica_group_history: ScopeActionProcessor[
        ScopedSearchReplicaGroupHistoryAction, ScopedSearchReplicaGroupHistoryActionResult
    ]
    search_route_scoped_history: GlobalActionProcessor[
        SearchRouteScopedHistoryAction, SearchRouteScopedHistoryActionResult
    ]

    def __init__(
        self,
        session: ProcessorGroup[SessionData],
        deployment: ProcessorGroup[ModelDeploymentData],
        replica_group: ProcessorGroup[ModelDeploymentData],
        service: SchedulingHistoryService,
    ) -> None:
        session_histories: LookupFieldGroup[SessionSchedulingHistoryData] = session.field_group(
            FieldGroupMeta(SessionSchedulingHistoryFieldType()),
            SessionSchedulingHistoryData,
            LookupSessionSchedulingHistoryOwnerAction,
            LookupBulkSessionSchedulingHistoryOwnerAction,
        )
        kernel_histories: LookupFieldGroup[KernelSchedulingHistoryData] = session.field_group(
            FieldGroupMeta(KernelSchedulingHistoryFieldType()),
            KernelSchedulingHistoryData,
            LookupKernelSchedulingHistoryOwnerAction,
            LookupBulkKernelSchedulingHistoryOwnerAction,
        )
        deployment_histories: LookupFieldGroup[DeploymentHistoryData] = deployment.field_group(
            FieldGroupMeta(DeploymentHistoryFieldType()),
            DeploymentHistoryData,
            LookupDeploymentHistoryOwnerAction,
            LookupBulkDeploymentHistoryOwnerAction,
        )
        route_histories: LookupFieldGroup[RouteHistoryData] = deployment.field_group(
            FieldGroupMeta(RouteHistoryFieldType()),
            RouteHistoryData,
            LookupRouteHistoryOwnerAction,
            LookupBulkRouteHistoryOwnerAction,
        )
        replica_group_histories: LookupFieldGroup[ReplicaGroupHistoryData] = (
            replica_group.field_group(
                FieldGroupMeta(ReplicaGroupHistoryFieldType()),
                ReplicaGroupHistoryData,
                LookupReplicaGroupHistoryOwnerAction,
                LookupBulkReplicaGroupHistoryOwnerAction,
            )
        )
        self.bulk_get_session_histories = session_histories.partial_bulk_get_ops(
            BulkGetSessionHistoriesAction
        )
        self.bulk_get_kernel_histories = kernel_histories.partial_bulk_get_ops(
            BulkGetKernelHistoriesAction
        )
        self.bulk_get_deployment_histories = deployment_histories.partial_bulk_get_ops(
            BulkGetDeploymentHistoriesAction
        )
        self.bulk_get_route_histories = route_histories.partial_bulk_get_ops(
            BulkGetRouteHistoriesAction
        )

        # Admin processors
        self.search_session_history = session_histories.global_searcher_ops(
            SearchSessionHistoryAction
        )
        self.search_kernel_history = kernel_histories.global_searcher_ops(SearchKernelHistoryAction)
        self.search_deployment_history = deployment_histories.global_searcher_ops(
            SearchDeploymentHistoryAction
        )
        self.global_search_replica_group_history = replica_group_histories.global_searcher_ops(
            GlobalSearchReplicaGroupHistoryAction
        )
        self.search_route_history = route_histories.global_searcher_ops(SearchRouteHistoryAction)

        # Scoped processors (added in 26.2.0)
        self.search_session_scoped_history = session.scope(
            SearchSessionScopedHistoryAction, service.search_session_scoped_history
        )
        self.search_kernel_scoped_history = session.scope(
            SearchKernelScopedHistoryAction, service.search_kernel_scoped_history
        )
        self.search_deployment_scoped_history = deployment.scope(
            SearchDeploymentScopedHistoryAction, service.search_deployment_scoped_history
        )
        self.scoped_search_replica_group_history = replica_group.scope(
            ScopedSearchReplicaGroupHistoryAction, service.scoped_search_replica_group_history
        )
        self.search_route_scoped_history = deployment.global_scope(
            SearchRouteScopedHistoryAction, service.search_route_scoped_history
        )

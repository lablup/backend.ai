from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor

from .actions import (
    GlobalSearchReplicaGroupHistoryAction,
    GlobalSearchReplicaGroupHistoryActionResult,
    ScopedSearchReplicaGroupHistoryAction,
    ScopedSearchReplicaGroupHistoryActionResult,
    SearchDeploymentHistoryAction,
    SearchDeploymentHistoryActionResult,
    SearchDeploymentScopedHistoryAction,
    SearchDeploymentScopedHistoryActionResult,
    SearchKernelHistoryAction,
    SearchKernelHistoryActionResult,
    SearchKernelScopedHistoryAction,
    SearchKernelScopedHistoryActionResult,
    SearchRouteHistoryAction,
    SearchRouteHistoryActionResult,
    SearchRouteScopedHistoryAction,
    SearchRouteScopedHistoryActionResult,
    SearchSessionHistoryAction,
    SearchSessionHistoryActionResult,
    SearchSessionScopedHistoryAction,
    SearchSessionScopedHistoryActionResult,
)
from .service import SchedulingHistoryService


class SchedulingHistoryProcessors:
    """Processor package for scheduling history operations."""

    # Admin processors
    search_session_history: GlobalActionProcessor[
        SearchSessionHistoryAction, SearchSessionHistoryActionResult
    ]
    search_kernel_history: GlobalActionProcessor[
        SearchKernelHistoryAction, SearchKernelHistoryActionResult
    ]
    search_deployment_history: GlobalActionProcessor[
        SearchDeploymentHistoryAction, SearchDeploymentHistoryActionResult
    ]
    global_search_replica_group_history: GlobalActionProcessor[
        GlobalSearchReplicaGroupHistoryAction, GlobalSearchReplicaGroupHistoryActionResult
    ]
    search_route_history: GlobalActionProcessor[
        SearchRouteHistoryAction, SearchRouteHistoryActionResult
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
        session: ProcessorGroup[Any],
        deployment: ProcessorGroup[Any],
        replica_group: ProcessorGroup[Any],
        service: SchedulingHistoryService,
    ) -> None:
        # Admin processors
        self.search_session_history = session.global_scope(
            SearchSessionHistoryAction, service.search_session_history
        )
        self.search_kernel_history = session.global_scope(
            SearchKernelHistoryAction, service.search_kernel_history
        )
        self.search_deployment_history = deployment.global_scope(
            SearchDeploymentHistoryAction, service.search_deployment_history
        )
        self.global_search_replica_group_history = replica_group.global_scope(
            GlobalSearchReplicaGroupHistoryAction, service.global_search_replica_group_history
        )
        self.search_route_history = deployment.global_scope(
            SearchRouteHistoryAction, service.search_route_history
        )

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

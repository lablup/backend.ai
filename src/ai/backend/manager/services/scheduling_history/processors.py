from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

from .actions import (
    SearchDeploymentHistoryAction,
    SearchDeploymentHistoryActionResult,
    SearchDeploymentScopedHistoryAction,
    SearchDeploymentScopedHistoryActionResult,
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


class SchedulingHistoryProcessors(AbstractProcessorPackage):
    """Processor package for scheduling history operations."""

    # Admin processors
    search_session_history: ActionProcessor[
        SearchSessionHistoryAction, SearchSessionHistoryActionResult
    ]
    search_deployment_history: ActionProcessor[
        SearchDeploymentHistoryAction, SearchDeploymentHistoryActionResult
    ]
    search_route_history: ActionProcessor[SearchRouteHistoryAction, SearchRouteHistoryActionResult]

    # Scoped processors (added in 26.2.0)
    search_session_scoped_history: ActionProcessor[
        SearchSessionScopedHistoryAction, SearchSessionScopedHistoryActionResult
    ]
    search_deployment_scoped_history: ActionProcessor[
        SearchDeploymentScopedHistoryAction, SearchDeploymentScopedHistoryActionResult
    ]
    search_route_scoped_history: ActionProcessor[
        SearchRouteScopedHistoryAction, SearchRouteScopedHistoryActionResult
    ]

    def __init__(
        self, service: SchedulingHistoryService, action_monitors: list[ActionMonitor]
    ) -> None:
        # Admin processors
        self.search_session_history = ActionProcessor(
            service.search_session_history, action_monitors
        )
        self.search_deployment_history = ActionProcessor(
            service.search_deployment_history, action_monitors
        )
        self.search_route_history = ActionProcessor(service.search_route_history, action_monitors)

        # Scoped processors (added in 26.2.0)
        self.search_session_scoped_history = ActionProcessor(
            service.search_session_scoped_history, action_monitors
        )
        self.search_deployment_scoped_history = ActionProcessor(
            service.search_deployment_scoped_history, action_monitors
        )
        self.search_route_scoped_history = ActionProcessor(
            service.search_route_scoped_history, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            # Admin actions
            SearchSessionHistoryAction.spec(),
            SearchDeploymentHistoryAction.spec(),
            SearchRouteHistoryAction.spec(),
            # Scoped actions (added in 26.2.0)
            SearchSessionScopedHistoryAction.spec(),
            SearchDeploymentScopedHistoryAction.spec(),
            SearchRouteScopedHistoryAction.spec(),
        ]

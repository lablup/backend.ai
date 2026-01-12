from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

from .actions import (
    SearchDeploymentHistoryAction,
    SearchDeploymentHistoryActionResult,
    SearchRouteHistoryAction,
    SearchRouteHistoryActionResult,
    SearchSessionHistoryAction,
    SearchSessionHistoryActionResult,
)
from .service import SchedulingHistoryService


class SchedulingHistoryProcessors(AbstractProcessorPackage):
    """Processor package for scheduling history operations."""

    search_session_history: ActionProcessor[
        SearchSessionHistoryAction, SearchSessionHistoryActionResult
    ]
    search_deployment_history: ActionProcessor[
        SearchDeploymentHistoryAction, SearchDeploymentHistoryActionResult
    ]
    search_route_history: ActionProcessor[SearchRouteHistoryAction, SearchRouteHistoryActionResult]

    def __init__(
        self, service: SchedulingHistoryService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.search_session_history = ActionProcessor(
            service.search_session_history, action_monitors
        )
        self.search_deployment_history = ActionProcessor(
            service.search_deployment_history, action_monitors
        )
        self.search_route_history = ActionProcessor(service.search_route_history, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            SearchSessionHistoryAction.spec(),
            SearchDeploymentHistoryAction.spec(),
            SearchRouteHistoryAction.spec(),
        ]

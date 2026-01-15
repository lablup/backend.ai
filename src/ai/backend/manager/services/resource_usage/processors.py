"""Resource Usage Processors."""

from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

from .actions import (
    SearchDomainUsageBucketsAction,
    SearchDomainUsageBucketsActionResult,
    SearchProjectUsageBucketsAction,
    SearchProjectUsageBucketsActionResult,
    SearchUserUsageBucketsAction,
    SearchUserUsageBucketsActionResult,
)
from .service import ResourceUsageService

__all__ = ("ResourceUsageProcessors",)


class ResourceUsageProcessors(AbstractProcessorPackage):
    """Processor package for resource usage operations."""

    # Domain Usage Buckets
    search_domain_usage_buckets: ActionProcessor[
        SearchDomainUsageBucketsAction, SearchDomainUsageBucketsActionResult
    ]

    # Project Usage Buckets
    search_project_usage_buckets: ActionProcessor[
        SearchProjectUsageBucketsAction, SearchProjectUsageBucketsActionResult
    ]

    # User Usage Buckets
    search_user_usage_buckets: ActionProcessor[
        SearchUserUsageBucketsAction, SearchUserUsageBucketsActionResult
    ]

    def __init__(self, service: ResourceUsageService, action_monitors: list[ActionMonitor]) -> None:
        # Domain Usage Buckets
        self.search_domain_usage_buckets = ActionProcessor(
            service.search_domain_usage_buckets, action_monitors
        )

        # Project Usage Buckets
        self.search_project_usage_buckets = ActionProcessor(
            service.search_project_usage_buckets, action_monitors
        )

        # User Usage Buckets
        self.search_user_usage_buckets = ActionProcessor(
            service.search_user_usage_buckets, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            # Domain
            SearchDomainUsageBucketsAction.spec(),
            # Project
            SearchProjectUsageBucketsAction.spec(),
            # User
            SearchUserUsageBucketsAction.spec(),
        ]

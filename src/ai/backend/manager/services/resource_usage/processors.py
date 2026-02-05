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
    SearchScopedDomainUsageBucketsAction,
    SearchScopedDomainUsageBucketsActionResult,
    SearchScopedProjectUsageBucketsAction,
    SearchScopedProjectUsageBucketsActionResult,
    SearchScopedUserUsageBucketsAction,
    SearchScopedUserUsageBucketsActionResult,
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
    search_scoped_domain_usage_buckets: ActionProcessor[
        SearchScopedDomainUsageBucketsAction, SearchScopedDomainUsageBucketsActionResult
    ]

    # Project Usage Buckets
    search_project_usage_buckets: ActionProcessor[
        SearchProjectUsageBucketsAction, SearchProjectUsageBucketsActionResult
    ]
    search_scoped_project_usage_buckets: ActionProcessor[
        SearchScopedProjectUsageBucketsAction, SearchScopedProjectUsageBucketsActionResult
    ]

    # User Usage Buckets
    search_user_usage_buckets: ActionProcessor[
        SearchUserUsageBucketsAction, SearchUserUsageBucketsActionResult
    ]
    search_scoped_user_usage_buckets: ActionProcessor[
        SearchScopedUserUsageBucketsAction, SearchScopedUserUsageBucketsActionResult
    ]

    def __init__(self, service: ResourceUsageService, action_monitors: list[ActionMonitor]) -> None:
        # Domain Usage Buckets
        self.search_domain_usage_buckets = ActionProcessor(
            service.search_domain_usage_buckets, action_monitors
        )
        self.search_scoped_domain_usage_buckets = ActionProcessor(
            service.search_scoped_domain_usage_buckets, action_monitors
        )

        # Project Usage Buckets
        self.search_project_usage_buckets = ActionProcessor(
            service.search_project_usage_buckets, action_monitors
        )
        self.search_scoped_project_usage_buckets = ActionProcessor(
            service.search_scoped_project_usage_buckets, action_monitors
        )

        # User Usage Buckets
        self.search_user_usage_buckets = ActionProcessor(
            service.search_user_usage_buckets, action_monitors
        )
        self.search_scoped_user_usage_buckets = ActionProcessor(
            service.search_scoped_user_usage_buckets, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            # Domain
            SearchDomainUsageBucketsAction.spec(),
            SearchScopedDomainUsageBucketsAction.spec(),
            # Project
            SearchProjectUsageBucketsAction.spec(),
            SearchScopedProjectUsageBucketsAction.spec(),
            # User
            SearchUserUsageBucketsAction.spec(),
            SearchScopedUserUsageBucketsAction.spec(),
        ]

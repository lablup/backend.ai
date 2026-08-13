"""Resource Usage Processors."""

from __future__ import annotations

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.validators import ActionValidators

from .actions import (
    OperationScopedDomainUsageBucketsAction,
    OperationScopedDomainUsageBucketsActionResult,
    OperationScopedProjectUsageBucketsAction,
    OperationScopedProjectUsageBucketsActionResult,
    OperationScopedUserUsageBucketsAction,
    OperationScopedUserUsageBucketsActionResult,
    SearchDomainUsageBucketsAction,
    SearchDomainUsageBucketsActionResult,
    SearchProjectUsageBucketsAction,
    SearchProjectUsageBucketsActionResult,
    SearchUserUsageBucketsAction,
    SearchUserUsageBucketsActionResult,
)
from .service import ResourceUsageService

__all__ = ("ResourceUsageProcessors",)


class ResourceUsageProcessors:
    """Processor package for resource usage operations."""

    # Domain Usage Buckets
    search_domain_usage_buckets: ActionProcessor[
        SearchDomainUsageBucketsAction, SearchDomainUsageBucketsActionResult
    ]
    search_scoped_domain_usage_buckets: ActionProcessor[
        OperationScopedDomainUsageBucketsAction, OperationScopedDomainUsageBucketsActionResult
    ]

    # Project Usage Buckets
    search_project_usage_buckets: ActionProcessor[
        SearchProjectUsageBucketsAction, SearchProjectUsageBucketsActionResult
    ]
    search_scoped_project_usage_buckets: ActionProcessor[
        OperationScopedProjectUsageBucketsAction, OperationScopedProjectUsageBucketsActionResult
    ]

    # User Usage Buckets
    search_user_usage_buckets: ActionProcessor[
        SearchUserUsageBucketsAction, SearchUserUsageBucketsActionResult
    ]
    search_scoped_user_usage_buckets: ActionProcessor[
        OperationScopedUserUsageBucketsAction, OperationScopedUserUsageBucketsActionResult
    ]

    def __init__(
        self,
        service: ResourceUsageService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
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

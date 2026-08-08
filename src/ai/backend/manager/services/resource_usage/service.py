"""Resource Usage Service."""

from __future__ import annotations

from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.resource_usage_history import ResourceUsageHistoryRepository

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

__all__ = ("ResourceUsageService",)


class ResourceUsageService:
    """Service for resource usage operations.

    Provides read operations wrapping the ResourceUsageHistoryRepository.
    Write operations (create/upsert) are handled directly by sokovan using the repository.
    """

    _repository: ResourceUsageHistoryRepository

    def __init__(self, repository: ResourceUsageHistoryRepository) -> None:
        self._repository = repository

    # Domain Usage Buckets

    async def search_domain_usage_buckets(
        self, action: SearchDomainUsageBucketsAction
    ) -> SearchDomainUsageBucketsActionResult:
        """Search domain usage buckets with pagination."""
        querier = BatchQuerier(
            pagination=action.pagination,
            conditions=action.conditions,
            orders=action.orders,
        )
        result = await self._repository.search_domain_usage_buckets(querier)
        return SearchDomainUsageBucketsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    # Project Usage Buckets

    async def search_project_usage_buckets(
        self, action: SearchProjectUsageBucketsAction
    ) -> SearchProjectUsageBucketsActionResult:
        """Search project usage buckets with pagination."""
        querier = BatchQuerier(
            pagination=action.pagination,
            conditions=action.conditions,
            orders=action.orders,
        )
        result = await self._repository.search_project_usage_buckets(querier)
        return SearchProjectUsageBucketsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    # User Usage Buckets

    async def search_user_usage_buckets(
        self, action: SearchUserUsageBucketsAction
    ) -> SearchUserUsageBucketsActionResult:
        """Search user usage buckets with pagination."""
        querier = BatchQuerier(
            pagination=action.pagination,
            conditions=action.conditions,
            orders=action.orders,
        )
        result = await self._repository.search_user_usage_buckets(querier)
        return SearchUserUsageBucketsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    # Scoped Usage Bucket Searches

    async def search_scoped_domain_usage_buckets(
        self,
        action: OperationScopedDomainUsageBucketsAction,
    ) -> OperationScopedDomainUsageBucketsActionResult:
        """Search domain usage buckets within scope."""
        result = await self._repository.search_domain_usage_buckets(
            action.querier,
            action.scope,
        )
        return OperationScopedDomainUsageBucketsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_scoped_project_usage_buckets(
        self,
        action: OperationScopedProjectUsageBucketsAction,
    ) -> OperationScopedProjectUsageBucketsActionResult:
        """Search project usage buckets within scope."""
        result = await self._repository.search_project_usage_buckets(
            action.querier,
            action.scope,
        )
        return OperationScopedProjectUsageBucketsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_scoped_user_usage_buckets(
        self,
        action: OperationScopedUserUsageBucketsAction,
    ) -> OperationScopedUserUsageBucketsActionResult:
        """Search user usage buckets within scope."""
        result = await self._repository.search_user_usage_buckets(
            action.querier,
            action.scope,
        )
        return OperationScopedUserUsageBucketsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

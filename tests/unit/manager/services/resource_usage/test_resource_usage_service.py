"""Tests for ResourceUsageService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.repositories.base import OffsetPagination
from ai.backend.manager.repositories.resource_usage_history import (
    DomainUsageBucketData,
    DomainUsageBucketSearchResult,
    ProjectUsageBucketData,
    ProjectUsageBucketSearchResult,
    ResourceUsageHistoryRepository,
    UserUsageBucketData,
    UserUsageBucketSearchResult,
)
from ai.backend.manager.services.resource_usage import (
    ResourceUsageService,
    SearchDomainUsageBucketsAction,
    SearchProjectUsageBucketsAction,
    SearchUserUsageBucketsAction,
)


@pytest.fixture
def mock_repository() -> MagicMock:
    return MagicMock(spec=ResourceUsageHistoryRepository)


@pytest.fixture
def service(mock_repository: MagicMock) -> ResourceUsageService:
    return ResourceUsageService(repository=mock_repository)


class TestSearchDomainUsageBuckets:
    @pytest.mark.asyncio
    async def test_search_domain_usage_buckets_returns_result(
        self,
        service: ResourceUsageService,
        mock_repository: MagicMock,
    ) -> None:
        """Should return search results from repository."""
        mock_bucket = MagicMock(spec=DomainUsageBucketData)
        mock_result = DomainUsageBucketSearchResult(
            items=[mock_bucket],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_domain_usage_buckets = AsyncMock(return_value=mock_result)

        action = SearchDomainUsageBucketsAction(
            pagination=OffsetPagination(offset=0, limit=10),
            conditions=[],
            orders=[],
        )

        result = await service.search_domain_usage_buckets(action)

        mock_repository.search_domain_usage_buckets.assert_called_once()
        assert result.items == [mock_bucket]
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_search_domain_usage_buckets_passes_querier(
        self,
        service: ResourceUsageService,
        mock_repository: MagicMock,
    ) -> None:
        """Should create BatchQuerier with correct parameters."""
        mock_result = DomainUsageBucketSearchResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_domain_usage_buckets = AsyncMock(return_value=mock_result)

        pagination = OffsetPagination(offset=0, limit=20)
        action = SearchDomainUsageBucketsAction(
            pagination=pagination,
            conditions=[],
            orders=[],
        )

        await service.search_domain_usage_buckets(action)

        call_args = mock_repository.search_domain_usage_buckets.call_args
        querier = call_args[0][0]

        assert querier.conditions == []
        assert querier.orders == []
        assert querier.pagination == pagination


class TestSearchProjectUsageBuckets:
    @pytest.mark.asyncio
    async def test_search_project_usage_buckets_returns_result(
        self,
        service: ResourceUsageService,
        mock_repository: MagicMock,
    ) -> None:
        """Should return search results from repository."""
        mock_bucket = MagicMock(spec=ProjectUsageBucketData)
        mock_result = ProjectUsageBucketSearchResult(
            items=[mock_bucket],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_project_usage_buckets = AsyncMock(return_value=mock_result)

        action = SearchProjectUsageBucketsAction(
            pagination=OffsetPagination(offset=0, limit=10),
            conditions=[],
            orders=[],
        )

        result = await service.search_project_usage_buckets(action)

        mock_repository.search_project_usage_buckets.assert_called_once()
        assert result.items == [mock_bucket]
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_search_project_usage_buckets_passes_querier(
        self,
        service: ResourceUsageService,
        mock_repository: MagicMock,
    ) -> None:
        """Should create BatchQuerier with correct parameters."""
        mock_result = ProjectUsageBucketSearchResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_project_usage_buckets = AsyncMock(return_value=mock_result)

        pagination = OffsetPagination(offset=0, limit=20)
        action = SearchProjectUsageBucketsAction(
            pagination=pagination,
            conditions=[],
            orders=[],
        )

        await service.search_project_usage_buckets(action)

        call_args = mock_repository.search_project_usage_buckets.call_args
        querier = call_args[0][0]

        assert querier.conditions == []
        assert querier.orders == []
        assert querier.pagination == pagination


class TestSearchUserUsageBuckets:
    @pytest.mark.asyncio
    async def test_search_user_usage_buckets_returns_result(
        self,
        service: ResourceUsageService,
        mock_repository: MagicMock,
    ) -> None:
        """Should return search results from repository."""
        mock_bucket = MagicMock(spec=UserUsageBucketData)
        mock_result = UserUsageBucketSearchResult(
            items=[mock_bucket],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_user_usage_buckets = AsyncMock(return_value=mock_result)

        action = SearchUserUsageBucketsAction(
            pagination=OffsetPagination(offset=0, limit=10),
            conditions=[],
            orders=[],
        )

        result = await service.search_user_usage_buckets(action)

        mock_repository.search_user_usage_buckets.assert_called_once()
        assert result.items == [mock_bucket]
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_search_user_usage_buckets_passes_querier(
        self,
        service: ResourceUsageService,
        mock_repository: MagicMock,
    ) -> None:
        """Should create BatchQuerier with correct parameters."""
        mock_result = UserUsageBucketSearchResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_user_usage_buckets = AsyncMock(return_value=mock_result)

        pagination = OffsetPagination(offset=0, limit=20)
        action = SearchUserUsageBucketsAction(
            pagination=pagination,
            conditions=[],
            orders=[],
        )

        await service.search_user_usage_buckets(action)

        call_args = mock_repository.search_user_usage_buckets.call_args
        querier = call_args[0][0]

        assert querier.conditions == []
        assert querier.orders == []
        assert querier.pagination == pagination

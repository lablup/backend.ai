"""Tests for FairShareService."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    DomainFairShareSearchResult,
    ProjectFairShareData,
    ProjectFairShareSearchResult,
    UserFairShareData,
    UserFairShareSearchResult,
)
from ai.backend.manager.repositories.base import OffsetPagination
from ai.backend.manager.repositories.fair_share import FairShareRepository
from ai.backend.manager.services.fair_share import (
    FairShareService,
    GetDomainFairShareAction,
    GetProjectFairShareAction,
    GetUserFairShareAction,
    SearchDomainFairSharesAction,
    SearchProjectFairSharesAction,
    SearchUserFairSharesAction,
)


@pytest.fixture
def mock_repository() -> MagicMock:
    return MagicMock(spec=FairShareRepository)


@pytest.fixture
def service(mock_repository: MagicMock) -> FairShareService:
    return FairShareService(repository=mock_repository)


# Domain Fair Share Tests


class TestGetDomainFairShare:
    @pytest.mark.asyncio
    async def test_get_domain_fair_share_calls_repository(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should call repository with correct parameters."""
        expected_data = MagicMock(spec=DomainFairShareData)
        expected_data.id = uuid.uuid4()
        mock_repository.get_domain_fair_share = AsyncMock(return_value=expected_data)

        action = GetDomainFairShareAction(
            resource_group="default",
            domain_name="test-domain",
        )

        result = await service.get_domain_fair_share(action)

        mock_repository.get_domain_fair_share.assert_called_once_with(
            resource_group="default",
            domain_name="test-domain",
        )
        assert result.data == expected_data


class TestSearchDomainFairShares:
    @pytest.mark.asyncio
    async def test_search_domain_fair_shares_returns_result(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should return search results from repository."""
        mock_fair_share = MagicMock(spec=DomainFairShareData)
        mock_result = DomainFairShareSearchResult(
            items=[mock_fair_share],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_domain_fair_shares = AsyncMock(return_value=mock_result)

        action = SearchDomainFairSharesAction(
            pagination=OffsetPagination(offset=0, limit=10),
            conditions=[],
            orders=[],
        )

        result = await service.search_domain_fair_shares(action)

        mock_repository.search_domain_fair_shares.assert_called_once()
        assert result.items == [mock_fair_share]
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_search_domain_fair_shares_passes_querier(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should create BatchQuerier with correct parameters."""
        mock_result = DomainFairShareSearchResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_domain_fair_shares = AsyncMock(return_value=mock_result)

        pagination = OffsetPagination(offset=0, limit=20)
        action = SearchDomainFairSharesAction(
            pagination=pagination,
            conditions=[],
            orders=[],
        )

        await service.search_domain_fair_shares(action)

        call_args = mock_repository.search_domain_fair_shares.call_args
        querier = call_args[0][0]

        assert querier.conditions == []
        assert querier.orders == []
        assert querier.pagination == pagination


# Project Fair Share Tests


class TestGetProjectFairShare:
    @pytest.mark.asyncio
    async def test_get_project_fair_share_calls_repository(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should call repository with correct parameters."""
        project_id = uuid.uuid4()
        expected_data = MagicMock(spec=ProjectFairShareData)
        expected_data.id = uuid.uuid4()
        mock_repository.get_project_fair_share = AsyncMock(return_value=expected_data)

        action = GetProjectFairShareAction(
            resource_group="default",
            project_id=project_id,
        )

        result = await service.get_project_fair_share(action)

        mock_repository.get_project_fair_share.assert_called_once_with(
            resource_group="default",
            project_id=project_id,
        )
        assert result.data == expected_data


class TestSearchProjectFairShares:
    @pytest.mark.asyncio
    async def test_search_project_fair_shares_returns_result(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should return search results from repository."""
        mock_fair_share = MagicMock(spec=ProjectFairShareData)
        mock_result = ProjectFairShareSearchResult(
            items=[mock_fair_share],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_project_fair_shares = AsyncMock(return_value=mock_result)

        action = SearchProjectFairSharesAction(
            pagination=OffsetPagination(offset=0, limit=10),
            conditions=[],
            orders=[],
        )

        result = await service.search_project_fair_shares(action)

        mock_repository.search_project_fair_shares.assert_called_once()
        assert result.items == [mock_fair_share]
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_search_project_fair_shares_passes_querier(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should create BatchQuerier with correct parameters."""
        mock_result = ProjectFairShareSearchResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_project_fair_shares = AsyncMock(return_value=mock_result)

        pagination = OffsetPagination(offset=0, limit=20)
        action = SearchProjectFairSharesAction(
            pagination=pagination,
            conditions=[],
            orders=[],
        )

        await service.search_project_fair_shares(action)

        call_args = mock_repository.search_project_fair_shares.call_args
        querier = call_args[0][0]

        assert querier.conditions == []
        assert querier.orders == []
        assert querier.pagination == pagination


# User Fair Share Tests


class TestGetUserFairShare:
    @pytest.mark.asyncio
    async def test_get_user_fair_share_calls_repository(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should call repository with correct parameters."""
        project_id = uuid.uuid4()
        user_uuid = uuid.uuid4()
        expected_data = MagicMock(spec=UserFairShareData)
        expected_data.id = uuid.uuid4()
        mock_repository.get_user_fair_share = AsyncMock(return_value=expected_data)

        action = GetUserFairShareAction(
            resource_group="default",
            project_id=project_id,
            user_uuid=user_uuid,
        )

        result = await service.get_user_fair_share(action)

        mock_repository.get_user_fair_share.assert_called_once_with(
            resource_group="default",
            project_id=project_id,
            user_uuid=user_uuid,
        )
        assert result.data == expected_data


class TestSearchUserFairShares:
    @pytest.mark.asyncio
    async def test_search_user_fair_shares_returns_result(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should return search results from repository."""
        mock_fair_share = MagicMock(spec=UserFairShareData)
        mock_result = UserFairShareSearchResult(
            items=[mock_fair_share],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_user_fair_shares = AsyncMock(return_value=mock_result)

        action = SearchUserFairSharesAction(
            pagination=OffsetPagination(offset=0, limit=10),
            conditions=[],
            orders=[],
        )

        result = await service.search_user_fair_shares(action)

        mock_repository.search_user_fair_shares.assert_called_once()
        assert result.items == [mock_fair_share]
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_search_user_fair_shares_passes_querier(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should create BatchQuerier with correct parameters."""
        mock_result = UserFairShareSearchResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_user_fair_shares = AsyncMock(return_value=mock_result)

        pagination = OffsetPagination(offset=0, limit=20)
        action = SearchUserFairSharesAction(
            pagination=pagination,
            conditions=[],
            orders=[],
        )

        await service.search_user_fair_shares(action)

        call_args = mock_repository.search_user_fair_shares.call_args
        querier = call_args[0][0]

        assert querier.conditions == []
        assert querier.orders == []
        assert querier.pagination == pagination

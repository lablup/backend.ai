"""Tests for resource usage client SDK functions."""

from __future__ import annotations

from http import HTTPStatus
from unittest import mock
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from aioresponses import aioresponses

from ai.backend.client.config import API_VERSION
from ai.backend.client.func.resource_usage import ResourceUsage
from ai.backend.client.session import Session
from ai.backend.common.dto.manager.fair_share import (
    DomainUsageBucketFilter,
    SearchDomainUsageBucketsRequest,
    SearchDomainUsageBucketsResponse,
    SearchProjectUsageBucketsRequest,
    SearchProjectUsageBucketsResponse,
    SearchUserUsageBucketsRequest,
    SearchUserUsageBucketsResponse,
)
from ai.backend.common.dto.manager.query import StringFilter


@pytest.fixture(autouse=True)
def api_version_mock() -> mock.AsyncMock:
    """Mock API version negotiation."""
    mock_nego_func = AsyncMock()
    mock_nego_func.return_value = API_VERSION
    with mock.patch("ai.backend.client.session._negotiate_api_version", mock_nego_func):
        yield mock_nego_func


class TestResourceUsageSearch:
    """Usage bucket search tests."""

    @pytest.mark.asyncio
    async def test_search_domain_usage_buckets_no_filter(self, dummy_endpoint: str) -> None:
        """Should search with default pagination."""
        with aioresponses() as m, Session():
            m.post(
                dummy_endpoint + "fair-share/usage-buckets/domains/search",
                status=HTTPStatus.OK,
                payload={
                    "items": [
                        {
                            "id": "00000000-0000-0000-0000-000000000001",
                            "domain_name": "domain1",
                            "resource_group": "default",
                            "metadata": {
                                "period_start": "2024-01-01",
                                "period_end": "2024-01-02",
                                "decay_unit_days": 1,
                                "created_at": "2024-01-02T00:00:00Z",
                                "updated_at": "2024-01-02T00:00:00Z",
                                "average_daily_usage": {"entries": []},
                                "usage_capacity_ratio": {"entries": []},
                                "average_capacity_per_second": {"entries": []},
                            },
                            "resource_usage": {"entries": []},
                            "capacity_snapshot": {"entries": []},
                        }
                    ],
                    "pagination": {"total": 1, "offset": 0, "limit": 50},
                },
            )

            result = ResourceUsage.search_domain_usage_buckets(
                request=SearchDomainUsageBucketsRequest(
                    filter=None,
                    order=None,
                    limit=50,
                    offset=0,
                )
            )

            assert isinstance(result, SearchDomainUsageBucketsResponse)
            assert len(result.items) == 1
            assert result.pagination.total == 1

    @pytest.mark.asyncio
    async def test_search_project_usage_buckets_no_filter(self, dummy_endpoint: str) -> None:
        """Should search with default pagination."""
        with aioresponses() as m, Session():
            m.post(
                dummy_endpoint + "fair-share/usage-buckets/projects/search",
                status=HTTPStatus.OK,
                payload={
                    "items": [
                        {
                            "id": "00000000-0000-0000-0000-000000000001",
                            "project_id": "00000000-0000-0000-0000-000000000002",
                            "domain_name": "domain1",
                            "resource_group": "default",
                            "metadata": {
                                "period_start": "2024-01-01",
                                "period_end": "2024-01-02",
                                "decay_unit_days": 1,
                                "created_at": "2024-01-02T00:00:00Z",
                                "updated_at": "2024-01-02T00:00:00Z",
                                "average_daily_usage": {"entries": []},
                                "usage_capacity_ratio": {"entries": []},
                                "average_capacity_per_second": {"entries": []},
                            },
                            "resource_usage": {"entries": []},
                            "capacity_snapshot": {"entries": []},
                        }
                    ],
                    "pagination": {"total": 1, "offset": 0, "limit": 50},
                },
            )

            result = ResourceUsage.search_project_usage_buckets(
                request=SearchProjectUsageBucketsRequest(
                    filter=None,
                    order=None,
                    limit=50,
                    offset=0,
                )
            )

            assert isinstance(result, SearchProjectUsageBucketsResponse)
            assert len(result.items) == 1
            assert result.pagination.total == 1

    @pytest.mark.asyncio
    async def test_search_user_usage_buckets_no_filter(self, dummy_endpoint: str) -> None:
        """Should search with default pagination."""
        with aioresponses() as m, Session():
            m.post(
                dummy_endpoint + "fair-share/usage-buckets/users/search",
                status=HTTPStatus.OK,
                payload={
                    "items": [
                        {
                            "id": "00000000-0000-0000-0000-000000000001",
                            "user_uuid": "00000000-0000-0000-0000-000000000002",
                            "project_id": "00000000-0000-0000-0000-000000000003",
                            "domain_name": "domain1",
                            "resource_group": "default",
                            "metadata": {
                                "period_start": "2024-01-01",
                                "period_end": "2024-01-02",
                                "decay_unit_days": 1,
                                "created_at": "2024-01-02T00:00:00Z",
                                "updated_at": "2024-01-02T00:00:00Z",
                                "average_daily_usage": {"entries": []},
                                "usage_capacity_ratio": {"entries": []},
                                "average_capacity_per_second": {"entries": []},
                            },
                            "resource_usage": {"entries": []},
                            "capacity_snapshot": {"entries": []},
                        }
                    ],
                    "pagination": {"total": 1, "offset": 0, "limit": 50},
                },
            )

            result = ResourceUsage.search_user_usage_buckets(
                request=SearchUserUsageBucketsRequest(
                    filter=None,
                    order=None,
                    limit=50,
                    offset=0,
                )
            )

            assert isinstance(result, SearchUserUsageBucketsResponse)
            assert len(result.items) == 1
            assert result.pagination.total == 1


class TestResourceUsageRGScoped:
    """RG-scoped usage bucket search tests."""

    @pytest.mark.asyncio
    async def test_rg_search_domain_usage_buckets_success(self, dummy_endpoint: str) -> None:
        """Should search domain usage buckets within RG scope."""
        with aioresponses() as m, Session():
            m.post(
                dummy_endpoint + "fair-share/rg/default/usage-buckets/domains/search",
                status=HTTPStatus.OK,
                payload={
                    "items": [
                        {
                            "id": "00000000-0000-0000-0000-000000000001",
                            "domain_name": "domain1",
                            "resource_group": "default",
                            "metadata": {
                                "period_start": "2024-01-01",
                                "period_end": "2024-01-02",
                                "decay_unit_days": 1,
                                "created_at": "2024-01-02T00:00:00Z",
                                "updated_at": "2024-01-02T00:00:00Z",
                                "average_daily_usage": {"entries": []},
                                "usage_capacity_ratio": {"entries": []},
                                "average_capacity_per_second": {"entries": []},
                            },
                            "resource_usage": {"entries": []},
                            "capacity_snapshot": {"entries": []},
                        }
                    ],
                    "pagination": {"total": 1, "offset": 0, "limit": 50},
                },
            )

            result = ResourceUsage.rg_search_domain_usage_buckets(
                resource_group="default",
                request=SearchDomainUsageBucketsRequest(
                    filter=None,
                    order=None,
                    limit=50,
                    offset=0,
                ),
            )

            assert isinstance(result, SearchDomainUsageBucketsResponse)
            assert len(result.items) == 1
            assert result.items[0].resource_group == "default"
            assert result.pagination.total == 1

    @pytest.mark.asyncio
    async def test_rg_search_project_usage_buckets_success(self, dummy_endpoint: str) -> None:
        """Should search project usage buckets within RG and domain scope."""
        with aioresponses() as m, Session():
            m.post(
                dummy_endpoint
                + "fair-share/rg/default/domains/domain1/usage-buckets/projects/search",
                status=HTTPStatus.OK,
                payload={
                    "items": [
                        {
                            "id": "00000000-0000-0000-0000-000000000001",
                            "project_id": "00000000-0000-0000-0000-000000000002",
                            "domain_name": "domain1",
                            "resource_group": "default",
                            "metadata": {
                                "period_start": "2024-01-01",
                                "period_end": "2024-01-02",
                                "decay_unit_days": 1,
                                "created_at": "2024-01-02T00:00:00Z",
                                "updated_at": "2024-01-02T00:00:00Z",
                                "average_daily_usage": {"entries": []},
                                "usage_capacity_ratio": {"entries": []},
                                "average_capacity_per_second": {"entries": []},
                            },
                            "resource_usage": {"entries": []},
                            "capacity_snapshot": {"entries": []},
                        }
                    ],
                    "pagination": {"total": 1, "offset": 0, "limit": 50},
                },
            )

            result = ResourceUsage.rg_search_project_usage_buckets(
                resource_group="default",
                domain_name="domain1",
                request=SearchProjectUsageBucketsRequest(
                    filter=None,
                    order=None,
                    limit=50,
                    offset=0,
                ),
            )

            assert isinstance(result, SearchProjectUsageBucketsResponse)
            assert len(result.items) == 1
            assert result.items[0].resource_group == "default"
            assert result.items[0].domain_name == "domain1"
            assert result.pagination.total == 1

    @pytest.mark.asyncio
    async def test_rg_search_user_usage_buckets_success(self, dummy_endpoint: str) -> None:
        """Should search user usage buckets within RG, domain, and project scope."""
        with aioresponses() as m, Session():
            project_id = UUID("00000000-0000-0000-0000-000000000003")
            m.post(
                dummy_endpoint
                + f"fair-share/rg/default/domains/domain1/projects/{project_id}/usage-buckets/users/search",
                status=HTTPStatus.OK,
                payload={
                    "items": [
                        {
                            "id": "00000000-0000-0000-0000-000000000001",
                            "user_uuid": "00000000-0000-0000-0000-000000000002",
                            "project_id": str(project_id),
                            "domain_name": "domain1",
                            "resource_group": "default",
                            "metadata": {
                                "period_start": "2024-01-01",
                                "period_end": "2024-01-02",
                                "decay_unit_days": 1,
                                "created_at": "2024-01-02T00:00:00Z",
                                "updated_at": "2024-01-02T00:00:00Z",
                                "average_daily_usage": {"entries": []},
                                "usage_capacity_ratio": {"entries": []},
                                "average_capacity_per_second": {"entries": []},
                            },
                            "resource_usage": {"entries": []},
                            "capacity_snapshot": {"entries": []},
                        }
                    ],
                    "pagination": {"total": 1, "offset": 0, "limit": 50},
                },
            )

            result = ResourceUsage.rg_search_user_usage_buckets(
                resource_group="default",
                domain_name="domain1",
                project_id=project_id,
                request=SearchUserUsageBucketsRequest(
                    filter=None,
                    order=None,
                    limit=50,
                    offset=0,
                ),
            )

            assert isinstance(result, SearchUserUsageBucketsResponse)
            assert len(result.items) == 1
            assert result.items[0].resource_group == "default"
            assert result.items[0].domain_name == "domain1"
            assert result.items[0].project_id == project_id
            assert result.pagination.total == 1

    @pytest.mark.asyncio
    async def test_rg_search_domain_usage_buckets_with_filter(self, dummy_endpoint: str) -> None:
        """Should apply filter in RG-scoped domain search."""
        with aioresponses() as m, Session():
            m.post(
                dummy_endpoint + "fair-share/rg/default/usage-buckets/domains/search",
                status=HTTPStatus.OK,
                payload={
                    "items": [],
                    "pagination": {"total": 0, "offset": 0, "limit": 50},
                },
            )

            result = ResourceUsage.rg_search_domain_usage_buckets(
                resource_group="default",
                request=SearchDomainUsageBucketsRequest(
                    filter=DomainUsageBucketFilter(
                        domain_name=StringFilter(equals="domain1"),
                    ),
                    order=None,
                    limit=50,
                    offset=0,
                ),
            )

            assert isinstance(result, SearchDomainUsageBucketsResponse)
            assert len(result.items) == 0
            assert result.pagination.total == 0

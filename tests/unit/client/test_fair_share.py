"""Tests for fair share client SDK functions."""

from __future__ import annotations

from decimal import Decimal
from http import HTTPStatus
from unittest import mock
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from aioresponses import aioresponses

from ai.backend.client.config import API_VERSION
from ai.backend.client.func.fair_share import FairShare
from ai.backend.client.session import Session
from ai.backend.common.dto.manager.fair_share import (
    BulkUpsertDomainFairShareWeightRequest,
    BulkUpsertDomainFairShareWeightResponse,
    BulkUpsertProjectFairShareWeightRequest,
    BulkUpsertProjectFairShareWeightResponse,
    BulkUpsertUserFairShareWeightRequest,
    BulkUpsertUserFairShareWeightResponse,
    DomainUsageBucketFilter,
    DomainWeightEntryInput,
    ProjectWeightEntryInput,
    SearchDomainUsageBucketsRequest,
    SearchDomainUsageBucketsResponse,
    SearchProjectUsageBucketsRequest,
    SearchProjectUsageBucketsResponse,
    SearchUserUsageBucketsRequest,
    SearchUserUsageBucketsResponse,
    UserWeightEntryInput,
)
from ai.backend.common.dto.manager.query import StringFilter


@pytest.fixture(autouse=True)
def api_version_mock() -> mock.AsyncMock:
    """Mock API version negotiation."""
    mock_nego_func = AsyncMock()
    mock_nego_func.return_value = API_VERSION
    with mock.patch("ai.backend.client.session._negotiate_api_version", mock_nego_func):
        yield mock_nego_func


class TestFairShareBulkUpsert:
    """Bulk upsert operations tests."""

    @pytest.mark.asyncio
    async def test_bulk_upsert_domain_success(self, dummy_endpoint: str) -> None:
        """Should bulk upsert domain weights successfully."""
        with aioresponses() as m, Session():
            m.post(
                dummy_endpoint + "fair-share/domains/bulk-upsert-weight",
                status=HTTPStatus.OK,
                payload={"upserted_count": 2},
            )

            result = FairShare.bulk_upsert_domain_fair_share_weight(
                request=BulkUpsertDomainFairShareWeightRequest(
                    resource_group="default",
                    inputs=[
                        DomainWeightEntryInput(domain_name="domain1", weight=Decimal("2.0")),
                        DomainWeightEntryInput(domain_name="domain2", weight=Decimal("3.0")),
                    ],
                )
            )

            assert isinstance(result, BulkUpsertDomainFairShareWeightResponse)
            assert result.upserted_count == 2

    @pytest.mark.asyncio
    async def test_bulk_upsert_domain_with_null_weight(self, dummy_endpoint: str) -> None:
        """Should handle null weight correctly."""
        with aioresponses() as m, Session():
            m.post(
                dummy_endpoint + "fair-share/domains/bulk-upsert-weight",
                status=HTTPStatus.OK,
                payload={"upserted_count": 1},
            )

            result = FairShare.bulk_upsert_domain_fair_share_weight(
                request=BulkUpsertDomainFairShareWeightRequest(
                    resource_group="default",
                    inputs=[
                        DomainWeightEntryInput(domain_name="domain1", weight=None),
                    ],
                )
            )

            assert result.upserted_count == 1

    @pytest.mark.asyncio
    async def test_bulk_upsert_domain_empty_list(self, dummy_endpoint: str) -> None:
        """Should handle empty input list."""
        with aioresponses() as m, Session():
            m.post(
                dummy_endpoint + "fair-share/domains/bulk-upsert-weight",
                status=HTTPStatus.OK,
                payload={"upserted_count": 0},
            )

            result = FairShare.bulk_upsert_domain_fair_share_weight(
                request=BulkUpsertDomainFairShareWeightRequest(
                    resource_group="default",
                    inputs=[],
                )
            )

            assert result.upserted_count == 0

    @pytest.mark.asyncio
    async def test_bulk_upsert_project_success(self, dummy_endpoint: str) -> None:
        """Should bulk upsert project weights successfully."""
        with aioresponses() as m, Session():
            m.post(
                dummy_endpoint + "fair-share/projects/bulk-upsert-weight",
                status=HTTPStatus.OK,
                payload={"upserted_count": 2},
            )

            project_id_1 = UUID("00000000-0000-0000-0000-000000000001")
            project_id_2 = UUID("00000000-0000-0000-0000-000000000002")

            result = FairShare.bulk_upsert_project_fair_share_weight(
                request=BulkUpsertProjectFairShareWeightRequest(
                    resource_group="default",
                    inputs=[
                        ProjectWeightEntryInput(
                            project_id=project_id_1,
                            domain_name="domain1",
                            weight=Decimal("2.0"),
                        ),
                        ProjectWeightEntryInput(
                            project_id=project_id_2,
                            domain_name="domain1",
                            weight=Decimal("3.0"),
                        ),
                    ],
                )
            )

            assert isinstance(result, BulkUpsertProjectFairShareWeightResponse)
            assert result.upserted_count == 2

    @pytest.mark.asyncio
    async def test_bulk_upsert_project_with_null_weight(self, dummy_endpoint: str) -> None:
        """Should handle null weight correctly."""
        with aioresponses() as m, Session():
            m.post(
                dummy_endpoint + "fair-share/projects/bulk-upsert-weight",
                status=HTTPStatus.OK,
                payload={"upserted_count": 1},
            )

            project_id = UUID("00000000-0000-0000-0000-000000000001")

            result = FairShare.bulk_upsert_project_fair_share_weight(
                request=BulkUpsertProjectFairShareWeightRequest(
                    resource_group="default",
                    inputs=[
                        ProjectWeightEntryInput(
                            project_id=project_id,
                            domain_name="domain1",
                            weight=None,
                        ),
                    ],
                )
            )

            assert result.upserted_count == 1

    @pytest.mark.asyncio
    async def test_bulk_upsert_user_success(self, dummy_endpoint: str) -> None:
        """Should bulk upsert user weights successfully."""
        with aioresponses() as m, Session():
            m.post(
                dummy_endpoint + "fair-share/users/bulk-upsert-weight",
                status=HTTPStatus.OK,
                payload={"upserted_count": 2},
            )

            user_uuid_1 = UUID("00000000-0000-0000-0000-000000000001")
            user_uuid_2 = UUID("00000000-0000-0000-0000-000000000002")
            project_id = UUID("00000000-0000-0000-0000-000000000003")

            result = FairShare.bulk_upsert_user_fair_share_weight(
                request=BulkUpsertUserFairShareWeightRequest(
                    resource_group="default",
                    inputs=[
                        UserWeightEntryInput(
                            user_uuid=user_uuid_1,
                            project_id=project_id,
                            domain_name="domain1",
                            weight=Decimal("2.0"),
                        ),
                        UserWeightEntryInput(
                            user_uuid=user_uuid_2,
                            project_id=project_id,
                            domain_name="domain1",
                            weight=Decimal("3.0"),
                        ),
                    ],
                )
            )

            assert isinstance(result, BulkUpsertUserFairShareWeightResponse)
            assert result.upserted_count == 2

    @pytest.mark.asyncio
    async def test_bulk_upsert_user_with_null_weight(self, dummy_endpoint: str) -> None:
        """Should handle null weight correctly."""
        with aioresponses() as m, Session():
            m.post(
                dummy_endpoint + "fair-share/users/bulk-upsert-weight",
                status=HTTPStatus.OK,
                payload={"upserted_count": 1},
            )

            user_uuid = UUID("00000000-0000-0000-0000-000000000001")
            project_id = UUID("00000000-0000-0000-0000-000000000002")

            result = FairShare.bulk_upsert_user_fair_share_weight(
                request=BulkUpsertUserFairShareWeightRequest(
                    resource_group="default",
                    inputs=[
                        UserWeightEntryInput(
                            user_uuid=user_uuid,
                            project_id=project_id,
                            domain_name="domain1",
                            weight=None,
                        ),
                    ],
                )
            )

            assert result.upserted_count == 1


class TestFairShareUsageBuckets:
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
                            },
                            "resource_usage": {"entries": []},
                            "capacity_snapshot": {"entries": []},
                        }
                    ],
                    "pagination": {"total": 1, "offset": 0, "limit": 50},
                },
            )

            result = FairShare.search_domain_usage_buckets(
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
    async def test_search_domain_usage_buckets_with_filter(self, dummy_endpoint: str) -> None:
        """Should apply filter correctly."""
        with aioresponses() as m, Session():
            m.post(
                dummy_endpoint + "fair-share/usage-buckets/domains/search",
                status=HTTPStatus.OK,
                payload={
                    "items": [],
                    "pagination": {"total": 0, "offset": 0, "limit": 50},
                },
            )

            result = FairShare.search_domain_usage_buckets(
                request=SearchDomainUsageBucketsRequest(
                    filter=DomainUsageBucketFilter(
                        domain_name=StringFilter(equals="domain1"),
                        resource_group=StringFilter(equals="default"),
                    ),
                    order=None,
                    limit=50,
                    offset=0,
                )
            )

            assert isinstance(result, SearchDomainUsageBucketsResponse)
            assert len(result.items) == 0

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
                            },
                            "resource_usage": {"entries": []},
                            "capacity_snapshot": {"entries": []},
                        }
                    ],
                    "pagination": {"total": 1, "offset": 0, "limit": 50},
                },
            )

            result = FairShare.search_project_usage_buckets(
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
                            },
                            "resource_usage": {"entries": []},
                            "capacity_snapshot": {"entries": []},
                        }
                    ],
                    "pagination": {"total": 1, "offset": 0, "limit": 50},
                },
            )

            result = FairShare.search_user_usage_buckets(
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

    @pytest.mark.asyncio
    async def test_search_user_usage_buckets_with_pagination(self, dummy_endpoint: str) -> None:
        """Should handle pagination parameters."""
        with aioresponses() as m, Session():
            m.post(
                dummy_endpoint + "fair-share/usage-buckets/users/search",
                status=HTTPStatus.OK,
                payload={
                    "items": [],
                    "pagination": {"total": 100, "offset": 50, "limit": 25},
                },
            )

            result = FairShare.search_user_usage_buckets(
                request=SearchUserUsageBucketsRequest(
                    filter=None,
                    order=None,
                    limit=25,
                    offset=50,
                )
            )

            assert isinstance(result, SearchUserUsageBucketsResponse)
            assert result.pagination.total == 100
            assert result.pagination.offset == 50
            assert result.pagination.limit == 25

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.fair_share import FairShareClient
from ai.backend.common.dto.manager.fair_share import (
    BulkUpsertDomainFairShareWeightRequest,
    BulkUpsertDomainFairShareWeightResponse,
    BulkUpsertProjectFairShareWeightRequest,
    BulkUpsertProjectFairShareWeightResponse,
    BulkUpsertUserFairShareWeightRequest,
    BulkUpsertUserFairShareWeightResponse,
    DomainWeightEntryInput,
    GetDomainFairShareResponse,
    GetProjectFairShareResponse,
    GetResourceGroupFairShareSpecResponse,
    GetUserFairShareResponse,
    ProjectWeightEntryInput,
    SearchDomainFairSharesRequest,
    SearchDomainFairSharesResponse,
    SearchDomainUsageBucketsRequest,
    SearchDomainUsageBucketsResponse,
    SearchProjectFairSharesRequest,
    SearchProjectFairSharesResponse,
    SearchProjectUsageBucketsRequest,
    SearchProjectUsageBucketsResponse,
    SearchResourceGroupFairShareSpecsResponse,
    SearchUserFairSharesRequest,
    SearchUserFairSharesResponse,
    SearchUserUsageBucketsRequest,
    SearchUserUsageBucketsResponse,
    UpdateResourceGroupFairShareSpecRequest,
    UpdateResourceGroupFairShareSpecResponse,
    UpsertDomainFairShareWeightRequest,
    UpsertDomainFairShareWeightResponse,
    UpsertProjectFairShareWeightRequest,
    UpsertProjectFairShareWeightResponse,
    UpsertUserFairShareWeightRequest,
    UpsertUserFairShareWeightResponse,
    UserWeightEntryInput,
)

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))

_SAMPLE_UUID_1 = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_SAMPLE_UUID_2 = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
_SAMPLE_UUID_3 = "cccccccc-cccc-cccc-cccc-cccccccccccc"


def _make_client(mock_session: MagicMock | None = None) -> BackendAIClient:
    return BackendAIClient(
        _DEFAULT_CONFIG,
        MockAuth(),
        mock_session or MagicMock(),
    )


def _make_request_session(resp: AsyncMock) -> MagicMock:
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _ok_response(data: object) -> AsyncMock:
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(return_value=data)
    return resp


def _fair_share_spec_data() -> dict[str, Any]:
    return {
        "weight": "1.0",
        "half_life_days": 7,
        "lookback_days": 30,
        "decay_unit_days": 1,
        "resource_weights": {"entries": [{"resource_type": "cpu", "quantity": "1.0"}]},
    }


def _calculation_snapshot_data() -> dict[str, Any]:
    return {
        "fair_share_factor": "0.5",
        "total_decayed_usage": {"entries": [{"resource_type": "cpu", "quantity": "10.0"}]},
        "normalized_usage": "0.3",
        "lookback_start": "2026-01-01",
        "lookback_end": "2026-01-31",
        "last_calculated_at": "2026-01-31T12:00:00",
    }


def _domain_fair_share_data(
    *,
    id: str = _SAMPLE_UUID_1,
    resource_group: str = "default",
    domain_name: str = "test-domain",
) -> dict[str, Any]:
    return {
        "id": id,
        "resource_group": resource_group,
        "domain_name": domain_name,
        "spec": _fair_share_spec_data(),
        "calculation_snapshot": _calculation_snapshot_data(),
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-31T12:00:00",
    }


def _project_fair_share_data(
    *,
    id: str = _SAMPLE_UUID_1,
    resource_group: str = "default",
    project_id: str = _SAMPLE_UUID_2,
    domain_name: str = "test-domain",
) -> dict[str, Any]:
    return {
        "id": id,
        "resource_group": resource_group,
        "project_id": project_id,
        "domain_name": domain_name,
        "spec": _fair_share_spec_data(),
        "calculation_snapshot": _calculation_snapshot_data(),
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-31T12:00:00",
    }


def _user_fair_share_data(
    *,
    id: str = _SAMPLE_UUID_1,
    resource_group: str = "default",
    user_uuid: str = _SAMPLE_UUID_3,
    project_id: str = _SAMPLE_UUID_2,
    domain_name: str = "test-domain",
) -> dict[str, Any]:
    return {
        "id": id,
        "resource_group": resource_group,
        "user_uuid": user_uuid,
        "project_id": project_id,
        "domain_name": domain_name,
        "spec": _fair_share_spec_data(),
        "calculation_snapshot": _calculation_snapshot_data(),
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-31T12:00:00",
    }


def _usage_bucket_metadata() -> dict[str, Any]:
    return {
        "period_start": "2026-01-01",
        "period_end": "2026-01-02",
        "decay_unit_days": 1,
        "created_at": "2026-01-02T00:00:00",
        "updated_at": "2026-01-02T00:00:00",
        "average_daily_usage": {"entries": [{"resource_type": "cpu", "quantity": "2.0"}]},
        "usage_capacity_ratio": {"entries": [{"resource_type": "cpu", "quantity": "0.1"}]},
    }


def _pagination_data(total: int = 1, offset: int = 0, limit: int = 50) -> dict[str, Any]:
    return {"total": total, "offset": offset, "limit": limit}


class TestFairShareClientDomainFairShare:
    @pytest.mark.asyncio
    async def test_get_domain_fair_share(self) -> None:
        raw = {"item": _domain_fair_share_data()}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        result = await fs.get_domain_fair_share("default", "test-domain")

        assert isinstance(result, GetDomainFairShareResponse)
        assert result.item is not None
        assert result.item.domain_name == "test-domain"
        assert result.item.resource_group == "default"
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/fair-share/domains/default/test-domain" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_get_domain_fair_share_none(self) -> None:
        raw = {"item": None}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        result = await fs.get_domain_fair_share("default", "missing")

        assert isinstance(result, GetDomainFairShareResponse)
        assert result.item is None

    @pytest.mark.asyncio
    async def test_search_domain_fair_shares(self) -> None:
        raw = {
            "items": [_domain_fair_share_data()],
            "pagination": _pagination_data(),
        }
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = SearchDomainFairSharesRequest()
        result = await fs.search_domain_fair_shares(request)

        assert isinstance(result, SearchDomainFairSharesResponse)
        assert len(result.items) == 1
        assert result.pagination.total == 1
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/fair-share/domains/search" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_rg_get_domain_fair_share(self) -> None:
        raw = {"item": _domain_fair_share_data()}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        result = await fs.rg_get_domain_fair_share("default", "test-domain")

        assert isinstance(result, GetDomainFairShareResponse)
        assert result.item is not None
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/fair-share/rg/default/domains/test-domain" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_rg_search_domain_fair_shares(self) -> None:
        raw = {
            "items": [_domain_fair_share_data()],
            "pagination": _pagination_data(),
        }
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = SearchDomainFairSharesRequest()
        result = await fs.rg_search_domain_fair_shares("default", request)

        assert isinstance(result, SearchDomainFairSharesResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/fair-share/rg/default/domains/search" in str(call_args[0][1])


class TestFairShareClientProjectFairShare:
    @pytest.mark.asyncio
    async def test_get_project_fair_share(self) -> None:
        raw = {"item": _project_fair_share_data()}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        result = await fs.get_project_fair_share("default", UUID(_SAMPLE_UUID_2))

        assert isinstance(result, GetProjectFairShareResponse)
        assert result.item is not None
        assert result.item.project_id == UUID(_SAMPLE_UUID_2)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert f"/fair-share/projects/default/{_SAMPLE_UUID_2}" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_get_project_fair_share_none(self) -> None:
        raw = {"item": None}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        result = await fs.get_project_fair_share("default", UUID(_SAMPLE_UUID_2))

        assert isinstance(result, GetProjectFairShareResponse)
        assert result.item is None

    @pytest.mark.asyncio
    async def test_search_project_fair_shares(self) -> None:
        raw = {
            "items": [_project_fair_share_data()],
            "pagination": _pagination_data(),
        }
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = SearchProjectFairSharesRequest()
        result = await fs.search_project_fair_shares(request)

        assert isinstance(result, SearchProjectFairSharesResponse)
        assert len(result.items) == 1
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/fair-share/projects/search" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_rg_get_project_fair_share(self) -> None:
        raw = {"item": _project_fair_share_data()}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        result = await fs.rg_get_project_fair_share("default", "test-domain", UUID(_SAMPLE_UUID_2))

        assert isinstance(result, GetProjectFairShareResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert f"/fair-share/rg/default/domains/test-domain/projects/{_SAMPLE_UUID_2}" in str(
            call_args[0][1]
        )

    @pytest.mark.asyncio
    async def test_rg_search_project_fair_shares(self) -> None:
        raw = {
            "items": [_project_fair_share_data()],
            "pagination": _pagination_data(),
        }
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = SearchProjectFairSharesRequest()
        result = await fs.rg_search_project_fair_shares("default", "test-domain", request)

        assert isinstance(result, SearchProjectFairSharesResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/fair-share/rg/default/domains/test-domain/projects/search" in str(call_args[0][1])


class TestFairShareClientUserFairShare:
    @pytest.mark.asyncio
    async def test_get_user_fair_share(self) -> None:
        raw = {"item": _user_fair_share_data()}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        result = await fs.get_user_fair_share("default", UUID(_SAMPLE_UUID_2), UUID(_SAMPLE_UUID_3))

        assert isinstance(result, GetUserFairShareResponse)
        assert result.item is not None
        assert result.item.user_uuid == UUID(_SAMPLE_UUID_3)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert f"/fair-share/users/default/{_SAMPLE_UUID_2}/{_SAMPLE_UUID_3}" in str(
            call_args[0][1]
        )

    @pytest.mark.asyncio
    async def test_get_user_fair_share_none(self) -> None:
        raw = {"item": None}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        result = await fs.get_user_fair_share("default", UUID(_SAMPLE_UUID_2), UUID(_SAMPLE_UUID_3))

        assert isinstance(result, GetUserFairShareResponse)
        assert result.item is None

    @pytest.mark.asyncio
    async def test_search_user_fair_shares(self) -> None:
        raw = {
            "items": [_user_fair_share_data()],
            "pagination": _pagination_data(),
        }
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = SearchUserFairSharesRequest()
        result = await fs.search_user_fair_shares(request)

        assert isinstance(result, SearchUserFairSharesResponse)
        assert len(result.items) == 1
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/fair-share/users/search" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_rg_get_user_fair_share(self) -> None:
        raw = {"item": _user_fair_share_data()}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        result = await fs.rg_get_user_fair_share(
            "default", "test-domain", UUID(_SAMPLE_UUID_2), UUID(_SAMPLE_UUID_3)
        )

        assert isinstance(result, GetUserFairShareResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert (
            f"/fair-share/rg/default/domains/test-domain/projects/{_SAMPLE_UUID_2}/users/{_SAMPLE_UUID_3}"
            in str(call_args[0][1])
        )

    @pytest.mark.asyncio
    async def test_rg_search_user_fair_shares(self) -> None:
        raw = {
            "items": [_user_fair_share_data()],
            "pagination": _pagination_data(),
        }
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = SearchUserFairSharesRequest()
        result = await fs.rg_search_user_fair_shares(
            "default", "test-domain", UUID(_SAMPLE_UUID_2), request
        )

        assert isinstance(result, SearchUserFairSharesResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert (
            f"/fair-share/rg/default/domains/test-domain/projects/{_SAMPLE_UUID_2}/users/search"
            in str(call_args[0][1])
        )


class TestFairShareClientUsageBuckets:
    @pytest.mark.asyncio
    async def test_search_domain_usage_buckets(self) -> None:
        raw = {
            "items": [
                {
                    "id": _SAMPLE_UUID_1,
                    "domain_name": "test-domain",
                    "resource_group": "default",
                    "metadata": _usage_bucket_metadata(),
                    "resource_usage": {"entries": [{"resource_type": "cpu", "quantity": "5.0"}]},
                    "capacity_snapshot": {
                        "entries": [{"resource_type": "cpu", "quantity": "100.0"}]
                    },
                }
            ],
            "pagination": _pagination_data(),
        }
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = SearchDomainUsageBucketsRequest()
        result = await fs.search_domain_usage_buckets(request)

        assert isinstance(result, SearchDomainUsageBucketsResponse)
        assert len(result.items) == 1
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/fair-share/usage-buckets/domains/search" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_search_project_usage_buckets(self) -> None:
        raw = {
            "items": [
                {
                    "id": _SAMPLE_UUID_1,
                    "project_id": _SAMPLE_UUID_2,
                    "domain_name": "test-domain",
                    "resource_group": "default",
                    "metadata": _usage_bucket_metadata(),
                    "resource_usage": {"entries": [{"resource_type": "cpu", "quantity": "3.0"}]},
                    "capacity_snapshot": {
                        "entries": [{"resource_type": "cpu", "quantity": "100.0"}]
                    },
                }
            ],
            "pagination": _pagination_data(),
        }
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = SearchProjectUsageBucketsRequest()
        result = await fs.search_project_usage_buckets(request)

        assert isinstance(result, SearchProjectUsageBucketsResponse)
        assert len(result.items) == 1
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/fair-share/usage-buckets/projects/search" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_search_user_usage_buckets(self) -> None:
        raw = {
            "items": [
                {
                    "id": _SAMPLE_UUID_1,
                    "user_uuid": _SAMPLE_UUID_3,
                    "project_id": _SAMPLE_UUID_2,
                    "domain_name": "test-domain",
                    "resource_group": "default",
                    "metadata": _usage_bucket_metadata(),
                    "resource_usage": {"entries": [{"resource_type": "cpu", "quantity": "1.0"}]},
                    "capacity_snapshot": {
                        "entries": [{"resource_type": "cpu", "quantity": "100.0"}]
                    },
                }
            ],
            "pagination": _pagination_data(),
        }
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = SearchUserUsageBucketsRequest()
        result = await fs.search_user_usage_buckets(request)

        assert isinstance(result, SearchUserUsageBucketsResponse)
        assert len(result.items) == 1
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/fair-share/usage-buckets/users/search" in str(call_args[0][1])


class TestFairShareClientRGScopedUsageBuckets:
    @pytest.mark.asyncio
    async def test_rg_search_domain_usage_buckets(self) -> None:
        raw = {"items": [], "pagination": _pagination_data(total=0)}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = SearchDomainUsageBucketsRequest()
        result = await fs.rg_search_domain_usage_buckets("default", request)

        assert isinstance(result, SearchDomainUsageBucketsResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/fair-share/rg/default/usage-buckets/domains/search" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_rg_search_project_usage_buckets(self) -> None:
        raw = {"items": [], "pagination": _pagination_data(total=0)}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = SearchProjectUsageBucketsRequest()
        result = await fs.rg_search_project_usage_buckets("default", "test-domain", request)

        assert isinstance(result, SearchProjectUsageBucketsResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/fair-share/rg/default/domains/test-domain/usage-buckets/projects/search" in str(
            call_args[0][1]
        )

    @pytest.mark.asyncio
    async def test_rg_search_user_usage_buckets(self) -> None:
        raw = {"items": [], "pagination": _pagination_data(total=0)}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = SearchUserUsageBucketsRequest()
        result = await fs.rg_search_user_usage_buckets(
            "default", "test-domain", UUID(_SAMPLE_UUID_2), request
        )

        assert isinstance(result, SearchUserUsageBucketsResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert (
            f"/fair-share/rg/default/domains/test-domain/projects/{_SAMPLE_UUID_2}/usage-buckets/users/search"
            in str(call_args[0][1])
        )


class TestFairShareClientWeights:
    @pytest.mark.asyncio
    async def test_upsert_domain_fair_share_weight(self) -> None:
        raw = {"item": _domain_fair_share_data()}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = UpsertDomainFairShareWeightRequest(weight=Decimal("2.0"))
        result = await fs.upsert_domain_fair_share_weight("default", "test-domain", request)

        assert isinstance(result, UpsertDomainFairShareWeightResponse)
        assert result.item.domain_name == "test-domain"
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PUT"
        assert "/fair-share/domains/default/test-domain/weight" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_upsert_project_fair_share_weight(self) -> None:
        raw = {"item": _project_fair_share_data()}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = UpsertProjectFairShareWeightRequest(
            domain_name="test-domain", weight=Decimal("1.5")
        )
        result = await fs.upsert_project_fair_share_weight("default", UUID(_SAMPLE_UUID_2), request)

        assert isinstance(result, UpsertProjectFairShareWeightResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PUT"
        assert f"/fair-share/projects/default/{_SAMPLE_UUID_2}/weight" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_upsert_user_fair_share_weight(self) -> None:
        raw = {"item": _user_fair_share_data()}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = UpsertUserFairShareWeightRequest(domain_name="test-domain", weight=Decimal("0.5"))
        result = await fs.upsert_user_fair_share_weight(
            "default", UUID(_SAMPLE_UUID_2), UUID(_SAMPLE_UUID_3), request
        )

        assert isinstance(result, UpsertUserFairShareWeightResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PUT"
        assert f"/fair-share/users/default/{_SAMPLE_UUID_2}/{_SAMPLE_UUID_3}/weight" in str(
            call_args[0][1]
        )


class TestFairShareClientBulkWeights:
    @pytest.mark.asyncio
    async def test_bulk_upsert_domain_fair_share_weight(self) -> None:
        raw = {"upserted_count": 2}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = BulkUpsertDomainFairShareWeightRequest(
            resource_group="default",
            inputs=[
                DomainWeightEntryInput(domain_name="d1", weight=Decimal("1.0")),
                DomainWeightEntryInput(domain_name="d2", weight=None),
            ],
        )
        result = await fs.bulk_upsert_domain_fair_share_weight(request)

        assert isinstance(result, BulkUpsertDomainFairShareWeightResponse)
        assert result.upserted_count == 2
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/fair-share/domains/bulk-upsert-weight" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_bulk_upsert_project_fair_share_weight(self) -> None:
        raw = {"upserted_count": 1}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = BulkUpsertProjectFairShareWeightRequest(
            resource_group="default",
            inputs=[
                ProjectWeightEntryInput(
                    project_id=UUID(_SAMPLE_UUID_2),
                    domain_name="test-domain",
                    weight=Decimal("1.0"),
                ),
            ],
        )
        result = await fs.bulk_upsert_project_fair_share_weight(request)

        assert isinstance(result, BulkUpsertProjectFairShareWeightResponse)
        assert result.upserted_count == 1
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/fair-share/projects/bulk-upsert-weight" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_bulk_upsert_user_fair_share_weight(self) -> None:
        raw = {"upserted_count": 3}
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = BulkUpsertUserFairShareWeightRequest(
            resource_group="default",
            inputs=[
                UserWeightEntryInput(
                    user_uuid=UUID(_SAMPLE_UUID_3),
                    project_id=UUID(_SAMPLE_UUID_2),
                    domain_name="test-domain",
                    weight=Decimal("1.0"),
                ),
            ],
        )
        result = await fs.bulk_upsert_user_fair_share_weight(request)

        assert isinstance(result, BulkUpsertUserFairShareWeightResponse)
        assert result.upserted_count == 3
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/fair-share/users/bulk-upsert-weight" in str(call_args[0][1])


class TestFairShareClientResourceGroupSpec:
    @pytest.mark.asyncio
    async def test_get_resource_group_fair_share_spec(self) -> None:
        raw = {
            "resource_group": "default",
            "fair_share_spec": {
                "half_life_days": 7,
                "lookback_days": 30,
                "decay_unit_days": 1,
                "default_weight": "1.0",
                "resource_weights": {"entries": [{"resource_type": "cpu", "quantity": "1.0"}]},
            },
        }
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        result = await fs.get_resource_group_fair_share_spec("default")

        assert isinstance(result, GetResourceGroupFairShareSpecResponse)
        assert result.resource_group == "default"
        assert result.fair_share_spec.half_life_days == 7
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/fair-share/resource-groups/default/spec" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_search_resource_group_fair_share_specs(self) -> None:
        raw = {
            "items": [
                {
                    "resource_group": "default",
                    "fair_share_spec": {
                        "half_life_days": 7,
                        "lookback_days": 30,
                        "decay_unit_days": 1,
                        "default_weight": "1.0",
                        "resource_weights": {
                            "entries": [{"resource_type": "cpu", "quantity": "1.0"}]
                        },
                    },
                }
            ],
            "total_count": 1,
        }
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        result = await fs.search_resource_group_fair_share_specs()

        assert isinstance(result, SearchResourceGroupFairShareSpecsResponse)
        assert len(result.items) == 1
        assert result.total_count == 1
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/fair-share/resource-groups/specs" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_update_resource_group_fair_share_spec(self) -> None:
        raw = {
            "resource_group": "default",
            "fair_share_spec": {
                "half_life_days": 14,
                "lookback_days": 60,
                "decay_unit_days": 1,
                "default_weight": "2.0",
                "resource_weights": {"entries": [{"resource_type": "cpu", "quantity": "1.0"}]},
            },
        }
        mock_session = _make_request_session(_ok_response(raw))
        client = _make_client(mock_session)
        fs = FairShareClient(client)

        request = UpdateResourceGroupFairShareSpecRequest(
            half_life_days=14,
            lookback_days=60,
            default_weight=Decimal("2.0"),
        )
        result = await fs.update_resource_group_fair_share_spec("default", request)

        assert isinstance(result, UpdateResourceGroupFairShareSpecResponse)
        assert result.fair_share_spec.half_life_days == 14
        assert result.fair_share_spec.lookback_days == 60
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PATCH"
        assert "/fair-share/resource-groups/default/spec" in str(call_args[0][1])

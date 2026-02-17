from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.domain import DomainClient
from ai.backend.common.dto.manager.domain import (
    CreateDomainRequest,
    CreateDomainResponse,
    DeleteDomainRequest,
    DeleteDomainResponse,
    DomainFilter,
    GetDomainResponse,
    PurgeDomainRequest,
    PurgeDomainResponse,
    SearchDomainsRequest,
    SearchDomainsResponse,
    UpdateDomainRequest,
    UpdateDomainResponse,
)
from ai.backend.common.dto.manager.query import StringFilter

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_request_session(resp: AsyncMock) -> MagicMock:
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _json_response(data: dict[str, Any], *, status: int = 200) -> AsyncMock:
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=data)
    return resp


def _make_domain_client(mock_session: MagicMock) -> DomainClient:
    client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)
    return DomainClient(client)


def _last_request_call(mock_session: MagicMock) -> tuple[str, str, dict[str, Any] | None]:
    args, kwargs = mock_session.request.call_args
    return args[0], str(args[1]), kwargs.get("json")


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

_SAMPLE_DOMAIN_DTO: dict[str, Any] = {
    "name": "test-domain",
    "description": "A test domain",
    "is_active": True,
    "created_at": "2025-01-01T00:00:00",
    "modified_at": "2025-01-01T00:00:00",
    "total_resource_slots": {},
    "allowed_vfolder_hosts": {},
    "allowed_docker_registries": [],
    "integration_id": None,
}


# ---------------------------------------------------------------------------
# Domain CRUD
# ---------------------------------------------------------------------------


class TestDomainCreate:
    @pytest.mark.asyncio
    async def test_create_domain(self) -> None:
        resp = _json_response({"domain": _SAMPLE_DOMAIN_DTO})
        mock_session = _make_request_session(resp)
        dc = _make_domain_client(mock_session)

        request = CreateDomainRequest(
            name="test-domain",
            description="A test domain",
        )
        result = await dc.create(request)

        assert isinstance(result, CreateDomainResponse)
        assert result.domain.name == "test-domain"
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/domains")
        assert body is not None
        assert body["name"] == "test-domain"
        assert body["description"] == "A test domain"


class TestDomainGet:
    @pytest.mark.asyncio
    async def test_get_domain(self) -> None:
        resp = _json_response({"domain": _SAMPLE_DOMAIN_DTO})
        mock_session = _make_request_session(resp)
        dc = _make_domain_client(mock_session)

        result = await dc.get("test-domain")

        assert isinstance(result, GetDomainResponse)
        assert result.domain.name == "test-domain"
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert "/admin/domains/test-domain" in url


class TestDomainSearch:
    @pytest.mark.asyncio
    async def test_search_domains(self) -> None:
        resp = _json_response({
            "domains": [_SAMPLE_DOMAIN_DTO],
            "pagination": {"total": 1, "offset": 0, "limit": 50},
        })
        mock_session = _make_request_session(resp)
        dc = _make_domain_client(mock_session)

        result = await dc.search(SearchDomainsRequest())

        assert isinstance(result, SearchDomainsResponse)
        assert len(result.domains) == 1
        assert result.pagination.total == 1
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/domains/search")
        assert body is not None

    @pytest.mark.asyncio
    async def test_search_domains_with_filter(self) -> None:
        resp = _json_response({
            "domains": [_SAMPLE_DOMAIN_DTO],
            "pagination": {"total": 1, "offset": 0, "limit": 50},
        })
        mock_session = _make_request_session(resp)
        dc = _make_domain_client(mock_session)

        request = SearchDomainsRequest(
            filter=DomainFilter(
                name=StringFilter(contains="test"),
                is_active=True,
            ),
            limit=10,
            offset=0,
        )
        result = await dc.search(request)

        assert isinstance(result, SearchDomainsResponse)
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert body is not None
        assert body["filter"]["name"]["contains"] == "test"
        assert body["filter"]["is_active"] is True
        assert body["limit"] == 10


class TestDomainUpdate:
    @pytest.mark.asyncio
    async def test_update_domain(self) -> None:
        updated_dto = {**_SAMPLE_DOMAIN_DTO, "description": "Updated description"}
        resp = _json_response({"domain": updated_dto})
        mock_session = _make_request_session(resp)
        dc = _make_domain_client(mock_session)

        result = await dc.update(
            "test-domain",
            UpdateDomainRequest(description="Updated description"),
        )

        assert isinstance(result, UpdateDomainResponse)
        assert result.domain.description == "Updated description"
        method, url, body = _last_request_call(mock_session)
        assert method == "PATCH"
        assert "/admin/domains/test-domain" in url
        assert body is not None
        assert body["description"] == "Updated description"


class TestDomainDelete:
    @pytest.mark.asyncio
    async def test_delete_domain(self) -> None:
        resp = _json_response({"deleted": True})
        mock_session = _make_request_session(resp)
        dc = _make_domain_client(mock_session)

        result = await dc.delete(DeleteDomainRequest(name="test-domain"))

        assert isinstance(result, DeleteDomainResponse)
        assert result.deleted is True
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/domains/delete")
        assert body is not None
        assert body["name"] == "test-domain"


class TestDomainPurge:
    @pytest.mark.asyncio
    async def test_purge_domain(self) -> None:
        resp = _json_response({"purged": True})
        mock_session = _make_request_session(resp)
        dc = _make_domain_client(mock_session)

        result = await dc.purge(PurgeDomainRequest(name="test-domain"))

        assert isinstance(result, PurgeDomainResponse)
        assert result.purged is True
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/domains/purge")
        assert body is not None
        assert body["name"] == "test-domain"

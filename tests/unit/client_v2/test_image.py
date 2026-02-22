from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.image import ImageClient
from ai.backend.common.dto.manager.image.request import (
    AliasImageRequest,
    DealiasImageRequest,
    ForgetImageRequest,
    ImageFilter,
    ImageOrder,
    PurgeImageRequest,
    RescanImagesRequest,
    SearchImagesRequest,
)
from ai.backend.common.dto.manager.image.response import (
    AliasImageResponse,
    ForgetImageResponse,
    GetImageResponse,
    PurgeImageResponse,
    RescanImagesResponse,
    SearchImagesResponse,
)
from ai.backend.common.dto.manager.image.types import (
    ImageOrderField,
    OrderDirection,
)
from ai.backend.common.dto.manager.query import StringFilter

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))

_SAMPLE_IMAGE_ID = UUID("11111111-1111-1111-1111-111111111111")
_SAMPLE_REGISTRY_ID = UUID("22222222-2222-2222-2222-222222222222")
_SAMPLE_ALIAS_ID = UUID("33333333-3333-3333-3333-333333333333")

_SAMPLE_IMAGE_DATA = {
    "id": str(_SAMPLE_IMAGE_ID),
    "name": "cr.example.com/lablup/python:3.11-ubuntu22.04",
    "registry": "cr.example.com",
    "registry_id": str(_SAMPLE_REGISTRY_ID),
    "project": "lablup",
    "tag": "3.11-ubuntu22.04",
    "architecture": "x86_64",
    "size_bytes": 1024000,
    "type": "compute",
    "status": "ALIVE",
    "labels": [{"key": "ai.backend.runtime-type", "value": "python"}],
    "tags": [{"key": "runtime", "value": "python"}, {"key": "version", "value": "3.11"}],
    "resource_limits": [{"key": "cpu", "min": "1", "max": "8"}],
    "accelerators": None,
    "config_digest": "sha256:abc123",
    "is_local": False,
    "created_at": "2025-01-01T00:00:00Z",
}


def _make_request_session(resp: AsyncMock) -> MagicMock:
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _make_client(mock_session: MagicMock) -> BackendAIClient:
    return BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)


def _make_image_client(mock_session: MagicMock) -> ImageClient:
    return ImageClient(_make_client(mock_session))


class TestSearchImages:
    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [_SAMPLE_IMAGE_DATA],
                "pagination": {"total": 1, "offset": 0, "limit": 50},
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_image_client(mock_session)

        request = SearchImagesRequest()
        result = await client.search(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/admin/images/search" in str(call_args[0][1])
        assert isinstance(result, SearchImagesResponse)
        assert len(result.items) == 1
        assert result.items[0].id == _SAMPLE_IMAGE_ID
        assert result.items[0].name == "cr.example.com/lablup/python:3.11-ubuntu22.04"
        assert result.items[0].architecture == "x86_64"
        assert result.pagination.total == 1

    @pytest.mark.asyncio
    async def test_with_name_filter(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [],
                "pagination": {"total": 0, "offset": 0, "limit": 50},
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_image_client(mock_session)

        request = SearchImagesRequest(
            filter=ImageFilter(
                name=StringFilter(contains="python"),
            ),
        )
        result = await client.search(request)

        call_kwargs = mock_session.request.call_args.kwargs
        body = call_kwargs["json"]
        assert body["filter"]["name"]["contains"] == "python"
        assert isinstance(result, SearchImagesResponse)

    @pytest.mark.asyncio
    async def test_with_ordering(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [],
                "pagination": {"total": 0, "offset": 0, "limit": 50},
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_image_client(mock_session)

        request = SearchImagesRequest(
            order=[
                ImageOrder(
                    field=ImageOrderField.CREATED_AT,
                    direction=OrderDirection.DESC,
                ),
            ],
            limit=25,
        )
        result = await client.search(request)

        call_kwargs = mock_session.request.call_args.kwargs
        body = call_kwargs["json"]
        assert body["order"][0]["field"] == "created_at"
        assert body["order"][0]["direction"] == "desc"
        assert body["limit"] == 25
        assert isinstance(result, SearchImagesResponse)


class TestGetImage:
    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "item": _SAMPLE_IMAGE_DATA,
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_image_client(mock_session)

        result = await client.get(_SAMPLE_IMAGE_ID)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert f"/admin/images/{_SAMPLE_IMAGE_ID}" in str(call_args[0][1])
        assert isinstance(result, GetImageResponse)
        assert result.item.id == _SAMPLE_IMAGE_ID
        assert result.item.registry == "cr.example.com"
        assert result.item.is_local is False
        assert len(result.item.labels) == 1
        assert result.item.labels[0].key == "ai.backend.runtime-type"


class TestRescanImages:
    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "item": _SAMPLE_IMAGE_DATA,
                "errors": [],
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_image_client(mock_session)

        request = RescanImagesRequest(
            canonical="cr.example.com/lablup/python:3.11-ubuntu22.04",
            architecture="x86_64",
        )
        result = await client.rescan(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/admin/images/rescan" in str(call_args[0][1])
        call_kwargs = mock_session.request.call_args.kwargs
        body = call_kwargs["json"]
        assert body["canonical"] == "cr.example.com/lablup/python:3.11-ubuntu22.04"
        assert body["architecture"] == "x86_64"
        assert isinstance(result, RescanImagesResponse)
        assert result.item.id == _SAMPLE_IMAGE_ID
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_with_errors(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "item": _SAMPLE_IMAGE_DATA,
                "errors": ["Failed to fetch manifest"],
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_image_client(mock_session)

        request = RescanImagesRequest(
            canonical="cr.example.com/lablup/python:3.11-ubuntu22.04",
            architecture="x86_64",
        )
        result = await client.rescan(request)

        assert isinstance(result, RescanImagesResponse)
        assert len(result.errors) == 1
        assert result.errors[0] == "Failed to fetch manifest"


class TestAliasImage:
    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "alias_id": str(_SAMPLE_ALIAS_ID),
                "alias": "python-3.11",
                "image_id": str(_SAMPLE_IMAGE_ID),
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_image_client(mock_session)

        request = AliasImageRequest(
            image_id=_SAMPLE_IMAGE_ID,
            alias="python-3.11",
        )
        result = await client.alias(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/admin/images/alias" in str(call_args[0][1])
        call_kwargs = mock_session.request.call_args.kwargs
        body = call_kwargs["json"]
        assert body["image_id"] == str(_SAMPLE_IMAGE_ID)
        assert body["alias"] == "python-3.11"
        assert isinstance(result, AliasImageResponse)
        assert result.alias_id == _SAMPLE_ALIAS_ID
        assert result.alias == "python-3.11"
        assert result.image_id == _SAMPLE_IMAGE_ID


class TestDealiasImage:
    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "alias_id": str(_SAMPLE_ALIAS_ID),
                "alias": "python-3.11",
                "image_id": str(_SAMPLE_IMAGE_ID),
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_image_client(mock_session)

        request = DealiasImageRequest(alias="python-3.11")
        result = await client.dealias(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/admin/images/dealias" in str(call_args[0][1])
        call_kwargs = mock_session.request.call_args.kwargs
        body = call_kwargs["json"]
        assert body["alias"] == "python-3.11"
        assert isinstance(result, AliasImageResponse)
        assert result.alias_id == _SAMPLE_ALIAS_ID


class TestForgetImage:
    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "item": {**_SAMPLE_IMAGE_DATA, "status": "DELETED"},
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_image_client(mock_session)

        request = ForgetImageRequest(image_id=_SAMPLE_IMAGE_ID)
        result = await client.forget(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/admin/images/forget" in str(call_args[0][1])
        call_kwargs = mock_session.request.call_args.kwargs
        body = call_kwargs["json"]
        assert body["image_id"] == str(_SAMPLE_IMAGE_ID)
        assert isinstance(result, ForgetImageResponse)
        assert result.item.id == _SAMPLE_IMAGE_ID
        assert result.item.status == "DELETED"


class TestPurgeImage:
    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "item": {**_SAMPLE_IMAGE_DATA, "status": "DELETED"},
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_image_client(mock_session)

        request = PurgeImageRequest(image_id=_SAMPLE_IMAGE_ID)
        result = await client.purge(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/admin/images/purge" in str(call_args[0][1])
        call_kwargs = mock_session.request.call_args.kwargs
        body = call_kwargs["json"]
        assert body["image_id"] == str(_SAMPLE_IMAGE_ID)
        assert isinstance(result, PurgeImageResponse)
        assert result.item.id == _SAMPLE_IMAGE_ID
        assert result.item.status == "DELETED"

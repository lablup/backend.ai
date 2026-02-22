"""Unit tests for ObjectStorageClient (SDK v2)."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.object_storage import ObjectStorageClient
from ai.backend.common.dto.manager.object_storage import (
    GetPresignedDownloadURLReq,
    GetPresignedUploadURLReq,
    ObjectStorageAllBucketsResponse,
    ObjectStorageBucketsResponse,
    ObjectStorageListResponse,
)
from ai.backend.common.dto.manager.object_storage.response import (
    GetPresignedDownloadURLResponse,
    GetPresignedUploadURLResponse,
)

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_request_session(resp: AsyncMock) -> MagicMock:
    """Build a mock aiohttp session whose ``request()`` returns *resp*."""
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


def _make_client(mock_session: MagicMock) -> ObjectStorageClient:
    client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)
    return ObjectStorageClient(client)


def _last_request_call(mock_session: MagicMock) -> tuple[str, str, dict[str, Any] | None]:
    """Return (method, url, json_body) from the last ``session.request()`` call."""
    args, kwargs = mock_session.request.call_args
    return args[0], str(args[1]), kwargs.get("json")


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

_SAMPLE_STORAGE = {
    "id": str(uuid.uuid4()),
    "name": "my-s3",
    "host": "s3.example.com",
    "access_key": "AKIA...",
    "secret_key": "secret",
    "endpoint": "https://s3.example.com",
    "region": "us-east-1",
}


class TestListObjectStorages:
    @pytest.mark.asyncio
    async def test_list_empty(self) -> None:
        resp = _json_response({"storages": []})
        mock_session = _make_request_session(resp)
        domain = _make_client(mock_session)

        result = await domain.list()

        assert isinstance(result, ObjectStorageListResponse)
        assert result.storages == []
        method, url, body = _last_request_call(mock_session)
        assert method == "GET"
        assert "/object-storages/" in url
        assert body is None

    @pytest.mark.asyncio
    async def test_list_with_items(self) -> None:
        resp = _json_response({"storages": [_SAMPLE_STORAGE]})
        mock_session = _make_request_session(resp)
        domain = _make_client(mock_session)

        result = await domain.list()

        assert isinstance(result, ObjectStorageListResponse)
        assert len(result.storages) == 1
        assert result.storages[0].name == "my-s3"
        assert result.storages[0].region == "us-east-1"


class TestGetBuckets:
    @pytest.mark.asyncio
    async def test_get_all_buckets(self) -> None:
        storage_id = uuid.uuid4()
        resp = _json_response({"buckets_by_storage": {str(storage_id): ["bucket-a", "bucket-b"]}})
        mock_session = _make_request_session(resp)
        domain = _make_client(mock_session)

        result = await domain.get_all_buckets()

        assert isinstance(result, ObjectStorageAllBucketsResponse)
        assert storage_id in result.buckets_by_storage
        assert result.buckets_by_storage[storage_id] == ["bucket-a", "bucket-b"]
        method, url, body = _last_request_call(mock_session)
        assert method == "GET"
        assert "/object-storages/buckets" in url
        assert body is None

    @pytest.mark.asyncio
    async def test_get_buckets_for_storage(self) -> None:
        storage_id = "storage-123"
        resp = _json_response({"buckets": ["b1", "b2", "b3"]})
        mock_session = _make_request_session(resp)
        domain = _make_client(mock_session)

        result = await domain.get_buckets(storage_id)

        assert isinstance(result, ObjectStorageBucketsResponse)
        assert result.buckets == ["b1", "b2", "b3"]
        method, url, body = _last_request_call(mock_session)
        assert method == "GET"
        assert f"/object-storages/{storage_id}/buckets" in url
        assert body is None


class TestPresignedURLs:
    @pytest.mark.asyncio
    async def test_get_presigned_upload_url(self) -> None:
        rev_id = uuid.uuid4()
        resp = _json_response({"presigned_url": "https://s3/upload", "fields": "{}"})
        mock_session = _make_request_session(resp)
        domain = _make_client(mock_session)

        request = GetPresignedUploadURLReq(artifact_revision_id=rev_id, key="model.bin")
        result = await domain.get_presigned_upload_url(request)

        assert isinstance(result, GetPresignedUploadURLResponse)
        assert result.presigned_url == "https://s3/upload"
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert "/object-storages/presigned/upload" in url
        assert body is not None
        assert body["artifact_revision_id"] == str(rev_id)
        assert body["key"] == "model.bin"

    @pytest.mark.asyncio
    async def test_get_presigned_upload_url_with_options(self) -> None:
        rev_id = uuid.uuid4()
        resp = _json_response({"presigned_url": "https://s3/upload", "fields": "{}"})
        mock_session = _make_request_session(resp)
        domain = _make_client(mock_session)

        request = GetPresignedUploadURLReq(
            artifact_revision_id=rev_id,
            key="data.tar.gz",
            content_type="application/gzip",
            expiration=3600,
            min_size=1024,
            max_size=1073741824,
        )
        result = await domain.get_presigned_upload_url(request)

        assert isinstance(result, GetPresignedUploadURLResponse)
        method, url, body = _last_request_call(mock_session)
        assert body is not None
        assert body["content_type"] == "application/gzip"
        assert body["expiration"] == 3600

    @pytest.mark.asyncio
    async def test_get_presigned_download_url(self) -> None:
        rev_id = uuid.uuid4()
        resp = _json_response({"presigned_url": "https://s3/download"})
        mock_session = _make_request_session(resp)
        domain = _make_client(mock_session)

        request = GetPresignedDownloadURLReq(artifact_revision_id=rev_id, key="model.bin")
        result = await domain.get_presigned_download_url(request)

        assert isinstance(result, GetPresignedDownloadURLResponse)
        assert result.presigned_url == "https://s3/download"
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert "/object-storages/presigned/download" in url
        assert body is not None
        assert body["artifact_revision_id"] == str(rev_id)

    @pytest.mark.asyncio
    async def test_get_presigned_download_url_with_expiration(self) -> None:
        rev_id = uuid.uuid4()
        resp = _json_response({"presigned_url": "https://s3/download"})
        mock_session = _make_request_session(resp)
        domain = _make_client(mock_session)

        request = GetPresignedDownloadURLReq(
            artifact_revision_id=rev_id,
            key="weights.bin",
            expiration=7200,
        )
        result = await domain.get_presigned_download_url(request)

        assert isinstance(result, GetPresignedDownloadURLResponse)
        method, url, body = _last_request_call(mock_session)
        assert body is not None
        assert body["expiration"] == 7200

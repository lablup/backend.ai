import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.storage import StorageClient
from ai.backend.common.dto.manager.storage.request import (
    GetPresignedDownloadURLReq,
    GetPresignedUploadURLReq,
    VFSListFilesReq,
)
from ai.backend.common.dto.manager.storage.response import (
    GetPresignedDownloadURLResponse,
    GetPresignedUploadURLResponse,
    GetVFSStorageResponse,
    ListVFSStorageResponse,
    ObjectStorageAllBucketsResponse,
    ObjectStorageBucketsResponse,
    ObjectStorageListResponse,
)
from ai.backend.common.dto.storage.response import VFSListFilesResponse

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_request_session(resp: AsyncMock) -> MagicMock:
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _make_client(mock_session: MagicMock) -> BackendAIClient:
    return BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)


class TestStorageClientObjectStorage:
    @pytest.mark.asyncio
    async def test_list_object_storages(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"storages": []})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = StorageClient(client)

        result = await domain.list_object_storages()

        assert isinstance(result, ObjectStorageListResponse)
        assert result.storages == []
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/object-storages/" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_get_presigned_upload_url(self) -> None:
        rev_id = uuid.uuid4()
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={"presigned_url": "https://s3/upload", "fields": "{}"}
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = StorageClient(client)

        request = GetPresignedUploadURLReq(artifact_revision_id=rev_id, key="model.bin")
        result = await domain.get_presigned_upload_url(request)

        assert isinstance(result, GetPresignedUploadURLResponse)
        assert result.presigned_url == "https://s3/upload"
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/object-storages/presigned/upload" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_get_presigned_download_url(self) -> None:
        rev_id = uuid.uuid4()
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"presigned_url": "https://s3/download"})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = StorageClient(client)

        request = GetPresignedDownloadURLReq(artifact_revision_id=rev_id, key="model.bin")
        result = await domain.get_presigned_download_url(request)

        assert isinstance(result, GetPresignedDownloadURLResponse)
        assert result.presigned_url == "https://s3/download"
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/object-storages/presigned/download" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_get_all_buckets(self) -> None:
        storage_id = uuid.uuid4()
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={"buckets_by_storage": {str(storage_id): ["bucket-a", "bucket-b"]}}
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = StorageClient(client)

        result = await domain.get_all_buckets()

        assert isinstance(result, ObjectStorageAllBucketsResponse)
        assert storage_id in result.buckets_by_storage
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/object-storages/buckets" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_get_buckets(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"buckets": ["b1", "b2"]})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = StorageClient(client)

        result = await domain.get_buckets("storage-abc")

        assert isinstance(result, ObjectStorageBucketsResponse)
        assert result.buckets == ["b1", "b2"]
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        url = str(call_args[0][1])
        assert "/object-storages/storage-abc/buckets" in url


class TestStorageClientVFS:
    @pytest.mark.asyncio
    async def test_list_vfs_storages(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"storages": []})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = StorageClient(client)

        result = await domain.list_vfs_storages()

        assert isinstance(result, ListVFSStorageResponse)
        assert result.storages == []
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/vfs-storages/" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_get_vfs_storage(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={"storage": {"name": "my-vfs", "base_path": "/data", "host": "host1"}}
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = StorageClient(client)

        result = await domain.get_vfs_storage("my-vfs")

        assert isinstance(result, GetVFSStorageResponse)
        assert result.storage.name == "my-vfs"
        assert result.storage.base_path == "/data"
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/vfs-storages/my-vfs" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_get_vfs_storage_path_interpolation(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={"storage": {"name": "special-name", "base_path": "/mnt", "host": "h"}}
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = StorageClient(client)

        await domain.get_vfs_storage("special-name")

        url = str(mock_session.request.call_args[0][1])
        assert "special-name" in url
        assert "vfs-storages" in url

    @pytest.mark.asyncio
    async def test_list_vfs_files(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"files": []})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = StorageClient(client)

        request = VFSListFilesReq(directory="/models")
        result = await domain.list_vfs_files("my-storage", request)

        assert isinstance(result, VFSListFilesResponse)
        assert result.files == []
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/vfs-storages/my-storage/files" in str(call_args[0][1])
        assert call_args.kwargs["json"]["directory"] == "/models"

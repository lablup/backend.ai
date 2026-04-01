from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.storage.request import (
    GetPresignedDownloadURLReq,
    GetPresignedUploadURLReq,
    VFSListFilesReq,
)
from ai.backend.common.dto.manager.storage.response import (
    ListVFSStorageResponse,
    ObjectStorageAllBucketsResponse,
    ObjectStorageBucketsResponse,
    ObjectStorageListResponse,
)

# ── Object Storage ──────────────────────────────────────────────────


class TestListObjectStorages:
    async def test_admin_lists_object_storages(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.storage.list_object_storages()
        assert isinstance(result, ObjectStorageListResponse)
        assert isinstance(result.storages, list)

    async def test_user_lists_object_storages(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        result = await user_registry.storage.list_object_storages()
        assert isinstance(result, ObjectStorageListResponse)
        assert isinstance(result.storages, list)


class TestGetPresignedUploadURL:
    async def test_presigned_upload_url_with_invalid_revision(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(Exception):
            await admin_registry.storage.get_presigned_upload_url(
                GetPresignedUploadURLReq(
                    artifact_revision_id=uuid.uuid4(),
                    key="test-file.txt",
                ),
            )


class TestGetPresignedDownloadURL:
    async def test_presigned_download_url_with_invalid_revision(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(Exception):
            await admin_registry.storage.get_presigned_download_url(
                GetPresignedDownloadURLReq(
                    artifact_revision_id=uuid.uuid4(),
                    key="test-file.txt",
                ),
            )


class TestGetAllBuckets:
    async def test_admin_gets_all_buckets(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.storage.get_all_buckets()
        assert isinstance(result, ObjectStorageAllBucketsResponse)
        assert isinstance(result.buckets_by_storage, dict)


class TestGetBuckets:
    async def test_get_buckets_with_nonexistent_storage(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.storage.get_buckets(str(uuid.uuid4()))
        assert isinstance(result, ObjectStorageBucketsResponse)
        assert result.buckets == []


# ── VFS Storage ─────────────────────────────────────────────────────


class TestListVFSStorages:
    async def test_admin_lists_vfs_storages(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.storage.list_vfs_storages()
        assert isinstance(result, ListVFSStorageResponse)
        assert isinstance(result.storages, list)

    async def test_user_lists_vfs_storages(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        result = await user_registry.storage.list_vfs_storages()
        assert isinstance(result, ListVFSStorageResponse)
        assert isinstance(result.storages, list)


class TestGetVFSStorage:
    async def test_get_vfs_storage_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(Exception):
            await admin_registry.storage.get_vfs_storage("nonexistent-storage")


class TestListVFSFiles:
    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Storage proxy is unavailable in component test environment."
            " Even though the server handler reads JSON body via BodyParam"
            " (which works for GET), the VFS storage lookup fails because"
            " no storage proxy is configured."
        ),
    )
    async def test_list_vfs_files_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        await admin_registry.storage.list_vfs_files(
            "nonexistent-storage",
            VFSListFilesReq(directory="/"),
        )

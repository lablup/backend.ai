from __future__ import annotations

import uuid
from collections.abc import Callable, Coroutine
from typing import Any

import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.object_storage.request import (
    GetPresignedDownloadURLReq,
    GetPresignedUploadURLReq,
)
from ai.backend.common.dto.manager.object_storage.response import (
    ObjectStorageAllBucketsResponse,
    ObjectStorageBucketsResponse,
    ObjectStorageListResponse,
)

ObjectStorageFactory = Callable[..., Coroutine[Any, Any, dict[str, Any]]]
StorageNamespaceFactory = Callable[..., Coroutine[Any, Any, dict[str, Any]]]


class TestListObjectStorageFull:
    async def test_admin_lists_storages_with_data(
        self,
        admin_registry: BackendAIClientRegistry,
        object_storage_factory: ObjectStorageFactory,
    ) -> None:
        created = await object_storage_factory()
        result = await admin_registry.object_storage.list()
        assert isinstance(result, ObjectStorageListResponse)
        assert len(result.storages) >= 1
        names = [s.name for s in result.storages]
        assert created["name"] in names

    async def test_admin_lists_storages_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.object_storage.list()
        assert isinstance(result, ObjectStorageListResponse)
        assert result.storages == []

    async def test_user_lists_storages_same_as_admin(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        object_storage_factory: ObjectStorageFactory,
    ) -> None:
        await object_storage_factory()
        admin_result = await admin_registry.object_storage.list()
        user_result = await user_registry.object_storage.list()
        assert isinstance(admin_result, ObjectStorageListResponse)
        assert isinstance(user_result, ObjectStorageListResponse)
        admin_names = {s.name for s in admin_result.storages}
        user_names = {s.name for s in user_result.storages}
        assert admin_names == user_names


class TestGetBucketsFull:
    async def test_admin_gets_all_buckets_grouped_by_storage(
        self,
        admin_registry: BackendAIClientRegistry,
        object_storage_factory: ObjectStorageFactory,
        storage_namespace_factory: StorageNamespaceFactory,
    ) -> None:
        storage1 = await object_storage_factory()
        storage2 = await object_storage_factory()
        ns1 = await storage_namespace_factory(storage_id=storage1["id"])
        ns2 = await storage_namespace_factory(storage_id=storage2["id"])
        result = await admin_registry.object_storage.get_all_buckets()
        assert isinstance(result, ObjectStorageAllBucketsResponse)
        assert storage1["id"] in result.buckets_by_storage
        assert storage2["id"] in result.buckets_by_storage
        assert ns1["namespace"] in result.buckets_by_storage[storage1["id"]]
        assert ns2["namespace"] in result.buckets_by_storage[storage2["id"]]

    async def test_admin_gets_specific_storage_buckets_only(
        self,
        admin_registry: BackendAIClientRegistry,
        object_storage_factory: ObjectStorageFactory,
        storage_namespace_factory: StorageNamespaceFactory,
    ) -> None:
        storage1 = await object_storage_factory()
        storage2 = await object_storage_factory()
        ns1 = await storage_namespace_factory(storage_id=storage1["id"])
        ns2 = await storage_namespace_factory(storage_id=storage2["id"])
        result = await admin_registry.object_storage.get_buckets(str(storage1["id"]))
        assert isinstance(result, ObjectStorageBucketsResponse)
        assert ns1["namespace"] in result.buckets
        assert ns2["namespace"] not in result.buckets


class TestPresignedURLFull:
    async def test_upload_url_fails_without_reservoir_config(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        req = GetPresignedUploadURLReq(
            artifact_revision_id=uuid.uuid4(),
            key="test-file.txt",
        )
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_registry.object_storage.get_presigned_upload_url(req)
        assert exc_info.value.status == 500

    async def test_download_url_fails_without_reservoir_config(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        req = GetPresignedDownloadURLReq(
            artifact_revision_id=uuid.uuid4(),
            key="test-file.txt",
        )
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_registry.object_storage.get_presigned_download_url(req)
        assert exc_info.value.status == 500

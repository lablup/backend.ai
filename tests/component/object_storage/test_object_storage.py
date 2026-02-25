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


class TestListObjectStorages:
    @pytest.mark.asyncio
    async def test_admin_lists_empty_storages(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.object_storage.list()
        assert isinstance(result, ObjectStorageListResponse)
        assert result.storages == []

    @pytest.mark.asyncio
    async def test_admin_lists_storages(
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

    @pytest.mark.asyncio
    async def test_user_lists_storages(
        self,
        user_registry: BackendAIClientRegistry,
        object_storage_factory: ObjectStorageFactory,
    ) -> None:
        created = await object_storage_factory()
        result = await user_registry.object_storage.list()
        assert isinstance(result, ObjectStorageListResponse)
        names = [s.name for s in result.storages]
        assert created["name"] in names


class TestGetAllBuckets:
    @pytest.mark.asyncio
    async def test_admin_gets_all_buckets_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.object_storage.get_all_buckets()
        assert isinstance(result, ObjectStorageAllBucketsResponse)
        assert result.buckets_by_storage == {}

    @pytest.mark.asyncio
    async def test_admin_gets_all_buckets(
        self,
        admin_registry: BackendAIClientRegistry,
        object_storage_factory: ObjectStorageFactory,
        storage_namespace_factory: StorageNamespaceFactory,
    ) -> None:
        storage = await object_storage_factory()
        ns = await storage_namespace_factory(storage_id=storage["id"])
        result = await admin_registry.object_storage.get_all_buckets()
        assert isinstance(result, ObjectStorageAllBucketsResponse)
        assert storage["id"] in result.buckets_by_storage
        assert ns["namespace"] in result.buckets_by_storage[storage["id"]]


class TestGetBuckets:
    @pytest.mark.asyncio
    async def test_admin_gets_buckets_for_storage(
        self,
        admin_registry: BackendAIClientRegistry,
        object_storage_factory: ObjectStorageFactory,
        storage_namespace_factory: StorageNamespaceFactory,
    ) -> None:
        storage = await object_storage_factory()
        ns = await storage_namespace_factory(storage_id=storage["id"])
        result = await admin_registry.object_storage.get_buckets(str(storage["id"]))
        assert isinstance(result, ObjectStorageBucketsResponse)
        assert ns["namespace"] in result.buckets

    @pytest.mark.asyncio
    async def test_admin_gets_buckets_empty_storage(
        self,
        admin_registry: BackendAIClientRegistry,
        object_storage_factory: ObjectStorageFactory,
    ) -> None:
        storage = await object_storage_factory()
        result = await admin_registry.object_storage.get_buckets(str(storage["id"]))
        assert isinstance(result, ObjectStorageBucketsResponse)
        assert result.buckets == []


class TestPresignedUploadURL:
    @pytest.mark.asyncio
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


class TestPresignedDownloadURL:
    @pytest.mark.asyncio
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

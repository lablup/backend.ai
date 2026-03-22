from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.object_storage.response import (
    ObjectStorageAllBucketsResponse,
    ObjectStorageBucketsResponse,
    ObjectStorageListResponse,
)

ObjectStorageFactory = Callable[..., Coroutine[Any, Any, dict[str, Any]]]
StorageNamespaceFactory = Callable[..., Coroutine[Any, Any, dict[str, Any]]]


class TestListObjectStorageFull:
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

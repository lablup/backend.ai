from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.object_storage.response import (
    ObjectStorageAllBucketsResponse,
    ObjectStorageBucketsResponse,
)

ObjectStorageFactory = Callable[..., Coroutine[Any, Any, dict[str, Any]]]
StorageNamespaceFactory = Callable[..., Coroutine[Any, Any, dict[str, Any]]]


class TestStorageNamespaceRegisterUnregister:
    """Storage namespace register/unregister integration test via bucket APIs."""

    async def test_register_namespace_via_factory_and_list(
        self,
        admin_registry: BackendAIClientRegistry,
        object_storage_factory: ObjectStorageFactory,
        storage_namespace_factory: StorageNamespaceFactory,
    ) -> None:
        """Register a namespace (bucket) and verify it appears in get_buckets."""
        storage = await object_storage_factory()
        ns = await storage_namespace_factory(storage_id=storage["id"])

        result = await admin_registry.object_storage.get_buckets(str(storage["id"]))
        assert isinstance(result, ObjectStorageBucketsResponse)
        assert ns["namespace"] in result.buckets

    async def test_namespace_appears_in_all_buckets(
        self,
        admin_registry: BackendAIClientRegistry,
        object_storage_factory: ObjectStorageFactory,
        storage_namespace_factory: StorageNamespaceFactory,
    ) -> None:
        """Registered namespaces appear in the all-buckets response grouped by storage."""
        storage = await object_storage_factory()
        ns1 = await storage_namespace_factory(storage_id=storage["id"])
        ns2 = await storage_namespace_factory(storage_id=storage["id"])

        result = await admin_registry.object_storage.get_all_buckets()
        assert isinstance(result, ObjectStorageAllBucketsResponse)
        assert storage["id"] in result.buckets_by_storage
        buckets = result.buckets_by_storage[storage["id"]]
        assert ns1["namespace"] in buckets
        assert ns2["namespace"] in buckets

    async def test_empty_storage_has_no_buckets(
        self,
        admin_registry: BackendAIClientRegistry,
        object_storage_factory: ObjectStorageFactory,
    ) -> None:
        """A storage with no registered namespaces returns empty bucket list."""
        storage = await object_storage_factory()
        result = await admin_registry.object_storage.get_buckets(str(storage["id"]))
        assert isinstance(result, ObjectStorageBucketsResponse)
        assert result.buckets == []

    async def test_multiple_storages_grouped_correctly(
        self,
        admin_registry: BackendAIClientRegistry,
        object_storage_factory: ObjectStorageFactory,
        storage_namespace_factory: StorageNamespaceFactory,
    ) -> None:
        """Namespaces from different storages are grouped correctly in all-buckets."""
        storage1 = await object_storage_factory()
        storage2 = await object_storage_factory()
        ns1 = await storage_namespace_factory(storage_id=storage1["id"])
        ns2 = await storage_namespace_factory(storage_id=storage2["id"])

        result = await admin_registry.object_storage.get_all_buckets()
        assert isinstance(result, ObjectStorageAllBucketsResponse)

        assert storage1["id"] in result.buckets_by_storage
        assert ns1["namespace"] in result.buckets_by_storage[storage1["id"]]

        assert storage2["id"] in result.buckets_by_storage
        assert ns2["namespace"] in result.buckets_by_storage[storage2["id"]]

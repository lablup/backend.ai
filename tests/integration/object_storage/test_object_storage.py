from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.object_storage.response import (
    ObjectStorageAllBucketsResponse,
    ObjectStorageBucketsResponse,
    ObjectStorageListResponse,
)

ObjectStorageFactory = Callable[..., Coroutine[Any, Any, dict[str, Any]]]
StorageNamespaceFactory = Callable[..., Coroutine[Any, Any, dict[str, Any]]]


@pytest.mark.integration
class TestObjectStorageLifecycle:
    @pytest.mark.asyncio
    async def test_list_seed_and_query_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        object_storage_factory: ObjectStorageFactory,
        storage_namespace_factory: StorageNamespaceFactory,
    ) -> None:
        """list (empty) -> seed data -> list (has data) -> get_all_buckets -> get_buckets."""
        # 1. List: initially empty
        empty_result = await admin_registry.object_storage.list()
        assert isinstance(empty_result, ObjectStorageListResponse)
        assert empty_result.storages == []

        # 2. Seed an object storage and namespace
        storage = await object_storage_factory()
        ns = await storage_namespace_factory(storage_id=storage["id"])

        # 3. List: seeded storage appears
        list_result = await admin_registry.object_storage.list()
        assert isinstance(list_result, ObjectStorageListResponse)
        assert len(list_result.storages) >= 1
        names = [s.name for s in list_result.storages]
        assert storage["name"] in names

        # 4. Get all buckets: mapping includes the seeded storage
        all_buckets = await admin_registry.object_storage.get_all_buckets()
        assert isinstance(all_buckets, ObjectStorageAllBucketsResponse)
        assert storage["id"] in all_buckets.buckets_by_storage
        assert ns["namespace"] in all_buckets.buckets_by_storage[storage["id"]]

        # 5. Get buckets for the specific storage
        buckets = await admin_registry.object_storage.get_buckets(str(storage["id"]))
        assert isinstance(buckets, ObjectStorageBucketsResponse)
        assert ns["namespace"] in buckets.buckets

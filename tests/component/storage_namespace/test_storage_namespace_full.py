"""Component tests for storage namespace lifecycle via processors.

Tests register, unregister, per-storage listing, and all-namespaces grouped
query through the StorageNamespaceProcessors layer with a real database.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.storage_namespace.creators import StorageNamespaceCreatorSpec
from ai.backend.manager.services.storage_namespace.actions.get_all import GetAllNamespacesAction
from ai.backend.manager.services.storage_namespace.actions.get_multi import GetNamespacesAction
from ai.backend.manager.services.storage_namespace.actions.register import RegisterNamespaceAction
from ai.backend.manager.services.storage_namespace.actions.unregister import (
    UnregisterNamespaceAction,
)
from ai.backend.manager.services.storage_namespace.processors import StorageNamespaceProcessors

ObjectStorageFactory = Callable[..., Coroutine[Any, Any, dict[str, Any]]]
StorageNamespaceFactory = Callable[..., Coroutine[Any, Any, dict[str, Any]]]


class TestStorageNamespace:
    """Register, unregister, per-storage listing, and grouped query tests."""

    async def test_register_namespace(
        self,
        storage_namespace_processors: StorageNamespaceProcessors,
        object_storage_factory: ObjectStorageFactory,
    ) -> None:
        """Register namespace for a storage returns namespace data."""
        storage = await object_storage_factory()
        action = RegisterNamespaceAction(
            creator=Creator(
                spec=StorageNamespaceCreatorSpec(
                    storage_id=storage["id"],
                    bucket="register-test-ns",
                ),
            ),
        )
        result = await storage_namespace_processors.register.wait_for_complete(action)
        assert result.result.namespace == "register-test-ns"
        assert result.result.storage_id == storage["id"]
        assert result.result.id is not None
        assert result.storage_id == storage["id"]

    async def test_unregister_namespace(
        self,
        storage_namespace_processors: StorageNamespaceProcessors,
        object_storage_factory: ObjectStorageFactory,
        storage_namespace_factory: StorageNamespaceFactory,
    ) -> None:
        """Unregister namespace removes it from listings."""
        storage = await object_storage_factory()
        ns = await storage_namespace_factory(storage_id=storage["id"], namespace="to-unregister")

        # Verify it exists first
        get_action = GetNamespacesAction(storage_id=storage["id"])
        before = await storage_namespace_processors.get_namespaces.wait_for_complete(get_action)
        ns_names = [n.namespace for n in before.result]
        assert "to-unregister" in ns_names

        # Unregister
        unregister_action = UnregisterNamespaceAction(
            storage_id=storage["id"],
            namespace="to-unregister",
        )
        unregister_result = await storage_namespace_processors.unregister.wait_for_complete(
            unregister_action
        )
        assert unregister_result.storage_id == ns["storage_id"]

        # Verify removed
        after = await storage_namespace_processors.get_namespaces.wait_for_complete(get_action)
        ns_names_after = [n.namespace for n in after.result]
        assert "to-unregister" not in ns_names_after

    async def test_list_namespaces_per_storage(
        self,
        storage_namespace_processors: StorageNamespaceProcessors,
        object_storage_factory: ObjectStorageFactory,
        storage_namespace_factory: StorageNamespaceFactory,
    ) -> None:
        """List namespaces per storage returns only that storage's namespaces."""
        storage_a = await object_storage_factory()
        storage_b = await object_storage_factory()
        await storage_namespace_factory(storage_id=storage_a["id"], namespace="ns-alpha")
        await storage_namespace_factory(storage_id=storage_a["id"], namespace="ns-beta")
        await storage_namespace_factory(storage_id=storage_b["id"], namespace="ns-gamma")

        # List storage_a namespaces
        action_a = GetNamespacesAction(storage_id=storage_a["id"])
        result_a = await storage_namespace_processors.get_namespaces.wait_for_complete(action_a)
        names_a = [n.namespace for n in result_a.result]
        assert "ns-alpha" in names_a
        assert "ns-beta" in names_a
        assert "ns-gamma" not in names_a

        # List storage_b namespaces
        action_b = GetNamespacesAction(storage_id=storage_b["id"])
        result_b = await storage_namespace_processors.get_namespaces.wait_for_complete(action_b)
        names_b = [n.namespace for n in result_b.result]
        assert "ns-gamma" in names_b
        assert "ns-alpha" not in names_b
        assert "ns-beta" not in names_b

    async def test_all_namespaces_grouped_query(
        self,
        storage_namespace_processors: StorageNamespaceProcessors,
        object_storage_factory: ObjectStorageFactory,
        storage_namespace_factory: StorageNamespaceFactory,
    ) -> None:
        """All-namespaces grouped query returns namespaces grouped by storage."""
        storage_x = await object_storage_factory()
        storage_y = await object_storage_factory()
        await storage_namespace_factory(storage_id=storage_x["id"], namespace="grouped-x1")
        await storage_namespace_factory(storage_id=storage_x["id"], namespace="grouped-x2")
        await storage_namespace_factory(storage_id=storage_y["id"], namespace="grouped-y1")

        action = GetAllNamespacesAction()
        result = await storage_namespace_processors.get_all_namespaces.wait_for_complete(action)

        assert storage_x["id"] in result.result
        assert "grouped-x1" in result.result[storage_x["id"]]
        assert "grouped-x2" in result.result[storage_x["id"]]

        assert storage_y["id"] in result.result
        assert "grouped-y1" in result.result[storage_y["id"]]

    async def test_register_and_unregister_lifecycle(
        self,
        storage_namespace_processors: StorageNamespaceProcessors,
        object_storage_factory: ObjectStorageFactory,
    ) -> None:
        """Full lifecycle: register -> verify listed -> unregister -> verify gone."""
        storage = await object_storage_factory()

        # Register via processor
        register_result = await storage_namespace_processors.register.wait_for_complete(
            RegisterNamespaceAction(
                creator=Creator(
                    spec=StorageNamespaceCreatorSpec(
                        storage_id=storage["id"],
                        bucket="lifecycle-ns",
                    ),
                ),
            )
        )
        assert register_result.result.namespace == "lifecycle-ns"

        # Verify listed
        list_result = await storage_namespace_processors.get_namespaces.wait_for_complete(
            GetNamespacesAction(storage_id=storage["id"])
        )
        assert "lifecycle-ns" in [n.namespace for n in list_result.result]

        # Verify in grouped query
        all_result = await storage_namespace_processors.get_all_namespaces.wait_for_complete(
            GetAllNamespacesAction()
        )
        assert "lifecycle-ns" in all_result.result[storage["id"]]

        # Unregister
        await storage_namespace_processors.unregister.wait_for_complete(
            UnregisterNamespaceAction(storage_id=storage["id"], namespace="lifecycle-ns")
        )

        # Verify gone from per-storage listing
        after = await storage_namespace_processors.get_namespaces.wait_for_complete(
            GetNamespacesAction(storage_id=storage["id"])
        )
        assert "lifecycle-ns" not in [n.namespace for n in after.result]

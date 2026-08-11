"""
Tests for StorageNamespaceService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.identifier.storage_namespace import StorageNamespaceID
from ai.backend.manager.data.storage_namespace.types import (
    StorageNamespaceData,
)
from ai.backend.manager.repositories.storage_namespace.repository import (
    StorageNamespaceRepository,
)
from ai.backend.manager.services.storage_namespace.actions.get_all import (
    GetAllNamespacesAction,
)
from ai.backend.manager.services.storage_namespace.actions.unregister import (
    UnregisterNamespaceAction,
)
from ai.backend.manager.services.storage_namespace.service import StorageNamespaceService


class TestStorageNamespaceService:
    """Test cases for StorageNamespaceService"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create mocked StorageNamespaceRepository"""
        return MagicMock(spec=StorageNamespaceRepository)

    @pytest.fixture
    def storage_namespace_service(
        self,
        mock_repository: MagicMock,
    ) -> StorageNamespaceService:
        """Create StorageNamespaceService instance with mocked repository"""
        return StorageNamespaceService(storage_namespace_repository=mock_repository)

    @pytest.fixture
    def sample_storage_namespace_data(self) -> StorageNamespaceData:
        """Create sample storage namespace data"""
        return StorageNamespaceData(
            id=StorageNamespaceID(uuid4()),
            storage_id=uuid4(),
            namespace="test-namespace",
        )

    # =========================================================================
    # Tests - Register
    # =========================================================================

    async def test_unregister_namespace_returns_storage_id(
        self,
        storage_namespace_service: StorageNamespaceService,
        mock_repository: MagicMock,
    ) -> None:
        """Test unregistering a namespace returns the storage_id"""
        storage_id = uuid4()
        namespace = "test-namespace"
        mock_repository.unregister = AsyncMock(return_value=storage_id)

        action = UnregisterNamespaceAction(storage_id=storage_id, namespace=namespace)
        result = await storage_namespace_service.unregister(action)

        assert result.storage_id == storage_id
        mock_repository.unregister.assert_called_once_with(storage_id, namespace)

    async def test_unregister_namespace_nonexistent_raises_error(
        self,
        storage_namespace_service: StorageNamespaceService,
        mock_repository: MagicMock,
    ) -> None:
        """Test unregistering a non-existent namespace raises an error"""
        storage_id = uuid4()
        mock_repository.unregister = AsyncMock(side_effect=Exception("Namespace not found"))

        action = UnregisterNamespaceAction(storage_id=storage_id, namespace="nonexistent")
        with pytest.raises(Exception, match="Namespace not found"):
            await storage_namespace_service.unregister(action)

    # =========================================================================
    # Tests - GetNamespaces
    # =========================================================================

    async def test_get_all_namespaces_returns_grouped_dict(
        self,
        storage_namespace_service: StorageNamespaceService,
        mock_repository: MagicMock,
    ) -> None:
        """Test getting all namespaces returns storage UUID -> namespace list dict"""
        storage_id_1 = uuid4()
        storage_id_2 = uuid4()
        expected = {
            storage_id_1: ["ns-a", "ns-b"],
            storage_id_2: ["ns-c"],
        }
        mock_repository.get_all_namespaces_by_storage = AsyncMock(return_value=expected)

        action = GetAllNamespacesAction()
        result = await storage_namespace_service.get_all_namespaces(action)

        assert result.result == expected
        assert len(result.result[storage_id_1]) == 2
        assert len(result.result[storage_id_2]) == 1
        mock_repository.get_all_namespaces_by_storage.assert_called_once()

    async def test_get_all_namespaces_multiple_storages_grouped_correctly(
        self,
        storage_namespace_service: StorageNamespaceService,
        mock_repository: MagicMock,
    ) -> None:
        """Test multiple storages are grouped correctly in the result"""
        storage_id_1 = uuid4()
        storage_id_2 = uuid4()
        storage_id_3 = uuid4()
        expected = {
            storage_id_1: ["alpha"],
            storage_id_2: ["beta", "gamma"],
            storage_id_3: ["delta", "epsilon", "zeta"],
        }
        mock_repository.get_all_namespaces_by_storage = AsyncMock(return_value=expected)

        action = GetAllNamespacesAction()
        result = await storage_namespace_service.get_all_namespaces(action)

        assert set(result.result.keys()) == {storage_id_1, storage_id_2, storage_id_3}
        assert result.result[storage_id_1] == ["alpha"]
        assert result.result[storage_id_2] == ["beta", "gamma"]
        assert result.result[storage_id_3] == ["delta", "epsilon", "zeta"]

    async def test_get_all_namespaces_empty_returns_empty_dict(
        self,
        storage_namespace_service: StorageNamespaceService,
        mock_repository: MagicMock,
    ) -> None:
        """Test getting all namespaces when no storages returns empty dict"""
        mock_repository.get_all_namespaces_by_storage = AsyncMock(return_value={})

        action = GetAllNamespacesAction()
        result = await storage_namespace_service.get_all_namespaces(action)

        assert result.result == {}
        mock_repository.get_all_namespaces_by_storage.assert_called_once()

    # =========================================================================
    # Tests - Search
    # =========================================================================

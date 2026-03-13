"""
Tests for StorageNamespaceService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.manager.data.storage_namespace.types import (
    StorageNamespaceData,
    StorageNamespaceListResult,
)
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.storage_namespace.repository import (
    StorageNamespaceRepository,
)
from ai.backend.manager.services.storage_namespace.actions.get_all import (
    GetAllNamespacesAction,
)
from ai.backend.manager.services.storage_namespace.actions.get_multi import (
    GetNamespacesAction,
)
from ai.backend.manager.services.storage_namespace.actions.register import (
    RegisterNamespaceAction,
)
from ai.backend.manager.services.storage_namespace.actions.search import (
    SearchStorageNamespacesAction,
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
            id=uuid4(),
            storage_id=uuid4(),
            namespace="test-namespace",
        )

    # =========================================================================
    # Tests - Register
    # =========================================================================

    async def test_register_namespace_returns_storage_namespace_data(
        self,
        storage_namespace_service: StorageNamespaceService,
        mock_repository: MagicMock,
        sample_storage_namespace_data: StorageNamespaceData,
    ) -> None:
        """Test registering a namespace returns StorageNamespaceData with storage_id"""
        mock_creator = MagicMock()
        mock_repository.register = AsyncMock(return_value=sample_storage_namespace_data)

        action = RegisterNamespaceAction(creator=mock_creator)
        result = await storage_namespace_service.register(action)

        assert result.result == sample_storage_namespace_data
        assert result.storage_id == sample_storage_namespace_data.storage_id
        mock_repository.register.assert_called_once_with(mock_creator)

    async def test_register_namespace_duplicate_raises_error(
        self,
        storage_namespace_service: StorageNamespaceService,
        mock_repository: MagicMock,
    ) -> None:
        """Test registering a duplicate namespace raises an error"""
        mock_creator = MagicMock()
        mock_repository.register = AsyncMock(
            side_effect=Exception("Duplicate namespace registration")
        )

        action = RegisterNamespaceAction(creator=mock_creator)
        with pytest.raises(Exception, match="Duplicate namespace registration"):
            await storage_namespace_service.register(action)

    # =========================================================================
    # Tests - Unregister
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

    async def test_get_namespaces_returns_list(
        self,
        storage_namespace_service: StorageNamespaceService,
        mock_repository: MagicMock,
        sample_storage_namespace_data: StorageNamespaceData,
    ) -> None:
        """Test getting namespaces for a storage_id returns namespace list"""
        storage_id = sample_storage_namespace_data.storage_id
        ns_data_2 = StorageNamespaceData(
            id=uuid4(), storage_id=storage_id, namespace="second-namespace"
        )
        mock_repository.get_namespaces = AsyncMock(
            return_value=[sample_storage_namespace_data, ns_data_2]
        )

        action = GetNamespacesAction(storage_id=storage_id)
        result = await storage_namespace_service.get_namespaces(action)

        assert len(result.result) == 2
        assert result.result[0] == sample_storage_namespace_data
        assert result.result[1] == ns_data_2
        mock_repository.get_namespaces.assert_called_once_with(storage_id)

    async def test_get_namespaces_empty_returns_empty_list(
        self,
        storage_namespace_service: StorageNamespaceService,
        mock_repository: MagicMock,
    ) -> None:
        """Test getting namespaces when no registrations returns empty list"""
        storage_id = uuid4()
        mock_repository.get_namespaces = AsyncMock(return_value=[])

        action = GetNamespacesAction(storage_id=storage_id)
        result = await storage_namespace_service.get_namespaces(action)

        assert result.result == []
        mock_repository.get_namespaces.assert_called_once_with(storage_id)

    # =========================================================================
    # Tests - GetAllNamespaces
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

    async def test_search_storage_namespaces(
        self,
        storage_namespace_service: StorageNamespaceService,
        mock_repository: MagicMock,
        sample_storage_namespace_data: StorageNamespaceData,
    ) -> None:
        """Test searching storage namespaces with querier"""
        mock_repository.search = AsyncMock(
            return_value=StorageNamespaceListResult(
                items=[sample_storage_namespace_data],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchStorageNamespacesAction(querier=querier)
        result = await storage_namespace_service.search(action)

        assert result.namespaces == [sample_storage_namespace_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_repository.search.assert_called_once_with(querier)

    async def test_search_storage_namespaces_empty_result(
        self,
        storage_namespace_service: StorageNamespaceService,
        mock_repository: MagicMock,
    ) -> None:
        """Test searching storage namespaces when no results are found"""
        mock_repository.search = AsyncMock(
            return_value=StorageNamespaceListResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchStorageNamespacesAction(querier=querier)
        result = await storage_namespace_service.search(action)

        assert result.namespaces == []
        assert result.total_count == 0

    async def test_search_storage_namespaces_with_pagination(
        self,
        storage_namespace_service: StorageNamespaceService,
        mock_repository: MagicMock,
        sample_storage_namespace_data: StorageNamespaceData,
    ) -> None:
        """Test searching storage namespaces with pagination"""
        mock_repository.search = AsyncMock(
            return_value=StorageNamespaceListResult(
                items=[sample_storage_namespace_data],
                total_count=25,
                has_next_page=True,
                has_previous_page=True,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )
        action = SearchStorageNamespacesAction(querier=querier)
        result = await storage_namespace_service.search(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True

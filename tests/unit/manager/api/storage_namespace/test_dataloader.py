"""Tests for storage_namespace GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.api.gql.data_loader.storage_namespace.loader import (
    load_storage_namespaces_by_ids,
)
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData


class TestLoadStorageNamespacesByIds:
    """Tests for load_storage_namespaces_by_ids function."""

    @staticmethod
    def create_mock_namespace(namespace_id: uuid.UUID) -> MagicMock:
        return MagicMock(spec=StorageNamespaceData, id=namespace_id)

    @staticmethod
    def create_mock_processor(namespaces: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.namespaces = namespaces
        mock_processor.search_storage_namespaces.wait_for_complete = AsyncMock(
            return_value=mock_action_result
        )
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_storage_namespaces_by_ids(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search_storage_namespaces.wait_for_complete.assert_not_called()

    async def test_returns_namespaces_in_request_order(self) -> None:
        # Given
        id1, id2, id3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        namespace1 = self.create_mock_namespace(id1)
        namespace2 = self.create_mock_namespace(id2)
        namespace3 = self.create_mock_namespace(id3)
        mock_processor = self.create_mock_processor(
            [namespace3, namespace1, namespace2]  # DB returns in different order
        )

        # When
        result = await load_storage_namespaces_by_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [namespace1, namespace2, namespace3]

    async def test_returns_none_for_missing_ids(self) -> None:
        # Given
        existing_id = uuid.uuid4()
        missing_id = uuid.uuid4()
        existing_namespace = self.create_mock_namespace(existing_id)
        mock_processor = self.create_mock_processor([existing_namespace])

        # When
        result = await load_storage_namespaces_by_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [existing_namespace, None]

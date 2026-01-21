"""Tests for object storage GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.api.gql.data_loader.object_storage.loader import (
    load_object_storages_by_ids,
)
from ai.backend.manager.data.object_storage.types import ObjectStorageData


class TestLoadObjectStoragesByIds:
    """Tests for load_object_storages_by_ids function."""

    @staticmethod
    def create_mock_storage(storage_id: uuid.UUID) -> MagicMock:
        mock = MagicMock(spec=ObjectStorageData)
        mock.id = storage_id
        return mock

    @staticmethod
    def create_mock_processor(storages: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.storages = storages
        mock_processor.search_object_storages.wait_for_complete = AsyncMock(
            return_value=mock_action_result
        )
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_object_storages_by_ids(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search_object_storages.wait_for_complete.assert_not_called()

    async def test_returns_storages_in_request_order(self) -> None:
        # Given
        id1, id2, id3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        storage1 = self.create_mock_storage(id1)
        storage2 = self.create_mock_storage(id2)
        storage3 = self.create_mock_storage(id3)
        mock_processor = self.create_mock_processor(
            [storage3, storage1, storage2]  # DB returns in different order
        )

        # When
        result = await load_object_storages_by_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [storage1, storage2, storage3]

    async def test_returns_none_for_missing_ids(self) -> None:
        # Given
        existing_id = uuid.uuid4()
        missing_id = uuid.uuid4()
        existing_storage = self.create_mock_storage(existing_id)
        mock_processor = self.create_mock_processor([existing_storage])

        # When
        result = await load_object_storages_by_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [existing_storage, None]

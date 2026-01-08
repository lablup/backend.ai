"""Tests for artifact registry GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.api.gql.data_loader.artifact_registry.loader import (
    load_artifact_registries_by_ids,
)
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData


class TestLoadArtifactRegistriesByIds:
    """Tests for load_artifact_registries_by_ids function."""

    @staticmethod
    def create_mock_registry(registry_id: uuid.UUID) -> MagicMock:
        return MagicMock(spec=ArtifactRegistryData, id=registry_id)

    @staticmethod
    def create_mock_processor(registries: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.registries = registries
        mock_processor.search_artifact_registries.wait_for_complete = AsyncMock(
            return_value=mock_action_result
        )
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_artifact_registries_by_ids(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search_artifact_registries.wait_for_complete.assert_not_called()

    async def test_returns_registries_in_request_order(self) -> None:
        # Given
        id1, id2, id3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        registry1 = self.create_mock_registry(id1)
        registry2 = self.create_mock_registry(id2)
        registry3 = self.create_mock_registry(id3)
        mock_processor = self.create_mock_processor(
            [registry3, registry1, registry2]  # DB returns in different order
        )

        # When
        result = await load_artifact_registries_by_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [registry1, registry2, registry3]

    async def test_returns_none_for_missing_ids(self) -> None:
        # Given
        existing_id = uuid.uuid4()
        missing_id = uuid.uuid4()
        existing_registry = self.create_mock_registry(existing_id)
        mock_processor = self.create_mock_processor([existing_registry])

        # When
        result = await load_artifact_registries_by_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [existing_registry, None]

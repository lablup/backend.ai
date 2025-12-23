"""Tests for artifact GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.api.gql.data_loader.artifact.loader import load_artifacts_by_ids
from ai.backend.manager.data.artifact.types import ArtifactData


class TestLoadArtifactsByIds:
    """Tests for load_artifacts_by_ids function."""

    @staticmethod
    def create_mock_artifact(artifact_id: uuid.UUID) -> MagicMock:
        return MagicMock(spec=ArtifactData, id=artifact_id)

    @staticmethod
    def create_mock_processor(artifacts: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.data = artifacts
        mock_processor.search_artifacts.wait_for_complete = AsyncMock(
            return_value=mock_action_result
        )
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_artifacts_by_ids(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search_artifacts.wait_for_complete.assert_not_called()

    async def test_returns_artifacts_in_request_order(self) -> None:
        # Given
        id1, id2, id3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        artifact1 = self.create_mock_artifact(id1)
        artifact2 = self.create_mock_artifact(id2)
        artifact3 = self.create_mock_artifact(id3)
        mock_processor = self.create_mock_processor(
            [artifact3, artifact1, artifact2]  # DB returns in different order
        )

        # When
        result = await load_artifacts_by_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [artifact1, artifact2, artifact3]

    async def test_returns_none_for_missing_ids(self) -> None:
        # Given
        existing_id = uuid.uuid4()
        missing_id = uuid.uuid4()
        existing_artifact = self.create_mock_artifact(existing_id)
        mock_processor = self.create_mock_processor([existing_artifact])

        # When
        result = await load_artifacts_by_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [existing_artifact, None]

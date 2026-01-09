"""Tests for artifact revision GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.api.gql.data_loader.artifact_revision.loader import (
    load_artifact_revisions_by_ids,
)
from ai.backend.manager.data.artifact.types import ArtifactRevisionData


class TestLoadArtifactRevisionsByIds:
    """Tests for load_artifact_revisions_by_ids function."""

    @staticmethod
    def create_mock_revision(revision_id: uuid.UUID) -> MagicMock:
        return MagicMock(spec=ArtifactRevisionData, id=revision_id)

    @staticmethod
    def create_mock_processor(revisions: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.data = revisions
        mock_processor.search_revision.wait_for_complete = AsyncMock(
            return_value=mock_action_result
        )
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_artifact_revisions_by_ids(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search_revision.wait_for_complete.assert_not_called()

    async def test_returns_revisions_in_request_order(self) -> None:
        # Given
        id1, id2, id3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        revision1 = self.create_mock_revision(id1)
        revision2 = self.create_mock_revision(id2)
        revision3 = self.create_mock_revision(id3)
        mock_processor = self.create_mock_processor(
            [revision3, revision1, revision2]  # DB returns in different order
        )

        # When
        result = await load_artifact_revisions_by_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [revision1, revision2, revision3]

    async def test_returns_none_for_missing_ids(self) -> None:
        # Given
        existing_id = uuid.uuid4()
        missing_id = uuid.uuid4()
        existing_revision = self.create_mock_revision(existing_id)
        mock_processor = self.create_mock_processor([existing_revision])

        # When
        result = await load_artifact_revisions_by_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [existing_revision, None]

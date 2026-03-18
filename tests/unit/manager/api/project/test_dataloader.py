"""Tests for project GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.api.gql.data_loader.project.loader import load_projects_by_ids
from ai.backend.manager.data.group.types import GroupData


class TestLoadProjectsByIds:
    """Tests for load_projects_by_ids function."""

    @staticmethod
    def create_mock_project(project_id: uuid.UUID) -> MagicMock:
        mock = MagicMock(spec=GroupData)
        mock.id = project_id
        return mock

    @staticmethod
    def create_mock_processor(projects: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.items = projects
        mock_processor.search_projects.wait_for_complete = AsyncMock(
            return_value=mock_action_result
        )
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_projects_by_ids(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search_projects.wait_for_complete.assert_not_called()

    async def test_returns_projects_in_request_order(self) -> None:
        # Given
        id1, id2, id3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        project1 = self.create_mock_project(id1)
        project2 = self.create_mock_project(id2)
        project3 = self.create_mock_project(id3)
        mock_processor = self.create_mock_processor(
            [project3, project1, project2]  # DB returns in different order
        )

        # When
        result = await load_projects_by_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [project1, project2, project3]

    async def test_returns_none_for_missing_ids(self) -> None:
        # Given
        existing_id = uuid.uuid4()
        missing_id = uuid.uuid4()
        existing_project = self.create_mock_project(existing_id)
        mock_processor = self.create_mock_processor([existing_project])

        # When
        result = await load_projects_by_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [existing_project, None]

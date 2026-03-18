"""Tests for user GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.api.gql.data_loader.user.loader import load_users_by_ids
from ai.backend.manager.data.user.types import UserData


class TestLoadUsersByIds:
    """Tests for load_users_by_ids function."""

    @staticmethod
    def create_mock_user(user_uuid: uuid.UUID) -> MagicMock:
        mock = MagicMock(spec=UserData)
        mock.uuid = user_uuid
        return mock

    @staticmethod
    def create_mock_processor(users: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.users = users
        mock_processor.search_users.wait_for_complete = AsyncMock(return_value=mock_action_result)
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_users_by_ids(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search_users.wait_for_complete.assert_not_called()

    async def test_returns_users_in_request_order(self) -> None:
        # Given
        id1, id2, id3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        user1 = self.create_mock_user(id1)
        user2 = self.create_mock_user(id2)
        user3 = self.create_mock_user(id3)
        mock_processor = self.create_mock_processor(
            [user3, user1, user2]  # DB returns in different order
        )

        # When
        result = await load_users_by_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [user1, user2, user3]

    async def test_returns_none_for_missing_ids(self) -> None:
        # Given
        existing_id = uuid.uuid4()
        missing_id = uuid.uuid4()
        existing_user = self.create_mock_user(existing_id)
        mock_processor = self.create_mock_processor([existing_user])

        # When
        result = await load_users_by_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [existing_user, None]

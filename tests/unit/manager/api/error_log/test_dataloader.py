"""Tests for error_log GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.api.gql.data_loader.error_log.loader import (
    load_error_logs_by_ids,
)
from ai.backend.manager.data.error_log.types import ErrorLogData


class TestLoadErrorLogsByIds:
    """Tests for load_error_logs_by_ids function."""

    @staticmethod
    def create_mock_error_log(error_log_id: uuid.UUID) -> MagicMock:
        return MagicMock(spec=ErrorLogData, id=error_log_id)

    @staticmethod
    def create_mock_processor(error_logs: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.data = error_logs
        mock_processor.search.wait_for_complete = AsyncMock(return_value=mock_action_result)
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_error_logs_by_ids(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search.wait_for_complete.assert_not_called()

    async def test_returns_error_logs_in_request_order(self) -> None:
        # Given
        id1, id2, id3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        error_log1 = self.create_mock_error_log(id1)
        error_log2 = self.create_mock_error_log(id2)
        error_log3 = self.create_mock_error_log(id3)
        mock_processor = self.create_mock_processor(
            [error_log3, error_log1, error_log2]  # DB returns in different order
        )

        # When
        result = await load_error_logs_by_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [error_log1, error_log2, error_log3]

    async def test_returns_none_for_missing_ids(self) -> None:
        # Given
        existing_id = uuid.uuid4()
        missing_id = uuid.uuid4()
        existing_error_log = self.create_mock_error_log(existing_id)
        mock_processor = self.create_mock_processor([existing_error_log])

        # When
        result = await load_error_logs_by_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [existing_error_log, None]

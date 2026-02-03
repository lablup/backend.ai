"""Tests for audit_log GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.api.gql.data_loader.audit_log.loader import (
    load_audit_logs_by_ids,
)
from ai.backend.manager.data.audit_log.types import AuditLogData


class TestLoadAuditLogsByIds:
    """Tests for load_audit_logs_by_ids function."""

    @staticmethod
    def create_mock_audit_log(audit_log_id: uuid.UUID) -> MagicMock:
        return MagicMock(spec=AuditLogData, id=audit_log_id)

    @staticmethod
    def create_mock_processor(audit_logs: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.data = audit_logs
        mock_processor.search.wait_for_complete = AsyncMock(return_value=mock_action_result)
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_audit_logs_by_ids(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search.wait_for_complete.assert_not_called()

    async def test_returns_audit_logs_in_request_order(self) -> None:
        # Given
        id1, id2, id3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        audit_log1 = self.create_mock_audit_log(id1)
        audit_log2 = self.create_mock_audit_log(id2)
        audit_log3 = self.create_mock_audit_log(id3)
        mock_processor = self.create_mock_processor(
            [audit_log3, audit_log1, audit_log2]  # DB returns in different order
        )

        # When
        result = await load_audit_logs_by_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [audit_log1, audit_log2, audit_log3]

    async def test_returns_none_for_missing_ids(self) -> None:
        # Given
        existing_id = uuid.uuid4()
        missing_id = uuid.uuid4()
        existing_audit_log = self.create_mock_audit_log(existing_id)
        mock_processor = self.create_mock_processor([existing_audit_log])

        # When
        result = await load_audit_logs_by_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [existing_audit_log, None]

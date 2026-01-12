"""Tests for GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.api.gql.data_loader.notification.loader import (
    load_channels_by_ids,
    load_rules_by_ids,
)
from ai.backend.manager.data.notification import NotificationChannelData, NotificationRuleData


class TestLoadChannelsByIds:
    """Tests for load_channels_by_ids function."""

    @staticmethod
    def create_mock_channel(channel_id: uuid.UUID) -> MagicMock:
        return MagicMock(spec=NotificationChannelData, id=channel_id)

    @staticmethod
    def create_mock_processor(channels: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.channels = channels
        mock_processor.search_channels.wait_for_complete = AsyncMock(
            return_value=mock_action_result
        )
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_channels_by_ids(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search_channels.wait_for_complete.assert_not_called()

    async def test_returns_channels_in_request_order(self) -> None:
        # Given
        id1, id2, id3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        channel1 = self.create_mock_channel(id1)
        channel2 = self.create_mock_channel(id2)
        channel3 = self.create_mock_channel(id3)
        mock_processor = self.create_mock_processor(
            [channel3, channel1, channel2]  # DB returns in different order
        )

        # When
        result = await load_channels_by_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [channel1, channel2, channel3]

    async def test_returns_none_for_missing_ids(self) -> None:
        # Given
        existing_id = uuid.uuid4()
        missing_id = uuid.uuid4()
        existing_channel = self.create_mock_channel(existing_id)
        mock_processor = self.create_mock_processor([existing_channel])

        # When
        result = await load_channels_by_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [existing_channel, None]


class TestLoadRulesByIds:
    """Tests for load_rules_by_ids function."""

    @staticmethod
    def create_mock_rule(rule_id: uuid.UUID) -> MagicMock:
        return MagicMock(spec=NotificationRuleData, id=rule_id)

    @staticmethod
    def create_mock_processor(rules: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.rules = rules
        mock_processor.search_rules.wait_for_complete = AsyncMock(return_value=mock_action_result)
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_rules_by_ids(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search_rules.wait_for_complete.assert_not_called()

    async def test_returns_rules_in_request_order(self) -> None:
        # Given
        id1, id2, id3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        rule1 = self.create_mock_rule(id1)
        rule2 = self.create_mock_rule(id2)
        rule3 = self.create_mock_rule(id3)
        mock_processor = self.create_mock_processor(
            [rule2, rule3, rule1]  # DB returns in different order
        )

        # When
        result = await load_rules_by_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [rule1, rule2, rule3]

    async def test_returns_none_for_missing_ids(self) -> None:
        # Given
        existing_id = uuid.uuid4()
        missing_id = uuid.uuid4()
        existing_rule = self.create_mock_rule(existing_id)
        mock_processor = self.create_mock_processor([existing_rule])

        # When
        result = await load_rules_by_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [existing_rule, None]

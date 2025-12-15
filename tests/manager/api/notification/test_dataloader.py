"""Tests for GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.api.gql.data_loader.notification.loader import (
    load_channels_by_ids,
    load_rules_by_ids,
)
from ai.backend.manager.data.notification import NotificationChannelData, NotificationRuleData


class TestLoadChannelsByIds:
    """Tests for load_channels_by_ids function."""

    @pytest.mark.asyncio
    async def test_empty_ids_returns_empty_list(self) -> None:
        """Test that empty channel_ids returns empty list."""
        mock_processor = MagicMock()

        result = await load_channels_by_ids(mock_processor, [])

        assert result == []
        mock_processor.search_channels.wait_for_complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_channels_in_request_order(self) -> None:
        """Test that channels are returned in the same order as requested IDs."""
        id1, id2, id3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

        channel1 = MagicMock(spec=NotificationChannelData, id=id1)
        channel2 = MagicMock(spec=NotificationChannelData, id=id2)
        channel3 = MagicMock(spec=NotificationChannelData, id=id3)

        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        # DB returns in different order
        mock_action_result.channels = [channel3, channel1, channel2]
        mock_processor.search_channels.wait_for_complete = AsyncMock(
            return_value=mock_action_result
        )

        result = await load_channels_by_ids(mock_processor, [id1, id2, id3])

        assert len(result) == 3
        assert result[0] == channel1
        assert result[1] == channel2
        assert result[2] == channel3

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_ids(self) -> None:
        """Test that None is returned for IDs not found in DB."""
        existing_id = uuid.uuid4()
        missing_id = uuid.uuid4()

        existing_channel = MagicMock(spec=NotificationChannelData, id=existing_id)

        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.channels = [existing_channel]
        mock_processor.search_channels.wait_for_complete = AsyncMock(
            return_value=mock_action_result
        )

        result = await load_channels_by_ids(mock_processor, [existing_id, missing_id])

        assert len(result) == 2
        assert result[0] == existing_channel
        assert result[1] is None


class TestLoadRulesByIds:
    """Tests for load_rules_by_ids function."""

    @pytest.mark.asyncio
    async def test_empty_ids_returns_empty_list(self) -> None:
        """Test that empty rule_ids returns empty list."""
        mock_processor = MagicMock()

        result = await load_rules_by_ids(mock_processor, [])

        assert result == []
        mock_processor.search_rules.wait_for_complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_rules_in_request_order(self) -> None:
        """Test that rules are returned in the same order as requested IDs."""
        id1, id2, id3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

        rule1 = MagicMock(spec=NotificationRuleData, id=id1)
        rule2 = MagicMock(spec=NotificationRuleData, id=id2)
        rule3 = MagicMock(spec=NotificationRuleData, id=id3)

        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        # DB returns in different order
        mock_action_result.rules = [rule2, rule3, rule1]
        mock_processor.search_rules.wait_for_complete = AsyncMock(return_value=mock_action_result)

        result = await load_rules_by_ids(mock_processor, [id1, id2, id3])

        assert len(result) == 3
        assert result[0] == rule1
        assert result[1] == rule2
        assert result[2] == rule3

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_ids(self) -> None:
        """Test that None is returned for IDs not found in DB."""
        existing_id = uuid.uuid4()
        missing_id = uuid.uuid4()

        existing_rule = MagicMock(spec=NotificationRuleData, id=existing_id)

        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.rules = [existing_rule]
        mock_processor.search_rules.wait_for_complete = AsyncMock(return_value=mock_action_result)

        result = await load_rules_by_ids(mock_processor, [existing_id, missing_id])

        assert len(result) == 2
        assert result[0] == existing_rule
        assert result[1] is None

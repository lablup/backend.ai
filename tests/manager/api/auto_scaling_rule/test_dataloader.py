"""Tests for auto scaling rule GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.api.gql.data_loader.auto_scaling_rule.loader import (
    load_auto_scaling_rules_by_ids,
)
from ai.backend.manager.data.deployment.types import ModelDeploymentAutoScalingRuleData


class TestLoadAutoScalingRulesByIds:
    """Tests for load_auto_scaling_rules_by_ids function."""

    @staticmethod
    def create_mock_rule(rule_id: uuid.UUID) -> MagicMock:
        mock = MagicMock(spec=ModelDeploymentAutoScalingRuleData)
        mock.id = rule_id
        return mock

    @staticmethod
    def create_mock_processor(rules: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.data = rules
        mock_processor.batch_load_auto_scaling_rules.wait_for_complete = AsyncMock(
            return_value=mock_action_result
        )
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_auto_scaling_rules_by_ids(mock_processor, [])

        # Then
        assert result == []
        mock_processor.batch_load_auto_scaling_rules.wait_for_complete.assert_not_called()

    async def test_returns_rules_in_request_order(self) -> None:
        # Given
        id1, id2, id3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        rule1 = self.create_mock_rule(id1)
        rule2 = self.create_mock_rule(id2)
        rule3 = self.create_mock_rule(id3)
        mock_processor = self.create_mock_processor(
            [rule3, rule1, rule2]  # DB returns in different order
        )

        # When
        result = await load_auto_scaling_rules_by_ids(mock_processor, [id1, id2, id3])

        # Then
        assert result == [rule1, rule2, rule3]

    async def test_returns_none_for_missing_ids(self) -> None:
        # Given
        existing_id = uuid.uuid4()
        missing_id = uuid.uuid4()
        existing_rule = self.create_mock_rule(existing_id)
        mock_processor = self.create_mock_processor([existing_rule])

        # When
        result = await load_auto_scaling_rules_by_ids(mock_processor, [existing_id, missing_id])

        # Then
        assert result == [existing_rule, None]

    async def test_returns_none_for_all_when_processor_is_none(self) -> None:
        # Given
        id1, id2 = uuid.uuid4(), uuid.uuid4()

        # When
        result = await load_auto_scaling_rules_by_ids(None, [id1, id2])

        # Then
        assert result == [None, None]

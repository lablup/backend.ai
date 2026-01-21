"""Tests for scaling group GraphQL DataLoader utilities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.api.gql.data_loader.scaling_group.loader import (
    load_scaling_groups_by_names,
)
from ai.backend.manager.data.scaling_group.types import ScalingGroupData


class TestLoadScalingGroupsByNames:
    """Tests for load_scaling_groups_by_names function."""

    @staticmethod
    def create_mock_scaling_group(sg_name: str) -> MagicMock:
        mock = MagicMock(spec=ScalingGroupData)
        mock.name = sg_name
        return mock

    @staticmethod
    def create_mock_processor(scaling_groups: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.scaling_groups = scaling_groups
        mock_processor.search_scaling_groups.wait_for_complete = AsyncMock(
            return_value=mock_action_result
        )
        return mock_processor

    async def test_empty_names_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_scaling_groups_by_names(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search_scaling_groups.wait_for_complete.assert_not_called()

    async def test_returns_scaling_groups_in_request_order(self) -> None:
        # Given
        name1, name2, name3 = "sg1", "sg2", "sg3"
        sg1 = self.create_mock_scaling_group(name1)
        sg2 = self.create_mock_scaling_group(name2)
        sg3 = self.create_mock_scaling_group(name3)
        mock_processor = self.create_mock_processor(
            [sg3, sg1, sg2]  # DB returns in different order
        )

        # When
        result = await load_scaling_groups_by_names(mock_processor, [name1, name2, name3])

        # Then
        assert result == [sg1, sg2, sg3]

    async def test_returns_none_for_missing_names(self) -> None:
        # Given
        existing_name = "existing-sg"
        missing_name = "missing-sg"
        existing_sg = self.create_mock_scaling_group(existing_name)
        mock_processor = self.create_mock_processor([existing_sg])

        # When
        result = await load_scaling_groups_by_names(mock_processor, [existing_name, missing_name])

        # Then
        assert result == [existing_sg, None]

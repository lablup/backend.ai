"""Tests for resource group GraphQL DataLoader utilities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.api.gql.data_loader.resource_group.loader import (
    load_resource_groups_by_names,
)
from ai.backend.manager.data.scaling_group.types import ScalingGroupData


class TestLoadResourceGroupsByNames:
    """Tests for load_resource_groups_by_names function."""

    @staticmethod
    def create_mock_resource_group(rg_name: str) -> MagicMock:
        mock = MagicMock(spec=ScalingGroupData)
        mock.name = rg_name
        return mock

    @staticmethod
    def create_mock_processor(resource_groups: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.scaling_groups = resource_groups
        mock_processor.search_scaling_groups.wait_for_complete = AsyncMock(
            return_value=mock_action_result
        )
        return mock_processor

    async def test_empty_names_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_resource_groups_by_names(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search_scaling_groups.wait_for_complete.assert_not_called()

    async def test_returns_resource_groups_in_request_order(self) -> None:
        # Given
        name1, name2, name3 = "rg1", "rg2", "rg3"
        rg1 = self.create_mock_resource_group(name1)
        rg2 = self.create_mock_resource_group(name2)
        rg3 = self.create_mock_resource_group(name3)
        mock_processor = self.create_mock_processor(
            [rg3, rg1, rg2]  # DB returns in different order
        )

        # When
        result = await load_resource_groups_by_names(mock_processor, [name1, name2, name3])

        # Then
        assert result == [rg1, rg2, rg3]

    async def test_returns_none_for_missing_names(self) -> None:
        # Given
        existing_name = "existing-rg"
        missing_name = "missing-rg"
        existing_rg = self.create_mock_resource_group(existing_name)
        mock_processor = self.create_mock_processor([existing_rg])

        # When
        result = await load_resource_groups_by_names(mock_processor, [existing_name, missing_name])

        # Then
        assert result == [existing_rg, None]

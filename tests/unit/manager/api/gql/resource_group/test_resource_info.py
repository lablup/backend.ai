"""Tests for ResourceInfo GQL type and resolver."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.api.gql.resource_group.types import (
    ResourceGroupGQL,
    ResourceGroupMetadataGQL,
    ResourceGroupNetworkConfigGQL,
    ResourceGroupSchedulerConfigGQL,
    ResourceGroupStatusGQL,
    ResourceInfoGQL,
    SchedulerTypeGQL,
)
from ai.backend.manager.data.scaling_group.types import ResourceInfo
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.scaling_group.types import FairShareScalingGroupSpec
from ai.backend.manager.services.scaling_group.actions.get_resource_info import (
    GetResourceInfoActionResult,
)


class TestResourceInfoGQL:
    """Tests for ResourceInfoGQL type conversion."""

    def test_from_resource_info_converts_all_fields(self) -> None:
        """Test that all fields are correctly converted to ResourceSlotGQL."""
        # Given
        resource_info = ResourceInfo(
            capacity=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")}),
            used=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4294967296")}),
            free=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4294967296")}),
        )

        # When
        gql_type = ResourceInfoGQL.from_resource_info(resource_info)

        # Then
        assert isinstance(gql_type, ResourceInfoGQL)
        assert isinstance(gql_type.capacity, ResourceSlotGQL)
        assert isinstance(gql_type.used, ResourceSlotGQL)
        assert isinstance(gql_type.free, ResourceSlotGQL)

        # Verify capacity entries
        capacity_entries = {e.resource_type: e.quantity for e in gql_type.capacity.entries}
        assert capacity_entries["cpu"] == Decimal("4")
        assert capacity_entries["mem"] == Decimal("8589934592")

        # Verify used entries
        used_entries = {e.resource_type: e.quantity for e in gql_type.used.entries}
        assert used_entries["cpu"] == Decimal("2")
        assert used_entries["mem"] == Decimal("4294967296")

        # Verify free entries
        free_entries = {e.resource_type: e.quantity for e in gql_type.free.entries}
        assert free_entries["cpu"] == Decimal("2")
        assert free_entries["mem"] == Decimal("4294967296")

    def test_from_resource_info_with_empty_slots(self) -> None:
        """Test conversion when ResourceInfo has empty ResourceSlots."""
        # Given
        resource_info = ResourceInfo(
            capacity=ResourceSlot(),
            used=ResourceSlot(),
            free=ResourceSlot(),
        )

        # When
        gql_type = ResourceInfoGQL.from_resource_info(resource_info)

        # Then
        assert isinstance(gql_type, ResourceInfoGQL)
        assert gql_type.capacity.entries == []
        assert gql_type.used.entries == []
        assert gql_type.free.entries == []

    def test_from_resource_info_with_multiple_resource_types(self) -> None:
        """Test conversion with various resource types including accelerators."""
        # Given
        resource_info = ResourceInfo(
            capacity=ResourceSlot({
                "cpu": Decimal("8"),
                "mem": Decimal("17179869184"),
                "cuda.shares": Decimal("4"),
                "rocm.devices": Decimal("2"),
            }),
            used=ResourceSlot({
                "cpu": Decimal("4"),
                "mem": Decimal("8589934592"),
                "cuda.shares": Decimal("2"),
                "rocm.devices": Decimal("1"),
            }),
            free=ResourceSlot({
                "cpu": Decimal("4"),
                "mem": Decimal("8589934592"),
                "cuda.shares": Decimal("2"),
                "rocm.devices": Decimal("1"),
            }),
        )

        # When
        gql_type = ResourceInfoGQL.from_resource_info(resource_info)

        # Then
        capacity_entries = {e.resource_type: e.quantity for e in gql_type.capacity.entries}
        assert len(capacity_entries) == 4
        assert capacity_entries["cpu"] == Decimal("8")
        assert capacity_entries["mem"] == Decimal("17179869184")
        assert capacity_entries["cuda.shares"] == Decimal("4")
        assert capacity_entries["rocm.devices"] == Decimal("2")


class TestResourceGroupGQLResourceInfoResolver:
    """Tests for ResourceGroupGQL.resource_info resolver."""

    @pytest.fixture
    def mock_get_resource_info_processor(self) -> AsyncMock:
        """Create mock get_resource_info ActionProcessor."""
        return AsyncMock()

    @pytest.fixture
    def mock_context(self, mock_get_resource_info_processor: AsyncMock) -> MagicMock:
        """Create mock GraphQL context with processors."""
        context = MagicMock()
        context.processors = MagicMock()
        context.processors.scaling_group = MagicMock()
        context.processors.scaling_group.get_resource_info = mock_get_resource_info_processor
        return context

    @pytest.fixture
    def mock_info(self, mock_context: MagicMock) -> MagicMock:
        """Create mock strawberry.Info with context."""
        info = MagicMock()
        info.context = mock_context
        return info

    @pytest.fixture
    def resource_group_gql(self) -> ResourceGroupGQL:
        """Create ResourceGroupGQL instance for testing."""
        return ResourceGroupGQL(
            id="test-group",
            name="test-group",
            status=ResourceGroupStatusGQL(is_active=True, is_public=True),
            metadata=ResourceGroupMetadataGQL(
                description="Test resource group",
                created_at=datetime.now(UTC),
            ),
            network=ResourceGroupNetworkConfigGQL(
                wsproxy_addr=None,
                use_host_network=False,
            ),
            scheduler=ResourceGroupSchedulerConfigGQL(type=SchedulerTypeGQL.FIFO),
            _fair_share_spec_data=FairShareScalingGroupSpec(
                half_life_days=7,
                lookback_days=28,
                decay_unit_days=1,
                default_weight=Decimal("1.0"),
                resource_weights=ResourceSlot({}),
            ),
        )

    @pytest.fixture
    def sample_resource_info(self) -> ResourceInfo:
        """Create sample ResourceInfo for testing."""
        return ResourceInfo(
            capacity=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")}),
            used=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2147483648")}),
            free=ResourceSlot({"cpu": Decimal("3"), "mem": Decimal("6442450944")}),
        )

    @pytest.mark.asyncio
    async def test_resolver_calls_processor_with_correct_action(
        self,
        resource_group_gql: ResourceGroupGQL,
        mock_info: MagicMock,
        mock_get_resource_info_processor: AsyncMock,
        sample_resource_info: ResourceInfo,
    ) -> None:
        """Test that resolver calls processor with correct action."""
        # Given
        mock_get_resource_info_processor.wait_for_complete.return_value = (
            GetResourceInfoActionResult(resource_info=sample_resource_info)
        )

        # When
        result = await resource_group_gql.resource_info(info=mock_info)

        # Then
        mock_get_resource_info_processor.wait_for_complete.assert_called_once()
        call_args = mock_get_resource_info_processor.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.scaling_group == "test-group"
        assert isinstance(result, ResourceInfoGQL)

    @pytest.mark.asyncio
    async def test_resolver_returns_converted_gql_type(
        self,
        resource_group_gql: ResourceGroupGQL,
        mock_info: MagicMock,
        mock_get_resource_info_processor: AsyncMock,
        sample_resource_info: ResourceInfo,
    ) -> None:
        """Test that resolver returns properly converted ResourceInfoGQL."""
        # Given
        mock_get_resource_info_processor.wait_for_complete.return_value = (
            GetResourceInfoActionResult(resource_info=sample_resource_info)
        )

        # When
        result = await resource_group_gql.resource_info(info=mock_info)

        # Then
        assert isinstance(result, ResourceInfoGQL)

        capacity_entries = {e.resource_type: e.quantity for e in result.capacity.entries}
        assert capacity_entries["cpu"] == Decimal("4")
        assert capacity_entries["mem"] == Decimal("8589934592")

        used_entries = {e.resource_type: e.quantity for e in result.used.entries}
        assert used_entries["cpu"] == Decimal("1")
        assert used_entries["mem"] == Decimal("2147483648")

        free_entries = {e.resource_type: e.quantity for e in result.free.entries}
        assert free_entries["cpu"] == Decimal("3")
        assert free_entries["mem"] == Decimal("6442450944")

    @pytest.mark.asyncio
    async def test_resolver_propagates_scaling_group_not_found(
        self,
        resource_group_gql: ResourceGroupGQL,
        mock_info: MagicMock,
        mock_get_resource_info_processor: AsyncMock,
    ) -> None:
        """Test that ScalingGroupNotFound exception propagates correctly."""
        # Given
        mock_get_resource_info_processor.wait_for_complete.side_effect = ScalingGroupNotFound(
            "test-group"
        )

        # When / Then
        with pytest.raises(ScalingGroupNotFound):
            await resource_group_gql.resource_info(info=mock_info)

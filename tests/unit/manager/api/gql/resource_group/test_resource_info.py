"""Tests for ResourceInfo GQL type and resolver."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.dto.manager.v2.fair_share.types import (
    ResourceSlotEntryInfo,
    ResourceSlotInfo,
)
from ai.backend.common.dto.manager.v2.resource_group.response import (
    PreemptionConfigInfo,
    ResourceGroupMetadataInfo,
    ResourceGroupNetworkConfigInfo,
    ResourceGroupSchedulerConfigInfo,
    ResourceGroupStatusInfo,
    ResourceInfoNode,
)
from ai.backend.common.dto.manager.v2.resource_group.types import (
    PreemptionModeDTO,
    PreemptionOrderDTO,
    SchedulerTypeDTO,
)
from ai.backend.common.types import SlotQuantity
from ai.backend.manager.api.adapters.resource_group import (
    _normalize_quantity,
    _slot_quantities_to_resource_slot_info,
)
from ai.backend.manager.api.gql.fair_share.types.common import ResourceSlotGQL
from ai.backend.manager.api.gql.resource_group.types import (
    ResourceGroupGQL,
    ResourceGroupMetadataGQL,
    ResourceGroupNetworkConfigGQL,
    ResourceGroupSchedulerConfigGQL,
    ResourceGroupStatusGQL,
    ResourceInfoGQL,
)
from ai.backend.manager.errors.resource import ScalingGroupNotFound


class TestResourceSlotGQLNormalization:
    """Regression tests for BA-4636: quantity decimal normalization in adapter layer."""

    def test_normalize_quantity_strips_trailing_zeros(self) -> None:
        """Values from DB (NUMERIC scale=6) should have trailing zeros stripped."""
        assert _normalize_quantity(Decimal("7.000000")) == Decimal("7")
        assert _normalize_quantity(Decimal("0.500000")) == Decimal("0.5")
        assert _normalize_quantity(Decimal("0.250000")) == Decimal("0.25")

    def test_normalize_quantity_no_scientific_notation_for_large_integers(self) -> None:
        """Large integer quantities must not be serialized in scientific notation."""
        result = _normalize_quantity(Decimal("17179869184.000000"))
        assert str(result) == "17179869184"
        assert "E" not in str(result)
        assert "e" not in str(result)

    def test_normalize_quantity_preserves_fractional_precision(self) -> None:
        """Fractional values should keep meaningful decimal places."""
        assert _normalize_quantity(Decimal("1.500000")) == Decimal("1.5")
        assert _normalize_quantity(Decimal("4294967296.000000")) == Decimal("4294967296")

    def test_slot_quantities_to_resource_slot_info_normalizes_values(self) -> None:
        """_slot_quantities_to_resource_slot_info should normalize DB decimal values."""
        quantities = [
            SlotQuantity("cpu", Decimal("7.000000")),
            SlotQuantity("mem", Decimal("4294967296.000000")),
            SlotQuantity("cuda.shares", Decimal("0.500000")),
        ]

        result = _slot_quantities_to_resource_slot_info(quantities)

        entries = {e.resource_type: e.quantity for e in result.entries}
        assert str(entries["cpu"]) == "7"
        assert str(entries["mem"]) == "4294967296"
        assert str(entries["cuda.shares"]) == "0.5"

    def test_from_pydantic_preserves_normalized_values(self) -> None:
        """ResourceInfoGQL.from_pydantic() should preserve already-normalized values."""
        dto = ResourceInfoNode(
            capacity=ResourceSlotInfo(
                entries=[
                    ResourceSlotEntryInfo(resource_type="cpu", quantity=Decimal("7")),
                    ResourceSlotEntryInfo(resource_type="mem", quantity=Decimal("4294967296")),
                ]
            ),
            used=ResourceSlotInfo(
                entries=[
                    ResourceSlotEntryInfo(resource_type="cpu", quantity=Decimal("2")),
                ]
            ),
            free=ResourceSlotInfo(
                entries=[
                    ResourceSlotEntryInfo(resource_type="cpu", quantity=Decimal("5")),
                    ResourceSlotEntryInfo(resource_type="mem", quantity=Decimal("4294967296")),
                ]
            ),
        )

        gql = ResourceInfoGQL.from_pydantic(dto)

        capacity_entries = {e.resource_type: e.quantity for e in gql.capacity.entries}
        assert str(capacity_entries["cpu"]) == "7"
        assert str(capacity_entries["mem"]) == "4294967296"


class TestResourceInfoGQL:
    """Tests for ResourceInfoGQL type conversion via from_pydantic."""

    def test_from_pydantic_converts_all_fields(self) -> None:
        """Test that all fields are correctly converted from ResourceInfoNode DTO."""
        # Given
        dto = ResourceInfoNode(
            capacity=ResourceSlotInfo(
                entries=[
                    ResourceSlotEntryInfo(resource_type="cpu", quantity=Decimal("4")),
                    ResourceSlotEntryInfo(resource_type="mem", quantity=Decimal("8589934592")),
                ]
            ),
            used=ResourceSlotInfo(
                entries=[
                    ResourceSlotEntryInfo(resource_type="cpu", quantity=Decimal("2")),
                    ResourceSlotEntryInfo(resource_type="mem", quantity=Decimal("4294967296")),
                ]
            ),
            free=ResourceSlotInfo(
                entries=[
                    ResourceSlotEntryInfo(resource_type="cpu", quantity=Decimal("2")),
                    ResourceSlotEntryInfo(resource_type="mem", quantity=Decimal("4294967296")),
                ]
            ),
        )

        # When
        gql_type = ResourceInfoGQL.from_pydantic(dto)

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

    def test_from_pydantic_with_empty_slots(self) -> None:
        """Test conversion when ResourceInfoNode has empty ResourceSlotInfo."""
        # Given
        dto = ResourceInfoNode(
            capacity=ResourceSlotInfo(entries=[]),
            used=ResourceSlotInfo(entries=[]),
            free=ResourceSlotInfo(entries=[]),
        )

        # When
        gql_type = ResourceInfoGQL.from_pydantic(dto)

        # Then
        assert isinstance(gql_type, ResourceInfoGQL)
        assert gql_type.capacity.entries == []
        assert gql_type.used.entries == []
        assert gql_type.free.entries == []

    def test_from_pydantic_with_multiple_resource_types(self) -> None:
        """Test conversion with various resource types including accelerators."""
        # Given
        dto = ResourceInfoNode(
            capacity=ResourceSlotInfo(
                entries=[
                    ResourceSlotEntryInfo(resource_type="cpu", quantity=Decimal("8")),
                    ResourceSlotEntryInfo(resource_type="mem", quantity=Decimal("17179869184")),
                    ResourceSlotEntryInfo(resource_type="cuda.shares", quantity=Decimal("4")),
                    ResourceSlotEntryInfo(resource_type="rocm.devices", quantity=Decimal("2")),
                ]
            ),
            used=ResourceSlotInfo(
                entries=[
                    ResourceSlotEntryInfo(resource_type="cpu", quantity=Decimal("4")),
                    ResourceSlotEntryInfo(resource_type="mem", quantity=Decimal("8589934592")),
                    ResourceSlotEntryInfo(resource_type="cuda.shares", quantity=Decimal("2")),
                    ResourceSlotEntryInfo(resource_type="rocm.devices", quantity=Decimal("1")),
                ]
            ),
            free=ResourceSlotInfo(
                entries=[
                    ResourceSlotEntryInfo(resource_type="cpu", quantity=Decimal("4")),
                    ResourceSlotEntryInfo(resource_type="mem", quantity=Decimal("8589934592")),
                    ResourceSlotEntryInfo(resource_type="cuda.shares", quantity=Decimal("2")),
                    ResourceSlotEntryInfo(resource_type="rocm.devices", quantity=Decimal("1")),
                ]
            ),
        )

        # When
        gql_type = ResourceInfoGQL.from_pydantic(dto)

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
    def mock_context(self) -> MagicMock:
        """Create mock GraphQL context with adapter."""
        context = MagicMock()
        context.adapters.resource_group.get_resource_info = AsyncMock()
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
            status=ResourceGroupStatusGQL.from_pydantic(
                ResourceGroupStatusInfo(is_active=True, is_public=True)
            ),
            metadata=ResourceGroupMetadataGQL.from_pydantic(
                ResourceGroupMetadataInfo(
                    description="Test resource group",
                    created_at=datetime.now(UTC),
                )
            ),
            network=ResourceGroupNetworkConfigGQL.from_pydantic(
                ResourceGroupNetworkConfigInfo(
                    wsproxy_addr=None,
                    use_host_network=False,
                )
            ),
            scheduler=ResourceGroupSchedulerConfigGQL.from_pydantic(
                ResourceGroupSchedulerConfigInfo(
                    type=SchedulerTypeDTO.FIFO,
                    preemption=PreemptionConfigInfo(
                        preemptible_priority=5,
                        order=PreemptionOrderDTO.OLDEST,
                        mode=PreemptionModeDTO.TERMINATE,
                    ),
                )
            ),
        )

    @pytest.fixture
    def sample_resource_info_node(self) -> ResourceInfoNode:
        """Create sample ResourceInfoNode for testing."""
        return ResourceInfoNode(
            capacity=ResourceSlotInfo(
                entries=[
                    ResourceSlotEntryInfo(resource_type="cpu", quantity=Decimal("4")),
                    ResourceSlotEntryInfo(resource_type="mem", quantity=Decimal("8589934592")),
                ]
            ),
            used=ResourceSlotInfo(
                entries=[
                    ResourceSlotEntryInfo(resource_type="cpu", quantity=Decimal("1")),
                    ResourceSlotEntryInfo(resource_type="mem", quantity=Decimal("2147483648")),
                ]
            ),
            free=ResourceSlotInfo(
                entries=[
                    ResourceSlotEntryInfo(resource_type="cpu", quantity=Decimal("3")),
                    ResourceSlotEntryInfo(resource_type="mem", quantity=Decimal("6442450944")),
                ]
            ),
        )

    async def test_resolver_calls_adapter_with_correct_name(
        self,
        resource_group_gql: ResourceGroupGQL,
        mock_info: MagicMock,
        mock_context: MagicMock,
        sample_resource_info_node: ResourceInfoNode,
    ) -> None:
        """Test that resolver calls adapter with correct scaling group name."""
        # Given
        mock_context.adapters.resource_group.get_resource_info.return_value = (
            sample_resource_info_node
        )

        # When
        result = await resource_group_gql.resource_info(info=mock_info)

        # Then
        mock_context.adapters.resource_group.get_resource_info.assert_called_once_with("test-group")
        assert isinstance(result, ResourceInfoGQL)

    async def test_resolver_returns_converted_gql_type(
        self,
        resource_group_gql: ResourceGroupGQL,
        mock_info: MagicMock,
        mock_context: MagicMock,
        sample_resource_info_node: ResourceInfoNode,
    ) -> None:
        """Test that resolver returns properly converted ResourceInfoGQL."""
        # Given
        mock_context.adapters.resource_group.get_resource_info.return_value = (
            sample_resource_info_node
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

    async def test_resolver_propagates_scaling_group_not_found(
        self,
        resource_group_gql: ResourceGroupGQL,
        mock_info: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that ScalingGroupNotFound exception propagates correctly."""
        # Given
        mock_context.adapters.resource_group.get_resource_info.side_effect = ScalingGroupNotFound(
            "test-group"
        )

        # When / Then
        with pytest.raises(ScalingGroupNotFound):
            await resource_group_gql.resource_info(info=mock_info)

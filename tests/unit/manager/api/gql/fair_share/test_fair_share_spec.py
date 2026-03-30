"""Tests for FairShareSpecGQL weight and uses_default fields."""

from __future__ import annotations

from decimal import Decimal

import pytest

from ai.backend.common.dto.manager.v2.fair_share.types import (
    FairShareSpecInfo,
    ResourceWeightEntryInfo,
)
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.adapters.fair_share import FairShareAdapter
from ai.backend.manager.api.gql.fair_share.types.common import FairShareSpecGQL
from ai.backend.manager.data.fair_share.types import FairShareSpec


class TestFairShareSpecGQLWeight:
    """Tests for FairShareSpecGQL weight and uses_default conversion via adapter."""

    @pytest.fixture
    def default_weight(self) -> Decimal:
        """Default weight from resource group (different from typical default 1.0)."""
        return Decimal("3.0")

    @pytest.fixture
    def spec_with_explicit_weight(self) -> FairShareSpec:
        """FairShareSpec with explicitly set weight.

        Uses values different from defaults to ensure proper conversion.
        Defaults: half_life_days=7, lookback_days=28, decay_unit_days=1
        """
        return FairShareSpec(
            weight=Decimal("2.5"),
            half_life_days=14,  # Different from default 7
            lookback_days=30,  # Different from default 28
            decay_unit_days=2,  # Different from default 1
            resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("0.5")}),
        )

    @pytest.fixture
    def spec_with_default_weight(self, default_weight: Decimal) -> FairShareSpec:
        """FairShareSpec using default weight (Repository set it from default_weight)."""
        return FairShareSpec(
            weight=default_weight,  # Repository already set this to default_weight
            half_life_days=14,
            lookback_days=30,
            decay_unit_days=2,
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
        )

    def test_uses_explicit_weight_when_set(
        self,
        spec_with_explicit_weight: FairShareSpec,
    ) -> None:
        """Test that explicit weight is used when set."""
        # When: convert via adapter then wrap in GQL type
        spec_info = FairShareAdapter._convert_spec(
            spec_with_explicit_weight, use_default=False, uses_default_resources=frozenset()
        )
        gql = FairShareSpecGQL.from_pydantic(spec_info)

        # Then
        assert gql.weight == Decimal("2.5")
        assert gql.uses_default is False

    def test_uses_default_weight(
        self,
        spec_with_default_weight: FairShareSpec,
    ) -> None:
        """Test that default weight flag is set when using defaults."""
        # When
        spec_info = FairShareAdapter._convert_spec(
            spec_with_default_weight, use_default=True, uses_default_resources=frozenset()
        )
        gql = FairShareSpecGQL.from_pydantic(spec_info)

        # Then
        assert gql.weight == Decimal("3.0")  # default_weight fixture value
        assert gql.uses_default is True

    def test_uses_default_false_when_weight_equals_default(
        self,
    ) -> None:
        """Test that uses_default is False even if explicit weight equals default."""
        # Given: explicit weight that happens to equal default
        spec = FairShareSpec(
            weight=Decimal("3.0"),  # Same as default_weight but explicitly set
            half_life_days=14,
            lookback_days=30,
            decay_unit_days=2,
            resource_weights=ResourceSlot(),
        )

        # When
        spec_info = FairShareAdapter._convert_spec(
            spec, use_default=False, uses_default_resources=frozenset()
        )
        gql = FairShareSpecGQL.from_pydantic(spec_info)

        # Then
        assert gql.weight == Decimal("3.0")
        assert gql.uses_default is False  # Explicit setting, not default

    def test_preserves_other_spec_fields(
        self,
        spec_with_explicit_weight: FairShareSpec,
    ) -> None:
        """Test that other spec fields are correctly converted."""
        # When
        spec_info = FairShareAdapter._convert_spec(
            spec_with_explicit_weight, use_default=False, uses_default_resources=frozenset()
        )
        gql = FairShareSpecGQL.from_pydantic(spec_info)

        # Then
        assert gql.half_life_days == 14
        assert gql.lookback_days == 30
        assert gql.decay_unit_days == 2
        assert len(gql.resource_weights) == 2

    def test_adapter_convert_spec_returns_correct_dto(
        self,
        spec_with_explicit_weight: FairShareSpec,
    ) -> None:
        """Test that FairShareAdapter._convert_spec() returns correct FairShareSpecInfo DTO."""
        # When
        spec_info = FairShareAdapter._convert_spec(
            spec_with_explicit_weight,
            use_default=False,
            uses_default_resources=frozenset({"mem"}),
        )

        # Then
        assert isinstance(spec_info, FairShareSpecInfo)
        assert spec_info.weight == Decimal("2.5")
        assert spec_info.uses_default is False
        assert spec_info.half_life_days == 14
        assert spec_info.lookback_days == 30
        assert spec_info.decay_unit_days == 2
        assert len(spec_info.resource_weights) == 2

        weight_map = {entry.resource_type: entry for entry in spec_info.resource_weights}
        assert isinstance(weight_map["cpu"], ResourceWeightEntryInfo)
        assert weight_map["cpu"].uses_default is False
        assert weight_map["mem"].uses_default is True

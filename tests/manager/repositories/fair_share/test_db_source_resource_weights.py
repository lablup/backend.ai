"""Integration tests for Fair Share resource weights merging in DB source.

These tests verify that resource weights are correctly merged between
entity-specific weights and scaling group defaults.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.fair_share import FairShareData
from ai.backend.manager.models.fair_share.row import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)


class TestDomainFairShareRowToData:
    """Test DomainFairShareRow.to_data() with resource weight merging."""

    def test_partial_explicit_weights_with_null_weight(self) -> None:
        """Scenario 2.2: Domain fair share with NULL weight and partial resource weights."""
        # Given: Create a DomainFairShareRow with partial resource weights
        row = DomainFairShareRow(
            id=uuid.uuid4(),
            resource_group="default",
            domain_name="test-domain",
            weight=None,  # Uses default_weight
            fair_share_factor=Decimal("1.0"),
            total_decayed_usage=ResourceSlot({}),
            resource_weights=ResourceSlot({"cuda.device": Decimal("5.0")}),  # Partial
            normalized_usage=Decimal("0.0"),
            last_calculated_at=datetime.now(UTC),
            lookback_start=date.today(),
            lookback_end=date.today(),
            half_life_days=7,
            lookback_days=28,
            decay_unit_days=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        default_weight = Decimal("1.0")
        available_slots = ResourceSlot(
            {
                "cpu": Decimal("100"),
                "mem": Decimal("1000"),
                "cuda.device": Decimal("8"),
            }
        )

        # When
        result = row.to_data(default_weight, available_slots)

        # Then
        assert isinstance(result.data, FairShareData)
        assert result.data.spec.weight == Decimal("1.0")  # Uses default_weight
        assert result.data.use_default is True

        # Check merged resource weights - missing resources use default_weight
        assert result.data.spec.resource_weights["cpu"] == Decimal("1.0")  # default_weight
        assert result.data.spec.resource_weights["mem"] == Decimal("1.0")  # default_weight
        assert result.data.spec.resource_weights["cuda.device"] == Decimal("5.0")  # explicit

        # Check uses_default_resources
        assert "cpu" in result.data.uses_default_resources
        assert "mem" in result.data.uses_default_resources
        assert "cuda.device" not in result.data.uses_default_resources

    def test_explicit_weight_with_all_default_resource_weights(self) -> None:
        """Scenario 2.3: Explicit entity weight but all resource weights use defaults."""
        # Given
        row = DomainFairShareRow(
            id=uuid.uuid4(),
            resource_group="default",
            domain_name="test-domain",
            weight=Decimal("2.0"),  # Explicit weight
            fair_share_factor=Decimal("1.0"),
            total_decayed_usage=ResourceSlot({}),
            resource_weights=ResourceSlot({}),  # Empty - all use defaults
            normalized_usage=Decimal("0.0"),
            last_calculated_at=datetime.now(UTC),
            lookback_start=date.today(),
            lookback_end=date.today(),
            half_life_days=7,
            lookback_days=28,
            decay_unit_days=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        default_weight = Decimal("1.0")
        available_slots = ResourceSlot({"cpu": Decimal("100"), "mem": Decimal("1000")})

        # When
        result = row.to_data(default_weight, available_slots)

        # Then
        assert result.data.spec.weight == Decimal("2.0")  # Uses explicit weight
        assert result.data.use_default is False  # Explicit weight set

        # All resource weights use default_weight
        assert result.data.spec.resource_weights["cpu"] == Decimal("1.0")
        assert result.data.spec.resource_weights["mem"] == Decimal("1.0")

        # All resources use defaults
        assert result.data.uses_default_resources == frozenset(["cpu", "mem"])


class TestProjectFairShareRowToData:
    """Test ProjectFairShareRow.to_data() with resource weight merging."""

    def test_partial_resource_weights(self) -> None:
        """Scenario 2.4: Project fair share with partial resource weights."""
        # Given
        row = ProjectFairShareRow(
            id=uuid.uuid4(),
            resource_group="default",
            project_id=uuid.uuid4(),
            domain_name="test-domain",
            weight=Decimal("1.5"),
            fair_share_factor=Decimal("1.0"),
            total_decayed_usage=ResourceSlot({}),
            resource_weights=ResourceSlot({"cuda.shares": Decimal("0.1")}),
            normalized_usage=Decimal("0.0"),
            last_calculated_at=datetime.now(UTC),
            lookback_start=date.today(),
            lookback_end=date.today(),
            half_life_days=7,
            lookback_days=28,
            decay_unit_days=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        default_weight = Decimal("1.0")
        available_slots = ResourceSlot(
            {
                "cpu": Decimal("100"),
                "mem": Decimal("1000"),
                "cuda.shares": Decimal("4.0"),
            }
        )

        # When
        result = row.to_data(default_weight, available_slots)

        # Then - missing resources use default_weight
        assert result.data.spec.resource_weights["cpu"] == Decimal("1.0")  # default_weight
        assert result.data.spec.resource_weights["mem"] == Decimal("1.0")  # default_weight
        assert result.data.spec.resource_weights["cuda.shares"] == Decimal("0.1")  # explicit
        assert result.data.uses_default_resources == frozenset(["cpu", "mem"])


class TestUserFairShareRowToData:
    """Test UserFairShareRow.to_data() with resource weight merging."""

    def test_empty_resource_weights(self) -> None:
        """Scenario 2.5: User fair share with empty resource weights (all defaults)."""
        # Given
        row = UserFairShareRow(
            id=uuid.uuid4(),
            resource_group="default",
            user_uuid=uuid.uuid4(),
            project_id=uuid.uuid4(),
            domain_name="test-domain",
            weight=None,
            fair_share_factor=Decimal("1.0"),
            total_decayed_usage=ResourceSlot({}),
            resource_weights=ResourceSlot({}),  # All use defaults
            normalized_usage=Decimal("0.0"),
            last_calculated_at=datetime.now(UTC),
            lookback_start=date.today(),
            lookback_end=date.today(),
            half_life_days=7,
            lookback_days=28,
            decay_unit_days=1,
            scheduling_rank=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        default_weight = Decimal("1.0")
        available_slots = ResourceSlot({"cpu": Decimal("100"), "mem": Decimal("1000")})

        # When
        result = row.to_data(default_weight, available_slots)

        # Then - all missing resources use default_weight
        assert result.data.spec.resource_weights["cpu"] == Decimal("1.0")
        assert result.data.spec.resource_weights["mem"] == Decimal("1.0")
        assert result.data.uses_default_resources == frozenset(["cpu", "mem"])
        assert result.data.use_default is True


class TestResourceWeightMergingEdgeCases:
    """Test edge cases for resource weight merging."""

    def test_new_resource_type_fallback_to_one(self) -> None:
        """Test fallback to 1.0 for new resource types not in defaults."""
        # Given
        row = DomainFairShareRow(
            id=uuid.uuid4(),
            resource_group="default",
            domain_name="test-domain",
            weight=Decimal("1.0"),
            fair_share_factor=Decimal("1.0"),
            total_decayed_usage=ResourceSlot({}),
            resource_weights=ResourceSlot({}),
            normalized_usage=Decimal("0.0"),
            last_calculated_at=datetime.now(UTC),
            lookback_start=date.today(),
            lookback_end=date.today(),
            half_life_days=7,
            lookback_days=28,
            decay_unit_days=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        default_weight = Decimal("1.0")
        available_slots = ResourceSlot(
            {
                "cpu": Decimal("100"),
                "new.accelerator": Decimal("4"),  # New resource type
            }
        )

        # When
        result = row.to_data(default_weight, available_slots)

        # Then - all missing resources use default_weight
        assert result.data.spec.resource_weights["cpu"] == Decimal("1.0")
        assert result.data.spec.resource_weights["new.accelerator"] == Decimal("1.0")
        assert result.data.uses_default_resources == frozenset(
            ["cpu", "new.accelerator"]
        )

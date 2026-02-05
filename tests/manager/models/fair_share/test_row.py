"""Unit tests for Fair Share Row models."""

from __future__ import annotations

from decimal import Decimal

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.fair_share.row import _merge_resource_weights


class TestMergeResourceWeights:
    """Test _merge_resource_weights() helper function."""

    def test_all_explicit_weights(self) -> None:
        """Scenario 1.1: All resources have explicit weights configured."""
        # Given
        row_weights = ResourceSlot({
            "cpu": Decimal("2.0"),
            "mem": Decimal("0.5"),
            "cuda.device": Decimal("5.0"),
        })
        default_weight = Decimal("1.0")
        available_slots = ResourceSlot({
            "cpu": Decimal("100"),
            "mem": Decimal("1000"),
            "cuda.device": Decimal("8"),
        })

        # When
        merged, uses_default = _merge_resource_weights(row_weights, default_weight, available_slots)

        # Then
        assert merged["cpu"] == Decimal("2.0")
        assert merged["mem"] == Decimal("0.5")
        assert merged["cuda.device"] == Decimal("5.0")
        assert uses_default == frozenset()  # No defaults used

    def test_partial_explicit_weights(self) -> None:
        """Scenario 1.2: Some resources explicit, others use default_weight."""
        # Given
        row_weights = ResourceSlot({"cuda.device": Decimal("5.0")})
        default_weight = Decimal("1.0")
        available_slots = ResourceSlot({
            "cpu": Decimal("100"),
            "mem": Decimal("1000"),
            "cuda.device": Decimal("8"),
        })

        # When
        merged, uses_default = _merge_resource_weights(row_weights, default_weight, available_slots)

        # Then
        assert merged["cpu"] == Decimal("1.0")  # Uses default_weight
        assert merged["mem"] == Decimal("1.0")  # Uses default_weight
        assert merged["cuda.device"] == Decimal("5.0")  # Explicit
        assert uses_default == frozenset(["cpu", "mem"])

    def test_all_default_weights(self) -> None:
        """Scenario 1.3: All resources use default_weight."""
        # Given
        row_weights = ResourceSlot({})  # Empty
        default_weight = Decimal("1.0")
        available_slots = ResourceSlot({"cpu": Decimal("100"), "mem": Decimal("1000")})

        # When
        merged, uses_default = _merge_resource_weights(row_weights, default_weight, available_slots)

        # Then
        assert merged["cpu"] == Decimal("1.0")
        assert merged["mem"] == Decimal("1.0")
        assert uses_default == frozenset(["cpu", "mem"])

    def test_different_default_weight_value(self) -> None:
        """Scenario 1.4: Using different default_weight value (e.g., 2.0)."""
        # Given
        row_weights = ResourceSlot({})
        default_weight = Decimal("2.0")  # Different default
        available_slots = ResourceSlot({
            "cpu": Decimal("100"),
            "mem": Decimal("1000"),
            "new.accelerator": Decimal("4"),
        })

        # When
        merged, uses_default = _merge_resource_weights(row_weights, default_weight, available_slots)

        # Then
        assert merged["cpu"] == Decimal("2.0")  # All use default_weight
        assert merged["mem"] == Decimal("2.0")
        assert merged["new.accelerator"] == Decimal("2.0")
        assert uses_default == frozenset(["cpu", "mem", "new.accelerator"])

    def test_empty_available_slots(self) -> None:
        """Edge Case E.1: Empty available_slots."""
        # Given
        row_weights = ResourceSlot({"cpu": Decimal("2.0")})
        default_weight = Decimal("1.0")
        available_slots = ResourceSlot({})  # Empty cluster

        # When
        merged, uses_default = _merge_resource_weights(row_weights, default_weight, available_slots)

        # Then
        assert merged == ResourceSlot({})
        assert uses_default == frozenset()

    def test_mixed_explicit_and_default_weights(self) -> None:
        """Test mixed scenario with multiple resource types."""
        # Given
        row_weights = ResourceSlot({
            "cuda.device": Decimal("10.0"),
            "rocm.device": Decimal("8.0"),
        })
        default_weight = Decimal("1.0")
        available_slots = ResourceSlot({
            "cpu": Decimal("100"),
            "mem": Decimal("1000"),
            "cuda.device": Decimal("8"),
            "cuda.shares": Decimal("4.0"),
            "rocm.device": Decimal("8"),
        })

        # When
        merged, uses_default = _merge_resource_weights(row_weights, default_weight, available_slots)

        # Then
        # Explicit weights
        assert merged["cuda.device"] == Decimal("10.0")
        assert merged["rocm.device"] == Decimal("8.0")

        # Use default_weight (1.0) for missing resources
        assert merged["cpu"] == Decimal("1.0")
        assert merged["mem"] == Decimal("1.0")
        assert merged["cuda.shares"] == Decimal("1.0")

        # Check uses_default
        assert uses_default == frozenset(["cpu", "mem", "cuda.shares"])


class TestDomainFairShareRowToData:
    """Test DomainFairShareRow.to_data() with merged resource weights.

    Note: This requires database fixtures, so it's more of an integration test.
    We'll test this in integration tests instead.
    """

    pass  # Integration tests will cover this

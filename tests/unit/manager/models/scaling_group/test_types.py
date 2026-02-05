"""Tests for FairShareScalingGroupSpec Pydantic serialization."""

from __future__ import annotations

from decimal import Decimal

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.scaling_group.types import FairShareScalingGroupSpec


class TestFairShareScalingGroupSpec:
    """Test FairShareScalingGroupSpec Pydantic model serialization and deserialization."""

    def test_create_with_resource_slot(self) -> None:
        """Test creating FairShareScalingGroupSpec with ResourceSlot."""
        resource_weights = ResourceSlot({
            "cpu": Decimal("1.0"),
            "mem": Decimal("0.001"),
            "cuda.device": Decimal("10.0"),
        })

        spec = FairShareScalingGroupSpec(
            half_life_days=7,
            lookback_days=28,
            decay_unit_days=1,
            default_weight=Decimal("1.0"),
            resource_weights=resource_weights,
        )

        assert spec.half_life_days == 7
        assert spec.lookback_days == 28
        assert spec.decay_unit_days == 1
        assert spec.default_weight == Decimal("1.0")
        assert isinstance(spec.resource_weights, ResourceSlot)
        assert spec.resource_weights["cpu"] == Decimal("1.0")
        assert spec.resource_weights["mem"] == Decimal("0.001")
        assert spec.resource_weights["cuda.device"] == Decimal("10.0")

    def test_model_dump_json_mode(self) -> None:
        """Test model_dump with mode='json' properly serializes ResourceSlot."""
        resource_weights = ResourceSlot({
            "cpu": Decimal("1.0"),
            "mem": Decimal("0.001"),
            "cuda.device": Decimal("10.0"),
        })

        spec = FairShareScalingGroupSpec(
            half_life_days=7,
            lookback_days=28,
            decay_unit_days=1,
            default_weight=Decimal("1.0"),
            resource_weights=resource_weights,
        )

        # This should not raise PydanticSerializationError
        dumped = spec.model_dump(mode="json")

        assert isinstance(dumped, dict)
        assert dumped["half_life_days"] == 7
        assert dumped["lookback_days"] == 28
        assert dumped["decay_unit_days"] == 1
        assert dumped["default_weight"] == "1.0"
        assert isinstance(dumped["resource_weights"], dict)
        assert dumped["resource_weights"]["cpu"] == "1.0"
        assert dumped["resource_weights"]["mem"] == "0.001"
        assert dumped["resource_weights"]["cuda.device"] == "10.0"

    def test_model_validate_from_dict(self) -> None:
        """Test model_validate properly deserializes dict to ResourceSlot."""
        data = {
            "half_life_days": 7,
            "lookback_days": 28,
            "decay_unit_days": 1,
            "default_weight": "1.0",
            "resource_weights": {
                "cpu": "1.0",
                "mem": "0.001",
                "cuda.device": "10.0",
            },
        }

        spec = FairShareScalingGroupSpec.model_validate(data)

        assert spec.half_life_days == 7
        assert spec.lookback_days == 28
        assert spec.decay_unit_days == 1
        assert spec.default_weight == Decimal("1.0")
        assert isinstance(spec.resource_weights, ResourceSlot)
        assert spec.resource_weights["cpu"] == Decimal("1.0")
        assert spec.resource_weights["mem"] == Decimal("0.001")
        assert spec.resource_weights["cuda.device"] == Decimal("10.0")

    def test_roundtrip_serialization(self) -> None:
        """Test full roundtrip: create -> dump -> validate."""
        original = FairShareScalingGroupSpec(
            half_life_days=14,
            lookback_days=56,
            decay_unit_days=7,
            default_weight=Decimal("2.5"),
            resource_weights=ResourceSlot({
                "cpu": Decimal("1.5"),
                "mem": Decimal("0.002"),
                "cuda.device": Decimal("20.0"),
            }),
        )

        # Dump to JSON-serializable dict
        dumped = original.model_dump(mode="json")

        # Validate back from dict
        restored = FairShareScalingGroupSpec.model_validate(dumped)

        assert restored.half_life_days == original.half_life_days
        assert restored.lookback_days == original.lookback_days
        assert restored.decay_unit_days == original.decay_unit_days
        assert restored.default_weight == original.default_weight
        assert isinstance(restored.resource_weights, ResourceSlot)
        assert dict(restored.resource_weights) == dict(original.resource_weights)

    def test_default_empty_resource_weights(self) -> None:
        """Test default factory creates empty ResourceSlot."""
        spec = FairShareScalingGroupSpec()

        assert isinstance(spec.resource_weights, ResourceSlot)
        assert len(spec.resource_weights) == 0
        assert dict(spec.resource_weights) == {}

    def test_validate_resource_weights_from_empty_dict(self) -> None:
        """Test validator handles empty dict."""
        data = {
            "half_life_days": 7,
            "lookback_days": 28,
            "decay_unit_days": 1,
            "default_weight": "1.0",
            "resource_weights": {},
        }

        spec = FairShareScalingGroupSpec.model_validate(data)

        assert isinstance(spec.resource_weights, ResourceSlot)
        assert len(spec.resource_weights) == 0

    def test_validate_resource_weights_preserves_existing_resource_slot(self) -> None:
        """Test validator preserves ResourceSlot if already correct type."""
        resource_slot = ResourceSlot({"cpu": Decimal("1.0")})

        data = {
            "half_life_days": 7,
            "lookback_days": 28,
            "decay_unit_days": 1,
            "default_weight": "1.0",
            "resource_weights": resource_slot,
        }

        spec = FairShareScalingGroupSpec.model_validate(data)

        assert spec.resource_weights is resource_slot

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from ai.backend.common.types import ResourceSlot

__all__ = ("FairShareScalingGroupSpec",)


class FairShareScalingGroupSpec(BaseModel):
    """Fair Share calculation configuration for a Resource Group.

    Used for Fair Share metric calculation regardless of the scheduler type.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    half_life_days: int = 7
    """Half-life for exponential decay in days."""

    lookback_days: int = 28
    """Total lookback period in days for usage aggregation."""

    decay_unit_days: int = 1
    """Granularity of decay buckets in days."""

    default_weight: Decimal = Decimal("1.0")
    """Default weight for entities without explicit weight in this scaling group."""

    resource_weights: ResourceSlot = Field(default_factory=ResourceSlot)
    """Weights for each resource type when calculating normalized usage.

    If a resource type is not specified, default weight (1.0) is used.
    Example: ResourceSlot({"cpu": 1.0, "mem": 0.001, "cuda.device": 10.0})
    """

    @field_serializer("resource_weights", mode="plain")
    def serialize_resource_weights(self, value: ResourceSlot) -> dict[str, Any]:
        """Serialize ResourceSlot to dict for JSON compatibility."""
        return {k: str(v) for k, v in value.items()}

    @field_validator("resource_weights", mode="before")
    @classmethod
    def validate_resource_weights(cls, value: Any) -> ResourceSlot:
        """Deserialize dict to ResourceSlot.

        Converts string values to Decimal to avoid BinarySize parsing issues.
        """
        if isinstance(value, ResourceSlot):
            return value
        if isinstance(value, dict):
            # Convert string values to Decimal to bypass BinarySize parsing
            converted = {k: Decimal(v) if isinstance(v, str) else v for k, v in value.items()}
            return ResourceSlot(converted)
        return ResourceSlot()

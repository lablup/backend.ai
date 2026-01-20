from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict

__all__ = ("FairShareScalingGroupSpec",)


class FairShareScalingGroupSpec(BaseModel):
    """Fair Share calculation configuration for a Resource Group.

    Used for Fair Share metric calculation regardless of the scheduler type.
    """

    model_config = ConfigDict(frozen=True)

    half_life_days: int = 7
    """Half-life for exponential decay in days."""

    lookback_days: int = 28
    """Total lookback period in days for usage aggregation."""

    decay_unit_days: int = 1
    """Granularity of decay buckets in days."""

    default_weight: Decimal = Decimal("1.0")
    """Default weight for users in this scaling group."""

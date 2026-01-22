"""Common GQL types for Fair Share module."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal

import strawberry


@strawberry.type(
    name="ResourceSlotEntry",
    description=(
        "Added in 26.1.0. A single entry representing one resource type and its allocated quantity. "
        "Resource types include compute resources (cpu, mem), accelerators (cuda.shares, cuda.device, "
        "rocm.device), and custom resources defined by plugins."
    ),
)
class ResourceSlotEntryGQL:
    """Single resource slot entry with resource type and quantity."""

    resource_type: str = strawberry.field(
        description=(
            "Resource type identifier. Common types include: "
            "'cpu' (CPU cores), 'mem' (memory in bytes), "
            "'cuda.shares' (fractional GPU), 'cuda.device' (whole GPU devices), "
            "'rocm.device' (AMD GPU devices). Custom accelerator plugins may define additional types."
        )
    )
    quantity: Decimal = strawberry.field(
        description=(
            "Quantity of the resource. "
            "For 'cpu': number of cores (e.g., 2.0, 0.5). "
            "For 'mem': bytes (e.g., 4294967296 for 4GB). "
            "For accelerators: device count or share fraction."
        )
    )


@strawberry.input(
    name="ResourceWeightEntryInput",
    description=(
        "Added in 26.1.0. Input for a single resource weight entry. "
        "Specifies how much a resource type contributes to fair share calculations."
    ),
)
class ResourceWeightEntryInputGQL:
    """Input for single resource weight entry."""

    resource_type: str = strawberry.field(
        description=(
            "Resource type identifier (e.g., 'cpu', 'mem', 'cuda.shares'). "
            "Must match the resource types used in the cluster."
        )
    )
    weight: Decimal | None = strawberry.field(
        default=None,
        description=(
            "Weight multiplier for this resource type in fair share calculations. "
            "Higher weight means this resource contributes more to the normalized usage. "
            "Set to null to remove this resource type (revert to default weight 1.0). "
            "Example: 0.001 for memory (bytes) to normalize against CPU cores."
        ),
    )


@strawberry.type(
    name="ResourceSlot",
    description=(
        "Added in 26.1.0. A collection of compute resource allocations. "
        "Represents the resources consumed, allocated, or available for a workload. "
        "Each entry specifies a resource type and its quantity."
    ),
)
class ResourceSlotGQL:
    """Resource slot containing multiple resource type entries."""

    entries: list[ResourceSlotEntryGQL] = strawberry.field(
        description=(
            "List of resource allocations. Each entry contains a resource type and quantity pair. "
            "The list may include cpu, mem, and various accelerator types depending on the cluster configuration."
        )
    )

    @classmethod
    def from_resource_slot(cls, slot: Mapping[str, Decimal | str]) -> ResourceSlotGQL:
        """Convert a ResourceSlot or dict-based resource slot to GraphQL type."""
        entries = [
            ResourceSlotEntryGQL(
                resource_type=k,
                quantity=Decimal(v) if isinstance(v, str) else v,
            )
            for k, v in slot.items()
        ]
        return cls(entries=entries)


@strawberry.type(
    name="FairShareSpec",
    description=(
        "Added in 26.1.0. Configuration parameters that control how fair share factors are calculated. "
        "These parameters determine the decay rate, lookback period, and resource weighting for usage aggregation."
    ),
)
class FairShareSpecGQL:
    """Specification parameters for fair share calculation."""

    weight: Decimal | None = strawberry.field(
        description=(
            "Base weight multiplier for this entity. Higher weight values result in higher scheduling priority. "
            "Null means using resource group's default_weight."
        )
    )
    half_life_days: int = strawberry.field(
        description=(
            "Half-life for exponential decay in days. Determines how quickly historical usage loses significance. "
            "For example, with half_life_days=7, usage from 7 days ago contributes half as much as today's usage."
        )
    )
    lookback_days: int = strawberry.field(
        description=(
            "Total lookback period in days for usage aggregation. Only usage within this window is considered. "
            "Typical values range from 7 to 30 days depending on scheduling policy."
        )
    )
    decay_unit_days: int = strawberry.field(
        description=(
            "Granularity of decay buckets in days. Usage is aggregated into buckets of this size. "
            "Smaller values provide more precision but require more storage. Typically 1 day."
        )
    )
    resource_weights: ResourceSlotGQL = strawberry.field(
        description=(
            "Weights for each resource type when calculating normalized usage. "
            "Allows different resources to contribute differently to the fair share calculation. "
            "For example, GPU usage might be weighted higher than CPU usage."
        )
    )


@strawberry.type(
    name="FairShareCalculationSnapshot",
    description=(
        "Added in 26.1.0. Snapshot of the most recent fair share calculation results. "
        "Contains the computed fair share factor and the intermediate values used in the calculation."
    ),
)
class FairShareCalculationSnapshotGQL:
    """Contains the computed values and the time window used for calculation."""

    fair_share_factor: Decimal = strawberry.field(
        description=(
            "Computed fair share factor ranging from 0 to 1. "
            "Higher values indicate more entitlement to resources (less historical usage relative to others). "
            "Used by the scheduler to prioritize workloads - entities with higher factors get scheduled first."
        )
    )
    total_decayed_usage: ResourceSlotGQL = strawberry.field(
        description=(
            "Sum of exponentially decayed historical usage across the lookback period. "
            "Recent usage contributes more than older usage based on the half-life decay function. "
            "This is the raw usage data before normalization."
        )
    )
    normalized_usage: Decimal = strawberry.field(
        description=(
            "Single scalar value representing weighted resource consumption. "
            "Computed by applying resource weights to the decayed usage and summing. "
            "Used to compare usage across entities with different resource consumption patterns."
        )
    )
    lookback_start: date = strawberry.field(
        description=(
            "Start date of the lookback window used in this calculation (inclusive). "
            "Usage before this date is not considered in the fair share factor computation."
        )
    )
    lookback_end: date = strawberry.field(
        description=(
            "End date of the lookback window used in this calculation (inclusive). "
            "Typically the current date or the date of the last calculation."
        )
    )
    last_calculated_at: datetime = strawberry.field(
        description=(
            "Timestamp when this fair share calculation was performed. "
            "Fair share factors are recalculated periodically by the scheduler."
        )
    )

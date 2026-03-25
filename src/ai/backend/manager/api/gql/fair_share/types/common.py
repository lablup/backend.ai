"""Common GQL types for Fair Share module."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from ai.backend.common.dto.manager.v2.fair_share.types import (
    FairShareCalculationSnapshotInfo,
    FairShareSpecInfo,
    ResourceSlotEntryInfo,
    ResourceSlotInfo,
    ResourceWeightEntryInfo,
)
from ai.backend.common.dto.manager.v2.resource_group.request import (
    ResourceWeightEntryInput as ResourceWeightEntryInputDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_added_field,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "A single entry representing one resource type and its allocated quantity. "
            "Resource types include compute resources (cpu, mem), accelerators (cuda.shares, cuda.device, "
            "rocm.device), and custom resources defined by plugins."
        ),
    ),
    model=ResourceSlotEntryInfo,
    name="ResourceSlotEntry",
)
class ResourceSlotEntryGQL(PydanticOutputMixin[ResourceSlotEntryInfo]):
    """Single resource slot entry with resource type and quantity."""

    resource_type: str = gql_field(
        description="Resource type identifier. Common types include: 'cpu' (CPU cores), 'mem' (memory in bytes), 'cuda.shares' (fractional GPU), 'cuda.device' (whole GPU devices), 'rocm.device' (AMD GPU devices). Custom accelerator plugins may define additional types."
    )
    quantity: Decimal = gql_field(
        description="Quantity of the resource. For 'cpu': number of cores (e.g., 2.0, 0.5). For 'mem': bytes (e.g., 4294967296 for 4GB). For accelerators: device count or share fraction."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for a single resource weight entry. Specifies how much a resource type contributes to fair share calculations.",
        added_version="26.1.0",
    ),
    name="ResourceWeightEntryInput",
)
class ResourceWeightEntryInputGQL(PydanticInputMixin[ResourceWeightEntryInputDTO]):
    """Input for single resource weight entry."""

    resource_type: str = gql_field(
        description="Resource type identifier (e.g., 'cpu', 'mem', 'cuda.shares'). Must match the resource types used in the cluster."
    )
    weight: Decimal | None = gql_field(
        description="Weight multiplier for this resource type in fair share calculations. Higher weight means this resource contributes more to the normalized usage. Set to null to remove this resource type (revert to default weight 1.0). Example: 0.001 for memory (bytes) to normalize against CPU cores.",
        default=None,
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "A collection of compute resource allocations. "
            "Represents the resources consumed, allocated, or available for a workload. "
            "Each entry specifies a resource type and its quantity."
        ),
    ),
    model=ResourceSlotInfo,
    name="ResourceSlot",
)
class ResourceSlotGQL(PydanticOutputMixin[ResourceSlotInfo]):
    """Resource slot containing multiple resource type entries."""

    entries: list[ResourceSlotEntryGQL] = gql_field(
        description="List of resource allocations. Each entry contains a resource type and quantity pair. The list may include cpu, mem, and various accelerator types depending on the cluster configuration."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Resource weight with default indicator. "
            "Shows whether this resource type's weight was explicitly set or uses default."
        ),
    ),
    model=ResourceWeightEntryInfo,
    name="ResourceWeightEntry",
)
class ResourceWeightEntryGQL(PydanticOutputMixin[ResourceWeightEntryInfo]):
    """Individual resource type weight with default usage flag."""

    resource_type: str = gql_field(
        description="Resource type identifier (e.g., 'cpu', 'mem', 'cuda.device'). Matches the resource types available in the scaling group."
    )

    weight: Decimal = gql_field(
        description="Weight multiplier for this resource type in fair share calculations. Higher weight means more contribution to normalized usage."
    )

    uses_default: bool = gql_field(
        description="Whether this resource uses the resource group's default weight. True means no explicit weight was configured for this type."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Configuration parameters that control how fair share factors are calculated. "
            "These parameters determine the decay rate, lookback period, and resource weighting for usage aggregation."
        ),
    ),
    model=FairShareSpecInfo,
    name="FairShareSpec",
)
class FairShareSpecGQL(PydanticOutputMixin[FairShareSpecInfo]):
    """Specification parameters for fair share calculation."""

    weight: Decimal = gql_field(
        description="Base weight multiplier for this entity. Higher weight values result in higher scheduling priority. This is the effective weight - either the explicitly set value or the resource group's default_weight."
    )
    uses_default: bool = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.1.0",
            description="Whether this entity uses the resource group's default_weight. True means no explicit weight was set and the default is being used. False means an explicit weight value was configured for this entity.",
        )
    )
    half_life_days: int = gql_field(
        description="Half-life for exponential decay in days. Determines how quickly historical usage loses significance. For example, with half_life_days=7, usage from 7 days ago contributes half as much as today's usage."
    )
    lookback_days: int = gql_field(
        description="Total lookback period in days for usage aggregation. Only usage within this window is considered. Typical values range from 7 to 30 days depending on scheduling policy."
    )
    decay_unit_days: int = gql_field(
        description="Granularity of decay buckets in days. Usage is aggregated into buckets of this size. Smaller values provide more precision but require more storage. Typically 1 day."
    )
    resource_weights: list[ResourceWeightEntryGQL] = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.2.0",
            description="Weights for each resource type with default indicators. Shows which resources use explicit vs default weights. Allows different resources to contribute differently to the fair share calculation. For example, GPU usage might be weighted higher than CPU usage.",
        )
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Snapshot of the most recent fair share calculation results. "
            "Contains the computed fair share factor and the intermediate values used in the calculation."
        ),
    ),
    model=FairShareCalculationSnapshotInfo,
    name="FairShareCalculationSnapshot",
)
class FairShareCalculationSnapshotGQL(PydanticOutputMixin[FairShareCalculationSnapshotInfo]):
    """Contains the computed values and the time window used for calculation."""

    fair_share_factor: Decimal = gql_field(
        description="Computed fair share factor ranging from 0 to 1. Higher values indicate more entitlement to resources (less historical usage relative to others). Used by the scheduler to prioritize workloads - entities with higher factors get scheduled first."
    )
    total_decayed_usage: ResourceSlotGQL = gql_field(
        description="Sum of exponentially decayed historical usage across the lookback period. Recent usage contributes more than older usage based on the half-life decay function. This is the raw usage data before normalization."
    )
    normalized_usage: Decimal = gql_field(
        description="Single scalar value representing weighted resource consumption. Computed by applying resource weights to the decayed usage and summing. Used to compare usage across entities with different resource consumption patterns."
    )
    lookback_start: date = gql_field(
        description="Start date of the lookback window used in this calculation (inclusive). Usage before this date is not considered in the fair share factor computation."
    )
    lookback_end: date = gql_field(
        description="End date of the lookback window used in this calculation (inclusive). Typically the current date or the date of the last calculation."
    )
    last_calculated_at: datetime = gql_field(
        description="Timestamp when this fair share calculation was performed. Fair share factors are recalculated periodically by the scheduler."
    )

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.2.0",
            description="Average daily decayed resource usage during the lookback period. Calculated as total_decayed_usage divided by lookback duration in days. For each resource type, this represents the average decayed amount consumed per day. Units match the resource type (e.g., CPU cores, memory bytes).",
        )
    )  # type: ignore[misc]
    def average_daily_decayed_usage(self) -> ResourceSlotGQL:
        from ai.backend.manager.api.gql.resource_usage.types.common_calculations import (
            calculate_average_daily_usage,
        )

        return calculate_average_daily_usage(
            self.total_decayed_usage,
            self.lookback_start,
            self.lookback_end,
        )

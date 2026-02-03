"""Data classes for Fair Share domain."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from ai.backend.common.types import ResourceSlot


@dataclass(frozen=True)
class ProjectUserIds:
    """A project with its associated user IDs for batch fair share lookup."""

    project_id: uuid.UUID
    user_ids: frozenset[uuid.UUID]


@dataclass(frozen=True)
class UserProjectKey:
    """Key identifying a user within a project for fair share tracking."""

    user_uuid: uuid.UUID
    project_id: uuid.UUID


@dataclass(frozen=True)
class FairShareSpec:
    """Specification parameters for fair share calculation.

    These values determine how fair share factor is computed.
    """

    weight: Decimal | None
    """Base weight for this entity (higher weight = higher priority).
    None means use resource group's default_weight."""

    half_life_days: int
    """Half-life for exponential decay in days."""

    lookback_days: int
    """Total lookback period in days for usage aggregation."""

    decay_unit_days: int
    """Granularity of decay buckets in days."""

    resource_weights: ResourceSlot
    """Weights for each resource type when calculating normalized usage."""


@dataclass(frozen=True)
class FairShareCalculationSnapshot:
    """Snapshot of the most recent fair share calculation.

    Contains the computed values and the time window used for calculation.
    """

    fair_share_factor: Decimal
    """Computed fair share factor (0-1 range, higher = more entitled)."""

    total_decayed_usage: ResourceSlot
    """Sum of decayed historical usage across all resource types."""

    normalized_usage: Decimal
    """Single scalar representing weighted resource consumption."""

    lookback_start: date
    """Start date of the lookback window used in calculation."""

    lookback_end: date
    """End date of the lookback window used in calculation."""

    last_calculated_at: datetime
    """Timestamp when this calculation was performed."""


@dataclass(frozen=True)
class FairShareMetadata:
    """Audit metadata for fair share entities."""

    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DomainFairShareData:
    """Domain-level fair share data."""

    id: uuid.UUID
    resource_group: str
    domain_name: str
    spec: FairShareSpec
    calculation_snapshot: FairShareCalculationSnapshot
    metadata: FairShareMetadata
    default_weight: Decimal
    """Resource group's default weight for entities without explicit weight."""
    uses_default: bool = False
    """True if this data was generated from defaults (no fair share record exists)."""


@dataclass(frozen=True)
class ProjectFairShareData:
    """Project-level fair share data."""

    id: uuid.UUID
    resource_group: str
    project_id: uuid.UUID
    domain_name: str
    spec: FairShareSpec
    calculation_snapshot: FairShareCalculationSnapshot
    metadata: FairShareMetadata
    default_weight: Decimal
    """Resource group's default weight for entities without explicit weight."""
    uses_default: bool = False
    """True if this data was generated from defaults (no fair share record exists)."""


@dataclass(frozen=True)
class UserFairShareData:
    """User-level fair share data."""

    id: uuid.UUID
    resource_group: str
    user_uuid: uuid.UUID
    project_id: uuid.UUID
    domain_name: str
    spec: FairShareSpec
    calculation_snapshot: FairShareCalculationSnapshot
    metadata: FairShareMetadata
    default_weight: Decimal
    """Resource group's default weight for entities without explicit weight."""
    uses_default: bool = False
    """True if this data was generated from defaults (no fair share record exists)."""
    scheduling_rank: int | None = None
    """Computed scheduling priority rank. Lower value = higher priority.
    None means rank calculation has not been performed yet."""


@dataclass(frozen=True)
class UserFairShareFactors:
    """Combined fair share factors for a user across all hierarchy levels.

    Used for sorting workloads by fair share priority.
    Higher factors = higher priority.
    """

    user_uuid: uuid.UUID
    project_id: uuid.UUID
    domain_name: str
    domain_factor: Decimal
    project_factor: Decimal
    user_factor: Decimal

    def sort_key(self) -> tuple[Decimal, Decimal, Decimal]:
        """Return a tuple for sorting (higher factor = higher priority).

        Returns negated values since Python sorts ascending by default.
        """
        return (-self.domain_factor, -self.project_factor, -self.user_factor)


@dataclass(frozen=True)
class DomainFairShareSearchResult:
    """Search result with pagination info for domain fair shares."""

    items: list[DomainFairShareData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class ProjectFairShareSearchResult:
    """Search result with pagination info for project fair shares."""

    items: list[ProjectFairShareData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class UserFairShareSearchResult:
    """Search result with pagination info for user fair shares."""

    items: list[UserFairShareData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


# ==================== Batched Read Results ====================


@dataclass(frozen=True)
class FairSharesByLevel:
    """Fair share records grouped by hierarchy level.

    Used for factor calculation to get current weights and configurations.
    """

    domain: Mapping[str, DomainFairShareData]
    """Domain fair shares keyed by domain_name."""

    project: Mapping[uuid.UUID, ProjectFairShareData]
    """Project fair shares keyed by project_id."""

    user: Mapping[UserProjectKey, UserFairShareData]
    """User fair shares keyed by UserProjectKey."""


@dataclass(frozen=True)
class RawUsageBucketsByLevel:
    """Raw usage buckets grouped by hierarchy level before decay is applied.

    Contains per-date ResourceSlot buckets for each entity in the lookback window.
    The Calculator is responsible for applying time decay to these raw buckets.
    """

    domain: Mapping[str, Mapping[date, ResourceSlot]]
    """Raw usage buckets by domain_name -> date -> usage."""

    project: Mapping[uuid.UUID, Mapping[date, ResourceSlot]]
    """Raw usage buckets by project_id -> date -> usage."""

    user: Mapping[UserProjectKey, Mapping[date, ResourceSlot]]
    """Raw usage buckets by UserProjectKey -> date -> usage."""

    def is_empty(self) -> bool:
        """Check if there are no usage buckets at any level."""
        return not self.domain and not self.project and not self.user


@dataclass(frozen=True)
class FairShareCalculationContext:
    """All data needed for fair share factor calculation.

    Combines fair share records (for weights) and raw usage buckets.
    This is the result of batched DB reads.
    The Calculator applies time decay to raw_usage_buckets internally.
    """

    fair_shares: FairSharesByLevel
    """Current fair share records with weights."""

    raw_usage_buckets: RawUsageBucketsByLevel
    """Raw usage buckets from lookback window (decay not applied yet)."""

    half_life_days: int
    """Half-life for exponential decay in days."""

    lookback_days: int
    """Number of days in lookback window."""

    default_weight: Decimal
    """Default weight for entities without explicit weight."""

    resource_weights: ResourceSlot
    """Default resource weights for normalized usage calculation."""

    cluster_capacity: ResourceSlot
    """Total available slots from all ALIVE schedulable agents in the scaling group.
    Used to normalize usage: usage[r] / (capacity[r] * lookback_days * SECONDS_PER_DAY).
    """

    today: date
    """Current date for decay calculation."""

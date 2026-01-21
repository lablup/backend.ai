"""Data classes for Fair Share domain."""

from __future__ import annotations

import uuid
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
class FairShareSpec:
    """Specification parameters for fair share calculation.

    These values determine how fair share factor is computed.
    """

    weight: Decimal
    """Base weight for this entity (higher weight = higher priority)."""

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

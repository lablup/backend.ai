"""Creator specs for Fair Share repository INSERT operations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class DomainFairShareCreatorSpec(CreatorSpec[DomainFairShareRow]):
    """Creator spec for DomainFairShareRow.

    Only identity fields are required. Spec fields use Row defaults if not provided.
    """

    # Identity (required)
    resource_group: str
    domain_name: str

    # Spec (optional - uses Row defaults if None)
    weight: Decimal | None = None
    half_life_days: int | None = None
    lookback_days: int | None = None
    decay_unit_days: int | None = None
    resource_weights: ResourceSlot | None = None

    @override
    def build_row(self) -> DomainFairShareRow:
        row = DomainFairShareRow(
            resource_group=self.resource_group,
            domain_name=self.domain_name,
        )
        if self.weight is not None:
            row.weight = self.weight
        if self.half_life_days is not None:
            row.half_life_days = self.half_life_days
        if self.lookback_days is not None:
            row.lookback_days = self.lookback_days
        if self.decay_unit_days is not None:
            row.decay_unit_days = self.decay_unit_days
        if self.resource_weights is not None:
            row.resource_weights = self.resource_weights
        return row


@dataclass
class ProjectFairShareCreatorSpec(CreatorSpec[ProjectFairShareRow]):
    """Creator spec for ProjectFairShareRow.

    Only identity fields are required. Spec fields use Row defaults if not provided.
    """

    # Identity (required)
    resource_group: str
    project_id: uuid.UUID
    domain_name: str

    # Spec (optional - uses Row defaults if None)
    weight: Decimal | None = None
    half_life_days: int | None = None
    lookback_days: int | None = None
    decay_unit_days: int | None = None
    resource_weights: ResourceSlot | None = None

    @override
    def build_row(self) -> ProjectFairShareRow:
        row = ProjectFairShareRow(
            resource_group=self.resource_group,
            project_id=self.project_id,
            domain_name=self.domain_name,
        )
        if self.weight is not None:
            row.weight = self.weight
        if self.half_life_days is not None:
            row.half_life_days = self.half_life_days
        if self.lookback_days is not None:
            row.lookback_days = self.lookback_days
        if self.decay_unit_days is not None:
            row.decay_unit_days = self.decay_unit_days
        if self.resource_weights is not None:
            row.resource_weights = self.resource_weights
        return row


@dataclass
class UserFairShareCreatorSpec(CreatorSpec[UserFairShareRow]):
    """Creator spec for UserFairShareRow.

    Only identity fields are required. Spec fields use Row defaults if not provided.
    """

    # Identity (required)
    resource_group: str
    user_uuid: uuid.UUID
    project_id: uuid.UUID
    domain_name: str

    # Spec (optional - uses Row defaults if None)
    weight: Decimal | None = None
    half_life_days: int | None = None
    lookback_days: int | None = None
    decay_unit_days: int | None = None
    resource_weights: ResourceSlot | None = None

    @override
    def build_row(self) -> UserFairShareRow:
        row = UserFairShareRow(
            resource_group=self.resource_group,
            user_uuid=self.user_uuid,
            project_id=self.project_id,
            domain_name=self.domain_name,
        )
        if self.weight is not None:
            row.weight = self.weight
        if self.half_life_days is not None:
            row.half_life_days = self.half_life_days
        if self.lookback_days is not None:
            row.lookback_days = self.lookback_days
        if self.decay_unit_days is not None:
            row.decay_unit_days = self.decay_unit_days
        if self.resource_weights is not None:
            row.resource_weights = self.resource_weights
        return row

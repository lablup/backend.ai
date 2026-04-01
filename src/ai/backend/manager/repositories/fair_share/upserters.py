"""Upserter specs for Fair Share repository upsert (INSERT ON CONFLICT UPDATE) operations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.repositories.base import UpserterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class DomainFairShareUpserterSpec(UpserterSpec[DomainFairShareRow]):
    """Upserter spec for DomainFairShareRow.

    Unique constraint: (resource_group, domain_name)

    - Identity fields are required (for unique constraint)
    - Spec fields use Row defaults on INSERT if NOP
    - Calculation fields are only updated if UPDATE
    """

    # Identity (required)
    resource_group: str
    domain_name: str

    # Spec (uses Row defaults on INSERT if NOP)
    # weight uses TriState to support NULLIFY (set to None means use resource group's default_weight)
    weight: TriState[Decimal] = field(default_factory=TriState.nop)
    half_life_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    lookback_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    decay_unit_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    resource_weights: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)

    # Calculation snapshot (OptionalState - for UPDATE only)
    fair_share_factor: OptionalState[Decimal] = field(default_factory=OptionalState.nop)
    total_decayed_usage: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)
    normalized_usage: OptionalState[Decimal] = field(default_factory=OptionalState.nop)
    lookback_start: OptionalState[date] = field(default_factory=OptionalState.nop)
    lookback_end: OptionalState[date] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[DomainFairShareRow]:
        return DomainFairShareRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {
            "resource_group": self.resource_group,
            "domain_name": self.domain_name,
        }
        # Spec fields
        self.weight.update_dict(values, "weight")
        self.half_life_days.update_dict(values, "half_life_days")
        self.lookback_days.update_dict(values, "lookback_days")
        self.decay_unit_days.update_dict(values, "decay_unit_days")
        self.resource_weights.update_dict(values, "resource_weights")
        # Calculation fields
        self.fair_share_factor.update_dict(values, "fair_share_factor")
        self.total_decayed_usage.update_dict(values, "total_decayed_usage")
        self.normalized_usage.update_dict(values, "normalized_usage")
        self.lookback_start.update_dict(values, "lookback_start")
        self.lookback_end.update_dict(values, "lookback_end")
        return values

    @override
    def build_update_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        # Spec fields (weight can be updated via mutation)
        self.weight.update_dict(values, "weight")
        # Calculation fields
        self.fair_share_factor.update_dict(values, "fair_share_factor")
        self.total_decayed_usage.update_dict(values, "total_decayed_usage")
        self.normalized_usage.update_dict(values, "normalized_usage")
        self.resource_weights.update_dict(values, "resource_weights")
        self.lookback_start.update_dict(values, "lookback_start")
        self.lookback_end.update_dict(values, "lookback_end")
        return values


@dataclass
class DomainFairShareBulkWeightUpserterSpec(UpserterSpec[DomainFairShareRow]):
    """Simplified upserter spec for bulk weight updates on DomainFairShareRow.

    Used with BulkUpserter for updating weights across multiple domains.
    Has fixed update column (weight only) to ensure consistent bulk operations.
    """

    resource_group: str
    domain_name: str
    weight: Decimal | None  # None means use resource group's default_weight

    @property
    @override
    def row_class(self) -> type[DomainFairShareRow]:
        return DomainFairShareRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "resource_group": self.resource_group,
            "domain_name": self.domain_name,
            "weight": self.weight,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"weight": self.weight}


@dataclass
class ProjectFairShareUpserterSpec(UpserterSpec[ProjectFairShareRow]):
    """Upserter spec for ProjectFairShareRow.

    Unique constraint: (resource_group, project_id)

    - Identity fields are required (for unique constraint)
    - Spec fields use Row defaults on INSERT if NOP
    - Calculation fields are only updated if UPDATE
    """

    # Identity (required)
    resource_group: str
    project_id: uuid.UUID
    domain_name: str

    # Spec (uses Row defaults on INSERT if NOP)
    # weight uses TriState to support NULLIFY (set to None means use resource group's default_weight)
    weight: TriState[Decimal] = field(default_factory=TriState.nop)
    half_life_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    lookback_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    decay_unit_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    resource_weights: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)

    # Calculation snapshot (OptionalState - for UPDATE only)
    fair_share_factor: OptionalState[Decimal] = field(default_factory=OptionalState.nop)
    total_decayed_usage: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)
    normalized_usage: OptionalState[Decimal] = field(default_factory=OptionalState.nop)
    lookback_start: OptionalState[date] = field(default_factory=OptionalState.nop)
    lookback_end: OptionalState[date] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[ProjectFairShareRow]:
        return ProjectFairShareRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {
            "resource_group": self.resource_group,
            "project_id": self.project_id,
            "domain_name": self.domain_name,
        }
        # Spec fields
        self.weight.update_dict(values, "weight")
        self.half_life_days.update_dict(values, "half_life_days")
        self.lookback_days.update_dict(values, "lookback_days")
        self.decay_unit_days.update_dict(values, "decay_unit_days")
        self.resource_weights.update_dict(values, "resource_weights")
        # Calculation fields
        self.fair_share_factor.update_dict(values, "fair_share_factor")
        self.total_decayed_usage.update_dict(values, "total_decayed_usage")
        self.normalized_usage.update_dict(values, "normalized_usage")
        self.lookback_start.update_dict(values, "lookback_start")
        self.lookback_end.update_dict(values, "lookback_end")
        return values

    @override
    def build_update_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        # Spec fields (weight can be updated via mutation)
        self.weight.update_dict(values, "weight")
        # Calculation fields
        self.fair_share_factor.update_dict(values, "fair_share_factor")
        self.total_decayed_usage.update_dict(values, "total_decayed_usage")
        self.normalized_usage.update_dict(values, "normalized_usage")
        self.resource_weights.update_dict(values, "resource_weights")
        self.lookback_start.update_dict(values, "lookback_start")
        self.lookback_end.update_dict(values, "lookback_end")
        return values


@dataclass
class ProjectFairShareBulkWeightUpserterSpec(UpserterSpec[ProjectFairShareRow]):
    """Simplified upserter spec for bulk weight updates on ProjectFairShareRow.

    Used with BulkUpserter for updating weights across multiple projects.
    Has fixed update column (weight only) to ensure consistent bulk operations.
    """

    resource_group: str
    project_id: uuid.UUID
    domain_name: str
    weight: Decimal | None  # None means use resource group's default_weight

    @property
    @override
    def row_class(self) -> type[ProjectFairShareRow]:
        return ProjectFairShareRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "resource_group": self.resource_group,
            "project_id": self.project_id,
            "domain_name": self.domain_name,
            "weight": self.weight,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"weight": self.weight}


@dataclass
class UserFairShareUpserterSpec(UpserterSpec[UserFairShareRow]):
    """Upserter spec for UserFairShareRow.

    Unique constraint: (resource_group, user_uuid, project_id)

    - Identity fields are required (for unique constraint)
    - Spec fields use Row defaults on INSERT if NOP
    - Calculation fields are only updated if UPDATE
    """

    # Identity (required)
    resource_group: str
    user_uuid: uuid.UUID
    project_id: uuid.UUID
    domain_name: str

    # Spec (uses Row defaults on INSERT if NOP)
    # weight uses TriState to support NULLIFY (set to None means use resource group's default_weight)
    weight: TriState[Decimal] = field(default_factory=TriState.nop)
    half_life_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    lookback_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    decay_unit_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    resource_weights: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)

    # Calculation snapshot (OptionalState - for UPDATE only)
    fair_share_factor: OptionalState[Decimal] = field(default_factory=OptionalState.nop)
    total_decayed_usage: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)
    normalized_usage: OptionalState[Decimal] = field(default_factory=OptionalState.nop)
    lookback_start: OptionalState[date] = field(default_factory=OptionalState.nop)
    lookback_end: OptionalState[date] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[UserFairShareRow]:
        return UserFairShareRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {
            "resource_group": self.resource_group,
            "user_uuid": self.user_uuid,
            "project_id": self.project_id,
            "domain_name": self.domain_name,
        }
        # Spec fields
        self.weight.update_dict(values, "weight")
        self.half_life_days.update_dict(values, "half_life_days")
        self.lookback_days.update_dict(values, "lookback_days")
        self.decay_unit_days.update_dict(values, "decay_unit_days")
        self.resource_weights.update_dict(values, "resource_weights")
        # Calculation fields
        self.fair_share_factor.update_dict(values, "fair_share_factor")
        self.total_decayed_usage.update_dict(values, "total_decayed_usage")
        self.normalized_usage.update_dict(values, "normalized_usage")
        self.lookback_start.update_dict(values, "lookback_start")
        self.lookback_end.update_dict(values, "lookback_end")
        return values

    @override
    def build_update_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        # Spec fields (weight can be updated via mutation)
        self.weight.update_dict(values, "weight")
        # Calculation fields
        self.fair_share_factor.update_dict(values, "fair_share_factor")
        self.total_decayed_usage.update_dict(values, "total_decayed_usage")
        self.normalized_usage.update_dict(values, "normalized_usage")
        self.resource_weights.update_dict(values, "resource_weights")
        self.lookback_start.update_dict(values, "lookback_start")
        self.lookback_end.update_dict(values, "lookback_end")
        return values


@dataclass
class UserFairShareBulkWeightUpserterSpec(UpserterSpec[UserFairShareRow]):
    """Simplified upserter spec for bulk weight updates on UserFairShareRow.

    Used with BulkUpserter for updating weights across multiple users.
    Has fixed update column (weight only) to ensure consistent bulk operations.
    """

    resource_group: str
    user_uuid: uuid.UUID
    project_id: uuid.UUID
    domain_name: str
    weight: Decimal | None  # None means use resource group's default_weight

    @property
    @override
    def row_class(self) -> type[UserFairShareRow]:
        return UserFairShareRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "resource_group": self.resource_group,
            "user_uuid": self.user_uuid,
            "project_id": self.project_id,
            "domain_name": self.domain_name,
            "weight": self.weight,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"weight": self.weight}

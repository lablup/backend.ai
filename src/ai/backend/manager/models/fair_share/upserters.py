"""Sidecar upsert specs of the fair share tables.

A fair share row is read through its resource group's permission and owned by
nothing, so it is a sidecar rather than an entity or a field of one.

``default_weight`` and ``available_slots`` describe the resource group the row sits
in rather than the row itself. The repository reads them before the write and puts
them on the spec, because ``to_data`` is handed the settled row alone.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import ResourceSlot, SlotQuantity
from ai.backend.manager.data.fair_share.types import (
    DomainFairShareData,
    ProjectFairShareData,
    UserFairShareData,
)
from ai.backend.manager.models.fair_share.row import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import DanglingFieldUpserter
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class DomainFairShareUpserter(DanglingFieldUpserter[DomainFairShareRow, DomainFairShareData]):
    """One domain's fair share state in one resource group."""

    resource_group: str
    resource_group_id: ResourceGroupID
    domain_name: str
    weight: TriState[Decimal] = field(default_factory=TriState.nop)
    half_life_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    lookback_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    decay_unit_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    resource_weights: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)
    fair_share_factor: OptionalState[Decimal] = field(default_factory=OptionalState.nop)
    total_decayed_usage: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)
    normalized_usage: OptionalState[Decimal] = field(default_factory=OptionalState.nop)
    lookback_start: OptionalState[date] = field(default_factory=OptionalState.nop)
    lookback_end: OptionalState[date] = field(default_factory=OptionalState.nop)

    # Read off the resource group before the write.
    default_weight: Decimal = Decimal(0)
    available_slots: list[SlotQuantity] = field(default_factory=list)

    @override
    def row_class(self) -> type[DomainFairShareRow]:
        return DomainFairShareRow

    @override
    def index_elements(self) -> list[str]:
        return ["resource_group_id", "domain_name"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {
            "resource_group": self.resource_group,
            "resource_group_id": self.resource_group_id,
            "domain_name": self.domain_name,
        }
        self.weight.update_dict(values, "weight")
        self.half_life_days.update_dict(values, "half_life_days")
        self.lookback_days.update_dict(values, "lookback_days")
        self.decay_unit_days.update_dict(values, "decay_unit_days")
        self.resource_weights.update_dict(values, "resource_weights")
        self.fair_share_factor.update_dict(values, "fair_share_factor")
        self.total_decayed_usage.update_dict(values, "total_decayed_usage")
        self.normalized_usage.update_dict(values, "normalized_usage")
        self.lookback_start.update_dict(values, "lookback_start")
        self.lookback_end.update_dict(values, "lookback_end")
        return values

    @override
    def build_update_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {"resource_group_id": self.resource_group_id}
        self.weight.update_dict(values, "weight")
        self.fair_share_factor.update_dict(values, "fair_share_factor")
        self.total_decayed_usage.update_dict(values, "total_decayed_usage")
        self.normalized_usage.update_dict(values, "normalized_usage")
        self.resource_weights.update_dict(values, "resource_weights")
        self.lookback_start.update_dict(values, "lookback_start")
        self.lookback_end.update_dict(values, "lookback_end")
        return values

    @override
    def to_data(self, row: DomainFairShareRow) -> DomainFairShareData:
        return row.to_data(
            default_weight=self.default_weight,
            available_slots=self.available_slots,
        )


@dataclass
class ProjectFairShareUpserter(DanglingFieldUpserter[ProjectFairShareRow, ProjectFairShareData]):
    """One project's fair share state in one resource group."""

    resource_group: str
    resource_group_id: ResourceGroupID
    project_id: uuid.UUID
    domain_name: str
    weight: TriState[Decimal] = field(default_factory=TriState.nop)
    half_life_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    lookback_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    decay_unit_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    resource_weights: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)
    fair_share_factor: OptionalState[Decimal] = field(default_factory=OptionalState.nop)
    total_decayed_usage: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)
    normalized_usage: OptionalState[Decimal] = field(default_factory=OptionalState.nop)
    lookback_start: OptionalState[date] = field(default_factory=OptionalState.nop)
    lookback_end: OptionalState[date] = field(default_factory=OptionalState.nop)

    # Read off the resource group before the write.
    default_weight: Decimal = Decimal(0)
    available_slots: list[SlotQuantity] = field(default_factory=list)

    @override
    def row_class(self) -> type[ProjectFairShareRow]:
        return ProjectFairShareRow

    @override
    def index_elements(self) -> list[str]:
        return ["resource_group_id", "project_id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {
            "resource_group": self.resource_group,
            "resource_group_id": self.resource_group_id,
            "project_id": self.project_id,
            "domain_name": self.domain_name,
        }
        self.weight.update_dict(values, "weight")
        self.half_life_days.update_dict(values, "half_life_days")
        self.lookback_days.update_dict(values, "lookback_days")
        self.decay_unit_days.update_dict(values, "decay_unit_days")
        self.resource_weights.update_dict(values, "resource_weights")
        self.fair_share_factor.update_dict(values, "fair_share_factor")
        self.total_decayed_usage.update_dict(values, "total_decayed_usage")
        self.normalized_usage.update_dict(values, "normalized_usage")
        self.lookback_start.update_dict(values, "lookback_start")
        self.lookback_end.update_dict(values, "lookback_end")
        return values

    @override
    def build_update_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {"resource_group_id": self.resource_group_id}
        self.weight.update_dict(values, "weight")
        self.fair_share_factor.update_dict(values, "fair_share_factor")
        self.total_decayed_usage.update_dict(values, "total_decayed_usage")
        self.normalized_usage.update_dict(values, "normalized_usage")
        self.resource_weights.update_dict(values, "resource_weights")
        self.lookback_start.update_dict(values, "lookback_start")
        self.lookback_end.update_dict(values, "lookback_end")
        return values

    @override
    def to_data(self, row: ProjectFairShareRow) -> ProjectFairShareData:
        return row.to_data(
            default_weight=self.default_weight,
            available_slots=self.available_slots,
        )


@dataclass
class UserFairShareUpserter(DanglingFieldUpserter[UserFairShareRow, UserFairShareData]):
    """One user's fair share state in one resource group."""

    resource_group: str
    resource_group_id: ResourceGroupID
    user_uuid: uuid.UUID
    project_id: uuid.UUID
    domain_name: str
    weight: TriState[Decimal] = field(default_factory=TriState.nop)
    half_life_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    lookback_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    decay_unit_days: OptionalState[int] = field(default_factory=OptionalState.nop)
    resource_weights: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)
    fair_share_factor: OptionalState[Decimal] = field(default_factory=OptionalState.nop)
    total_decayed_usage: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)
    normalized_usage: OptionalState[Decimal] = field(default_factory=OptionalState.nop)
    lookback_start: OptionalState[date] = field(default_factory=OptionalState.nop)
    lookback_end: OptionalState[date] = field(default_factory=OptionalState.nop)

    # Read off the resource group before the write.
    default_weight: Decimal = Decimal(0)
    available_slots: list[SlotQuantity] = field(default_factory=list)

    @override
    def row_class(self) -> type[UserFairShareRow]:
        return UserFairShareRow

    @override
    def index_elements(self) -> list[str]:
        return ["resource_group_id", "user_uuid", "project_id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {
            "resource_group": self.resource_group,
            "resource_group_id": self.resource_group_id,
            "user_uuid": self.user_uuid,
            "project_id": self.project_id,
            "domain_name": self.domain_name,
        }
        self.weight.update_dict(values, "weight")
        self.half_life_days.update_dict(values, "half_life_days")
        self.lookback_days.update_dict(values, "lookback_days")
        self.decay_unit_days.update_dict(values, "decay_unit_days")
        self.resource_weights.update_dict(values, "resource_weights")
        self.fair_share_factor.update_dict(values, "fair_share_factor")
        self.total_decayed_usage.update_dict(values, "total_decayed_usage")
        self.normalized_usage.update_dict(values, "normalized_usage")
        self.lookback_start.update_dict(values, "lookback_start")
        self.lookback_end.update_dict(values, "lookback_end")
        return values

    @override
    def build_update_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {"resource_group_id": self.resource_group_id}
        self.weight.update_dict(values, "weight")
        self.fair_share_factor.update_dict(values, "fair_share_factor")
        self.total_decayed_usage.update_dict(values, "total_decayed_usage")
        self.normalized_usage.update_dict(values, "normalized_usage")
        self.resource_weights.update_dict(values, "resource_weights")
        self.lookback_start.update_dict(values, "lookback_start")
        self.lookback_end.update_dict(values, "lookback_end")
        return values

    @override
    def to_data(self, row: UserFairShareRow) -> UserFairShareData:
        return row.to_data(
            default_weight=self.default_weight,
            available_slots=self.available_slots,
        )

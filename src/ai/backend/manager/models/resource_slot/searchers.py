"""Searcher implementations for the resource slot repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.manager.data.deployment.types import RevisionResourceSlotData
from ai.backend.manager.data.resource_slot.types import (
    AgentResourceData,
    ResourceAllocationData,
    ResourceSlotTypeData,
)
from ai.backend.manager.models.resource_slot.row import (
    AgentResourceRow,
    DeploymentRevisionResourceSlotRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.resource_slot.searchable_fields import (
    AgentResourceSearchableFields,
    ResourceAllocationSearchableFields,
    ResourceSlotTypeSearchableFields,
    RevisionResourceSlotSearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ResourceSlotTypeSearcher(Searcher[ResourceSlotTypeRow, ResourceSlotTypeData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ResourceSlotTypeRow)

    @override
    def to_data(self, row: ResourceSlotTypeRow) -> ResourceSlotTypeData:
        return ResourceSlotTypeSearchableFields.own.to_data(row)


@dataclass
class AgentResourceSearcher(Searcher[AgentResourceRow, AgentResourceData]):
    """Slot rows ordered by the caller's choice, or by catalog rank by default."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        query = sa.select(AgentResourceRow).join(
            ResourceSlotTypeRow, AgentResourceRow.slot_name == ResourceSlotTypeRow.slot_name
        )
        if not self.orders:
            query = query.order_by(ResourceSlotTypeRow.rank)
        return query

    @override
    def to_data(self, row: AgentResourceRow) -> AgentResourceData:
        return AgentResourceSearchableFields.own.to_data(row)


@dataclass
class UnrankedAgentResourceSearcher(Searcher[AgentResourceRow, AgentResourceData]):
    """Slot rows in the order the caller names, without the slot catalog's rank."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(AgentResourceRow)

    @override
    def to_data(self, row: AgentResourceRow) -> AgentResourceData:
        return AgentResourceSearchableFields.own.to_data(row)


@dataclass
class ResourceAllocationSearcher(Searcher[ResourceAllocationRow, ResourceAllocationData]):
    """Resource allocation rows matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ResourceAllocationRow)

    @override
    def to_data(self, row: ResourceAllocationRow) -> ResourceAllocationData:
        return ResourceAllocationSearchableFields.own.to_data(row)


@dataclass
class RevisionResourceSlotSearcher(
    Searcher[DeploymentRevisionResourceSlotRow, RevisionResourceSlotData]
):
    """The slot rows of one revision, joined to the slot catalog so a rank order is
    expressible."""

    revision_id: DeploymentRevisionID = field(kw_only=True)

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return (
            sa.select(DeploymentRevisionResourceSlotRow)
            .join(
                ResourceSlotTypeRow,
                DeploymentRevisionResourceSlotRow.slot_name == ResourceSlotTypeRow.slot_name,
            )
            .where(DeploymentRevisionResourceSlotRow.revision_id == self.revision_id)
        )

    @override
    def to_data(self, row: DeploymentRevisionResourceSlotRow) -> RevisionResourceSlotData:
        return RevisionResourceSlotSearchableFields.own.to_data(row)

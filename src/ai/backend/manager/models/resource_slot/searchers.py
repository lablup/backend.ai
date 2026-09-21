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
    ResourceSlotTypeSearchableFields,
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
    """Slot rows in the slot catalog's own rank order. Which agents' rows these are
    is the operation scope's to say."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return (
            sa.select(AgentResourceRow)
            .join(ResourceSlotTypeRow, AgentResourceRow.slot_name == ResourceSlotTypeRow.slot_name)
            .order_by(ResourceSlotTypeRow.rank)
        )

    @override
    def to_data(self, row: AgentResourceRow) -> AgentResourceData:
        return row.to_data()


@dataclass
class UnrankedAgentResourceSearcher(Searcher[AgentResourceRow, AgentResourceData]):
    """Slot rows in the order the caller names, without the slot catalog's rank."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(AgentResourceRow)

    @override
    def to_data(self, row: AgentResourceRow) -> AgentResourceData:
        return row.to_data()


@dataclass
class ResourceAllocationSearcher(Searcher[ResourceAllocationRow, ResourceAllocationData]):
    """Resource allocation rows matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ResourceAllocationRow)

    @override
    def to_data(self, row: ResourceAllocationRow) -> ResourceAllocationData:
        return ResourceAllocationData(
            id=row.id,
            kernel_id=row.kernel_id,
            slot_name=row.slot_name,
            requested=row.requested,
            used=row.used,
        )


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
        return RevisionResourceSlotData(
            revision_id=row.revision_id,
            slot_name=row.slot_name,
            quantity=row.quantity,
        )

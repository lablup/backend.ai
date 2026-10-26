"""
Request DTOs for KernelGroup v2 API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.kernel_group.types import (
    KernelGroupEnvironOrderField,
    KernelGroupEnvironScope,
    KernelGroupOrderField,
    KernelGroupResourceSlotOrderField,
    KernelGroupResourceSlotScope,
    KernelGroupScope,
)

__all__ = (
    "KernelGroupEnvironFilter",
    "KernelGroupEnvironOrder",
    "KernelGroupFilter",
    "KernelGroupOrder",
    "KernelGroupResourceSlotFilter",
    "KernelGroupResourceSlotOrder",
    "ScopedSearchKernelGroupEnvironsInput",
    "ScopedSearchKernelGroupResourceSlotsInput",
    "ScopedSearchKernelGroupsInput",
)


class KernelGroupFilter(BaseRequestModel):
    """Filter for kernel groups."""

    field_id: UUIDFilter | None = Field(default=None, description="Filter by kernel group ID.")
    role: StringFilter | None = Field(default=None, description="Filter by role.")
    created_at: DateTimeFilter | None = Field(default=None, description="Filter by creation time.")

    AND: list[KernelGroupFilter] | None = Field(default=None, description="AND logical combinator.")
    OR: list[KernelGroupFilter] | None = Field(default=None, description="OR logical combinator.")
    NOT: list[KernelGroupFilter] | None = Field(default=None, description="NOT logical combinator.")


KernelGroupFilter.model_rebuild()


class KernelGroupOrder(BaseRequestModel):
    """Order specification for kernel groups."""

    field: KernelGroupOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class ScopedSearchKernelGroupsInput(BaseRequestModel):
    """Input for searching kernel groups within sessions."""

    scope: KernelGroupScope = Field(description="Scope (OR across all items).")
    filter: KernelGroupFilter | None = Field(default=None, description="Filter conditions.")
    order: list[KernelGroupOrder] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")


class KernelGroupEnvironFilter(BaseRequestModel):
    """Filter for kernel group environ rows."""

    field_id: UUIDFilter | None = Field(default=None, description="Filter by environ row ID.")
    kernel_group_id: UUIDFilter | None = Field(
        default=None, description="Filter by the kernel group the row belongs to."
    )
    key: StringFilter | None = Field(default=None, description="Filter by variable name.")

    AND: list[KernelGroupEnvironFilter] | None = Field(
        default=None, description="AND logical combinator."
    )
    OR: list[KernelGroupEnvironFilter] | None = Field(
        default=None, description="OR logical combinator."
    )
    NOT: list[KernelGroupEnvironFilter] | None = Field(
        default=None, description="NOT logical combinator."
    )


KernelGroupEnvironFilter.model_rebuild()


class KernelGroupEnvironOrder(BaseRequestModel):
    """Order specification for kernel group environ rows."""

    field: KernelGroupEnvironOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class ScopedSearchKernelGroupEnvironsInput(BaseRequestModel):
    """Input for searching the environ rows of kernel groups within sessions."""

    scope: KernelGroupEnvironScope = Field(description="Scope (OR across all items).")
    filter: KernelGroupEnvironFilter | None = Field(default=None, description="Filter conditions.")
    order: list[KernelGroupEnvironOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")


class KernelGroupResourceSlotFilter(BaseRequestModel):
    """Filter for kernel group resource slot rows."""

    field_id: UUIDFilter | None = Field(default=None, description="Filter by resource slot row ID.")
    kernel_group_id: UUIDFilter | None = Field(
        default=None, description="Filter by the kernel group the row belongs to."
    )
    slot_name: StringFilter | None = Field(default=None, description="Filter by slot name.")

    AND: list[KernelGroupResourceSlotFilter] | None = Field(
        default=None, description="AND logical combinator."
    )
    OR: list[KernelGroupResourceSlotFilter] | None = Field(
        default=None, description="OR logical combinator."
    )
    NOT: list[KernelGroupResourceSlotFilter] | None = Field(
        default=None, description="NOT logical combinator."
    )


KernelGroupResourceSlotFilter.model_rebuild()


class KernelGroupResourceSlotOrder(BaseRequestModel):
    """Order specification for kernel group resource slot rows."""

    field: KernelGroupResourceSlotOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class ScopedSearchKernelGroupResourceSlotsInput(BaseRequestModel):
    """Input for searching the resource slot rows of kernel groups within sessions."""

    scope: KernelGroupResourceSlotScope = Field(description="Scope (OR across all items).")
    filter: KernelGroupResourceSlotFilter | None = Field(
        default=None, description="Filter conditions."
    )
    order: list[KernelGroupResourceSlotOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")

"""
Request DTOs for Project export report.

This module defines the filter, order, and request structures specific to project data export,
including filters for project name, domain, and active status.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeRangeFilter, StringFilter

from .types import OrderDirection

__all__ = (
    "BooleanFilter",
    "ProjectExportFilter",
    "ProjectExportOrder",
    "ProjectExportOrderField",
    "ProjectExportCSVRequest",
)


class BooleanFilter(BaseRequestModel):
    """
    Filter for boolean fields.

    Simple filter that matches records where the field equals the specified value.
    """

    equals: bool = Field(
        description=(
            "The boolean value to match. "
            "Set to true to include only records where the field is true, "
            "or false to include only records where the field is false."
        )
    )


class ProjectExportOrderField(StrEnum):
    """
    Orderable fields for project export.

    These are the fields that can be used for sorting project export results.
    Only base project fields are supported for ordering.
    """

    NAME = "name"
    DOMAIN_NAME = "domain_name"
    IS_ACTIVE = "is_active"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"


class ProjectExportOrder(BaseRequestModel):
    """
    Specifies how to sort the exported project data.

    Multiple ProjectExportOrder instances can be provided to define multi-level sorting.
    The order in the list determines priority (first item is primary sort key).
    """

    field: ProjectExportOrderField = Field(
        description=(
            "The field to sort by. Only base project fields are supported: "
            "name, domain_name, is_active, created_at, modified_at. "
            "JOIN fields (resource_policy, scaling_group, container_registry) are not orderable."
        )
    )
    direction: OrderDirection = Field(
        default=OrderDirection.ASC,
        description=(
            "Sort direction. 'asc' for ascending (A-Z, oldest-first, false-first), "
            "'desc' for descending (Z-A, newest-first, true-first). Default is 'asc'."
        ),
    )


class ProjectExportFilter(BaseRequestModel):
    """
    Filter conditions specific to project export.

    All specified conditions are combined with AND logic.
    Only records matching all specified filters will be exported.
    Use this to narrow down the exported project data to specific criteria.

    Only base project fields are supported for filtering.
    """

    name: StringFilter | None = Field(
        default=None,
        description=(
            "Filter projects by name. Supports various match modes: "
            "contains, equals, starts_with, ends_with. "
            "Can be case-insensitive and/or negated."
        ),
    )
    domain_name: StringFilter | None = Field(
        default=None,
        description=(
            "Filter projects by domain name. "
            "Use this to export projects belonging to a specific domain."
        ),
    )
    is_active: BooleanFilter | None = Field(
        default=None,
        description=(
            "Filter projects by active status. "
            "Set equals to true for active projects only, "
            "or false for inactive/archived projects only."
        ),
    )
    created_at: DateTimeRangeFilter | None = Field(
        default=None,
        description=(
            "Filter projects by creation timestamp. "
            "Specify 'after' and/or 'before' to define the datetime range. "
            "Useful for exporting projects created within a specific period."
        ),
    )


class ProjectExportCSVRequest(BaseRequestModel):
    """
    Request body for project CSV export operations.

    This is the request model for POST /export/projects/csv endpoint.
    All parameters are optional to allow flexible export configurations.
    """

    fields: list[str] | None = Field(
        default=None,
        description=(
            "List of field keys to include in the export. "
            "Available fields: id, name, description, domain_name, is_active, "
            "total_resource_slots, created_at, modified_at. "
            "If not specified or empty, all available fields will be exported."
        ),
    )
    filter: ProjectExportFilter | None = Field(
        default=None,
        description=(
            "Filter conditions to apply before export. "
            "Only projects matching all specified conditions will be included. "
            "If not specified, all projects (up to max_rows limit) will be exported."
        ),
    )
    order: list[ProjectExportOrder] | None = Field(
        default=None,
        description=(
            "List of ordering specifications for sorting the exported data. "
            "Multiple orders can be specified for multi-level sorting. "
            "The first item in the list is the primary sort key."
        ),
    )
    encoding: str = Field(
        default="utf-8",
        description=(
            "Character encoding for the CSV output. "
            "Supported values: 'utf-8' (default, recommended for most uses), "
            "'euc-kr' (for Korean systems requiring legacy encoding)."
        ),
    )

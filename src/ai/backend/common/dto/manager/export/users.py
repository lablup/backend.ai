"""
Request DTOs for User export report.

This module defines the filter, order, and request structures specific to user data export,
including filters for username, email, domain, role, and status fields.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeRangeFilter, StringFilter

from .types import OrderDirection

__all__ = (
    "UserExportFilter",
    "UserExportOrder",
    "UserExportOrderField",
    "UserExportCSVRequest",
)


class UserExportOrderField(StrEnum):
    """
    Orderable fields for user export.

    These are the fields that can be used for sorting user export results.
    Not all user fields are sortable - only commonly used sort keys are included.
    """

    USERNAME = "username"
    EMAIL = "email"
    FULL_NAME = "full_name"
    DOMAIN_NAME = "domain_name"
    ROLE = "role"
    STATUS = "status"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"


class UserExportOrder(BaseRequestModel):
    """
    Specifies how to sort the exported user data.

    Multiple UserExportOrder instances can be provided to define multi-level sorting.
    The order in the list determines priority (first item is primary sort key).
    """

    field: UserExportOrderField = Field(
        description=(
            "The field to sort by. Must be one of the valid user orderable fields: "
            "username, email, full_name, domain_name, role, status, created_at, modified_at."
        )
    )
    direction: OrderDirection = Field(
        default=OrderDirection.ASC,
        description=(
            "Sort direction. 'asc' for ascending (A-Z, oldest-first), "
            "'desc' for descending (Z-A, newest-first). Default is 'asc'."
        ),
    )


class UserExportFilter(BaseRequestModel):
    """
    Filter conditions specific to user export.

    All specified conditions are combined with AND logic.
    Only records matching all specified filters will be exported.
    Use this to narrow down the exported user data to specific criteria.
    """

    username: Optional[StringFilter] = Field(
        default=None,
        description=(
            "Filter users by username. Supports various match modes: "
            "contains, equals, starts_with, ends_with. "
            "Can be case-insensitive and/or negated."
        ),
    )
    email: Optional[StringFilter] = Field(
        default=None,
        description=(
            "Filter users by email address. Supports various match modes: "
            "contains, equals, starts_with, ends_with. "
            "Useful for finding users from specific email domains."
        ),
    )
    domain_name: Optional[StringFilter] = Field(
        default=None,
        description=(
            "Filter users by their assigned domain name. "
            "Use this to export users belonging to a specific domain."
        ),
    )
    role: Optional[list[str]] = Field(
        default=None,
        description=(
            "Filter users by role(s). Accepts a list of role values "
            "(e.g., ['admin', 'user', 'monitor']). Uses IN query."
        ),
    )
    status: Optional[list[str]] = Field(
        default=None,
        description=(
            "Filter users by account status(es). Accepts a list of status values "
            "(e.g., ['active', 'inactive']). Uses IN query."
        ),
    )
    created_at: Optional[DateTimeRangeFilter] = Field(
        default=None,
        description=(
            "Filter users by their registration timestamp. "
            "Specify 'after' and/or 'before' to define the datetime range. "
            "Useful for exporting users registered within a specific period."
        ),
    )


class UserExportCSVRequest(BaseRequestModel):
    """
    Request body for user CSV export operations.

    This is the request model for POST /export/users/csv endpoint.
    All parameters are optional to allow flexible export configurations.
    """

    fields: Optional[list[str]] = Field(
        default=None,
        description=(
            "List of field keys to include in the export. "
            "Available fields: uuid, username, email, full_name, domain_name, role, status, created_at, modified_at. "
            "If not specified or empty, all available fields will be exported."
        ),
    )
    filter: Optional[UserExportFilter] = Field(
        default=None,
        description=(
            "Filter conditions to apply before export. "
            "Only users matching all specified conditions will be included. "
            "If not specified, all users (up to max_rows limit) will be exported."
        ),
    )
    order: Optional[list[UserExportOrder]] = Field(
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

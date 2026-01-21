import uuid
from datetime import datetime
from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class DateTimeRangeFilter(BaseRequestModel):
    """
    Filters records by a datetime range.

    Both boundaries are inclusive. You can specify just 'after', just 'before',
    or both to define the range. Records matching the boundary values are included.
    This filter is shared across all report types for datetime fields like
    created_at, modified_at, terminated_at, etc.
    """

    after: Optional[datetime] = Field(
        default=None,
        description=(
            "Include only records created on or after this datetime. "
            "Should be in ISO 8601 format (e.g., '2024-01-01T00:00:00Z'). "
            "If not specified, there is no lower bound on the datetime range."
        ),
    )
    before: Optional[datetime] = Field(
        default=None,
        description=(
            "Include only records created on or before this datetime. "
            "Should be in ISO 8601 format (e.g., '2024-12-31T23:59:59Z'). "
            "If not specified, there is no upper bound on the datetime range."
        ),
    )


class StringFilter(BaseRequestModel):
    """Comprehensive string field filter supporting multiple match operations.

    Provides flexible string matching with four operation types (equals, contains,
    starts_with, ends_with), each available in case-sensitive, case-insensitive,
    and negated variants for complete filtering control.
    """

    # Basic operations (case-sensitive)
    equals: Optional[str] = Field(default=None, description="Exact match (case-sensitive)")
    contains: Optional[str] = Field(default=None, description="Contains (case-sensitive)")
    starts_with: Optional[str] = Field(default=None, description="Starts with (case-sensitive)")
    ends_with: Optional[str] = Field(default=None, description="Ends with (case-sensitive)")

    # NOT operations (case-sensitive)
    not_equals: Optional[str] = Field(default=None, description="Not equals (case-sensitive)")
    not_contains: Optional[str] = Field(default=None, description="Not contains (case-sensitive)")
    not_starts_with: Optional[str] = Field(
        default=None, description="Not starts with (case-sensitive)"
    )
    not_ends_with: Optional[str] = Field(default=None, description="Not ends with (case-sensitive)")

    # Case-insensitive operations
    i_equals: Optional[str] = Field(default=None, description="Exact match (case-insensitive)")
    i_contains: Optional[str] = Field(default=None, description="Contains (case-insensitive)")
    i_starts_with: Optional[str] = Field(default=None, description="Starts with (case-insensitive)")
    i_ends_with: Optional[str] = Field(default=None, description="Ends with (case-insensitive)")

    # Case-insensitive NOT operations
    i_not_equals: Optional[str] = Field(default=None, description="Not equals (case-insensitive)")
    i_not_contains: Optional[str] = Field(
        default=None, description="Not contains (case-insensitive)"
    )
    i_not_starts_with: Optional[str] = Field(
        default=None, description="Not starts with (case-insensitive)"
    )
    i_not_ends_with: Optional[str] = Field(
        default=None, description="Not ends with (case-insensitive)"
    )


class UUIDFilter(BaseRequestModel):
    """Filter for UUID fields supporting equality and set operations.

    Provides UUID matching with equals/not_equals and in/not_in operations.
    """

    # Basic operations
    equals: Optional[uuid.UUID] = Field(default=None, description="Exact UUID match")
    in_: Optional[list[uuid.UUID]] = Field(default=None, alias="in", description="UUID is in list")

    # NOT operations
    not_equals: Optional[uuid.UUID] = Field(default=None, description="Not equals UUID")
    not_in: Optional[list[uuid.UUID]] = Field(default=None, description="UUID is not in list")


class ListGroupQuery(BaseRequestModel):
    group_id: Optional[uuid.UUID] = Field(default=None, alias="groupId")

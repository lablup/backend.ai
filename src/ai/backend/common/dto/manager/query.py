import uuid
from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


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


class ListGroupQuery(BaseRequestModel):
    group_id: Optional[uuid.UUID] = Field(default=None, alias="groupId")

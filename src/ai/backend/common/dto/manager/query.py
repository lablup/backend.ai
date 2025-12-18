import uuid
from typing import Optional

from pydantic import Field

from ...api_handlers import BaseRequestModel


class StringFilter(BaseRequestModel):
    """String field filter with case-sensitive and case-insensitive options."""

    equals: Optional[str] = Field(default=None, description="Exact match (case-sensitive)")
    i_equals: Optional[str] = Field(default=None, description="Exact match (case-insensitive)")
    contains: Optional[str] = Field(default=None, description="Contains (case-sensitive)")
    i_contains: Optional[str] = Field(default=None, description="Contains (case-insensitive)")


class ListGroupQuery(BaseRequestModel):
    group_id: Optional[uuid.UUID] = Field(default=None, alias="groupId")

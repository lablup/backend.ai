import uuid
from typing import Generic, Optional, TypeVar

from pydantic import Field

from ...api_handlers import BaseRequestModel

TFilterValue = TypeVar("TFilterValue")


class StrictValueFilter(BaseRequestModel, Generic[TFilterValue]):
    """Filter for exact match of a strict value type."""

    equals: TFilterValue = Field(description="Exact match")


class StringFilter(BaseRequestModel):
    """String field filter with case-sensitive and case-insensitive options."""

    equals: Optional[str] = Field(default=None, description="Exact match (case-sensitive)")
    i_equals: Optional[str] = Field(default=None, description="Exact match (case-insensitive)")
    contains: Optional[str] = Field(default=None, description="Contains (case-sensitive)")
    i_contains: Optional[str] = Field(default=None, description="Contains (case-insensitive)")


class UUIDFilter(BaseRequestModel):
    """UUID field filter for exact match."""

    equals: uuid.UUID = Field(description="Exact match UUID")


class ListGroupQuery(BaseRequestModel):
    group_id: Optional[uuid.UUID] = Field(default=None, alias="groupId")

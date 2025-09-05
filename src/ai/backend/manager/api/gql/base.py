from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Optional, Protocol, Type, TypeVar, cast

import graphene
import orjson
import strawberry
from graphql import StringValueNode
from graphql_relay.utils import base64, unbase64
from strawberry.types import get_object_definition, has_object_definition

from ai.backend.common.types import ResourceSlot

if TYPE_CHECKING:
    from ai.backend.manager.types import (
        PaginationOptions,
    )


@strawberry.scalar
class ByteSize(str):
    """
    Custom scalar type for representing byte sizes in GraphQL.
    """

    @staticmethod
    def parse_value(value: str) -> str:
        return value

    @staticmethod
    def parse_literal(ast) -> str:
        if not isinstance(ast, StringValueNode):
            raise ValueError("ByteSize must be provided as a string literal")
        value = ast.value
        return value


@strawberry.input
class StringFilter:
    contains: Optional[str] = None
    starts_with: Optional[str] = None
    ends_with: Optional[str] = None
    equals: Optional[str] = None
    not_equals: Optional[str] = None

    i_contains: Optional[str] = strawberry.field(name="iContains", default=None)
    i_starts_with: Optional[str] = strawberry.field(name="iStartsWith", default=None)
    i_ends_with: Optional[str] = strawberry.field(name="iEndsWith", default=None)
    i_equals: Optional[str] = strawberry.field(name="iEquals", default=None)
    i_not_equals: Optional[str] = strawberry.field(name="iNotEquals", default=None)

    def apply_to_column(self, column):
        """Apply this string filter to a SQLAlchemy column and return the condition.

        Args:
            column: SQLAlchemy column to apply the filter to

        Returns:
            SQLAlchemy condition expression or None if no filter is set
        """

        if self.equals:
            return column == self.equals
        elif self.i_equals:
            return column.ilike(self.i_equals)
        elif self.not_equals:
            return column != self.not_equals
        elif self.i_not_equals:
            return ~column.ilike(self.i_not_equals)
        elif self.starts_with:
            return column.like(f"{self.starts_with}%")
        elif self.i_starts_with:
            return column.ilike(f"{self.i_starts_with}%")
        elif self.ends_with:
            return column.like(f"%{self.ends_with}")
        elif self.i_ends_with:
            return column.ilike(f"%{self.i_ends_with}")
        elif self.contains:
            return column.like(f"%{self.contains}%")
        elif self.i_contains:
            return column.ilike(f"%{self.i_contains}%")

        return None


@strawberry.input
class IntFilter:
    equals: Optional[int] = None
    not_equals: Optional[int] = None
    greater_than: Optional[int] = None
    greater_than_or_equal: Optional[int] = None
    less_than: Optional[int] = None
    less_than_or_equal: Optional[int] = None

    def apply_to_column(self, column):
        """Apply this int filter to a SQLAlchemy column and return the condition.

        Args:
            column: SQLAlchemy column to apply the filter to

        Returns:
            SQLAlchemy condition expression or None if no filter is set
        """

        if self.equals is not None:
            return column == self.equals
        elif self.not_equals is not None:
            return column != self.not_equals
        elif self.greater_than is not None:
            return column > self.greater_than
        elif self.greater_than_or_equal is not None:
            return column >= self.greater_than_or_equal
        elif self.less_than is not None:
            return column < self.less_than
        elif self.less_than_or_equal is not None:
            return column <= self.less_than_or_equal

        return None


@strawberry.enum
class OrderDirection(StrEnum):
    ASC = "ASC"
    DESC = "DESC"


@strawberry.enum
class Ordering(StrEnum):
    ASC = "ASC"
    ASC_NULLS_FIRST = "ASC_NULLS_FIRST"
    ASC_NULLS_LAST = "ASC_NULLS_LAST"
    DESC = "DESC"
    DESC_NULLS_FIRST = "DESC_NULLS_FIRST"
    DESC_NULLS_LAST = "DESC_NULLS_LAST"


@strawberry.scalar(description="Added in 25.13.0")
class JSONString:
    @staticmethod
    def parse_value(value: str | bytes) -> Mapping[str, Any]:
        if isinstance(value, str):
            return orjson.loads(value)
        if isinstance(value, bytes):
            return orjson.loads(value)
        return value

    @staticmethod
    def serialize(value: Any) -> JSONString:
        if isinstance(value, (dict, list)):
            return cast(JSONString, orjson.dumps(value).decode("utf-8"))
        elif isinstance(value, str):
            return cast(JSONString, value)
        else:
            return cast(JSONString, orjson.dumps(value).decode("utf-8"))

    @staticmethod
    def from_resource_slot(resource_slot: ResourceSlot) -> JSONString:
        return JSONString.serialize(resource_slot.to_json())


def to_global_id(
    type_: Type[Any], local_id: uuid.UUID | str, is_target_graphene_object: bool = False
) -> str:
    if is_target_graphene_object:
        # For compatibility with existing Graphene-based global IDs
        if not issubclass(type_, graphene.ObjectType):
            raise TypeError(
                "type_ must be a graphene ObjectType when is_target_graphene_object is True."
            )
        typename = type_.__name__
        return base64(f"{typename}:{local_id}")
    if not has_object_definition(type_):
        raise TypeError("type_ must be a Strawberry object type (Node or Edge).")
    typename = get_object_definition(type_, strict=True).name
    return base64(f"{typename}:{local_id}")


def resolve_global_id(global_id: str) -> tuple[str, str]:
    unbased_global_id = unbase64(global_id)
    type_, _, id_ = unbased_global_id.partition(":")
    return type_, id_


def build_pagination_options(
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> PaginationOptions:
    from ai.backend.manager.types import (
        BackwardPaginationOptions,
        ForwardPaginationOptions,
        OffsetBasedPaginationOptions,
        PaginationOptions,
    )

    """Build pagination options from GraphQL arguments"""
    pagination = PaginationOptions()

    # Handle offset-based pagination
    if offset is not None or limit is not None:
        pagination.offset = OffsetBasedPaginationOptions(offset=offset, limit=limit)
        return pagination

    # Handle cursor-based pagination
    if after is not None or first is not None:
        pagination.forward = ForwardPaginationOptions(after=after, first=first)
    elif before is not None or last is not None:
        pagination.backward = BackwardPaginationOptions(before=before, last=last)

    return pagination


@dataclass
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str] = None
    end_cursor: Optional[str] = None

    def to_strawberry_page_info(self) -> "strawberry.relay.PageInfo":
        return strawberry.relay.PageInfo(
            has_next_page=self.has_next_page,
            has_previous_page=self.has_previous_page,
            start_cursor=self.start_cursor,
            end_cursor=self.end_cursor,
        )


class HasCursor(Protocol):
    cursor: str


TEdge = TypeVar("TEdge", bound=HasCursor)


def build_page_info(
    edges: list[TEdge], total_count: int, pagination_options: PaginationOptions
) -> PageInfo:
    """Build PageInfo from edges and pagination options"""
    has_next_page = False
    has_previous_page = False

    if pagination_options.offset:
        # Offset-based pagination
        offset = pagination_options.offset.offset or 0

        has_previous_page = offset > 0
        has_next_page = (offset + len(edges)) < total_count

    elif pagination_options.forward:
        # Forward pagination (after/first)
        first = pagination_options.forward.first
        if first is not None:
            # If we got exactly the requested number and there might be more
            has_next_page = len(edges) == first
        else:
            # If no first specified, check if we have all items
            has_next_page = len(edges) < total_count
        has_previous_page = pagination_options.forward.after is not None

    elif pagination_options.backward:
        # Backward pagination (before/last)
        last = pagination_options.backward.last
        if last is not None:
            # If we got exactly the requested number, there might be more before
            has_previous_page = len(edges) == last
        else:
            # If no last specified, assume there could be previous items
            has_previous_page = True
        has_next_page = pagination_options.backward.before is not None

    else:
        # Default case - assume we have all items if no pagination specified
        has_next_page = len(edges) < total_count
        has_previous_page = False

    return PageInfo(
        has_next_page=has_next_page,
        has_previous_page=has_previous_page,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )

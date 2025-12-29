from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Optional, Protocol, Type, TypeVar, cast

import graphene
import strawberry
from graphql import StringValueNode
from graphql_relay.utils import base64, unbase64
from strawberry.types import get_object_definition, has_object_definition

from ai.backend.common.json import dump_json_str, load_json
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.common.types import IntFilterData, StringFilterData

if TYPE_CHECKING:
    from ai.backend.manager.repositories.base import QueryCondition
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

    def to_dataclass(self) -> StringFilterData:
        return StringFilterData(
            contains=self.contains,
            starts_with=self.starts_with,
            ends_with=self.ends_with,
            equals=self.equals,
            not_equals=self.not_equals,
            i_contains=self.i_contains,
            i_starts_with=self.i_starts_with,
            i_ends_with=self.i_ends_with,
            i_equals=self.i_equals,
            i_not_equals=self.i_not_equals,
        )

    def build_query_condition(
        self,
        contains_factory: Callable[[str, bool], QueryCondition],
        equals_factory: Callable[[str, bool], QueryCondition],
    ) -> Optional[QueryCondition]:
        """Build a query condition from this filter using the provided factory callables.

        Args:
            contains_factory: Factory function that takes (value, case_insensitive) and returns QueryCondition
            equals_factory: Factory function that takes (value, case_insensitive) and returns QueryCondition

        Returns:
            QueryCondition if any filter field is set, None otherwise
        """
        if self.equals:
            return equals_factory(self.equals, False)
        elif self.i_equals:
            return equals_factory(self.i_equals, True)
        elif self.contains:
            return contains_factory(self.contains, False)
        elif self.i_contains:
            return contains_factory(self.i_contains, True)
        return None


@strawberry.input
class IntFilter:
    equals: Optional[int] = None
    not_equals: Optional[int] = None
    greater_than: Optional[int] = None
    greater_than_or_equal: Optional[int] = None
    less_than: Optional[int] = None
    less_than_or_equal: Optional[int] = None

    def to_dataclass(self) -> IntFilterData:
        return IntFilterData(
            equals=self.equals,
            not_equals=self.not_equals,
            greater_than=self.greater_than,
            greater_than_or_equal=self.greater_than_or_equal,
            less_than=self.less_than,
            less_than_or_equal=self.less_than_or_equal,
        )


@strawberry.input
class DateTimeFilter:
    """Filter for datetime fields."""

    before: Optional[datetime] = None
    after: Optional[datetime] = None
    equals: Optional[datetime] = None
    not_equals: Optional[datetime] = None

    def build_query_condition(
        self,
        before_factory: Callable[[datetime], QueryCondition],
        after_factory: Callable[[datetime], QueryCondition],
        equals_factory: Optional[Callable[[datetime], QueryCondition]] = None,
    ) -> Optional[QueryCondition]:
        """Build a query condition from this filter using the provided factory callables.

        Args:
            before_factory: Factory function that takes datetime and returns QueryCondition for < comparison
            after_factory: Factory function that takes datetime and returns QueryCondition for > comparison
            equals_factory: Optional factory function for = comparison

        Returns:
            QueryCondition if any filter field is set, None otherwise
        """
        if self.equals and equals_factory:
            return equals_factory(self.equals)
        elif self.before:
            return before_factory(self.before)
        elif self.after:
            return after_factory(self.after)
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


@strawberry.scalar(description="Added in 25.15.0")
class JSONString:
    @staticmethod
    def parse_value(value: str | bytes) -> Mapping[str, Any]:
        if isinstance(value, str):
            return load_json(value)
        if isinstance(value, bytes):
            return load_json(value)
        return value

    @staticmethod
    def serialize(value: Any) -> JSONString:
        if isinstance(value, (dict, list)):
            return cast(JSONString, dump_json_str(value))
        elif isinstance(value, str):
            return cast(JSONString, value)
        else:
            return cast(JSONString, dump_json_str(value))

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


CURSOR_VERSION = "v1"


def encode_cursor(row_id: str | uuid.UUID) -> str:
    """Encode row ID to cursor format: base64(cursor:v1:{row_id})"""
    raw = f"cursor:{CURSOR_VERSION}:{row_id}"
    return base64(raw)


def decode_cursor(cursor: str) -> str:
    """Decode cursor and return row_id. Raises InvalidCursor on failure."""
    from ai.backend.manager.errors.api import InvalidCursor

    try:
        raw = unbase64(cursor)
    except Exception as e:
        raise InvalidCursor(f"Invalid cursor encoding: {cursor}") from e

    parts = raw.split(":", 2)
    if len(parts) != 3 or parts[0] != "cursor" or parts[1] != CURSOR_VERSION:
        raise InvalidCursor(f"Invalid cursor format: {cursor}")
    return parts[2]  # row_id


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

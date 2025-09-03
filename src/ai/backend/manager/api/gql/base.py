from __future__ import annotations

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Optional, Type

import orjson
import strawberry
from graphql import StringValueNode
from graphql_relay.utils import base64, unbase64
from strawberry.types import get_object_definition, has_object_definition

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


def serialize_json(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return orjson.dumps(value).decode("utf-8")
    elif isinstance(value, str):
        return value
    else:
        return orjson.dumps(value).decode("utf-8")


def parse_json(value: str | bytes) -> Any:
    if isinstance(value, str):
        return orjson.loads(value)
    elif isinstance(value, bytes):
        return orjson.loads(value)
    else:
        return value


@strawberry.scalar(
    name="JSONString",
    description="A custom scalar for JSON strings using orjson",
    serialize=serialize_json,
    parse_value=parse_json,
    parse_literal=lambda v: parse_json(v.value) if hasattr(v, "value") else v,
)
class JSONString:
    pass


def to_global_id(type_: Type[Any], local_id: uuid.UUID | str) -> str:
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

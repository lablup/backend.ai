from __future__ import annotations

from enum import StrEnum
from typing import Any, Optional

import orjson
import strawberry


@strawberry.scalar
class ByteSize:
    """
    Custom scalar type for representing byte sizes in GraphQL.
    """

    pass


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

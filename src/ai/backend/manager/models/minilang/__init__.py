from enum import Enum
from typing import Any, Callable, Generic, NamedTuple, TypeVar

import sqlalchemy as sa


class ArrayFieldItem(NamedTuple):
    column_name: str


class JSONFieldItem(NamedTuple):
    column_name: str
    key_name: str


TEnum = TypeVar("TEnum", bound=Enum)


class EnumFieldItem(NamedTuple, Generic[TEnum]):
    column_name: str
    enum_cls: TEnum


FieldSpecItem = tuple[
    str | ArrayFieldItem | JSONFieldItem | EnumFieldItem, Callable[[str], Any] | None
]
OrderSpecItem = tuple[
    str | ArrayFieldItem | JSONFieldItem | EnumFieldItem, Callable[[sa.Column], Any] | None
]


def get_col_from_table(table, column_name: str):
    try:
        return table.c[column_name]
    except AttributeError:
        # For ORM class table
        return getattr(table, column_name)

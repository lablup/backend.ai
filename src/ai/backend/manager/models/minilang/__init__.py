from enum import Enum
from typing import Any, Callable, Generic, NamedTuple, TypeVar

import sqlalchemy as sa


class ArrayFieldItem(NamedTuple):
    column_name: str


class JSONFieldItem(NamedTuple):
    column_name: str
    key_name: str


class ORMFieldItem(NamedTuple):
    column: sa.orm.attributes.InstrumentedAttribute


TEnum = TypeVar("TEnum", bound=Enum)


class EnumFieldItem(NamedTuple, Generic[TEnum]):
    column_name: str
    enum_cls: TEnum


FieldSpecItem = tuple[
    str | ArrayFieldItem | JSONFieldItem | EnumFieldItem | ORMFieldItem, Callable[[str], Any] | None
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


class ExternalTableFilterSpec:
    """
    Specification for filtering on external tables that require JOINs.
    This allows filters on related tables (like project_name from GroupRow)
    to be handled separately and passed to repository layer for JOIN operations.
    """

    def __init__(
        self,
        field_name: str,
        target_table: sa.Table,
        target_column: str,
        join_builder: Callable[[sa.Table], sa.sql.Join],
        transform: Callable[[str], Any] | None = None,
    ) -> None:
        """
        Args:
            field_name: Name of the field in the filter expression (e.g., "project_name")
            target_table: SQLAlchemy table to apply the filter on (e.g., GroupRow.__table__)
            target_column: Column name in the target table (e.g., "name")
            join_builder: Function that builds the JOIN clause given the base table
            transform: Optional transform function for the field value
        """
        self.field_name = field_name
        self.target_table = target_table
        self.target_column = target_column
        self.transform = transform
        self.join_builder = join_builder

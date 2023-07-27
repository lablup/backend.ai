from typing import Any, Callable, NamedTuple

import sqlalchemy as sa


class ArrayFieldItem(NamedTuple):
    column_name: str


class JSONFieldItem(NamedTuple):
    column_name: str
    key_name: str


FieldSpecItem = tuple[str | ArrayFieldItem | JSONFieldItem, Callable[[str], Any] | None]
OrderSpecItem = tuple[str | ArrayFieldItem | JSONFieldItem, Callable[[sa.Column], Any] | None]

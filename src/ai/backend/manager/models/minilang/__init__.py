from typing import Any, Callable, NamedTuple

import sqlalchemy as sa


class JSONFieldItem(NamedTuple):
    column_name: str
    key_name: str


FieldSpecItem = tuple[str | JSONFieldItem, Callable[[str], Any] | None]
OrderSpecItem = tuple[str | JSONFieldItem, Callable[[sa.Column], Any] | None]

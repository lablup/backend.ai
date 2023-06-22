from typing import Any, Callable, NamedTuple, Optional, Tuple


class JSONFieldItem(NamedTuple):
    column_name: str
    key_name: str


FieldSpecItem = Tuple[str | JSONFieldItem, Optional[Callable[[str], Any]]]

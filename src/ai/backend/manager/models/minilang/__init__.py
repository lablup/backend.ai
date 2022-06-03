from typing import (
    Any,
    Callable,
    Optional,
    Tuple,
)

FieldSpecItem = Tuple[str, Optional[Callable[[str], Any]]]

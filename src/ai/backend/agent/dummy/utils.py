import random
from typing import Any


def get_delay_from_cfg(value: Any) -> float:
    match value:
        case float():
            return value
        case (a, b):
            return random.uniform(a, b)
        case None:
            return 0
        case _:
            raise RuntimeError("Value must be checked before assigned to config")

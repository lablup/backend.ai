from __future__ import annotations

import enum
from typing import Final

__all__: Final[tuple[str, ...]] = ("NetworkType",)


class NetworkType(enum.StrEnum):
    VOLATILE = "volatile"
    PERSISTENT = "persistent"
    HOST = "host"

from __future__ import annotations

from typing import NewType

from ai.backend.common.types import BinarySize

WekaQuotaID = NewType("WekaQuotaID", str)


def format_size(s: BinarySize) -> str:
    ss = str(s)
    if ss.endswith("bytes"):
        return ss.replace("bytes", "B").replace(" ", "")
    return ss.replace(" ", "")

from __future__ import annotations

import enum
from typing import NewType

VASTQuotaID = NewType("VASTQuotaID", str)


class APIVersion(enum.StrEnum):
    V1 = "v1"
    V2 = "v2"
    LATEST = "latest"

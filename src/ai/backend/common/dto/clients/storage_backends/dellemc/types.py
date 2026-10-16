from __future__ import annotations

import enum
from typing import NewType

OneFSQuotaID = NewType("OneFSQuotaID", str)


class OneFSQuotaType(enum.StrEnum):
    DIRECTORY = "directory"
    USER = "user"
    GROUP = "group"

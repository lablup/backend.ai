from __future__ import annotations

import enum
from typing import Annotated

from pydantic import PlainSerializer

CommaSeparatedFields = Annotated[
    list[str], PlainSerializer(lambda fields: ",".join(fields), return_type=str)
]


class NetAppJobResponseCode(enum.StrEnum):
    QUOTA_ALEADY_ENABLED = "5308507"


class NetAppXCPEntryType(enum.Enum):
    FILE = 0
    DIRECTORY = 1
    SYMLINK = 2

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AppConfigPolicyData:
    id: uuid.UUID
    config_name: str
    scope_sources: Sequence[str]
    created_at: datetime
    updated_at: datetime

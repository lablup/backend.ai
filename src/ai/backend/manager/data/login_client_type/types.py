from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

__all__ = ("LoginClientTypeData",)


@dataclass(frozen=True)
class LoginClientTypeData:
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    modified_at: datetime

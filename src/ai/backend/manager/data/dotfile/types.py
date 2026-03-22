from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass


class DotfileScope(enum.StrEnum):
    DOMAIN = "domain"
    GROUP = "group"
    USER = "user"


DotfileEntityKey = str | uuid.UUID


@dataclass(frozen=True)
class DotfileEntry:
    path: str
    perm: str
    data: str


@dataclass(frozen=True)
class DotfileQueryResult:
    entries: list[DotfileEntry]
    leftover_space: int

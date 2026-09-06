from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass
class UserProjectEntityUnbinder:
    """Names the users to remove from a project."""

    user_uuids: list[UUID]
    project_id: UUID

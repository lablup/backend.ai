from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.repositories.ops.v2.seed.types import SeedRosterWrite
from ai.backend.manager.seed.base import SeedItems, SeedRejection, SeedRelationItem


class ProjectMemberSeed(SeedRelationItem):
    """One user on a project's roster, joined as the roster API joins one: the project's
    auto_assign roles are granted with it."""

    project_id: ProjectID
    user_id: UserID

    @override
    def key(self) -> str:
        return f"{self.project_id}:{self.user_id}"

    @override
    def write(self) -> SeedRosterWrite:
        return SeedRosterWrite(project_id=self.project_id, user_id=self.user_id)

    @override
    def check(self) -> list[str]:
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[ProjectMemberSeed]]) -> list[SeedRejection]:
        """None: the roster refuses an item naming a personal project, a missing entity
        or a user outside the project's domain when it is written."""
        return []

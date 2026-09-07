"""A project's roster, written through the roster ops."""

from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.repositories.ops.v2.roster.provider import RosterOpsProvider
from ai.backend.manager.repositories.ops.v2.roster.write import RosterLeaveResult

__all__ = ("RbacRosterRepository",)


class RbacRosterRepository:
    """Who is on a project's roster."""

    _ops: RosterOpsProvider

    def __init__(self, ops_provider: RosterOpsProvider) -> None:
        self._ops = ops_provider

    async def join_members(
        self,
        project_id: ProjectID,
        user_ids: Sequence[UserID],
        role_id: RoleID | None = None,
    ) -> list[UserData]:
        """Put the named users on the roster, granting ``role_id`` or the project's
        auto_assign roles. Answers who joined."""
        async with self._ops.write_ops() as w:
            return await w.join_members(project_id, user_ids, role_id)

    async def leave_members(
        self, project_id: ProjectID, user_ids: Sequence[UserID]
    ) -> RosterLeaveResult:
        """Take the named users off the roster, reporting the ones that could not."""
        async with self._ops.write_ops() as w:
            return await w.leave_members(project_id, user_ids)

    async def join_member(self, project_id: ProjectID, user_id: UserID) -> None:
        """Put one user on the roster. Idempotent."""
        async with self._ops.write_ops() as w:
            await w.join_member(project_id, user_id)

    async def leave_member(self, project_id: ProjectID, user_id: UserID) -> None:
        """Take one user off the roster. Silent where they were not on it."""
        async with self._ops.write_ops() as w:
            await w.leave_member(project_id, user_id)

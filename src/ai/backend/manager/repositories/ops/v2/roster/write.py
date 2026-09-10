"""Roster writes: who is on a project's roster and what joining grants.

A user on a project roster is a share capped to read, and granting the project's roles
is the second step of joining rather than part of the same fact (BEP-1076). Both steps
land in one primitive so a caller cannot write one without the other.

A personal project takes no member beyond the user it was created with. The refusal is
here, so no path can add one: the projects a user is enrolled in are narrowed by several
callers, and a filter each of them applies is a filter each of them can forget.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass, field
from typing import ClassVar

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.data.project.types import UnassignUserFailure
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.resource import (
    PersonalProjectMemberAdditionError,
    ProjectNotFound,
)
from ai.backend.manager.models.project import ProjectRow, ProjectType
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.virtual_entity.queries import user_scope_membership_exists
from ai.backend.manager.repositories.ops.v2.cap import V2CapOps
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps

__all__ = ("RosterLeaveResult", "V2RosterWriteOps")


@dataclass
class RosterLeaveResult:
    """Who left the roster, and which named users could not."""

    members: list[UserData] = field(default_factory=list)
    failures: list[UnassignUserFailure] = field(default_factory=list)


class V2RosterWriteOps(V2WriteOps, V2CapOps):
    """The v2 write ops plus a project's roster."""

    # A project roster caps its users to read.
    _MEMBER_CAP: ClassVar[Permission] = Permission.READ

    async def join_member(self, project_id: ProjectID, user_id: UserID) -> None:
        """Put one user on the project's roster. Idempotent; refuses a personal
        project."""
        await self._refuse_personal_project(project_id)
        await self._join(project_id, user_id)

    async def join_members(
        self,
        project_id: ProjectID,
        user_ids: Sequence[UserID],
        role_id: RoleID | None = None,
    ) -> list[UserData]:
        """Put the named users on the project's roster and grant them ``role_id``, or
        the project's auto_assign roles where none is named. Answers who was added.

        Narrowed to users of the project's domain that are not already on it: a user
        outside the domain is not a member the project can take, and one already on the
        roster is not added again.
        """
        if not user_ids:
            return []
        await self._refuse_personal_project(project_id)
        if role_id is not None and not await self._role_exists(role_id):
            raise InvalidAPIParameters(f"Role not found: {role_id}")
        rows = await self._joinable_users(project_id, user_ids)
        if not rows:
            return []
        for row in rows:
            await self._join(project_id, UserID(row.uuid))
        if role_id is not None:
            await self._bulk_insert_ignore_conflicts([
                UserRoleRow(user_id=row.uuid, role_id=role_id) for row in rows
            ])
        return [row.to_data() for row in rows]

    async def leave_member(self, project_id: ProjectID, user_id: UserID) -> None:
        """Take one user off the project's roster. Silent where they were not on it."""
        await self._project_type(project_id)
        await self._leave(project_id, user_id)

    async def leave_members(
        self, project_id: ProjectID, user_ids: Sequence[UserID]
    ) -> RosterLeaveResult:
        """Take the named users off the project's roster, reporting the ones that could
        not leave and why."""
        await self._project_type(project_id)
        if not user_ids:
            return RosterLeaveResult()
        requested = set(user_ids)
        existing = set(
            (
                await self._sess.scalars(sa.select(UserRow.uuid).where(UserRow.uuid.in_(requested)))
            ).all()
        )
        joined_rows = (
            await self._sess.scalars(
                sa.select(UserRow).where(
                    UserRow.uuid.in_(requested),
                    user_scope_membership_exists(ProjectEntityType(), project_id, UserRow.uuid),
                )
            )
        ).all()
        joined = {row.uuid for row in joined_rows}
        for user_id in requested:
            await self._leave(project_id, UserID(user_id))
        failures = [
            UnassignUserFailure(user_id=uid, reason="User does not exist.")
            for uid in requested - existing
        ] + [
            UnassignUserFailure(user_id=uid, reason="User is not assigned to this project.")
            for uid in existing - joined
        ]
        return RosterLeaveResult(
            members=[row.to_data() for row in joined_rows],
            failures=failures,
        )

    async def _role_exists(self, role_id: RoleID) -> bool:
        stmt = sa.select(sa.literal(1)).select_from(RoleRow).where(RoleRow.id == role_id)
        return (await self._sess.execute(stmt)).first() is not None

    async def _joinable_users(
        self, project_id: ProjectID, user_ids: Collection[UserID]
    ) -> list[UserRow]:
        """The named users that belong to the project's domain and are not yet on its
        roster."""
        project_domain = (
            sa.select(ProjectRow.domain_name).where(ProjectRow.id == project_id).scalar_subquery()
        )
        return list(
            (
                await self._sess.scalars(
                    sa.select(UserRow).where(
                        UserRow.uuid.in_(user_ids),
                        UserRow.domain_name == project_domain,
                        ~user_scope_membership_exists(
                            ProjectEntityType(), project_id, UserRow.uuid
                        ),
                    )
                )
            ).all()
        )

    async def _project_type(self, project_id: ProjectID) -> ProjectType:
        """The kind of project the id names; a roster write onto one that is not there
        is refused rather than silently writing an edge to nothing."""
        project_type = await self._sess.scalar(
            sa.select(ProjectRow.type).where(ProjectRow.id == project_id)
        )
        if project_type is None:
            raise ProjectNotFound(f"Project not found: {project_id}")
        return project_type

    async def _refuse_personal_project(self, project_id: ProjectID) -> None:
        """Refuse the write when the project is a personal one, which keeps its owner as
        its only member."""
        if await self._project_type(project_id) is ProjectType.PERSONAL:
            raise PersonalProjectMemberAdditionError(
                f"Personal project takes no members: {project_id}"
            )

    async def _revoke_project_roles(self, project_id: ProjectID, user_id: UserID) -> None:
        """Unmap the user from every role of the project — the reverse of what joining
        granted, read the same way."""
        project_role_ids = sa.select(RoleRow.id).where(
            RoleRow.scope_type == ProjectEntityType(),
            RoleRow.scope_id == project_id,
        )
        await self._sess.execute(
            sa.delete(UserRoleRow).where(
                UserRoleRow.user_id == user_id,
                UserRoleRow.role_id.in_(project_role_ids),
            )
        )

    async def _join(self, project_id: ProjectID, user_id: UserID) -> None:
        """Put the user on the project's roster — a share capped to read — and grant the
        project's auto_assign roles. The project is provisioned first: one created before
        the graph, or by a data migration, has no virtual entity yet."""
        await self._provision([project_id])
        membership_id = await self._reset_share(project_id, user_id)
        await self._insert_caps(membership_id, dict.fromkeys(self._bits_of(self._MEMBER_CAP)))
        await self._grant_auto_assign_roles([project_id], user_id)

    async def _leave(self, project_id: ProjectID, user_id: UserID) -> None:
        """Take the user off the project's roster — the reverse of :meth:`_join`, the
        cap rows going with the edge, and the project's roles taken back. Silent where
        the user was never on it.

        Taking the roles back is the other half of removal, not the caller's to remember
        (BEP-1076): a role may only be chosen from the project's own, so holding one
        without being on the roster is not a state that arises. What comes back is the
        roles of this project that this user holds."""
        await self._disown([project_id], user_id)
        await self._revoke_project_roles(project_id, user_id)

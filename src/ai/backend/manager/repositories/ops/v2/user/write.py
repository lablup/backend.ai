"""User provisioning writes: creating a user in full within one transaction.

Only the user domain provisions a user, so the primitives sit here: the general v2
write ops plus these, and a repository handed the general ops never sees them.

Setting the user's projects is its own method — the projects are stated again on every
update, so joining them is not part of becoming a user. Creation calls it inside the
same transaction.
"""

from __future__ import annotations

import re
from collections.abc import Collection
from dataclasses import dataclass
from re import Pattern
from typing import ClassVar

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.keypair.types import KeyPairData, KeyPairSecrets
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.keypair.creators import DefaultKeypairCreator
from ai.backend.manager.models.project import ProjectRow, ProjectType
from ai.backend.manager.models.project.creators import ProjectCreator
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.user.creators import UserCreator
from ai.backend.manager.models.virtual_entity.queries import user_scope_membership_query
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.roster.write import V2RosterWriteOps


@dataclass
class FullUserCreator:
    """The user to create and what its default keypair is made of. The domain it is
    created in is the user spec's own, and the keypair's active and admin flags are
    read off the user that was written rather than guessed from the spec."""

    user: UserCreator
    keypair_secrets: KeyPairSecrets
    keypair_resource_policy: str
    keypair_rate_limit: int | None = None


@dataclass
class FullUserCreatorResult:
    """A fully provisioned user and the keypair it authorizes with."""

    user: UserData
    keypair: KeyPairData


class V2UserWriteOps(V2RosterWriteOps):
    """The roster write ops plus provisioning a user."""

    # groups.name is a slug of at most 64 characters; the tail is reserved for the
    # collision suffix a personal project's name may need.
    _NON_SLUG_CHARS: ClassVar[Pattern[str]] = re.compile(r"[^\w.-]")
    _SLUG_SEPARATOR_RUN: ClassVar[Pattern[str]] = re.compile(r"[._-]{2,}")
    _SLUG_EDGE_CHARS: ClassVar[str] = "._-"
    _PROJECT_NAME_BASE_LIMIT: ClassVar[int] = 60
    _PROJECT_NAME_SUFFIX_LIMIT: ClassVar[int] = 1000

    async def user_exists(self, email: str, username: str) -> bool:
        """Whether an account already holds either name."""
        return (
            await self._sess.scalar(
                sa.select(
                    sa.exists().where(sa.or_(UserRow.email == email, UserRow.username == username))
                )
            )
        ) or False

    async def create_user(self, creation: FullUserCreator) -> FullUserCreatorResult:
        """Provision a user: the row, its virtual entity, the domain that owns and
        governs it, the roles its scope's and its domain's presets call for, the keypair
        it authorizes with, and the personal project it alone belongs to."""
        domain_id = creation.user.domain_id
        # The user is created in its domain, so the domain has to be in the graph
        # first: one created before the graph, or by a data migration, has no node yet.
        await self._provision([domain_id])
        # Writes the user's place on the domain's roster too: the domain is the scope
        # the spec is created in, so it owns and governs the user.
        user = await self.create_role_managed_entity(creation.user)
        user_id = UserID(user.id)
        await self._grant_auto_assign_roles([user_id, domain_id], user_id)
        keypair = await self._create_default_keypair(user, creation)
        await self._create_personal_project(user_id, user.username, domain_id)
        return FullUserCreatorResult(user=user, keypair=keypair)

    async def _create_default_keypair(
        self, user: UserData, creation: FullUserCreator
    ) -> KeyPairData:
        """Write the keypair the user authorizes with. Its flags mirror the user as it
        was written — the row's own defaults may have answered for the spec."""
        return await self.create_field(
            UserID(user.id),
            DefaultKeypairCreator(
                secrets=creation.keypair_secrets,
                is_active=user.status == UserStatus.ACTIVE,
                is_admin=user.role in (UserRole.SUPERADMIN, UserRole.ADMIN),
                resource_policy=creation.keypair_resource_policy,
                rate_limit=creation.keypair_rate_limit,
            ),
        )

    async def join_projects(
        self,
        user_id: UserID,
        domain_id: DomainID,
        project_ids: Collection[ProjectID],
    ) -> None:
        """Put the user on each project's roster — the domain's model-store projects
        always included, ``project_ids`` narrowed to projects that exist in the domain,
        and personal projects left out."""
        domain_name = await self._domain_name(domain_id)
        for project_id in await self._member_project_ids(domain_name, project_ids):
            await self._join(project_id, user_id)

    async def replace_user_projects(
        self,
        user_id: UserID,
        domain_name: str,
        project_ids: Collection[ProjectID],
    ) -> None:
        """Set the user's projects to ``project_ids``, the domain's model-store projects
        always included.

        Only the projects entering or leaving the set are touched, so an unchanged
        membership keeps its rows. Personal projects stand outside: none is joined and
        the user's own is never left. Leaving takes the project's roles back.
        """
        target = await self._member_project_ids(domain_name, project_ids)
        joined = await self._joined_project_ids(user_id)
        for project_id in sorted(joined - target, key=str):
            await self._leave(project_id, user_id)
        for project_id in sorted(target - joined, key=str):
            await self._join(project_id, user_id)

    async def _create_personal_project(
        self, user_id: UserID, username: str, domain_id: DomainID
    ) -> ProjectData:
        """Create the user's personal project in its domain and put the user on the
        roster as its only member. The project is created in the domain, so the domain's
        roles reach it the way they reach every other project.

        Joins through the primitive rather than :meth:`join_member`, which refuses a
        personal project: the owner is the one member such a project ever takes."""
        domain_name = await self._domain_name(domain_id)
        project = await self.create_role_managed_entity(
            ProjectCreator.personal(
                name=await self._personal_project_name(domain_name, username, user_id),
                domain_id=domain_id,
                domain_name=domain_name,
                user_id=user_id,
            )
        )
        await self._join(ProjectID(project.id), user_id)
        return project

    async def _domain_name(self, domain_id: DomainID) -> str:
        """The name of the domain the user was created in. The user row's own
        ``domain_name`` is filled by the database and is not loaded yet at this point."""
        name = await self._sess.scalar(sa.select(DomainRow.name).where(DomainRow.id == domain_id))
        if name is None:
            raise DomainNotFound(f"Domain '{domain_id}' does not exist.")
        return name

    async def _personal_project_name(self, domain_name: str, username: str, user_id: UserID) -> str:
        """The username as a slug, given a numeric suffix when the domain already holds
        a project of that name. Falls back to the user id, which no name can collide
        with, when the username slugifies to nothing or every suffix is taken."""
        base = self._slugify(username) or str(user_id)
        taken = set(
            (
                await self._sess.scalars(
                    sa.select(ProjectRow.name).where(
                        ProjectRow.domain_name == domain_name,
                        sa.or_(
                            ProjectRow.name == base,
                            ProjectRow.name.like(f"{self._escape_like(base)}-%", escape="\\"),
                        ),
                    )
                )
            ).all()
        )
        if base not in taken:
            return base
        for suffix in range(2, self._PROJECT_NAME_SUFFIX_LIMIT):
            candidate = f"{base}-{suffix}"
            if candidate not in taken:
                return candidate
        return str(user_id)

    def _slugify(self, value: str) -> str:
        """``value`` reduced to what the project name column accepts: every other
        character becomes a hyphen, runs of separators collapse, and the edges are
        trimmed. Empty when nothing survives."""
        slug = self._SLUG_SEPARATOR_RUN.sub("-", self._NON_SLUG_CHARS.sub("-", value))
        slug = slug.strip(self._SLUG_EDGE_CHARS)[: self._PROJECT_NAME_BASE_LIMIT]
        return slug.rstrip(self._SLUG_EDGE_CHARS)

    def _escape_like(self, value: str) -> str:
        """``value`` as a literal LIKE prefix; a slug may carry an underscore."""
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    async def _member_project_ids(
        self,
        domain_name: str,
        project_ids: Collection[ProjectID],
    ) -> set[ProjectID]:
        """``project_ids`` narrowed to the domain's real projects, plus the domain's
        model-store projects that every user joins. A personal project is never among
        them: it takes no member beyond the user it was created with."""
        stmt = sa.select(ProjectRow.id).where(
            ProjectRow.domain_name == domain_name,
            ProjectRow.type != ProjectType.PERSONAL,
            sa.or_(ProjectRow.id.in_(project_ids), ProjectRow.type == ProjectType.MODEL_STORE),
        )
        return {ProjectID(row) for row in (await self._sess.scalars(stmt)).all()}

    async def _joined_project_ids(self, user_id: UserID) -> set[ProjectID]:
        """The projects the user is on the roster of, personal ones left out."""
        stmt = user_scope_membership_query(PROJECT_SCOPE_TYPE, user_id).where(
            VirtualEntityRow.entity_id.not_in(
                sa.select(ProjectRow.id).where(ProjectRow.type == ProjectType.PERSONAL)
            )
        )
        return {ProjectID(row.scope_id) for row in (await self._sess.execute(stmt)).all()}

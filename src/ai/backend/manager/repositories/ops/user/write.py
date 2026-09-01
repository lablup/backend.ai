"""User provisioning writes: creating a user in full within one transaction.

Only the user domain provisions a user, so the primitive sits here:
:class:`UserWriteOps` extends the RBAC write ops with it, and a repository handed the
RBAC ones never sees it.

Extending the legacy RBAC lineage is temporary: the primitives user creation stands on
live only on the legacy RBAC ops. The move to the v2 lineage (``ops/v2/user/``) follows
the removal of the legacy path in BA-7574.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE, DomainID
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.keypair.types import KeyPairData, KeyPairSecrets
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.keypair.creators import DefaultKeypairCreator
from ai.backend.manager.models.project import ProjectRow, ProjectType
from ai.backend.manager.models.user import UserRow, UserStatus
from ai.backend.manager.repositories.ops.rbac.provider import (
    EntityMembersAddition,
    RBACWriteOps,
    ScopeCreation,
    ScopeUserMember,
)


@dataclass
class FullUserCreation:
    """Everything needed to provision a user in full: the user-scope creation, the
    scopes to enroll in, the default keypair's policy, and that keypair's key material.

    The caller generates ``keypair_secrets`` because the secret key is encrypted through
    the key provider pool before it is bound.
    """

    creation: ScopeCreation[UserRow]
    domain_id: DomainID
    project_ids: Collection[ProjectID]
    keypair_resource_policy: str
    keypair_secrets: KeyPairSecrets
    keypair_rate_limit: int | None = None


@dataclass
class FullUserCreationResult:
    """A fully provisioned user: the row and the keypair the user authorizes with."""

    user_row: UserRow
    keypair: KeyPairData


class UserWriteOps(RBACWriteOps):
    """The RBAC write ops plus provisioning a user in full."""

    async def create_full_user(
        self,
        full_creation: FullUserCreation,
    ) -> FullUserCreationResult:
        """Provision a user end to end in one transaction.

        Creates the user scope (row, virtual scope, own-scope roles) and grants those
        roles, writes the keypair the user authorizes with, then enrolls the user in
        its domain's and projects' virtual scopes.
        """
        user_row = await self._create_user_scope(full_creation.creation)
        user_id = UserID(user_row.uuid)
        keypair = await self._create_default_keypair(user_id, user_row, full_creation)
        await self._enroll_in_domain(user_id, full_creation.domain_id)
        await self._enroll_in_projects(user_id, full_creation.domain_id, full_creation.project_ids)

        # The insert leaves the server-default columns unloaded, and default_keypair is the
        # keypair created just above; reload both so callers can read the row without a
        # sync-context lazy refresh.
        await self._sess.flush()
        await self._sess.refresh(user_row)
        await self._sess.refresh(user_row, ["default_keypair"])
        return FullUserCreationResult(user_row=user_row, keypair=keypair)

    async def _create_user_scope(self, creation: ScopeCreation[UserRow]) -> UserRow:
        """Write the user row with its virtual scope and own-scope roles, and grant
        those roles to the user."""
        creation_result = await self.create_scope(creation)
        user_row = creation_result.row
        await self.assign_roles_to_user(UserID(user_row.uuid), creation_result.auto_grant_role_ids)
        return user_row

    async def _create_default_keypair(
        self,
        user_id: UserID,
        user_row: UserRow,
        full_creation: FullUserCreation,
    ) -> KeyPairData:
        """Write the keypair the user authorizes with."""
        return await self.create_field(
            user_id,
            DefaultKeypairCreator(
                secrets=full_creation.keypair_secrets,
                is_active=user_row.status == UserStatus.ACTIVE,
                is_admin=user_row.role in (UserRole.SUPERADMIN, UserRole.ADMIN),
                resource_policy=full_creation.keypair_resource_policy,
                rate_limit=full_creation.keypair_rate_limit,
            ),
        )

    async def _enroll_in_domain(self, user_id: UserID, domain_id: DomainID) -> None:
        """Enroll the user in its domain's virtual scope, inheriting the domain's
        permissions over what the user owns."""
        domain_scope = ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=domain_id)
        await self.ensure_scope(domain_scope)
        await self.add_bulk_inheriting_members(
            EntityMembersAddition(scope=domain_scope, members=[ScopeUserMember(user_id=user_id)])
        )

    async def _enroll_in_projects(
        self,
        user_id: UserID,
        domain_id: DomainID,
        project_ids: Collection[ProjectID],
    ) -> None:
        """Enroll the user in each project's virtual scope — the domain's model-store
        projects always included, ``project_ids`` narrowed to projects that exist in
        the domain, and personal projects left out."""
        member = ScopeUserMember(user_id=user_id)
        for project_id in await self._domain_member_project_ids(domain_id, project_ids):
            project_scope = ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=project_id)
            await self.ensure_scope(project_scope)
            await self.add_bulk_members(
                EntityMembersAddition(scope=project_scope, members=[member])
            )

    async def _domain_member_project_ids(
        self,
        domain_id: DomainID,
        project_ids: Collection[ProjectID],
    ) -> list[ProjectID]:
        """``project_ids`` narrowed to the domain's real projects, plus the domain's
        model-store projects that every user joins. A personal project is never among
        them: it takes no member beyond the user it was created with."""
        stmt = (
            sa.select(ProjectRow.id)
            .join(DomainRow, DomainRow.name == ProjectRow.domain_name)
            .where(
                DomainRow.id == domain_id,
                ProjectRow.type != ProjectType.PERSONAL,
                sa.or_(ProjectRow.id.in_(project_ids), ProjectRow.type == ProjectType.MODEL_STORE),
            )
        )
        return [ProjectID(row) for row in (await self._sess.scalars(stmt)).all()]

"""Purge specs for the users table and the rows a user leaves behind."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.error_log import ErrorLogID
from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.role import ROLE_ENTITY_TYPE, RoleID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder_permission import VFolderPermissionID
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.user import UserPurgeFailure
from ai.backend.manager.models.error_log.row import ErrorLogRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import AssocGroupUserRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.session.row import (
    AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES,
    SessionRow,
)
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.specs.purger import (
    EntityBatchPurger,
    EntityPurger,
    FieldBatchPurger,
)
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.vfolder.row import VFolderPermissionRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow


@dataclass
class UserErrorLogPurger(FieldBatchPurger[UserID, ErrorLogRow, ErrorLogID]):
    """Clears the errors recorded against a user."""

    @override
    def build_subquery(self, owner_id: UserID) -> sa.sql.Select[Any]:
        return sa.select(ErrorLogRow).where(ErrorLogRow.user == owner_id)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ErrorLogRow) -> ErrorLogID:
        return row.id


@dataclass
class UserKeyPairPurger(FieldBatchPurger[UserID, KeyPairRow, KeyPairID]):
    """Clears the keypairs a user authorizes with."""

    @override
    def build_subquery(self, owner_id: UserID) -> sa.sql.Select[Any]:
        return sa.select(KeyPairRow).where(KeyPairRow.user == owner_id)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: KeyPairRow) -> KeyPairID:
        return row.id


@dataclass
class UserVFolderPermissionPurger(
    FieldBatchPurger[UserID, VFolderPermissionRow, VFolderPermissionID]
):
    """Clears the vfolder permissions granted to a user."""

    @override
    def build_subquery(self, owner_id: UserID) -> sa.sql.Select[Any]:
        return sa.select(VFolderPermissionRow).where(VFolderPermissionRow.user == owner_id)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: VFolderPermissionRow) -> VFolderPermissionID:
        return VFolderPermissionID(row.id)


@dataclass
class UserGroupAssociationPurger(FieldBatchPurger[UserID, AssocGroupUserRow, ProjectID]):
    """Clears the legacy project association rows a user holds."""

    @override
    def build_subquery(self, owner_id: UserID) -> sa.sql.Select[Any]:
        return sa.select(AssocGroupUserRow).where(AssocGroupUserRow.user_id == owner_id)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: AssocGroupUserRow) -> ProjectID:
        return row.group_id


@dataclass
class UserScopeAssociationPurger(FieldBatchPurger[UserID, AssociationScopesEntitiesRow, UUID]):
    """Clears the legacy scope associations a user leaves behind, on both sides: the
    rows enrolling the user under other scopes, and the rows enrolled under the scope
    the user is."""

    @override
    def build_subquery(self, owner_id: UserID) -> sa.sql.Select[Any]:
        return sa.select(AssociationScopesEntitiesRow).where(
            sa.or_(
                sa.and_(
                    AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                    AssociationScopesEntitiesRow.entity_id == str(owner_id),
                ),
                sa.and_(
                    AssociationScopesEntitiesRow.scope_type == ScopeType.USER,
                    AssociationScopesEntitiesRow.scope_id == str(owner_id),
                ),
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: AssociationScopesEntitiesRow) -> UUID:
        return row.id


@dataclass
class UserProjectRolePurger(FieldBatchPurger[UserID, UserRoleRow, RoleID]):
    """Unmaps a user from the roles a project scope owns.

    The project's roles are the role entities enrolled in its virtual entity.
    """

    project_id: ProjectID

    @override
    def build_subquery(self, owner_id: UserID) -> sa.sql.Select[Any]:
        project_role_ids = (
            sa.select(EntityMembershipRow.entity_id)
            .join(VirtualEntityRow, EntityMembershipRow.virtual_entity_id == VirtualEntityRow.id)
            .where(
                VirtualEntityRow.entity_type == PROJECT_SCOPE_TYPE,
                VirtualEntityRow.entity_id == self.project_id,
                EntityMembershipRow.entity_type == ROLE_ENTITY_TYPE,
            )
        )
        return sa.select(UserRoleRow).where(
            UserRoleRow.user_id == owner_id,
            UserRoleRow.role_id.in_(project_role_ids),
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: UserRoleRow) -> RoleID:
        return row.role_id


@dataclass
class UserSessionGroupPurger(EntityBatchPurger[SessionGroupRow, SessionGroupID]):
    """Clears the placement groups a user owns, each with the RBAC graph it left.

    A group is only a placement policy, but its members are not: dropping it while a
    member session still holds an agent would hide that session from the scheduler's
    per-agent member counts before its containers are gone. The purge therefore
    refuses while any member is still occupying resources, the same way it refuses
    while the user's vfolders are mounted to active kernels.
    """

    user_id: UserID

    @override
    def entity_id(self, row: SessionGroupRow) -> EntityIdentifier:
        return row.id

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[SessionGroupRow]]:
        return sa.select(SessionGroupRow).where(SessionGroupRow.owner_user_id == self.user_id)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return (
            ConflictCheck(
                condition=lambda: sa.and_(
                    ReplicaGroupRow.session_group_id == SessionGroupRow.id,
                    SessionGroupRow.owner_user_id == self.user_id,
                ),
                error=UserPurgeFailure(
                    "Some of the user's placement groups still belong to a replica group. "
                    "Delegate or remove their deployments first.",
                ),
            ),
            ConflictCheck(
                condition=lambda: sa.and_(
                    SessionRow.session_group_id == SessionGroupRow.id,
                    SessionGroupRow.owner_user_id == self.user_id,
                    SessionRow.status.in_(AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES),
                ),
                error=UserPurgeFailure(
                    "Some sessions of the user's placement groups are still occupying agents. "
                    "Wait for those sessions to terminate first.",
                ),
            ),
        )

    @override
    def to_data(self, row: SessionGroupRow) -> SessionGroupID:
        return row.id


@dataclass
class UserPurger(EntityPurger[UserRow, UserData]):
    """Removes a user along with the scope it was."""

    user_id: UserID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def row_class(self) -> type[UserRow]:
        return UserRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return UserRow.uuid

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: UserRow) -> UserData:
        return row.to_data()

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.errors.user import UserPurgeFailure
from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.models.group import AssocGroupUserRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.session.row import AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.vfolder import VFolderPermissionRow
from ai.backend.manager.repositories.base.purger import BatchPurger, BatchPurgerSpec
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityBatchPurgerSpec


@dataclass
class UserErrorLogBatchPurgerSpec(BatchPurgerSpec[ErrorLogRow]):
    """PurgerSpec for deleting all error logs belonging to a user."""

    user_uuid: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ErrorLogRow]]:
        return sa.select(ErrorLogRow).where(ErrorLogRow.__table__.c.user == self.user_uuid)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class UserKeyPairBatchPurgerSpec(BatchPurgerSpec[KeyPairRow]):
    """PurgerSpec for deleting all keypairs belonging to a user."""

    user_uuid: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[KeyPairRow]]:
        return sa.select(KeyPairRow).where(KeyPairRow.user == self.user_uuid)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class UserVFolderPermissionBatchPurgerSpec(BatchPurgerSpec[VFolderPermissionRow]):
    """PurgerSpec for deleting all vfolder permissions belonging to a user."""

    user_uuid: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[VFolderPermissionRow]]:
        return sa.select(VFolderPermissionRow).where(VFolderPermissionRow.user == self.user_uuid)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class UserGroupAssociationBatchPurgerSpec(BatchPurgerSpec[AssocGroupUserRow]):
    """PurgerSpec for deleting all group associations belonging to a user."""

    user_uuid: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[AssocGroupUserRow]]:
        return sa.select(AssocGroupUserRow).where(AssocGroupUserRow.user_id == self.user_uuid)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class UserSessionGroupBatchPurgerSpec(BatchPurgerSpec[SessionGroupRow]):
    """PurgerSpec for deleting the placement groups a user owns.

    A group is only a placement policy, but its members are not: dropping it
    while a member session still holds an agent would hide that session from the
    scheduler's per-agent member counts before its containers are gone. The
    purge therefore refuses while any member is still occupying resources, the
    same way it refuses while the user's vfolders are mounted to active kernels.
    """

    user_uuid: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[SessionGroupRow]]:
        return sa.select(SessionGroupRow).where(SessionGroupRow.owner_user_id == self.user_uuid)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return (
            ConflictCheck(
                condition=lambda: sa.and_(
                    ReplicaGroupRow.session_group_id == SessionGroupRow.id,
                    SessionGroupRow.owner_user_id == self.user_uuid,
                ),
                error=UserPurgeFailure(
                    "Some of the user's placement groups still belong to a replica group. "
                    "Delegate or remove their deployments first.",
                ),
            ),
            ConflictCheck(
                condition=lambda: sa.and_(
                    SessionRow.session_group_id == SessionGroupRow.id,
                    SessionGroupRow.owner_user_id == self.user_uuid,
                    SessionRow.status.in_(AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES),
                ),
                error=UserPurgeFailure(
                    "Some sessions of the user's placement groups are still occupying agents. "
                    "Wait for those sessions to terminate first.",
                ),
            ),
        )


@dataclass
class UserProjectRoleBatchPurgerSpec(BatchPurgerSpec[UserRoleRow]):
    """PurgerSpec for unmapping a user from the roles bound at a project scope."""

    user_uuid: UUID
    project_id: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[UserRoleRow]]:
        project_role_ids = sa.select(AssociationScopesEntitiesRow.entity_id).where(
            AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
            AssociationScopesEntitiesRow.scope_id == str(self.project_id),
            AssociationScopesEntitiesRow.entity_type == EntityType.ROLE,
        )
        return sa.select(UserRoleRow).where(
            UserRoleRow.user_id == self.user_uuid,
            sa.cast(UserRoleRow.role_id, sa.String).in_(project_role_ids),
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class UserBatchPurgerSpec(RBACEntityBatchPurgerSpec[UserRow]):
    """PurgerSpec for deleting a user with RBAC scope/permission cleanup."""

    user_uuid: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[UserRow]]:
        return sa.select(UserRow).where(UserRow.uuid == self.user_uuid)

    @override
    def element_type(self) -> RBACElementType:
        return RBACElementType.USER

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


def create_user_error_log_purger(user_uuid: UUID) -> BatchPurger[ErrorLogRow]:
    """Create a BatchPurger for deleting all error logs belonging to a user."""
    return BatchPurger(
        spec=UserErrorLogBatchPurgerSpec(user_uuid=user_uuid),
    )


def create_user_keypair_purger(user_uuid: UUID) -> BatchPurger[KeyPairRow]:
    """Create a BatchPurger for deleting all keypairs belonging to a user."""
    return BatchPurger(
        spec=UserKeyPairBatchPurgerSpec(user_uuid=user_uuid),
    )


def create_user_vfolder_permission_purger(user_uuid: UUID) -> BatchPurger[VFolderPermissionRow]:
    """Create a BatchPurger for deleting all vfolder permissions belonging to a user."""
    return BatchPurger(
        spec=UserVFolderPermissionBatchPurgerSpec(user_uuid=user_uuid),
    )


def create_user_group_association_purger(user_uuid: UUID) -> BatchPurger[AssocGroupUserRow]:
    """Create a BatchPurger for deleting all group associations belonging to a user."""
    return BatchPurger(
        spec=UserGroupAssociationBatchPurgerSpec(user_uuid=user_uuid),
    )


def create_user_project_role_purger(user_uuid: UUID, project_id: UUID) -> BatchPurger[UserRoleRow]:
    """Create a BatchPurger unmapping a user from the roles bound at a project scope."""
    return BatchPurger(
        spec=UserProjectRoleBatchPurgerSpec(user_uuid=user_uuid, project_id=project_id),
    )


def create_user_purger(user_uuid: UUID) -> BatchPurger[UserRow]:
    """Create a BatchPurger for deleting a user."""
    return BatchPurger(
        spec=UserBatchPurgerSpec(user_uuid=user_uuid),
        batch_size=1,  # We expect only one row to be deleted
    )


def create_user_session_group_purger(user_uuid: UUID) -> BatchPurger[SessionGroupRow]:
    """Create a BatchPurger for deleting the placement groups a user owns."""
    return BatchPurger(
        spec=UserSessionGroupBatchPurgerSpec(user_uuid=user_uuid),
    )

"""Purge specs for the users table and the rows a user leaves behind."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.error_log import ErrorLogID
from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.user import UserPurgeFailure
from ai.backend.manager.models.error_log.row import ErrorLogRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import AssocGroupUserRow
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
class UserVFolderPermissionPurger(FieldBatchPurger[UserID, VFolderPermissionRow, VFolderUUID]):
    """Clears the vfolder permissions granted to a user.

    Answers with the folders taken back rather than the rows removed: what the caller
    does next is take the share caps off those folders, and the row ids name nothing
    it can act on.
    """

    @override
    def build_subquery(self, owner_id: UserID) -> sa.sql.Select[Any]:
        return sa.select(VFolderPermissionRow).where(VFolderPermissionRow.user == owner_id)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: VFolderPermissionRow) -> VFolderUUID:
        return VFolderUUID(row.vfolder)


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

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.models.group import AssocGroupUserRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.vfolder import VFolderPermissionRow
from ai.backend.manager.repositories.base.purger import BatchPurger, BatchPurgerSpec


@dataclass
class UserErrorLogBatchPurgerSpec(BatchPurgerSpec[ErrorLogRow]):
    """PurgerSpec for deleting all error logs belonging to a user."""

    user_uuid: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ErrorLogRow]]:
        return sa.select(ErrorLogRow).where(
            ErrorLogRow.__table__.c.user == self.user_uuid  # type: ignore[attr-defined]
        )


@dataclass
class UserKeyPairBatchPurgerSpec(BatchPurgerSpec[KeyPairRow]):
    """PurgerSpec for deleting all keypairs belonging to a user."""

    user_uuid: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[KeyPairRow]]:
        return sa.select(KeyPairRow).where(KeyPairRow.user == self.user_uuid)


@dataclass
class UserVFolderPermissionBatchPurgerSpec(BatchPurgerSpec[VFolderPermissionRow]):
    """PurgerSpec for deleting all vfolder permissions belonging to a user."""

    user_uuid: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[VFolderPermissionRow]]:
        return sa.select(VFolderPermissionRow).where(VFolderPermissionRow.user == self.user_uuid)


@dataclass
class UserGroupAssociationBatchPurgerSpec(BatchPurgerSpec[AssocGroupUserRow]):
    """PurgerSpec for deleting all group associations belonging to a user."""

    user_uuid: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[AssocGroupUserRow]]:
        return sa.select(AssocGroupUserRow).where(AssocGroupUserRow.user_id == self.user_uuid)


@dataclass
class UserBatchPurgerSpec(BatchPurgerSpec[UserRow]):
    """PurgerSpec for deleting a user."""

    user_uuid: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[UserRow]]:
        return sa.select(UserRow).where(UserRow.uuid == self.user_uuid)


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


def create_user_purger(user_uuid: UUID) -> BatchPurger[UserRow]:
    """Create a BatchPurger for deleting a user."""
    return BatchPurger(
        spec=UserBatchPurgerSpec(user_uuid=user_uuid),
        batch_size=1,  # We expect only one row to be deleted
    )

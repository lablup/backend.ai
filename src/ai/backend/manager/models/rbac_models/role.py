from __future__ import annotations

import uuid
from datetime import datetime
from typing import (
    TYPE_CHECKING,
)

import sqlalchemy as sa
from sqlalchemy.orm import (
    Mapped,
    foreign,
    mapped_column,
    relationship,
)

from ai.backend.manager.data.permission.role import (
    RoleData,
    RoleDetailData,
)
from ai.backend.manager.data.permission.status import (
    RoleStatus,
)
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)

if TYPE_CHECKING:
    from .permission.object_permission import ObjectPermissionRow
    from .permission.permission_group import PermissionGroupRow
    from .user_role import UserRoleRow


def _get_mapped_user_role_rows_join_condition() -> sa.ColumnElement[bool]:
    from .user_role import UserRoleRow

    return RoleRow.id == foreign(UserRoleRow.role_id)


def _get_object_permission_rows_join_condition() -> sa.ColumnElement[bool]:
    from .permission.object_permission import ObjectPermissionRow

    return RoleRow.id == foreign(ObjectPermissionRow.role_id)


def _get_permission_group_rows_join_condition() -> sa.ColumnElement[bool]:
    from .permission.permission_group import PermissionGroupRow

    return RoleRow.id == foreign(PermissionGroupRow.role_id)


class RoleRow(Base):  # type: ignore[misc]
    __tablename__ = "roles"
    __table_args__ = (sa.Index("ix_id_status", "id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String(64), nullable=False)
    description: Mapped[str | None] = mapped_column("description", sa.Text, nullable=True)
    source: Mapped[RoleSource] = mapped_column(
        "source",
        StrEnumType(RoleSource, length=16),
        nullable=False,
        default=RoleSource.SYSTEM,
        server_default=str(RoleSource.SYSTEM),
    )
    status: Mapped[RoleStatus] = mapped_column(
        "status",
        StrEnumType(RoleStatus),
        nullable=False,
        default=RoleStatus.ACTIVE,
        server_default=RoleStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        "updated_at", sa.DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        "deleted_at", sa.DateTime(timezone=True), nullable=True
    )

    mapped_user_role_rows: Mapped[list[UserRoleRow]] = relationship(
        "UserRoleRow",
        back_populates="role_row",
        primaryjoin=_get_mapped_user_role_rows_join_condition,
    )
    object_permission_rows: Mapped[list[ObjectPermissionRow]] = relationship(
        "ObjectPermissionRow",
        back_populates="role_row",
        primaryjoin=_get_object_permission_rows_join_condition,
        viewonly=True,
    )
    permission_group_rows: Mapped[list[PermissionGroupRow]] = relationship(
        "PermissionGroupRow",
        back_populates="role_row",
        primaryjoin=_get_permission_group_rows_join_condition,
        viewonly=True,
    )

    def to_data(self) -> RoleData:
        return RoleData(
            id=self.id,
            name=self.name,
            source=self.source,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at or self.created_at,
            deleted_at=self.deleted_at,
            description=self.description,
        )

    def to_detail_data_without_users(self) -> RoleDetailData:
        """Convert to detail data without assigned users."""
        return RoleDetailData(
            id=self.id,
            name=self.name,
            source=self.source,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at or self.created_at,
            deleted_at=self.deleted_at,
            description=self.description,
            permission_groups=[pg_row.to_extended_data() for pg_row in self.permission_group_rows],
            object_permissions=[op_row.to_data() for op_row in self.object_permission_rows],
        )

"""migrate user data to roles

Revision ID: a4d56e86d9ee
Revises: 28fecac94e67
Create Date: 2025-08-06 21:28:29.354670

"""

import enum
import uuid
from collections.abc import Collection
from typing import Any, Optional, cast

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine import Connection, Row
from sqlalchemy.orm import foreign, registry, relationship

from ai.backend.manager.models.base import GUID, EnumValueType, IDColumn, metadata
from ai.backend.manager.models.rbac_models.migrate.types import PermissionCreateInputGroup
from ai.backend.manager.models.rbac_models.migrate.user import (
    ADMIN_ROLE_NAME_SUFFIX,
    ProjectData,
    ProjectUserAssociationData,
    RoleNameUtil,
    UserData,
    create_project_admin_role_and_permissions,
    create_project_user_role_and_permissions,
    create_user_self_role_and_permissions,
    map_user_to_project_role,
)

# revision identifiers, used by Alembic.
revision = "a4d56e86d9ee"
down_revision = "28fecac94e67"
branch_labels = None
depends_on = None


mapper_registry = registry(metadata=metadata)
Base: Any = mapper_registry.generate_base()  # TODO: remove Any after #422 is merged


class UserRole(enum.StrEnum):
    """
    User's role.
    """

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    MONITOR = "monitor"


class GroupRow(Base):
    __tablename__ = "groups"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = IDColumn()

    users = relationship("AssocGroupUserRow")
    scope_permissions: "list[ScopePermissionRow]" = relationship(
        "ScopePermissionRow",
        primaryjoin=lambda: GroupRow.id == sa.cast(foreign(ScopePermissionRow.scope_id), UUID),
    )


class AssocGroupUserRow(Base):
    __tablename__ = "association_groups_users"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = IDColumn()
    user_id: uuid.UUID = sa.Column("user_id", GUID, nullable=False)
    group_id: uuid.UUID = sa.Column(
        "group_id",
        GUID,
        sa.ForeignKey("groups.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )


class UserRow(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    uuid = IDColumn("uuid")
    username = sa.Column("username", sa.String(length=64), unique=True)
    domain_name = sa.Column("domain_name", sa.String(length=64), index=True)
    role = sa.Column("role", EnumValueType(UserRole), default=UserRole.USER)


class UserRoleRow(Base):
    __tablename__ = "user_roles"
    __table_args__ = {"extend_existing": True}
    id: uuid.UUID = IDColumn()
    user_id: uuid.UUID = sa.Column("user_id", GUID, nullable=False)
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)


class RoleRow(Base):
    __tablename__ = "roles"
    __table_args__ = {"extend_existing": True}
    id: uuid.UUID = IDColumn()
    name: str = sa.Column("name", sa.String(64), nullable=False)
    description: Optional[str] = sa.Column("description", sa.Text, nullable=True)


class ScopePermissionRow(Base):
    __tablename__ = "scope_permissions"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = IDColumn()
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)
    entity_type: str = sa.Column(
        "entity_type", sa.String(32), nullable=False
    )  # e.g., "session", "vfolder", "image" etc.
    operation: str = sa.Column(
        "operation", sa.String(32), nullable=False
    )  # e.g., "create", "read", "delete", "grant:create", "grant:read" etc.
    scope_type: str = sa.Column(
        "scope_type", sa.String(32), nullable=False
    )  # e.g., "global", "domain", "project", "user" etc.
    scope_id: str = sa.Column(
        "scope_id", sa.String(64), nullable=False
    )  # e.g., "global", "domain_id", "project_id", "user_id" etc.


class AssociationScopesEntitiesRow(Base):
    __tablename__ = "association_scopes_entities"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = IDColumn()
    scope_type: str = sa.Column(
        "scope_type",
        sa.String(32),
        nullable=False,
    )  # e.g., "global", "domain", "project", "user" etc.
    scope_id: str = sa.Column(
        "scope_id",
        sa.String(64),
        nullable=False,
    )  # e.g., "global", "domain_id", "project_id", "user_id" etc.
    entity_type: str = sa.Column(
        "entity_type", sa.String(32), nullable=False
    )  # e.g., "session", "vfolder", "image" etc.
    entity_id: str = sa.Column(
        "entity_id",
        sa.String(64),
        nullable=False,
    )


def _insert_if_data_exists(db_conn: Connection, row_type, data: Collection) -> None:
    if data:
        db_conn.execute(sa.insert(row_type), data)


def _insert_from_create_input_group(
    db_conn: Connection, input_group: PermissionCreateInputGroup
) -> None:
    _insert_if_data_exists(db_conn, RoleRow, input_group.to_role_insert_data())
    _insert_if_data_exists(db_conn, UserRoleRow, input_group.to_user_role_insert_data())
    _insert_if_data_exists(
        db_conn, ScopePermissionRow, input_group.to_scope_permission_insert_data()
    )
    _insert_if_data_exists(
        db_conn,
        AssociationScopesEntitiesRow,
        input_group.to_association_scopes_entities_insert_data(),
    )


def _migrate_user_data(db_conn: Connection) -> None:
    offset = 0
    page_size = 1000
    while True:
        user_query = (
            sa.select(UserRow.uuid, UserRow.username, UserRow.domain_name, UserRow.role)
            .offset(offset)
            .limit(page_size)
            .order_by(UserRow.uuid)
        )
        rows = db_conn.execute(user_query).all()
        rows = cast(list[Row], rows)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            data = UserData.from_row(row)
            input_data = create_user_self_role_and_permissions(data)
            input_group.merge(input_data)
        _insert_from_create_input_group(db_conn, input_group)


def _migrate_project_data(db_conn: Connection) -> None:
    offset = 0
    page_size = 1000
    while True:
        project_query = sa.select(GroupRow.id).offset(offset).limit(page_size).order_by(GroupRow.id)
        rows = db_conn.scalars(project_query).all()
        rows = cast(list[Row], rows)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            data = ProjectData.from_row(row)
            admin_input_data = create_project_admin_role_and_permissions(data)
            user_input_data = create_project_user_role_and_permissions(data)
            input_group.merge(admin_input_data)
            input_group.merge(user_input_data)
        _insert_from_create_input_group(db_conn, input_group)


def _migrate_admin_user_project_mapping_data(db_conn: Connection) -> None:
    offset = 0
    page_size = 1000
    j = (
        sa.join(
            UserRow,
            AssocGroupUserRow,
            UserRow.uuid == AssocGroupUserRow.user_id,
        )
        .join(
            ScopePermissionRow,
            AssocGroupUserRow.group_id == sa.cast(ScopePermissionRow.scope_id, UUID),
        )
        .join(
            RoleRow,
            ScopePermissionRow.role_id == RoleRow.id,
        )
    )
    while True:
        query = (
            sa.select(
                UserRow.uuid,
                UserRow.role,
                AssocGroupUserRow.group_id,
                RoleRow.id.label("role_id"),  # type: ignore[attr-defined]
                RoleRow.name.label("role_name"),  # type: ignore[attr-defined]
            )
            .select_from(j)
            .where(
                sa.and_(
                    RoleRow.name.like(f"%{ADMIN_ROLE_NAME_SUFFIX}"),  # type: ignore[attr-defined]
                    UserRow.role.in_([UserRole.SUPERADMIN, UserRole.ADMIN]),
                )
            )
            .offset(offset)
            .limit(page_size)
            .order_by(UserRow.uuid)
        )
        rows = db_conn.execute(query).all()
        rows = cast(list[Row], rows)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            if not RoleNameUtil.is_admin_role(row.role_name):
                continue
            data = ProjectUserAssociationData(project_id=row.group_id, user_id=row.uuid)
            input_data = map_user_to_project_role(row.role_id, data)
            input_group.merge(input_data)
        _insert_from_create_input_group(db_conn, input_group)


def _migrate_user_project_mapping_data(db_conn: Connection) -> None:
    offset = 0
    page_size = 1000
    j = (
        sa.join(
            UserRow,
            AssocGroupUserRow,
            UserRow.uuid == AssocGroupUserRow.user_id,
        )
        .join(
            ScopePermissionRow,
            AssocGroupUserRow.group_id == sa.cast(ScopePermissionRow.scope_id, UUID),
        )
        .join(
            RoleRow,
            ScopePermissionRow.role_id == RoleRow.id,
        )
    )
    while True:
        query = (
            sa.select(
                UserRow.uuid,
                UserRow.role,
                AssocGroupUserRow.group_id,
                RoleRow.id.label("role_id"),  # type: ignore[attr-defined]
                RoleRow.name.label("role_name"),  # type: ignore[attr-defined]
            )
            .select_from(j)
            .where(
                sa.and_(
                    sa.not_(RoleRow.name.like(f"%{ADMIN_ROLE_NAME_SUFFIX}")),  # type: ignore[attr-defined]
                    UserRow.role.not_in([UserRole.SUPERADMIN, UserRole.ADMIN]),
                )
            )
            .offset(offset)
            .limit(page_size)
            .order_by(UserRow.uuid)
        )
        rows = db_conn.execute(query).all()
        rows = cast(list[Row], rows)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            if RoleNameUtil.is_admin_role(row.role_name):
                continue
            data = ProjectUserAssociationData(project_id=row.group_id, user_id=row.uuid)
            input_data = map_user_to_project_role(row.role_id, data)
            input_group.merge(input_data)
        _insert_from_create_input_group(db_conn, input_group)


def upgrade() -> None:
    conn = op.get_bind()
    _migrate_user_data(conn)
    _migrate_project_data(conn)
    _migrate_admin_user_project_mapping_data(conn)
    _migrate_user_project_mapping_data(conn)


def downgrade() -> None:
    conn = op.get_bind()
    # Remove all data from the new RBAC tables
    conn.execute(sa.delete(AssociationScopesEntitiesRow))
    conn.execute(sa.delete(ScopePermissionRow))
    conn.execute(sa.delete(UserRoleRow))
    conn.execute(sa.delete(RoleRow))

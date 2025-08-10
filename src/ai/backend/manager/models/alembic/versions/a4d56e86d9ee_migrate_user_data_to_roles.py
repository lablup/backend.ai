"""migrate user data to roles

Revision ID: a4d56e86d9ee
Revises: 42feff246198
Create Date: 2025-08-06 21:28:29.354670

"""

import enum
import uuid
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine import Connection, Row
from sqlalchemy.orm import registry

from ai.backend.manager.models.base import GUID, EnumValueType, IDColumn, metadata
from ai.backend.manager.models.rbac_models.migration.enums import RoleSource
from ai.backend.manager.models.rbac_models.migration.models import (
    AssociationScopesEntitiesRow,
    ObjectPermissionRow,
    RoleRow,
    ScopePermissionRow,
    UserRoleRow,
)
from ai.backend.manager.models.rbac_models.migration.types import (
    PermissionCreateInputGroup,
)
from ai.backend.manager.models.rbac_models.migration.user import (
    ProjectData,
    ProjectUserAssociationData,
    UserData,
    create_project_admin_role_and_permissions,
    create_project_member_role_and_permissions,
    create_user_self_role_and_permissions,
    map_user_to_project_role,
)
from ai.backend.manager.models.rbac_models.migration.utils import insert_from_create_input_group

# revision identifiers, used by Alembic.
revision = "a4d56e86d9ee"
down_revision = "42feff246198"
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


def _query_user_row(db_conn: Connection, offset: int, page_size: int) -> list[Row]:
    """
    Query all user rows with pagination.
    """
    user_query = (
        sa.select(UserRow.uuid, UserRow.username, UserRow.domain_name, UserRow.role)
        .offset(offset)
        .limit(page_size)
        .order_by(UserRow.uuid)
    )
    return db_conn.execute(user_query).all()


def _create_user_self_roles_and_permissions(db_conn: Connection) -> None:
    """
    Migrate user data to roles and permissions.
    All users have a default self role and permissions.
    """
    offset = 0
    page_size = 1000
    while True:
        rows = _query_user_row(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            data = UserData.from_row(row)
            input_data = create_user_self_role_and_permissions(data)
            input_group.merge(input_data)
        insert_from_create_input_group(db_conn, input_group)


def _query_project_row(db_conn: Connection, offset: int, page_size: int) -> list[Row]:
    """
    Query all project rows with pagination.
    """
    project_query = sa.select(GroupRow.id).offset(offset).limit(page_size).order_by(GroupRow.id)
    return db_conn.execute(project_query).all()


def _create_project_roles_and_permissions(db_conn: Connection) -> None:
    """
    Migrate project data to roles and permissions.
    All projects have a default admin role and a user role.
    """
    offset = 0
    page_size = 1000
    while True:
        rows = _query_project_row(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            data = ProjectData.from_row(row)
            admin_input_data = create_project_admin_role_and_permissions(data)
            user_input_data = create_project_member_role_and_permissions(data)
            input_group.merge(admin_input_data)
            input_group.merge(user_input_data)
        insert_from_create_input_group(db_conn, input_group)


def _query_admin_user_rows_with_project_role(
    db_conn: Connection, offset: int, page_size: int
) -> list[Row]:
    """
    Query all admin user rows with project association and project admin role.
    """
    query = (
        sa.select(
            UserRow.uuid,
            UserRow.role,
            AssocGroupUserRow.group_id,
            RoleRow.id.label("role_id"),  # type: ignore[attr-defined]
        )
        .select_from(
            sa.join(
                UserRow,
                AssocGroupUserRow,
                UserRow.uuid == AssocGroupUserRow.user_id,
            ).join(
                RoleRow,
                AssocGroupUserRow.group_id == sa.cast(RoleRow.description, UUID),
            )
        )
        .where(
            sa.and_(
                UserRow.role.in_([UserRole.SUPERADMIN, UserRole.ADMIN]),
                RoleRow.source == RoleSource.SYSTEM,
            )
        )
        .offset(offset)
        .limit(page_size)
        .order_by(UserRow.uuid)
    )
    return db_conn.execute(query).all()


def _map_admin_users_to_project_role(db_conn: Connection) -> None:
    offset = 0
    page_size = 1000

    while True:
        rows = _query_admin_user_rows_with_project_role(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            data = ProjectUserAssociationData(project_id=row.group_id, user_id=row.uuid)
            input_data = map_user_to_project_role(row.role_id, data)
            input_group.merge(input_data)
        insert_from_create_input_group(db_conn, input_group)


def _query_member_user_rows_with_project_role(
    db_conn: Connection, offset: int, page_size: int
) -> list[Row]:
    """
    Query all admin user rows with project association and project role.
    """
    query = (
        sa.select(
            UserRow.uuid,
            UserRow.role,
            AssocGroupUserRow.group_id,
            RoleRow.id.label("role_id"),  # type: ignore[attr-defined]
        )
        .select_from(
            sa.join(
                UserRow,
                AssocGroupUserRow,
                UserRow.uuid == AssocGroupUserRow.user_id,
            ).join(
                RoleRow,
                AssocGroupUserRow.group_id == sa.cast(RoleRow.description, UUID),
            )
        )
        .where(
            sa.and_(
                UserRow.role.not_in([UserRole.SUPERADMIN, UserRole.ADMIN]),
                RoleRow.source == RoleSource.CUSTOM,
            )
        )
        .offset(offset)
        .limit(page_size)
        .order_by(UserRow.uuid)
    )
    return db_conn.execute(query).all()


def _map_member_users_to_project_role(db_conn: Connection) -> None:
    offset = 0
    page_size = 1000
    while True:
        rows = _query_member_user_rows_with_project_role(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            data = ProjectUserAssociationData(project_id=row.group_id, user_id=row.uuid)
            input_data = map_user_to_project_role(row.role_id, data)
            input_group.merge(input_data)
        insert_from_create_input_group(db_conn, input_group)


def upgrade() -> None:
    conn = op.get_bind()
    _create_user_self_roles_and_permissions(conn)
    _create_project_roles_and_permissions(conn)
    _map_admin_users_to_project_role(conn)
    _map_member_users_to_project_role(conn)


def downgrade() -> None:
    conn = op.get_bind()
    # Remove all data from the new RBAC tables
    conn.execute(sa.delete(AssociationScopesEntitiesRow))
    conn.execute(sa.delete(ObjectPermissionRow))
    conn.execute(sa.delete(ScopePermissionRow))
    conn.execute(sa.delete(UserRoleRow))
    conn.execute(sa.delete(RoleRow))

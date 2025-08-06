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
from sqlalchemy.orm import Session, foreign, registry, relationship, selectinload

from ai.backend.manager.models.base import GUID, EnumValueType, IDColumn, metadata
from ai.backend.manager.models.rbac_models.migrate.types import PermissionCreateInputGroup
from ai.backend.manager.models.rbac_models.migrate.user import (
    map_role_to_project,
    project_row_to_rbac_migration_data,
    user_row_to_rbac_migration_data,
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


def _insert_if_data_exists(db_session: Session, row_type, data: Collection) -> None:
    if data:
        db_session.execute(sa.insert(row_type), data)


def _insert_from_create_input_group(
    db_session: Session, input_group: PermissionCreateInputGroup
) -> None:
    _insert_if_data_exists(db_session, RoleRow, input_group.to_role_insert_data())
    _insert_if_data_exists(db_session, UserRoleRow, input_group.to_user_role_insert_data())
    _insert_if_data_exists(
        db_session, ScopePermissionRow, input_group.to_scope_permission_insert_data()
    )
    _insert_if_data_exists(
        db_session,
        AssociationScopesEntitiesRow,
        input_group.to_association_scopes_entities_insert_data(),
    )


def _migrate_project_data(db_session: Session) -> None:
    offset = 0
    page_size = 1000
    while True:
        project_query = sa.select(GroupRow).offset(offset).limit(page_size).order_by(GroupRow.id)
        rows = db_session.scalars(project_query).all()
        rows = cast(list[GroupRow], rows)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            data = project_row_to_rbac_migration_data(row)
            input_group.merge(data)
        _insert_from_create_input_group(db_session, input_group)


def _migrate_user_data(db_session: Session) -> None:
    offset = 0
    page_size = 1000
    while True:
        user_query = sa.select(UserRow).offset(offset).limit(page_size).order_by(UserRow.uuid)
        rows = db_session.scalars(user_query).all()
        rows = cast(list[UserRow], rows)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            data = user_row_to_rbac_migration_data(row)
            input_group.merge(data)
        _insert_from_create_input_group(db_session, input_group)


def _migrate_project_user_mapping_data(db_session: Session) -> None:
    offset = 0
    page_size = 1000
    while True:
        query = (
            sa.select(GroupRow)
            .options(
                selectinload(GroupRow.users),
                selectinload(GroupRow.scope_permissions),
            )
            .offset(offset)
            .limit(page_size)
            .order_by(GroupRow.id)
        )
        rows = db_session.scalars(query).all()
        rows = cast(list[GroupRow], rows)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            role_ids: set[uuid.UUID] = {permission.role_id for permission in row.scope_permissions}
            for role_id in role_ids:
                data = map_role_to_project(role_id, row)
                input_group.merge(data)
        _insert_from_create_input_group(db_session, input_group)


def upgrade() -> None:
    conn = op.get_bind()

    with Session(bind=conn) as db_session:
        _migrate_project_data(db_session)
        _migrate_user_data(db_session)
        _migrate_project_user_mapping_data(db_session)


def downgrade() -> None:
    pass

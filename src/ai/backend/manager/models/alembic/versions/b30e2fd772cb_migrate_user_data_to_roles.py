"""migrate user data to roles

Revision ID: b30e2fd772cb
Revises: 28fecac94e67
Create Date: 2025-08-06 21:03:17.496742

"""

import enum
import uuid
from typing import Any, Optional, cast

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import registry, relationship

from ai.backend.manager.models.base import GUID, EnumValueType, IDColumn, metadata
from ai.backend.manager.models.rbac_models.migrate.types import PermissionCreateInputGroup
from ai.backend.manager.models.rbac_models.migrate.user import (
    UserData,
)

# revision identifiers, used by Alembic.
revision = "4a60160ba8e0"
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


class AssocGroupUserRow(Base):
    __tablename__ = "association_groups_users"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = IDColumn()
    user_id: uuid.UUID = sa.Column("user_id", GUID, nullable=False)
    group_id: uuid.UUID = sa.Column("group_id", GUID, nullable=False)


class UserRow(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    uuid = IDColumn("uuid")
    username = sa.Column("username", sa.String(length=64), unique=True)
    domain_name = sa.Column("domain_name", sa.String(length=64), index=True)
    role = sa.Column("role", EnumValueType(UserRole), default=UserRole.USER)

    groups = relationship("AssocGroupUserRow", back_populates="user")


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


def upgrade() -> None:
    conn = op.get_bind()

    offset = 0
    page_size = 1000
    while True:
        user_query = sa.select(UserRow).offset(offset).limit(page_size).order_by(UserRow.uuid)
        user_rows = conn.scalars(user_query).all()
        user_rows = cast(list[UserRow], user_rows)
        offset += page_size
        if not user_rows:
            break
        input = PermissionCreateInputGroup()
        for row in user_rows:
            data = UserData.from_user_row(row)
            input_data = data.to_role_create_input()
            input.merge(input_data)
        conn.execute(sa.insert(RoleRow), input.to_role_insert_data())
        conn.execute(sa.insert(UserRoleRow), input.to_user_role_insert_data())
        conn.execute(sa.insert(ScopePermissionRow), input.to_scope_permission_insert_data())
        conn.execute(
            sa.insert(AssociationScopesEntitiesRow),
            input.to_association_scopes_entities_insert_data(),
        )


def downgrade() -> None:
    pass

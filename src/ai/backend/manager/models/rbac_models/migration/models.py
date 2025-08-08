"""
This module defines models that are used only when migrating existing data to the new RBAC system.
Any models defined here SHOULD NOT be used in the main RBAC system.
"""

import uuid
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.orm import registry

from ai.backend.manager.models.base import GUID, IDColumn, metadata

mapper_registry = registry(metadata=metadata)
Base: Any = mapper_registry.generate_base()


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
    entity_type: str = sa.Column("entity_type", sa.String(32), nullable=False)
    operation: str = sa.Column("operation", sa.String(32), nullable=False)
    scope_type: str = sa.Column("scope_type", sa.String(32), nullable=False)
    scope_id: str = sa.Column("scope_id", sa.String(64), nullable=False)


class ObjectPermissionRow(Base):
    __tablename__ = "object_permissions"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = IDColumn()
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)
    entity_type: str = sa.Column("entity_type", sa.String(32), nullable=False)
    entity_id: str = sa.Column("entity_id", sa.String(64), nullable=False)
    operation: str = sa.Column("operation", sa.String(32), nullable=False)


class AssociationScopesEntitiesRow(Base):
    __tablename__ = "association_scopes_entities"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = IDColumn()
    scope_type: str = sa.Column(
        "scope_type",
        sa.String(32),
        nullable=False,
    )
    scope_id: str = sa.Column(
        "scope_id",
        sa.String(64),
        nullable=False,
    )
    entity_type: str = sa.Column("entity_type", sa.String(32), nullable=False)
    entity_id: str = sa.Column(
        "entity_id",
        sa.String(64),
        nullable=False,
    )

"""
This module defines models that are used only when migrating existing data to the new RBAC system.
Any models defined here SHOULD NOT be used in the main RBAC system.

All models are defined in functional style.
The reason for this is to prevent some test code fixtures from incorrectly inferring SQLAlchemy model types.
"""

import sqlalchemy as sa
from sqlalchemy.orm import registry

from ai.backend.manager.models.base import GUID, IDColumn, metadata

mapper_registry = registry(metadata=metadata)


def get_user_roles_table() -> sa.Table:
    user_roles_table = sa.Table(
        "user_roles",
        mapper_registry.metadata,
        IDColumn(),
        sa.Column("user_id", GUID, nullable=False),
        sa.Column("role_id", GUID, nullable=False),
        extend_existing=True,
    )
    return user_roles_table


def get_roles_table() -> sa.Table:
    roles_table = sa.Table(
        "roles",
        mapper_registry.metadata,
        IDColumn(),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column(
            "source",
            sa.VARCHAR(16),
            nullable=False,
            default="system",
        ),
        sa.Column("description", sa.Text, nullable=True),
        extend_existing=True,
    )
    return roles_table


def get_permission_groups_table() -> sa.Table:
    permission_groups_table = sa.Table(
        "permission_groups",
        mapper_registry.metadata,
        IDColumn(),
        sa.Column("role_id", GUID, nullable=False),
        sa.Column("scope_type", sa.VARCHAR(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        extend_existing=True,
    )
    return permission_groups_table


def get_permissions_table() -> sa.Table:
    permissions_table = sa.Table(
        "permissions",
        mapper_registry.metadata,
        IDColumn(),
        sa.Column("permission_group_id", GUID, nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("operation", sa.String(32), nullable=False),
        extend_existing=True,
    )
    return permissions_table


def get_object_permissions_table() -> sa.Table:
    object_permissions_table = sa.Table(
        "object_permissions",
        mapper_registry.metadata,
        IDColumn(),
        sa.Column("role_id", GUID, nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("operation", sa.String(32), nullable=False),
        extend_existing=True,
    )
    return object_permissions_table


def get_association_scopes_entities_table() -> sa.Table:
    association_scopes_entities_table = sa.Table(
        "association_scopes_entities",
        mapper_registry.metadata,
        IDColumn(),
        sa.Column("scope_type", sa.String(32), nullable=False),
        sa.Column("scope_id", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        extend_existing=True,
    )
    return association_scopes_entities_table

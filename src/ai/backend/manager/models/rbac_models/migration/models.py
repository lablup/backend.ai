"""
This module defines models that are used only when migrating existing data to the new RBAC system.
Any models defined here SHOULD NOT be used in the main RBAC system.

All models are defined in functional style.
The reason for this is to prevent some test code fixtures from incorrectly inferring SQLAlchemy model types.

NOTE: Several table definitions below are DEPRECATED because the underlying tables
or columns have been dropped or redesigned by later migrations. They are kept solely
to allow old Alembic migration files to remain importable. New migrations should
define tables inline or use raw SQL instead of calling these shared helpers.
"""

import sqlalchemy as sa
from sqlalchemy.orm import registry

from ai.backend.manager.models.base import GUID, IDColumn, metadata

mapper_registry = registry(metadata=metadata)


def get_user_roles_table() -> sa.Table:
    return sa.Table(
        "user_roles",
        mapper_registry.metadata,
        IDColumn(),
        sa.Column("user_id", GUID, nullable=False),
        sa.Column("role_id", GUID, nullable=False),
        extend_existing=True,
    )


def get_roles_table() -> sa.Table:
    return sa.Table(
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


def get_permission_groups_table() -> sa.Table:
    """DEPRECATED: The ``permission_groups`` table was dropped by migration
    ``f41bbe0c0f12``. Retained only for old migration imports. New migrations
    should define tables inline or use raw SQL."""
    return sa.Table(
        "permission_groups",
        mapper_registry.metadata,
        IDColumn(),
        sa.Column("role_id", GUID, nullable=False),
        sa.Column("scope_type", sa.VARCHAR(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        extend_existing=True,
    )


def get_permissions_table() -> sa.Table:
    """DEPRECATED: This definition uses the pre-``f41bbe0c0f12`` schema
    (``permission_group_id`` column). The current ``permissions`` table has
    ``role_id``, ``scope_type``, ``scope_id`` instead. Retained only for
    old migration imports. New migrations should define the table inline
    or use raw SQL."""
    return sa.Table(
        "permissions",
        mapper_registry.metadata,
        IDColumn(),
        sa.Column("permission_group_id", GUID, nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("operation", sa.String(32), nullable=False),
        extend_existing=True,
    )


def get_object_permissions_table() -> sa.Table:
    """DEPRECATED: The ``object_permissions`` table is deprecated. This
    definition uses a legacy schema. Retained only for old migration imports.
    New migrations should define the table inline or use raw SQL."""
    return sa.Table(
        "object_permissions",
        mapper_registry.metadata,
        IDColumn(),
        sa.Column("role_id", GUID, nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("operation", sa.String(32), nullable=False),
        extend_existing=True,
    )


def get_association_scopes_entities_table() -> sa.Table:
    """Table definition for old migrations. New migrations should define
    the table inline or use raw SQL to avoid schema drift."""
    return sa.Table(
        "association_scopes_entities",
        mapper_registry.metadata,
        IDColumn(),
        sa.Column("scope_type", sa.String(32), nullable=False),
        sa.Column("scope_id", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        extend_existing=True,
    )

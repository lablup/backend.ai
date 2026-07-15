"""backfill role-to-scope mappings in association_scopes_entities

Migrations 2c9000848b6e (user roles), e43125b98bba (domain roles), and
430b1631804d (project roles) created SYSTEM-sourced roles but never inserted
the corresponding (entity_type='role') rows into association_scopes_entities.
This causes GraphQL scope resolution to return null for these roles.

This migration backfills the missing entries by:
1. Matching role_domain_*_admin roles to their domain via name parsing.
2. Matching role_project_*_admin roles to their project via the 8-char UUID
   prefix in the role name.
3. Matching role_user_* and user-* roles to their user via the user_roles
   join table. The former were created by earlier RBAC migrations; the
   latter by 2c9000848b6e which uses the runtime naming convention.
4. Skipping role_superadmin and role_monitor (global roles with no entity
   scope).

The migration is idempotent (INSERT ... ON CONFLICT DO NOTHING).

Revision ID: d3683e2703ff
Revises: f9a8cfaca907
Create Date: 2026-04-16

"""

from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection

from ai.backend.manager.models.base import GUID, IDColumn, metadata

# revision identifiers, used by Alembic.
revision = "d3683e2703ff"
down_revision = "f9a8cfaca907"
# Part of: 26.5.0
branch_labels = None
depends_on = None

_registry_metadata = metadata


def _get_roles_table() -> sa.Table:
    return sa.Table(
        "roles",
        _registry_metadata,
        IDColumn(),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("source", sa.VARCHAR(16), nullable=False),
        extend_existing=True,
    )


def _get_assoc_table() -> sa.Table:
    return sa.Table(
        "association_scopes_entities",
        _registry_metadata,
        IDColumn(),
        sa.Column("scope_type", sa.String(32), nullable=False),
        sa.Column("scope_id", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        extend_existing=True,
    )


def _get_domains_table() -> sa.Table:
    return sa.Table(
        "domains",
        _registry_metadata,
        sa.Column("name", sa.String(64), primary_key=True),
        extend_existing=True,
    )


def _get_groups_table() -> sa.Table:
    return sa.Table(
        "groups",
        _registry_metadata,
        IDColumn(),
        extend_existing=True,
    )


def _get_user_roles_table() -> sa.Table:
    return sa.Table(
        "user_roles",
        _registry_metadata,
        IDColumn(),
        sa.Column("user_id", GUID, nullable=False),
        sa.Column("role_id", GUID, nullable=False),
        extend_existing=True,
    )


_MAX_BIND_PARAMS = 16000


def _insert_skip_on_conflict(
    db_conn: Connection, table: sa.Table, rows: list[dict[str, Any]]
) -> None:
    if not rows:
        return
    params_per_row = max(1, len(rows[0]))
    chunk_size = max(1, _MAX_BIND_PARAMS // params_per_row)
    for start in range(0, len(rows), chunk_size):
        chunk = rows[start : start + chunk_size]
        stmt = pg_insert(table).values(chunk).on_conflict_do_nothing()
        db_conn.execute(stmt)


def _backfill_domain_admin_roles(db_conn: Connection) -> None:
    """Backfill role→scope for role_domain_*_admin roles.

    Role name pattern: ``role_domain_{domain_name}_admin``
    Scope: (domain, domain_name)
    """
    roles = _get_roles_table()
    assoc = _get_assoc_table()
    domains = _get_domains_table()

    # Find domain admin roles that have no scope mapping yet.
    already_mapped = (
        sa.select(sa.literal(1))
        .select_from(assoc)
        .where(
            assoc.c.entity_type == "role",
            assoc.c.entity_id == sa.cast(roles.c.id, sa.String),
        )
        .exists()
    )

    # Extract domain name from role name:
    # "role_domain_{name}_admin" → strip prefix "role_domain_" (12 chars)
    # and suffix "_admin" (6 chars).
    domain_name_expr = sa.func.substring(
        roles.c.name,
        sa.literal(13),  # len("role_domain_") + 1
        sa.func.length(roles.c.name) - sa.literal(18),  # 12 + 6
    )

    stmt = sa.select(roles.c.id, domain_name_expr.label("domain_name")).where(
        roles.c.name.like("role_domain_%_admin"),
        roles.c.source == "system",
        sa.not_(already_mapped),
    )
    rows = db_conn.execute(stmt).all()

    # Verify that the domains actually exist.
    domain_names = {r.domain_name for r in rows}
    if domain_names:
        existing = set(
            db_conn.scalars(sa.select(domains.c.name).where(domains.c.name.in_(domain_names))).all()
        )
    else:
        existing = set()

    assoc_rows = [
        {
            "scope_type": "domain",
            "scope_id": r.domain_name,
            "entity_type": "role",
            "entity_id": str(r.id),
        }
        for r in rows
        if r.domain_name in existing
    ]
    _insert_skip_on_conflict(db_conn, assoc, assoc_rows)


def _backfill_project_admin_roles(db_conn: Connection) -> None:
    """Backfill role→scope for role_project_*_admin roles.

    Role name pattern: ``role_project_{id[:8]}_admin``
    Scope: (project, project_id)
    """
    roles = _get_roles_table()
    assoc = _get_assoc_table()
    groups = _get_groups_table()

    already_mapped = (
        sa.select(sa.literal(1))
        .select_from(assoc)
        .where(
            assoc.c.entity_type == "role",
            assoc.c.entity_id == sa.cast(roles.c.id, sa.String),
        )
        .exists()
    )

    # Extract 8-char UUID prefix from role name:
    # "role_project_{id8}_admin" → chars 14..21
    id_prefix_expr = sa.func.substring(roles.c.name, sa.literal(14), sa.literal(8))

    # Match against groups whose UUID starts with the same 8 chars.
    stmt = (
        sa.select(roles.c.id.label("role_id"), groups.c.id.label("project_id"))
        .select_from(
            roles.join(
                groups,
                sa.func.substring(sa.cast(groups.c.id, sa.String), 1, 8) == id_prefix_expr,
            )
        )
        .where(
            roles.c.name.like("role_project_%_admin"),
            roles.c.source == "system",
            sa.not_(already_mapped),
        )
    )
    rows = db_conn.execute(stmt).all()

    assoc_rows = [
        {
            "scope_type": "project",
            "scope_id": str(r.project_id),
            "entity_type": "role",
            "entity_id": str(r.role_id),
        }
        for r in rows
    ]
    _insert_skip_on_conflict(db_conn, assoc, assoc_rows)


def _backfill_user_roles(db_conn: Connection) -> None:
    """Backfill role→scope for user system roles.

    Two naming conventions exist:
    - ``role_user_{username}`` — created by earlier RBAC migrations
    - ``user-{uuid[:8]}`` — created by migration 2c9000848b6e

    Scope: (user, user_id)

    We resolve user_id via the user_roles join table — the user_roles mapping
    was created by the original migrations, only the association_scopes_entities
    entry was missed.
    """
    roles = _get_roles_table()
    assoc = _get_assoc_table()
    user_roles = _get_user_roles_table()

    already_mapped = (
        sa.select(sa.literal(1))
        .select_from(assoc)
        .where(
            assoc.c.entity_type == "role",
            assoc.c.entity_id == sa.cast(roles.c.id, sa.String),
        )
        .exists()
    )

    stmt = (
        sa.select(
            roles.c.id.label("role_id"),
            user_roles.c.user_id,
        )
        .select_from(roles.join(user_roles, user_roles.c.role_id == roles.c.id))
        .where(
            sa.or_(
                roles.c.name.like("role_user_%"),
                roles.c.name.like("user-%"),
            ),
            roles.c.source == "system",
            # Exclude global roles that happen to start with "role_user_"
            roles.c.name.notin_(["role_superadmin", "role_monitor"]),
            sa.not_(already_mapped),
        )
    )
    rows = db_conn.execute(stmt).all()

    assoc_rows = [
        {
            "scope_type": "user",
            "scope_id": str(r.user_id),
            "entity_type": "role",
            "entity_id": str(r.role_id),
        }
        for r in rows
    ]
    _insert_skip_on_conflict(db_conn, assoc, assoc_rows)


def upgrade() -> None:
    conn = op.get_bind()
    _backfill_domain_admin_roles(conn)
    _backfill_project_admin_roles(conn)
    _backfill_user_roles(conn)


def downgrade() -> None:
    # The backfill only adds missing data. Removing it would re-break scope
    # resolution, so downgrade is intentionally a no-op.
    pass

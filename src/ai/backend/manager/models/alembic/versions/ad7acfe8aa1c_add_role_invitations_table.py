"""add role_invitations table and grant role:assignment permissions

Creates the role_invitations table for blind-invite role grants. Grants
role:assignment permissions on:
- Every user self-role (read + update) so users can view and
  accept/reject invitations addressed to them.
- Every project admin role (create + read + soft-delete) so project
  admins can create and cancel invitations.

The permission grants are idempotent (ON CONFLICT DO NOTHING).

Revision ID: ad7acfe8aa1c
Revises: d3683e2703ff
Create Date: 2026-04-19

"""

from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection

from ai.backend.manager.models.base import GUID, IDColumn, metadata

# revision identifiers, used by Alembic.
revision = "ad7acfe8aa1c"
down_revision = "d3683e2703ff"
# Part of: 26.5.0
branch_labels = None
depends_on = None

_ENTITY_TYPE = "role:assignment"


def _get_roles_table() -> sa.Table:
    return sa.Table(
        "roles",
        metadata,
        IDColumn(),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("source", sa.VARCHAR(16), nullable=False),
        extend_existing=True,
    )


def _get_assoc_table() -> sa.Table:
    return sa.Table(
        "association_scopes_entities",
        metadata,
        IDColumn(),
        sa.Column("scope_type", sa.String(32), nullable=False),
        sa.Column("scope_id", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        extend_existing=True,
    )


def _get_permissions_table() -> sa.Table:
    return sa.Table(
        "permissions",
        metadata,
        IDColumn(),
        sa.Column("role_id", GUID, nullable=False),
        sa.Column("scope_type", sa.VARCHAR(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("operation", sa.String(32), nullable=False),
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


def _grant_user_self_role_permissions(db_conn: Connection) -> None:
    """Grant read + update on role:assignment to every user self-role.

    User self-roles follow naming conventions 'user-{uuid8}' (current) or
    'role_user_{username}' (legacy). We resolve the scope via the
    association_scopes_entities table.
    """
    roles = _get_roles_table()
    assoc = _get_assoc_table()
    permissions = _get_permissions_table()

    stmt = (
        sa.select(
            roles.c.id.label("role_id"),
            assoc.c.scope_type,
            assoc.c.scope_id,
        )
        .select_from(
            roles.join(
                assoc,
                sa.and_(
                    assoc.c.entity_type == "role",
                    sa.cast(assoc.c.entity_id, sa.String) == sa.cast(roles.c.id, sa.String),
                    assoc.c.scope_type == "user",
                ),
            )
        )
        .where(
            sa.or_(
                roles.c.name.like("user-%"),
                roles.c.name.like("role_user_%"),
            ),
            roles.c.source == "system",
        )
    )
    rows = db_conn.execute(stmt).all()

    perm_rows: list[dict[str, Any]] = []
    for row in rows:
        for operation in ("read", "update"):
            perm_rows.append({
                "role_id": row.role_id,
                "scope_type": row.scope_type,
                "scope_id": row.scope_id,
                "entity_type": _ENTITY_TYPE,
                "operation": operation,
            })
    _insert_skip_on_conflict(db_conn, permissions, perm_rows)


def _grant_project_admin_role_permissions(db_conn: Connection) -> None:
    """Grant create + read + soft-delete on role:assignment to every
    project admin system role.

    Project admin roles follow naming conventions 'project-{uuid8}-admin'
    (current) or 'role_project_{uuid8}_admin' (legacy). We resolve the
    scope via the association_scopes_entities table.
    """
    roles = _get_roles_table()
    assoc = _get_assoc_table()
    permissions = _get_permissions_table()

    stmt = (
        sa.select(
            roles.c.id.label("role_id"),
            assoc.c.scope_type,
            assoc.c.scope_id,
        )
        .select_from(
            roles.join(
                assoc,
                sa.and_(
                    assoc.c.entity_type == "role",
                    sa.cast(assoc.c.entity_id, sa.String) == sa.cast(roles.c.id, sa.String),
                    assoc.c.scope_type == "project",
                ),
            )
        )
        .where(
            sa.or_(
                roles.c.name.like("project-%-admin"),
                roles.c.name.like("role_project_%_admin"),
            ),
            roles.c.source == "system",
        )
    )
    rows = db_conn.execute(stmt).all()

    perm_rows: list[dict[str, Any]] = []
    for row in rows:
        for operation in ("create", "read", "soft-delete"):
            perm_rows.append({
                "role_id": row.role_id,
                "scope_type": row.scope_type,
                "scope_id": row.scope_id,
                "entity_type": _ENTITY_TYPE,
                "operation": operation,
            })
    _insert_skip_on_conflict(db_conn, permissions, perm_rows)


def upgrade() -> None:
    op.create_table(
        "role_invitations",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "inviter_user_id",
            GUID,
            sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "invitee_user_id",
            GUID,
            sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role_id",
            GUID,
            sa.ForeignKey("roles.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "state",
            sa.VARCHAR(64),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_role_invitations_invitee_user_id",
        "role_invitations",
        ["invitee_user_id"],
    )
    op.create_index(
        "uq_role_invitations_active",
        "role_invitations",
        ["invitee_user_id", "role_id"],
        unique=True,
        postgresql_where=sa.text("state != 'accepted'"),
    )

    conn = op.get_bind()
    _grant_user_self_role_permissions(conn)
    _grant_project_admin_role_permissions(conn)


def downgrade() -> None:
    # drop_table takes the table's indexes with it; dropping them by name first
    # only breaks on installs that never had them.
    op.drop_table("role_invitations")

"""Drop the scope from permission rows

A role sits in one scope, so its permissions hold there and name no scope of their own.
Removes ``permissions.scope_type`` / ``permissions.scope_id`` with the indexes and the
unique constraint over them, and keys the rows on ``(role_id, entity_type, permission)``.

A row naming a scope other than its role's would lose that scope silently, so the
migration counts those first and stops when it finds any. A folder share granted the
invitee's role rows scoped to the folder; those are dropped before the count, since the
share is carried from ``vfolder_permissions`` later in the chain. ``3632aad9d5d9`` granted
a session's creator and its project's admins read on that session's app service, scoped to
the session; those are dropped too, since ``f4a1c9d20b73`` retires the entity type and the
session answers for it. So are the rows of a system role ``f4a1c9d20b73`` rewrites or
removes, and the rows scoped to a user, project or domain that no longer exists.

Create Date: 2026-09-09

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c092d242a027"
down_revision = "c7d419b0a58e"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_CHECK_QUERY = """\
-- permission rows naming a scope other than their role's, per role and scope
SELECT r.id AS role_id, r.name, r.source, r.scope_type AS role_scope_type,
       r.scope_id AS role_scope_id, p.scope_type, p.scope_id, count(*) AS row_count,
       (SELECT count(*) FROM user_roles ur WHERE ur.role_id = r.id) AS holders
FROM permissions p JOIN roles r ON r.id = p.role_id
WHERE p.scope_type IS DISTINCT FROM r.scope_type
   OR p.scope_id IS DISTINCT FROM CAST(r.scope_id AS text)
GROUP BY r.id, r.name, r.source, r.scope_type, r.scope_id, p.scope_type, p.scope_id
ORDER BY r.name, p.scope_type, p.scope_id;"""


def drop_folder_share_grants(conn: sa.engine.Connection) -> None:
    """Drop the rows a folder share granted: scoped to the folder, on a role sitting in
    another scope."""
    conn.execute(
        sa.text("""
            DELETE FROM permissions p
            USING roles r
            WHERE r.id = p.role_id
              AND p.scope_type = 'vfolder'
              AND (p.scope_type IS DISTINCT FROM r.scope_type
                   OR p.scope_id IS DISTINCT FROM CAST(r.scope_id AS text))
        """)
    )


def drop_session_app_service_grants(conn: sa.engine.Connection) -> None:
    """Drop the rows granting read on a session's app service: scoped to the session, on a
    role sitting in another scope."""
    conn.execute(
        sa.text("""
            DELETE FROM permissions p
            USING roles r
            WHERE r.id = p.role_id
              AND p.entity_type = 'session:app_service'
              AND (p.scope_type IS DISTINCT FROM r.scope_type
                   OR p.scope_id IS DISTINCT FROM CAST(r.scope_id AS text))
        """)
    )


# The presets ``f4a1c9d20b73`` writes; it replaces the permissions of the system roles
# linked to them and removes the system roles linked to none.
_REWRITTEN_PRESET_IDS = (
    "9ebf4f57-9e67-5631-997a-d2d79cc3815f",
    "22c4db03-24aa-5ff8-b5a9-64b2a2182413",
    "06057849-3534-546f-b74c-b79d5d3ecf5e",
    "776c1366-dcf3-5abd-b8de-bc3ad3b759ad",
)

_UUID_PATTERN = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"


def drop_rewritten_system_role_grants(conn: sa.engine.Connection) -> None:
    """Drop the rows naming another scope on a system role that ``f4a1c9d20b73`` rewrites
    or removes: they do not survive that revision either way."""
    conn.execute(
        sa.text("""
            DELETE FROM permissions p
            USING roles r
            WHERE r.id = p.role_id
              AND r.source = 'system'
              AND (r.role_preset_id IS NULL
                   OR CAST(r.role_preset_id AS text) = ANY(:preset_ids))
              AND (p.scope_type IS DISTINCT FROM r.scope_type
                   OR p.scope_id IS DISTINCT FROM CAST(r.scope_id AS text))
        """).bindparams(preset_ids=list(_REWRITTEN_PRESET_IDS))
    )


def drop_grants_on_deleted_scopes(conn: sa.engine.Connection) -> None:
    """Drop the rows naming another scope that is a user, project or domain no longer in
    the database, or that is not named by a uuid."""
    conn.execute(
        sa.text("""
            DELETE FROM permissions p
            USING roles r
            WHERE r.id = p.role_id
              AND p.scope_type IN ('user', 'project', 'domain')
              AND (p.scope_type IS DISTINCT FROM r.scope_type
                   OR p.scope_id IS DISTINCT FROM CAST(r.scope_id AS text))
              AND (
                  p.scope_id !~* :uuid_pattern
                  OR (p.scope_type = 'user' AND NOT EXISTS (
                      SELECT 1 FROM users u WHERE CAST(u.uuid AS text) = p.scope_id))
                  OR (p.scope_type = 'project' AND NOT EXISTS (
                      SELECT 1 FROM groups g WHERE CAST(g.id AS text) = p.scope_id))
                  OR (p.scope_type = 'domain' AND NOT EXISTS (
                      SELECT 1 FROM domains d WHERE CAST(d.id AS text) = p.scope_id))
              )
        """).bindparams(uuid_pattern=_UUID_PATTERN)
    )


def refuse_rows_disagreeing_with_their_role(conn: sa.engine.Connection) -> None:
    """Stop when a permission row names a scope other than the one its role sits in.

    Dropping the columns would take that scope with them, so the rows are counted while
    they can still be read. Cleaning them up is a decision for whoever owns the data.

    Once every row agrees with its role, the old unique key — which counts the scope —
    already makes ``(role_id, entity_type, permission)`` unique, so the narrower key the
    upgrade puts in its place needs no deduplication.
    """
    count = conn.execute(
        sa.text("""
            SELECT count(*)
            FROM permissions p JOIN roles r ON r.id = p.role_id
            WHERE p.scope_type IS DISTINCT FROM r.scope_type
               OR p.scope_id IS DISTINCT FROM CAST(r.scope_id AS text)
        """)
    ).scalar_one()
    if count:
        raise RuntimeError(
            f"{count} permission row(s) name a scope other than their role's."
            f" Resolve them first; check query:\n{_CHECK_QUERY}"
        )


def upgrade() -> None:
    conn = op.get_bind()
    drop_folder_share_grants(conn)
    drop_session_app_service_grants(conn)
    drop_rewritten_system_role_grants(conn)
    drop_grants_on_deleted_scopes(conn)
    refuse_rows_disagreeing_with_their_role(conn)
    op.drop_constraint("uq_permissions_role_scope_entity_permission", "permissions", type_="unique")
    op.drop_index("ix_permissions_role_scope", table_name="permissions")
    op.drop_index("ix_permissions_scope_entity", table_name="permissions")
    op.drop_column("permissions", "scope_id")
    op.drop_column("permissions", "scope_type")
    op.create_index(
        "ix_permissions_entity",
        "permissions",
        ["entity_type"],
        unique=False,
        postgresql_include=["permission", "role_id"],
    )
    op.create_unique_constraint(
        "uq_permissions_role_entity_permission",
        "permissions",
        ["role_id", "entity_type", "permission"],
    )


def downgrade() -> None:
    """Restore the columns and fill them from each row's role.

    The scope a row named before the upgrade is gone; the role's is what the upgrade
    kept, and it is the only scope the row can be given back.
    """
    op.drop_constraint("uq_permissions_role_entity_permission", "permissions", type_="unique")
    op.drop_index("ix_permissions_entity", table_name="permissions")
    op.add_column("permissions", sa.Column("scope_type", sa.String(length=32), nullable=True))
    op.add_column("permissions", sa.Column("scope_id", sa.String(length=64), nullable=True))
    op.execute(
        sa.text("""
            UPDATE permissions p
            SET scope_type = r.scope_type, scope_id = CAST(r.scope_id AS text)
            FROM roles r WHERE r.id = p.role_id
        """)
    )
    op.execute(sa.text("DELETE FROM permissions WHERE scope_type IS NULL OR scope_id IS NULL"))
    op.alter_column("permissions", "scope_type", nullable=False)
    op.alter_column("permissions", "scope_id", nullable=False)
    op.create_index(
        "ix_permissions_role_scope", "permissions", ["role_id", "scope_type", "scope_id"]
    )
    op.create_index(
        "ix_permissions_scope_entity",
        "permissions",
        ["scope_type", "scope_id", "entity_type"],
        postgresql_include=["permission", "role_id"],
    )
    op.create_unique_constraint(
        "uq_permissions_role_scope_entity_permission",
        "permissions",
        ["role_id", "scope_type", "scope_id", "entity_type", "permission"],
    )

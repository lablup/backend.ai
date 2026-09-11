"""Drop the scope from permission rows

A role sits in one scope, so its permissions hold there and name no scope of their own.
Removes ``permissions.scope_type`` / ``permissions.scope_id`` with the indexes and the
unique constraint over them, and keys the rows on ``(role_id, entity_type, permission)``.

A row naming a scope other than its role's would lose that scope silently, so the
migration counts those first and stops when it finds any.

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
-- permission rows naming a scope other than their role's
SELECT p.id, p.role_id, p.scope_type, p.scope_id, r.scope_type, r.scope_id
FROM permissions p JOIN roles r ON r.id = p.role_id
WHERE p.scope_type IS DISTINCT FROM r.scope_type
   OR p.scope_id IS DISTINCT FROM CAST(r.scope_id AS text);"""


def _refuse_rows_disagreeing_with_their_role(conn: sa.engine.Connection) -> None:
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
    _refuse_rows_disagreeing_with_their_role(conn)
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

"""Make role preset names unique within a scope

Revision ID: a37b92a3e063
Revises: d4b8e2a7c913
Create Date: 2026-10-07

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "a37b92a3e063"
down_revision = "d4b8e2a7c913"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

# PARTITION BY puts NULL scope_ids in one partition, as NULLS NOT DISTINCT compares them.
_PRESETS_SHARING_A_NAME_IN_A_SCOPE_QUERY = """\
SELECT id, name, scope_type, scope_id, deleted_at FROM (
    SELECT *, count(*) OVER (PARTITION BY name, scope_type, scope_id) AS presets_with_the_name
    FROM role_presets
) AS p WHERE presets_with_the_name > 1
ORDER BY name, scope_type, scope_id, id;"""

_MAX_PRESETS_IN_ERROR = 20


def _refuse_presets_sharing_a_name_in_a_scope(conn: Connection) -> None:
    rows = conn.execute(sa.text(_PRESETS_SHARING_A_NAME_IN_A_SCOPE_QUERY)).all()
    if not rows:
        return
    listed = "\n".join(
        f"  {row.id} name={row.name!r} scope_type={row.scope_type!r} "
        f"scope_id={row.scope_id} deleted_at={row.deleted_at}"
        for row in rows[:_MAX_PRESETS_IN_ERROR]
    )
    omitted = "\n  ..." if len(rows) > _MAX_PRESETS_IN_ERROR else ""
    raise RuntimeError(
        "Role presets share a name within one scope, soft-deleted ones included:\n"
        f"{listed}{omitted}\n"
        "Rename or purge them first; check query:\n"
        f"{_PRESETS_SHARING_A_NAME_IN_A_SCOPE_QUERY}"
    )


def upgrade() -> None:
    _refuse_presets_sharing_a_name_in_a_scope(op.get_bind())
    op.create_unique_constraint(
        op.f("uq_role_presets_name"),
        "role_presets",
        ["name", "scope_type", "scope_id"],
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    op.drop_constraint(op.f("uq_role_presets_name"), "role_presets", type_="unique")

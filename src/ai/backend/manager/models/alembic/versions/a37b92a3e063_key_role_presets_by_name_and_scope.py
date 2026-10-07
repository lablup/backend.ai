"""key role_presets by (name, scope_type, scope_id)

``UNIQUE NULLS NOT DISTINCT`` keys a preset for every scope of a type, whose scope_id is
NULL, like any other. Deleted rows are keyed too. Existing duplicates stop the upgrade.

Revision ID: a37b92a3e063
Revises: f7b1e5a9032c
Create Date: 2026-10-07

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "a37b92a3e063"
down_revision = "f7b1e5a9032c"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_CHECK_QUERY = """\
-- role presets sharing one name in one scope, deleted rows included
SELECT name, scope_type, scope_id, array_agg(id) FROM role_presets
GROUP BY 1, 2, 3 HAVING count(*) > 1;"""


def refuse_duplicate_names(conn: Connection) -> None:
    duplicated = conn.execute(sa.text(_CHECK_QUERY)).all()
    if duplicated:
        listed = "; ".join(
            f"{name!r} in {scope_type}/{scope_id or '*'}"
            for name, scope_type, scope_id, _ in duplicated[:20]
        )
        raise RuntimeError(
            f"Role presets share one name in one scope: {listed}"
            f"{' ...' if len(duplicated) > 20 else ''}. Rename or purge them first; "
            f"check query:\n{_CHECK_QUERY}"
        )


def upgrade() -> None:
    refuse_duplicate_names(op.get_bind())
    op.create_unique_constraint(
        op.f("uq_role_presets_name"),
        "role_presets",
        ["name", "scope_type", "scope_id"],
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    op.drop_constraint(op.f("uq_role_presets_name"), "role_presets", type_="unique")

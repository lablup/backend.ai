"""Make role preset names unique within a scope

Revision ID: a37b92a3e063
Revises: d4b8e2a7c913
Create Date: 2026-10-07

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a37b92a3e063"
down_revision = "d4b8e2a7c913"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_CHECK_QUERY = """\
-- role presets sharing a name in one scope, soft-deleted ones included
SELECT name, scope_type, scope_id, count(*) FROM role_presets
GROUP BY 1, 2, 3 HAVING count(*) > 1;"""


def upgrade() -> None:
    duplicated = op.get_bind().execute(sa.text(_CHECK_QUERY)).all()
    if duplicated:
        raise RuntimeError(
            f"{len(duplicated)} name(s) are shared by more than one role preset in one scope."
            f" Rename or purge the duplicates first; check query:\n{_CHECK_QUERY}"
        )
    op.create_unique_constraint(
        op.f("uq_role_presets_name"),
        "role_presets",
        ["name", "scope_type", "scope_id"],
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    op.drop_constraint(op.f("uq_role_presets_name"), "role_presets", type_="unique")

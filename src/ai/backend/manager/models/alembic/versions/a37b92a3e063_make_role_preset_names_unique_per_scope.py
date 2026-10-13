"""Make role preset names unique within a scope

Revision ID: a37b92a3e063
Revises: ede445fb9d0d
Create Date: 2026-10-07

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a37b92a3e063"
down_revision = "ede445fb9d0d"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        op.f("uq_role_presets_name"),
        "role_presets",
        ["name", "scope_type", "scope_id"],
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    op.drop_constraint(op.f("uq_role_presets_name"), "role_presets", type_="unique")

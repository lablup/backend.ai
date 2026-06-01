"""add routing replica_group fk

Revision ID: 3f8a1c6b2e94
Revises: b7d4e2a9c1f3
Create Date: 2026-05-30 10:00:00.000000

Part of: 26.6.0
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "3f8a1c6b2e94"
down_revision = "b7d4e2a9c1f3"
branch_labels = None
depends_on = None

# Part of: 26.6.0


def upgrade() -> None:
    op.create_foreign_key(
        op.f("fk_routings_replica_group_id_replica_groups"),
        "routings",
        "replica_groups",
        ["replica_group_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_routings_replica_group_id_replica_groups"),
        "routings",
        type_="foreignkey",
    )

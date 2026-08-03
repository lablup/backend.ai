"""add domain_id to users

``users`` referenced its domain by name while nearly everything that filters by
domain keys off the id, so every path starting from a user converted the name.
Adds the id alongside the name and backfills it; ``domain_name`` stays.

Idempotent: the column is added only if absent, and the backfill only touches
rows whose ``domain_id`` is still NULL.

Revision ID: c1a7d3f05e28
Revises: 857c4d02c4b9
Create Date: 2026-08-03 18:40:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "c1a7d3f05e28"
down_revision = "857c4d02c4b9"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("users")}
    if "domain_id" not in cols:
        op.add_column("users", sa.Column("domain_id", GUID, nullable=True))
        op.create_index(op.f("ix_users_domain_id"), "users", ["domain_id"])
        op.create_foreign_key(
            "fk_users_domain_id_domains",
            "users",
            "domains",
            ["domain_id"],
            ["id"],
        )
    bind.execute(
        sa.text("""
            UPDATE users u
            SET domain_id = d.id
            FROM domains d
            WHERE u.domain_name = d.name
              AND u.domain_id IS NULL
        """)
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("users")}
    if "domain_id" in cols:
        op.drop_constraint("fk_users_domain_id_domains", "users", type_="foreignkey")
        op.drop_index(op.f("ix_users_domain_id"), table_name="users")
        op.drop_column("users", "domain_id")

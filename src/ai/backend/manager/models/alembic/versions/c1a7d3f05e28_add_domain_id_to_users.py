"""add domain_id to users

``users`` referenced its domain by name while nearly everything that filters by
domain keys off the id, so every path starting from a user converted the name.
Adds the id alongside the name and backfills it; ``domain_name`` stays.

Revision ID: c1a7d3f05e28
Revises: 9fbeda8995ff
Create Date: 2026-08-03 18:40:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "c1a7d3f05e28"
down_revision = "9fbeda8995ff"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("domain_id", GUID, nullable=True))
    op.create_index(op.f("ix_users_domain_id"), "users", ["domain_id"])
    op.create_foreign_key(
        "fk_users_domain_id_domains",
        "users",
        "domains",
        ["domain_id"],
        ["id"],
    )
    op.get_bind().execute(
        sa.text("""
            UPDATE users u
            SET domain_id = d.id
            FROM domains d
            WHERE u.domain_name = d.name
        """)
    )
    # Referencing the pair needs a unique index over the pair; `id` and `name` are unique
    # on their own, which does not cover it.
    op.create_unique_constraint("uq_domains_id_name", "domains", ["id", "name"])
    op.create_foreign_key(
        "fk_users_domain_pair_domains",
        "users",
        "domains",
        ["domain_id", "domain_name"],
        ["id", "name"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_domain_pair_domains", "users", type_="foreignkey")
    op.drop_constraint("uq_domains_id_name", "domains", type_="unique")
    op.drop_constraint("fk_users_domain_id_domains", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_domain_id"), table_name="users")
    op.drop_column("users", "domain_id")

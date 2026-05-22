"""add ``domain_id`` UUID FK column to ``groups``

Adds a ``groups.domain_id`` UUID column referencing ``domains.id``,
backfills it from ``domains.name`` via the legacy ``groups.domain_name``
column, and drops the old FK (which used ``ON DELETE CASCADE`` and
``ON UPDATE CASCADE``). The new FK on ``domain_id`` carries the same
``CASCADE`` semantics. The legacy ``groups.domain_name`` string column
is retained without a FK constraint; its removal is deferred to
BA-6122. The ``domains`` primary key remains ``name`` in this revision —
the PK swap is BA-6046.

Revision ID: c1d3f5a86124
Revises: b8a85c96607c
Create Date: 2026-05-21

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "c1d3f5a86124"
down_revision = "b8a85c96607c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    op.add_column("groups", sa.Column("domain_id", GUID(), nullable=True))
    conn.execute(
        sa.text(
            "UPDATE groups SET domain_id = domains.id "
            "FROM domains WHERE groups.domain_name = domains.name"
        )
    )
    op.alter_column("groups", "domain_id", nullable=False)

    op.drop_constraint("fk_groups_domain_name_domains", "groups", type_="foreignkey")
    op.create_foreign_key(
        "fk_groups_domain_id_domains",
        "groups",
        "domains",
        ["domain_id"],
        ["id"],
        ondelete="CASCADE",
        onupdate="CASCADE",
    )
    op.create_index("ix_groups_domain_id", "groups", ["domain_id"])

    op.drop_constraint("uq_groups_name_domain_name", "groups", type_="unique")
    op.create_unique_constraint("uq_groups_name_domain_id", "groups", ["name", "domain_id"])


def downgrade() -> None:
    op.drop_constraint("uq_groups_name_domain_id", "groups", type_="unique")
    op.create_unique_constraint("uq_groups_name_domain_name", "groups", ["name", "domain_name"])

    op.drop_index("ix_groups_domain_id", table_name="groups")
    op.drop_constraint("fk_groups_domain_id_domains", "groups", type_="foreignkey")
    op.create_foreign_key(
        "fk_groups_domain_name_domains",
        "groups",
        "domains",
        ["domain_name"],
        ["name"],
        ondelete="CASCADE",
        onupdate="CASCADE",
    )
    op.drop_column("groups", "domain_id")

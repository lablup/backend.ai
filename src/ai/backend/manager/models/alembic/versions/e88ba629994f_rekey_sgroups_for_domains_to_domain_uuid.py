"""rekey sgroups_for_domains to domain uuid

``sgroups_for_domains`` referenced its domain by the ``domains.name`` FK
column while the RBAC tables key domains by ``domains.id``. This migration
replaces the ``domain`` name FK column with a ``domain_id`` FK column
referencing ``domains.id``, completing the UUID keying of the mapping table
together with the preceding ``resource_group_id`` rekey.

Revision ID: e88ba629994f
Revises: 9896475bc170
Create Date: 2026-08-03 21:20:21.064822

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "e88ba629994f"
down_revision = "9896475bc170"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    op.add_column("sgroups_for_domains", sa.Column("domain_id", GUID(), nullable=True))
    conn.execute(
        sa.text("""
            UPDATE sgroups_for_domains sfd
            SET domain_id = d.id
            FROM domains d
            WHERE sfd.domain = d.name
        """)
    )
    op.alter_column("sgroups_for_domains", "domain_id", nullable=False)
    op.drop_constraint(
        "fk_sgroups_for_domains_domain_domains", "sgroups_for_domains", type_="foreignkey"
    )
    op.drop_constraint("uq_sgroup_domain", "sgroups_for_domains", type_="unique")
    op.drop_index("ix_sgroups_for_domains_domain", table_name="sgroups_for_domains")
    op.drop_column("sgroups_for_domains", "domain")
    op.create_unique_constraint(
        "uq_sgroup_domain", "sgroups_for_domains", ["resource_group_id", "domain_id"]
    )
    op.create_index("ix_sgroups_for_domains_domain_id", "sgroups_for_domains", ["domain_id"])
    op.create_foreign_key(
        "fk_sgroups_for_domains_domain_id_domains",
        "sgroups_for_domains",
        "domains",
        ["domain_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )


def downgrade() -> None:
    conn = op.get_bind()
    op.add_column("sgroups_for_domains", sa.Column("domain", sa.String(length=64), nullable=True))
    conn.execute(
        sa.text("""
            UPDATE sgroups_for_domains sfd
            SET domain = d.name
            FROM domains d
            WHERE sfd.domain_id = d.id
        """)
    )
    op.alter_column("sgroups_for_domains", "domain", nullable=False)
    op.drop_constraint(
        "fk_sgroups_for_domains_domain_id_domains", "sgroups_for_domains", type_="foreignkey"
    )
    op.drop_constraint("uq_sgroup_domain", "sgroups_for_domains", type_="unique")
    op.drop_index("ix_sgroups_for_domains_domain_id", table_name="sgroups_for_domains")
    op.drop_column("sgroups_for_domains", "domain_id")
    op.create_unique_constraint(
        "uq_sgroup_domain", "sgroups_for_domains", ["resource_group_id", "domain"]
    )
    op.create_index("ix_sgroups_for_domains_domain", "sgroups_for_domains", ["domain"])
    op.create_foreign_key(
        "fk_sgroups_for_domains_domain_domains",
        "sgroups_for_domains",
        "domains",
        ["domain"],
        ["name"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )

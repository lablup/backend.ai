"""migrate deployment_revisions.runtime_variant to runtime_variant_id UUID FK

Replaces the ``runtime_variant`` string column on ``deployment_revisions``
with a ``runtime_variant_id`` UUID column that carries a proper foreign
key to ``runtime_variants.id`` with ``ON DELETE RESTRICT``.

Having the reference as a UUID FK lets the Manager drop all name-based
dispatch in the deployment pipeline (the column previously mirrored
``RuntimeVariant`` enum values and was used both for storage and for
runtime branching). RESTRICT prevents removal of a variant row while
any revision still references it.

Backfill semantics:
* Each existing revision's string value is resolved to the matching
  ``runtime_variants.name`` row.
* Any revision whose string value no longer matches a row (for example
  because the named variant was removed between operator runs) is
  backfilled with the ``custom`` variant as a safe fallback — ``custom``
  is guaranteed to exist by the seed fixture and defers all behavior to
  the vfolder config files.

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-04-19

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

# revision identifiers, used by Alembic.
revision = "d8e9f0a1b2c3"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


_FK_NAME = "fk_deployment_revisions_runtime_variant_id_runtime_variants"


def upgrade() -> None:
    op.add_column(
        "deployment_revisions",
        sa.Column("runtime_variant_id", pgsql.UUID(as_uuid=True), nullable=True),
    )
    # Resolve the string value to the matching runtime_variants row.
    op.execute(
        sa.text(
            "UPDATE deployment_revisions dr "
            "SET runtime_variant_id = rv.id "
            "FROM runtime_variants rv "
            "WHERE rv.name = dr.runtime_variant"
        )
    )
    # Fall back to the ``custom`` variant for any revision whose string
    # did not resolve — e.g. a variant row that was removed by an
    # operator after deployments were created.
    op.execute(
        sa.text(
            "UPDATE deployment_revisions "
            "SET runtime_variant_id = ("
            "    SELECT id FROM runtime_variants WHERE name = 'custom'"
            ") "
            "WHERE runtime_variant_id IS NULL"
        )
    )
    op.alter_column("deployment_revisions", "runtime_variant_id", nullable=False)
    op.create_foreign_key(
        _FK_NAME,
        source_table="deployment_revisions",
        referent_table="runtime_variants",
        local_cols=["runtime_variant_id"],
        remote_cols=["id"],
        ondelete="RESTRICT",
    )
    op.drop_column("deployment_revisions", "runtime_variant")


def downgrade() -> None:
    op.add_column(
        "deployment_revisions",
        sa.Column(
            "runtime_variant",
            sa.String(length=64),
            nullable=True,
        ),
    )
    # Restore the string value from the variant row.
    op.execute(
        sa.text(
            "UPDATE deployment_revisions dr "
            "SET runtime_variant = rv.name "
            "FROM runtime_variants rv "
            "WHERE rv.id = dr.runtime_variant_id"
        )
    )
    op.alter_column(
        "deployment_revisions",
        "runtime_variant",
        nullable=False,
        server_default="custom",
    )
    op.drop_constraint(_FK_NAME, "deployment_revisions", type_="foreignkey")
    op.drop_column("deployment_revisions", "runtime_variant_id")

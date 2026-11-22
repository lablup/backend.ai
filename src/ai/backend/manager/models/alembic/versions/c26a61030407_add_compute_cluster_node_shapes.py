"""Add the node shapes a compute cluster's gateway reports to compute_clusters."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c26a61030407"  # Part of: NEXT_RELEASE_VERSION
down_revision = "b416c30abfd3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("compute_clusters")}
    if "node_shapes" in columns:
        return
    op.add_column(
        "compute_clusters",
        sa.Column("node_shapes", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.execute("ALTER TABLE compute_clusters DROP COLUMN IF EXISTS node_shapes")

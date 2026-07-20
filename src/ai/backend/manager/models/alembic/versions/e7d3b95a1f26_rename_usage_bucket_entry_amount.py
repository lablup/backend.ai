"""rename usage_bucket_entries.amount to resource_usage

The column holds resource-seconds, not a resource amount.  Under the old name
``amount * duration_seconds`` reads like the quantity a caller wants, when both
columns are already sums and their product is a cross product.

``resource_usage`` is the name the three parent bucket tables and
``kernel_usage_records`` already use for this quantity, so the table now speaks
the same vocabulary as the rest of the schema.

Revision ID: e7d3b95a1f26
Revises: c4a91d7e05b2
Create Date: 2026-07-20 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e7d3b95a1f26"
down_revision = "c4a91d7e05b2"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "usage_bucket_entries",
        "amount",
        new_column_name="resource_usage",
        existing_type=sa.Numeric(precision=32, scale=6),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "usage_bucket_entries",
        "resource_usage",
        new_column_name="amount",
        existing_type=sa.Numeric(precision=32, scale=6),
        existing_nullable=False,
    )

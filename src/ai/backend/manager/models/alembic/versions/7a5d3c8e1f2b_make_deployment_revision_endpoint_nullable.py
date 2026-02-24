"""make deployment_revision endpoint nullable

Revision ID: 7a5d3c8e1f2b
Revises: 03ff6767b2e4
Create Date: 2026-02-24

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "7a5d3c8e1f2b"
down_revision = "03ff6767b2e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make endpoint column nullable to support orphan revisions
    op.alter_column(
        "deployment_revisions",
        "endpoint",
        existing_type=GUID(),
        nullable=True,
    )

    # Drop the existing unique constraint
    op.drop_constraint(
        "uq_deployment_revisions_endpoint_revision_number",
        "deployment_revisions",
    )

    # Create a partial unique index that only applies when endpoint IS NOT NULL
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_deployment_revisions_endpoint_revision_number "
            "ON deployment_revisions (endpoint, revision_number) "
            "WHERE endpoint IS NOT NULL"
        )
    )


def downgrade() -> None:
    # Drop partial unique index
    op.drop_index(
        "uq_deployment_revisions_endpoint_revision_number",
        table_name="deployment_revisions",
    )

    # Recreate original unique constraint
    op.create_unique_constraint(
        "uq_deployment_revisions_endpoint_revision_number",
        "deployment_revisions",
        ["endpoint", "revision_number"],
    )

    # Make endpoint column non-nullable again
    op.alter_column(
        "deployment_revisions",
        "endpoint",
        existing_type=GUID(),
        nullable=False,
    )

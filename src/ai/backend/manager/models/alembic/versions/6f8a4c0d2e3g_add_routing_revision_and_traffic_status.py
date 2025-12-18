"""add routing revision and traffic_status columns

Revision ID: 6f8a4c0d2e3g
Revises: 5e7a3b9c1d2f
Create Date: 2025-12-17

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "6f8a4c0d2e3g"
down_revision = "5e7a3b9c1d2f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create RouteTrafficStatus enum type (active/inactive only)
    op.execute("CREATE TYPE routetrafficstatus AS ENUM ('active', 'inactive')")

    # 2. Add revision column (nullable, no FK constraint)
    op.add_column(
        "routings",
        sa.Column("revision", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # 3. Add traffic_status column with default 'active'
    op.add_column(
        "routings",
        sa.Column(
            "traffic_status",
            postgresql.ENUM(
                "active",
                "inactive",
                name="routetrafficstatus",
                create_type=False,
            ),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
    )

    # 4. Set revision for existing routes from endpoint.current_revision
    op.execute("""
        UPDATE routings r
        SET revision = e.current_revision
        FROM endpoints e
        WHERE r.endpoint = e.id
          AND e.current_revision IS NOT NULL
    """)


def downgrade() -> None:
    op.drop_column("routings", "traffic_status")
    op.drop_column("routings", "revision")
    op.execute("DROP TYPE routetrafficstatus")

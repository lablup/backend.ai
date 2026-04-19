"""convert routing status and traffic_status from native ENUM to VARCHAR

Revision ID: 04e150fdefa0
Revises: b16a619f26d5
Create Date: 2026-04-05

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "04e150fdefa0"
down_revision = "b16a619f26d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert status: native ENUM → VARCHAR
    op.alter_column(
        "routings",
        "status",
        type_=sa.VARCHAR(64),
        existing_nullable=False,
        postgresql_using="status::text",
    )

    # Convert traffic_status: native ENUM → VARCHAR
    op.alter_column(
        "routings",
        "traffic_status",
        type_=sa.VARCHAR(64),
        existing_nullable=False,
        server_default=sa.text("'active'"),
        postgresql_using="traffic_status::text",
    )

    # Drop the native ENUM types
    op.execute(sa.text("DROP TYPE IF EXISTS routestatus"))
    op.execute(sa.text("DROP TYPE IF EXISTS routetrafficstatus"))


def downgrade() -> None:
    # Recreate native ENUM types — include 'healthy', 'unhealthy', 'degraded'
    # which were converted to 'running' + health_status by e3111d960208 but
    # must exist in the enum for that migration's downgrade to cast back.
    op.execute(
        sa.text(
            "CREATE TYPE routestatus AS ENUM "
            "('provisioning', 'running', 'healthy', 'unhealthy', 'degraded',"
            " 'terminating', 'terminated', 'failed_to_start')"
        )
    )
    op.execute(sa.text("CREATE TYPE routetrafficstatus AS ENUM ('active', 'inactive')"))

    # Convert back: VARCHAR → native ENUM (create_type=False since types are
    # already created above via raw SQL)
    op.alter_column(
        "routings",
        "status",
        type_=postgresql.ENUM(
            "provisioning",
            "running",
            "healthy",
            "unhealthy",
            "degraded",
            "terminating",
            "terminated",
            "failed_to_start",
            name="routestatus",
            create_type=False,
        ),
        existing_nullable=False,
        postgresql_using="status::routestatus",
    )
    # Drop the VARCHAR default before altering the type, otherwise Postgres
    # cannot automatically cast the existing default ('active'::text) to the
    # new enum type and raises DatatypeMismatchError.
    op.execute(sa.text("ALTER TABLE routings ALTER COLUMN traffic_status DROP DEFAULT"))
    op.alter_column(
        "routings",
        "traffic_status",
        type_=postgresql.ENUM("active", "inactive", name="routetrafficstatus", create_type=False),
        existing_nullable=False,
        postgresql_using="traffic_status::routetrafficstatus",
    )
    op.execute(
        sa.text(
            "ALTER TABLE routings ALTER COLUMN traffic_status "
            "SET DEFAULT 'active'::routetrafficstatus"
        )
    )

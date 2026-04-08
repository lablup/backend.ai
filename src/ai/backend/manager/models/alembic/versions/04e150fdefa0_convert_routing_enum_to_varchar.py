"""convert routing status and traffic_status from native ENUM to VARCHAR

Revision ID: 04e150fdefa0
Revises: b16a619f26d5
Create Date: 2026-04-05

"""

import sqlalchemy as sa
from alembic import op

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
    # Recreate native ENUM types
    op.execute(
        sa.text(
            "CREATE TYPE routestatus AS ENUM "
            "('provisioning', 'running', 'terminating', 'terminated', 'failed_to_start')"
        )
    )
    op.execute(sa.text("CREATE TYPE routetrafficstatus AS ENUM ('active', 'inactive')"))

    # Convert back: VARCHAR → native ENUM
    op.alter_column(
        "routings",
        "status",
        type_=sa.Enum(
            "provisioning",
            "running",
            "terminating",
            "terminated",
            "failed_to_start",
            name="routestatus",
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
        type_=sa.Enum("active", "inactive", name="routetrafficstatus"),
        existing_nullable=False,
        postgresql_using="traffic_status::routetrafficstatus",
    )
    op.execute(
        sa.text(
            "ALTER TABLE routings ALTER COLUMN traffic_status "
            "SET DEFAULT 'active'::routetrafficstatus"
        )
    )

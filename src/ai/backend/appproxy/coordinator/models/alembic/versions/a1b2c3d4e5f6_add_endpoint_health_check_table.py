"""add endpoint health check table

Revision ID: a1b2c3d4e5f6
Revises: 7dbbc087108e
Create Date: 2025-06-30 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from ai.backend.appproxy.coordinator.models.base import GUID, convention

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "7dbbc087108e"
branch_labels = None
depends_on = None


metadata = sa.MetaData(naming_convention=convention)
circuit = sa.Table(
    "circuits",
    metadata,
    sa.Column("id", GUID, primary_key=True),
    sa.Column("endpoint_id", GUID, primary_key=True),
)
endpoint = sa.Table(
    "endpoints",
    metadata,
    sa.Column("id", GUID, primary_key=True),
)


def upgrade():
    # Create endpoints table
    op.create_table(
        "endpoints",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "health_check_enabled",
            sa.Boolean(),
            nullable=False,
            default=False,
            server_default="false",
        ),
        sa.Column("health_check_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    conn = op.get_bind()
    query = (
        sa.select(circuit.c.id, circuit.c.endpoint_id)
        .select_from(circuit)
        .where(circuit.c.endpoint_id.is_not(None))
    )
    rows = conn.execute(query).fetchall()
    endpoint_ids = [r.endpoint_id for r in rows]
    query = endpoint.insert().values([{"id": e} for e in endpoint_ids])
    op.execute(query)


def downgrade():
    # Drop endpoints table
    op.drop_table("endpoints")

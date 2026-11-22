"""Create the compute_clusters table for Kubernetes-backed resource groups."""

import sqlalchemy as sa
from alembic import op

revision = "b416c30abfd3"  # Part of: NEXT_RELEASE_VERSION
down_revision = "6f6d61f67ca0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "compute_clusters" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "compute_clusters",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("uuid_generate_v7()")),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("api_server", sa.String(length=2048), nullable=False),
        sa.Column("kubeconfig", sa.Text(), nullable=False),
        sa.Column("namespace_prefix", sa.String(length=32), nullable=False, server_default="bai-"),
        sa.Column("gateway_addr", sa.String(length=256), nullable=True),
        sa.Column("gateway_public_key", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="UNKNOWN"),
        sa.Column("status_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_compute_clusters")),
        sa.UniqueConstraint("name", name=op.f("uq_compute_clusters_name")),
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS compute_clusters")

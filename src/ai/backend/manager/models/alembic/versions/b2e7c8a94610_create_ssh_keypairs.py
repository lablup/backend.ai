"""Create the user-owned SSH keypairs table."""

import sqlalchemy as sa
from alembic import op

revision = "b2e7c8a94610"  # Part of: NEXT_RELEASE_VERSION
down_revision = "111e2255487b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ssh_keypairs",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("uuid_generate_v7()")),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("private_key", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ssh_keypairs")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.uuid"],
            name=op.f("fk_ssh_keypairs_user_id_users"),
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_ssh_keypairs_user_id", "ssh_keypairs", ["user_id"])
    op.create_index(
        "uq_ssh_keypairs_is_default",
        "ssh_keypairs",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )


def downgrade() -> None:
    op.drop_table("ssh_keypairs")

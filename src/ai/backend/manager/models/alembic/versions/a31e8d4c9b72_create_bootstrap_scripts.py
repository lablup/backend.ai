"""Move keypair scripts into entity-addressed bootstrap scripts."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "a31e8d4c9b72"
down_revision = "ede445fb9d0d"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bootstrap_scripts",
        sa.Column(
            "id",
            postgresql.UUID(),
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", postgresql.UUID(), nullable=False),
        sa.Column("script", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bootstrap_scripts")),
        sa.CheckConstraint(
            "char_length(script) <= 65536", name=op.f("ck_bootstrap_scripts_script_length")
        ),
    )
    op.create_index(
        "uq_bootstrap_scripts_is_default",
        "bootstrap_scripts",
        ["entity_type", "entity_id"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )
    op.execute(
        sa.text("""
        INSERT INTO bootstrap_scripts (entity_type, entity_id, script, is_default)
        SELECT 'user', k."user", k.bootstrap_script, k.is_default
        FROM keypairs AS k
    """)
    )
    op.drop_column("keypairs", "bootstrap_script")


def downgrade() -> None:
    op.add_column(
        "keypairs",
        sa.Column("bootstrap_script", sa.String(64 * 1024), nullable=False, server_default=""),
    )
    op.execute(
        sa.text("""
        UPDATE keypairs AS k
        SET bootstrap_script = b.script
        FROM bootstrap_scripts AS b
        WHERE b.entity_type = 'user' AND b.entity_id = k."user" AND b.is_default
    """)
    )
    op.drop_table("bootstrap_scripts")

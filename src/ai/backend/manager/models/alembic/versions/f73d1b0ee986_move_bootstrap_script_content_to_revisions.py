"""Move bootstrap script content into revisions, and soft-delete bootstrap scripts."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "f73d1b0ee986"  # Part of: NEXT_RELEASE_VERSION
down_revision = "456a338e7c3a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bootstrap_script_revisions",
        sa.Column(
            "id",
            postgresql.UUID(),
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("script_id", postgresql.UUID(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("script", sa.Text(), nullable=False),
        sa.Column("creator_id", postgresql.UUID(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bootstrap_script_revisions")),
        sa.ForeignKeyConstraint(
            ["script_id"],
            ["bootstrap_scripts.id"],
            name=op.f("fk_bootstrap_script_revisions_script_id_bootstrap_scripts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["users.uuid"],
            name=op.f("fk_bootstrap_script_revisions_creator_id_users"),
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "script_id", "revision_number", name=op.f("uq_bootstrap_script_revisions_script_id")
        ),
        sa.CheckConstraint(
            "char_length(script) <= 65536",
            name=op.f("ck_bootstrap_script_revisions_script_length"),
        ),
    )
    # The writer of an existing script is unknown, so its first revision names no creator.
    op.execute(
        sa.text("""
        INSERT INTO bootstrap_script_revisions (script_id, revision_number, script, created_at)
        SELECT id, 1, script, created_at FROM bootstrap_scripts
    """)
    )
    op.drop_column("bootstrap_scripts", "script")
    op.add_column(
        "bootstrap_scripts",
        sa.Column(
            "deleted_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.null()
        ),
    )
    op.drop_index("uq_bootstrap_scripts_is_default", table_name="bootstrap_scripts")
    op.create_index(
        "uq_bootstrap_scripts_is_default",
        "bootstrap_scripts",
        ["entity_type", "entity_id"],
        unique=True,
        postgresql_where=sa.text("is_default AND deleted_at IS NULL"),
    )


def downgrade() -> None:
    # The old schema cannot hold a soft-deleted script, so those go.
    op.execute(sa.text("DELETE FROM bootstrap_scripts WHERE deleted_at IS NOT NULL"))
    op.drop_index("uq_bootstrap_scripts_is_default", table_name="bootstrap_scripts")
    op.create_index(
        "uq_bootstrap_scripts_is_default",
        "bootstrap_scripts",
        ["entity_type", "entity_id"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )
    op.drop_column("bootstrap_scripts", "deleted_at")
    op.add_column(
        "bootstrap_scripts",
        sa.Column("script", sa.Text(), nullable=False, server_default=""),
    )
    op.execute(
        sa.text("""
        UPDATE bootstrap_scripts AS s
        SET script = r.script
        FROM (
            SELECT DISTINCT ON (script_id) script_id, script
            FROM bootstrap_script_revisions
            ORDER BY script_id, revision_number DESC
        ) AS r
        WHERE r.script_id = s.id
    """)
    )
    op.alter_column("bootstrap_scripts", "script", server_default=None)
    op.create_check_constraint(
        op.f("ck_bootstrap_scripts_script_length"),
        "bootstrap_scripts",
        "char_length(script) <= 65536",
    )
    op.drop_table("bootstrap_script_revisions")

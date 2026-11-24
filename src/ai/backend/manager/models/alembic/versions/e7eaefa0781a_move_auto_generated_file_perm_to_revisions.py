"""Move auto-generated file permission to revisions

Every revision of a file takes the file's permission, and the file keeps only its path and
default mark. A revision then holds everything a session is written with.

Revision ID: e7eaefa0781a
Revises: 4ab2e2e50939
Create Date: 2026-11-24

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "e7eaefa0781a"  # Part of: NEXT_RELEASE_VERSION
down_revision = "4ab2e2e50939"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE auto_generated_file_revisions ADD COLUMN perm TEXT")
    op.execute("""
        UPDATE auto_generated_file_revisions r
        SET perm = f.perm
        FROM auto_generated_files f
        WHERE f.id = r.file_id
    """)
    op.execute("ALTER TABLE auto_generated_file_revisions ALTER COLUMN perm SET NOT NULL")
    op.execute(
        "ALTER TABLE auto_generated_file_revisions "
        "ADD CONSTRAINT ck_auto_generated_file_revisions_perm_length "
        "CHECK (char_length(perm) <= 4)"
    )
    op.execute(
        "ALTER TABLE auto_generated_files DROP CONSTRAINT ck_auto_generated_files_perm_length"
    )
    op.execute("ALTER TABLE auto_generated_files DROP COLUMN perm")


def downgrade() -> None:
    op.execute("ALTER TABLE auto_generated_files ADD COLUMN perm TEXT")
    op.execute("""
        UPDATE auto_generated_files f
        SET perm = latest.perm
        FROM (
            SELECT DISTINCT ON (file_id) file_id, perm
            FROM auto_generated_file_revisions
            ORDER BY file_id, revision_number DESC
        ) latest
        WHERE latest.file_id = f.id
    """)
    op.execute("UPDATE auto_generated_files SET perm = '644' WHERE perm IS NULL")
    op.execute("ALTER TABLE auto_generated_files ALTER COLUMN perm SET NOT NULL")
    op.execute(
        "ALTER TABLE auto_generated_files ADD CONSTRAINT ck_auto_generated_files_perm_length "
        "CHECK (char_length(perm) <= 4)"
    )
    op.execute(
        "ALTER TABLE auto_generated_file_revisions "
        "DROP CONSTRAINT ck_auto_generated_file_revisions_perm_length"
    )
    op.execute("ALTER TABLE auto_generated_file_revisions DROP COLUMN perm")

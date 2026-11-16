"""Move auto-generated file data to revisions

Each file's data becomes its revision 1, and the file keeps only its path, permission and
default mark. The writer of the existing data is not known, so the revisions name none.

Revision ID: 75cc7e8fc4d2
Revises: 592dedb4a39c
Create Date: 2026-11-16

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "75cc7e8fc4d2"  # Part of: NEXT_RELEASE_VERSION
down_revision = "592dedb4a39c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO auto_generated_file_revisions (file_id, revision_number, data, created_at)
        SELECT id, 1, data, updated_at FROM auto_generated_files
    """)
    op.execute(
        "ALTER TABLE auto_generated_files DROP CONSTRAINT ck_auto_generated_files_data_length"
    )
    op.execute("ALTER TABLE auto_generated_files DROP COLUMN data")


def downgrade() -> None:
    op.execute("ALTER TABLE auto_generated_files ADD COLUMN data TEXT")
    op.execute("""
        UPDATE auto_generated_files f
        SET data = latest.data
        FROM (
            SELECT DISTINCT ON (file_id) file_id, data
            FROM auto_generated_file_revisions
            ORDER BY file_id, revision_number DESC
        ) latest
        WHERE latest.file_id = f.id
    """)
    op.execute("UPDATE auto_generated_files SET data = '' WHERE data IS NULL")
    op.execute("ALTER TABLE auto_generated_files ALTER COLUMN data SET NOT NULL")
    op.execute(
        "ALTER TABLE auto_generated_files ADD CONSTRAINT ck_auto_generated_files_data_length "
        "CHECK (char_length(data) <= 65536)"
    )
    op.execute("DELETE FROM auto_generated_file_revisions")

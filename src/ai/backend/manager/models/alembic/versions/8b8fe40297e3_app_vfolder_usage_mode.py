"""app_vfolder_usage_mode

Revision ID: 8b8fe40297e3
Revises: 75ea2b136830
Create Date: 2024-03-10 17:37:37.058155

"""

import enum
import textwrap

from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "8b8fe40297e3"
down_revision = "75ea2b136830"
branch_labels = None
depends_on = None


class NewVFolderUsageMode(enum.StrEnum):
    GENERAL = "general"
    MODEL = "model"
    DATA = "data"
    APP = "app"


class OldVFolderUsageMode(enum.StrEnum):
    GENERAL = "general"
    MODEL = "model"
    DATA = "data"


def upgrade():
    conn = op.get_bind()

    # Add `app` to vfolders.usage_mode
    usage_mode_choices = [m.value for m in NewVFolderUsageMode]
    str_choice = "','".join(usage_mode_choices)
    conn.execute(text("ALTER TYPE vfolderusagemode RENAME TO vfolderusagemode__;"))
    conn.execute(text(f"CREATE TYPE vfolderusagemode as enum ('{str_choice}')"))
    conn.execute(
        text(
            textwrap.dedent(
                """\
        ALTER TABLE vfolders
            ALTER COLUMN usage_mode TYPE vfolderusagemode USING usage_mode::text::vfolderusagemode;
    """
            )
        )
    )
    conn.execute(text("DROP TYPE vfolderusagemode__;"))


def downgrade():
    conn = op.get_bind()

    # Replace `app` usage_mode to `general`
    conn.execute(text("UPDATE vfolders SET usage_mode = 'general' WHERE usage_mode = 'app';"))

    # Remove `app` usage_mode type
    usage_mode_choices = [m.value for m in OldVFolderUsageMode]
    str_choice = "','".join(usage_mode_choices)
    conn.execute(text("ALTER TYPE vfolderusagemode RENAME TO vfolderusagemode__;"))
    conn.execute(text(f"CREATE TYPE vfolderusagemode as enum ('{str_choice}')"))
    conn.execute(
        text(
            textwrap.dedent(
                """\
        ALTER TABLE vfolders
            ALTER COLUMN usage_mode TYPE vfolderusagemode USING usage_mode::text::vfolderusagemode;
    """
            )
        )
    )
    conn.execute(text("DROP TYPE vfolderusagemode__;"))

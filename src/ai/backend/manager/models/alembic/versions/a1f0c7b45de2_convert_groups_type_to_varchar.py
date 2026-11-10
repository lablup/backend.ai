"""convert groups.type from native ENUM to VARCHAR

Revision ID: a1f0c7b45de2
Revises: c8e4b1a09d37
Create Date: 2026-09-01

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a1f0c7b45de2"
down_revision = "c8e4b1a09d37"
branch_labels = None
depends_on = None

PROJECT_TYPES = ("general", "model-store", "personal")


def upgrade() -> None:
    op.alter_column(
        "groups",
        "type",
        type_=sa.VARCHAR(64),
        existing_nullable=False,
        postgresql_using="type::text",
    )
    op.execute(sa.text("DROP TYPE IF EXISTS projecttype"))


def downgrade() -> None:
    # 'personal' is included so rows written after the upgrade can be cast back.
    op.execute(
        sa.text(
            f"CREATE TYPE projecttype AS ENUM ({', '.join(repr(value) for value in PROJECT_TYPES)})"
        )
    )
    op.alter_column(
        "groups",
        "type",
        type_=postgresql.ENUM(*PROJECT_TYPES, name="projecttype", create_type=False),
        existing_nullable=False,
        postgresql_using="type::projecttype",
    )

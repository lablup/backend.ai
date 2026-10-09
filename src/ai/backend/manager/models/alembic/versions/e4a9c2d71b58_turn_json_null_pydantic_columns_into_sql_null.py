"""Turn JSON null in nullable PydanticColumn columns into SQL NULL

`PydanticColumn` bound None as the JSON value `null`. Rewrite those values as SQL NULL.

Revision ID: e4a9c2d71b58
Revises: e8b41c6d2f73
Create Date: 2026-10-08

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e4a9c2d71b58"
down_revision = "e8b41c6d2f73"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


NULLABLE_PYDANTIC_COLUMNS: Final[tuple[tuple[str, str], ...]] = (
    ("deployment_revisions", "model_definition"),
    ("deployment_revision_presets", "model_definition"),
    ("routings", "health_check"),
    ("runtime_variant_presets", "ui_option"),
    ("scaling_groups", "fair_share_spec"),
)


def turn_json_null_into_sql_null(conn: sa.engine.Connection) -> None:
    for table, column in NULLABLE_PYDANTIC_COLUMNS:
        conn.execute(
            sa.text(f"UPDATE {table} SET {column} = NULL WHERE jsonb_typeof({column}) = 'null'")
        )


def upgrade() -> None:
    turn_json_null_into_sql_null(op.get_bind())


def downgrade() -> None:
    # Both values read back as None, so nothing is restored.
    pass

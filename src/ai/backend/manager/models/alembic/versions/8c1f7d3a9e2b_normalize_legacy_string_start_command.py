"""normalize legacy string start_command in stored model definitions

Wrap legacy string ``start_command`` values as one-item lists so rows
created before #11402 narrowed the schema to ``list[str] | None`` pass
Pydantic validation.

Revision ID: 8c1f7d3a9e2b
Revises: dec0deba5893
Create Date: 2026-04-30

"""

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "8c1f7d3a9e2b"
down_revision = "dec0deba5893"
# Part of: 26.5.0
branch_labels = None
depends_on = None


def _normalize_model_definition(conn: Connection, table: str, column: str) -> None:
    rows = conn.execute(
        sa.text(f"SELECT id, {column} FROM {table} WHERE {column} IS NOT NULL")
    ).fetchall()

    for row_id, model_definition in rows:
        changed = False
        for model in model_definition.get("models") or []:
            try:
                start_command = model["service"]["start_command"]
            except (KeyError, TypeError):
                continue
            if isinstance(start_command, str):
                model["service"]["start_command"] = [start_command]
                changed = True

        if changed:
            conn.execute(
                sa.text(f"UPDATE {table} SET {column} = CAST(:definition AS JSONB) WHERE id = :id"),
                {"definition": json.dumps(model_definition), "id": row_id},
            )


def upgrade() -> None:
    conn = op.get_bind()
    _normalize_model_definition(conn, "deployment_revisions", "model_definition")
    _normalize_model_definition(conn, "deployment_revision_presets", "model_definition")
    _normalize_model_definition(conn, "runtime_variants", "default_model_definition")


def downgrade() -> None:
    # No-op: list form is also valid under the pre-#11402 schema.
    pass

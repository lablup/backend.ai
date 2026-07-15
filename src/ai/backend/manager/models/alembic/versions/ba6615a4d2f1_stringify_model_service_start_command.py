"""stringify model service start_command

Convert stored model-definition ``service.start_command`` values from argv
lists back to a single command string. This keeps persisted model definitions
aligned with the internal model representation while accepting rows already
converted by the previous compatibility migrations.

Revision ID: ba6615a4d2f1
Revises: ada41cb881bb
Create Date: 2026-06-29

"""

import json
import shlex

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "ba6615a4d2f1"
down_revision = "ada41cb881bb"
# Part of: 26.7.0 (main)
branch_labels = None
depends_on = None


def _stringify_model_definition(conn: Connection, table: str, column: str) -> None:
    rows = conn.execute(
        sa.text(f"SELECT id, {column} FROM {table} WHERE {column} IS NOT NULL")
    ).fetchall()

    for row_id, model_definition in rows:
        # The IS NOT NULL filter only excludes SQL NULL; a JSONB column can still
        # hold a JSON ``null`` (or any non-object value) that decodes to a non-dict.
        if not isinstance(model_definition, dict):
            continue
        changed = False
        models = model_definition.get("models") or []
        for model in models:
            try:
                start_command = model["service"]["start_command"]
            except (KeyError, TypeError):
                continue
            if isinstance(start_command, list):
                model["service"]["start_command"] = shlex.join(start_command)
                changed = True

        if changed:
            model_definition["models"] = models
            conn.execute(
                sa.text(f"UPDATE {table} SET {column} = CAST(:definition AS JSONB) WHERE id = :id"),
                {"definition": json.dumps(model_definition), "id": row_id},
            )


def upgrade() -> None:
    conn = op.get_bind()
    _stringify_model_definition(conn, "deployment_revisions", "model_definition")
    _stringify_model_definition(conn, "deployment_revision_presets", "model_definition")
    _stringify_model_definition(conn, "runtime_variants", "default_model_definition")


def downgrade() -> None:
    # Data-only compatibility conversion. Reconstructing the previous argv
    # representation would be lossy for shell scripts, so this is a no-op.
    pass

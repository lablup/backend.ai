"""renormalize legacy hyphenated ``start-command`` key

``service`` entries written with the legacy hyphenated key
``start-command`` were not matched by 8c1f7d3a9e2b (it only looked
up ``start_command`` with an underscore), so the key was left
untouched and Pydantic validation now rejects them. Move the value
under ``start_command`` and drop the hyphenated key. If the value
is a string, split it on whitespace into argv tokens before
storing.

Existing ``start_command`` values (already under the underscored
key) are left untouched even if a stray ``start-command`` key
also exists — the underscored value wins and the hyphenated key
is dropped.

Revision ID: 46e007d9b237
Revises: c4d5e6f7a8b9
Create Date: 2026-05-06

"""

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
# Part of: 26.4.6 (main)
revision = "46e007d9b237"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def _renormalize_model_definition(conn: Connection, table: str, column: str) -> None:
    rows = conn.execute(
        sa.text(f"SELECT id, {column} FROM {table} WHERE {column} IS NOT NULL")
    ).fetchall()

    for row_id, model_definition in rows:
        if not isinstance(model_definition, dict):
            continue
        changed = False
        for model in model_definition.get("models") or []:
            if not isinstance(model, dict):
                continue
            service = model.get("service")
            if not isinstance(service, dict):
                continue

            if "start-command" not in service:
                continue
            hyphen_value = service.pop("start-command")
            changed = True
            if "start_command" in service:
                continue
            if isinstance(hyphen_value, str):
                hyphen_value = hyphen_value.split()
            service["start_command"] = hyphen_value

        if changed:
            conn.execute(
                sa.text(f"UPDATE {table} SET {column} = CAST(:definition AS JSONB) WHERE id = :id"),
                {"definition": json.dumps(model_definition), "id": row_id},
            )


def upgrade() -> None:
    conn = op.get_bind()
    _renormalize_model_definition(conn, "deployment_revisions", "model_definition")
    _renormalize_model_definition(conn, "deployment_revision_presets", "model_definition")
    _renormalize_model_definition(conn, "runtime_variants", "default_model_definition")


def downgrade() -> None:
    # No-op: argv-list form is valid under any prior schema, and the
    # hyphenated legacy key was never officially supported.
    pass

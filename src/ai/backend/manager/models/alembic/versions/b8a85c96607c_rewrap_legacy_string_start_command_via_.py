"""rewrap legacy string start_command via shell -c

Repairs single-token argv rows broken by ``8c1f7d3a9e2b`` (e.g.
``["python service.py"]``) by rewrapping as ``[shell, "-c", token]``
when ``service.shell`` is set. Rows without ``shell`` are left as-is
to match the updated validator (no shell -> no wrap). Re-applicable.

Revision ID: b8a85c96607c
Revises: 7a9be5b982c0
Create Date: 2026-05-19

"""

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "b8a85c96607c"
down_revision = "7a9be5b982c0"
# Part of: 26.5.1
branch_labels = None
depends_on = None


def _rewrap_model_definition(conn: Connection, table: str, column: str) -> None:
    rows = conn.execute(
        sa.text(f"SELECT id, {column} FROM {table} WHERE {column} IS NOT NULL")
    ).fetchall()

    for row_id, model_definition in rows:
        changed = False
        for model in model_definition.get("models") or []:
            service = model.get("service") or {}
            start_command = service.get("start_command")
            shell = service.get("shell")
            if (
                isinstance(start_command, list)
                and len(start_command) == 1
                and " " in start_command[0]
                and shell
            ):
                service["start_command"] = [shell, "-c", start_command[0]]
                changed = True

        if changed:
            conn.execute(
                sa.text(f"UPDATE {table} SET {column} = CAST(:definition AS JSONB) WHERE id = :id"),
                {"definition": json.dumps(model_definition), "id": row_id},
            )


def upgrade() -> None:
    conn = op.get_bind()
    _rewrap_model_definition(conn, "deployment_revisions", "model_definition")
    _rewrap_model_definition(conn, "deployment_revision_presets", "model_definition")
    _rewrap_model_definition(conn, "runtime_variants", "default_model_definition")


def downgrade() -> None:
    # No-op: the ``[shell, "-c", token]`` form is also valid argv under
    # any prior schema.
    pass

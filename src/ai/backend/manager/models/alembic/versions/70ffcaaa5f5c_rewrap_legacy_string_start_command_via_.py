"""rewrap legacy string start_command via shell -c

Migration ``8c1f7d3a9e2b`` (Part of: 26.5.0) wrapped any legacy ``str``
``start_command`` as a one-item argv list (e.g. ``"python service.py"``
became ``["python service.py"]``). That value is meaningless at exec
time -- ``execve`` would look for a binary literally named
``"python service.py"`` -- and it loses the shell semantics the user
originally intended.

This migration repairs those rows by replacing single-element argv
lists whose only token still looks like a shell command (contains
whitespace) with ``[shell, "-c", token]``, where ``shell`` comes from
the sibling ``service.shell`` field and falls back to ``/bin/bash`` to
match ``ai.backend.common.config.DEFAULT_SHELL``. Multi-token argv
lists and single-token lists without whitespace are left untouched,
so the migration is safe to re-apply.

Revision ID: 70ffcaaa5f5c
Revises: ba42cb865efe
Create Date: 2026-05-18

"""

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "70ffcaaa5f5c"
down_revision = "ba42cb865efe"
# Part of: 26.5.1
branch_labels = None
depends_on = None

DEFAULT_SHELL = "/bin/bash"


def _rewrap_model_definition(conn: Connection, table: str, column: str) -> None:
    rows = conn.execute(
        sa.text(f"SELECT id, {column} FROM {table} WHERE {column} IS NOT NULL")
    ).fetchall()

    for row_id, model_definition in rows:
        changed = False
        for model in model_definition.get("models") or []:
            service = model.get("service") or {}
            start_command = service.get("start_command")
            if isinstance(start_command, list) and len(start_command) == 1 and " " in start_command[0]:
                # Case when the start_command is a single string that looks like a shell command.
                # e.g. ["python service.py"] -> ["/bin/bash", "-c", "python service.py"]
                shell = service.get("shell") or DEFAULT_SHELL
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

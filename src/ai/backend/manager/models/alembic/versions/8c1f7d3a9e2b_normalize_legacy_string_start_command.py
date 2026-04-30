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


def _normalize_model(model: object) -> tuple[object, bool]:
    if not isinstance(model, dict):
        return model, False

    service = model.get("service")
    if not isinstance(service, dict):
        return model, False

    start_command = service.get("start_command")
    if not isinstance(start_command, str):
        return model, False

    normalized_service = {**service, "start_command": [start_command]}
    return {**model, "service": normalized_service}, True


def _normalize_models(models: object) -> tuple[object, bool]:
    if not isinstance(models, list):
        return models, False

    changed = False
    normalized_models = []
    for model in models:
        normalized_model, model_changed = _normalize_model(model)
        normalized_models.append(normalized_model)
        changed = changed or model_changed

    return normalized_models, changed


def _normalize_model_definition(conn: Connection, table: str, column: str) -> None:
    rows = conn.execute(
        sa.text(f"SELECT id, {column} FROM {table} WHERE {column} IS NOT NULL")
    ).fetchall()

    for row_id, model_definition in rows:
        if not isinstance(model_definition, dict):
            continue
        normalized_models, changed = _normalize_models(model_definition.get("models"))
        if not changed:
            continue

        normalized_definition = {**model_definition, "models": normalized_models}
        conn.execute(
            sa.text(f"UPDATE {table} SET {column} = CAST(:definition AS JSONB) WHERE id = :id"),
            {"definition": json.dumps(normalized_definition), "id": row_id},
        )


def upgrade() -> None:
    conn = op.get_bind()
    _normalize_model_definition(conn, "deployment_revisions", "model_definition")
    _normalize_model_definition(conn, "deployment_revision_presets", "model_definition")
    _normalize_model_definition(conn, "runtime_variants", "default_model_definition")


def downgrade() -> None:
    # No-op: list form is also valid under the pre-#11402 schema.
    pass

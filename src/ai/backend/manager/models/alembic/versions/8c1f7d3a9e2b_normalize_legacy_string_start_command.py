"""normalize legacy string start_command in stored model definitions

BA-5891 / PR #11402 narrowed ``ModelServiceConfig.start_command`` from
``str | list[str]`` to ``list[str] | None``. Existing rows that were
created when the string form was still accepted now fail Pydantic
validation when SQLAlchemy materializes the JSONB columns through
``PydanticColumn(ModelDefinition[Draft])``, which 500s every reader
(``myDeployments``/``adminDeployments``, scheduler, the
``admin_refresh_deployment_revisions`` repair path itself, ...).

This migration wraps legacy string values as a one-item list so the
new schema accepts the rows without otherwise changing the stored
command value.

Three columns hold ``ModelDefinition``-shaped JSONB and need rewriting:

- ``deployment_revisions.model_definition``
- ``deployment_revision_presets.model_definition``
- ``runtime_variants.default_model_definition`` (Draft variant; ``models``
  may be ``None`` for the empty seed of the ``custom`` runtime variant)

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
    # Data-only migration: downgrade is intentionally a no-op.
    # Reverting to the prior string form would be ambiguous for rows that
    # were already created in the new list form, and the pre-PR runtime
    # accepted both representations anyway.
    pass

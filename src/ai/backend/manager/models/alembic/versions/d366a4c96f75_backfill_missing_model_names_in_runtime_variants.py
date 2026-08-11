"""backfill missing model names in runtime_variants

``default_model_definition`` now loads as ``DefaultModelDefinition``, which
requires ``name`` on every model entry; fill nameless entries from the variant
name so pre-existing rows keep loading. Idempotent.

Revision ID: d366a4c96f75
Revises: c1a7d3f05e28
Create Date: 2026-08-05 18:30:00.000000

"""

import json

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d366a4c96f75"
down_revision = "c1a7d3f05e28"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT id, name, default_model_definition FROM runtime_variants "
            "WHERE jsonb_typeof(default_model_definition->'models') = 'array' "
            "AND EXISTS ("
            "  SELECT 1 FROM jsonb_array_elements(default_model_definition->'models') AS m"
            "  WHERE jsonb_typeof(m) = 'object' AND m->>'name' IS NULL"
            ")"
        )
    ).fetchall()
    for row in rows:
        definition = dict(row.default_model_definition)
        models = definition["models"]
        for idx, model in enumerate(models):
            # Non-object elements (JSON null, scalars) are left for app-level validation.
            if isinstance(model, dict) and model.get("name") is None:
                model["name"] = f"{row.name}-model" if idx == 0 else f"{row.name}-model-{idx}"
        bind.execute(
            sa.text(
                "UPDATE runtime_variants "
                "SET default_model_definition = CAST(:definition AS JSONB) "
                "WHERE id = :id"
            ).bindparams(id=row.id, definition=json.dumps(definition))
        )


def downgrade() -> None:
    # Backfilled names are indistinguishable from operator-set ones; keep them.
    pass

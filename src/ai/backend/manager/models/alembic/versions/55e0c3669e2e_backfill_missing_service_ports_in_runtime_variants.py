"""backfill missing service ports in runtime_variants

``default_model_definition`` now requires ``service.port`` (> 1) on every
model entry; create the service block and/or fill the port so pre-existing
rows keep loading. Idempotent: only touches entries whose port is absent,
null, or not greater than 1.

Revision ID: 55e0c3669e2e
Revises: 2dccb3069031
Create Date: 2026-08-06 13:10:00.000000

"""

import json

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "55e0c3669e2e"
down_revision = "2dccb3069031"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

# Every seeded baseline ships a port, so only rows written outside the seed
# chain can lack one; 8000 matches the most common seeded service port.
_FALLBACK_PORT = 8000


def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT id, default_model_definition FROM runtime_variants "
            "WHERE jsonb_typeof(default_model_definition->'models') = 'array' "
            "AND EXISTS ("
            "  SELECT 1 FROM jsonb_array_elements(default_model_definition->'models') AS m"
            "  WHERE jsonb_typeof(m) = 'object' AND ("
            "    (m->'service'->>'port') IS NULL"
            "    OR (jsonb_typeof(m->'service'->'port') = 'number'"
            "        AND (m->'service'->>'port')::numeric <= 1)"
            "  )"
            ")"
        )
    ).fetchall()
    for row in rows:
        definition = dict(row.default_model_definition)
        for model in definition["models"]:
            # Non-object elements (JSON null, scalars) are left for app-level validation.
            if not isinstance(model, dict):
                continue
            service = model.get("service")
            if not isinstance(service, dict):
                service = {}
                model["service"] = service
            port = service.get("port")
            if port is None or (isinstance(port, (int, float)) and port <= 1):
                service["port"] = _FALLBACK_PORT
        bind.execute(
            sa.text(
                "UPDATE runtime_variants "
                "SET default_model_definition = CAST(:definition AS JSONB) "
                "WHERE id = :id"
            ).bindparams(id=row.id, definition=json.dumps(definition))
        )


def downgrade() -> None:
    # Backfilled ports are indistinguishable from operator-set ones; keep them.
    pass

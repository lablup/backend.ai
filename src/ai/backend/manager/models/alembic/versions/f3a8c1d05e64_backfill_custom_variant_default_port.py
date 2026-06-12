"""backfill default service port for custom runtime variant

Backfill the ``port`` that ``ed42bc179b91`` omitted from the ``custom``
variant's seeded ``service`` block, for databases that already ran it.
Idempotent: only touches a ``custom`` service block missing a ``port``.

Revision ID: f3a8c1d05e64
Revises: a3f1c7e2b9d4
Create Date: 2026-06-12

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f3a8c1d05e64"
down_revision = "a3f1c7e2b9d4"
# Part of: 26.6.4
branch_labels = None
depends_on = None

_DEFAULT_PORT = 8080


def upgrade() -> None:
    bind = op.get_bind()
    # Add models[0].service.port = 8080 only when the custom variant has a
    # service block but no port yet. Idempotent: re-running is a no-op once
    # the port is present.
    bind.execute(
        sa.text(
            "UPDATE runtime_variants "
            "SET default_model_definition = jsonb_set("
            "default_model_definition, '{models,0,service,port}', to_jsonb(CAST(:port AS integer))) "
            "WHERE name = 'custom' "
            "AND default_model_definition #> '{models,0,service}' IS NOT NULL "
            "AND default_model_definition #> '{models,0,service,port}' IS NULL"
        ).bindparams(port=_DEFAULT_PORT)
    )


def downgrade() -> None:
    bind = op.get_bind()
    # Remove the port only when it still equals the value this migration set,
    # so a port supplied by other means is left untouched.
    bind.execute(
        sa.text(
            "UPDATE runtime_variants "
            "SET default_model_definition = "
            "default_model_definition #- '{models,0,service,port}' "
            "WHERE name = 'custom' "
            "AND default_model_definition #> '{models,0,service,port}' = to_jsonb(CAST(:port AS integer))"
        ).bindparams(port=_DEFAULT_PORT)
    )

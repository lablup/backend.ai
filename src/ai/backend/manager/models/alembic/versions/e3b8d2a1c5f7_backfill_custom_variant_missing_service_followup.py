"""backfill custom runtime variant service block (main-head duplicate)

Idempotent duplicate of ``c7e1a9d4f6b2`` placed at the main head. ``c7e1a9d4f6b2``
is inserted into the chain right after ``9fc9e6bfe695``, so databases already
upgraded past that point (i.e. existing ``main`` databases) never run it; this
revision re-applies the same repair for them. A no-op once
``models[0].service.port`` is present.

Revision ID: e3b8d2a1c5f7
Revises: d3f8a1c45e9b
Create Date: 2026-06-23

"""

import json
from typing import Any

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e3b8d2a1c5f7"
down_revision = "d3f8a1c45e9b"
# Part of: 26.4.6 (backport), 26.7.0 (main)
branch_labels = None
depends_on = None

_DEFAULT_PORT = 8080
_DEFAULT_SERVICE: dict[str, Any] = {
    "port": _DEFAULT_PORT,
    "health_check": {
        "enable": False,
        "path": "/health",
        "interval": 10.0,
        "max_retries": 10,
        "initial_delay": 1800.0,
    },
}
_CUSTOM_DEFINITION: dict[str, Any] = {
    "models": [
        {
            "name": "custom-model",
            "service": _DEFAULT_SERVICE,
        }
    ]
}


def upgrade() -> None:
    bind = op.get_bind()

    # (1) models[0] missing entirely (default is null / [] / absent / not an
    #     object) -> seed the full custom definition.
    bind.execute(
        sa.text(
            "UPDATE runtime_variants "
            "SET default_model_definition = CAST(:definition AS JSONB) "
            "WHERE name = 'custom' "
            "AND jsonb_typeof(default_model_definition #> '{models,0}') IS DISTINCT FROM 'object'"
        ).bindparams(definition=json.dumps(_CUSTOM_DEFINITION))
    )

    # (2) models[0] is an object but service is missing/null -> create the full
    #     service block (create_missing = true).
    bind.execute(
        sa.text(
            "UPDATE runtime_variants "
            "SET default_model_definition = jsonb_set("
            "default_model_definition, '{models,0,service}', CAST(:service AS JSONB), true) "
            "WHERE name = 'custom' "
            "AND jsonb_typeof(default_model_definition #> '{models,0}') = 'object' "
            "AND jsonb_typeof(default_model_definition #> '{models,0,service}') IS DISTINCT FROM 'object'"
        ).bindparams(service=json.dumps(_DEFAULT_SERVICE))
    )

    # (3) service is an object but port is missing/null -> set the default port.
    bind.execute(
        sa.text(
            "UPDATE runtime_variants "
            "SET default_model_definition = jsonb_set("
            "default_model_definition, '{models,0,service,port}', to_jsonb(CAST(:port AS integer))) "
            "WHERE name = 'custom' "
            "AND jsonb_typeof(default_model_definition #> '{models,0,service}') = 'object' "
            "AND default_model_definition #>> '{models,0,service,port}' IS NULL"
        ).bindparams(port=_DEFAULT_PORT)
    )


def downgrade() -> None:
    # Data-only backfill that repairs an invalid baseline; the corrected state
    # is the desired one. Reversing would re-introduce the broken baseline and
    # cannot distinguish repaired rows from always-valid ones, so this is a no-op.
    pass

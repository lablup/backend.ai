"""backfill custom runtime variant service block when missing

``f3a8c1d05e64`` only backfilled the default ``port`` when the ``custom``
variant's ``models[0].service`` was already a JSON object. Databases whose
``custom`` baseline has no ``service`` block (or no ``models[0]`` at all) were
left without a port, so deployments still fail with ``port: Field required``.

This migration converges the ``custom`` baseline to the seeded default for
every remaining state, idempotently:

- ``models[0]`` missing / null / empty array  -> seed the full definition
- ``models[0]`` present but ``service`` missing/null -> create the full service block
- ``service`` present but ``port`` missing/null -> set the default port

Re-running is a no-op once ``models[0].service.port`` is present.

Revision ID: c7e1a9d4f6b2
Revises: 9fc9e6bfe695
Create Date: 2026-06-23

"""

import json
from typing import Any

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c7e1a9d4f6b2"
down_revision = "9fc9e6bfe695"
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

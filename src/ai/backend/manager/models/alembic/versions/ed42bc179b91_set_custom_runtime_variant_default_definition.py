"""seed custom runtime_variant default_model_definition

The ``custom`` variant previously held an empty Draft ({"models": null}),
so a deployment that omitted ``health_check`` in its model-definition.yaml
fell back to the schema default ``initial_delay`` of 60s — too short for
large models that take minutes to load, causing premature unhealthy
routes. Seed a baseline ``health_check`` (path ``/health``,
``initial_delay`` 1800s) matching the prebuilt variants. The user's
model-definition.yaml / request still override it field-by-field, so this
acts purely as a fallback layer. Operator-customised rows are left as-is.

Revision ID: ed42bc179b91
Revises: 0113c63f3261
Create Date: 2026-05-29

"""

# Part of: 26.6.0

import json
from typing import Any

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ed42bc179b91"
down_revision = "0113c63f3261"
branch_labels = None
depends_on = None


_CUSTOM_DEFINITION_WITH_HEALTH_CHECK: dict[str, Any] = {
    "models": [
        {
            "name": "custom-model",
            "service": {
                "health_check": {
                    "path": "/health",
                    "interval": 10.0,
                    "max_retries": 10,
                    "initial_delay": 1800.0,
                },
            },
        }
    ]
}

_EMPTY_DEFINITION: dict[str, Any] = {"models": None}


def upgrade() -> None:
    # Seed only the rows still holding the original empty definition, so an
    # operator-customised custom variant is left untouched.
    op.execute(
        sa.text(
            "UPDATE runtime_variants "
            "SET default_model_definition = CAST(:custom_definition_with_health_check AS JSONB) "
            "WHERE name = 'custom' AND default_model_definition = CAST(:empty_definition AS JSONB)"
        ).bindparams(
            custom_definition_with_health_check=json.dumps(_CUSTOM_DEFINITION_WITH_HEALTH_CHECK),
            empty_definition=json.dumps(_EMPTY_DEFINITION),
        )
    )


def downgrade() -> None:
    # Revert only the value this migration set; leave later operator edits intact.
    op.execute(
        sa.text(
            "UPDATE runtime_variants "
            "SET default_model_definition = CAST(:empty_definition AS JSONB) "
            "WHERE name = 'custom' "
            "AND default_model_definition = CAST(:custom_definition_with_health_check AS JSONB)"
        ).bindparams(
            custom_definition_with_health_check=json.dumps(_CUSTOM_DEFINITION_WITH_HEALTH_CHECK),
            empty_definition=json.dumps(_EMPTY_DEFINITION),
        )
    )

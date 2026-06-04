"""seed the custom runtime_variant default model definition

``ModelHealthCheck`` gained an ``enable`` flag (default ``False``), so health
checks are now opt-in. The ``custom`` runtime variant shipped with an empty
definition (``{"models": null}``); seed it with a default model definition whose
health check is present but disabled, so a custom deployment can opt in later by
flipping ``enable``. Pre-existing health_check blocks need no backfill: without
the ``enable`` key they read back as disabled, matching the new opt-in default.

Revision ID: ed42bc179b91
Revises: eb9d9c018e85
Create Date: 2026-05-29

"""

# Part of: 26.6.0

import json
from typing import Any

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ed42bc179b91"
down_revision = "eb9d9c018e85"
branch_labels = None
depends_on = None


_CUSTOM_DEFINITION: dict[str, Any] = {
    "models": [
        {
            "name": "custom-model",
            "service": {
                "health_check": {
                    "enable": False,
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
    op.get_bind().execute(
        sa.text(
            "UPDATE runtime_variants "
            "SET default_model_definition = CAST(:seed AS JSONB) "
            "WHERE name = 'custom' AND default_model_definition = CAST(:empty AS JSONB)"
        ).bindparams(
            seed=json.dumps(_CUSTOM_DEFINITION),
            empty=json.dumps(_EMPTY_DEFINITION),
        )
    )


def downgrade() -> None:
    op.get_bind().execute(
        sa.text(
            "UPDATE runtime_variants "
            "SET default_model_definition = CAST(:empty AS JSONB) "
            "WHERE name = 'custom' AND default_model_definition = CAST(:seed AS JSONB)"
        ).bindparams(
            seed=json.dumps(_CUSTOM_DEFINITION),
            empty=json.dumps(_EMPTY_DEFINITION),
        )
    )
